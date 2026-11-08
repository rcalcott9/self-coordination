#!/usr/bin/env python3
"""Study 3 PLAY/PASS Stag Hunt battery table + V_hat-vs-B figure + Qwen same-order B sensitivity (no API calls).
Frozen B = max(7, 10*c_pool). Qwen game prompt implies a same-presentation partner, so the labelled
sensitivity recomputes B with c_same = mean over the two orders of the within-order unbiased agreement."""
import json
from pathlib import Path
import numpy as np, pandas as pd, matplotlib.pyplot as plt
plt.style.use("academic")
HERE = Path(__file__).resolve().parent.parent
ST = Path.home() / "Desktop/Superrationality/Stag"
rng = np.random.default_rng(20261010)


def boot(v, B=10000):
    v = np.asarray(v, float); m = rng.choice(v, (B, len(v))).mean(1)
    return float(v.mean()), float(np.quantile(m, .025)), float(np.quantile(m, .975))


def u(k):
    k = np.asarray(k, float); n = k.sum()
    return float((k * (k - 1)).sum() / (n * (n - 1))) if n > 1 else np.nan


# ---- Qwen same-order c from raw Stage 0 draws
qsame = {}
for tag, d in (("off", "qwen_staghunt_pilot_20260916"), ("on", "qwen_staghunt_thinking_20261008")):
    t = pd.read_csv(ST / d / "analysis/trials.csv")
    s0 = t[(t.phase == "stage0") & (t.status == "ok") & t.object_canonical.notna()]
    rows = []
    for it, g in s0.groupby("item_id"):
        per = {o: u(h.object_canonical.value_counts().values) for o, h in g.groupby("orientation")}
        n_o = g.groupby("orientation").size().to_dict()
        c_pool = u(g.object_canonical.value_counts().values)
        c_same = float(np.mean(list(per.values())))
        rows.append(dict(item_id=it, c_pool_recomputed=c_pool, c_same=c_same, n_by_order=json.dumps(n_o),
                         **{f"c_{o}": v for o, v in per.items()}))
    qsame[tag] = pd.DataFrame(rows).set_index("item_id")

# ---- assemble per-item COPY rows for every battery arm
arms = []
def add(model, setting, status, df, key, draws, src):
    c = df[df.condition == "COPY"] if "condition" in df else df
    d = df[df.condition == "DIFFERENT"].set_index(key).p_play if "condition" in df and (df.condition == "DIFFERENT").any() else None
    for _, r in c.iterrows():
        cval = r.get("c_hat_fresh", r.get("c_hat"))
        arms.append(dict(model=model, setting=setting, status=status, item=r[key], draws_per_cell=draws, source=src,
                         c_pool=cval, B=r.B, v_hat=r.v_hat, p_play_copy=r.p_play,
                         p_play_diff=(d.get(r[key]) if d is not None else np.nan)))

tm = ST / "two_model_staghunt_20260916/analysis"
pa = pd.read_csv(tm / "per_array.csv")
for m in ("GPT-5.5", "Claude Opus 5"):
    add(m, "low", "frozen pilot (primary)", pa[pa.model == m], "array", 20, "two_model_staghunt_20260916/analysis/per_array.csv")
ext = pd.read_csv(tm / "ext_per_array.csv")
for m in ("GPT-5.5", "Claude Opus 5"):
    e = ext[(ext.model == m) & (ext.set == "high")]
    add(m, "high", "exploratory pilot (own Stage 0)", e, "array", 10, "two_model_staghunt_20260916/analysis/ext_per_array.csv [set=high]")
fb = pd.read_csv(ST / "fable_staghunt_20261008/analysis/per_array.csv")
add("Claude Fable 5.1", "low", "frozen (Opus arrays)", fb, "array", 20, "fable_staghunt_20261008/analysis/per_array.csv")
for tag, d, lab in (("off", "qwen_staghunt_pilot_20260916", "thinking off"), ("on", "qwen_staghunt_thinking_20261008", "thinking on")):
    q = pd.read_csv(ST / d / "analysis/per_item.csv")
    add("Qwen step-316", lab, "frozen pilot" if tag == "off" else "exploratory (thinking on)", q, "item_id", 20, f"{d}/analysis/per_item.csv")
