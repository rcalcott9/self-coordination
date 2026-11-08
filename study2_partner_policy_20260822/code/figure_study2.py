"""
Study 2 result figure: the 2x2 Stimulus x Partner interaction, one panel per actor.

The whole claim of Study 2 is a difference of slopes, so the figure is the classic
interaction plot: stimulus level on x, attempt rate on y, one line per partner
condition. Non-parallel lines ARE the result; parallel lines with a vertical offset
are the secondary main-effect finding and must look different at a glance.

ACADEMIC STYLE. `plt.style.use("academic")` is applied ONCE at import, from
~/.matplotlib/stylelib/academic.mplstyle - Arial ~9pt, plain black text, 0.8pt black
axes, top/right spines off, ticks outward, no gridlines, 5.5 x 3.2 in at 300 dpi,
PDF and PNG both written. The style file cannot enforce greyscale survivability, so
this script does: SAME is a solid line with a FILLED circle, DIFFERENT is a dashed
line with an OPEN square. Tone is a third, redundant cue, never the only one.
Error bars are thin capped lines, not translucent bands.

NO TITLE OR SUBTITLE INSIDE THE AXES. Each panel carries only the actor's name as a
plain left-aligned panel label. n, the CI definition, the test and the effect size
go in the caption, which is written to a sidecar .txt next to the figure so it can
be pasted into the manuscript rather than baked into the image.

Run:  python3 figure_study2.py                      # newest cell-rate table
      python3 figure_study2.py --tag interaction    # a specific analysis run
      python3 figure_study2.py --sample holdout
"""
import argparse, csv, glob, os, sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import study2_schema as S

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)

# Set once, not per call.
try:
    plt.style.use("academic")
except OSError:
    sys.exit("matplotlib style 'academic' not found.\n"
             "  Expected at ~/.matplotlib/stylelib/academic.mplstyle")

# Marker + linetype + tone. Each cue is redundant, so the figure survives greyscale.
SERIES = {
    "same":      dict(label="Same model", linestyle="-", marker="o",
                      mfc="black", mec="black", color="black"),
    "different": dict(label="Different model", linestyle="--", marker="s",
                      mfc="white", mec="black", color="0.45"),
}
XPOS = {"low": 0.0, "high": 1.0}
DODGE = {"same": -0.035, "different": +0.035}       # so the caps do not overlap


def newest(pattern, d):
    f = glob.glob(os.path.join(d, pattern))
    return max(f, key=os.path.getmtime) if f else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", default=None, help="study2_cell_rates*.csv")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--sample", default=None,
                    help="which sample to plot; default = the run's primary")
    ap.add_argument("--out", default=os.path.join(EXP, "figures", "study2_interaction"))
    args = ap.parse_args()

    adir = os.path.join(EXP, "analysis")
    path = args.cells or newest(f"study2_cell_rates_{args.tag}.csv" if args.tag
                                else "study2_cell_rates*.csv", adir)
    if not path or not os.path.exists(path):
        sys.exit(f"no cell-rate table found in {adir} (run analyze_study2.py first)")
    rows = [r for r in csv.DictReader(open(path)) if r["scope"] == "pooled"]
    if not rows:
        sys.exit(f"{path}: no pooled rows")

    samp = args.sample or next((r["sample"] for r in rows
                                if str(r["primary_sample"]).lower() == "true"),
                               rows[0]["sample"])
    rows = [r for r in rows if r["sample"] == samp]
    actors = sorted(set(r["actor"] for r in rows))
    cell = {(r["actor"], r["stimulus_level"], r["partner"]): r for r in rows}

    fig, axes = plt.subplots(1, len(actors), figsize=(5.5, 3.2), sharey=True)
    if len(actors) == 1:
        axes = [axes]

    for ax, actor in zip(axes, actors):
        for w in ("same", "different"):
            xs, ys, lo, hi = [], [], [], []
            for lvl in ("low", "high"):
                r = cell.get((actor, lvl, w))
                if not r or r["attempt_rate"] == "":
                    continue
                y = float(r["attempt_rate"])
                xs.append(XPOS[lvl] + DODGE[w])
                ys.append(y)
                lo.append(y - float(r["ci_lo"]))
                hi.append(float(r["ci_hi"]) - y)
            if not xs:
                continue
            st = dict(SERIES[w])
            lab = st.pop("label")
            ax.errorbar(xs, ys, yerr=[lo, hi], capsize=2.5, elinewidth=0.8,
                        capthick=0.8, linewidth=0.8, markersize=4.5,
                        markeredgewidth=0.8, label=lab, **st)
        ax.set_xlim(-0.35, 1.35)
        ax.set_xticks([0.0, 1.0])
        ax.set_xticklabels(["Low", "High"])
        ax.set_xlabel("Own-copy match of stimulus")
        # Panel identity only. No descriptive text inside the axes.
        ax.set_title(S.DISPLAY.get(actor, actor), loc="left")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("P(ATTEMPT)")
    # Figure-level legend BELOW the panels rather than inside one of them. An in-axes
    # legend has no reliably empty corner here: in the interaction case both series
    # rise toward High and the lower right is occupied by the DIFFERENT series' error
    # bar; in the main-effect case the lower left is. Putting it outside means the
    # placement is correct for every result the figure might have to show, and it
    # keeps the axes free of anything but data.
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.09, 1, 1))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    png, pdf = args.out + ".png", args.out + ".pdf"
    fig.savefig(png, dpi=300)
    fig.savefig(pdf)                      # vector text, pdf.fonttype 42 from the style
    print(f"  -> {png}")
    print(f"  -> {pdf}")

    # ---- caption sidecar: everything that must NOT sit inside the axes -------
    ctab = os.path.join(adir, os.path.basename(path).replace("cell_rates", "contrasts"))
    bits = []
    if os.path.exists(ctab):
        for r in csv.DictReader(open(ctab)):
            if r["scope"] == "pooled" and r["sample"] == samp:
                bits.append(
                    f"{r['actor_name']}: gap(same) {float(r['gap_same']):+.3f}, "
                    f"gap(different) {float(r['gap_diff']):+.3f}, "
                    f"interaction {float(r['interaction']):+.3f} "
                    f"[{float(r['interaction_ci_lo']):+.3f}, "
                    f"{float(r['interaction_ci_hi']):+.3f}], "
                    f"one-sided permutation p = {float(r['interaction_perm_p_one']):.4f}")
    ns = defaultdict(int)
    for r in rows:
        ns[r["actor"]] += int(r["n"])
    cap = (
        "Attempt rate by stimulus own-copy match (Low, High) and partner condition "
        "(same model, different model), pooled over matched pairs and safe payoff "
        f"levels; {samp} sample "
        + ", ".join(f"n = {ns[a]} trials for {S.DISPLAY.get(a, a)}" for a in actors)
        + ". Points are raw attempt proportions computed from trial counts; error "
        "bars are 95% percentile bootstrap intervals resampling trials within cell. "
        "The primary test is the interaction (gap under same minus gap under "
        "different), tested by permuting the partner label within each "
        "pair x stimulus x payoff stratum. "
        + " ".join(bits))
    cpath = args.out + "_caption.txt"
    with open(cpath, "w") as fh:
        fh.write(cap + "\n")
    print(f"  -> {cpath}")


if __name__ == "__main__":
    main()
