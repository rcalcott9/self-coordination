"""
STAGE C - the primary experiment: self-play betting / opt-out.

The focal model is told it is coordinating with another independent instance of
ITSELF, sees the stimulus, and chooses ATTEMPT (10 points on a match, 0 on a
mismatch) or SAFE (a guaranteed payoff). It never sees ground-truth match rates or
auditor predictions.

Requiring CHOICE alongside DECISION lets us estimate coordination CONDITIONAL on
attempting - the thing an attempt is a bet about - rather than assuming it equals
the unconditional Stage-A rate.

--stimuli defaults to the union of stimuli in the approved matched-pair table
(matched_pairs.csv), so Stage C is run only on the pairs the design selected.

Payoff grid: default {3,5,7,9}. analyze_stage_ab.py prints a recommendation if the
selected pairs' true self-match values cluster somewhere that grid brackets poorly;
--safe-values overrides it, and the chosen grid is echoed in the run header and
stored on every row.

Run:  python3 stage_c_betting.py --dry-run
      python3 stage_c_betting.py --n 30
      python3 stage_c_betting.py --n 30 --safe-values 5 6 7 8
"""
import argparse, csv, os, sys
import psc_common as P

PAIRS_CSV = os.path.join(P.EXP, "matched_pairs.csv")


def stimuli_from_pairs(approved_only=True):
    if not os.path.exists(PAIRS_CSV):
        sys.exit(f"no matched-pair table at {PAIRS_CSV}\n"
                 "Run analyze_stage_ab.py first, then get the pair table approved.")
    rows = list(csv.DictReader(open(PAIRS_CSV)))
    if approved_only:
        rows = [r for r in rows if str(r.get("approved", "")).lower() in ("true", "1", "yes")]
        if not rows:
            sys.exit("matched_pairs.csv has no rows with approved=True.\n"
                     "Stage C must not run on an unapproved pair set.")
    per_model = {}
    for r in rows:
        per_model.setdefault(r["focal_model"], set()).update(
            [r["stimulus_high"], r["stimulus_low"]])
    return per_model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30, help="valid calls per model x stimulus x payoff")
    ap.add_argument("--safe-values", type=int, nargs="*", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=P.WORKERS)
    ap.add_argument("--models", nargs="*", default=None,
                    choices=["gpt", "claude"],
                    help="restrict to these actors; default = both")
    ap.add_argument("--stimuli", nargs="*", default=None,
                    help="override; default = union of approved matched-pair stimuli")
    ap.add_argument("--all-battery", action="store_true",
                    help="ignore matched_pairs.csv and run the full 15-stimulus battery")
    args = ap.parse_args()

    safes = args.safe_values or P.SAFE_VALUES_DEFAULT
    if args.safe_values and sorted(args.safe_values) != sorted(P.SAFE_VALUES_DEFAULT):
        print(f"!! payoff grid overridden: {P.SAFE_VALUES_DEFAULT} -> {sorted(safes)}")
        print("   The rationale must have been printed and approved (see spec §7).\n")

    P.build_manifest()
    if args.stimuli:
        per_model = {m: set(args.stimuli) for m in ("gpt", "claude")}
    elif args.all_battery:
        per_model = {m: set(P.BATTERY) for m in ("gpt", "claude")}
    else:
        per_model = stimuli_from_pairs()

    if args.models:
        per_model = {m: v for m, v in per_model.items() if m in args.models}
    cells = [{"actor": m, "sid": s, "safe": v}
             for m, sset in per_model.items() for s in sorted(sset) for v in safes]
    jobs = P.build_jobs(cells, args.n, P.SEEDS["C"])
    for j in jobs:
        j["seed"] = P.SEEDS["C"]

    def prompt_for(job):
        return P.betting_prompt(job["safe"])

    def parse_for(job, raw):
        dec, side = P.parse_decision(raw)
        # Valid = a decision was parsed. An ATTEMPT with an unparseable CHOICE is
        # still a valid participation datum; the conditional-coordination analysis
        # simply drops that trial, and the miss is visible in the raw log.
        return {"decision": dec, "side": side, "valid": bool(dec)}

    print("=== STAGE C - self-play betting / opt-out ===")
    print(f"models     : {P.DISPLAY['gpt']} ({P.GPT_ID}), {P.DISPLAY['claude']} ({P.CLAUDE_ID})")
    for m, sset in sorted(per_model.items()):
        print(f"  {P.DISPLAY[m]:16} {len(sset)} stimuli: {', '.join(sorted(sset))}")
    print(f"safe payoffs: {sorted(safes)}   (EV-neutral p = S/10)")
    print(f"prompt sha8 : " + ", ".join(f"S{v}={P.sha8(P.betting_prompt(v))}" for v in sorted(safes)))
    print(f"seed        : {P.SEEDS['C']}   AB/BA exactly {args.n // 2}/{args.n // 2} per cell")
    print(f"cells       : {len(cells)}   trials: {len(jobs)}"
          f"{'   [DRY RUN]' if args.dry_run else ''}\n", flush=True)

    all_sids = sorted(set(s for sset in per_model.values() for s in sset))
    P.run_stage("C", jobs, prompt_for, parse_for, P.load_images(all_sids),
                args.dry_run, args.workers)


if __name__ == "__main__":
    main()
