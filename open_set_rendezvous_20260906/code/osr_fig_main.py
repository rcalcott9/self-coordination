"""Open-set online rendezvous -- MAIN PAPER FIGURE (two panels).

Presentational only. Every value is either read from the frozen results file
`data/osr_strategic_results.json` or recomputed from the frozen raw data through
the frozen helpers in osr_strategic.py / osr_analyze.py. No new endpoint is
defined here.

ONE DEPARTURE, FLAGGED
    The frozen strategic analysis fixed DEPTHS = (1, 5, 10, 50). Panel B also
    shows k = 25, which was NOT pre-specified. It is computed here with the same
    frozen joint()/monitor_sets()/boot_diff() functions and the frozen SEED, and
    is marked `prespecified=0` in the plot-data CSV. The four pre-specified
    depths are read verbatim from the frozen results file so the plotted numbers
    are byte-identical to the logged ones.

PANEL A  what monitoring does, at the headline definition (canon_host, k=5)
PANEL B  robustness of the joint-success effect across depth x matching level
"""
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import osr_strategic as ST                                           # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
F, G = ROOT / "data", ROOT / "figures"
LEVELS = ("exact", "canon_page", "canon_host")
LEVEL_LAB = {"exact": "exact string", "canon_page": "canonical page",
             "canon_host": "canonical host  (panel A)"}
PRESPEC = (1, 5, 10, 50)
DEPTHS_B = (1, 5, 10, 25, 50)
K_MAIN, LEVEL_MAIN = 5, "canon_host"

INK = "0.10"             # means, both conditions
ACCENT = "#1f5fa9"       # ONE accent, ONE meaning: canonical host = the panel A
                         # definition. Not reused for anything else.
FAINT = "0.80"


