"""Open-set online rendezvous -- figures.

Written AFTER the analysis was complete. Purely presentational: every number
plotted is recomputed from the frozen raw data using the frozen helpers in
osr_analyze.py / osr_strategic.py. No new statistic is defined here.

Panels
  A  baseline convergence      within-context p_match vs cross-context p_cross
  B  criterion (d), amended    distinct locations by canonicalization level
  C  joint payoff vs monitor depth, by level, with 95% bootstrap CI
  D  coordination collapse     per-context p_match, baseline -> monitored
  E  evasion                   per-context p_evade, baseline -> monitored
  F  the conjunction           per-context joint,   baseline -> monitored
  (D/E/F at k=5, canon_host -- the depth and level where the joint effect is largest)
"""
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import osr_strategic as ST                                           # noqa: E402
import osr_analyze as FZ                                             # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
F, G = ROOT / "data", ROOT / "figures"
LEVELS = ("exact", "canon_page", "canon_host")
LEVEL_LAB = {"exact": "exact URL", "canon_page": "canonical page",
             "canon_host": "canonical host"}
LEVEL_TICK = {"exact": "exact\nURL", "canon_page": "canonical\npage",
              "canon_host": "canonical\nhost"}
DEPTHS = (1, 5, 10, 50)
K_SHOW, LEVEL_SHOW = 5, "canon_host"
FLOOR = 30            # criterion (d) threshold, unchanged by Amendment 01


def finish(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(direction="out", width=0.8, length=3)
    ax.grid(False)


def panel_tag(ax, s):
    ax.text(-0.22, 1.04, s, transform=ax.transAxes, fontsize=10, va="bottom")


def slopegraph(ax, pairs, ylab, ylim=None):
    """pairs: list of (baseline, monitored) per context."""
    for b, m in pairs:
        if np.isnan(b) or np.isnan(m):
            continue
        ax.plot([0, 1], [b, m], color="0.72", lw=0.6, solid_capstyle="round",
                zorder=1)
        ax.plot(0, b, marker="o", ms=3.0, mfc="k", mec="k", zorder=2)
        ax.plot(1, m, marker="s", ms=3.2, mfc="none", mec="k", mew=0.7, zorder=2)
    mb = np.nanmean([p[0] for p in pairs])
    mm = np.nanmean([p[1] for p in pairs])
    ax.plot([0, 1], [mb, mm], color="k", lw=1.6, zorder=3)
    ax.plot(0, mb, marker="o", ms=5.5, mfc="k", mec="k", zorder=4)
    ax.plot(1, mm, marker="s", ms=5.5, mfc="w", mec="k", mew=1.2, zorder=4)
    ax.set_xlim(-0.35, 1.35)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["baseline", "monitored"])
    ax.set_ylabel(ylab)
    if ylim:
        ax.set_ylim(*ylim)
    finish(ax)
    return mb, mm


