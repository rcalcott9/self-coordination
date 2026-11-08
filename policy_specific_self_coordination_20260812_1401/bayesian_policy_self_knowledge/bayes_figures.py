"""
Figures for the Bayesian decision analysis. Visualisation only.

  A  latent subjective coordination beliefs - does inferred q sit nearer the
     model's own held-out reliability, or nearer the external-model estimate?
  B  posterior for the policy-specific weight lambda
  C  posterior predictive betting curves against the observed Stage C data

Run with the local venv:  ./.venv/bin/python bayes_figures.py
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
VIZ = os.path.join(os.path.dirname(HERE), "visualizations")
LBL = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
SAFES = [3, 5, 7, 9]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7.5,
    "axes.linewidth": 0.8, "axes.edgecolor": "black", "text.color": "black",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out",
    "axes.grid": False, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
})

Q_STY = dict(marker="o", markerfacecolor="black", markeredgecolor="black", markersize=6,
             linestyle="none")
T_STY = dict(marker="s", markerfacecolor="white", markeredgecolor="black", markersize=6,
             linestyle="none", markeredgewidth=1.0)
A_STY = dict(marker="^", markerfacecolor="0.6", markeredgecolor="black", markersize=6,
             linestyle="none", markeredgewidth=0.8)
EB = dict(elinewidth=0.8, capsize=2.2, capthick=0.8, ecolor="black")


def save(fig, stem, note):
    os.makedirs(VIZ, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(VIZ, f"{stem}.{ext}"), facecolor="white")
    plt.close(fig)
    print(f"\n-> {stem}.png / .pdf\n{note.strip()}")


def load():
    d = json.load(open(os.path.join(HERE, "model_data.json")))
    q = np.load(os.path.join(HERE, "q_posterior.npy"))
    lam = np.load(os.path.join(HERE, "lambda_posterior.npy"))
    ppc = np.load(os.path.join(HERE, "ppc_m3.npy")) if \
        os.path.exists(os.path.join(HERE, "ppc_m3.npy")) else None
    return d, q, lam, ppc


def figA(d, q):
    pairs, cells = d["pairs"], d["cells"]
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    ys = []
    for i, pr in enumerate(pairs):
        base = i * 1.0
        for j, (ix, tag) in enumerate(((pr["hi_ix"], "high"), (pr["lo_ix"], "low"))):
            y = base + (-0.19 if j == 0 else 0.19)
            ys.append(y)
            c = cells[ix]
            qs = q[:, ix]
            qm = np.median(qs); lo, hi = np.quantile(qs, [0.05, 0.95])
            ax.plot([c["aud_mean"], c["true_point"]], [y, y], color="0.75",
                    linewidth=1.4, zorder=1, solid_capstyle="round")
            ax.plot([c["aud_mean"]], [y], **A_STY, zorder=3)
            ax.plot([c["true_point"]], [y], **T_STY, zorder=3)
            ax.errorbar([qm], [y], xerr=[[qm - lo], [hi - qm]], **EB, zorder=4)
            ax.plot([qm], [y], **Q_STY, zorder=5)
            ax.text(-0.035, y, tag, fontsize=6.2, va="center", ha="right", color="0.4")
    ax.set_yticks([i * 1.0 for i in range(len(pairs))])
    ax.set_yticklabels([f"Pair {i+1}\n{LBL[p['model']]}" for i, p in enumerate(pairs)],
                       fontsize=7.5)
    ax.axhline(2.5, color="0.85", linewidth=0.8)
    ax.set_xlim(-0.12, 1.05)
    ax.set_ylim(-0.65, len(pairs) - 0.35)
    ax.invert_yaxis()
    ax.set_xlabel("coordination probability")
    handles = [Line2D([], [], **A_STY, label="external-model prediction"),
               Line2D([], [], **T_STY, label="held-out own-copy match"),
               Line2D([], [], **Q_STY, label="inferred subjective belief $q$ (90% CrI)")]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.30), ncol=3)
    fig.suptitle("Where does the inferred decision belief sit?", fontsize=11, y=1.00)
    fig.tight_layout()
    save(fig, "figure_bayes_subjective_beliefs", """
