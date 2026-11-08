"""
Full A -> B -> C pipeline for the three gate-passing historical rungs.

ONE MODEL PER RUNG. The runners are restricted with --models / --focal so a rung spends
nothing on the other provider.

AUDITOR PARTNER - A DOCUMENTED DEVIATION. The auditor arm needs an external observer to
predict the focal model. In the original and the 5.4/4.8 replication that observer was
the CONTEMPORANEOUS partner model. No contemporaneous partner exists for GPT-4o (the
oldest callable Claude is 2025-09), so each historical rung is audited by the current
flagship of the other provider, held CONSTANT across rungs:

    OpenAI rungs     audited by claude-opus-5
    Anthropic rungs  audited by gpt-5.5

A constant modern observer is arguably better for cross-rung comparability, but it does
mean the auditor covariate is not measured identically on the two already-collected
anchors. Auditor prediction enters ONLY as a pair-matching covariate (gate E5), never as
an outcome, so this cannot manufacture a Stage C effect.

Generic salience is rated by the focal model and the same fixed partner, pooled, as in
the original design.

Run:  python3 run_ladder.py
"""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ladder_models import LADDER, CODE, env_for

RUN = ["gpt4o", "gpt5", "opus45"]          # gate-passing rungs; opus46 excluded (gate D)
PARTNER = {"openai": ("PSC_CLAUDE_ID", "claude-opus-5", "PSC_CLAUDE_NAME", "Claude Opus 5",
                      "PSC_CLAUDE_SURFACE", "thinking"),
           "anthropic": ("PSC_GPT_ID", "gpt-5.5", "PSC_GPT_NAME", "GPT-5.5",
                         "PSC_GPT_SURFACE", "reasoning")}


def sh(cmd, env, log, label):
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.run(cmd, cwd=CODE, env=env, stdout=fh,
                            stderr=subprocess.STDOUT).returncode
    print(f"    {label:26} rc={rc}  {time.time()-t0:6.0f}s  -> {os.path.basename(log)}")
    return rc


def main():
    summary = []
    for key in RUN:
        m = next(x for x in LADDER if x["key"] == key)
        role = "gpt" if m["provider"] == "openai" else "claude"
        env = env_for(m)
        a, av, b, bv, c, cv = PARTNER[m["provider"]]
        env[a], env[b], env[c] = av, bv, cv
        exp = env["PSC_EXP_DIR"]
        os.makedirs(exp, exist_ok=True)
        L = lambda n: os.path.join(ROOT, "run_logs", f"{key}_{n}.log")
        print(f"\n=== {m['display']} ({m['model_id']}) surface="
              f"{m['gpt_surface'] or m['claude_surface']} ===")

        # gate data lives in the same tree; move it aside so the fresh Stage A is clean
        import glob, shutil
        gate_dir = os.path.join(exp, "competence_gate_data")
        os.makedirs(gate_dir, exist_ok=True)
        for f in glob.glob(os.path.join(exp, "data", "stage*")):
            shutil.move(f, os.path.join(gate_dir, os.path.basename(f)))

        rc = {}
        rc["A"] = sh([sys.executable, "stage_a_ground_truth.py", "--n", "60",
                      "--models", role], env, L("stageA"), "Stage A (n=60 x 15)")
        rc["B"] = sh([sys.executable, "stage_b_perception.py", "--arm", "both",
                      "--n", "30", "--focal", role], env, L("stageB"), "Stage B (auditor+salience)")
        rc["AB"] = sh([sys.executable, "analyze_stage_ab.py"], env, L("analyze_ab"),
                      "analyze A+B")
        rc["SEL"] = sh([sys.executable, "select_pairs_replication.py"], env, L("select"),
                       "frozen pair selection")
        if rc["SEL"] != 0:
            print("    !! pair selection did not yield a usable set - see log; skipping Stage C")
            summary.append(dict(model=key, stopped_at="pair_selection", rc=rc))
            continue

        # mark the selected pairs approved for the Stage C runner
        import csv
        ap = {r["pair_id"] for r in csv.DictReader(
            open(os.path.join(exp, "pairs", "approved_pairs.csv")))}
        mp = os.path.join(exp, "matched_pairs.csv")
        rows = list(csv.DictReader(open(mp)))
        fields = list(rows[0]) + ([] if "approved" in rows[0] else ["approved"])
        for r in rows:
            r["approved"] = "True" if r["pair_id"] in ap else "False"
        with open(mp, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, restval="")
            w.writeheader(); w.writerows(rows)
        print(f"    approved {len(ap)} pairs")

        rc["C"] = sh([sys.executable, "stage_c_betting.py", "--n", "30",
                      "--models", role], env, L("stageC"), "Stage C (n=30 x pairs x 4)")
        rc["PRIM"] = sh([sys.executable, "analyze_replication_primary.py"], env,
                        L("primary"), "primary analysis")
        summary.append(dict(model=key, display=m["display"], model_id=m["model_id"],
                            n_pairs=len(ap), rc=rc))

    json.dump(summary, open(os.path.join(ROOT, "analysis", "run_summary.json"), "w"),
              indent=2, default=str)
    print(f"\n-> {ROOT}/analysis/run_summary.json")


if __name__ == "__main__":
    main()
