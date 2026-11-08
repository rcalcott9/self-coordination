"""Stage A1 SCREEN - single focal model, depth 15, drop-only.

Reuses the frozen Study 1 code path verbatim (prompt sha8 3003ae1b, build_jobs,
run_stage, parse_side). The ONLY differences from stage_a_ground_truth.py are:
  * load_manifest() instead of build_manifest()  (our 120-stimulus battery)
  * one focal model
  * depth from --n
A1 output is used ONLY to drop stimuli. It never enters a pair estimate.
"""
import argparse, os, sys
os.environ.setdefault("PSC_EXP_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.expanduser(
    "~/Desktop/Coordination/Self_Coordination/policy_specific_self_coordination_20260812_1401/code"))
import psc_common as P


def prompt_for(job): return P.STAGE_A_PROMPT
def parse_for(job, raw):
    side = P.parse_side(raw)
    return {"side": side, "valid": bool(side)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--model", default="gpt", choices=["gpt", "claude"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=P.WORKERS)
    ap.add_argument("--tag", default="A1")
    ap.add_argument("--stimuli-from", default=None,
                    help="JSON file with a `retained` list; restricts the cells")
    a = ap.parse_args()

    man = P.load_manifest()
    sids = [r["stimulus_id"] for r in man]
    if a.stimuli_from:
        import json
        keep = set(json.load(open(a.stimuli_from))["retained"])
        sids = [s for s in sids if s in keep]
    cells = [{"actor": a.model, "sid": s} for s in sids]
    jobs = P.build_jobs(cells, a.n, P.SEEDS["A"])
    for j in jobs: j["seed"] = P.SEEDS["A"]

    print("=== STAGE A1 SCREEN (drop-only) ===")
    print(f"focal    : {P.DISPLAY[a.model]} ({P.GPT_ID if a.model=='gpt' else P.CLAUDE_ID})")
    print(f"stimuli  : {len(sids)}    depth: {a.n}")
    print(f"prompt   : sha8={P.sha8(P.STAGE_A_PROMPT)}  (canonical 3003ae1b)")
    print(f"EXP dir  : {P.EXP}")
    print(f"trials   : {len(jobs)}{'   [DRY RUN]' if a.dry_run else ''}\n", flush=True)
    P.run_stage("A", jobs, prompt_for, parse_for, P.load_images(sids),
                a.dry_run, a.workers, tag=a.tag)


if __name__ == "__main__":
    main()
