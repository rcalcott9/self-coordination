"""Two-panel figure: stated confidence vs true own-copy match, and what betting tracks."""
import csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.style.use("academic")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "figures")
os.makedirs(OUT, exist_ok=True)

recs = list(csv.DictReader(open(os.path.join(HERE, "..", "data", "cell_table.csv"))))
for r in recs:
    for k in r:
        if k not in ("model", "stimulus", "modal"):
            r[k] = float(r[k])

G = [r for r in recs if r["model"] == "gpt-5.4"]
C = [r for r in recs if r["model"] == "claude-opus-4-8"]
G.sort(key=lambda r: r["stimulus"]); C.sort(key=lambda r: r["stimulus"])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(5.5, 2.9))

# -- Panel A: stated vs true -------------------------------------------------
ax1.plot([0.45, 1.02], [0.45, 1.02], color="0.6", lw=0.8, ls=(0, (4, 3)), zorder=1)
ax1.plot([r["true_match"] for r in G], [r["stated_p"] for r in G],
         "o", mfc="k", mec="k", ms=4.5, lw=0, label="GPT-5.4", zorder=3)
ax1.plot([r["true_match"] for r in C], [r["stated_p"] for r in C],
         "s", mfc="none", mec="k", mew=0.9, ms=4.5, lw=0,
         label="Claude Opus 4.8", zorder=3)

# the inkblot crossover: same image, opposite reliability, same stated P
gi = [r for r in G if r["stimulus"] == "inkblot"][0]
ci = [r for r in C if r["stimulus"] == "inkblot"][0]
ax1.plot([ci["true_match"], gi["true_match"]], [ci["stated_p"], gi["stated_p"]],
         "-", color="k", lw=0.8, zorder=2)
ARR = dict(arrowstyle="-", lw=0.7, color="0.35",
           shrinkA=1, shrinkB=3)
ax1.annotate("inkblot, Claude\nat chance (0.49)",
             xy=(ci["true_match"], ci["stated_p"]), xytext=(0.545, 0.925),
             ha="left", va="top", fontsize=7, arrowprops=ARR)
ax1.annotate("inkblot, GPT\nnear-perfect (0.97)",
             xy=(gi["true_match"], gi["stated_p"]), xytext=(1.005, 0.452),
             ha="right", va="bottom", fontsize=7, arrowprops=ARR)

ax1.set_xlabel("True own-copy match rate")
ax1.set_ylabel("Stated coordination probability")
ax1.set_xlim(0.44, 1.04); ax1.set_ylim(0.44, 1.04)
ax1.set_xticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
ax1.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
ax1.legend(frameon=False, loc="upper left", fontsize=7.5, handletextpad=0.4,
           borderaxespad=0.2)
ax1.text(0.02, 0.02, "A", transform=ax1.transAxes, fontsize=10, va="bottom")

# -- Panel B: partial correlations -------------------------------------------
labels = ["true match\n(raw)", "stated P\n(raw)",
          "true match\n| stated P", "stated P\n| true match"]
vals = [0.590, 0.785, -0.026, 0.642]
lo = [0.0, 0.0, -0.464, 0.532]   # leave-one-out range for the partials
hi = [0.0, 0.0, 0.140, 0.852]
x = np.arange(4)
ax2.axhline(0, color="k", lw=0.8, zorder=1)
for i, (v, a, b) in enumerate(zip(vals, lo, hi)):
    fc = "k" if i in (0, 2) else "none"
    ax2.plot([i], [v], "o" if i in (0, 2) else "s", mfc=fc, mec="k", mew=0.9,
             ms=5, zorder=3)
    if i >= 2:
        ax2.plot([i, i], [a, b], "-", color="k", lw=0.9, zorder=2)
        ax2.plot([i - 0.07, i + 0.07], [a, a], "-", color="k", lw=0.9, zorder=2)
        ax2.plot([i - 0.07, i + 0.07], [b, b], "-", color="k", lw=0.9, zorder=2)
ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=7)
ax2.set_ylabel("Correlation with attempt rate")
ax2.set_xlim(-0.5, 3.5); ax2.set_ylim(-0.65, 1.0)
ax2.text(0.02, 0.02, "B", transform=ax2.transAxes, fontsize=10, va="bottom")

fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT, f"confidence_residual.{ext}"), dpi=300)
print("wrote", os.path.join(OUT, "confidence_residual.[png|pdf]"))
