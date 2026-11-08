"""E18 figures. Academic style, grayscale, no in-plot prose. PDF + 300 dpi PNG."""
import csv, json, os, collections, itertools
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("academic")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "analysis", "out", "e18")
S = json.load(open(os.path.join(SRC, "summary.json")))
cells = list(csv.DictReader(open(os.path.join(SRC, "cell_metrics.csv"))))
pairs = list(csv.DictReader(open(os.path.join(SRC, "pair_metrics.csv"))))
ORD = ["gpt-4-turbo-2024-04-09", "gpt-4.1-2025-04-14", "gpt-5-2025-08-07",
       "gpt-5.5-2026-04-23", "claude-opus-4-5-20251101", "claude-opus-4-6",
       "claude-opus-4-7", "claude-opus-4-8", "claude-opus-5"]
VIN = {m: S["C_combined_17"]["by_checkpoint"][m]["vintage"] for m in ORD}
FAMG = {m: ("gpt" if m.startswith("gpt") else "claude") for m in ORD}


def save(fig, name):
    for ext, kw in ((".pdf", {}), (".png", dict(dpi=300))):
        fig.savefig(os.path.join(SRC, name + ext), bbox_inches="tight",
                    facecolor="white", **kw)
    plt.close(fig)
    print("wrote", name)


# ---- Figure 1: fraction deterministic by checkpoint -------------------------
fig, ax = plt.subplots(figsize=(5.5, 3.2))
for key, lab, mk, fc, ls in (("A_original_12", "original battery (12 items)", "o", "k", "-"),
                             ("B_expansion_5", "expansion battery (5 items)", "s", "white", "--")):
    xs = [VIN[m] for m in ORD]
    ys = [S[key]["by_checkpoint"][m]["frac_deterministic"] for m in ORD]
    o = np.argsort(xs)
    ax.plot(np.array(xs)[o], np.array(ys)[o], ls, color="k", lw=1.1, marker=mk,
            ms=5, markerfacecolor=fc, markeredgecolor="k", markeredgewidth=.9, label=lab)
ax.set_xlabel("Checkpoint vintage (years since 2025-01)")
ax.set_ylabel("Proportion of cells fully deterministic\n(same option on all 48 trials)")
ax.set_ylim(-.03, .85); ax.set_xlim(-.9, 1.7)
ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, 1.18), fontsize=8, ncol=1)
for s in ("top", "right"): ax.spines[s].set_visible(False)
save(fig, "e18_fig1_determinism")

# ---- Figure 2: decomposition over vintage, combined battery -----------------
fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.9), sharey=True)
for ax, key, lab in zip(axes, ("A_original_12", "B_expansion_5", "C_combined_17"),
                        ("A  original 12", "B  expansion 5", "C  combined 17")):
    P = [r for r in pairs if r["dataset"] == key]
    g = collections.OrderedDict()
    for r in P:
        g.setdefault((r["model_a"], r["model_b"]), []).append(r)
    x = np.array([float(v[0]["vintage"]) for v in g.values()])
    for stat, mk, fc, ls in (("log_cross_match", "o", "k", "-"),
                             ("determinism_channel", "^", "k", "-"),
                             ("alignment_channel", "D", "white", "--")):
        y = np.array([np.mean([float(r[stat]) for r in v]) for v in g.values()])
        ax.scatter(x, y, s=11, marker=mk, facecolors=fc, edgecolors="k",
                   linewidths=.6, zorder=3)
        m, b = np.polyfit(x, y, 1)
        gx = np.linspace(x.min(), x.max(), 30)
        ax.plot(gx, m * gx + b, ls, color="k", lw=1.1, zorder=2)
    ax.set_xlabel("Vintage (yr since 2025-01)", fontsize=8)
    ax.set_title(lab, fontsize=8.5, pad=6)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
