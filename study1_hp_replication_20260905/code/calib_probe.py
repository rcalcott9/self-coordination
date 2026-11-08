"""
Calibration probe for the Opus-5-focal replication. Measures ACTUAL token usage on the
REAL Study 1 prompts, so the $81 estimate becomes a measurement before ~13k calls are
committed. Uses psc_common's own settings verbatim (adaptive thinking + effort low for
Claude, reasoning effort low for GPT) and only adds usage capture, which psc_common
discards.

  python3 calib_probe.py --n 12
"""
import argparse, base64, json, os, statistics, sys
os.environ.setdefault("PSC_EXP_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.expanduser(
    "~/Desktop/Coordination/Self_Coordination/policy_specific_self_coordination_20260812_1401/code"))
import psc_common as P

IN_P, OUT_P = 5.00, 30.00


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=12)
    a = ap.parse_args()
    assert P.CLAUDE_ID == "claude-opus-5", P.CLAUDE_ID
    man = P.load_manifest()
    sids = [r["stimulus_id"] for r in man][:a.n]
    imgs = P.load_images(sids)
    cl = P.make_clients()
    # the three distinct prompt shapes the replication actually uses
    arms = [("A_focal_choice", "claude", P.STAGE_A_PROMPT),
            ("B_auditor", "gpt", P.auditor_prompt("claude")),
            ("B_salience", "gpt", P.SALIENCE_PROMPT)]
    print(f"probe: {len(sids)} stimuli x {len(arms)} arms = {len(sids)*len(arms)} calls")
    print(f"  claude={P.CLAUDE_ID} settings={P.CLAUDE_SETTINGS['thinking']}")
    print(f"  gpt={P.GPT_ID}\n")
    out = {}
    for name, who, prompt in arms:
        ti, to = [], []
        for sid in sids:
            k = [x for x in imgs if x[0] == sid][0]
            b64 = imgs[k] if isinstance(imgs[k], str) else imgs[k]
            try:
                if who == "claude":
                    r = cl["claude"].messages.create(
                        model=P.CLAUDE_ID, max_tokens=P.CLAUDE_MAX_TOKENS,
                        thinking={"type": "adaptive", "display": "summarized"},
                        output_config={"effort": "low"},
                        messages=[{"role": "user", "content": [
                            {"type": "image", "source": {"type": "base64",
                             "media_type": "image/png", "data": b64}},
                            {"type": "text", "text": prompt}]}])
                    ti.append(r.usage.input_tokens); to.append(r.usage.output_tokens)
                else:
                    r = cl["gpt"].responses.create(
                        model=P.GPT_ID, reasoning={"effort": "low", "summary": "auto"},
                        input=[{"role": "user", "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_image",
                             "image_url": f"data:image/png;base64,{b64}"}]}])
                    ti.append(r.usage.input_tokens); to.append(r.usage.output_tokens)
            except Exception as e:
                print(f"  [fail] {name} {sid}: {type(e).__name__}: {e}"[:160]); continue
        mi, mo = statistics.mean(ti), statistics.mean(to)
        c = (mi * IN_P + mo * OUT_P) / 1e6
        out[name] = dict(model=P.CLAUDE_ID if who == "claude" else P.GPT_ID,
                         n=len(ti), in_tok=mi, out_tok=mo, usd_per_call=c)
        print(f"  {name:16} {P.CLAUDE_ID if who=='claude' else P.GPT_ID:20} "
              f"n={len(ti):3d}  in {mi:6.0f}  out {mo:6.0f}   ${c:.5f}/call")

    A = out["A_focal_choice"]["usd_per_call"]
    B = (out["B_auditor"]["usd_per_call"] + out["B_salience"]["usd_per_call"]) / 2
    stages = [("A1 screen", 1920, A), ("A2 confirm", 2880, A),
              ("B auditor", 1920, out["B_auditor"]["usd_per_call"]),
              ("B salience", 1920, out["B_salience"]["usd_per_call"]),
              ("C betting", 4608, A)]
    print("\n=== SIZED FROM MEASUREMENT ===")
    tot = 0.0
    for nm, n, r in stages:
        tot += n * r
        print(f"  {nm:12} {n:5d} x ${r:.5f} = ${n*r:7.2f}")
    p1 = sum(n * r for nm, n, r in stages[:4])
    print(f"  {'TOTAL':12} {13248:5d}          = ${tot:7.2f}")
    print(f"  Phase 1 (gated) ${p1:.2f}   Phase 2 Stage C ${tot-p1:.2f}")
    print(f"  +20% contingency ${tot*1.2:.2f}   vs $100 ceiling: "
          f"{'FITS' if tot*1.2 < 100 else 'TIGHT/OVER'}")
    print("\n  NOTE: Stage C's betting prompt is not probed here (it needs a payoff "
          "frame and a paired stimulus); A_focal_choice is used as its proxy and may "
          "understate it.")
    json.dump(dict(arms=out, total=tot, phase1=p1), open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "runs", "calib_probe.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
