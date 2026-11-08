"""
Opus 4.7 - fills the Anthropic gap between 4.6 (competence-gate fail) and 4.8.

PROCEDURE, identical to the other rungs and decided before any call:
  1. amended competence gate (>=1 control with a transferable convention; valid-output,
     mapping fidelity and payoff sensitivity unchanged)
  2. Stage A n=60 on the original 15-stimulus battery
  3. Stage B auditor + generic salience, n=30, auditor partner gpt-5.5 (the constant
     modern external observer used for all Anthropic rungs)
  4. frozen selector; STOP if fewer than 3 pairs are SELECTED after non-reuse
  5. if <3 selected, retry once on the frozen 45-stimulus universe (the same remedy
     already applied to GPT-5 and Opus 4.5 - not a new decision)
  6. FROZEN payoff-saturation screen on the actual selected stimuli, exactly as
     specified for Opus 4.5: N=10 per stimulus x payoff, SAFE in {3,9}, saturated at
     >=95% ATTEMPT at SAFE=9. Applied here because BOTH earlier Claude rungs saturated
     and the small gate-D screen proved unreliable at n=12.
  7. full Stage C, SAFE {3,5,7,9}, n=30, only if the screen passes

No threshold, selector rule or payoff grid is modified.

Run:  python3 run_opus47.py
"""
import csv, glob, json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ladder_models import LADDER, CODE, env_for
from run_expansion_select import EXPANSION, saturation_screen, SATURATION_LIMIT

KEY = "opus47"
ROLE = "claude"


def sh(cmd, env, log, label):
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.run(cmd, cwd=CODE, env=env, stdout=fh,
                            stderr=subprocess.STDOUT).returncode
    print(f"    {label:34} rc={rc}  {time.time()-t0:6.0f}s")
    return rc


def base_env(expanded=False):
    m = next(x for x in LADDER if x["key"] == KEY)
    env = env_for(m)
    env["PSC_GPT_ID"] = "gpt-5.5"
    env["PSC_GPT_NAME"] = "GPT-5.5"
    env["PSC_GPT_SURFACE"] = "reasoning"
    if expanded:
        env["PSC_EXTRA_STIMULI"] = ",".join(EXPANSION)
        env["PSC_EXP_DIR"] = env["PSC_EXP_DIR"] + "_expanded"
    return m, env


def select_count(exp):
    p = os.path.join(exp, "pairs", "approved_pairs.csv")
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def mark_approved(exp, sel):
    mp = os.path.join(exp, "matched_pairs.csv")
    rows = list(csv.DictReader(open(mp)))
    ids = {p["pair_id"] for p in sel}
    f = list(rows[0]) + ([] if "approved" in rows[0] else ["approved"])
    for r in rows:
        r["approved"] = "True" if r["pair_id"] in ids else "False"
    with open(mp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=f, restval="")
        w.writeheader(); w.writerows(rows)


