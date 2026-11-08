"""
Merge the original-15 and expansion-30 raw data, apply the FROZEN selector to the
combined 45-stimulus universe, then take the model-specific Stage C decision.

WHY A MERGE STEP EXISTS. analyze_stage_ab.py resolves its inputs with
newest("stageA_*.csv") - it reads ONE file. The original-battery raw files were copied
into the expansion tree as `orig15_stage*.csv`, which deliberately does NOT match that
glob, so without this step the candidate universe would silently be the 30 new stimuli
only and the original 15 would vanish. This concatenates both into a single
`stageA_MERGED_*.csv` (and likewise for each Stage B arm) written last, so it is the
newest file and the one analyze_stage_ab picks up.

STAGE C DECISIONS
  GPT-5     >=3 selected pairs -> fresh Stage C on the NEW selection, reported
            separately from the earlier 2-pair run. <3 -> stop, no threshold change.
  Opus 4.5  additionally faces a PROSPECTIVELY FROZEN payoff-saturation screen on the
            actual newly selected stimuli, because its earlier Stage C was ATTEMPT on
            240/240 trials:
                SAFE in {3, 9}, N = 10 per selected stimulus x payoff (frozen here)
                if >= 95% of SAFE=9 choices are ATTEMPT -> declare payoff-saturated,
                label "Stage C uninformative due to payoff saturation on the selected
                stimulus distribution", and stop.
            This is NOT a self-knowledge test. It only asks whether Stage C has enough
            outcome variance to be informative. The threshold is fixed before running
            and is not tuned afterwards.

The payoff grid stays {3,5,7,9} for the full Stage C. No new payoff levels.

Run:  python3 run_expansion_select.py
"""
import csv, glob, json, os, subprocess, sys, time
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ladder_models import LADDER, CODE, env_for

REPO = os.path.expanduser("~/Desktop/Coordination/LLM_Coordination/Name_game_experiment")
EXPANSION = [r["stimulus_id"] for r in
             csv.DictReader(open(os.path.join(REPO, "stimuli", "expansion",
                                              "manifest.csv")))]
PARTNER = {"openai": ("PSC_CLAUDE_ID", "claude-opus-5", "PSC_CLAUDE_NAME",
                      "Claude Opus 5", "PSC_CLAUDE_SURFACE", "thinking"),
           "anthropic": ("PSC_GPT_ID", "gpt-5.5", "PSC_GPT_NAME", "GPT-5.5",
                         "PSC_GPT_SURFACE", "reasoning")}

SCREEN_N = 10                 # frozen before running
SCREEN_SAFES = [3, 9]
SATURATION_LIMIT = 0.95       # >= this share of ATTEMPT at SAFE=9 -> saturated


def sh(cmd, env, log, label):
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.run(cmd, cwd=CODE, env=env, stdout=fh,
                            stderr=subprocess.STDOUT).returncode
    print(f"    {label:34} rc={rc}  {time.time()-t0:6.0f}s")
    return rc


