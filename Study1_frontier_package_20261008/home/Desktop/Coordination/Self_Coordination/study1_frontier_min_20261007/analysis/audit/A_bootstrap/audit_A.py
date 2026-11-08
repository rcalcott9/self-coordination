"""Workstream A audit: agreement estimation, bootstrap bias, CI variants, test definitions.
Read-only on all study files; writes only into this folder. No API calls."""
import csv, glob, json, os
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
F = json.load(open(os.path.join(ROOT, "design", "FROZEN.json")))
ARR = F["arrays"]; K = len(ARR)
MID = {"gpt": "gpt-5.5-2026-04-23", "claude": "claude-opus-5"}
R = json.load(open(os.path.join(ROOT, "analysis", "out", "results.json")))
IT = {(r["model"], r["array"]): r for r in csv.DictReader(open(os.path.join(ROOT, "analysis", "out", "item_table.csv")))}
rng = np.random.default_rng(777)
B = 2000
out = {}


def wmm(c):
    c = np.asarray(c, float); n = c.sum(-1)
    return (c * (c - 1)).sum(-1) / (n * (n - 1))


C = {m: {a: np.zeros(4) for a in ARR} for m in MID}
for r in csv.DictReader(open(F["calibration_reuse"]["source"])):
    for m, mid in MID.items():
        if r["checkpoint_requested"] == mid and r["parse_ok"] == "1":
            C[m][r["array_id"]][int(r["canonical_index"])] += 1
rows = [r for f in glob.glob(os.path.join(ROOT, "runs", "main", "*.csv")) for r in csv.DictReader(open(f)) if r["parse_ok"] == "1"]
REP = {}
for r in rows:
    if r["task"] in ("SELFPRED", "AUDITOR"):
        REP.setdefault((r["focal"], r["task"], r["array"]), []).append(int(r["match_probability"]) / 100)