def main():
    L = lambda n: os.path.join(ROOT, "run_logs", f"{KEY}_{n}.log")
    rec = {"model": KEY}

    # ---- 1. competence gate ------------------------------------------------
    m, env = base_env()
    os.makedirs(os.path.join(env["PSC_EXP_DIR"], "data"), exist_ok=True)
    print(f"=== {m['display']} ({m['model_id']}) ===\n  competence gate")
    sh([sys.executable, "-c", "import psc_common as P; P.build_manifest(write=True)"],
       env, L("manifest"), "manifest")
    import competence_gate as G
    sh([sys.executable, "stage_a_ground_truth.py", "--n", str(G.N_STAGE_A),
        "--models", ROLE, "--stimuli", *G.CONTROLS], env, L("gate_stageA"),
       "gate Stage A")
    sh([sys.executable, "stage_c_betting.py", "--n", str(G.N_STAGE_C),
        "--safe-values", *[str(s) for s in G.SAFES], "--models", ROLE,
        "--all-battery", "--stimuli", *G.CONTROLS], env, L("gate_stageC"),
       "gate Stage C")
    gate = G.score(env["PSC_EXP_DIR"], m)
    rec["gate"] = gate
    G.show({**gate, "display": m["display"]})
    if not gate.get("passes_all"):
        rec["stopped_at"] = "competence_gate"
        print("  STOP: task-incompetent for this paradigm.")
        return _save(rec)

    # archive gate data so the real Stage A starts clean
    import shutil
    gd = os.path.join(env["PSC_EXP_DIR"], "competence_gate_data")
    os.makedirs(gd, exist_ok=True)
    for f in glob.glob(os.path.join(env["PSC_EXP_DIR"], "data", "stage*")):
        shutil.move(f, os.path.join(gd, os.path.basename(f)))

    # ---- 2-5. pipeline on 15, then 45 if needed ----------------------------
    for expanded in (False, True):
        m, env = base_env(expanded)
        exp = env["PSC_EXP_DIR"]
        tag = "45-stimulus" if expanded else "15-stimulus"
        os.makedirs(os.path.join(exp, "data"), exist_ok=True)
        print(f"\n  --- {tag} universe ---")
        stim = (["--stimuli", *EXPANSION] if expanded else [])
        if expanded:
            for pat in ("stageA_*.csv", "stageB_auditor_*.csv", "stageB_salience_*.csv"):
                for f in glob.glob(os.path.join(base_env()[1]["PSC_EXP_DIR"], "data", pat)):
                    if "_DRY" in f:
                        continue
                    dst = os.path.join(exp, "data", "orig15_" + os.path.basename(f))
                    if not os.path.exists(dst):
                        shutil.copy(f, dst)
        sh([sys.executable, "stage_a_ground_truth.py", "--n", "60", "--models", ROLE,
            *stim], env, L(f"stageA_{tag}"), f"Stage A ({tag})")
        sh([sys.executable, "stage_b_perception.py", "--arm", "both", "--n", "30",
            "--focal", ROLE, *stim], env, L(f"stageB_{tag}"), f"Stage B ({tag})")
        if expanded:
            from run_expansion_select import merge
            merge(exp, "stageA", "orig15_stageA_*.csv", "stageA_*.csv")
            merge(exp, "stageB_auditor", "orig15_stageB_auditor_*.csv",
                  "stageB_auditor_*.csv")
            merge(exp, "stageB_salience", "orig15_stageB_salience_*.csv",
                  "stageB_salience_*.csv")
        sh([sys.executable, "analyze_stage_ab.py"], env, L(f"analyze_{tag}"),
           "analyze A+B")
        sh([sys.executable, "select_pairs_replication.py"], env, L(f"select_{tag}"),
           "frozen selector")
        sel = select_count(exp)
        print(f"    selected {len(sel)} pairs")
        rec[f"n_selected_{tag}"] = len(sel)
        if len(sel) >= 3:
            rec["universe"] = tag
            rec["pairs"] = [f"{p['stimulus_high']} > {p['stimulus_low']}" for p in sel]
            break
        if expanded:
            rec["stopped_at"] = "selection_below_minimum"
            print("    STOP: <3 selected pairs even on the expanded universe.")
            return _save(rec)

    mark_approved(exp, sel)

    # ---- 6. frozen payoff-saturation screen --------------------------------
    stimuli = sorted({s for p in sel for s in (p["stimulus_high"], p["stimulus_low"])})
    sat, rate = saturation_screen(env, ROLE, exp, stimuli, L("payoff_screen"))
    rec["screen_attempt_rate_at_safe9"] = rate
    rec["payoff_saturated"] = sat
    print(f"\n    payoff screen: ATTEMPT at SAFE=9 = {rate}  (limit {SATURATION_LIMIT})")
    if sat is None or sat:
        rec["stopped_at"] = "payoff_saturation"
        print("    STOP: Stage C uninformative due to payoff saturation.")
        return _save(rec)

    # ---- 7. Stage C --------------------------------------------------------
    rec["stage_c_rc"] = sh([sys.executable, "stage_c_betting.py", "--n", "30",
                            "--models", ROLE], env, L("stageC"),
                           "Stage C (n=30, safe {3,5,7,9})")
    rec["primary_rc"] = sh([sys.executable, "analyze_replication_primary.py"], env,
                           L("primary"), "primary analysis")
    _save(rec)


def _save(rec):
    p = os.path.join(ROOT, "analysis", "opus47_run.json")
    json.dump(rec, open(p, "w"), indent=2, default=str)
    print(f"\n-> {p}")


if __name__ == "__main__":
    main()
