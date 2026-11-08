"""
Gate 1 availability + control-surface probe.  ONE call per checkpoint, 17 calls.

Derived from policy_specific_self_coordination_20260812_1401/code/ladder_probe.py.
The original and its 2026-08-14 output are NOT touched; that output is preserved
beside this file as ladder_probe_20260814_PRESERVED.json.

Three changes from the original:

  (a) OUT redirected into this study's run directory.
  (b) Vision-detection substring bug fixed. The original tested
        "image" in low and "not supported" in low
      which misses OpenAI's actual phrasing "does not support image input"
      ("not support", no trailing 'ed'), so a genuine no-vision model was
      recorded as vision=True.
  (c) The Anthropic branch now probes THINKING OFF rather than adaptive-on,
      because that is the setting Stage 1 must run under, and the question the
      panel needs answered is which checkpoints accept it.  Two rungs, in order:
        1. thinking={"type": "disabled"}      -- explicit off
        2. no thinking parameter at all       -- implicit off
      Whether any thinking block comes back is recorded, so "off" is verified
      from the response rather than assumed from the request.

  claude-haiku-4-5-20251001 is added; it was never in the 2026-08-14 probe.

Prompt and stimulus are the frozen four-option visual ones
(s4_common.STAGE_A_PROMPT, sha8 d40ea45d) so the probe exercises the real call
shape.  No results from this probe enter any analysis.

Run:  python3 gate1_probe.py
"""
import base64, datetime, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "study2_4opt_20260830", "code"))
import s4_common as S4                                    # noqa: E402

OUT = HERE
STIM = os.path.join(ROOT, "study2_4opt_20260830", "stimuli",
                    "F01_oddone_m0", "perm00.png")

OPENAI = [
    ("gpt-4-0613",   "gpt-4-0613",             "2023-06"),
    ("gpt-4-turbo",  "gpt-4-turbo-2024-04-09", "2024-04"),
    ("gpt-4o",       "gpt-4o-2024-05-13",      "2024-05"),
    ("gpt-4o",       "gpt-4o-2024-11-20",      "2024-11"),
    ("gpt-4.1",      "gpt-4.1-2025-04-14",     "2025-04"),
    ("gpt-5",        "gpt-5-2025-08-07",       "2025-08"),
    ("gpt-5.1",      "gpt-5.1-2025-11-13",     "2025-11"),
    ("gpt-5.2",      "gpt-5.2-2025-12-11",     "2025-12"),
    ("gpt-5.4",      "gpt-5.4-2026-03-05",     "2026-03"),
    ("gpt-5.5",      "gpt-5.5-2026-04-23",     "2026-04"),
]
ANTHROPIC = [
    ("claude-sonnet-4-5", "claude-sonnet-4-5-20250929", "2025-09"),
    ("claude-haiku-4-5",  "claude-haiku-4-5-20251001",  "2025-10"),
    ("claude-opus-4-5",   "claude-opus-4-5-20251101",   "2025-11"),
    ("claude-opus-4-6",   "claude-opus-4-6",            "2026-02"),
    ("claude-opus-4-7",   "claude-opus-4-7",            "2026-04"),
    ("claude-opus-4-8",   "claude-opus-4-8",            "2026-05"),
    ("claude-opus-5",     "claude-opus-5",              "2026-07"),
]

REASONING_OK = ("gpt-5",)


def openai_call(client, mid, img, prompt):
    kw = dict(model=mid, input=[{"role": "user", "content": [
        {"type": "input_text", "text": prompt},
        {"type": "input_image", "image_url": f"data:image/png;base64,{img}"}]}])
    if mid.startswith(REASONING_OK):
        kw["reasoning"] = {"effort": "low", "summary": "auto"}
        surface = "reasoning.effort=low"
    else:
        kw["temperature"] = 1.0
        surface = "temperature=1.0 (no reasoning param)"
    r = client.responses.create(**kw)
    u = getattr(r, "usage", None)
    usage = {"in": getattr(u, "input_tokens", None),
             "out": getattr(u, "output_tokens", None)} if u else None
    return (r.output_text or ""), getattr(r, "model", ""), surface, usage, None


