"""
Opus 4.6 - resume the full-battery run after the OpenAI credit exhaustion.

WHAT FAILED (2026-08-16/17). Stage A finished clean: 2,700 trials on all 45 stimuli,
0 unparseable, 0 lost, 0 API errors. Stage B then hit exhausted OpenAI credits:

    stageB_auditor_20260816_224444.csv    1,350 trials, 0 valid
                                          (2,697 x 429 insufficient_quota, 3 conn errors)
    stageB_salience_20260817_022446.csv   died at 164 rows
                                          (60 valid claude, 104 failed gpt)

Both arms need OpenAI - the auditor of a Claude-focal rung IS GPT-5.5, and generic
salience is a two-rater pooled quantity. Without them analyze_stage_ab.py writes no
matched_pairs.csv and the frozen selector cannot run. Credits were topped up 2026-08-17.

WHAT THIS DOES
  1. Re-runs Stage B, both arms, on all 45 stimuli (--focal claude, n=30) - the same
     invocation that failed. analyze_stage_ab.py resolves each arm with newest(), one
     file per stem, so the fresh files SUPERSEDE the failed ones outright: no partial
     rows are merged and the 60 valid claude salience rows cannot double-count.
  2. Checks validity per arm and STOPS below 95%, rather than handing a
     credit-shaped hole to the selector the way the overnight run did.
  3. Hands off to opus46_full.main(): merge -> analyze A+B -> frozen selector
     -> frozen payoff-saturation screen (Gate D, on the ACTUAL selected stimuli)
     -> Stage C.

No threshold, ranking rule, payoff grid or prompt is modified. The failed rows are
kept in place; they already carry valid_response=False / included_in_analysis=False.

STANDING OF THE ORIGINAL GATE VERDICT. Unchanged as a record of what a 48-trial screen
showed. Stage A has since established that its Gate C conclusion does not generalise -
25 of 45 stimuli carry a clean form rule and A_sd 0.232 is the largest of any rung,
while the two stimuli the gate looked at are both position fallback on this model
(analysis/opus46_stageA_verdict.md). Gate D - zero payoff response - is what this run
tests properly, on selected stimuli rather than those two.

Run:  python3 opus46_resume.py
"""
import csv, glob, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ladder_models import CODE
from run_expansion_select import EXPANSION

import opus46_full

EXP = opus46_full.EXP
ROLE = opus46_full.ROLE
MIN_VALID = 0.95            # frozen here; the overnight run had 0.00 on the auditor arm


def sh(cmd, e, log, label):
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.run(cmd, cwd=CODE, env=e, stdout=fh,
                            stderr=subprocess.STDOUT).returncode
    print(f"    {label:38} rc={rc}  {time.time()-t0:6.0f}s", flush=True)
    return rc


def newest(stem):
    fs = [f for f in glob.glob(os.path.join(EXP, "data", f"{stem}_*.csv"))
          if "_DRY" not in f and "MERGED" not in f]
    return max(fs, key=os.path.getmtime) if fs else None


def validity(stem):
    """Share of rows that survived, on the file analyze_stage_ab will actually read."""
    f = newest(stem)
    if not f:
        return None, 0, None
    rows = list(csv.DictReader(open(f)))
    ok = sum(1 for r in rows if r["valid_response"] == "True")
    return (ok / len(rows) if rows else 0.0), len(rows), os.path.basename(f)


def main():
    e = opus46_full.env()
    L = lambda n: os.path.join(ROOT, "run_logs", f"opus46_resume_{n}.log")

    print("=== Opus 4.6 resume: Stage B, both arms, 45 stimuli ===")
    print(f"    superseding auditor  : {os.path.basename(newest('stageB_auditor') or '-')}")
    print(f"    superseding salience : {os.path.basename(newest('stageB_salience') or '-')}")

    # No --stimuli: PSC_EXTRA_STIMULI puts all 45 in P.BATTERY, which is how the
    # failed run was invoked. --focal claude keeps the auditor arm to GPT-5.5 -> 4.6.
    sh([sys.executable, "stage_b_perception.py", "--arm", "both", "--n", "30",
        "--focal", ROLE], e, L("stageB"), "Stage B both arms (n=30, 45 stimuli)")

    stop = False
    for stem, expect in (("stageB_auditor", 1350), ("stageB_salience", 2700)):
        rate, n, fn = validity(stem)
        if rate is None:
            print(f"    {stem:22} NO FILE WRITTEN")
            stop = True
            continue
        flag = "ok" if rate >= MIN_VALID else f"BELOW {MIN_VALID}"
        print(f"    {stem:22} {n:5} rows  valid {rate:.3f}  {flag}   {fn}")
        if rate < MIN_VALID:
            stop = True
    if stop:
        print("\n  STOP: Stage B incomplete. Not handing a partial arm to the selector.")
        return

    print("\n=== handing off to opus46_full ===", flush=True)
    return opus46_full.main()


if __name__ == "__main__":
    main()
