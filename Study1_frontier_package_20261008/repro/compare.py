"""Compare regenerated outputs with the reported copies in reported/. Numbers: |diff| <= 1e-9 (relative 1e-9);
CSV: cell-wise (numeric tolerance); PNG: pixel-identical; R text: identical lines."""
import csv, json, os, sys, math
import numpy as np
PKG = os.environ["S1PKG"]; H = os.path.join(PKG, "home", "Desktop/Coordination/Self_Coordination")
S1 = os.path.join(H, "study1_frontier_min_20261007"); S1B = os.path.join(H, "study1b_crossed_object_20261007")
R = os.path.join(PKG, "reported")
pairs = [(f"study1/{f}", f"{S1}/analysis/out/{f}") for f in ["results.json", "item_table.csv", "fig1_calibration.png",
         "fig2_paired_error.png", "fig3_playpass.png", "figS3_old_vs_corrected.png"]]
pairs += [(f"study1/{f}", f"{S1}/analysis/out/divergence/{f}") for f in ["divergence_results.json", "divergence_items.csv"]]
pairs += [("study1/ANCHOR_CHECK.json", f"{S1}/runs/anchor/ANCHOR_CHECK.json")]
pairs += [(f"study1/audit/{f}", f"{S1}/analysis/audit/{f}") for f in ["A_bootstrap/audit_A_results.json",
          "B_ordering_multiplicity/B_checks.json", "B_ordering_multiplicity/multiplicity.json", "C_glm/glmm_output.txt",
          "C_glm/glmm_opus_adj_output.txt", "D_drift/drift_audit.json"]]
pairs += [(f"study1b/{f}", f"{S1B}/analysis/out/{f}") for f in ["results.json", "item_table.csv", "family_sensitivity.json",
          "projection_diagnostic_full.json", "fig_selfcross.png"]]
pairs += [("study1b/power_final.json", os.path.join(PKG, "reproduced", "scratch", "power_final.json"))]


def num_eq(a, b, path, bad):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            if k not in a or k not in b: bad.append(f"{path}.{k}: key missing"); continue
            num_eq(a[k], b[k], f"{path}.{k}", bad)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): bad.append(f"{path}: length {len(a)} vs {len(b)}"); return
        for i, (x, y) in enumerate(zip(a, b)): num_eq(x, y, f"{path}[{i}]", bad)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if not (math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) or (math.isnan(a) and math.isnan(b))):
            bad.append(f"{path}: {a} vs {b}")
    elif a != b:
        bad.append(f"{path}: {str(a)[:60]} vs {str(b)[:60]}")


ok_all = True; rows = []
for rep, new in pairs:
    rp = os.path.join(R, rep); bad = []
    if not os.path.exists(new): rows.append((rep, "MISSING OUTPUT")); ok_all = False; continue
    if rep.endswith(".json"):
        num_eq(json.load(open(rp)), json.load(open(new)), "", bad)
    elif rep.endswith(".csv"):
        a, b = list(csv.reader(open(rp))), list(csv.reader(open(new)))
        if len(a) != len(b): bad.append("row count")
        for i, (x, y) in enumerate(zip(a, b)):
            for j, (u, v) in enumerate(zip(x, y)):
                if u != v:
                    try:
                        if not math.isclose(float(u), float(v), rel_tol=1e-9, abs_tol=1e-9): bad.append(f"r{i}c{j}: {u} vs {v}")
                    except ValueError: bad.append(f"r{i}c{j}: {u} vs {v}")
    elif rep.endswith(".png"):
        import matplotlib.image as mi
        x, y = mi.imread(rp), mi.imread(new)
        if x.shape != y.shape or not np.array_equal(x, y):
            bad.append(f"pixels differ (shape {x.shape} vs {y.shape}, max|d|={np.abs(x-y).max() if x.shape==y.shape else 'n/a'})")
    else:
        a = [l for l in open(rp).read().splitlines() if l.strip()]; b = [l for l in open(new).read().splitlines() if l.strip()]
        if a != b: bad.append(f"text differs ({sum(1 for u,v in zip(a,b) if u!=v)} lines)")
    rows.append((rep, "OK" if not bad else "DIFF: " + "; ".join(bad[:4]) + (f" (+{len(bad)-4} more)" if len(bad) > 4 else "")))
    ok_all &= not bad
print("\nREPRODUCTION CHECK")
for r, s in rows: print(f"  {s[:4]:4s}  {r}" + ("" if s == "OK" else f"\n        {s}"))
print("ALL REPORTED OUTPUTS REPRODUCED" if ok_all else "SOME OUTPUTS DIFFER - see above")
sys.exit(0 if ok_all else 2)
