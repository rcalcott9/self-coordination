"""
Study 2 (revised) MAIN FIGURE: the compatibility dose-response.

  x  the stimulus's empirically measured same-model coordination advantage
     (own-copy reliability minus cross-model reliability), from the confirmation
     screen
  y  the same-minus-different partner effect on P(ATTEMPT)
  one point per (actor x stimulus)

The claim of Study 2 is a SLOPE, so the figure is a scatter with a fitted line, and
the two competing accounts are visually distinct at a glance:

    MODEL A  coarse identity heuristic   -> a FLAT line at some height
    MODEL B  policy-specific sensitivity -> a line with positive slope

The x = 0 and y = 0 reference lines are drawn because both zeros mean something.
x = 0 is the stimulus on which sharing a policy confers no coordination advantage at
all; y = 0 is indifference between a same-model and a different-model partner. The
quadrant a point falls in is the reading: points at negative x with negative y, and
points at positive x with positive y, are the dose-response. A cloud at constant y
across all x is MODEL A.

ACADEMIC STYLE. plt.style.use("academic") is applied ONCE at import from
~/.matplotlib/stylelib/academic.mplstyle - Arial ~9 pt (Helvetica, then DejaVu Sans,
as fallbacks), plain black text, 0.8 pt black axes, top and right spines off, ticks
outward, no gridlines, 5.5 x 3.2 in at 300 dpi, PDF and PNG both written.

GREYSCALE SURVIVAL. The style file cannot enforce it, so this script does. GPT-5.5 is
a FILLED CIRCLE on a SOLID line; Claude Opus 5 is an OPEN SQUARE on a DASHED line.
Tone is a third, redundant cue and never the only one, so the two actors stay
distinguishable in a black-and-white printout.

ERROR BARS are thin capped lines, not translucent bands - in BOTH directions. The
vertical bars are the 95 % percentile bootstrap interval on the partner effect. The
horizontal bars are the advantage's own sampling error from the confirmation screen,
and they are drawn precisely because the x-axis variable is MEASURED: they are the
visible reason the analysis carries an errors-in-variables model rather than plain
OLS on these points.

THE FITTED BAND is the one filled region on the plot, and it is a REGRESSION
interval, not an error bar in disguise: a pointwise 95 % band built from bootstrap
draws of the fitted line, drawn in light grey with thin dotted boundaries so it reads
correctly in greyscale. If the analysis wrote no draw file the band is simply omitted
rather than faked.

NO TITLE OR SUBTITLE INSIDE THE AXES. n, the slope, its interval, the permutation p
and the model-comparison verdict go in the caption, which is written to a sidecar
.txt next to the figure so it can be pasted into the manuscript rather than baked
into the image.

Run:  python3 figure_dose_response.py --tag dose_b
      python3 figure_dose_response.py --tag dose_b --out ../figures/dose_response_dose_b
"""
import argparse, csv, glob, os, sys
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import study2_schema as S

# Set once, not per call.
try:
    plt.style.use("academic")
except OSError:
    sys.exit("matplotlib style 'academic' not found.\n"
             "  Expected at ~/.matplotlib/stylelib/academic.mplstyle")

# Marker + linetype + tone. Every cue is redundant, so the figure survives greyscale.
SERIES = {
    "gpt":    dict(label="GPT-5.5", marker="o", mfc="black", mec="black",
                   color="black", linestyle="-"),
    "claude": dict(label="Claude Opus 5", marker="s", mfc="white", mec="black",
                   color="0.40", linestyle="--"),
}
ORDER = ("gpt", "claude")


def newest(pattern, d):
    f = glob.glob(os.path.join(d, pattern))
    return max(f, key=os.path.getmtime) if f else None


