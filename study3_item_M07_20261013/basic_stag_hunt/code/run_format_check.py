"""M07 SELF format check: 8 calls (2 models x 2 action + 2 prediction). Nothing else.

Authorization (verbatim, user, 2026-10-14, session 80332460): "run". Read narrowly as the recorded
next action: the 8-call format check (~$0.10), then stop and inspect. It does not start the SELF
pilot or the fixed-partner pilot.

Format-check calls use their own order seeds (kind "fc_action"/"fc_prediction"), so the pilot's
seeded slots are untouched. Responses are for parsing inspection only and are not pilot data.
Run 1 (results/format_check_20261014_000026) kept only visible text and two usage numbers. Since
2026-10-14 every call also keeps stop reason, full usage, block types/lengths and the raw response
(summarize()); verified offline on constructed responses, no rerun.
Same API surfaces as Study 1/2 (s4_common): GPT-5.5 reasoning effort low; Opus 5 adaptive thinking,
effort low. Hard stop if logged cost reaches CAP.
"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import selfplay as SP
sys.path.insert(0, "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code")
import s4_common as S

CAP = 0.50
PRICE = {"gpt": (5, 30), "claude": (5, 25)}          # $ per M input / output tokens (applied spec)
KEY = {"gpt-5.5": "gpt", "claude-opus-5": "claude"}


def summarize(fam, r):
    """Everything needed to tell empty visible text from absent generation, kept per call:
    stop reason, the full returned usage object, each content/output block's type and text length,
    and the complete raw response."""
    raw = r.model_dump(mode="json")
    if fam == "gpt":
        blocks = [dict(type=o.get("type"), n_chars=sum(len(c.get("text") or "") for c in o.get("content") or [])
                       + sum(len(x.get("text") or "") for x in o.get("summary") or []))
                  for o in raw.get("output") or []]
        return dict(text=r.output_text or "", api_model=r.model, response_id=r.id, stop_reason=raw.get("status"),
                    incomplete_details=raw.get("incomplete_details"), usage=raw.get("usage"), blocks=blocks, raw=raw)
    blocks = [dict(type=b.get("type"), n_chars=len(b.get("text") or b.get("thinking") or ""),
                   has_signature=bool(b.get("signature")), has_data=bool(b.get("data")))
              for b in raw.get("content") or []]
    return dict(text="".join(b.get("text") or "" for b in raw.get("content") or [] if b.get("type") == "text"),
                api_model=r.model, response_id=r.id, stop_reason=raw.get("stop_reason"),
                stop_details=raw.get("stop_details"), usage=raw.get("usage"), blocks=blocks, raw=raw)


def ask(clients, fam, prompt):
    if fam == "gpt":
        r = clients["gpt"].responses.create(model=S.GPT_ID, reasoning={"effort": "low", "summary": "auto"},
                                            input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}])
    else:
        r = clients["claude"].messages.create(model=S.CLAUDE_ID, max_tokens=S.CLAUDE_MAX_TOKENS,
                                              thinking={"type": "adaptive", "display": "summarized"},
                                              output_config={"effort": "low"},
                                              messages=[{"role": "user", "content": prompt}])
    return summarize(fam, r)


def main():
    jobs = []
    for m in SP.MODELS:
        for kind, f in (("fc_action", SP.action_prompt), ("fc_prediction", SP.prediction_prompt)):
            for i in range(2):
                o = SP.order(m, kind, i)
                jobs.append(dict(call_id=f"{m}|{kind}|{i}", model=m, kind=kind.replace("fc_", ""), i=i,
                                 order="|".join(o), prompt=f(m, o)))
    assert len(jobs) == 8
    out = os.path.join(SP.HERE, "results", f"format_check_{time.strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(out)
    clients = S.make_clients()
    spent = [0.0]

    def one(j):
        if spent[0] >= CAP:
            return dict(j, response=None, error="cap reached")
        fam = KEY[j["model"]]
        try:
            x = ask(clients, fam, j["prompt"])
            tin, tout = x["usage"]["input_tokens"], x["usage"]["output_tokens"]
            cost = (tin * PRICE[fam][0] + tout * PRICE[fam][1]) / 1e6
            spent[0] += cost
            return dict(j, response=x.pop("text"), input_tokens=tin, output_tokens=tout, cost=cost, error=None, **x)
        except Exception as e:
            body = getattr(e, "body", None)
            return dict(j, response=None, error=f"{type(e).__name__}: {e}", error_body=body,
                        status_code=getattr(e, "status_code", None))

    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(one, jobs))
    with open(os.path.join(out, "responses.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    for r in rows:
        parsed = (SP.parse_action(r["response"]) if r["kind"] == "action"
                  else SP.parse_prediction(r["response"], r["order"].split("|"))) if r["response"] else None
        print(f"--- {r['call_id']}  model={r.get('api_model')}  in/out={r.get('input_tokens')}/{r.get('output_tokens')}  "
              f"${r.get('cost', 0):.4f}  error={r['error']}")
        print(repr(r["response"]))
        print("parsed:", parsed)
    print(f"\ntotal logged cost ${spent[0]:.4f}  ->  {out}")


if __name__ == "__main__":
    main()
