"""
Cross-family convention agreement, both domains. One dot = one item.

Dot-histogram: items stack at the agreement value they take, so the shape IS the
distribution and every item is still individually visible. Only the items at the two
extremes are named - everything in between is a count, not a label.
"""
import csv, itertools, os, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("academic")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "analysis", "out")
ORD = ["gpt-4-turbo-2024-04-09", "gpt-4.1-2025-04-14", "gpt-5-2025-08-07",
       "gpt-5.5-2026-04-23", "claude-opus-4-5-20251101", "claude-opus-4-6",
       "claude-opus-4-7", "claude-opus-4-8", "claude-opus-5"]
XPAIRS = [(a, b) for a, b in itertools.combinations(ORD, 2)
          if a.startswith("gpt") != b.startswith("gpt")]


def load(path, keep=None):
    d = {}
    for r in csv.DictReader(open(path)):
        if keep and r.get("dataset") != keep:
            continue
        d[(r["item_id"], r["model_id"])] = (int(r["modal_identity"]), float(r["modal_share"]))
    items = sorted({i for i, _ in d})
    return {i: (np.mean([d[(i, a)][0] == d[(i, b)][0] for a, b in XPAIRS]),
                np.mean([d[(i, m)][1] for m in ORD])) for i in items}


CODE = load(os.path.join(OUT, "e18", "cell_metrics.csv"), "C_combined_17")
VIS = load(os.path.join(OUT, "stage1_frame", "cell_metrics.csv"))
BINS = np.arange(0, 1.0001, 0.05)

fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
fig.subplots_adjust(bottom=.30, wspace=.13)
for ax, data, title, strip in ((axes[0], CODE, "Code  ·  17 items", ("code_", "x_")),
                               (axes[1], VIS, "Visual  ·  41 arrays", ("",))):
    stack = collections.defaultdict(list)
    for it, (agr, hold) in data.items():
        stack[BINS[np.clip(np.digitize(agr, BINS) - 1, 0, len(BINS) - 2)]].append((it, hold))
    for x, group in stack.items():
        for k, (it, hold) in enumerate(sorted(group, key=lambda g: -g[1])):
            ax.plot(x, k + .5, "o", ms=7.5, markerfacecolor=plt.cm.Greys(.25 + .6 * hold),
                    markeredgecolor="#1D2027", markeredgewidth=.8, zorder=3)
    top = max(len(v) for v in stack.values())
    ax.set_title(title, fontsize=9.5, pad=10)
    ax.set_xlabel("Cross-family modal agreement")
    ax.set_xlim(-.06, 1.16); ax.set_ylim(0, max(top + 2.0, 8))
    ax.set_xticks([0, .25, .5, .75, 1.0])
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)

axes[0].set_ylabel("Number of items")
axes[0].set_yticks(range(0, 20, 5))

h = [plt.Line2D([], [], ls="", marker="o", ms=7.5, markeredgecolor="#1D2027",
                markerfacecolor=plt.cm.Greys(.25 + .6 * v),
                label=f"{v:.0%}") for v in (.3, .6, .9)]
fig.legend(handles=h, frameon=False, ncol=3, fontsize=8, loc="lower center",
           bbox_to_anchor=(.5, .015),
           title="Mean modal share — how firmly the convention is held",
           title_fontsize=8, handletextpad=.2, columnspacing=1.6)
fig.text(.5, .155, "One dot = one item. Agreement is over the 20 GPT x Claude "
         "checkpoint pairs. Items are not labelled; see caption.",
         ha="center", fontsize=7.5, style="italic")

for ext, kw in ((".pdf", {}), (".png", dict(dpi=300))):
    fig.savefig(os.path.join(OUT, "conventions_simple" + ext),
                facecolor="white", **kw)
print("wrote conventions_simple.pdf / .png")
for nm, d in (("code", CODE), ("visual", VIS)):
    v = [a for a, _ in d.values()]
    print(f"  {nm:7} n={len(v):2d}  at 1.00: {sum(1 for x in v if x==1):2d}  "
          f"at 0.00: {sum(1 for x in v if x==0)}  median {np.median(v):.2f}")
