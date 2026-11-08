"""
Pre-flight for the GPT-5.4 / Opus-4.8 procedural replication.  ~6 paid calls.

PURPOSE. Confirm, before committing a 4,800-call budget, that:
  1. gpt-5.4 accepts reasoning={"effort":"low","summary":"auto"}
  2. claude-opus-4-8 accepts thinking={"type":"adaptive","display":"summarized"}
     AND output_config={"effort":"low"}          <- the identified risk
  3. the model ID returned matches the ID requested (catches silent alias drift)
  4. every stage's prompt parses on both models
  5. max_tokens=2000 (the EXACT Aug-7 Opus-4.8 setting, recovered from
     step1c_output/targeted_confirmation_calls.csv) does not truncate on the LONGEST
     prompt in the series, the Stage C betting prompt.

IT DOES NOT SUBSTITUTE SETTINGS. If a setting is rejected, this reports the raw
provider error and exits non-zero. Nothing is silently swapped.

Run:  python3 preflight_5_4_4_8.py
"""
import json, os, sys, traceback
import psc_common as P

GPT_ID = "gpt-5.4"
GPT_ID_PINNED = "gpt-5.4-2026-03-05"
CLAUDE_ID = "claude-opus-4-8"
CLAUDE_MAX_TOKENS = 2000          # exact Aug-7 value, not the Aug-12 value of 4000

OUT = os.path.join(P.EXP, "replication_5_4_4_8", "preflight")


def gpt_call(client, img_b64, prompt):
    r = client.responses.create(
        model=GPT_ID,
        reasoning={"effort": "low", "summary": "auto"},
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_image", "image_url": f"data:image/png;base64,{img_b64}"}]}])
    reasoning = ""
    for item in r.output:
        if item.type == "reasoning" and item.summary:
            reasoning = " ".join(p.text for p in item.summary)
            break
    status = getattr(r, "status", "")
    incomplete = getattr(r, "incomplete_details", None)
    return dict(text=(r.output_text or ""), reasoning=reasoning,
                model_returned=getattr(r, "model", ""), stop=str(status),
                truncated=bool(incomplete),
                settings={"model": GPT_ID,
                          "reasoning": {"effort": "low", "summary": "auto"},
                          "temperature": None, "max_output_tokens": None, "seed": None})


def claude_call(client, img_b64, prompt):
    r = client.messages.create(
        model=CLAUDE_ID,
        max_tokens=CLAUDE_MAX_TOKENS,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": img_b64}},
            {"type": "text", "text": prompt}]}])
    reasoning, answer = "", ""
    for b in r.content:
        if b.type == "thinking":
            reasoning = b.thinking or ""
        elif b.type == "text":
            answer += b.text
    u = getattr(r, "usage", None)
    return dict(text=answer, reasoning=reasoning, model_returned=getattr(r, "model", ""),
                stop=str(getattr(r, "stop_reason", "")),
                truncated=(getattr(r, "stop_reason", "") == "max_tokens"),
                usage={"in": getattr(u, "input_tokens", None),
                       "out": getattr(u, "output_tokens", None)} if u else None,
                settings={"model": CLAUDE_ID, "max_tokens": CLAUDE_MAX_TOKENS,
                          "thinking": {"type": "adaptive", "display": "summarized"},
                          "output_config": {"effort": "low"},
                          "temperature": None, "seed": None})


CALL = {"gpt": gpt_call, "claude": claude_call}
WANT = {"gpt": GPT_ID, "claude": CLAUDE_ID}


def main():
    os.makedirs(OUT, exist_ok=True)
    clients = P.make_clients()
    imgs = P.load_images(["proto"])          # keyed by (stimulus, variant)
    img = imgs[("proto", "AB")]

    # The three prompts, shortest to longest. Stage C is the truncation stress test.
    stage_a = P.PROMPT if hasattr(P, "PROMPT") else P.STEP1_PROMPT
    probes = [("A_ground_truth", stage_a, P.parse_side),
              ("B_auditor", P.auditor_prompt("gpt"), P.parse_probability),
              ("C_betting", P.betting_prompt(7), P.parse_decision)]

    results, failures = [], []
    for model in ("gpt", "claude"):
        for name, prompt, parser in probes:
            rec = dict(model=model, probe=name, requested=WANT[model],
                       prompt_sha8=P.sha8(prompt), prompt_chars=len(prompt))
            try:
                r = CALL[model](clients[model], img, prompt)
                rec.update(r)
                try:
                    rec["parsed"] = repr(parser(r["text"]))
                except Exception as e:
                    rec["parsed"] = f"__PARSE_RAISED__ {e}"
                rec["id_matches"] = r["model_returned"].startswith(WANT[model])
                rec["ok"] = (bool(r["text"].strip()) and not r["truncated"]
                             and rec["id_matches"]
                             and not str(rec["parsed"]).startswith("__"))
                if not rec["ok"]:
                    failures.append(f"{model}/{name}: text={bool(r['text'].strip())} "
                                    f"truncated={r['truncated']} "
                                    f"id_returned={r['model_returned']!r} "
                                    f"parsed={rec['parsed']}")
            except Exception as e:
                rec.update(ok=False, error=f"{type(e).__name__}: {e}",
                           trace=traceback.format_exc()[-1200:])
                failures.append(f"{model}/{name}: RAISED {type(e).__name__}: {e}")
            results.append(rec)
            flag = "ok " if rec.get("ok") else "FAIL"
            print(f"  [{flag}] {model:7} {name:16} "
                  f"returned={rec.get('model_returned','-')!r:26} "
                  f"stop={rec.get('stop','-')!r:14} parsed={rec.get('parsed','-')}")

    with open(os.path.join(OUT, "preflight_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  {len(results) - len(failures)} of {len(results)} probes ok")
    if failures:
        print("\nFAILURES - main run must NOT launch:")
        for x in failures:
            print("   -", x)
        sys.exit(1)
    print("  settings confirmed; results -> replication_5_4_4_8/preflight/")


if __name__ == "__main__":
    main()
