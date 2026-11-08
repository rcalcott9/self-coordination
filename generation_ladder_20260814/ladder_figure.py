"""
Cross-generation ladder figure. OpenAI and Anthropic kept visually separate.

TOP    policy-specific structure: rho(own-copy match, generic salience). LOW is what
       the design needs - reliability that public salience does not already predict.
BOTTOM strategic selectivity: mean high-minus-low ATTEMPT gap across that generation's
       OWN selected pairs. Rungs where Stage C could not run are marked on the axis,
       NOT interpolated.

Deliberately no fitted trend line: 3-4 usable points per family cannot support one, and
two of eight rungs have no Stage C value at all.

Run:  python3 ladder_figure.py
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.linewidth": 0.8, "axes.edgecolor": "black", "text.color": "black",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out",
    "axes.grid": False, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
})

OPEN = dict(marker="o", markerfacecolor="white", markeredgecolor="black",
            markersize=6.5, markeredgewidth=1.2, linestyle="none")
FILL = dict(marker="o", markerfacecolor="black", markeredgecolor="black",
            markersize=6.5, linestyle="none")


def main():
    per = json.load(open(os.path.join(ROOT, "analysis", "ladder_per_model.json")))
    tab = {r["model"]: r for r in
           json.load(open(os.path.join(ROOT, "analysis", "ladder_table.json")))}
    fams = [("OpenAI", ["GPT-4o", "GPT-5", "GPT-5.4", "GPT-5.5"]),
            ("Anthropic", ["Opus 4.5", "Opus 4.6", "Opus 4.8", "Opus 5"])]

    fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.0), sharex="col")
    for col, (fam, names) in enumerate(fams):
        xs = range(len(names))

        # --- top: policy-specific structure ---
        ax = axes[0][col]
        ys = [tab.get(n, {}).get("rho_sal") for n in names]
        ok = [(x, y) for x, y in zip(xs, ys) if y is not None]
        if len(ok) > 1:
            ax.plot([p[0] for p in ok], [p[1] for p in ok], color="0.55", lw=1.0, zorder=1)
        for x, y in ok:
            ax.plot([x], [y], **FILL, zorder=3)
        for x, n in zip(xs, names):
            if tab.get(n, {}).get("rho_sal") is None:
                ax.text(x, 0.05, "no\ndata", ha="center", va="bottom", fontsize=6.5,
                        color="0.45")
        ax.set_ylim(-0.05, 1.0); ax.set_yticks([0, .25, .5, .75, 1.0])
        ax.set_title(fam, fontsize=10, pad=6)
        if col == 0:
            ax.set_ylabel("reliability explained by\npublic salience  (Spearman $\\rho$)")

        # --- bottom: strategic selectivity ---
        ax = axes[1][col]
        pm = {r["model"]: r for r in per}
        ys = [pm.get(n, {}).get("mean_gap") for n in names]
        ok = [(x, y) for x, y in zip(xs, ys) if y is not None]
        if len(ok) > 1:
            ax.plot([p[0] for p in ok], [p[1] for p in ok], color="0.55", lw=1.0, zorder=1)
        for x, y in ok:
            r = pm[names[x]]
            sty = FILL if r.get("perm_p", 1) < 0.05 else OPEN
            ax.plot([x], [y], **sty, zorder=3)
        ax.axhline(0, color="black", lw=0.8, ls=":")
        for x, n in zip(xs, names):
            if pm.get(n, {}).get("mean_gap") is None:
                why = {"GPT-4o": "no admissible\npairs",
                       "Opus 4.5": "payoff\nsaturated",
                       "Opus 4.6": "competence\ngate"}.get(n, "not run")
                ax.text(x, 0.005, why, ha="center", va="bottom", fontsize=6.5,
                        color="0.45", style="italic")
        ax.set_ylim(-0.03, 0.22); ax.set_yticks([0, .05, .10, .15, .20])
        ax.set_xticks(list(xs)); ax.set_xticklabels(names, fontsize=8)
        ax.set_xlim(-0.5, len(names) - 0.5)
        if col == 0:
            ax.set_ylabel("strategic selectivity\nmean high-minus-low P(attempt)")

    fig.legend(handles=[Line2D([], [], **FILL, label="permutation p < 0.05"),
                        Line2D([], [], **OPEN, label="not significant")],
               loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.06), fontsize=8)
    fig.suptitle("Strategic selectivity, and the structure it requires, across model "
                 "generations", fontsize=11, y=1.02)
    fig.tight_layout()
    for e in ("png", "pdf"):
        fig.savefig(os.path.join(ROOT, "figures", f"ladder_summary.{e}"),
                    facecolor="white")
    plt.close(fig)
    print("-> figures/ladder_summary.png / .pdf")


if __name__ == "__main__":
    main()