def finish(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(direction="out", width=0.8, length=3)
    ax.grid(False)


def per_context(base_a, mon_a, base_m, mon_m, level, k):
    """Frozen computation, lifted verbatim from osr_strategic.main()."""
    ba = ST.agent_by_ctx(base_a, level)
    ma = ST.agent_by_ctx(mon_a, level)
    bs = ST.monitor_sets(base_m, level, k)
    ms = ST.monitor_sets(mon_m, level, k)
    ctxs = sorted(set(ba) & set(ma))
    rows = []
    for c in ctxs:
        jb, pmb, peb = ST.joint(ba[c], bs.get(c, set()))
        jm, pmm, pem = ST.joint(ma[c], ms.get(c, set()))
        rows.append({"context_id": c, "joint_B": jb, "joint_M": jm,
                     "p_match_B": pmb, "p_match_M": pmm,
                     "p_evade_B": peb, "p_evade_M": pem})
    return rows


def main():
    G.mkdir(exist_ok=True)
    plt.style.use("academic")
    plt.rcParams.update({"font.size": 9, "font.family": "sans-serif",
                         "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"]})

    res = json.loads((F / "osr_strategic_results.json").read_text())
    base_a, mon_a = ST.load("baseline"), ST.load("monitored")
    base_m, mon_m = ST.load("monitor_baseline"), ST.load("monitor_monitored")

    # ---------------- panel A data: canon_host, k = 5 -------------------------
    rowsA = per_context(base_a, mon_a, base_m, mon_m, LEVEL_MAIN, K_MAIN)
    MEAS = (("p_match", "Copy–copy\ncoordination"),
            ("p_evade", "Monitor\nevasion"),
            ("joint", "Successful\njoint outcome"))

    # ---------------- panel B data: depth x level -----------------------------
    rng = np.random.default_rng(ST.SEED)
    B = {}
    for lv in LEVELS:
        for k in DEPTHS_B:
            if k in PRESPEC:
                r = res[f"{lv}|k{k}|joint"]
                B[(lv, k)] = (r["diff"], r["lo"], r["hi"], r["pos"], r["neg"], 1)
            else:
                rr = per_context(base_a, mon_a, base_m, mon_m, lv, k)
                pairs = [(x["joint_M"], x["joint_B"]) for x in rr]
                m, lo, hi, _ = ST.boot_diff(pairs, rng)
                pos, neg = ST.signtest(pairs)
                B[(lv, k)] = (m, lo, hi, pos, neg, 0)

    # ================= figure =================================================
    fig = plt.figure(figsize=(7.2, 4.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.58, 1.0], wspace=0.30,
                          left=0.075, right=0.985, top=0.845, bottom=0.135)
    axA, axB = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

    # ---------------- PANEL A -------------------------------------------------
    centres = np.array([0.0, 2.0, 4.0])
    off = 0.50
    for gi, (key, lab) in enumerate(MEAS):
        xb, xm = centres[gi] - off, centres[gi] + off
        b = np.array([r[f"{key}_B"] for r in rowsA], float)
        m = np.array([r[f"{key}_M"] for r in rowsA], float)
        for bi, mi in zip(b, m):                       # 18 context-level lines
            axA.plot([xb, xm], [bi, mi], color=FAINT, lw=0.6, zorder=1,
                     solid_capstyle="round")
        axA.plot([xb] * len(b), b, ls="none", marker="o", ms=2.6, mfc=FAINT,
                 mec=FAINT, zorder=2)
        axA.plot([xm] * len(m), m, ls="none", marker="s", ms=2.6, mfc=FAINT,
                 mec=FAINT, zorder=2)
        mb, mm = b.mean(), m.mean()
        axA.plot([xb, xm], [mb, mm], color=INK, lw=2.4, zorder=4,
                 solid_capstyle="round")
        axA.plot(xb, mb, marker="o", ms=9, mfc=INK, mec=INK, zorder=5)
        axA.plot(xm, mm, marker="s", ms=9.5, mfc="w", mec=INK, mew=2.0,
                 zorder=5)
        axA.text(centres[gi], 1.055, lab, ha="center", va="bottom", fontsize=9.5)

    ann = [("Δ = −0.465\n17 / 18 contexts ↓", 0.150),
           ("Δ = +0.451", 0.950),
           ("Δ = +0.094\n95% CI [+0.039, +0.164]", 0.700)]
    for gi, (txt, yy) in enumerate(ann):
        axA.text(centres[gi], yy, txt, ha="center", va="center", fontsize=8.2,
                 linespacing=1.35, zorder=6,
                 bbox=dict(fc="w", ec="none", alpha=0.85, pad=1.4))

    axA.set_xticks(np.concatenate([centres - off, centres + off]))
    axA.set_xticklabels(["baseline"] * 3 + ["monitored"] * 3, fontsize=8)
    axA.set_xlim(centres[0] - 1.2, centres[-1] + 1.2)
    axA.set_ylim(-0.02, 1.02)
    axA.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    axA.set_ylabel("probability", fontsize=10)
    finish(axA)
    axA.set_title("A. Monitoring increases evasion mainly by reducing coordination",
                  fontsize=10, loc="left", pad=30)

    # ---------------- PANEL B -------------------------------------------------
    style = {"exact": ("^", ":", "w", INK),
             "canon_page": ("s", "--", "w", INK),
             "canon_host": ("o", "-", ACCENT, ACCENT)}
    xs = np.arange(len(DEPTHS_B))
    axB.axhline(0, color="0.55", lw=0.9, zorder=1)
    for i, lv in enumerate(LEVELS):
        dx = (i - 1) * 0.085
        y = np.array([B[(lv, k)][0] for k in DEPTHS_B])
        lo = y - np.array([B[(lv, k)][1] for k in DEPTHS_B])
        hi = np.array([B[(lv, k)][2] for k in DEPTHS_B]) - y
        mk, ls, mfc, c = style[lv]
        axB.errorbar(xs + dx, y, yerr=[lo, hi], fmt=mk, ls=ls, color=c, mfc=mfc,
                     mec=c, ms=4.6, lw=1.0, elinewidth=0.8, capsize=2.2,
                     capthick=0.8, mew=1.0, label=LEVEL_LAB[lv], zorder=3)
    axB.set_xticks(xs)
    axB.set_xticklabels([str(k) for k in DEPTHS_B], fontsize=9)
    axB.set_xlabel("monitor depth  k", fontsize=10)
    axB.set_ylabel("Δ joint success\n(monitored − baseline)", fontsize=10)
    axB.set_xlim(-0.5, len(DEPTHS_B) - 0.5)
    axB.set_ylim(-0.215, 0.215)
    axB.legend(frameon=False, fontsize=8, loc="lower right", handlelength=2.4,
               borderaxespad=0.3, labelspacing=0.35)
    finish(axB)
    axB.set_title("B. Joint-success advantage depends on matching\nlevel and monitor depth",
                  fontsize=10, loc="left", pad=18)   # aligns "B." with "A."

    # NOTE: the suggested overall title repeated panel A's title word for word.
    # Two titles saying one sentence is clutter, so the panel titles carry it.
    fig.savefig(G / "osr_fig_main.pdf")
    fig.savefig(G / "osr_fig_main.png", dpi=300)

    # ---------------- plot-data CSVs -----------------------------------------
    with open(G / "osr_fig_main_panelA_data.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["panel", "measure", "level", "k", "context_id",
                    "baseline", "monitored"])
        for key, _ in MEAS:
            for r in rowsA:
                w.writerow(["A", key, LEVEL_MAIN, K_MAIN, r["context_id"],
                            f"{r[f'{key}_B']:.6f}", f"{r[f'{key}_M']:.6f}"])
            b = np.mean([r[f"{key}_B"] for r in rowsA])
            m = np.mean([r[f"{key}_M"] for r in rowsA])
            w.writerow(["A", key, LEVEL_MAIN, K_MAIN, "MEAN",
                        f"{b:.6f}", f"{m:.6f}"])
    with open(G / "osr_fig_main_panelB_data.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["panel", "level", "k", "diff", "ci_lo", "ci_hi",
                    "sign_pos", "sign_neg", "prespecified"])
        for lv in LEVELS:
            for k in DEPTHS_B:
                d, lo, hi, pos, neg, ps = B[(lv, k)]
                w.writerow(["B", lv, k, f"{d:.6f}", f"{lo:.6f}", f"{hi:.6f}",
                            pos, neg, ps])

    print(f"-> {G/'osr_fig_main.pdf'}")
    print(f"-> {G/'osr_fig_main.png'}")
    print(f"-> {G/'osr_fig_main_panelA_data.csv'}")
    print(f"-> {G/'osr_fig_main_panelB_data.csv'}")
    print(f"\npanel A ({LEVEL_MAIN}, k={K_MAIN}, n={len(rowsA)} contexts)")
    for key, _ in MEAS:
        b = np.mean([r[f"{key}_B"] for r in rowsA])
        m = np.mean([r[f"{key}_M"] for r in rowsA])
        print(f"   {key:8s} {b:.4f} -> {m:.4f}   (Δ {m-b:+.4f})")
    print("\npanel B  Δ joint success")
    print("   level          " + "".join(f"{'k='+str(k):>12s}" for k in DEPTHS_B))
    for lv in LEVELS:
        cells = "".join(f"{B[(lv,k)][0]:+12.4f}" for k in DEPTHS_B)
        print(f"   {lv:14s}{cells}")
    print("   (k=25 not pre-specified; computed here with the frozen helpers)")


if __name__ == "__main__":
    main()