def merge(exp, stem, orig_glob, new_glob):
    """Concatenate original-battery and expansion raw files into one newest file."""
    d = os.path.join(exp, "data")
    src = sorted(glob.glob(os.path.join(d, orig_glob)))
    new = [f for f in sorted(glob.glob(os.path.join(d, new_glob)))
           if "_DRY" not in f and "MERGED" not in f and not
           os.path.basename(f).startswith("orig15_")]
    if not new:
        return None
    rows, fields = [], None
    for f in src + new:
        r = list(csv.DictReader(open(f)))
        if r:
            fields = fields or list(r[0])
            rows += r
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(d, f"{stem}_MERGED_{ts}.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, restval="")
        w.writeheader(); w.writerows(rows)
    stim = len({x["stimulus"] for x in rows})
    print(f"    merged {stem:16} {len(src)}+{len(new)} files -> {len(rows):5} rows, "
          f"{stim} stimuli")
    return out


def saturation_screen(env, role, exp, sel_stimuli, log):
    """Frozen variance check on the ACTUAL selected stimuli. Returns (saturated, rate)."""
    rc = sh([sys.executable, "stage_c_betting.py", "--n", str(SCREEN_N),
             "--safe-values", *[str(s) for s in SCREEN_SAFES], "--models", role,
             "--all-battery", "--stimuli", *sel_stimuli], env, log,
            f"payoff screen (n={SCREEN_N}, safe {SCREEN_SAFES})")
    if rc != 0:
        return None, None
    f = max([x for x in glob.glob(os.path.join(exp, "data", "stageC_*.csv"))
             if "_DRY" not in x], key=os.path.getmtime)
    rows = [r for r in csv.DictReader(open(f))
            if r["included_in_analysis"] == "True" and r["actor_model"] == role
            and int(float(r["safe_payoff"])) == 9]
    att = sum(1 for r in rows if r["participation_decision"] == "ATTEMPT")
    rate = att / len(rows) if rows else float("nan")
    os.rename(f, f.replace("stageC_", "payoffscreen_"))
    return (rate >= SATURATION_LIMIT), rate


def main():
    out = []
    for key in ("gpt5", "opus45"):
        m = next(x for x in LADDER if x["key"] == key)
        role = "gpt" if m["provider"] == "openai" else "claude"
        env = env_for(m)
        a, av, b, bv, c, cv = PARTNER[m["provider"]]
        env[a], env[b], env[c] = av, bv, cv
        env["PSC_EXTRA_STIMULI"] = ",".join(EXPANSION)
        exp = env["PSC_EXP_DIR"] + "_expanded"
        env["PSC_EXP_DIR"] = exp
        L = lambda n: os.path.join(ROOT, "run_logs", f"{key}_exp_{n}.log")
        print(f"\n=== {m['display']} - expanded universe ===")
        rec = dict(model=key, display=m["display"], exp_dir=exp)

        merge(exp, "stageA", "orig15_stageA_*.csv", "stageA_*.csv")
        merge(exp, "stageB_auditor", "orig15_stageB_auditor_*.csv", "stageB_auditor_*.csv")
        merge(exp, "stageB_salience", "orig15_stageB_salience_*.csv", "stageB_salience_*.csv")

        if sh([sys.executable, "analyze_stage_ab.py"], env, L("analyze_ab"),
              "analyze A+B (45 stimuli)") != 0:
            rec["stopped_at"] = "analyze_ab"; out.append(rec); continue

        rc_sel = sh([sys.executable, "select_pairs_replication.py"], env, L("select"),
                    "frozen selector (unchanged)")
        apf = os.path.join(exp, "pairs", "approved_pairs.csv")
        sel = list(csv.DictReader(open(apf))) if os.path.exists(apf) else []
        rec["n_selected"] = len(sel)
        rec["pairs"] = [f"{p['stimulus_high']} > {p['stimulus_low']}" for p in sel]
        if rc_sel != 0 or len(sel) < 3:
            print(f"    STOP: {len(sel)} selected pairs (< 3). No Stage C, no "
                  f"threshold change.")
            rec["stopped_at"] = "selection_below_minimum"; out.append(rec); continue
        print(f"    selected {len(sel)} pairs: {rec['pairs']}")

        # mark approved for the Stage C runner
        mp = os.path.join(exp, "matched_pairs.csv")
        rows = list(csv.DictReader(open(mp)))
        ids = {p["pair_id"] for p in sel}
        fields = list(rows[0]) + ([] if "approved" in rows[0] else ["approved"])
        for r in rows:
            r["approved"] = "True" if r["pair_id"] in ids else "False"
        with open(mp, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, restval="")
            w.writeheader(); w.writerows(rows)

        if key == "opus45":
            stim = sorted({s for p in sel
                           for s in (p["stimulus_high"], p["stimulus_low"])})
            sat, rate = saturation_screen(env, role, exp, stim, L("payoff_screen"))
            rec["screen_attempt_rate_at_safe9"] = rate
            rec["payoff_saturated"] = sat
            print(f"    payoff screen: ATTEMPT at SAFE=9 = {rate:.3f} "
                  f"(limit {SATURATION_LIMIT})")
            if sat is None or sat:
                print("    STOP: Stage C uninformative due to payoff saturation on "
                      "the selected stimulus distribution.")
                rec["stopped_at"] = "payoff_saturation"; out.append(rec); continue

        rec["stage_c_rc"] = sh([sys.executable, "stage_c_betting.py", "--n", "30",
                                "--models", role], env, L("stageC"),
                               "Stage C (n=30, safe {3,5,7,9})")
        rec["primary_rc"] = sh([sys.executable, "analyze_replication_primary.py"], env,
                               L("primary"), "primary analysis")
        out.append(rec)

    json.dump(out, open(os.path.join(ROOT, "analysis", "expansion_select.json"), "w"),
              indent=2, default=str)
    print(f"\n-> {ROOT}/analysis/expansion_select.json")


if __name__ == "__main__":
    main()
