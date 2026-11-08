#!/usr/bin/env python3
"""SENSITIVITY (exploratory, 2026-10-13; no API calls): winner's-curse bias in the Study 3 benchmark.
Frozen B = max(7, 10*c_hat) takes a max over a noisy c_hat, so E[B_hat] >= the true benchmark
(Jensen), biasing V_hat - B downward, i.e. toward the "copies fall short" claim. Two corrections:
  B_bc  bootstrap bias-corrected: B_hat - (mean_b max(7, 10*c*_b) - B_hat), multinomial resampling
        of the Stage 0 object counts; floored at 7 (PASS is always available).
  B_cf  cross-fitted: split Stage 0 draws in half; choose PLAY iff 10*c_A > 7 on half A and value the
        choice on half B (10*c_B or 7); average over 2,000 random splits. This is the expected value of
        the plug-in policy, an unbiased but conservative (lower) benchmark.
V_hat and the frozen B are taken unchanged from tables/study3_battery_items.csv."""
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent.parent
ST = Path.home() / "Desktop/Superrationality/Stag"
rng = np.random.default_rng(20261010)
NB, NS = 4000, 2000


def u(k):
    k = np.asarray(k, float); n = k.sum(-1)
    return (k * (k - 1)).sum(-1) / (n * (n - 1))


def corrections(counts):
    k = np.asarray(counts, int); n = int(k.sum())
    B = max(7.0, 10 * u(k))
    star = rng.multinomial(n, k / n, size=NB)
    bias = float(np.maximum(7, 10 * u(star)).mean() - B)
    draws = np.repeat(np.arange(len(k)), k)
    cf = []
    for _ in range(NS):
        p = rng.permutation(draws); a, b = p[: n // 2], p[n // 2:]
        ca, cb = u(np.bincount(a, minlength=len(k))), u(np.bincount(b, minlength=len(k)))
        cf.append(10 * cb if 10 * ca > 7 else 7.0)
    return B, bias, max(7.0, B - bias), float(np.mean(cf))


# Stage 0 counts per arm (same sources the frozen B values were computed from)
S = []
tm = ST / "two_model_staghunt_20260916/analysis"
f0 = pd.read_csv(tm / "fresh_stage0.csv")
for _, r in f0.iterrows():
    S.append(dict(model=r.model, setting="low", item=r["array"], counts=r.counts))
eb = pd.read_csv(tm / "ext_baselines.csv")
for _, r in eb[eb.effort == "high"].iterrows():
    S.append(dict(model=r.model, setting="high", item=r["array"], counts=r.counts))
fb = pd.read_csv(ST / "fable_staghunt_20261008/analysis/fresh_stage0.csv")
for _, r in fb.iterrows():
    S.append(dict(model=r.model, setting="low", item=r["array"], counts=r.counts))
for d, lab in (("qwen_staghunt_pilot_20260916", "thinking off"), ("qwen_staghunt_thinking_20261008", "thinking on")):
    t = pd.read_csv(ST / d / "analysis/trials.csv")
    s0 = t[(t.phase == "stage0") & (t.status == "ok") & t.object_canonical.notna()]
    for it, g in s0.groupby("item_id"):
        S.append(dict(model="Qwen step-316", setting=lab, item=it,
                      counts="/".join(map(str, np.bincount(g.object_canonical.astype(int), minlength=2)))))
S = pd.DataFrame(S)

A = pd.read_csv(HERE / "tables/study3_battery_items.csv")
A = A.merge(S, on=["model", "setting", "item"], how="left", validate="one_to_one")
assert A.counts.notna().all(), A[A.counts.isna()][["model", "setting", "item"]]
out = A.apply(lambda r: pd.Series(corrections([int(x) for x in r.counts.split("/")]), index=["B_recomputed", "B_bias", "B_bc", "B_cf"]), axis=1)
A = pd.concat([A, out], axis=1)
assert (A.B_recomputed - A.B).abs().max() < 1e-9, "frozen B not reproduced from Stage 0 counts"
A["v_minus_B_bc"] = A.v_hat - A.B_bc; A["v_minus_B_cf"] = A.v_hat - A.B_cf


def boot(v):
    v = np.asarray(v, float); m = rng.choice(v, (10000, len(v))).mean(1)
    return float(v.mean()), float(np.quantile(m, .025)), float(np.quantile(m, .975))


rows = []
for (m, s), g in A.groupby(["model", "setting"], sort=False):
    r = dict(model=m, setting=s, status=g.status.iloc[0], items=len(g), mean_B_bias=float(g.B_bias.mean()))
    for col, lab in (("v_minus_B", "frozen"), ("v_minus_B_bc", "bias_corrected"), ("v_minus_B_cf", "cross_fitted")):
        e = boot(g[col]); r[f"V_minus_B_{lab}"] = e[0]; r[f"ci_{lab}"] = f"[{e[1]:.2f}, {e[2]:.2f}]"
        r[f"items_below_{lab}"] = int((g[col] < -1e-9).sum())
    rows.append(r)
T = pd.DataFrame(rows)
A.to_csv(HERE / "tables/study3_benchmark_bias_items.csv", index=False)
T.to_csv(HERE / "tables/study3_benchmark_bias.csv", index=False)
print(T.round(3).to_string())
