"""
Stage C PILOT - estimate decision-scale beta3 before committing to a confirmatory.

WHY A PILOT. The power simulation is anchored on a PREDICTION-task gradient
(manipulation check: +0.051/unit GPT, +0.066/unit Claude -> beta3 ~ .033/.043).
At that size the study is unwinnable at any feasible scale; at beta3 >= .15 the
existing 8/7-pair battery is already at 0.94/0.91 power. The two branches are
decided by ONE unmeasured quantity - whether the gradient transfers from stating a
probability to making a decision. A decision near a payoff threshold can amplify a
small perceived-p shift, or the safe payoff can swamp it. ~4,800 calls settles it,
and also replaces the two guessed simulation nuisance parameters (between-family SD
of attempt rate, and the LOW x DIFFERENT baseline) with measured ones.

This is explicitly NOT the confirmatory sample.

DESIGN. focal x pair x level(HIGH/LOW) x partner(SAME/DIFF) x safe{3,5,7,9} x 20.
Pairs come from candidate_pairs.csv - distinct families on both sides, HIGH
model-specific (own-cross >= .15), LOW non-positional.

  GPT     8 pairs x 2 x 2 x 4 x 20 = 2,560
  Claude  7 pairs x 2 x 2 x 4 x 20 = 2,240

Run:  python3 run_pilot.py --dry-run
      python3 run_pilot.py --reps 4 --pairs 1     # smoke
      python3 run_pilot.py
"""
import os, csv, json, argparse
import s4_common as S


def load_pairs():
    p = os.path.join(S.DATA, "candidate_pairs.csv")
    return list(csv.DictReader(open(p)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20, help="per cell (div by 4)")
    ap.add_argument("--pairs", type=int, default=None, help="limit pairs per focal")
    ap.add_argument("--focal", nargs="*", default=["gpt", "claude"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=S.WORKERS)
    ap.add_argument("--resume-from", default=None)
    a = ap.parse_args()

    pairs = [r for r in load_pairs() if r["focal"] in a.focal]
    byf = {}
    for r in pairs:
        byf.setdefault(r["focal"], []).append(r)
    if a.pairs:
        for f in byf:
            byf[f] = byf[f][:a.pairs]

    jobs = []
    for focal, prs in byf.items():
        for pi, pr in enumerate(prs):
            for level, sid in (("HIGH", pr["high_stimulus"]),
                               ("LOW", pr["low_stimulus"])):
                for same in (True, False):
                    for safe in S.SAFE_VALUES:
                        for t, perm_id in enumerate(S.position_schedule(a.reps)):
                            jobs.append(dict(
                                job_key=f"pc|{focal}|{pi}|{level}|{int(same)}|{safe}|{t}",
                                focal=focal, actor=focal, pair_index=pi,
                                pair_id=f"{focal}_{pi}", level=level, sid=sid,
                                family=(pr["high_family"] if level == "HIGH"
                                        else pr["low_family"]),
                                partner_same=same, safe=safe, trial=t,
                                perm_id=perm_id,
                                stim_self_match=float(pr["high_self"] if level == "HIGH"
                                                      else pr["low_self"]),
                                high_own_minus_cross=float(pr["high_own_minus_cross"]),
                                gap_design=float(pr["gap"])))

    for f, prs in byf.items():
        n = len(prs) * 2 * 2 * 4 * a.reps
        print(f"  {S.DISPLAY[f]:16} {len(prs)} pairs -> {n:,} calls")
    print(f"planned calls = {len(jobs):,}")
    print(f"prompt sha8 (gpt/same/safe=7) = "
          f"{S.sha8(S.betting_prompt('gpt', True, 7))}")

    if a.dry_run:
        print("\n--- SAME, safe=7 ---\n" + S.betting_prompt("gpt", True, 7))
        print("\n--- DIFFERENT, safe=3 ---\n" + S.betting_prompt("gpt", False, 3))
        return

    imgs = {}

    def images_for(job):
        k = (job["sid"], job["perm_id"])
        if k not in imgs:
            imgs[k] = S.b64(os.path.join(S.STIM, job["sid"],
                                         f"perm{job['perm_id']:02d}.png"))
        return imgs[k]

    def prompt_for(job):
        return S.betting_prompt(job["focal"], job["partner_same"], job["safe"])

    prefix, rows = S.run_stage("stageC_pilot", jobs, prompt_for, images_for,
                               workers=a.workers, resume_from=a.resume_from)

    man, out, fails = {}, [], 0
    for r in rows:
        sid = r["sid"]
        if sid not in man:
            man[sid] = json.load(open(os.path.join(S.STIM, sid, "manifest.json")))
        dec = S.parse_decision(r["raw"]) if r["ok"] else None
        pos = S.parse_choice(r["raw"]) if r["ok"] else None
        item = man[sid][str(r["perm_id"])][pos] if pos is not None else None
        # A SAFE decision with CHOICE: NONE is well-formed, not a parse failure.
        bad = r["ok"] and (dec is None or (dec == "ATTEMPT" and pos is None))
        if bad:
            fails += 1
        out.append(dict(
            focal=r["focal"], pair_id=r["pair_id"], level=r["level"],
            stimulus_id=sid, family=r["family"],
            partner_same=int(r["partner_same"]), safe=r["safe"], trial=r["trial"],
            perm_id=r["perm_id"],
            decision=(dec or ""), attempt=("" if dec is None else int(dec == "ATTEMPT")),
            chosen_item=("" if item is None else item),
            chosen_position=("" if pos is None else pos + 1),
            stim_self_match=r["stim_self_match"],
            high_own_minus_cross=r["high_own_minus_cross"],
            ok=r["ok"], parse_ok=(not bad and dec is not None), error=r["error"],
            api_model=r["api_model"], ts=r["ts"],
            raw=r["raw"].replace("\n", " | ")[:900]))

    p = os.path.join(S.DATA, "stageC_pilot_results.csv")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    print(f"\nwrote {p}  ({len(out):,} rows)")
    print(f"  transport ok  : {sum(1 for r in out if r['ok']):,}/{len(out):,}")
    print(f"  parsed ok     : {sum(1 for r in out if r['parse_ok']):,}/{len(out):,}")
    print(f"  PARSE FAILURES: {fails} (kept with parse_ok=False)")
    att = [r for r in out if r["attempt"] != ""]
    if att:
        print(f"  overall ATTEMPT rate: {sum(r['attempt'] for r in att)/len(att):.3f}")


if __name__ == "__main__":
    main()
