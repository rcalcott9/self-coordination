"""EXPLORATORY. Cross-model divergence vs self / auditor prediction error. Existing data only.

Joins analysis/out/item_table.csv to the per-object VIS-FRAME-41 counts for GPT-5.5 and Opus 5.
All analyses are continuous and array-level, with no selection on observed prediction errors.

Calibration uncertainty, two mechanisms:
  * hierarchical bootstrap (B=2000): resample arrays; within array resample both models'
    48 calibration draws (multinomial) and the self/auditor reps;
  * SPLIT-HALF for any analysis whose outcome and predictor both contain the focal model's
    measured y (e.g. |A - y_f| vs |y_a - y_f|): shared measurement noise in y_f would create a
    spurious positive association. Each model's 48 draws are split into two halves of 24, one
    draw per presentation order in each half (orders were shown exactly twice, so both halves
    stay position-balanced). The outcome uses half 1 and the divergence uses half 2. Results are
    averaged over 200 random splits; the bootstrap redraws splits too.
"""
import csv, json, os
import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis", "out", "divergence"); os.makedirs(OUT, exist_ok=True)
F = json.load(open(os.path.join(ROOT, "design", "FROZEN.json")))
ARR = F["arrays"]; K = len(ARR)
MID = {"gpt": "gpt-5.5-2026-04-23", "claude": "claude-opus-5"}
OTH = {"gpt": "claude", "claude": "gpt"}
rng = np.random.default_rng(20261009)
B, NSPLIT = 2000, 200

# per-object draws, kept with presentation id so splits can be position-balanced
draws = {m: {a: [] for a in ARR} for m in MID}
for r in csv.DictReader(open(F["calibration_reuse"]["source"])):
    for m, mid in MID.items():
        if r["checkpoint_requested"] == mid and r["parse_ok"] == "1":
            draws[m][r["array_id"]].append((int(r["presentation_id"]), int(r["canonical_index"])))
item = {(r["model"], r["array"]): r for r in csv.DictReader(open(os.path.join(ROOT, "analysis", "out", "item_table.csv")))}
reps = {}
for f in os.listdir(os.path.join(ROOT, "runs", "main")):
    if f.endswith(".csv"):
        for r in csv.DictReader(open(os.path.join(ROOT, "runs", "main", f))):
            if r["parse_ok"] == "1" and r["task"] in ("SELFPRED", "AUDITOR"):
                reps.setdefault((r["focal"], r["task"], r["array"]), []).append(int(r["match_probability"]) / 100)


def wmm(c):
    c = np.asarray(c, float); n = c.sum(-1)
    return (c * (c - 1)).sum(-1) / (n * (n - 1))


C = {m: np.array([np.bincount([c for _, c in draws[m][a]], minlength=4) for a in ARR]) for m in MID}
assert all((C[m].sum(1) == 48).all() for m in MID)
S = {m: [np.array(reps[(m, "SELFPRED", a)]) for a in ARR] for m in MID}
A = {m: [np.array(reps[(m, "AUDITOR", a)]) for a in ARR] for m in MID}   # A[m] = auditor's prediction ABOUT m
# join check against item_table
for m in MID:
    y_it = np.array([float(item[(m, a)]["y_actual"]) for a in ARR])
    assert np.allclose(y_it, wmm(C[m]), atol=1e-4)
    assert np.allclose([float(item[(m, a)]["self_mean"]) for a in ARR], [x.mean() for x in S[m]], atol=1e-4)
    assert np.allclose([float(item[(m, a)]["auditor_mean"]) for a in ARR], [x.mean() for x in A[m]], atol=1e-4)


def halves(m, a):
    """Two position-balanced halves of 24 draws (one per presentation order each)."""
    by = {}
    for p, c in draws[m][a]:
        by.setdefault(p, []).append(c)
    h1, h2 = [], []
    for p, v in by.items():
        assert len(v) == 2
        i = rng.integers(2)
        h1.append(v[i]); h2.append(v[1 - i])
    return np.bincount(h1, minlength=4), np.bincount(h2, minlength=4)


def modal_sets(c):
    return set(np.flatnonzero(c == c.max()))