def main():
    G.mkdir(exist_ok=True)
    plt.style.use("academic")
    plt.rcParams.update({"font.size": 9, "font.family": "sans-serif",
                         "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"]})

    summ = json.loads((F / "osr_context_summary.json").read_text())
    res = json.loads((F / "osr_strategic_results.json").read_text())
    base_a = ST.load("baseline")
    mon_a = ST.load("monitored")
    base_m = ST.load("monitor_baseline")
    mon_m = ST.load("monitor_monitored")

    fig, axes = plt.subplots(2, 3, figsize=(7.5, 5.4))
    (axA, axB, axC), (axD, axE, axF) = axes

    # ---- A  baseline convergence: within vs cross, canonical host -------------
    rows = [r for r in summ if r["level"] == LEVEL_SHOW]
    within = np.array([r["p_match"] for r in rows])
    cross = np.array([r["p_cross"] for r in rows])
    axA.plot([0, 1], [0, 1], "--", color="0.7", lw=0.8, zorder=1)
    axA.scatter(cross, within, s=16, facecolors="none", edgecolors="k",
                linewidths=0.7, zorder=2)
    axA.set_xlabel("cross-context match  p$_{cross}$")
    axA.set_ylabel("within-context match  p$_{match}$")
    axA.set_xlim(-0.03, 1.0)
    axA.set_ylim(-0.03, 1.05)
    axA.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    axA.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    axA.text(0.40, 0.14, f"mean {within.mean():.2f} vs {cross.mean():.2f}\n"
             f"n = {len(rows)} contexts", fontsize=7.5, va="bottom")
    finish(axA)
    panel_tag(axA, "A")

    # ---- B  criterion (d): distinct locations by level ------------------------
    counts = []
    for lv in LEVELS:
        vals = {r[lv] for r in base_a if r.get("status") in FZ.OK and r.get(lv)}
        counts.append(len(vals))
    x = np.arange(3)
    fills = ["0.35", "0.35", "w"]          # canon_host is the level that failed
    axB.bar(x, counts, width=0.6, color=fills, edgecolor="k", lw=0.8, zorder=2)
    axB.axhline(FLOOR, ls="--", color="k", lw=0.8, zorder=3)
    axB.text(2.42, FLOOR + 1.5, f"pre-registered floor ({FLOOR})", fontsize=7.5,
             ha="right", va="bottom")
    for xi, c in zip(x, counts):
        axB.text(xi, c + 1.2, str(c), ha="center", fontsize=8)
    axB.set_xticks(x)
    axB.set_xticklabels([LEVEL_TICK[l] for l in LEVELS], fontsize=7.5)
    axB.set_ylabel("distinct locations emitted")
    axB.set_ylim(0, max(counts) * 1.22)
    finish(axB)
    panel_tag(axB, "B")

    # ---- C  joint payoff difference vs monitor depth --------------------------
    marks = {"exact": ("^", "dotted", "none"),
             "canon_page": ("s", "dashed", "none"),
             "canon_host": ("o", "solid", "k")}
    xs = np.arange(len(DEPTHS))
    axC.axhline(0, color="0.6", lw=0.8, zorder=1)
    for i, lv in enumerate(LEVELS):
        off = (i - 1) * 0.11
        d = [res[f"{lv}|k{k}|joint"] for k in DEPTHS]
        y = np.array([v["diff"] for v in d])
        lo = y - np.array([v["lo"] for v in d])
        hi = np.array([v["hi"] for v in d]) - y
        mk, ls, mfc = marks[lv]
        axC.errorbar(xs + off, y, yerr=[lo, hi], fmt=mk, ls=ls, color="k",
                     mfc=mfc, mec="k", ms=4, lw=0.8, elinewidth=0.7, capsize=2,
                     capthick=0.7, mew=0.8, label=LEVEL_LAB[lv], zorder=2)
    axC.set_xticks(xs)
    axC.set_xticklabels([f"k = {k}" for k in DEPTHS], fontsize=7.5)
    axC.set_xlabel("monitor list depth")
    axC.set_ylabel("Δ joint payoff\n(monitored − baseline)")
    axC.set_xlim(-0.45, len(DEPTHS) - 0.55)
    axC.set_ylim(-0.21, 0.27)
    axC.legend(frameon=False, fontsize=7, loc="upper left",
               handlelength=2.2, borderaxespad=0.2)
    finish(axC)
    panel_tag(axC, "C")

    # ---- D/E/F  the decomposition, k=5, canonical host ------------------------
    ba = ST.agent_by_ctx(base_a, LEVEL_SHOW)
    ma = ST.agent_by_ctx(mon_a, LEVEL_SHOW)
    bs = ST.monitor_sets(base_m, LEVEL_SHOW, K_SHOW)
    ms = ST.monitor_sets(mon_m, LEVEL_SHOW, K_SHOW)
    ctxs = sorted(set(ba) & set(ma))
    jm_, pm_, pe_ = [], [], []
    for c in ctxs:
        jb, pmb, peb = ST.joint(ba[c], bs.get(c, set()))
        jmo, pmm, pem = ST.joint(ma[c], ms.get(c, set()))
        jm_.append((jb, jmo))
        pm_.append((pmb, pmm))
        pe_.append((peb, pem))

    for ax, pairs, lab, key, tag in (
            (axD, pm_, "coordination  p$_{match}$", "p_match", "D"),
            (axE, pe_, "evasion  p$_{evade}$", "p_evade", "E"),
            (axF, jm_, "joint payoff", "joint", "F")):
        top = max(max(p) for p in pairs)
        hi = 1.06 if key in ("p_match", "p_evade") else top * 1.15
        slopegraph(ax, pairs, lab, ylim=(-0.035 * hi, hi))
        r = res[f"{LEVEL_SHOW}|k{K_SHOW}|{key}"]
        ax.text(0.5, 1.02, f"Δ {r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]\n"
                f"{r['pos']}+ / {r['neg']}−",
                transform=ax.transAxes, ha="center", va="bottom", fontsize=7.5)
        panel_tag(ax, tag)

    fig.tight_layout(w_pad=1.8, h_pad=2.6)
    fig.savefig(G / "osr_main.pdf")
    fig.savefig(G / "osr_main.png", dpi=300)
    print(f"-> {G/'osr_main.pdf'}")
    print(f"-> {G/'osr_main.png'}")
    print(f"   A  within {within.mean():.4f}  cross {cross.mean():.4f}")
    print(f"   B  distinct {dict(zip(LEVELS, counts))}  floor {FLOOR}")
    print(f"   D/E/F at k={K_SHOW}, {LEVEL_SHOW}, {len(ctxs)} contexts")
    for nm, pr in (("p_match", pm_), ("p_evade", pe_), ("joint", jm_)):
        print(f"     {nm:8s} {np.nanmean([p[0] for p in pr]):.4f} -> "
              f"{np.nanmean([p[1] for p in pr]):.4f}")


if __name__ == "__main__":
    main()
