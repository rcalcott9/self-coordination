"""Family-level sensitivity for the Study 1b primary contrast (post hoc; frozen primary unchanged).
Array contrasts (analysis/out/item_table.csv) are averaged within stimulus family; families are
weighted equally. Exact two-sided sign-flip over all 2^F sign patterns; leave-one-family-out.
"""
import csv, itertools, json, os
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = [r for r in csv.DictReader(open(os.path.join(ROOT, "analysis", "out", "item_table.csv")))
     if r["stratum"] in ("S1", "S2_G", "S2_O")]
fam = {}
for r in T:
    fam.setdefault(r["array"].rsplit("_m", 1)[0], []).append(r)


def exact_p(v):
    v = np.asarray(v); pats = np.array(list(itertools.product([-1, 1], repeat=len(v))))
    return float(np.mean(np.abs((pats * v).mean(1)) >= abs(v.mean()) - 1e-12)), len(pats)


out = {"n_arrays": len(T), "n_families": len(fam),
       "families": {f: dict(arrays=[r["array"] for r in rs], strata=[r["stratum"] for r in rs]) for f, rs in fam.items()}}
for k in ("D_pooled", "D_gpt", "D_opus"):
    fm = {f: float(np.mean([float(r[k]) for r in rs])) for f, rs in fam.items()}
    v = np.array(list(fm.values())); p, npat = exact_p(v)
    lofo = {f: float(np.mean([fm[g] for g in fm if g != f])) for f in fm}
    lofo_arr = {f: float(np.mean([float(r[k]) for r in T if r["array"].rsplit("_m", 1)[0] != f])) for f in fm}
    out[k] = dict(family_means={f: round(x, 4) for f, x in fm.items()}, equal_weight_family_mean=float(v.mean()),
                  exact_signflip_p=p, n_sign_patterns=npat, min_attainable_p=2 / npat,
                  n_families_pos=int((v > 0).sum()), n_families_neg=int((v < 0).sum()),
                  lofo_family_mean=lofo, lofo_range=[min(lofo.values()), max(lofo.values())],
                  lofo_array_mean_range=[min(lofo_arr.values()), max(lofo_arr.values())])
json.dump(out, open(os.path.join(ROOT, "analysis", "out", "family_sensitivity.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
