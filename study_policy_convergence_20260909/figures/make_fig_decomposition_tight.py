"""Determinism figure, tightened layout. Visual arm and code arm from one code path.

    python3 make_fig_decomposition_tight.py            # visual (default)
    python3 make_fig_decomposition_tight.py --code     # code conventions

Same data and same appearance as policy_convergence_fixed-3.png (frozen stage1_frame,
41 items, 9 models, 36 pairs) - only the layout changes. Panel C no longer sits marooned
in the bottom half: the three panels now share the canvas evenly, C spanning the full
width at a height matched to its single axis of information.

As in make_fig_decomposition.py, every plotted quantity is recomputed from the frozen
pair_metrics.csv and asserted against the pipeline's own convergence.json before drawing.
No number is typed in from a report.
"""
import argparse, csv, json, os, collections
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
_ap = argparse.ArgumentParser()
_ap.add_argument("--code", action="store_true")
ARGS = _ap.parse_args()

# Per-arm settings. The VISUAL entry reproduces the approved figure byte-for-byte; only a
# new branch is added, nothing about the visual arm is re-tuned.
CFG = {
 False: dict(
   out="stage1_frame", name="fig_determinism_tight",
   title="Rising model agreement is explained by increasing determinism",
   ylim=(-1.10, -.02), xlim=(-.35, 1.55), cxlim=(-.055, .172),
   expect=(.1993, .1974, .0019),
   das_expect=((.0875, .0334, .1453), (.0365, -.0302, .1022)), npairs=36, nitems=41),
 True: dict(
   out="code_pilot", name="fig_determinism_code",
   title="Agreement on code conventions rises only partly through determinism",
   ylim=(-.60, -.00), xlim=(-.35, 1.55), cxlim=(-.075, .155),
   expect=(.1157, .0732, .0425),
   das_expect=None, npairs=36, nitems=12),
}[bool(ARGS.code)]
SRC = os.path.join(HERE, "..", "analysis", "out", CFG["out"])
OUT = os.path.join(SRC, CFG["name"])

plt.style.use("academic")
# The reference PNG reads at a larger type scale than the 9 pt journal-column default.
# Layout is what was asked to change, so the type scale is held where it was.
plt.rcParams.update({"font.size": 11, "axes.labelsize": 11, "xtick.labelsize": 11,
                     "ytick.labelsize": 11, "legend.fontsize": 11,
                     "axes.linewidth": 1.1, "xtick.major.width": 1.1,
                     "ytick.major.width": 1.1, "xtick.major.size": 4.5,
                     "ytick.major.size": 4.5})

rows = list(csv.DictReader(open(os.path.join(SRC, "pair_metrics.csv"))))
conv = json.load(open(os.path.join(SRC, "convergence.json")))
F = lambda r, k: float(r[k])


def ols(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    return np.polyfit(x[m], y[m], 1)


# ---------------------------------------------------------------- recompute ----
v = [F(r, "vintage") for r in rows]
tot_m, tot_b = ols(v, [F(r, "log_cross_match") for r in rows])
det_m, det_b = ols(v, [F(r, "determinism_channel") for r in rows])
ali_m, ali_b = ols(v, [F(r, "alignment_channel") for r in rows])

d = conv["decomposition_of_raw_trend"]
assert abs(tot_m - d["log_cross_match_slope"]) < 1e-9
assert abs(det_m - d["determinism_channel_slope"]) < 1e-9
assert abs(ali_m - d["alignment_channel_slope"]) < 1e-9
resid = (det_m + ali_m) - tot_m
assert abs(resid) < 1e-6
e = CFG["expect"]
assert abs(tot_m - e[0]) < 5e-5 and abs(det_m - e[1]) < 5e-5 and abs(ali_m - e[2]) < 5e-5, \
    (tot_m, det_m, ali_m)
share = det_m / tot_m
assert abs(share - d["share_from_determinism"]) < 1e-9

g = collections.OrderedDict()
for r in rows:
    g.setdefault((r["model_a"], r["model_b"]), []).append(r)
assert len(g) == CFG["npairs"] and {len(x) for x in g.values()} == {CFG["nitems"]}
pv = np.array([F(x[0], "vintage") for x in g.values()])
ptype = [x[0]["pair_type"] for x in g.values()]
P = {k: np.array([np.nanmean([F(r, k) for r in x]) for x in g.values()])
     for k in ("log_cross_match", "determinism_channel", "alignment_channel")}
for k, m in (("log_cross_match", tot_m), ("determinism_channel", det_m),
             ("alignment_channel", ali_m)):
    assert abs(ols(pv, P[k])[0] - m) < 1e-9, k

das = conv["by_pair_type"]["das"]
W, X = das["within_family"], das["cross_family"]
if CFG["das_expect"]:
    for grp, want in zip((W, X), CFG["das_expect"]):
        for got, w in zip((grp["slope"], grp["lo"], grp["hi"]), want):
            assert abs(got - w) < 5e-5, (got, w)
print(f"assertions pass - total {tot_m:+.4f} = determinism {det_m:+.4f} + "
      f"alignment {ali_m:+.4f} ({100*share:.1f}% determinism)")

# ------------------------------------------------------------------- figure ----
# Tightened: A and B keep the top row, C spans the full width beneath them at a height
# proportional to its content (two rows of estimates), with the row gap cut to what the
# x-label of the top row actually needs.
fig = plt.figure(figsize=(9.8, 6.0))
# Margins are deliberately generous: the figure is read at column width in a draft, and
# the panel letters and axis labels need air around them. top leaves room for the main
# title, which sits above the panels rather than inside any axes.
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.42], hspace=.58, wspace=.30,
                      left=.105, right=.955, top=.845, bottom=.135)
