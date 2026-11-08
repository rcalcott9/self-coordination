"""Rebuild C_glm/trials.csv (trial-level PLAY/PASS joined to y and A) for glmm.R. Packaging script added 2026-10-08;
the audit agent built trials.csv inline. Verified byte-identical against the audit's trials.csv by reproduce.sh."""
import csv, glob, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
IT = {(r["model"], r["array"]): r for r in csv.DictReader(open(os.path.join(ROOT, "analysis", "out", "item_table.csv")))}
rows = []
for f in sorted(glob.glob(os.path.join(ROOT, "runs", "main", "*.csv"))):
    for r in csv.DictReader(open(f)):
        if r["task"] == "PLAYPASS" and r["parse_ok"] == "1":
            it = IT[(r["focal"], r["array"])]
            rows.append([r["focal"], r["array"], int(r["decision"] == "PLAY"), it["y_actual"], it["auditor_mean"]])
rows.sort(key=lambda x: (x[0] != "gpt", x[1], -x[2]))
out = os.path.join(HERE, "trials_rebuilt.csv")
with open(out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["model", "array", "play", "y", "A"]); w.writerows(rows)
print("wrote", out, len(rows))
