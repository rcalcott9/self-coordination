"""Stage B v3 - two separate public baselines, single focal model.

  auditor  : Claude Opus 5 predicts GPT-5.5's self-self match rate.
             (frozen P.auditor_prompt('gpt'), actor = P.OTHER['gpt'] = claude)
  salience : Claude Opus 5 only rates generic salience. The frozen runner uses
             BOTH models as raters; with one focal model the NON-FOCAL rater is
             used alone, so the focal model never rates stimuli it will later be
             tested on. Prompt itself is P.SALIENCE_PROMPT, unchanged.

Arms stay separate calls in separate conversations, as in Study 1.
"""
import argparse, json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); EXP=os.path.dirname(HERE)
os.environ.setdefault("PSC_EXP_DIR", EXP)
sys.path.insert(0, os.path.expanduser(
  "~/Desktop/Coordination/Self_Coordination/policy_specific_self_coordination_20260812_1401/code"))
import psc_common as P

FOCAL = os.environ.get("S1_FOCAL", "gpt")   # default unchanged: the 2026-09-05 GPT-5.5 run reproduces exactly
RATER = P.OTHER[FOCAL]          # claude


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=("auditor","salience","both"), default="both")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=P.WORKERS)
    ap.add_argument("--stimuli-from", default=None)
    a = ap.parse_args()

    sids = [r["stimulus_id"] for r in P.load_manifest()]
    if a.stimuli_from:
        keep = set(json.load(open(a.stimuli_from))["retained"])
        sids = [s for s in sids if s in keep]
    images = P.load_images(sids)

    for arm in (("auditor","salience") if a.arm=="both" else (a.arm,)):
        if arm == "auditor":
            cells=[{"actor":RATER,"focal":FOCAL,"arm":"auditor","sid":s} for s in sids]
            seed=P.SEEDS["B_auditor"]
            prompt_for=lambda job: P.auditor_prompt(job["focal"])
            def parse_for(job, raw):
                prob, side = P.parse_probability(raw)
                return {"prob":prob,"side":side,"valid":prob is not None}
        else:
            cells=[{"actor":RATER,"arm":"salience","sid":s} for s in sids]
            seed=P.SEEDS["B_salience"]
            prompt_for=lambda job: P.SALIENCE_PROMPT
            def parse_for(job, raw):
                v=P.parse_salience(raw); return {"salience":v,"valid":v is not None}
        jobs=P.build_jobs(cells, a.n, seed)
        for j in jobs: j["seed"]=seed
        print(f"\n=== STAGE B / {arm} (v3, single focal) ===")
        print(f"  focal={P.DISPLAY[FOCAL]}   rater/auditor={P.DISPLAY[RATER]}")
        print(f"  prompt sha8: {P.sha8(P.auditor_prompt(FOCAL) if arm=='auditor' else P.SALIENCE_PROMPT)}")
        print(f"  stimuli {len(sids)}   trials {len(jobs)}"
              f"{'   [DRY RUN]' if a.dry_run else ''}\n", flush=True)
        P.run_stage("B", jobs, prompt_for, parse_for, images, a.dry_run, a.workers, tag=arm)


if __name__ == "__main__":
    main()