axL, axR = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
axB = fig.add_subplot(gs[1, :])

XL, YL = CFG["xlim"], CFG["ylim"]
gx = np.linspace(XL[0], XL[1], 40)
wf = np.array([p == "within_family" for p in ptype])

# --- A: raw agreement ---------------------------------------------------------
axL.scatter(pv[wf], P["log_cross_match"][wf], s=42, marker="o", facecolors="none",
            edgecolors="k", linewidths=1.1, zorder=3, label="Within-family pairs")
axL.scatter(pv[~wf], P["log_cross_match"][~wf], s=42, marker="s", facecolors="k",
            edgecolors="k", linewidths=1.1, zorder=3, label="Cross-family pairs")
axL.plot(gx, tot_m * gx + tot_b, "-", color="k", lw=1.6, zorder=2)
axL.set_ylabel("Log expected pairwise agreement")
axL.set_xlim(*XL); axL.set_ylim(*YL)
axL.legend(frameon=False, loc="upper left", handletextpad=.5, borderpad=.1,
           labelspacing=.35, borderaxespad=.2)
axL.set_title("A  Pairwise agreement across model generations", pad=10)

# --- B: split into channels ---------------------------------------------------
axR.plot(gx, det_m * gx + det_b, "-", color="k", lw=1.6, zorder=2)
axR.scatter(pv, P["determinism_channel"], s=40, marker="^", facecolors="k",
            edgecolors="k", linewidths=.9, zorder=3, label="Determinism")
axR.plot(gx, ali_m * gx + ali_b, "--", color="k", lw=1.6, dashes=(5, 3), zorder=2)
axR.scatter(pv, P["alignment_channel"], s=44, marker="D", facecolors="white",
            edgecolors="k", linewidths=.9, zorder=3, label="Alignment")
axR.set_xlim(*XL); axR.set_ylim(*YL)
axR.set_ylabel("Contribution to log expected agreement")
h, l = axR.get_legend_handles_labels()
axR.legend(h, l, frameon=False, loc="lower right", handletextpad=.5, borderpad=.1,
           labelspacing=.35, borderaxespad=.4)
axR.set_title("B  Decomposition of pairwise agreement", pad=10)

for ax in (axL, axR):
    ax.set_xlabel("Checkpoint vintage (years since Jan. 2025)")

# --- C: determinism-adjusted slope by family ----------------------------------
axB.axvline(0, color="k", lw=1.2, ls=(0, (5, 4)), zorder=1)
for y, grp, filled in ((1, W, True), (0, X, False)):
    s, lo, hi = grp["slope"], grp["lo"], grp["hi"]
    axB.plot([lo, hi], [y, y], "-", color="k", lw=1.4, zorder=2)
    for e in (lo, hi):
        axB.plot([e, e], [y - .16, y + .16], "-", color="k", lw=1.4, zorder=2)
    axB.plot(s, y, "o" if filled else "s", ms=9, color="k",
             markerfacecolor="k" if filled else "white", markeredgewidth=1.4, zorder=3)
axB.set_yticks([1, 0])
axB.set_yticklabels(["Within-family", "Cross-family"])
axB.set_ylim(-.55, 1.55); axB.set_xlim(*CFG["cxlim"])
axB.tick_params(axis="y", length=0)
axB.set_xlabel("Change in determinism-adjusted similarity per year")
axB.set_title("C  Determinism-adjusted similarity", pad=10)

for ax in (axL, axR, axB):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)

fig.suptitle(CFG["title"],
             fontsize=13, y=.955, x=.105, ha="left")

for ext, kw in ((".pdf", {}), (".png", dict(dpi=300))):
    fig.savefig(OUT + ext, facecolor="white", **kw)
print("wrote", os.path.normpath(OUT + ".pdf"), "/ .png")