def fnum(x, default=float("nan")):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stimuli", default=None, help="dose_stimulus_effects*.csv")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--sample", default=None,
                    help="which sample to plot; default = the run's primary")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    adir = os.path.join(EXP, "analysis")
    path = args.stimuli or newest(
        f"dose_stimulus_effects_{args.tag}.csv" if args.tag
        else "dose_stimulus_effects*.csv", adir)
    if not path or not os.path.exists(path):
        sys.exit(f"no per-stimulus table found in {adir} "
                 "(run analyze_dose_response.py first)")
    tag = args.tag or os.path.basename(path)[len("dose_stimulus_effects"):-4].lstrip("_")
    out = args.out or os.path.join(EXP, "figures",
                                   "dose_response" + (f"_{tag}" if tag else ""))

    rows = list(csv.DictReader(open(path)))
    samp = args.sample or next((r["sample"] for r in rows
                                if str(r["primary_sample"]).lower() == "true"),
                               rows[0]["sample"])
    rows = [r for r in rows if r["sample"] == samp]
    if not rows:
        sys.exit(f"{path}: no rows for sample {samp}")

    fig, ax = plt.subplots(figsize=(5.5, 3.2))

    xall = [fnum(r["advantage"]) for r in rows]
    lo_x, hi_x = min(xall), max(xall)
    pad = 0.08 * (hi_x - lo_x if hi_x > lo_x else 1.0)
    grid = np.linspace(lo_x - pad, hi_x + pad, 120)

    # ---- fitted line + pointwise band, from the analysis's own bootstrap draws ---
    dpath = os.path.join(adir, os.path.basename(path).replace(
        "dose_stimulus_effects", "dose_fit_draws"))
    draws = list(csv.DictReader(open(dpath))) if os.path.exists(dpath) else []
    slope_txt = ""
    if draws:
        g1 = np.array([fnum(d["g1"]) for d in draws])
        g0s = {a: np.array([fnum(d[f"g0[{a}]"]) for d in draws])
               for a in ORDER if f"g0[{a}]" in draws[0]}
        if g0s:
            # ONE band, not one per actor. The slope is shared by construction and the
            # actor-specific intercepts differ by far less than the band is wide, so
            # two overlaid bands would be two drawings of the same uncertainty. The
            # band is built from the mean intercept; the two fitted LINES are drawn
            # separately so the actor-specific intercepts are still visible.
            gm = np.mean(np.column_stack(list(g0s.values())), axis=1)
            lines = gm[:, None] + g1[:, None] * grid[None, :]
            lo = np.percentile(lines, 2.5, axis=0)
            hi = np.percentile(lines, 97.5, axis=0)
            ax.fill_between(grid, lo, hi, facecolor="0.90", edgecolor="none", zorder=0)
            ax.plot(grid, lo, color="0.55", linewidth=0.5, linestyle=":", zorder=0)
            ax.plot(grid, hi, color="0.55", linewidth=0.5, linestyle=":", zorder=0)
            for a, g0 in g0s.items():
                st = SERIES[a]
                ax.plot(grid, np.median(g0) + np.median(g1) * grid, color=st["color"],
                        linestyle=st["linestyle"], linewidth=0.8, zorder=2)
        slope_txt = (f"fitted slope {np.median(g1):+.3f} "
                     f"[{np.percentile(g1, 2.5):+.3f}, {np.percentile(g1, 97.5):+.3f}]")

    # ---- reference lines: both zeros mean something -----------------------------
    ax.axhline(0.0, color="black", linewidth=0.5, linestyle="-", zorder=1)
    ax.axvline(0.0, color="black", linewidth=0.5, linestyle="-", zorder=1)

    # ---- the points, with thin capped error bars in BOTH directions -------------
    for a in ORDER:
        sub = [r for r in rows if r["actor"] == a]
        if not sub:
            continue
        x = np.array([fnum(r["advantage"]) for r in sub])
        y = np.array([fnum(r["partner_effect"]) for r in sub])
        ylo = y - np.array([fnum(r["ci_lo"]) for r in sub])
        yhi = np.array([fnum(r["ci_hi"]) for r in sub]) - y
        xe = np.array([fnum(r.get("advantage_se", ""), 0.0) for r in sub])
        xe = np.nan_to_num(xe) * 1.96
        st = dict(SERIES[a])
        lab = st.pop("label")
        st.pop("linestyle")
        ax.errorbar(x, y, yerr=[ylo, yhi], xerr=xe, fmt=st["marker"],
                    mfc=st["mfc"], mec=st["mec"], color=st["color"],
                    ecolor=st["color"], capsize=2.5, elinewidth=0.8, capthick=0.8,
                    markersize=4.5, markeredgewidth=0.8, linestyle="none",
                    label=lab, zorder=3)

    # Axis labels stay short enough to fit a journal column at 9 pt; the full
    # definitions of both quantities live in the caption, not inside the axes.
    ax.set_xlabel("Same-model coordination advantage")
    ax.set_ylabel("Partner effect on P(ATTEMPT)")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_xlim(grid[0], grid[-1])

    # Legend inside the axes only if a corner is genuinely empty; otherwise below.
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.08, 1, 1))

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fig.savefig(out + ".png", dpi=300)
    fig.savefig(out + ".pdf")            # vector text, pdf.fonttype 42 from the style
    print(f"  -> {out}.png")
    print(f"  -> {out}.pdf")

    # ---- caption sidecar: everything that must NOT sit inside the axes ----------
    spath = os.path.join(adir, os.path.basename(path).replace(
        "dose_stimulus_effects", "dose_slopes"))
    bits = []
    if os.path.exists(spath):
        for r in csv.DictReader(open(spath)):
            if (r["sample"] == samp and r["scope"].startswith("POOLED")
                    and r["stimulus_set"] == "all stimuli"):
                bits.append(
                    f"Pooled Partner x Advantage slope {fnum(r['g1_plugin']):+.3f} "
                    f"[{fnum(r['g1_plugin_ci_lo']):+.3f}, "
                    f"{fnum(r['g1_plugin_ci_hi']):+.3f}], one-sided permutation "
                    f"p = {fnum(r['g1_perm_p_one']):.4f}; leave-one-stimulus-out "
                    f"model comparison favours {r['loso_verdict']} "
                    f"(verdict: {r['verdict']}).")
            if (r["sample"] == samp and r["scope"].startswith("POOLED")
                    and r["stimulus_set"] != "all stimuli"):
                bits.append(
                    f"Excluding a_chev_ud the slope is {fnum(r['g1_plugin']):+.3f} "
                    f"[{fnum(r['g1_plugin_ci_lo']):+.3f}, "
                    f"{fnum(r['g1_plugin_ci_hi']):+.3f}], "
                    f"p = {fnum(r['g1_perm_p_one']):.4f}.")
    ns = defaultdict(int)
    for r in rows:
        ns[r["actor"]] += int(r["n_same"]) + int(r["n_diff"])
    cap = (
        "Same-minus-different partner effect on P(ATTEMPT) against each stimulus's "
        "measured same-model coordination advantage (own-copy reliability minus "
        "cross-model reliability, the latter derived from the two models' independent "
        "binary-choice marginals). One point per actor x stimulus, "
        + ", ".join(f"{S.DISPLAY.get(a, a)} n = {ns[a]} trials" for a in ORDER if ns[a])
        + f"; {samp} sample. Vertical bars are 95% percentile bootstrap intervals "
        "resampling trials within cell; horizontal bars are 1.96 x the advantage's "
        "own sampling error from the confirmation screen, which is why the primary "
        "analysis fits an errors-in-variables model rather than regressing on these "
        "points directly. Lines are the fitted trial-level model (shared slope, "
        "actor-specific intercept) with a pointwise 95% bootstrap band. "
        + (slope_txt + ". " if slope_txt else "")
        + "A flat line is the coarse identity heuristic; a positive slope is "
        "policy-specific sensitivity. " + " ".join(bits))
    with open(out + "_caption.txt", "w") as fh:
        fh.write(cap + "\n")
    print(f"  -> {out}_caption.txt")


if __name__ == "__main__":
    main()
