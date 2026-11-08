"""Pair-level high-minus-low ATTEMPT gaps: original 3 pairs vs new prospective 8."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 8, "axes.linewidth": 0.8, "axes.edgecolor": "black",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out", "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight"})

d = json.load(open(os.path.join(ROOT, "analysis", "opus47_robustness.json")))
rows = ([(n, g, "orig") for n, g in zip(d["original_sample"]["pairs"],
                                        d["original_sample"]["gaps"])]
        + [(n, g, "new") for n, g in zip(d["new_sample"]["pairs"],
                                         d["new_sample"]["gaps"])])
fig, ax = plt.subplots(figsize=(6.0, 4.2))
ax.axvline(0, color="black", lw=0.9, ls=":", zorder=1)
ys = list(range(len(rows)))[::-1]
for y, (name, gap, grp) in zip(ys, rows):
    is_rot = name.startswith("rot >")
    sty = (dict(marker="o", markerfacecolor="black", markeredgecolor="black")
           if grp == "orig" else
           dict(marker="s", markerfacecolor="white", markeredgecolor="black",
                markeredgewidth=1.2))
    ax.plot([0, gap], [y, y], color="0.6", lw=0.9, zorder=2)
    ax.plot([gap], [y], markersize=8 if is_rot else 6.5, linestyle="none",
            zorder=3, **sty)
    if is_rot:
        # label to the RIGHT of the marker; on the left it collided with the tick label
        ax.annotate("original reversal", (gap, y), textcoords="offset points",
                    xytext=(11, 0), ha="left", va="center", fontsize=7.5,
                    style="italic")
ax.set_yticks(ys)
ax.set_yticklabels([n.replace(" > ", "\n  > ") for n, _, _ in rows], fontsize=6.8)
ax.set_ylim(-0.8, len(rows) - 0.2)
ax.set_xlim(-0.35, 0.55)
ax.set_xlabel("$\\Delta$ P(ATTEMPT), higher minus lower own-copy reliability")
ax.legend(handles=[Line2D([], [], marker="o", markerfacecolor="black",
                          markeredgecolor="black", linestyle="none", markersize=6.5,
                          label=f"original 3 pairs (mean {d['original_sample']['mean_gap']:+.3f})"),
                   Line2D([], [], marker="s", markerfacecolor="white",
                          markeredgecolor="black", markeredgewidth=1.2,
                          linestyle="none", markersize=6.5,
                          label=f"new prospective 8 pairs (mean {d['new_sample']['mean_gap']:+.3f})")],
          loc="lower right", fontsize=8)
fig.suptitle("Opus 4.7: pair-level coordination sensitivity, original vs new sample",
             fontsize=10.5, y=1.01)
fig.tight_layout()
for e in ("png", "pdf"):
    fig.savefig(os.path.join(ROOT, "figures", f"opus47_robustness_pair_effects.{e}"),
                facecolor="white")
print("-> figures/opus47_robustness_pair_effects.png / .pdf")
