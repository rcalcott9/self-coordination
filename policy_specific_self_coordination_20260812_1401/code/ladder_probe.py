"""
Technical compatibility probe for the model-generation ladder. 1 call per candidate.

Answers, per model, EMPIRICALLY rather than by assumption:
  - does it accept an image at all (vision support)?
  - which control surface does it expose - reasoning effort, or temperature?
  - does the Stage A prompt parse?
  - what model ID actually comes back (catches silent alias drift)?

THE CONFOUND THIS EXPOSES. The paradigm's frozen setting is
reasoning={"effort":"low"} (OpenAI) / thinking adaptive + output_config effort
(Anthropic). Pre-5 OpenAI models have NO reasoning parameter and instead expose
temperature. So "identical settings" CANNOT hold across the reasoning boundary; the
ladder necessarily compares models that differ in control surface as well as
generation. That is reported, not silently patched.

Run:  python3 ladder_probe.py
"""
import json, os, sys, traceback
import psc_common as P

OUT = os.path.join(P.EXP, "ladder", "probe")

# Flagship / widest-spacing candidates, oldest first. Pinned snapshots where published.
OPENAI = [
    ("gpt-4-0613", "gpt-4-0613", "2023-06"),
    ("gpt-4-turbo", "gpt-4-turbo-2024-04-09", "2024-04"),
    ("gpt-4o", "gpt-4o-2024-05-13", "2024-05"),
    ("gpt-4o", "gpt-4o-2024-11-20", "2024-11"),
    ("gpt-4.1", "gpt-4.1-2025-04-14", "2025-04"),
    ("gpt-5", "gpt-5-2025-08-07", "2025-08"),
    ("gpt-5.1", "gpt-5.1-2025-11-13", "2025-11"),
    ("gpt-5.2", "gpt-5.2-2025-12-11", "2025-12"),
    ("gpt-5.4", "gpt-5.4-2026-03-05", "2026-03"),
    ("gpt-5.5", "gpt-5.5-2026-04-23", "2026-04"),
]
ANTHROPIC = [
    ("claude-sonnet-4-5", "claude-sonnet-4-5-20250929", "2025-09"),
    ("claude-opus-4-5", "claude-opus-4-5-20251101", "2025-11"),
    ("claude-opus-4-6", "claude-opus-4-6", "2026-02"),
    ("claude-opus-4-7", "claude-opus-4-7", "2026-04"),
    ("claude-opus-4-8", "claude-opus-4-8", "2026-05"),
    ("claude-opus-5", "claude-opus-5", "2026-07"),
]

REASONING_OK = ("gpt-5",)      # prefix test; pre-5 OpenAI has no reasoning param


def openai_call(client, mid, img, prompt):
    """Try reasoning effort first for gpt-5+; fall back to temperature for older."""
    kw = dict(model=mid, input=[{"role": "user", "content": [
        {"type": "input_text", "text": prompt},
        {"type": "input_image", "image_url": f"data:image/png;base64,{img}"}]}])
    surface = "reasoning.effort=low"
    if mid.startswith(REASONING_OK):
        kw["reasoning"] = {"effort": "low", "summary": "auto"}
    else:
        kw["temperature"] = 1.0
        surface = "temperature=1.0 (no reasoning param)"
    r = client.responses.create(**kw)
    return (r.output_text or ""), getattr(r, "model", ""), surface


def anthropic_call(client, mid, img, prompt):
    r = client.messages.create(
        model=mid, max_tokens=2000,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": img}},
            {"type": "text", "text": prompt}]}])
    txt = "".join(b.text for b in r.content if b.type == "text")
    return txt, getattr(r, "model", ""), "thinking=adaptive + output_config.effort=low"


def anthropic_fallback(client, mid, img, prompt):
    """Older Claude may reject adaptive thinking / output_config. Try plain."""
    r = client.messages.create(
        model=mid, max_tokens=2000, temperature=1.0,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": img}},
            {"type": "text", "text": prompt}]}])
    txt = "".join(b.text for b in r.content if b.type == "text")
    return txt, getattr(r, "model", ""), "temperature=1.0 (no thinking/effort)"


def main():
    os.makedirs(OUT, exist_ok=True)
    clients = P.make_clients()
    img = P.load_images(["proto"])[("proto", "AB")]
    prompt = P.STEP1_PROMPT
    results = []

    for provider, cands in (("openai", OPENAI), ("anthropic", ANTHROPIC)):
        print(f"\n=== {provider} ===")
        for fam, mid, date in cands:
            rec = dict(provider=provider, family=fam, model_id=mid, released=date)
            try:
                if provider == "openai":
                    txt, ret, surface = openai_call(clients["gpt"], mid, img, prompt)
                else:
                    try:
                        txt, ret, surface = anthropic_call(clients["claude"], mid, img, prompt)
                    except Exception as e1:
                        rec["primary_surface_error"] = f"{type(e1).__name__}: {str(e1)[:160]}"
                        txt, ret, surface = anthropic_fallback(clients["claude"], mid, img, prompt)
                parsed = P.parse_side(txt)
                rec.update(ok=True, vision=True, control_surface=surface,
                           model_returned=ret, parsed=repr(parsed),
                           parses=parsed not in (None, "__ERR__"),
                           reply_chars=len(txt))
                print(f"  [ok  ] {mid:28} ret={ret:28} {surface:38} parsed={parsed!r}")
            except Exception as e:
                msg = f"{type(e).__name__}: {str(e)[:200]}"
                low = msg.lower()
                rec.update(ok=False, error=msg,
                           vision=not ("image" in low and "not supported" in low),
                           control_surface=None)
                print(f"  [FAIL] {mid:28} {msg[:110]}")
            results.append(rec)

    json.dump(results, open(os.path.join(OUT, "ladder_probe.json"), "w"),
              indent=2, default=str)
    ok = [r for r in results if r.get("ok") and r.get("parses")]
    print(f"\n  usable for the paradigm: {len(ok)} of {len(results)}")
    for r in ok:
        print(f"    {r['released']}  {r['model_id']:28} {r['control_surface']}")
    print(f"  -> {OUT}/ladder_probe.json")


if __name__ == "__main__":
    main()