def stats_for(CG, CO, SG, SO, AG, AO, split=None):
    """All statistics for one (possibly resampled) dataset. CG/CO: K x 4 counts.
    split: dict m -> (K x 4 half1, K x 4 half2) for the noise-separated analyses."""
    pG, pO = CG / CG.sum(1, keepdims=True), CO / CO.sum(1, keepdims=True)
    yG, yO = wmm(CG), wmm(CO)
    out = {}
    # 1. favourite-object and distribution agreement
    same = np.array([1.0 if modal_sets(g) == modal_sets(o) and len(modal_sets(g)) == 1
                     else (len(modal_sets(g) & modal_sets(o)) / max(len(modal_sets(g) | modal_sets(o)), 1))
                     for g, o in zip(CG, CO)])
    out["same_modal_rate"] = same.mean()
    out["cross_match_mean"] = (pG * pO).sum(1).mean()          # P(GPT draw == Opus draw)
    out["overlap_mean"] = np.minimum(pG, pO).sum(1).mean()      # 1 - total variation
    # 2. matching-probability agreement
    out["r_yG_yO"] = np.corrcoef(yG, yO)[0, 1]
    out["spearman_yG_yO"] = stats.spearmanr(yG, yO)[0]
    out["mean_abs_dy"] = np.abs(yG - yO).mean()
    out["mean_signed_dy_G_minus_O"] = (yG - yO).mean()
    # 5. baseline: auditor's own measured y as prediction of focal y
    for f, yf, ya, Af, Sf in (("gpt", yG, yO, AG, SG), ("claude", yO, yG, AO, SO)):
        out[f"{f}:mae_auditor"] = np.abs(Af - yf).mean()
        out[f"{f}:mae_self"] = np.abs(Sf - yf).mean()
        out[f"{f}:mae_baseline_own_y"] = np.abs(ya - yf).mean()
        out[f"{f}:baseline_minus_auditor_mae"] = out[f"{f}:mae_baseline_own_y"] - out[f"{f}:mae_auditor"]
        out[f"{f}:r_auditor_with_focal_y"] = np.corrcoef(Af, yf)[0, 1]
        out[f"{f}:r_auditor_with_own_y"] = np.corrcoef(Af, ya)[0, 1]
        out[f"{f}:r_baseline_with_focal_y"] = np.corrcoef(ya, yf)[0, 1]
        out[f"{f}:self_minus_baseline_mae"] = out[f"{f}:mae_self"] - out[f"{f}:mae_baseline_own_y"]
        X = np.column_stack([np.ones(len(yf)), yf, ya])
        cf = np.linalg.lstsq(X, Af, rcond=None)[0]
        out[f"{f}:proj_A_on_focal_y"], out[f"{f}:proj_A_on_auditor_own_y"] = cf[1], cf[2]
        cs = np.linalg.lstsq(X, Sf, rcond=None)[0]
        out[f"{f}:self_on_focal_y_adj_other_y"], out[f"{f}:self_on_other_y_adj_focal_y"] = cs[1], cs[2]
    # 3-4. error vs divergence, noise-separated by split halves
    if split is not None:
        acc = {}
        for s_ in range(len(split)):
            sp = split[s_]
            yG1, yG2 = wmm(sp["gpt"][0]), wmm(sp["gpt"][1])
            yO1, yO2 = wmm(sp["claude"][0]), wmm(sp["claude"][1])
            pG2 = sp["gpt"][1] / 24; pO2 = sp["claude"][1] / 24
            fav_div = 1 - np.minimum(pG2, pO2).sum(1)              # favourite/distribution divergence (TVD)
            for f, yf1, yf2, ya2, Af, Sf in (("gpt", yG1, yG2, yO2, AG, SG), ("claude", yO1, yO2, yG2, AO, SO)):
                ady = np.abs(ya2 - yf2)                             # matching-probability divergence (half 2)
                eA, eS = np.abs(Af - yf1), np.abs(Sf - yf1)         # errors scored on half 1
                for nm, yv in (("auditor_err", eA), ("self_err", eS), ("D", eA - eS)):
                    acc.setdefault(f"{f}:{nm}~absdy", []).append(np.polyfit(ady, yv, 1)[0])
                    acc.setdefault(f"{f}:{nm}~absdy_spearman", []).append(stats.spearmanr(ady, yv)[0])
                    acc.setdefault(f"{f}:{nm}~TVD", []).append(np.polyfit(fav_div, yv, 1)[0])
                    acc.setdefault(f"{f}:{nm}~TVD_spearman", []).append(stats.spearmanr(fav_div, yv)[0])
                # level-adjusted: control the focal model's own matching level (half 2, independent of outcome noise)
                for nm, yv in (("auditor_err", eA), ("self_err", eS), ("D", eA - eS)):
                    for dn, dv in (("absdy", ady), ("TVD", fav_div)):
                        X = np.column_stack([np.ones(len(dv)), dv, yf2])
                        acc.setdefault(f"{f}:{nm}~{dn}|adj_yf", []).append(np.linalg.lstsq(X, yv, rcond=None)[0][1])
                # projection: signed auditor error vs signed (auditor own y - focal y)
                acc.setdefault(f"{f}:signed_aud_err~signed_dy", []).append(np.polyfit(ya2 - yf2, Af - yf1, 1)[0])
        out.update({k: float(np.mean(v)) for k, v in acc.items()})
    return out


