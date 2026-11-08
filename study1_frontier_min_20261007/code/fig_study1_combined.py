"""Combined Study 1 figure from existing outputs only (no calls).
A: item-level P(PLAY) vs independently measured copy-matching probability (frame calibration), per model,
   with an UNADJUSTED pooled-logistic fitted curve. Auditor-adjusted GLMM estimates are stated in the caption only.
B: Study 1b target-specific self-minus-cross Brier advantage on the 10 divergent arrays: item points, means,
   array-bootstrap 95% CIs (from the frozen analysis results.json), zero line."""
import csv, json, os
import numpy as np
import statsmodels.api as sm
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.style.use("academic")
SC = os.path.expanduser("~/Desktop/Coordination/Self_Coordination")
S1 = os.path.join(SC, "study1_frontier_min_20261007"); S1B = os.path.join(SC, "study1b_crossed_object_20261007")
OUT = os.path.join(S1, "analysis", "figures")
it = list(csv.DictReader(open(os.path.join(S1, "analysis", "out", "item_table.csv"))))
ib = [r for r in csv.DictReader(open(os.path.join(S1B, "analysis", "out", "item_table.csv"))) if r["stratum"] in ("S1", "S2_G", "S2_O")]
RB = json.load(open(os.path.join(S1B, "analysis", "out", "results.json")))
assert len(ib) == 10
fig = plt.figure(figsize=(7.0, 2.7))
gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.8], wspace=0.38)
LAB = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
for k, m in enumerate(["gpt", "claude"]):
    ax = fig.add_subplot(gs[0, k])
    rows = [r for r in it if r["model"] == m]
    y = np.array([float(r["y_actual"]) for r in rows]); p = np.array([float(r["play_rate"]) for r in rows])
    n = np.array([int(r["n_play"]) for r in rows])
    z = 1.96; den = 1 + z*z/n; cen = (p + z*z/(2*n))/den; hw = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    ax.errorbar(y, p, yerr=[p-(cen-hw), (cen+hw)-p], fmt="none", ecolor="0.65", elinewidth=.5, capsize=1.2, zorder=1)
    ax.plot(y, p, ls="none", marker="o" if m == "gpt" else "s", mfc="black" if m == "gpt" else "white",
            mec="black", ms=3.8, zorder=3)
    X = sm.add_constant(y); fit = sm.GLM(np.column_stack([p*n, (1-p)*n]), X, family=sm.families.Binomial()).fit()
    xs = np.linspace(y.min(), 1, 80); ax.plot(xs, 1/(1+np.exp(-(fit.params[0]+fit.params[1]*xs))), color="black",
                                              lw=.9, ls="-" if m == "gpt" else "--", zorder=2)
    ax.text(.98, .03, "curve: unadjusted\npooled logistic", transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5)
    ax.set_xlim(.25, 1.02); ax.set_ylim(-.04, 1.04)
    ax.set_xlabel("Copy-matching probability\n(independent calibration)")
    if k == 0: ax.set_ylabel("Proportion choosing PLAY")
    ax.text(0, 1.03, ("A  " if k == 0 else "") + f"{LAB[m]}\n41 arrays × 12 trials", transform=ax.transAxes, va="bottom", fontsize=8.5)
axb = fig.add_subplot(gs[0, 2])
rng = np.random.default_rng(7)
for j, (key, col, lab) in enumerate([("D_gpt", "target_gpt", "Target\nGPT-5.5"), ("D_opus", "target_opus", "Target\nClaude Opus 5")]):
    v = np.array([float(r[key]) for r in ib]); x = j + rng.uniform(-.12, .12, len(v))
    axb.plot(x, v, ls="none", marker="o", mfc="white", mec="0.35", ms=3.6, zorder=2)
    s = RB["primary"][col]; axb.errorbar([j + .32], [s["mean"]], yerr=[[s["mean"]-s["ci95"][0]], [s["ci95"][1]-s["mean"]]],
                                         fmt="D", ms=4.2, mfc="black", mec="black", ecolor="black", elinewidth=1.1, capsize=3, zorder=3)
axb.axhline(0, color="black", lw=.8)
axb.set_xticks([0.12, 1.12]); axb.set_xticklabels(["Target\nGPT-5.5", "Target\nClaude Opus 5"])
axb.set_xlim(-.45, 1.6); axb.set_ylabel("Self minus cross Brier advantage")
axb.text(0, 1.03, "B  Divergent arrays\nn = 10 arrays (7 families)", transform=axb.transAxes, va="bottom", fontsize=8.5)
fig.subplots_adjust(left=.075, right=.99, bottom=.25, top=.82)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(OUT, f"fig_study1_combined.{ext}"), dpi=300)

