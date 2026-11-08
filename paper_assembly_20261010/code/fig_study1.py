#!/usr/bin/env python3
"""Study 1 2x3 figure from study1_figure_data_20261009 (no API calls).
Top: P(PLAY) vs measured agreement. Bottom: target-specific option-choice self advantage per item."""
import json
from pathlib import Path
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import statsmodels.api as sm
plt.style.use("academic")
HERE = Path(__file__).resolve().parent.parent
SRC = HERE.parent / "study1_figure_data_20261009/data"
OUT = HERE / "figures"; OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(20261010)
R = pd.read_csv(SRC / "reliability_items.csv")
S = pd.read_csv(SRC / "self_advantage_by_column.csv")
COLS = [("gpt", "GPT-5.5"), ("claude", "Claude Opus 5"), ("qwen", "Qwen step-316")]
ST = {"low": dict(marker="o", mfc="black", color="black", ls="-", label="Low reasoning"),
      "high": dict(marker="s", mfc="white", color="0.45", ls="--", label="High reasoning")}


def logit_curve(d, xs):
    X = sm.add_constant(d.x_agreement.values)
    y = np.c_[d.n_play.values, d.n_judgements_parsed.values - d.n_play.values]
    f = sm.GLM(y, X, family=sm.families.Binomial()).fit()
    return f.predict(sm.add_constant(xs))


def boot_ci(v, B=10000):
    v = np.asarray(v); m = rng.choice(v, (B, len(v))).mean(1)
    return v.mean(), np.quantile(m, .025), np.quantile(m, .975)


fig, ax = plt.subplots(2, 3, figsize=(6.5, 4.4))
summary = {}
for j, (c, name) in enumerate(COLS):
    a = ax[0, j]
    if c != "qwen":
        for s in ("low", "high"):
            d = R[(R.column == c) & (R.setting == s)]
            st = ST[s]
            a.plot(d.x_agreement, d.p_play, st["marker"], mfc=st["mfc"], mec=st["color"], ms=3.2, mew=.6, ls="none", label=st["label"])
            xs = np.linspace(.25, 1, 100); a.plot(xs, logit_curve(d, xs), color=st["color"], ls=st["ls"], lw=.9)
        a.set_xlim(.22, 1.02); a.set_xticks([.25, .5, .75, 1])
    else:
        d = R[(R.column == "qwen") & R.sample_type.str.startswith("observational")]
        a.plot(d.x_agreement, d.p_play, "o", mfc="black", mec="black", ms=3.2, mew=.6, ls="none", label="Observational")
        xs = np.linspace(.5, 1, 100); a.plot(xs, logit_curve(d, xs), color="black", lw=.9)
        k = R[(R.column == "qwen") & R.assignment.isin(["CLEAN", "NOISY"])]
        for asg, mk, ls in (("CLEAN", "s", "-"), ("NOISY", "^", ":")):
            e = k[k.assignment == asg].copy()
            e["bin"] = pd.qcut(e.x_agreement.rank(method="first"), 5, labels=False)
            g = e.groupby("bin").agg(x=("x_agreement", "mean"), y=("p_play", "mean"), se=("p_play", lambda v: v.std(ddof=1) / np.sqrt(len(v))))
            a.errorbar(g.x, g.y, yerr=1.96 * g.se, fmt=mk, mfc="white", mec="0.35", ecolor="0.35", ms=3.4, mew=.6, ls=ls, color="0.35",
                       lw=.7, capsize=1.5, elinewidth=.6, label=f"{asg.capitalize()} targets")
        a.set_xlim(.48, 1.02); a.set_xticks([.5, .75, 1])
    a.set_ylim(-.03, 1.03); a.set_xlabel("Measured agreement")
    if j == 0: a.set_ylabel("P(PLAY)")
    a.text(.02, 1.0, f"{'abc'[j]}  {name}", transform=a.transAxes, va="bottom", ha="left")
    a.legend(loc="lower right", frameon=False, fontsize=6, handlelength=1.4, borderaxespad=.2)

    b = ax[1, j]; d = S[S.column == c]
    groups = [("primary", "Divergent"), ("control", "Control")]
    settings = ["low", "high"] if c != "qwen" else ["thinking off"]
    for gi, (key, lab) in enumerate(groups):
        for si, s in enumerate(settings):
            v = d[(d.setting == s) & (d["sample"].str.lower().str.contains(key if key == "primary" else "control"))].D_self_target
            off = (si - (len(settings) - 1) / 2) * .28
            st = ST.get(s, ST["low"])
            xj = gi + off + rng.uniform(-.06, .06, len(v))
            b.plot(xj, v, st["marker"], mfc="none", mec="0.6", ms=2.6, mew=.5, ls="none")
            m, lo, hi = boot_ci(v)
            b.errorbar(gi + off, m, yerr=[[m - lo], [hi - m]], fmt=st["marker"], mfc=st["mfc"], mec=st["color"], ecolor=st["color"],
                       ms=4, mew=.7, capsize=2, elinewidth=.8, label=st["label"] if gi == 0 and c != "qwen" else None)
            summary[f"{c}|{s}|{key}"] = dict(n=int(len(v)), mean=float(m), ci95=[float(lo), float(hi)])
    b.axhline(0, color="black", lw=.5, ls=":")
    b.set_xticks([0, 1]); b.set_xticklabels([g[1] for g in groups]); b.set_xlim(-.6, 1.6)
    if j == 0: b.set_ylabel("Self advantage (Brier)")
    b.text(.02, 1.0, f"{'def'[j]}  {name}", transform=b.transAxes, va="bottom", ha="left")
    if c == "gpt": b.legend(loc="upper right", frameon=False, fontsize=6, handlelength=1.2)
ylo = min(x.get_ylim()[0] for x in ax[1]); yhi = max(x.get_ylim()[1] for x in ax[1])
for x in ax[1]: x.set_ylim(ylo, yhi)
fig.tight_layout(h_pad=1.2, w_pad=.8)
for ext in ("png", "pdf"): fig.savefig(OUT / f"fig_study1_2x3.{ext}", dpi=300)
json.dump(summary, open(HERE / "tables/fig_study1_bottom_row_summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
