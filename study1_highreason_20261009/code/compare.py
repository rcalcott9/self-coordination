"""Secondary: high- vs low-reasoning, paired by array, clustered by stimulus family.

1a (per model): y (measured match), S (self), A (auditor), PLAY rate, |S-y|, |A-y|, D = |A-y|-|S-y|.
   Low values: study1_frontier_min_20261007/analysis/out/item_table.csv (frame calibration y, low runs).
1b: D_pooled, D_gpt, D_opus and TVD on the original 10 primary arrays.
   Low values: study1b_crossed_object_20261007/analysis/out/item_table.csv.
Inference: mean of family-level means of (high - low); family-cluster bootstrap CI (10,000) and family-level
sign-flip (exact when <= 16 families). Arrays-level means also reported.

  python code/compare.py [--runs runs|runs_mock]
"""
import argparse, csv, itertools, json, os
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("--runs", default="runs"); a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); SC = os.path.dirname(ROOT)
suf = "_mock" if a.runs != "runs" else ""
OUT = os.path.join(ROOT, "analysis", "out_compare" + suf); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20261009)
fam = lambda x: x.rsplit("_m", 1)[0]


def load(p):
    return list(csv.DictReader(open(p)))


def infer(diffs, arrays):
    groups = {}
    for d, x in zip(diffs, arrays):
        groups.setdefault(fam(x), []).append(d)
    fv = np.array([np.mean(v) for v in groups.values()]); keys = list(groups)
    bs = []
    for _ in range(10000):
        pick = rng.integers(0, len(keys), len(keys))
        bs.append(np.mean(np.concatenate([groups[keys[i]] for i in pick])))
    if len(fv) <= 16:
        pats = np.array(list(itertools.product([-1, 1], repeat=len(fv))))
        p = float(np.mean(np.abs((pats * fv).mean(1)) >= abs(fv.mean()) - 1e-12)); kind = "exact"
    else:
        fl = rng.choice([-1, 1], size=(10000, len(fv)))
        p = float((np.sum(np.abs((fl * fv).mean(1)) >= abs(fv.mean()) - 1e-12) + 1) / 10001); kind = "simulated"
    return dict(n_arrays=len(diffs), n_families=len(fv), mean_array=float(np.mean(diffs)), mean_family=float(fv.mean()),
                ci95_family_boot=[float(np.quantile(bs, .025)), float(np.quantile(bs, .975))],
                family_signflip_p=p, p_kind=kind, n_up=int((np.asarray(diffs) > 0).sum()), n_down=int((np.asarray(diffs) < 0).sum()))


R = {"note": "secondary, paired by array; low and high differ in reasoning setting AND in the source of y for 1a "
             "(low: reused frame calibration; high: fresh REF)"}
lo = {(r["model"], r["array"]): r for r in load(os.path.join(SC, "study1_frontier_min_20261007", "analysis", "out", "item_table.csv"))}
hi = {(r["model"], r["array"]): r for r in load(os.path.join(ROOT, "analysis", "out_1a" + suf, "item_table.csv"))}
R["1a"] = {}
for m in ("gpt", "claude"):
    keys = sorted(k for k in hi if k[0] == m and k in lo); arrs = [k[1] for k in keys]
    res = {}
    for q, col in (("y", "y_actual"), ("self", "self_mean"), ("auditor", "auditor_mean"), ("play", "play_rate"), ("D", "D_paired")):
        res[q] = dict(low=float(np.mean([float(lo[k][col]) for k in keys])), high=float(np.mean([float(hi[k][col]) for k in keys])),
                      **infer([float(hi[k][col]) - float(lo[k][col]) for k in keys], arrs))
    for q, col in (("abs_err_self", "self_mean"), ("abs_err_aud", "auditor_mean")):
        e = lambda r: abs(float(r[col]) - float(r["y_actual"]))
        res[q] = dict(low=float(np.mean([e(lo[k]) for k in keys])), high=float(np.mean([e(hi[k]) for k in keys])),
                      **infer([e(hi[k]) - e(lo[k]) for k in keys], arrs))
    res["corr_y_low_high"] = float(np.corrcoef([float(lo[k]["y_actual"]) for k in keys], [float(hi[k]["y_actual"]) for k in keys])[0, 1])
    R["1a"][m] = res
lo_b = {r["array"]: r for r in load(os.path.join(SC, "study1b_crossed_object_20261007", "analysis", "out", "item_table.csv"))}
hi_b = {r["array"]: r for r in load(os.path.join(ROOT, "analysis", "out_1b" + suf, "item_table.csv"))}
F = json.load(open(os.path.join(ROOT, "design", "FROZEN.json")))
prim = [x for x in F["primary_1b"] if x in hi_b and x in lo_b]
R["1b_primary"] = {}
for q, cl, ch in (("D_pooled", "D_pooled", "D_pooled"), ("D_gpt", "D_gpt", "D_gpt"), ("D_opus", "D_opus", "D_opus"),
                  ("tvd", "tvd_fresh", "tvd_high")):
    R["1b_primary"][q] = dict(low=float(np.mean([float(lo_b[x][cl]) for x in prim])),
                              high=float(np.mean([float(hi_b[x][ch]) for x in prim])),
                              **infer([float(hi_b[x][ch]) - float(lo_b[x][cl]) for x in prim], prim))
json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1)
print(json.dumps(R, indent=1))
