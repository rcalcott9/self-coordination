"""
Stage C ELICITATION ARM — Opus 5, grid 3/5/7/9, depth 12.

Identical to stage_c_v3 except the prompt (elicit_prompt.elicit_betting_prompt) and the
parser (also reads MATCH_PROBABILITY). Same frozen pair table, same AB/BA schedule, same
model settings, same stimuli. Writes to its own tag so it can NEVER pool with the frozen
unprompted run.
"""
import argparse, csv, hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
os.environ.setdefault("PSC_EXP_DIR", EXP)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.expanduser(
    "~/Desktop/Coordination/Self_Coordination/policy_specific_self_coordination_20260812_1401/code"))
import psc_common as P
import elicit_prompt as E

FOCAL = os.environ.get("S1_FOCAL", "claude")
PROB_RE = re.compile(r"MATCH_PROBABILITY:\s*([0-9]{1,3})", re.I)


def parse_for(job, raw):
    dec, side = P.parse_decision(raw)
    m = PROB_RE.search(raw or "")
    prob = int(m.group(1)) if m else None
    if prob is not None and not (0 <= prob <= 100):
        prob = None
    return {"decision": dec, "side": side, "prob": prob,
            "valid": dec is not None and prob is not None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    TBL = os.environ["S1_PAIRS_FILE"]; SHAF = os.environ["S1_PAIRS_SHA"]
    want = open(SHAF).read().strip()
    got = hashlib.sha256(open(TBL, "rb").read()).hexdigest()
    if want != got:
        sys.exit(f"FROZEN PAIR TABLE HASH MISMATCH\n  expected {want}\n  got {got}")
    pairs = list(csv.DictReader(open(TBL)))
    assert all(r["approved"] == "True" for r in pairs), "unapproved rows"
    assert len(pairs) == int(os.environ["S1_PAIRS_N"])
    sids = sorted({r["stimulus_high"] for r in pairs} | {r["stimulus_low"] for r in pairs})
    safes = [int(x) for x in os.environ.get("S1_SAFE_GRID", "3,5,7,9").split(",")]

    cells = [{"actor": FOCAL, "sid": s, "safe": v} for s in sids for v in safes]
    jobs = P.build_jobs(cells, a.n, P.SEEDS["C"])
    for j in jobs:
        j["seed"] = P.SEEDS["C"]
    print("=== STAGE C — ELICITATION ARM (separate from the frozen run) ===")
    print(f"focal      : {P.DISPLAY[FOCAL]} ({P.CLAUDE_ID})")
    print(f"pairs      : {len(pairs)} (frozen, sha256 {got[:16]}...)")
    print(f"stimuli    : {len(sids)}   payoff grid: {safes}   n/cell: {a.n}")
    print("prompt sha8: " + ", ".join(
        f"S{v}={P.sha8(E.elicit_betting_prompt(v))}" for v in safes))
    print(f"caching    : {P.CACHE_PREFIX}   workers: {a.workers}")
    print(f"trials     : {len(jobs)}{'   [DRY RUN]' if a.dry_run else ''}\n", flush=True)
    P.run_stage("C", jobs, lambda job: E.elicit_betting_prompt(job["safe"]), parse_for,
                P.load_images(sids), a.dry_run, a.workers, tag="ELICIT")


if __name__ == "__main__":
    main()
