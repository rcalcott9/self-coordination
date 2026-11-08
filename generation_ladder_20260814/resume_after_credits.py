"""
Resume after the OpenAI credit exhaustion.

WHAT FAILED. Opus 4.5's expansion salience arm needs GPT-5.5 as its second generic-
salience rater. 1,734 of those calls returned 429 "no credits remaining", so the arm is
incomplete for the gpt rater while the claude rater finished (900/900 valid). GPT-5's
own expansion Stage A/B completed before the exhaustion and is untouched.

WHAT THIS DOES
  1. Opus 4.5 - re-run ONLY the salience arm on the 30 expansion stimuli. The failed
     rows carry valid_response=False / included_in_analysis=False, so they are already
     excluded from analysis; the fresh file supersedes them. No measure is changed:
     salience remains the two-rater pooled quantity it has always been.
  2. Opus 4.5 - merge, frozen selector, then the FROZEN payoff-saturation screen
     (N=10, SAFE in {3,9}, saturated if >=95% ATTEMPT at SAFE=9), then full Stage C
     only if it passes.
  3. GPT-5 - fresh Stage C on the 5 pairs the frozen selector already chose from the
     expanded universe, then the primary analysis. Reported SEPARATELY from the earlier
     2-pair run, which is preserved as a failed-initial-battery result.

No threshold, no payoff grid, no selector logic is modified anywhere in this file.

Run:  python3 resume_after_credits.py
"""
import csv, glob, json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ladder_models import LADDER, CODE, env_for
from run_expansion_select import (EXPANSION, PARTNER, merge, saturation_screen,
                                  SCREEN_N, SCREEN_SAFES, SATURATION_LIMIT)


def sh(cmd, env, log, label):
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.run(cmd, cwd=CODE, env=env, stdout=fh,
                            stderr=subprocess.STDOUT).returncode
    print(f"    {label:36} rc={rc}  {time.time()-t0:6.0f}s")
    return rc


def env_for_expanded(key):
    m = next(x for x in LADDER if x["key"] == key)
    env = env_for(m)
    a, av, b, bv, c, cv = PARTNER[m["provider"]]
    env[a], env[b], env[c] = av, bv, cv
    env["PSC_EXTRA_STIMULI"] = ",".join(EXPANSION)
    env["PSC_EXP_DIR"] = env["PSC_EXP_DIR"] + "_expanded"
    return m, env, ("gpt" if m["provider"] == "openai" else "claude")


