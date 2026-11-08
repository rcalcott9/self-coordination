"""
Own-copy coordination is not stable across model versions.

WHAT MAKES THIS A CLEAN VERSION COMPARISON. Both runs use the same 15 stimuli, the
same n=60, the same AB/BA counterbalancing, the same identity coding, and the SAME
PROMPT - psc_common asserts the step-1 prompt hash is 3003ae1b, which is the hash of
the prompt that produced the confirmed battery. The only thing that differs between
the two measurements is the model version:

    old   gpt-5.4          claude-opus-4-8     (2026-08-07, step1c_output)
    new   gpt-5.5          claude-opus-5       (2026-08-12, this experiment)

So a change here cannot be attributed to prompt drift or a different stimulus set.

WHAT IS PLOTTED. One row per model x stimulus cell, arrow from the old version's
own-copy match probability to the new version's. Filled arrowhead = new. Cells are
ordered by |change|, largest first, so instability reads top-down. The band at 0.5 is
chance: a cell inside it has no reproducible own-copy convention at all.

THE RULE-FLIP MARKER. A cell is marked if its form-consistency classification crosses
the 0.80 "clean rule" bar between versions - i.e. the model went from having a form
rule to not having one, or vice versa. This is the classification the whole matched-
pair design is built on, which is why its instability matters.

CAUTION ON READING SINGLE ARROWS. Each endpoint is one n=60 estimate with real
sampling error; short arrows are not evidence of change. The stdout table flags which
cells have DISJOINT bootstrap CIs, and the figure's claim rests on the aggregate
(correlation across cells, count of flips), not on any individual arrow.

Run:  python3 version_stability_figure.py
"""
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
VIZ = os.path.join(EXP, "visualizations")
OLD_CSV = os.path.expanduser("~/Desktop/Coordination/LLM_Coordination/Name_game_experiment/"
                             "step1c_output/targeted_confirmation_summary.csv")
NEW_CSV = os.path.join(EXP, "data", "fresh_self_match.csv")

FC_CLEAN = 0.80
VER = {"gpt": ("GPT-5.4", "GPT-5.5"), "claude": ("Claude Opus 4.8", "Claude Opus 5")}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 7.5, "legend.fontsize": 8,
    "axes.linewidth": 0.8, "axes.edgecolor": "black", "text.color": "black",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out",
    "axes.grid": False, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
})


