"""The finding, in one figure.

The same-model entry premium is large, and it is the SAME SIZE whether the focal
model's own convention on that stimulus is strong or weak. The bracketed gaps are
the point: they barely move across the x-axis, which is beta3 ~ 0.

Deliberately plain: two panels, four points each, gaps annotated, estimate and CI
stated on the panel. No third panel, no secondary measure.
"""
import os, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import s4_common as S

plt.style.use("academic")
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "figures")
os.makedirs(FIG, exist_ok=True)

rows = [r for r in csv.DictReader(open(os.path.join(S.DATA, "stageC_pilot_results.csv")))
        if r["parse_ok"] == "True"]

# beta3 with family-bootstrap CI, from the corrected analysis
B3 = {"gpt": (-0.022, -0.102, +0.067), "claude": (-0.025, -0.093, +0.041)}


def rate(focal, level, same):
    v = [int(r["attempt"]) for r in rows if r["focal"] == focal
         and r["level"] == level and r["partner_same"] == same]
    return np.mean(v), np.std(v, ddof=1) / np.sqrt(len(v))


fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.0), sharey=True)
X = [0, 1]
LEV = ["LOW", "HIGH"]

for ax, focal in zip(axes, ("gpt", "claude")):
    for same, mk, mfc, ls, lab in (("1", "o", "k", "-", "same-model partner"),
                                   ("0", "s", "none", "--", "different model")):
        y = [rate(focal, l, same)[0] for l in LEV]
        e = [rate(focal, l, same)[1] for l in LEV]
        ax.errorbar(X, y, yerr=e, fmt=mk, mfc=mfc, mec="k", mew=0.9, ms=5,
                    color="k", lw=1.0, ls=ls, capsize=2.5, elinewidth=0.8,
                    label=lab, zorder=3)

    # the gap at each level - this is what the finding is about
    for xi, lev in zip(X, LEV):
        hi = rate(focal, lev, "1")[0]
        lo = rate(focal, lev, "0")[0]
        # brackets sit OUTSIDE the data range so they never cross the lines
        xo = -0.30 if xi == 0 else 1.30
        ax.annotate("", xy=(xo, hi), xytext=(xo, lo),
                    arrowprops=dict(arrowstyle="<->", lw=0.8, color="0.35",
                                    shrinkA=0, shrinkB=0), zorder=2)
        ax.text(xo + (-0.06 if xi == 0 else 0.06), (hi + lo) / 2,
                f"{hi-lo:+.2f}", fontsize=7.5, color="0.2",
                ha="right" if xi == 0 else "left", va="center")

    b, lo_, hi_ = B3[focal]
    ax.set_xticks(X)
    ax.set_xticklabels(["weak own\nconvention", "strong own\nconvention"])
    ax.set_xlim(-0.62, 1.62)
    ax.set_ylim(0, 1.14)
    ax.text(0.5, 0.995, S.DISPLAY[focal], transform=ax.transAxes, ha="center",
            va="top", fontsize=8.5)
    ax.text(0.5, 0.925, f"interaction {b:+.3f}  [{lo_:+.3f}, {hi_:+.3f}]",
            transform=ax.transAxes, ha="center", va="top", fontsize=7,
            color="0.3")

axes[0].set_ylabel("P(enter the coordination game)")
axes[0].legend(frameon=False, fontsize=7.5, loc="lower left",
               handletextpad=0.6, borderaxespad=0.4)

fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(FIG, f"finding.{ext}"), dpi=300)
print("wrote", os.path.join(FIG, "finding.[png|pdf]"))
