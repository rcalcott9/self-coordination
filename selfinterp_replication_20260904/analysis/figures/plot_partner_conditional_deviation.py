"""Publication figure for the partner-conditional deviation pilot.

Every plotted value is recomputed from the trial-level results
(data/partner_pilot/partner_results.json) and cross-checked against the frozen
analysis output (data/partner_pilot/partner_analysis.json) before drawing.

Panel A -- own-policy adherence by partner condition (the main result)
Panel B -- own-policy adherence by focal preference-strength tertile

Wording discipline carried into the figure:
  * DIFF-INFORMED is labelled a positive control, not evidence of partner modelling.
  * SAME < UNKNOWN is presented descriptively, never as avoidance or anti-coordination.
  * partner preference is described as PREDICTED, never as observed on these items.
"""

import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
F = ROOT / "data" / "partner_pilot"
OUT_DIRS = [Path.home() / "Downloads", Path(__file__).resolve().parent]

CONDS = ["UNKNOWN", "SAME", "DIFF_UNINFORMED", "DIFF_INFORMED"]
LABELS = {"UNKNOWN": "UNKNOWN", "SAME": "SAME", "DIFF_UNINFORMED": "DIFF-\nUNINFORMED",
          "DIFF_INFORMED": "DIFF-\nINFORMED"}
TERTILES = ["low", "medium", "high"]
RNG = np.random.default_rng(20260907)
NB = 4000

# reported values, for verification only -- not plotted
REPORTED = {"UNKNOWN": (0.8639, 0.819, 0.914), "SAME": (0.8167, 0.769, 0.873),
            "DIFF_UNINFORMED": (0.7861, 0.724, 0.847),
            "DIFF_INFORMED": (0.5889, 0.500, 0.667)}


def load():
    items = {x["item"]: x for x in json.loads((F / "partner_items.json").read_text())}
    res = json.loads((F / "partner_results.json").read_text())
    ctx = {k: v["scenario"] for k, v in items.items()}
    ch = defaultdict(lambda: defaultdict(list))
    dropped = 0
    for r in res:
        if r.get("choice") in ("A", "B"):
            ch[r["cond"]][r["item"]].append(r["choice"])
        else:
            dropped += 1
    return items, ctx, ch, dropped, len(res)


def rate(ch, items, ctx, cond, contexts, subset=None):
    hit = tot = 0
    for it in (subset or items):
        if ctx[it] not in contexts:
            continue
        fav = items[it]["focal_favoured"]
        for x in ch[cond].get(it, []):
            tot += 1
            hit += (x == fav)
    return hit / tot if tot else None


def boot_ci(ch, items, ctx, cond, contexts, subset=None):
    """Cluster bootstrap on context -- the unit of independence."""
    out = []
    for _ in range(NB):
        pick = [contexts[i] for i in RNG.integers(0, len(contexts), len(contexts))]
        v = rate(ch, items, ctx, cond, set(pick), subset)
        if v is not None:
            out.append(v)
    a = np.array(out)
    return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))


