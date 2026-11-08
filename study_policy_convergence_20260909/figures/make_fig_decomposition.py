"""
STAGE1_REPORT figure: the raw agreement trend is determinism, not alignment.

Plots ONLY from the frozen merged dataset (analysis/out/stage1_frame/), never from
numbers typed into the report. Every plotted quantity is recomputed here and asserted
against the pipeline's own output before anything is drawn.

Two choices worth stating, both forced by the data rather than by taste:

  * Both top panels are in LOG expected-agreement units. The decomposition
    log M_AB = .5 log M_AA + .5 log M_BB + log cos_raw is additive only on the log
    scale, so +0.1993 is the slope of LOG agreement. On a raw match-rate axis the
    fitted slope is +0.1215 and the channels do not sum to it.
  * The right panel is two lines on the vintage axis, not a stacked bar. The alignment
    channel is 1% of the total, which on a stacked bar is a hairline the reader cannot
    see. Two lines make "one climbs, one is flat" legible at a glance, which is the
    point of the figure.

Points are the 36 model pairs (each the mean over all 41 items); the fitted lines are
OLS on all 1,476 pair x item rows. The design is balanced at 41 items per pair, so those
two slopes are identical to ~1e-15 - asserted below, not assumed.
"""
import csv, json, os, collections
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "analysis", "out", "stage1_frame")
plt.style.use("academic")

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
# The identity is exact in algebra but not in float: the pipeline itself reports a
# residual of 2.4e-08, so assert against THAT, not against 0. Tightening this to 1e-9
# fails, which is how the residual was found rather than assumed.
resid = (det_m + ali_m) - tot_m
assert abs(resid) < 1e-6 and abs(abs(resid) - abs(d["residual"])) < 1e-12
assert abs(tot_m - .1993) < 5e-5 and abs(det_m - .1974) < 5e-5 and abs(ali_m - .0019) < 5e-5, \
    "recomputed slopes disagree with STAGE1_REPORT"
share = det_m / tot_m
assert abs(share - d["share_from_determinism"]) < 1e-9 and share > .98

# pair-level aggregation must not move any slope (balanced design)
g = collections.OrderedDict()
for r in rows:
    g.setdefault((r["model_a"], r["model_b"]), []).append(r)
assert len(g) == 36 and {len(x) for x in g.values()} == {41}
pv = np.array([F(x[0], "vintage") for x in g.values()])
ptype = [x[0]["pair_type"] for x in g.values()]
P = {k: np.array([np.nanmean([F(r, k) for r in x]) for x in g.values()])
     for k in ("log_cross_match", "determinism_channel", "alignment_channel")}
for k, m in (("log_cross_match", tot_m), ("determinism_channel", det_m),
             ("alignment_channel", ali_m)):
    assert abs(ols(pv, P[k])[0] - m) < 1e-9, k

das = conv["by_pair_type"]["das"]
W, X = das["within_family"], das["cross_family"]
for got, want in ((W["slope"], .0875), (W["lo"], .0334), (W["hi"], .1453),
                  (X["slope"], .0365), (X["lo"], -.0302), (X["hi"], .1022)):
    assert abs(got - want) < 5e-5, (got, want)
assert X["lo"] < 0 < X["hi"] and W["lo"] > 0
print(f"assertions pass — total {tot_m:+.4f} = determinism {det_m:+.4f} + "
      f"alignment {ali_m:+.4f} ({100*share:.1f}% determinism)")

# ------------------------------------------------------------------- figure ----
fig = plt.figure(figsize=(5.5, 5.3))
gs = fig.add_gridspec(2, 2, height_ratios=[1.5, 1.0], hspace=.75, wspace=.34)
axL, axR = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
axB = fig.add_subplot(gs[1, :])
XL, YL = (-.35, 1.55), (-1.10, -.02)
gx = np.linspace(XL[0], XL[1], 40)
wf = np.array([p == "within_family" for p in ptype])

# --- left: the misleading picture --------------------------------------------
axL.scatter(pv[wf], P["log_cross_match"][wf], s=17, marker="o", facecolors="none",
            edgecolors="k", linewidths=.8, zorder=3, label="within-family pair")