FIGURE A. For each approved pair, and separately for the higher- and lower-reliability
stimulus: the external-model prediction (triangle), the model's own held-out
coordination rate (square), and the subjective belief q inferred from betting
behaviour (filled circle, 90% credible interval). The grey bar spans external
estimate to own-copy reality.
READ IT AS: if q sat on the triangle, betting would be explained by public
information alone; if it sat on the square, betting would track the model's actual
own-copy reliability. NOT: a readout of an internal representation - q is the belief
that best explains the choices under this decision model.
""")


def figB(d, lam):
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.8), sharex=True, sharey=True)
    for mi, ax in enumerate(axes):
        v = lam[:, mi]
        ax.hist(v, bins=60, color="0.75", edgecolor="black", linewidth=0.4, density=True)
        med = np.median(v); lo, hi = np.quantile(v, [0.05, 0.95])
        ax.axvline(0, color="black", linewidth=1.0, linestyle=":")
        ax.axvline(med, color="black", linewidth=1.2)
        ax.plot([lo, hi], [0, 0], color="black", linewidth=2.5, solid_capstyle="butt")
        ax.set_title(f"{LBL[d['models'][mi]]}\nmedian {med:+.2f}  "
                     f"90% [{lo:+.2f}, {hi:+.2f}]  P(>0)={np.mean(v>0):.2f}",
                     fontsize=8)
        ax.set_xlabel("weight on policy-specific\ncoordination information ($\\lambda$)")
        ax.set_yticks([])
    axes[0].set_ylabel("posterior density")
    fig.suptitle("Weight placed on own-policy information beyond the external estimate",
                 fontsize=10.5, y=1.10)
    fig.tight_layout()
    save(fig, "figure_bayes_lambda", """
FIGURE B. Posterior for lambda, the coefficient on the model's own held-out
coordination reliability once the external-model prediction and generic salience are
already in the belief equation. Dotted line at zero; thick bar is the 90% credible
interval.
SUPPORTS: whether Stage C betting carries information beyond the public baseline.
DOES NOT ESTABLISH: introspection. lambda is a behavioural weight, not an
introspection score, and a learned self-model produces the same signature. Read
alongside the identifiability caveats - for the model with only four stimuli the
belief equation is saturated and lambda is prior-driven.
""")


def figC(d, ppc):
    if ppc is None:
        print("\n(no posterior predictive draws found - figure C skipped)")
        return
    trials = d["trials"]; pairs = d["pairs"]; cells = d["cells"]
    y = np.array([t["y"] for t in trials])
    cell = np.array([t["cell"] for t in trials])
    safe = np.array([t["safe"] for t in trials])
    fig, axes = plt.subplots(1, 5, figsize=(8.2, 2.5), sharey=True)
    for ax, (i, pr) in zip(axes, enumerate(pairs)):
        for ix, sty, fc in ((pr["hi_ix"], "-", "black"), (pr["lo_ix"], "--", "white")):
            obs, med, lo, hi = [], [], [], []
            for s in SAFES:
                m = (cell == ix) & (safe == s)
                obs.append(y[m].mean())
                rep = ppc[:, m].mean(axis=1)
                med.append(np.median(rep)); lo.append(np.quantile(rep, .05))
                hi.append(np.quantile(rep, .95))
            ax.fill_between(SAFES, lo, hi, color="0.85", zorder=1)
            ax.plot(SAFES, med, color="0.45", linestyle=sty, linewidth=1.0, zorder=2)
            ax.plot(SAFES, obs, color="black", linestyle=sty, linewidth=1.1,
                    marker="o", markersize=4, markerfacecolor=fc,
                    markeredgecolor="black", zorder=3)
        ax.set_xticks(SAFES); ax.set_ylim(-0.03, 1.04); ax.set_xlim(2.4, 9.6)
        ax.set_title(f"Pair {i+1}\n{LBL[pr['model']]}", fontsize=7)
        ax.set_xlabel("safe payoff", fontsize=8)
    axes[0].set_ylabel("P(attempt)")
    handles = [Line2D([], [], color="black", marker="o", markerfacecolor="black",
                      linestyle="-", markersize=4, label="observed, higher reliability"),
               Line2D([], [], color="black", marker="o", markerfacecolor="white",
                      linestyle="--", markersize=4, label="observed, matched lower"),
               Line2D([], [], color="0.45", linestyle="-", label="posterior predictive median"),
               Line2D([], [], color="0.85", linewidth=6, label="90% predictive interval")]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.14))
    fig.suptitle("Posterior predictive check: does the model reproduce the betting pattern?",
                 fontsize=10.5, y=1.12)
    fig.tight_layout()
    save(fig, "figure_bayes_posterior_predictive", """
FIGURE C. Observed Stage C attempt rates (black, filled = higher reliability, open =
matched lower) against the M3 posterior predictive median and 90% interval (grey).
SUPPORTS: whether the fitted decision model reproduces the payoff response and the
within-pair separation it is being used to interpret. A model that missed these
would not be worth interpreting. DOES NOT ESTABLISH: that the decision model is the
correct account - reproducing the pattern it was fitted to is a minimum requirement,
not evidence of mechanism.
""")


if __name__ == "__main__":
    d, q, lam, ppc = load()
    figA(d, q); figB(d, lam); figC(d, ppc)