axes[0].set_ylabel("log expected agreement")
h = [plt.Line2D([], [], color="k", marker="o", ls="-", ms=4, lw=1.1, label="total"),
     plt.Line2D([], [], color="k", marker="^", ls="-", ms=4, lw=1.1, label="determinism channel"),
     plt.Line2D([], [], color="k", marker="D", ls="--", ms=4, lw=1.1,
                markerfacecolor="white", label="alignment channel")]
fig.legend(handles=h, frameon=False, ncol=3, fontsize=8, loc="lower center",
           bbox_to_anchor=(.5, -.13))
save(fig, "e18_fig2_decomposition")

# ---- Figure 3: das slope, within vs cross family, all three datasets --------
fig, ax = plt.subplots(figsize=(5.5, 3.0))
rows, y = [], 0
for key, lab in (("C_combined_17", "combined 17"), ("B_expansion_5", "expansion 5"),
                 ("A_original_12", "original 12")):
    for pt, ptl in (("cross_family", "cross family"), ("within_family", "within family")):
        v = S[key]["das_by_pair_type"][pt]
        rows.append((y, v["slope"], v["lo"], v["hi"], f"{lab} · {ptl}", pt)); y += 1
    y += .6
ax.axvline(0, color="k", lw=.9, ls=(0, (4, 3)), zorder=1)
for yy, s, lo, hi, lab, pt in rows:
    ax.plot([lo, hi], [yy, yy], "-", color="k", lw=1.1, zorder=2)
    for e in (lo, hi):
        ax.plot([e, e], [yy - .12, yy + .12], "-", color="k", lw=1.1, zorder=2)
    ax.plot(s, yy, "o" if pt == "within_family" else "s", ms=5, color="k",
            markerfacecolor="k" if pt == "within_family" else "white",
            markeredgewidth=1.0, zorder=3)
ax.set_yticks([r[0] for r in rows]); ax.set_yticklabels([r[4] for r in rows], fontsize=8)
ax.set_xlabel("Determinism-adjusted similarity slope per year\n"
              "(95% item-clustered bootstrap CI)")
ax.set_ylim(-.8, max(r[0] for r in rows) + .8)
ax.invert_yaxis()
for s in ("top", "right"): ax.spines[s].set_visible(False)
save(fig, "e18_fig3_das_slopes")

# ---- Figure 4: modal convention matrix, expansion battery -------------------
E = [r for r in cells if r["dataset"] == "B_expansion_5"]
items = sorted({r["item_id"] for r in E})
M = np.zeros((len(items), len(ORD)))
for r in E:
    M[items.index(r["item_id"]), ORD.index(r["model_id"])] = int(r["modal_identity"])
fig, ax = plt.subplots(figsize=(5.9, 2.6))
ax.imshow(M, cmap="Greys", vmin=-.6, vmax=3.9, aspect="auto")
for i in range(len(items)):
    for j in range(len(ORD)):
        ax.text(j, i, "ABCD"[int(M[i, j])], ha="center", va="center", fontsize=8,
                color="white" if M[i, j] > 1.6 else "black")
ax.set_xticks(range(len(ORD)))
ax.set_xticklabels([m.replace("claude-opus-", "opus ").replace("-2024-04-09", "")
                    .replace("-2025-04-14", "").replace("-2025-08-07", "")
                    .replace("-2026-04-23", "").replace("-20251101", "")
                    for m in ORD], rotation=45, ha="right", fontsize=7.5)
ax.set_yticks(range(len(items)))
ax.set_yticklabels([i.replace("x_", "") for i in items], fontsize=8)
ax.set_xticks(np.arange(-.5, len(ORD), 1), minor=True)
ax.set_yticks(np.arange(-.5, len(items), 1), minor=True)
ax.grid(which="minor", color="white", lw=1.4)
ax.tick_params(which="minor", length=0)
ax.axvline(3.5, color="k", lw=1.4)
for s in ax.spines.values(): s.set_visible(False)
save(fig, "e18_fig4_modal_matrix")
