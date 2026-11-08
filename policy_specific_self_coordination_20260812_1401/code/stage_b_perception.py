"""
STAGE B - the public-salience control, in two INDEPENDENT arms.

arm=auditor    -> auditor_prediction. The OTHER model predicts the focal model's
               self-self match rate; Claude predicts GPT-GPT, GPT predicts
               Claude-Claude. The auditor sees the stimulus, the game description
               and the identity of the target model - never empirical rates, never
               the target's outputs or choice distributions.

               This is NOT a pure public baseline. The auditor is a different model
               with its own policy and may have learned model-specific information
               about GPT or Claude, so it can partly anticipate the focal model's
               reliability for reasons unavailable from stimulus structure alone.
               Read it as "an external model's prediction of the focal model's
               self-coordination reliability", not "how focal the stimulus is".

arm=salience   -> generic_salience. Either model rates how obvious the focal choice
               would be to a *generic* capable AI player. No model is named, so this
               is the measure that comes closest to public stimulus structure alone.
               Both models rate every stimulus; reported per rater and pooled.

A pair matched on generic_salience but not on auditor_prediction is only partly
matched - the strongest pair differs substantially in true self-match while
differing little in BOTH.

The two arms are separate calls in separate conversations. Combining them would
let the probability answer anchor the salience answer and vice versa; prior
project practice only ever combined a probability with its own most-likely-choice,
which is one construct, not two.

Run:  python3 stage_b_perception.py --arm auditor --dry-run
      python3 stage_b_perception.py --arm salience --n 30
      python3 stage_b_perception.py --arm both --n 30
"""
import argparse
import psc_common as P


def make_auditor(args, sids):
    focals = tuple(args.focal) if args.focal else ("gpt", "claude")
    cells = [{"actor": P.OTHER[f], "focal": f, "arm": "auditor", "sid": s}
             for f in focals for s in sids]
    jobs = P.build_jobs(cells, args.n, P.SEEDS["B_auditor"])
    for j in jobs:
        j["seed"] = P.SEEDS["B_auditor"]

    def prompt_for(job):
        return P.auditor_prompt(job["focal"])

    def parse_for(job, raw):
        prob, side = P.parse_probability(raw)
        return {"prob": prob, "side": side, "valid": prob is not None}

    return jobs, prompt_for, parse_for


def make_salience(args, sids):
    cells = [{"actor": m, "arm": "salience", "sid": s}
             for m in ("gpt", "claude") for s in sids]
    jobs = P.build_jobs(cells, args.n, P.SEEDS["B_salience"])
    for j in jobs:
        j["seed"] = P.SEEDS["B_salience"]

    def prompt_for(job):
        return P.SALIENCE_PROMPT

    def parse_for(job, raw):
        v = P.parse_salience(raw)
        return {"salience": v, "valid": v is not None}

    return jobs, prompt_for, parse_for


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=("auditor", "salience", "both"), default="both")
    ap.add_argument("--n", type=int, default=30, help="predictions per cell")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=P.WORKERS)
    ap.add_argument("--focal", nargs="*", default=None, choices=["gpt", "claude"],
                    help="restrict the auditor arm to these focal models; default = both")
    ap.add_argument("--stimuli", nargs="*", default=None)
    args = ap.parse_args()

    sids = args.stimuli or P.BATTERY
    P.build_manifest()
    images = P.load_images(sids)
    arms = ("auditor", "salience") if args.arm == "both" else (args.arm,)

    for arm in arms:
        jobs, prompt_for, parse_for = (make_auditor if arm == "auditor" else make_salience)(args, sids)
        print(f"\n=== STAGE B / {arm} ===")
        if arm == "auditor":
            print(f"  {P.DISPLAY['claude']} predicts {P.DISPLAY['gpt']} self-self")
            print(f"  {P.DISPLAY['gpt']} predicts {P.DISPLAY['claude']} self-self")
            print(f"  prompt sha8 (focal=gpt)   : {P.sha8(P.auditor_prompt('gpt'))}")
            print(f"  prompt sha8 (focal=claude): {P.sha8(P.auditor_prompt('claude'))}")
        else:
            print(f"  both models rate generic salience (no focal model named)")
            print(f"  prompt sha8: {P.sha8(P.SALIENCE_PROMPT)}")
        print(f"  stimuli: {len(sids)}   trials: {len(jobs)}"
              f"{'   [DRY RUN]' if args.dry_run else ''}\n", flush=True)
        P.run_stage("B", jobs, prompt_for, parse_for, images,
                    args.dry_run, args.workers, tag=arm)


if __name__ == "__main__":
    main()
