"""
Agreement decomposition by domain — same construction as the Stage 1 figure.

Points are the 36 model pairs (each the mean over that domain's items); fitted lines are
OLS on all pair x item rows. Both designs are balanced (every pair sees every item), so
the pair-mean slope equals the item-level slope exactly - asserted, not assumed.

Log scale because log M_AB = .5 log M_AA + .5 log M_BB + log cos(theta) is additive only
there.
"""
import csv, os, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("academic")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "analysis", "out")
F = lambda r, k: float(r[k])


def ols(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    return np.polyfit(x[m], y[m], 1)


def load(path, keep=None):
    rows = [r for r in csv.DictReader(open(path))
            if (keep is None or r.get("dataset") == keep)]
    g = collections.OrderedDict()
    for r in rows:
        g.setdefault((r["model_a"], r["model_b"]), []).append(r)
    n_items = {len(v) for v in g.values()}
    assert len(n_items) == 1, n_items                       # balanced design
    slopes, P = {}, {}
    for k in ("log_cross_match", "determinism_channel", "alignment_channel"):
        item_level = ols([F(r, "vintage") for r in rows], [F(r, k) for r in rows])
        P[k] = np.array([np.mean([F(r, k) for r in v]) for v in g.values()])
        pair_level = ols([F(v[0], "vintage") for v in g.values()], P[k])
        assert abs(item_level[0] - pair_level[0]) < 1e-9, (k, item_level, pair_level)
        slopes[k] = item_level
    x = np.array([F(v[0], "vintage") for v in g.values()])
    return x, P, slopes, len(g), n_items.pop(), len(rows)


CODE = load(os.path.join(OUT, "e18", "pair_metrics.csv"), "C_combined_17")
VIS = load(os.path.join(OUT, "stage1_frame", "pair_metrics.csv"))

SER = (("log_cross_match", "total agreement", "o", "k", "-", 1.5),
       ("determinism_channel", "determinism channel", "^", "k", "-", 1.2),
       ("alignment_channel", "alignment channel", "D", "white", "--", 1.2))

lo = min(min(P[k].min() for k in P) for _, P, _, _, _, _ in (CODE, VIS)) - .09
hi = max(max(P[k].max() for k in P) for _, P, _, _, _, _ in (CODE, VIS)) + .17

fig, axes = plt.subplots(1, 2, figsize=(6.9, 3.9), sharey=True)
fig.subplots_adjust(bottom=.30, wspace=.09)
for ax, D, title in ((axes[0], CODE, "Code"), (axes[1], VIS, "Visual")):
    x, P, S, npair, nitem, nrow = D
    gx = np.linspace(x.min() - .08, x.max() + .08, 40)
    for k, _lab, mk, fc, ls, lw in SER:
        ax.scatter(x, P[k], s=17, marker=mk, facecolors=fc, edgecolors="#1D2027",
                   linewidths=.7, zorder=3)
        m, b = S[k]
        ln, = ax.plot(gx, m * gx + b, ls, color="#1D2027", lw=lw, zorder=2)
        if ls == "--":
            ln.set_dashes((4, 2.4))
    tot, det, ali = (S[k][0] for k, *_ in SER)
    ax.set_title(f"{title} · {nitem} items · {npair} model pairs", fontsize=9, pad=8)
    ax.set_xlabel("Checkpoint vintage (yr since 2025-01)")
    ax.set_ylim(lo, hi); ax.set_xlim(gx.min(), gx.max())
    txt = (f"total       {tot:+.4f}\n"
           f"determinism {det:+.4f}   {100*det/tot:.0f}%\n"
           f"alignment   {ali:+.4f}   {100*ali/tot:.0f}%")
    ax.text(.035, .975, txt, transform=ax.transAxes, fontsize=7.6, va="top",
            family="monospace")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axes[0].set_ylabel("log expected agreement between two models")

h = [plt.Line2D([], [], color="#1D2027", marker=mk, ls=ls, ms=4.5, lw=lw,
                markerfacecolor=fc, markeredgecolor="#1D2027", label=lab)
     for k, lab, mk, fc, ls, lw in SER]
fig.legend(handles=h, frameon=False, ncol=3, fontsize=8, loc="lower center",
           bbox_to_anchor=(.5, .02), columnspacing=2.2, handlelength=2.6)
fig.text(.5, .145, "Points are model pairs (mean over that domain's items); "
         "lines are OLS on all pair x item rows.", ha="center", fontsize=7.5,
         style="italic")

for ext, kw in ((".pdf", {}), (".png", dict(dpi=300))):
    fig.savefig(os.path.join(OUT, "domains_decomposition" + ext),
                facecolor="white", **kw)
print("wrote domains_decomposition.pdf / .png")
for nm, D in (("code", CODE), ("visual", VIS)):
    t, d, a = (D[2][k][0] for k, *_ in SER)
    print(f"  {nm:7} {D[5]:5d} rows  total {t:+.4f} = det {d:+.4f} + ali {a:+.4f}"
          f"   ({100*d/t:.0f}% determinism)")