A = pd.DataFrame(arms)
A["v_minus_B"] = A.v_hat - A.B
# Qwen same-order sensitivity
A["c_same"] = np.nan; A["B_same"] = np.nan
for tag, lab in (("off", "thinking off"), ("on", "thinking on")):
    m = (A.model == "Qwen step-316") & (A.setting == lab)
    qs = qsame[tag]
    A.loc[m, "c_same"] = A.loc[m, "item"].map(qs.c_same)
    A.loc[m, "c_pool_check"] = A.loc[m, "item"].map(qs.c_pool_recomputed)
    A.loc[m, "B_same"] = np.maximum(7, 10 * A.loc[m, "c_same"])
A["v_minus_B_same"] = A.v_hat - A.B_same
A.to_csv(HERE / "tables/study3_battery_items.csv", index=False)

rows = []
for (m, s), g in A.groupby(["model", "setting"], sort=False):
    vb = boot(g.v_minus_B); pc = boot(g.p_play_copy)
    r = dict(model=m, setting=s, status=g.status.iloc[0], items=len(g), draws_per_cell=int(g.draws_per_cell.iloc[0]),
             P_play_COPY=pc[0], P_play_COPY_ci=f"[{pc[1]:.2f}, {pc[2]:.2f}]",
             P_play_DIFF=float(g.p_play_diff.mean()) if g.p_play_diff.notna().any() else np.nan,
             mean_c=float(g.c_pool.mean()), mean_V_hat=float(g.v_hat.mean()), mean_B=float(g.B.mean()),
             V_minus_B=vb[0], V_minus_B_ci=f"[{vb[1]:.2f}, {vb[2]:.2f}]",
             items_V_below_B=int((g.v_minus_B < -1e-9).sum()))
    if g.B_same.notna().any():
        vs = boot(g.v_minus_B_same)
        r.update(SENS_mean_c_same=float(g.c_same.mean()), SENS_mean_B_same=float(g.B_same.mean()),
                 SENS_V_minus_B_same=vs[0], SENS_V_minus_B_same_ci=f"[{vs[1]:.2f}, {vs[2]:.2f}]",
                 SENS_items_V_below_B_same=int((g.v_minus_B_same < -1e-9).sum()),
                 check_c_pool_max_abs=float((g.c_pool - g.c_pool_check).abs().max()))
    rows.append(r)
T = pd.DataFrame(rows)
T.to_csv(HERE / "tables/study3_battery_table.csv", index=False)
print(T.to_string())

# ---- figure: V_hat vs B, one panel per model family
P = [("GPT-5.5", ["low", "high"]), ("Claude Opus 5", ["low", "high"]), ("Claude Fable 5.1", ["low"]), ("Qwen step-316", ["thinking off", "thinking on"])]
MK = {0: dict(marker="o", mfc="black", mec="black"), 1: dict(marker="s", mfc="white", mec="0.35")}
fig, ax = plt.subplots(1, 4, figsize=(6.5, 2.2), sharex=True, sharey=True)
for j, (m, ss) in enumerate(P):
    a = ax[j]; a.plot([6.8, 10.2], [6.8, 10.2], color="black", lw=.6, ls=":")
    for i, s in enumerate(ss):
        g = A[(A.model == m) & (A.setting == s)]
        jit = rng.uniform(-.06, .06, len(g))
        a.plot(g.B + jit, g.v_hat, ls="none", ms=3.4, mew=.6, label=s.replace("default", "default effort"), **MK[i])
    a.set_xlim(6.7, 10.3); a.set_ylim(4.0, 10.3); a.set_xticks([7, 8.5, 10])
    a.text(.02, 1.0, f"{'abcd'[j]}  {m}", transform=a.transAxes, va="bottom", ha="left")
    a.set_xlabel("Benchmark B")
    if j == 0: a.set_ylabel(r"Realised payoff $\hat V$")
    a.legend(loc="lower right", frameon=False, fontsize=6, handlelength=1, borderaxespad=.1)
fig.tight_layout(w_pad=.5)
for ext_ in ("png", "pdf"): fig.savefig(HERE / f"figures/fig_study3_vhat_vs_B.{ext_}", dpi=300)
