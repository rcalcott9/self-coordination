"""
GATE: does partner identity register BEHAVIOURALLY?

Nothing expensive runs until this passes. The prior is bad - the previous Study 2
found 0 of 1,424 Stage C rationales containing policy talk, partner mentioned in
3.5%/4.5%, and attention anti-correlated with where partner identity mattered. If
identity does not move predictions even under the most explicit wording available,
Stage C's convention x partner interaction is structurally unreachable and no
stimulus battery fixes it.

DESIGN. focal (2) x partner_same (2) x stimulus (8) x reps. Stimuli chosen from
discovery to span the cases where identity SHOULD matter and where it should not:

  anti_coordinated  both models decisive on DIFFERENT items; cross-match ~.13-.25.
                    A calibrated model should say ~high for a same-model partner
                    and ~low for a different-model partner. Largest predicted gap.
  one_sided         one model decisive, the other near chance.
  shared_control    both ~1.000 on the SAME item; cross ~1.000. NO gap predicted -
                    this is what separates "registers identity" from "says a lower
                    number whenever it hears the word different".

The shared controls are the reason this is a real test rather than a demand
characteristic: a model that simply discounts on hearing "different model" moves
on them too, and that pattern is distinguishable from tracking true cross-match.

MEASURES, all behavioural - the model is never asked about policies or self-models:
  MATCH_PROBABILITY  predicted P(match)
  MY_CHOICE          its own pick (does it abandon its convention to meet the other?)
  PARTNER_LIKELY     its prediction of the partner's pick

Run:  python3 run_manipulation_check.py --dry-run
      python3 run_manipulation_check.py
"""
import os, csv, json, argparse
import s4_common as S

# Frozen from discovery (cell_metrics_discovery.csv) BEFORE this run, recorded here
# so the selection is auditable and cannot drift.
STIMULI = [
    # sid,                kind,               gpt_modal, claude_modal, cross
    ("F10_curvature_m5", "anti_coordinated",  3, 0, 0.125),
    ("F10_curvature_m3", "anti_coordinated",  3, 0, 0.156),
    ("F06_density_m0",   "anti_coordinated",  3, 0, 0.250),
    ("F12_mirror_m7",    "one_sided_gpt",     3, 2, 0.085),
    ("F12_mirror_m6",    "one_sided_gpt",     1, 1, 0.458),
    ("F11_noise_m0",     "one_sided_claude",  2, 1, 0.292),
    ("F01_oddone_m0",    "shared_control",    3, 3, 1.000),
    ("F02_size_m2",      "shared_control",    0, 0, 1.000),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=12, help="reps per cell (div by 4)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=S.WORKERS)
    a = ap.parse_args()

    jobs = []
    for sid, kind, gm, cm, cross in STIMULI:
        for focal in ("gpt", "claude"):
            for same in (True, False):
                for trial, perm_id in enumerate(S.position_schedule(a.n)):
                    jobs.append(dict(
                        job_key=f"mc|{sid}|{focal}|{int(same)}|{trial}",
                        sid=sid, kind=kind, actor=focal, focal=focal,
                        partner_same=same, trial=trial, perm_id=perm_id,
                        gpt_modal=gm, claude_modal=cm, cross_match=cross))

    print(f"stimuli={len(STIMULI)}  focal=2  partner=2  reps={a.n}")
    for k in ("predict_gpt_same", "predict_gpt_diff",
              "predict_claude_same", "predict_claude_diff"):
        print(f"  prompt sha8 {k:22} {S.PROMPT_SHA[k]}")
    print(f"planned calls = {len(jobs)}")

    imgs = {}

    def images_for(job):
        k = (job["sid"], job["perm_id"])
        if k not in imgs:
            imgs[k] = S.b64(os.path.join(S.STIM, job["sid"],
                                         f"perm{job['perm_id']:02d}.png"))
        return imgs[k]

    def prompt_for(job):
        return S.predict_prompt(job["focal"], job["partner_same"])

    if a.dry_run:
        print("\n--- SAME ---\n" + S.predict_prompt("gpt", True))
        print("\n--- DIFFERENT ---\n" + S.predict_prompt("gpt", False))
        return

    prefix, rows = S.run_stage("manipcheck", jobs, prompt_for, images_for,
                               workers=a.workers)

    man, out, fails = {}, [], 0
    for r in rows:
        sid = r["sid"]
        if sid not in man:
            man[sid] = json.load(open(os.path.join(S.STIM, sid, "manifest.json")))
        pm = S.parse_probability(r["raw"]) if r["ok"] else None
        mc = S.parse_my_choice(r["raw"]) if r["ok"] else None
        pl = S.parse_likely(r["raw"]) if r["ok"] else None
        m = man[sid][str(r["perm_id"])]
        if r["ok"] and (pm is None or mc is None or pl is None):
            fails += 1
        out.append(dict(
            stimulus_id=sid, kind=r["kind"], focal=r["focal"],
            partner_same=int(r["partner_same"]), trial=r["trial"],
            perm_id=r["perm_id"],
            predicted_match=("" if pm is None else pm),
            my_choice_item=("" if mc is None else m[mc]),
            partner_pred_item=("" if pl is None else m[pl]),
            my_choice_pos=("" if mc is None else mc + 1),
            partner_pred_pos=("" if pl is None else pl + 1),
            gpt_modal=r["gpt_modal"], claude_modal=r["claude_modal"],
            true_cross=r["cross_match"],
            ok=r["ok"], parse_ok=(pm is not None and mc is not None and pl is not None),
            error=r["error"], api_model=r["api_model"], ts=r["ts"],
            raw=r["raw"].replace("\n", " | ")[:800]))

    p = os.path.join(S.DATA, "manipulation_check_results.csv")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    print(f"\nwrote {p}  ({len(out)} rows)")
    print(f"  transport ok : {sum(1 for r in out if r['ok'])}/{len(out)}")
    print(f"  parsed ok    : {sum(1 for r in out if r['parse_ok'])}/{len(out)}")
    print(f"  PARSE FAILURES: {fails} (kept with parse_ok=False)")


if __name__ == "__main__":
    main()
