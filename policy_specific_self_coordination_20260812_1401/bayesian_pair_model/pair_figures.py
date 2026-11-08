"""
Figures for the pair-constrained Bayesian analysis. Visualisation only.

  A  latent coordination belief per pair (q_low vs q_high, posterior intervals)
  B  population within-pair shift mu_delta, with the prior for comparison
  C  direct effect delta on willingness to ATTEMPT, with the prior

Run:  ../bayesian_policy_self_knowledge/.venv/bin/python pair_figures.py
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

# Canonical pair numbering, identical to the frequentist figures. model_data.json
# stores pairs in matched_pairs.csv file order (Claude first), which would make
# "Pair 1" mean different things in different figures of the same paper.
CANON = [("gpt", "c_contr_subtle", "b_spiral_cw"),
         ("gpt", "s_convexity", "d_dens_extreme"),
         ("gpt", "c_open_cplx", "s_density"),
         ("claude", "b_spiral_cw", "rot"),
         ("claude", "s_convexity", "d_dens_extreme")]


def canon_order(pairs):
    """Return indices into `pairs` in canonical Pair 1..5 order."""
    key = {(p["model"], p["hi"], p["lo"]): i for i, p in enumerate(pairs)}
    missing = [c for c in CANON if c not in key]
    if missing:
        raise SystemExit(f"canonical pair not found: {missing}")
    return [key[c] for c in CANON]


HI = dict(marker="o", markerfacecolor="black", markeredgecolor="black", markersize=6.5,
          linestyle="none")
LO = dict(marker="o", markerfacecolor="white", markeredgecolor="black", markersize=6.5,
          linestyle="none", markeredgewidth=1.0)
EB = dict(elinewidth=1.0, capsize=2.5, capthick=0.9, ecolor="black")


def save(fig, stem, note):
    os.makedirs(VIZ, exist_ok=True)
    for e in ("png", "pdf"):
        fig.savefig(os.path.join(VIZ, f"{stem}.{e}"), facecolor="white")
    plt.close(fig)
    print(f"\n-> {stem}.png / .pdf\n{note.strip()}")


def figA(pairs, qh, ql):
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for i in range(len(pairs)):
        y = i
        for arr, sty, off in ((ql[:, i], LO, 0.16), (qh[:, i], HI, -0.16)):
            m = np.median(arr); lo, hi = np.quantile(arr, [.05, .95])
            ax.errorbar([m], [y + off], xerr=[[m - lo], [hi - m]], **EB, zorder=2)
            ax.plot([m], [y + off], **sty, zorder=3)
        ax.plot([np.median(ql[:, i]), np.median(qh[:, i])], [y + 0.16, y - 0.16],
                color="0.6", linewidth=0.9, zorder=1)
    ax.set_yticks(range(len(pairs)))
    ax.set_yticklabels([f"Pair {i+1}\n{LBL[p['model']]}" for i, p in enumerate(pairs)],
                       fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.02)
    ax.set_xlabel("inferred decision-relevant coordination belief $q$")
    ax.legend(handles=[Line2D([], [], **HI, label="higher own-copy reliability"),
                       Line2D([], [], **LO, label="matched lower")],
              loc="lower left", fontsize=7.5)
    fig.suptitle("Inferred coordination belief, by matched pair", fontsize=10.5, y=1.01)
    fig.tight_layout()
    save(fig, "figure_pair_latent_beliefs", """
