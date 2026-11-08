"""
STAGE A - fresh self-play ground truth on GPT-5.5 and Claude Opus 5.

Each trial is an independent, one-shot call with no conversation history. The model
sees one composite image (two forms side by side) and answers with the POSITION it
chose; the A/B identity coding never reaches the model and is recoded afterwards.

The prompt is step1_form_choice.PROMPT verbatim (sha8 3003ae1b), so these numbers
are directly comparable to the confirmed n=60 battery collected on GPT-5.4 /
Claude Opus 4.8. Model version is the only thing that changed.

Run:  python3 stage_a_ground_truth.py --dry-run
      python3 stage_a_ground_truth.py --n 60
"""
import argparse
import psc_common as P


def prompt_for(job):
    return P.STAGE_A_PROMPT


def parse_for(job, raw):
    side = P.parse_side(raw)
    return {"side": side, "valid": bool(side)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60, help="valid trials per model x stimulus")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=P.WORKERS)
    ap.add_argument("--models", nargs="*", default=None,
                    choices=["gpt", "claude"],
                    help="restrict to these actors; default = both")
    ap.add_argument("--stimuli", nargs="*", default=None)
    args = ap.parse_args()

    sids = args.stimuli or P.BATTERY
    P.build_manifest()
    actors = tuple(args.models) if args.models else ("gpt", "claude")
    cells = [{"actor": m, "sid": s} for m in actors for s in sids]
    jobs = P.build_jobs(cells, args.n, P.SEEDS["A"])
    for j in jobs:
        j["seed"] = P.SEEDS["A"]

    print("=== STAGE A - fresh self-play ground truth ===")
    print(f"models   : {P.DISPLAY['gpt']} ({P.GPT_ID}), {P.DISPLAY['claude']} ({P.CLAUDE_ID})")
    print(f"stimuli  : {len(sids)}  ({', '.join(sids)})")
    print(f"prompt   : sha8={P.sha8(P.STAGE_A_PROMPT)}  (step1 canonical = 3003ae1b)")
    print(f"seed     : {P.SEEDS['A']}   AB/BA exactly {args.n // 2}/{args.n // 2} per cell")
    print(f"trials   : {len(jobs)}{'   [DRY RUN]' if args.dry_run else ''}\n", flush=True)

    P.run_stage("A", jobs, prompt_for, parse_for, P.load_images(sids),
                args.dry_run, args.workers)


if __name__ == "__main__":
    main()
