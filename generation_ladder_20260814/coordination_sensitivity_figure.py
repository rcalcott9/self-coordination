"""
Publication figure: policy-specific coordination sensitivity across model generations.

ONE quantity only - the Stage C effect

    mean P(ATTEMPT | higher own-copy reliability)
  - mean P(ATTEMPT | lower  own-copy reliability)

Salience correlations, payoff sensitivity and competence metrics are deliberately NOT
plotted; they belong in the text.

OPUS 4.6 WAS RECLASSIFIED 2026-08-18, from competence_gate_failed to payoff_saturated.
The Aug-14 gate excluded it on a 2-stimulus n=24 screen; the full battery (45 stimuli,
n=60) shows 25 clean form rules and A_sd 0.232, the LARGEST of any rung, and the frozen
selector returned 8 pairs, 7 of them `ideal`. It drops out one gate later, on the same
criterion as Opus 4.5: ATTEMPT at SAFE=9 = 0.963 against a 0.95 limit, payoff drop
0.006. Its place on the x-axis and its NA label are unchanged; only the stated reason
moves. Both early Anthropic rungs are now excluded for the same thing - always playing,
never pricing the safe option.

MISSING RUNGS ARE NOT ZEROS. Three generations have no interpretable Stage C estimate.
They keep their place on the x-axis and are marked "NA" in the tick label - below the
axis, not inside the plot area - so nothing can be read as a value near zero. No line
segment crosses a missing rung: the drawn segments connect only adjacent OBSERVED
generations, which happen to be contiguous in both families.

No regression line, no significance markers, y-axis anchored at 0 so the points read
directly as probability-point differences.

Run:  python3 coordination_sensitivity_figure.py
"""
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(ROOT, "figures")

# Opus 4.7 has TWO estimates. The plotted value is the PROSPECTIVE 8-pair sample
# (mean +0.063, 5/8 positive, permutation p = 0.00005), which is the preferred estimate
# because it is larger, independent, and shares no stimulus with the first sample. The
# initial 3-pair sample (-0.103) is shown as a secondary marker rather than dropped or
# averaged in - the two samples disagree in sign and the reader should see that.
SECONDARY = {("Anthropic", "Opus 4.7"): (-0.103, "initial 3-pair"),
             ("Anthropic", "Opus 4.8"): (0.033, "initial 2-pair")}

# provider, model, generation_order, sensitivity (None = no estimate), status
DATA = [
    ("OpenAI",    "GPT-4o",   1, None,   "not_identifiable"),
    ("OpenAI",    "GPT-5",    2,  0.008, "observed"),
    ("OpenAI",    "GPT-5.4",  3,  0.081, "observed"),
    ("OpenAI",    "GPT-5.5",  4,  0.175, "observed"),
    ("Anthropic", "Opus 4.5", 1, None,   "payoff_saturated"),
    ("Anthropic", "Opus 4.6", 2, None,   "payoff_saturated"),
    ("Anthropic", "Opus 4.7", 3,  0.063, "observed"),
    ("Anthropic", "Opus 4.8", 4,  0.026, "observed"),
    ("Anthropic", "Opus 5",   5,  0.100, "observed"),
]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5, "legend.fontsize": 8.5,
    "axes.linewidth": 0.8, "axes.edgecolor": "black", "text.color": "black",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out",
    "axes.grid": False, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
})

# marker AND linestyle differ, so the figure survives greyscale printing
STY = {"OpenAI":    dict(marker="o", markerfacecolor="black", markeredgecolor="black",
                         markersize=7, linestyle="-", linewidth=1.2, color="black"),
       "Anthropic": dict(marker="s", markerfacecolor="white", markeredgecolor="black",
                         markersize=6.8, markeredgewidth=1.2, linestyle="--",
                         linewidth=1.2, color="black")}