for m in MID:
    Cm = np.array([C[m][a] for a in ARR])
    y = wmm(Cm); plug = ((Cm / 48) ** 2).sum(1)
    yt = np.array([float(IT[(m, a)]["y_actual"]) for a in ARR])
    S = [np.array(REP[(m, "SELFPRED", a)]) for a in ARR]; A = [np.array(REP[(m, "AUDITOR", a)]) for a in ARR]
    Sm = np.array([s.mean() for s in S]); Am = np.array([s.mean() for s in A])
    o = {}
    # 1. estimator check
    o["y_matches_item_table_maxabs"] = float(np.abs(y - yt).max())
    o["n48_all"] = bool((Cm.sum(1) == 48).all())
    # 2. bootstrap centring of y*
    ystar = np.array([wmm(rng.multinomial(48, Cm[j] / 48, size=20000)).mean() for j in range(K)])
    o["ystar_minus_y_mean"] = float((ystar - y).mean()); o["ystar_minus_y_max"] = float((ystar - y).max())
    o["theory_(1-plug)/(n-1)_mean"] = float(((1 - plug) / 47).mean())
    o["ystar_minus_plugin_mean"] = float((ystar - plug).mean())

    def boot(variant):
        """variant: 'prespec' (as analyze.py), 'array_only', 'biascorr' (y* recentred on y)."""
        idx = rng.integers(0, K, size=(B, K))
        Db = np.empty(B); sl = {"S": np.empty(B), "A": np.empty(B)}; mse = {"S": np.empty(B), "A": np.empty(B)}
        if variant == "array_only":
            yb, Sb, Ab = y[idx], Sm[idx], Am[idx]
        else:
            yw = np.empty((B, K)); Sw = np.empty((B, K)); Aw = np.empty((B, K))
            for j in range(K):
                ys = wmm(rng.multinomial(48, Cm[j] / 48, size=B))
                if variant == "biascorr":
                    ys = ys - (ystar[j] - y[j])     # recentre so E[y*] = y
                yw[:, j] = ys
                Sw[:, j] = S[j][rng.integers(0, len(S[j]), (B, len(S[j])))].mean(1)
                Aw[:, j] = A[j][rng.integers(0, len(A[j]), (B, len(A[j])))].mean(1)
            yb = np.take_along_axis(yw, idx, 1); Sb = np.take_along_axis(Sw, idx, 1); Ab = np.take_along_axis(Aw, idx, 1)
        Db = (np.abs(Ab - yb) - np.abs(Sb - yb)).mean(1)
        for k, P in (("S", Sb), ("A", Ab)):
            for b in range(B):
                sl[k][b] = np.polyfit(yb[b], P[b], 1)[0]
            mse[k] = (P - yb).mean(1)
        return Db, sl, mse

    D_obs = float((np.abs(Am - y) - np.abs(Sm - y)).mean())
    o["D_obs"] = D_obs
    o["D_reported"] = R[m]["P1"]["mean_D"]; o["D_ci_reported"] = R[m]["P1"]["ci95"]
    sl_obs = {"S": np.polyfit(y, Sm, 1)[0], "A": np.polyfit(y, Am, 1)[0]}
    mse_obs = {"S": float((Sm - y).mean()), "A": float((Am - y).mean())}
    for v in ("prespec", "array_only", "biascorr"):
        Db, sl, mse = boot(v)
        o[f"{v}:D_ci_percentile"] = [float(np.quantile(Db, .025)), float(np.quantile(Db, .975))]
        o[f"{v}:D_boot_mean_minus_obs"] = float(Db.mean() - D_obs)
        o[f"{v}:D_boot_sd"] = float(Db.std())
        # basic (reverse-percentile) interval, which corrects for a shifted bootstrap centre
        o[f"{v}:D_ci_basic"] = [float(2 * D_obs - np.quantile(Db, .975)), float(2 * D_obs - np.quantile(Db, .025))]
        for k in ("S", "A"):
            o[f"{v}:slope_{k}_bias"] = float(sl[k].mean() - sl_obs[k])
            o[f"{v}:mse_{k}_bias"] = float(mse[k].mean() - mse_obs[k])
    # 4. P1 sign-flip with (k+1)/(N+1), and calibration-aware variant
    Di = np.abs(Am - y) - np.abs(Sm - y)
    N = 10000
    fl = rng.choice([-1, 1], (N, K))
    k = int((np.abs((fl * Di).mean(1)) >= abs(Di.mean())).sum())
    o["P1_signflip_p_(k+1)/(N+1)"] = (k + 1) / (N + 1); o["P1_signflip_p_reported"] = R[m]["P1"]["signflip_p"]
    # calibration-aware sign-flip: redraw y from multinomial each permutation (D_i noisy), flip signs
    ks = 0
    for i in range(2000):
        yb = wmm(np.array([rng.multinomial(48, Cm[j] / 48) for j in range(K)]))
        Dn = np.abs(Am - yb) - np.abs(Sm - yb)
        # uncentred, as in the standard sign-flip (centring would shrink the null spread)
        ks += abs((rng.choice([-1, 1], K) * Dn).mean()) >= abs(Di.mean())
    o["P1_calibration_aware_signflip_p_(2000)"] = (ks + 1) / 2001
    # P2 Spearman permutation p with (k+1)/(N+1)
    for nm, P in (("self", Sm), ("auditor", Am)):
        rho = stats.spearmanr(y, P)[0]
        kk = sum(abs(stats.spearmanr(y, rng.permutation(P))[0]) >= abs(rho) for _ in range(2000))
        o[f"P2_{nm}_spearman_p_(k+1)/(N+1)"] = (kk + 1) / 2001
        o[f"P2_{nm}_spearman_p_reported"] = R[m][f"P2_{nm}"]["spearman_perm_p"]
    out[m] = o

# Holm re-check with corrected p's
ps = {f"{m}:P1": out[m]["P1_signflip_p_(k+1)/(N+1)"] for m in MID}
ps.update({f"{m}:P2_{nm}": out[m][f"P2_{nm}_spearman_p_(k+1)/(N+1)"] for m in MID for nm in ("self", "auditor")})
order = sorted(ps.items(), key=lambda x: x[1]); holm = {}; run = 0
for i, (k_, p) in enumerate(order):
    run = max(run, min(1, p * (len(order) - i))); holm[k_] = run
out["holm_recomputed_(k+1)/(N+1)"] = holm
out["holm_reported"] = R["holm"]
# Holm with P1-only family (2 tests) for robustness of family definition
p1 = sorted([(k_, v) for k_, v in ps.items() if k_.endswith("P1")], key=lambda x: x[1])
out["holm_P1_only_family"] = {p1[0][0]: min(1, 2 * p1[0][1]), p1[1][0]: max(min(1, 2 * p1[0][1]), p1[1][1])}
# S2 reported check
out["S2_reported"] = {m: R[m]["S2"]["diff_ci"] for m in MID}
json.dump(out, open(os.path.join(HERE, "audit_A_results.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