def make_splits(CGd, COd, idx, n):
    """n random position-balanced splits for the arrays in idx (resampled order)."""
    res = []
    for _ in range(n):
        sp = {}
        for m in MID:
            h = [halves(m, ARR[j]) for j in idx]
            sp[m] = (np.array([x[0] for x in h]), np.array([x[1] for x in h]))
        res.append(sp)
    return res


# point estimates (observed data, splits averaged)
mean = lambda L: np.array([x.mean() for x in L])
obs = stats_for(C["gpt"], C["claude"], mean(S["gpt"]), mean(S["claude"]), mean(A["gpt"]), mean(A["claude"]),
                split=make_splits(None, None, np.arange(K), NSPLIT))
# hierarchical bootstrap; split-half quantities use 10 splits per replicate (split noise is
# averaged in the point estimate; in the bootstrap it adds a little width, i.e. conservative)
bs = []
for b in range(B):
    idx = rng.integers(0, K, K)
    CGb = np.array([rng.multinomial(48, C["gpt"][j] / 48) for j in idx])
    COb = np.array([rng.multinomial(48, C["claude"][j] / 48) for j in idx])
    rs = lambda L: np.array([L[j][rng.integers(0, len(L[j]), len(L[j]))].mean() for j in idx])
    # split halves are drawn from the ORIGINAL draws of each resampled array, then the half
    # counts are re-sampled multinomially so calibration noise enters them too
    sp = make_splits(None, None, idx, 10)
    for s_ in sp:
        for m in MID:
            s_[m] = tuple(np.array([rng.multinomial(24, h / 24) for h in half]) for half in s_[m])
    bs.append(stats_for(CGb, COb, rs(S["gpt"]), rs(S["claude"]), rs(A["gpt"]), rs(A["claude"]), split=sp))
keys = list(obs)
res = {k: dict(est=float(obs[k]), ci95=[float(np.quantile([d[k] for d in bs], .025)),
                                        float(np.quantile([d[k] for d in bs], .975))]) for k in keys}

# per-array table
pG, pO = C["gpt"] / 48, C["claude"] / 48
rows = []
for i, a in enumerate(ARR):
    g, o = C["gpt"][i], C["claude"][i]
    rows.append(dict(array=a, gpt_counts=g.tolist(), opus_counts=o.tolist(),
                     gpt_modal=sorted(modal_sets(g)), opus_modal=sorted(modal_sets(o)),
                     same_modal=modal_sets(g) == modal_sets(o),
                     cross_match=round(float((pG[i] * pO[i]).sum()), 4),
                     overlap=round(float(np.minimum(pG[i], pO[i]).sum()), 4),
                     y_gpt=round(float(wmm(g)), 4), y_opus=round(float(wmm(o)), 4),
                     abs_dy=round(float(abs(wmm(g) - wmm(o))), 4),
                     aud_of_gpt=round(float(A["gpt"][i].mean()), 4), self_gpt=round(float(S["gpt"][i].mean()), 4),
                     aud_of_opus=round(float(A["claude"][i].mean()), 4), self_opus=round(float(S["claude"][i].mean()), 4)))
with open(os.path.join(OUT, "divergence_items.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
# null reference for |dy|: expected mean |dy| if both models had IDENTICAL true distributions
# (pooled per array), from calibration noise alone
null = []
for _ in range(2000):
    d = []
    for i in range(K):
        pp = (C["gpt"][i] + C["claude"][i]) / 96
        d.append(abs(wmm(rng.multinomial(48, pp)) - wmm(rng.multinomial(48, pp))))
    null.append(np.mean(d))
res["mean_abs_dy_noise_floor_if_identical"] = dict(est=float(np.mean(null)), ci95=[float(np.quantile(null, .025)), float(np.quantile(null, .975))])
rel = {}
for m in MID:
    rr = []
    for _ in range(200):
        h = [halves(m, a) for a in ARR]
        rr.append(np.corrcoef(wmm(np.array([x[0] for x in h])), wmm(np.array([x[1] for x in h])))[0, 1])
    r = float(np.mean(rr)); rel[m] = dict(split_half_r=r, spearman_brown_48=2 * r / (1 + r))
res["y_reliability"] = rel
res["n_same_modal_point"] = int(sum(r["same_modal"] for r in rows))
res["n_tied_modal"] = {m: int(sum(len(modal_sets(c)) > 1 for c in C[m])) for m in MID}
json.dump(res, open(os.path.join(OUT, "divergence_results.json"), "w"), indent=1)
for k, v in res.items():
    print(k, v)