FIGURE A. Posterior median and 90% credible interval for the latent decision-relevant
coordination belief q, separately for the higher- and lower-reliability member of each
approved pair, from the pair-constrained model.
CLAIM: models behave as if the higher-reliability stimulus carries a higher chance of
successful self-coordination. NOT: a readout of an internal belief - q is whatever
value best explains the observed ATTEMPT/SAFE choices under this decision model, and
the absolute level is less well determined than the within-pair difference.
""")


def figB(mu, prior):
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    ax.hist(prior, bins=80, density=True, color="0.90", edgecolor="0.75",
            linewidth=0.3, label="prior")
    ax.hist(mu, bins=60, density=True, color="0.55", edgecolor="black",
            linewidth=0.4, label="posterior")
    m = np.median(mu); lo, hi = np.quantile(mu, [.05, .95])
    ax.axvline(0, color="black", linewidth=1.0, linestyle=":")
    ax.plot([lo, hi], [0, 0], color="black", linewidth=3, solid_capstyle="butt")
    ax.plot([m], [0], marker="o", color="black", markersize=5)
    ax.set_xlabel("average high-minus-low shift in inferred\ncoordination belief "
                  "($\\mu_\\delta$, logit scale)")
    ax.set_yticks([]); ax.set_ylabel("density")
    ax.legend(loc="upper right")
    ax.set_title(f"median {m:+.2f}   90% [{lo:+.2f}, {hi:+.2f}]   "
                 f"P($\\mu_\\delta$>0) = {(mu>0).mean():.3f}", fontsize=8.5)
    fig.suptitle("Population within-pair shift", fontsize=10.5, y=1.06)
    fig.tight_layout()
    save(fig, "figure_pair_mu_delta", """
FIGURE B. Posterior for mu_delta, the average within-pair shift in inferred
coordination belief, with the prior shown for comparison. Dotted line at zero; the
thick bar is the 90% credible interval.
CLAIM: whether, across matched pairs, models place higher decision-relevant
coordination probability on the stimulus their own copies handle better. The prior
overlay is the honest check - a posterior that merely reproduced the prior would carry
no information. NOT an introspection score, and not evidence of privileged access.
""")


def figC(dl, prior):
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    ax.hist(prior, bins=80, density=True, color="0.90", edgecolor="0.75",
            linewidth=0.3, label="prior")
    ax.hist(dl, bins=60, density=True, color="0.55", edgecolor="black",
            linewidth=0.4, label="posterior")
    m = np.median(dl); lo, hi = np.quantile(dl, [.05, .95])
    ax.axvline(0, color="black", linewidth=1.0, linestyle=":")
    ax.plot([lo, hi], [0, 0], color="black", linewidth=3, solid_capstyle="butt")
    ax.plot([m], [0], marker="o", color="black", markersize=5)
    ax.set_xlabel("effect of higher own-copy reliability on\nwillingness to ATTEMPT "
                  "($\\delta$, log-odds)")
    ax.set_yticks([]); ax.set_ylabel("density")
    ax.legend(loc="upper right")
    ax.set_title(f"median {m:+.2f} (OR {np.exp(m):.2f})   90% [{lo:+.2f}, {hi:+.2f}]   "
                 f"P($\\delta$>0) = {(dl>0).mean():.3f}", fontsize=8.5)
    fig.suptitle("Direct within-pair effect on betting", fontsize=10.5, y=1.06)
    fig.tight_layout()
    save(fig, "figure_pair_direct_delta", """
FIGURE C. Posterior for delta from the direct model (payoff + is_high), the change in
log-odds of attempting when the stimulus is the higher-reliability member of its pair,
with the prior for comparison.
CLAIM: the Bayesian counterpart of the pre-specified frequentist matched-pair result,
on a single interpretable scale. NOT independent confirmation - it is the same 1200
Stage C trials analysed a second way, and the pre-specified permutation test remains
the primary evidence.
""")


if __name__ == "__main__":
    d = json.load(open(os.path.join(os.path.dirname(HERE),
                                    "bayesian_policy_self_knowledge", "model_data.json")))
    order = canon_order(d["pairs"])
    pairs = [d["pairs"][i] for i in order]
    figA(pairs, np.load(os.path.join(HERE, "q_high.npy"))[:, order],
         np.load(os.path.join(HERE, "q_low.npy"))[:, order])
    figB(np.load(os.path.join(HERE, "mu_delta.npy")),
         np.load(os.path.join(HERE, "prior_mu_delta.npy")))
    figC(np.load(os.path.join(HERE, "delta_b1.npy")),
         np.load(os.path.join(HERE, "prior_delta.npy")))
