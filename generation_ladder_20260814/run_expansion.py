"""
Expansion run: fresh Stage A + Stage B on the frozen 30-stimulus battery, for the two
models the original battery under-served (GPT-5, Opus 4.5).

Original 15 stimuli are NOT rerun and NOT discarded. Their Stage A/B estimates are
reused and merged with the new ones, so the candidate universe is 45 stimuli.

Auditor assignment is unchanged from the ladder runs:
    GPT-5    audited by claude-opus-5
    Opus 4.5 audited by gpt-5.5

Everything downstream - the frozen selector, its E1-E6 thresholds, the non-reuse rule,
the ranking - is untouched. The only change is the size of the candidate universe, plus
the prospectively corrected stop rule (>=3 FINAL SELECTED pairs, not >=3 eligible).

Run:  python3 run_expansion.py
"""
import csv, glob, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ladder_models import LADDER, CODE, env_for

REPO = os.path.expanduser("~/Desktop/Coordination/LLM_Coordination/Name_game_experiment")
EXPANSION = [r["stimulus_id"] for r in
             csv.DictReader(open(os.path.join(REPO, "stimuli", "expansion",
                                              "manifest.csv")))]
RUN = ["gpt5", "opus45"]
PARTNER = {"openai": ("PSC_CLAUDE_ID", "claude-opus-5", "PSC_CLAUDE_NAME",
                      "Claude Opus 5", "PSC_CLAUDE_SURFACE", "thinking"),
           "anthropic": ("PSC_GPT_ID", "gpt-5.5", "PSC_GPT_NAME", "GPT-5.5",
                         "PSC_GPT_SURFACE", "reasoning")}


def sh(cmd, env, log, label):
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.run(cmd, cwd=CODE, env=env, stdout=fh,
                            stderr=subprocess.STDOUT).returncode
    print(f"    {label:30} rc={rc}  {time.time()-t0:6.0f}s")
    return rc


def main():
    print(f"expansion battery: {len(EXPANSION)} stimuli")
    out = []
    for key in RUN:
        m = next(x for x in LADDER if x["key"] == key)
        role = "gpt" if m["provider"] == "openai" else "claude"
        env = env_for(m)
        a, av, b, bv, c, cv = PARTNER[m["provider"]]
        env[a], env[b], env[c] = av, bv, cv
        env["PSC_EXTRA_STIMULI"] = ",".join(EXPANSION)
        # keep the ORIGINAL-battery run intact; the expansion writes into its own tree
        base = env["PSC_EXP_DIR"]
        exp = base + "_expanded"
        os.makedirs(os.path.join(exp, "data"), exist_ok=True)
        # carry the original 15-stimulus A/B raw files across so analyze_stage_ab sees
        # BOTH batteries and the candidate universe is 45 stimuli, not 30
        for pat in ("stageA_*.csv", "stageB_auditor_*.csv", "stageB_salience_*.csv"):
            for f in glob.glob(os.path.join(base, "data", pat)):
                if "_DRY" in f:
                    continue
                dst = os.path.join(exp, "data", "orig15_" + os.path.basename(f))
                if not os.path.exists(dst):
                    shutil.copy(f, dst)
        env["PSC_EXP_DIR"] = exp
        L = lambda n: os.path.join(ROOT, "run_logs", f"{key}_exp_{n}.log")
        print(f"\n=== {m['display']} - expansion ===")

        rc = {}
        rc["A"] = sh([sys.executable, "stage_a_ground_truth.py", "--n", "60",
                      "--models", role, "--stimuli", *EXPANSION], env, L("stageA"),
                     "Stage A (30 new x n=60)")
        rc["B"] = sh([sys.executable, "stage_b_perception.py", "--arm", "both",
                      "--n", "30", "--focal", role, "--stimuli", *EXPANSION], env,
                     L("stageB"), "Stage B (30 new)")
        out.append(dict(model=key, display=m["display"], exp_dir=exp, rc=rc))

    json.dump(out, open(os.path.join(ROOT, "analysis", "expansion_run.json"), "w"),
              indent=2, default=str)
    print(f"\n-> {ROOT}/analysis/expansion_run.json")


if __name__ == "__main__":
    main()
