"""
Modal convention by item x checkpoint, both domains side by side.

One cell = the option a checkpoint chose most often on that item, at n=48.
Letter = which canonical option. Shading = how firmly held (modal share), so a
convention that is held 48/48 reads darker than one held 20/48.

Items are ordered by cross-family modal agreement, so loci where GPT and Claude
disagree sit at the top of each panel.
"""
import csv, itertools, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
plt.style.use("academic")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "analysis", "out")
ORD = ["gpt-4-turbo-2024-04-09", "gpt-4.1-2025-04-14", "gpt-5-2025-08-07",
       "gpt-5.5-2026-04-23", "claude-opus-4-5-20251101", "claude-opus-4-6",
       "claude-opus-4-7", "claude-opus-4-8", "claude-opus-5"]
SHORT = ["GPT-4-turbo\n2024-04", "GPT-4.1\n2025-04", "GPT-5\n2025-08", "GPT-5.5\n2026-04",
         "Opus 4.5\n2025-11", "Opus 4.6\n2026-02", "Opus 4.7\n2026-04",
         "Opus 4.8\n2026-05", "Opus 5\n2026-07"]


def grid(path, keep=None, strip=""):
    rows = [r for r in csv.DictReader(open(path))
            if keep is None or r.get("dataset") == keep]
    d = {}
    for r in rows:
        d[(r["item_id"], r["model_id"])] = (int(r["modal_identity"]), float(r["modal_share"]))
    items = sorted({i for i, _ in d})
    xf = {}
    for it in items:
        pairs = [(a, b) for a, b in itertools.combinations(ORD, 2)
                 if a.startswith("gpt") != b.startswith("gpt")]
        xf[it] = np.mean([d[(it, a)][0] == d[(it, b)][0] for a, b in pairs])
    items.sort(key=lambda i: (xf[i], i))
    M = np.array([[d[(i, m)][0] for m in ORD] for i in items])
    S = np.array([[d[(i, m)][1] for m in ORD] for i in items])
    return items, M, S, xf, strip


CODE = grid(os.path.join(OUT, "e18", "cell_metrics.csv"), "C_combined_17", "code_|x_")
VIS = grid(os.path.join(OUT, "stage1_frame", "cell_metrics.csv"), None, "")

cmap = LinearSegmentedColormap.from_list("hold", ["#FFFFFF", "#3A4152"])
n_c, n_v = len(CODE[0]), len(VIS[0])
fig = plt.figure(figsize=(7.1, 8.4))
gs = fig.add_gridspec(2, 1, height_ratios=[n_c, n_v], hspace=.13)

for ax_i, (items, M, S, xf, strip) in enumerate((CODE, VIS)):
    ax = fig.add_subplot(gs[ax_i])
    ax.imshow(S, cmap=cmap, vmin=.25, vmax=1.0, aspect="auto")
    for i in range(len(items)):
        for j in range(len(ORD)):
            ax.text(j, i, "ABCD"[M[i, j]], ha="center", va="center", fontsize=7.2,
                    color="white" if S[i, j] > .68 else "#1D2027")
    lbl = []
    for i in items:
        s = i
        for pre in strip.split("|"):
            if pre and s.startswith(pre):
                s = s[len(pre):]
        lbl.append(f"{s}   {xf[i]:.2f}")
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels(lbl, fontsize=6.6, fontfamily="monospace")
    ax.set_xticks(np.arange(-.5, len(ORD), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(items), 1), minor=True)
    ax.grid(which="minor", color="white", lw=1.1)
    ax.tick_params(which="minor", length=0)
    ax.axvline(3.5, color="#1D2027", lw=1.6)
    for s_ in ax.spines.values():
        s_.set_visible(False)
    if ax_i == 0:
        ax.set_xticks(range(len(ORD)))
        ax.set_xticklabels(SHORT, fontsize=6.6)
        ax.xaxis.set_ticks_position("top")
        ax.tick_params(axis="x", length=0, pad=3)
        ax.set_ylabel("CODE  ·  17 items", fontsize=8.5, labelpad=8)
    else:
        ax.set_xticks([])
        ax.set_ylabel("VISUAL  ·  41 arrays", fontsize=8.5, labelpad=8)

cax = fig.add_axes([.915, .40, .013, .20])
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(.25, 1.0))
cb = fig.colorbar(sm, cax=cax)
cb.set_label("modal share (how firmly the convention is held)", fontsize=7, labelpad=6)
cb.set_ticks([.25, .5, .75, 1.0]); cb.ax.tick_params(labelsize=6.5)
cb.outline.set_visible(False)
fig.text(.915, .335, "row label suffix =\ncross-family\nmodal agreement",
         fontsize=6.6, va="top")

for ext, kw in ((".pdf", {}), (".png", dict(dpi=300))):
    fig.savefig(os.path.join(OUT, "conventions_map" + ext), bbox_inches="tight",
                facecolor="white", **kw)
print("wrote", os.path.join(OUT, "conventions_map.pdf / .png"))
print(f"  code: {n_c} items, {sum(1 for i in CODE[0] if CODE[3][i]==0)} at cross-family agreement 0.00")
print(f"  visual: {n_v} arrays, {sum(1 for i in VIS[0] if VIS[3][i]==0)} at 0.00, "
      f"{sum(1 for i in VIS[0] if VIS[3][i]==1)} at 1.00")