def main():
    items, ctx, ch, dropped, n_rows = load()
    contexts = sorted(set(ctx.values()))
    analysis = json.loads((F / "partner_analysis.json").read_text())

    print(f"SOURCE FILES")
    print(f"  trials   : {F/'partner_results.json'}  ({n_rows} rows)")
    print(f"  items    : {F/'partner_items.json'}")
    print(f"  analysis : {F/'partner_analysis.json'}  (cross-check only)")
    print(f"  rows dropped as unusable: {dropped}\n")

    print("PANEL A -- recomputed from trial-level data, vs reported")
    A = {}
    for c in CONDS:
        p = rate(ch, items, ctx, c, set(contexts))
        lo, hi = boot_ci(ch, items, ctx, c, contexts)
        A[c] = (p, lo, hi)
        rp, rlo, rhi = REPORTED[c]
        ok = abs(p - rp) < 5e-4
        print(f"  {c:17s} p={p:.4f} CI[{lo:.4f},{hi:.4f}]   reported {rp:.4f} "
              f"[{rlo:.3f},{rhi:.3f}]   point match: {ok}")

    print("\nPANEL B -- by focal preference-strength tertile")
    B = {}
    for c in CONDS:
        row = []
        for t in TERTILES:
            sub = [it for it in items if items[it]["tertile"] == t]
            p = rate(ch, items, ctx, c, set(contexts), sub)
            lo, hi = boot_ci(ch, items, ctx, c, contexts, sub)
            row.append((p, lo, hi))
        B[c] = row
        print(f"  {c:17s} " + "  ".join(f"{t}={v[0]:.4f}" for t, v in zip(TERTILES, row)))

    # ---------------------------------------------------------------- figure
    plt.style.use("academic")
    plt.rcParams.update({"font.size": 9, "font.family": "sans-serif",
                         "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"]})
    fig = plt.figure(figsize=(7.4, 3.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.7, 1.0], wspace=0.30)
    axA, axB = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

    # --- Panel A ---------------------------------------------------------
    x = np.arange(len(CONDS))
    fills = ["k", "k", "0.55", "none"]      # greyscale-safe: fill + marker both vary
    marks = ["o", "^", "D", "s"]
    for i, c in enumerate(CONDS):
        axA.errorbar(x[i], A[c][0],
                     yerr=[[A[c][0] - A[c][1]], [A[c][2] - A[c][0]]],
                     fmt=marks[i], color="k", markerfacecolor=fills[i], markersize=5.5,
                     capsize=3, elinewidth=0.8, capthick=0.8, zorder=3)
    axA.axhline(0.5, color="0.65", lw=0.6, ls=":", zorder=1)
    axA.text(3.45, 0.512, "chance", fontsize=6.5, color="0.45", va="bottom", ha="right")
    axA.set_xticks(x)
    axA.set_xticklabels([LABELS[c] for c in CONDS], fontsize=7.5)
    axA.set_ylim(0, 1); axA.set_xlim(-0.5, 3.5)
    axA.set_ylabel("P(choose focal model's own-policy option)", fontsize=8.5)
    axA.set_title("A.  Partner identity versus explicit partner-policy information",
                  fontsize=9, loc="left", pad=16)
    axA.text(0, 1.015, "Lower values indicate greater deviation toward the "
             "predicted partner-favoured option.",
             transform=axA.transAxes, fontsize=6.8, color="0.35", va="bottom")

    # --- Panel B ---------------------------------------------------------
    xb = np.arange(3)
    styles = {"UNKNOWN": ("o", "k", "-"), "SAME": ("^", "k", "-"),
              "DIFF_UNINFORMED": ("D", "0.55", "--"), "DIFF_INFORMED": ("s", "none", "-")}
    flat = {"UNKNOWN": "UNKNOWN", "SAME": "SAME",
            "DIFF_UNINFORMED": "DIFF-UNINFORMED", "DIFF_INFORMED": "DIFF-INFORMED"}
    for c in CONDS:
        m, fc, ls = styles[c]
        v = [B[c][k][0] for k in range(3)]
        e = [[B[c][k][0] - B[c][k][1] for k in range(3)],
             [B[c][k][2] - B[c][k][0] for k in range(3)]]
        axB.errorbar(xb, v, yerr=e, fmt=m, ls=ls, color="k", markerfacecolor=fc,
                     markersize=4, lw=0.8, capsize=2, elinewidth=0.7, capthick=0.7,
                     label=flat[c])
    axB.set_xticks(xb)
    axB.set_xticklabels(["low", "medium", "high"], fontsize=7.5)
    axB.set_xlabel("focal preference strength  |\u0394w|", fontsize=8.5)
    axB.set_ylim(0, 1); axB.set_xlim(-0.25, 2.25)
    axB.set_title("B.  Explicit partner information matters\n     most for weak preferences",
                  fontsize=9, loc="left", pad=16)
    axB.legend(frameon=False, fontsize=6.4, loc="lower right",
               handlelength=2.2, borderaxespad=0.2, labelspacing=0.35)

    for ax in (axA, axB):
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(0.8); ax.spines["bottom"].set_linewidth(0.8)
        ax.tick_params(direction="out", width=0.8, length=3, labelsize=8)
        ax.grid(False)

    fig.subplots_adjust(left=0.088, right=0.985, top=0.775, bottom=0.155)
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        for ext in ("pdf", "png"):
            fp = d / f"partner_conditional_deviation_pilot.{ext}"
            fig.savefig(fp, dpi=300)
            print(f"  saved {fp}")
    print(f"\nn = {n_rows} trials, {len(items)} items, {len(contexts)} contexts, "
          f"{dropped} dropped")


if __name__ == "__main__":
    main()
