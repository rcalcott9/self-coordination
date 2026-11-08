"""Stage C v3 - ATTEMPT vs SAFE, single focal model, frozen 24-pair table.

Frozen Study 1 code path: betting_prompt (BASE verbatim), build_jobs, run_stage,
parse_decision. Differences: load_manifest() not build_manifest(), one focal model.
Refuses to run unless the approved pair table matches its recorded SHA-256.
"""
import os, argparse, csv, hashlib, json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); EXP=os.path.dirname(HERE)
os.environ.setdefault("PSC_EXP_DIR", EXP)
sys.path.insert(0, os.path.expanduser(
  "~/Desktop/Coordination/Self_Coordination/policy_specific_self_coordination_20260812_1401/code"))
import psc_common as P

FOCAL = os.environ.get("S1_FOCAL", "gpt")   # default unchanged

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=P.WORKERS)
    a=ap.parse_args()

    # Table, its hash file and the expected row count are all overridable together, so a
    # different focal model gets its OWN frozen table. The hash check itself is NOT relaxed:
    # whichever table is used must still match a recorded sha256 and be fully approved.
    TBL  = os.environ.get("S1_PAIRS_FILE", os.path.join(EXP,"matched_pairs_FROZEN.csv"))
    SHAF = os.environ.get("S1_PAIRS_SHA",  os.path.join(EXP,"PAIRS_SHA256.txt"))
    NPAIR= int(os.environ.get("S1_PAIRS_N", "24"))
    want=open(SHAF).read().strip()
    got=hashlib.sha256(open(TBL,"rb").read()).hexdigest()
    if want!=got: sys.exit(f"FROZEN PAIR TABLE HASH MISMATCH\n  file {TBL}\n  expected {want}\n  got      {got}")
    pairs=list(csv.DictReader(open(TBL)))
    assert all(r["approved"]=="True" for r in pairs), "pair table contains unapproved rows"
    assert len(pairs)==NPAIR, f"pair table has {len(pairs)} rows, expected {NPAIR}"
    sids=sorted({r["stimulus_high"] for r in pairs} | {r["stimulus_low"] for r in pairs})
    # S1_SAFE_GRID overrides the frozen [3,5,7,9] payoff grid. Default unchanged, so both
    # completed Stage C runs reproduce exactly. Used for the dense boundary grid arm.
    safes=[float(x) if "." in x else int(x)
           for x in os.environ["S1_SAFE_GRID"].split(",")] \
          if os.environ.get("S1_SAFE_GRID") else P.SAFE_VALUES_DEFAULT

    cells=[{"actor":FOCAL,"sid":s,"safe":v} for s in sids for v in safes]
    jobs=P.build_jobs(cells, a.n, P.SEEDS["C"])
    for j in jobs: j["seed"]=P.SEEDS["C"]

    print("=== STAGE C v3 - ATTEMPT vs SAFE ===")
    print(f"focal      : {P.DISPLAY[FOCAL]} ({P.GPT_ID if FOCAL=='gpt' else P.CLAUDE_ID})")
    print(f"pairs      : {len(pairs)} (frozen, sha256 {got[:16]}...)")
    print(f"stimuli    : {len(sids)}   payoff grid: {safes}   n/cell: {a.n}")
    print("prompt sha8: " + ", ".join(f"S{v}={P.sha8(P.betting_prompt(v))}" for v in safes))
    print(f"trials     : {len(jobs)}{'   [DRY RUN]' if a.dry_run else ''}\n", flush=True)
    P.run_stage("C", jobs, lambda job: P.betting_prompt(job["safe"]),
                lambda job, raw: (lambda d: {"decision":d[0],"side":d[1],"valid":d[0] is not None})(P.parse_decision(raw)),
                P.load_images(sids), a.dry_run, a.workers)

if __name__ == "__main__":
    main()
