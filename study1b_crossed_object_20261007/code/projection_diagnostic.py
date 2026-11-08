"""Study 1b EXPLORATORY projection diagnostic + exact sign-flip p (not pre-specified).
Scripted verbatim from the inline computation reported in RESULTS v1/v2 (2026-10-08). No RNG."""
import csv, glob, json, itertools, os
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FM = json.load(open(os.path.join(ROOT, "design", "FROZEN_MAIN.json")))
FSHA = open(os.path.join(ROOT, "design", "FROZEN_MAIN.sha256")).read()[:8]
strat = {x: s for s, v in FM["strata"].items() for x in v}
rows = [r for f in glob.glob(os.path.join(ROOT, "runs", "main", "*.csv")) for r in csv.DictReader(open(f))
        if r["frozen_sha8"] == FSHA and r["parse_ok"] == "1"]
M = ["gpt", "claude"]; ref = {}; pred = {}
for r in rows:
    if r["task"] == "REF":
        ref.setdefault((r["answerer"], r["array"]), []).append(int(r["canonical_choice"]))
    else:
        pred.setdefault((r["answerer"], r["target"], r["array"]), []).append(np.array(json.loads(r["p_canonical"])))
ph = {k: np.bincount(v, minlength=4) / len(v) for k, v in ref.items()}
br = lambda q, p: q @ q - 2 * q @ p + 1
prim = [x for x in FM["arrays"] if strat[x] in ("S1", "S2_G", "S2_O")]
T = {r["array"]: r for r in csv.DictReader(open(os.path.join(ROOT, "analysis", "out", "item_table.csv")))}


def exact(v):
    v = np.array(v); obs = abs(v.mean()); pats = np.array(list(itertools.product([-1, 1], repeat=len(v))))
    return float(np.mean(np.abs((pats * v).mean(1)) >= obs - 1e-12))


out = {"exact_signflip_p": {k: exact([float(T[x][k]) for x in prim]) for k in ["D_pooled", "D_gpt", "D_opus"]}}
for P in M:
    O = [m for m in M if m != P][0]
    diff, proj, tgt = [], [], []
    for x in prim:
        qS = np.mean(pred[(P, P, x)], 0); qO = np.mean(pred[(P, O, x)], 0)
        diff.append(0.5 * np.abs(qS - qO).sum())
        bo = np.mean([br(q, ph[(P, x)]) for q in pred[(P, O, x)]]); bt = np.mean([br(q, ph[(O, x)]) for q in pred[(P, O, x)]])
        proj.append(bt - bo)
        dm = ph[("gpt", x)] - ph[("claude", x)]; dp = np.mean(pred[(P, "gpt", x)], 0) - np.mean(pred[(P, "claude", x)], 0)
        tgt.append(float(dp @ dm / (np.linalg.norm(dp) * np.linalg.norm(dm) + 1e-12)) if np.linalg.norm(dp) > 1e-6 else 0.0)
    out[P] = dict(mean_TVD_between_its_two_target_predictions=round(float(np.mean(diff)), 3),
                  arrays_with_TVD_gt_0p1=int(np.sum(np.array(diff) > .1)),
                  cross_pred_closer_to_own_policy_mean_brier_gap=round(float(np.mean(proj)), 3),
                  n_arrays_cross_closer_to_own=int(np.sum(np.array(proj) > 0)),
                  cosine_pred_vs_measured_target_difference_mean=round(float(np.mean(tgt)), 3), n=len(prim))
json.dump(out, open(os.path.join(ROOT, "analysis", "out", "projection_diagnostic_full.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