def _anthropic(client, mid, img, prompt, thinking_kw, surface):
    kw = dict(model=mid, max_tokens=2000,
              messages=[{"role": "user", "content": [
                  {"type": "image", "source": {"type": "base64",
                                               "media_type": "image/png",
                                               "data": img}},
                  {"type": "text", "text": prompt}]}])
    kw.update(thinking_kw)
    r = client.messages.create(**kw)
    txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    saw_thinking = any(getattr(b, "type", "") in ("thinking", "redacted_thinking")
                       for b in r.content)
    u = getattr(r, "usage", None)
    usage = {"in": getattr(u, "input_tokens", None),
             "out": getattr(u, "output_tokens", None)} if u else None
    return txt, getattr(r, "model", ""), surface, usage, saw_thinking


def main():
    clients = S4.make_clients()
    img = base64.b64encode(open(STIM, "rb").read()).decode()
    prompt = S4.STAGE_A_PROMPT
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results = []

    for provider, cands in (("openai", OPENAI), ("anthropic", ANTHROPIC)):
        print(f"\n=== {provider} ===")
        for fam, mid, date in cands:
            rec = dict(provider=provider, family=fam, model_id=mid, released=date)
            try:
                if provider == "openai":
                    txt, ret, surface, usage, thk = openai_call(
                        clients["gpt"], mid, img, prompt)
                else:
                    try:
                        txt, ret, surface, usage, thk = _anthropic(
                            clients["claude"], mid, img, prompt,
                            {"thinking": {"type": "disabled"}},
                            "thinking={'type':'disabled'} (explicit off)")
                    except Exception as e1:
                        rec["explicit_off_error"] = f"{type(e1).__name__}: {str(e1)[:200]}"
                        txt, ret, surface, usage, thk = _anthropic(
                            clients["claude"], mid, img, prompt, {},
                            "no thinking parameter (implicit off)")
                parsed = S4.parse_choice(txt)
                rec.update(ok=True, vision=True, control_surface=surface,
                           model_returned=ret, alias_match=(ret == mid),
                           parsed=parsed, parses=parsed is not None,
                           thinking_blocks_returned=thk, usage=usage,
                           reply_chars=len(txt))
                flag = "" if ret == mid else f"  ALIAS->{ret}"
                print(f"  [ok  ] {mid:28} {surface:44} parsed={parsed}"
                      f" thk={thk} usage={usage}{flag}")
            except Exception as e:
                msg = f"{type(e).__name__}: {str(e)[:250]}"
                low = msg.lower()
                no_vision = ("image" in low and
                             ("not support" in low or "unsupported" in low
                              or "does not accept" in low))
                rec.update(ok=False, error=msg, vision=not no_vision,
                           control_surface=None)
                print(f"  [FAIL] {mid:28} {msg[:120]}")
            results.append(rec)

    payload = {"probe": "gate1_availability_and_thinking_surface",
               "started_utc": started,
               "finished_utc": datetime.datetime.now(
                   datetime.timezone.utc).isoformat(),
               "stimulus": os.path.relpath(STIM, ROOT),
               "prompt_sha8": S4.__dict__.get("STAGE_A_PROMPT") and
                              __import__("hashlib").sha256(
                                  prompt.encode()).hexdigest()[:8],
               "results": results}
    dst = os.path.join(OUT, "gate1_probe.json")
    json.dump(payload, open(dst, "w"), indent=2, default=str)

    ok = [r for r in results if r.get("ok")]
    print(f"\n  reachable: {len(ok)} of {len(results)}")
    print(f"  parses   : {sum(1 for r in ok if r.get('parses'))}")
    print(f"  alias ok : {sum(1 for r in ok if r.get('alias_match'))}")
    ti = sum((r.get('usage') or {}).get('in') or 0 for r in ok)
    to = sum((r.get('usage') or {}).get('out') or 0 for r in ok)
    print(f"  tokens   : in={ti} out={to}")
    print(f"  -> {dst}")


if __name__ == "__main__":
    main()