axL.scatter(pv[~wf], P["log_cross_match"][~wf], s=17, marker="s", facecolors="k",
            edgecolors="k", linewidths=.8, zorder=3, label="cross-family pair")
axL.plot(gx, tot_m * gx + tot_b, "-", color="k", lw=1.3, zorder=2)
axL.set_ylabel("log expected agreement\nbetween two models")
axL.set_xlim(*XL); axL.set_ylim(*YL)
axL.legend(frameon=False, loc="lower right", fontsize=7, handletextpad=.25,
           borderpad=.1, labelspacing=.2)
axL.text(.02, 1.16, "Agreement rises with vintage", transform=axL.transAxes, fontsize=8)
axL.text(.02, 1.045, f"slope {tot_m:+.4f}/yr", transform=axL.transAxes, fontsize=7.5)

# --- right: same axis, split into channels -----------------------------------
axR.plot(gx, det_m * gx + det_b, "-", color="k", lw=1.3, zorder=2,
         label=f"determinism  {det_m:+.4f}  ({100*share:.0f}% of the total)")
axR.scatter(pv, P["determinism_channel"], s=15, marker="^", facecolors="k",
            edgecolors="k", linewidths=.7, zorder=3)
axR.plot(gx, ali_m * gx + ali_b, "--", color="k", lw=1.3, dashes=(4, 2.6), zorder=2,
         label=f"alignment  {ali_m:+.4f}  ({100*(1-share):.0f}% of the total)")
axR.scatter(pv, P["alignment_channel"], s=17, marker="D", facecolors="white",
            edgecolors="k", linewidths=.7, zorder=3)
axR.set_xlim(*XL); axR.set_ylim(*YL)
axR.set_ylabel("log expected agreement,\nsplit into channels")
# Keyed rather than labelled in place: the diamonds occupy the upper band and any text
# there collides with them.
axR.legend(frameon=False, loc="lower center", fontsize=7, handlelength=2.2,
           handletextpad=.4, borderpad=.1, labelspacing=.3,
           bbox_to_anchor=(.53, .045))
axR.text(.02, 1.16, "Only one channel moves", transform=axR.transAxes, fontsize=8)
axR.text(.02, 1.045, "same axis and scale as left", transform=axR.transAxes,
         fontsize=7.5, style="italic")
for ax in (axL, axR):
    ax.set_xlabel("Checkpoint vintage (yr since 2025-01)")

# --- bottom: determinism-adjusted slope by family ----------------------------
axB.axvline(0, color="k", lw=.9, ls=(0, (4, 3)), zorder=1)
for y, grp, filled in ((1, W, True), (0, X, False)):
    s, lo, hi = grp["slope"], grp["lo"], grp["hi"]
    axB.plot([lo, hi], [y, y], "-", color="k", lw=1.1, zorder=2)
    for e in (lo, hi):
        axB.plot([e, e], [y - .10, y + .10], "-", color="k", lw=1.1, zorder=2)
    axB.plot(s, y, "o" if filled else "s", ms=5.5, color="k",
             markerfacecolor="k" if filled else "white", markeredgewidth=1.0, zorder=3)
    axB.text(hi + .007, y, f"{s:+.4f}  [{lo:+.4f}, {hi:+.4f}]", va="center", fontsize=7.5)
axB.set_yticks([1, 0])
axB.set_yticklabels(["within family\n(same lineage)", "cross family\n(GPT vs Claude)"],
                    fontsize=8)
axB.set_ylim(-.75, 1.75); axB.set_xlim(-.075, .30)
axB.set_xlabel("Determinism-adjusted similarity slope per year\n"
               "(95% item-clustered bootstrap CI)")
axB.text(.004, -.53, "zero", fontsize=7.5, ha="left", va="center")
axB.text(.155, -.53, "cross-family interval contains zero", fontsize=7.5, style="italic")

for ax in (axL, axR, axB):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)

for ext, kw in ((".pdf", {}), (".png", dict(dpi=300))):
    fig.savefig(os.path.join(SRC, "fig_decomposition" + ext), bbox_inches="tight", **kw)
print("wrote fig_decomposition.pdf / .png ->", os.path.normpath(SRC))