def main():
    out = []
    L = lambda k, n: os.path.join(ROOT, "run_logs", f"{k}_exp_{n}.log")

    # ---------------------------------------------------------------- GPT-5 ---
    m, env, role = env_for_expanded("gpt5")
    exp = env["PSC_EXP_DIR"]
    print(f"\n=== {m['display']} - Stage C on the expanded selection ===")
    sel = list(csv.DictReader(open(os.path.join(exp, "pairs", "approved_pairs.csv"))))
    print(f"    {len(sel)} approved pairs: "
          f"{[p['stimulus_high'] + '>' + p['stimulus_low'] for p in sel]}")
    rec = dict(model="gpt5", display=m["display"], n_pairs=len(sel),
               pairs=[f"{p['stimulus_high']} > {p['stimulus_low']}" for p in sel])
    # The selector writes approved_pairs.csv; the Stage C runner reads the `approved`
    # column of matched_pairs.csv. When the selector is invoked outside the pipeline
    # runner that column is never set, and Stage C refuses to start. Mark it here.
    _mp = os.path.join(exp, "matched_pairs.csv")
    _rows = list(csv.DictReader(open(_mp)))
    _ids = {p["pair_id"] for p in sel}
    _f = list(_rows[0]) + ([] if "approved" in _rows[0] else ["approved"])
    for _r in _rows:
        _r["approved"] = "True" if _r["pair_id"] in _ids else "False"
    with open(_mp, "w", newline="") as _fh:
        _w = csv.DictWriter(_fh, fieldnames=_f, restval="")
        _w.writeheader(); _w.writerows(_rows)
    rec["stage_c_rc"] = sh([sys.executable, "stage_c_betting.py", "--n", "30",
                            "--models", role], env, L("gpt5", "stageC"),
                           "Stage C (n=30, safe {3,5,7,9})")
    rec["primary_rc"] = sh([sys.executable, "analyze_replication_primary.py"], env,
                           L("gpt5", "primary"), "primary analysis")
    out.append(rec)

    # ------------------------------------------------------------- Opus 4.5 ---
    m, env, role = env_for_expanded("opus45")
    exp = env["PSC_EXP_DIR"]
    print(f"\n=== {m['display']} - repair salience, then select ===")
    rec = dict(model="opus45", display=m["display"])
    rec["salience_rc"] = sh([sys.executable, "stage_b_perception.py", "--arm",
                             "salience", "--n", "30", "--stimuli", *EXPANSION], env,
                            L("opus45", "stageB_salience_retry"),
                            "Stage B salience RETRY (30 new)")

    merge(exp, "stageA", "orig15_stageA_*.csv", "stageA_*.csv")
    merge(exp, "stageB_auditor", "orig15_stageB_auditor_*.csv", "stageB_auditor_*.csv")
    merge(exp, "stageB_salience", "orig15_stageB_salience_*.csv",
          "stageB_salience_*.csv")

    if sh([sys.executable, "analyze_stage_ab.py"], env, L("opus45", "analyze_ab"),
          "analyze A+B (45 stimuli)") != 0:
        rec["stopped_at"] = "analyze_ab"; out.append(rec); _save(out); return

    rc_sel = sh([sys.executable, "select_pairs_replication.py"], env,
                L("opus45", "select"), "frozen selector (unchanged)")
    apf = os.path.join(exp, "pairs", "approved_pairs.csv")
    sel = list(csv.DictReader(open(apf))) if os.path.exists(apf) else []
    rec["n_selected"] = len(sel)
    rec["pairs"] = [f"{p['stimulus_high']} > {p['stimulus_low']}" for p in sel]
    print(f"    selected {len(sel)}: {rec['pairs']}")
    if rc_sel != 0 or len(sel) < 3:
        print("    STOP: fewer than 3 selected pairs. No Stage C, no threshold change.")
        rec["stopped_at"] = "selection_below_minimum"; out.append(rec); _save(out); return

    mp = os.path.join(exp, "matched_pairs.csv")
    rows = list(csv.DictReader(open(mp)))
    ids = {p["pair_id"] for p in sel}
    fields = list(rows[0]) + ([] if "approved" in rows[0] else ["approved"])
    for r in rows:
        r["approved"] = "True" if r["pair_id"] in ids else "False"
    with open(mp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, restval="")
        w.writeheader(); w.writerows(rows)

    stim = sorted({s for p in sel for s in (p["stimulus_high"], p["stimulus_low"])})
    sat, rate = saturation_screen(env, role, exp, stim, L("opus45", "payoff_screen"))
    rec["screen_attempt_rate_at_safe9"] = rate
    rec["payoff_saturated"] = sat
    print(f"    payoff screen: ATTEMPT at SAFE=9 = {rate}  (limit {SATURATION_LIMIT})")
    if sat is None or sat:
        print("    STOP: Stage C uninformative due to payoff saturation on the "
              "selected stimulus distribution.")
        rec["stopped_at"] = "payoff_saturation"; out.append(rec); _save(out); return

    rec["stage_c_rc"] = sh([sys.executable, "stage_c_betting.py", "--n", "30",
                            "--models", role], env, L("opus45", "stageC"),
                           "Stage C (n=30, safe {3,5,7,9})")
    rec["primary_rc"] = sh([sys.executable, "analyze_replication_primary.py"], env,
                           L("opus45", "primary"), "primary analysis")
    out.append(rec)
    _save(out)


def _save(out):
    p = os.path.join(ROOT, "analysis", "expansion_final.json")
    json.dump(out, open(p, "w"), indent=2, default=str)
    print(f"\n-> {p}")


if __name__ == "__main__":
    main()