def main():
    os.makedirs(FIGS, exist_ok=True)
    # Two panels: the families now have different numbers of generations (4 vs 5), so a
    # shared x-axis would force a false alignment between them.
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4), sharey=True,
                             gridspec_kw={"width_ratios": [4, 5]})

    for ax, prov in zip(axes, ("OpenAI", "Anthropic")):
        rows = sorted([d for d in DATA if d[0] == prov], key=lambda d: d[2])
        xs = [d[2] for d in rows if d[3] is not None]
        ys = [d[3] for d in rows if d[3] is not None]
        ax.axhline(0, color="black", lw=0.8, ls=":", zorder=1)
        ax.plot(xs, ys, **STY[prov], zorder=3)
        for d in rows:
            sec = SECONDARY.get((prov, d[1]))
            if sec and d[3] is not None:
                v, note = sec
                ax.plot([d[2], d[2]], [v, d[3]], color="0.65", lw=0.9, ls="-", zorder=2)
                ax.plot([d[2]], [v], marker="s", markerfacecolor="0.75",
                        markeredgecolor="0.45", markersize=5, linestyle="none", zorder=3)
                ax.annotate(note, (d[2], v), textcoords="offset points",
                            xytext=(9, -1), ha="left", va="center", fontsize=6.8,
                            color="0.35", style="italic")
                ax.annotate(f"{v:+.3f}".replace("0.", "."), (d[2], v),
                            textcoords="offset points", xytext=(-9, -1), ha="right",
                            va="center", fontsize=7.5, color="0.35")
        for x, y in zip(xs, ys):
            off = 9 if y >= 0 else -15
            ax.annotate(f"{y:+.3f}".replace("0.", "."), (x, y),
                        textcoords="offset points", xytext=(0, off),
                        ha="center", fontsize=8.5)
        ax.set_xticks([d[2] for d in rows])
        ax.set_xticklabels([d[1] + ("" if d[3] is not None else "\nNA")
                            for d in rows], fontsize=8)
        ax.set_xlim(0.5, len(rows) + 0.5)
        ax.set_title(prov, fontsize=9.5, pad=6)
        ax.tick_params(axis="x", length=3, pad=4)

    axes[0].set_ylim(-0.16, 0.22)
    axes[0].set_yticks([-0.15, -0.10, -0.05, 0, 0.05, 0.10, 0.15, 0.20])
    axes[0].set_ylabel("Policy-specific coordination sensitivity")

    fig.suptitle("Policy-specific coordination sensitivity across model generations",
                 fontsize=10.5, y=1.10)
    fig.text(0.5, 1.035, "$\\Delta$ P(ATTEMPT): higher- vs lower-own-copy-reliability "
             "stimulus", ha="center", fontsize=8.5)
    fig.text(0.5, -0.22, "Points show the mean difference in ATTEMPT probability "
             "between matched stimuli with higher versus lower\nown-copy coordination "
             "reliability. Missing generations lacked an interpretable Stage C "
             "estimate.", ha="center", fontsize=7.5, color="0.25")
    fig.tight_layout()

    for e in ("png", "pdf"):
        fig.savefig(os.path.join(FIGS, f"coordination_sensitivity_ladder.{e}"),
                    facecolor="white")
    plt.close(fig)

    with open(os.path.join(FIGS, "coordination_sensitivity_ladder.csv"), "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["provider", "model", "generation_order",
                    "coordination_sensitivity", "status", "note"])
        w_extra = {("Anthropic", "Opus 4.7"): "prospective 8-pair sample; initial "
                                               "3-pair sample was -0.103",
                   ("Anthropic", "Opus 4.8"): "prospective 7-pair sample; initial "
                                               "2-pair sample was +0.033",
                   ("Anthropic", "Opus 4.6"): "reclassified 2026-08-18: the Aug-14 "
                                              "competence-gate failure was a stimulus "
                                              "artifact (25/45 clean form rules, A_sd "
                                              "0.232, highest of any rung). 8 ideal "
                                              "pairs selected; excluded on payoff "
                                              "saturation, ATTEMPT at SAFE=9 = 0.963, "
                                              "drop 0.006"}
        for prov, model, order, val, status in DATA:
            w.writerow([prov, model, order, "" if val is None else f"{val:.3f}",
                        status, w_extra.get((prov, model), "")])

    print("-> figures/coordination_sensitivity_ladder.png / .pdf / .csv")
    for prov, model, order, val, status in DATA:
        print(f"   {prov:10}{model:9}{order}  "
              f"{('' if val is None else f'{val:+.3f}'):>7}  {status}")


if __name__ == "__main__":
    main()