def load():
    old = {(r["model"], r["stimulus_pair"]): r for r in csv.DictReader(open(OLD_CSV))}
    rows = []
    for x in csv.DictReader(open(NEW_CSV)):
        o = old.get((x["model"], x["stimulus"]))
        if o is None:
            raise SystemExit(f"no confirmed row for {x['model']}/{x['stimulus']}")
        om, nm = float(o["match_unbiased"]), float(x["self_match_unbiased"])
        ocl, och = float(o["ci_lo"]), float(o["ci_hi"])
        ncl, nch = float(x["self_match_ci_lo"]), float(x["self_match_ci_hi"])
        ofc, nfc = float(o["form_consistency"]), float(x["form_consistency"])
        rows.append(dict(
            model=x["model"], stim=x["stimulus"], old=om, new=nm,
            d=nm - om, flip=(ofc >= FC_CLEAN) != (nfc >= FC_CLEAN),
            disjoint=(och < ncl or nch < ocl), ofc=ofc, nfc=nfc))
    return rows


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sa = sum((x - ma) ** 2 for x in a) ** 0.5
    sb = sum((y - mb) ** 2 for y in b) ** 0.5
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def panel(ax, rs, model, show_ylab):
    rs = sorted(rs, key=lambda r: -abs(r["d"]))
    ax.axvspan(0.45, 0.55, color="0.92", zorder=0)          # chance band
    for i, r in enumerate(rs):
        y = len(rs) - 1 - i
        ax.annotate("", xy=(r["new"], y), xytext=(r["old"], y),
                    arrowprops=dict(arrowstyle="-|>", color="0.25", linewidth=1.0,
                                    shrinkA=0, shrinkB=0, mutation_scale=8), zorder=2)
        ax.plot([r["old"]], [y], marker="o", markerfacecolor="white",
                markeredgecolor="black", markersize=4.5, markeredgewidth=0.9,
                linestyle="none", zorder=3)
    ax.set_yticks(range(len(rs)))
    ax.set_yticklabels([r["stim"] + ("  *" if r["flip"] else "   ")
                        for r in reversed(rs)])
    for t, r in zip(ax.get_yticklabels(), reversed(rs)):
        if r["flip"]:
            t.set_fontweight("bold")
    ax.set_xlim(0.35, 1.05)
    ax.set_xticks([0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_ylim(-0.8, len(rs) - 0.2)
    ax.set_xlabel("own-copy match probability")
    a, b = VER[model]
    nf = sum(r["flip"] for r in rs)
    ax.set_title(f"{a}  →  {b}\n{nf} of {len(rs)} stimuli change rule status",
                 fontsize=9, pad=8)
    if not show_ylab:
        ax.tick_params(axis="y", length=0)


def main():
    rows = load()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.6))
    for ax, m in zip(axes, ("gpt", "claude")):
        panel(ax, [r for r in rows if r["model"] == m], m, True)

    handles = [Line2D([], [], marker="o", markerfacecolor="white", markeredgecolor="black",
                      markersize=4.5, markeredgewidth=0.9, linestyle="none",
                      label="older version"),
               Line2D([], [], marker=">", color="0.25", markersize=5, linestyle="-",
                      linewidth=1.0, label="newer version (arrowhead)"),
               Line2D([], [], marker="$*$", color="black", markersize=6,
                      linestyle="none", label="form-rule status flips (bold)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.075),
               fontsize=8)

    r_all = pearson([r["old"] for r in rows], [r["new"] for r in rows])
    nf = sum(r["flip"] for r in rows)
    nd = sum(r["disjoint"] for r in rows)
    fig.tight_layout()                       # before the titles, so they are not moved
    fig.suptitle("Own-copy coordination does not carry across model versions",
                 fontsize=11.5, y=1.105)
    fig.text(0.5, 1.045, f"Same prompt, same 15 stimuli, same n = 60 - only the model "
             f"version differs.  Old-vs-new correlation r = {r_all:+.2f} across "
             f"{len(rows)} cells.", ha="center", fontsize=8.5)

    os.makedirs(VIZ, exist_ok=True)
    for e in ("png", "pdf"):
        fig.savefig(os.path.join(VIZ, f"figure_version_stability.{e}"), facecolor="white")
    plt.close(fig)

    print("-> figure_version_stability.png / .pdf\n")
    print(f"{'model':7} {'stimulus':16} {'old':>6} {'new':>7} {'delta':>7}  flip  CIs")
    for r in sorted(rows, key=lambda z: (z["model"], -abs(z["d"]))):
        print(f"{r['model']:7} {r['stim']:16} {r['old']:6.3f} {r['new']:7.3f} "
              f"{r['d']:+7.3f}  {'YES ' if r['flip'] else '  . '} "
              f"{'disjoint' if r['disjoint'] else ''}")
    print(f"\nrule-status flips        : {nf} of {len(rows)} cells")
    st = {}
    for r in rows:
        st[r["stim"]] = st.get(r["stim"], False) or r["flip"]
    print(f"stimuli with >=1 flip    : {sum(st.values())} of {len(st)}")
    print(f"disjoint bootstrap CIs   : {nd} of {len(rows)} cells")
    print(f"old-vs-new correlation   : r = {r_all:+.3f}")
    md = sum(abs(r["d"]) for r in rows) / len(rows)
    print(f"mean |change| in match   : {md:.3f}")


if __name__ == "__main__":
    main()
