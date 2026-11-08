"""
Publication figures. Academic journal style throughout:

  Arial ~9pt, plain black text, no title inside the axes (descriptive text belongs
  in a caption), black 0.8pt axis lines with top/right spines removed, ticks
  outward, no heavy gridlines, thin capped error bars, journal-column size
  5.5 x 3.2in at 300dpi, exported as PDF as well as PNG so text stays vector.

  Series are distinguished by MARKER and LINETYPE as well as tone (filled circle /
  solid vs open square / dashed), so every figure survives greyscale printing.

  FIGURE 1  matching        per pair: auditor/public prediction vs true self-match
  FIGURE 2  primary         P(ATTEMPT) vs safe payoff, high- vs low-true stimulus
  FIGURE 3  summary         true - auditor  vs  within-pair willingness to attempt
  FIGURE S1 supplementary   attempt curves over safe payoff, all cells

Run:  python3 figures.py
"""
import csv, os, sys
from collections import defaultdict
import psc_common as P

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    plt.style.use("academic")
except Exception:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        "axes.linewidth": 0.8, "axes.edgecolor": "black", "text.color": "black",
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.major.width": 0.8, "ytick.major.width": 0.8,
        "axes.grid": False, "legend.frameon": False,
        "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    })

COL = 5.5, 3.2
HIGH = dict(marker="o", markerfacecolor="black", markeredgecolor="black",
            linestyle="-", color="black", markersize=4, linewidth=1.0)
LOW = dict(marker="s", markerfacecolor="white", markeredgecolor="black",
           linestyle="--", color="black", markersize=4, linewidth=1.0)
EB = dict(elinewidth=0.7, capsize=2, capthick=0.7, ecolor="black")


def read(name, base=None):
    p = os.path.join(base or P.DATA, name)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def save(fig, stem):
    os.makedirs(P.VIZ, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(P.VIZ, f"{stem}.{ext}"))
    print(f"  -> {os.path.join(P.VIZ, stem)}.png / .pdf")
    plt.close(fig)


def fig1_matching(pairs):
    """Pairs are similar in public prediction but different in true self-coordination."""
    if not pairs:
        return
    fig, axes = plt.subplots(1, 2, figsize=(COL[0], COL[1]), sharey=True)
    for ax, model in zip(axes, ("gpt", "claude")):
        ps = [p for p in pairs if p["focal_model"] == model]
        for i, p in enumerate(ps):
            for key, sty, lab in ((("true_self_match_high", "auditor_prediction_high"), HIGH, "high"),
                                  (("true_self_match_low", "auditor_prediction_low"), LOW, "low")):
                ax.plot([i - 0.12 if lab == "high" else i + 0.12], [float(p[key[0]])],
                        **{**sty, "linestyle": "none"})
                ax.plot([i - 0.12 if lab == "high" else i + 0.12], [float(p[key[1]])],
                        marker="_", color="black", markersize=9, linestyle="none")
            ax.plot([i - 0.12, i + 0.12],
                    [float(p["auditor_prediction_high"]), float(p["auditor_prediction_low"])],
                    color="black", linewidth=0.6, linestyle=":")
        ax.set_xticks(range(len(ps)))
        ax.set_xticklabels([p["pair_id"].split("__")[1][:9] + "\nvs " + p["pair_id"].split("__")[-1][:9]
                            for p in ps], fontsize=6)
        ax.set_xlabel(P.DISPLAY[model])
        ax.set_ylim(0, 1.02)
    axes[0].set_ylabel("coordination probability")
    axes[0].plot([], [], **HIGH, label="true self-match (high)")
    axes[0].plot([], [], **LOW, label="true self-match (low)")
    axes[0].plot([], [], marker="_", color="black", linestyle="none", label="auditor prediction")
    axes[0].legend(loc="lower left", fontsize=6)
    fig.tight_layout()
    save(fig, "fig1_matching")


def fig2_primary(pairs, att):
    """P(ATTEMPT) vs safe payoff, high- vs low-true stimulus, one panel per pair."""
    if not pairs or not att:
        return
    rate = {(r["model"], r["stimulus"], int(r["safe_payoff"])): r for r in att}
    n = len(pairs)
    ncol = min(n, 4)
    nrow = (n + ncol - 1) // ncol
    fig, axes = plt.subplots(nrow, ncol, figsize=(COL[0], COL[1] * max(nrow * 0.62, 0.8)),
                             sharey=True, squeeze=False)
    safes = sorted({int(r["safe_payoff"]) for r in att})
    for k, p in enumerate(pairs):
        ax = axes[k // ncol][k % ncol]
        m = p["focal_model"]
        for sid, sty in ((p["stimulus_high"], HIGH), (p["stimulus_low"], LOW)):
            xs, ys, lo, hi = [], [], [], []
            for s in safes:
                r = rate.get((m, sid, s))
                if not r:
                    continue
                xs.append(s); ys.append(float(r["attempt_rate"]))
                lo.append(float(r["attempt_rate"]) - float(r["ci_lo"]))
                hi.append(float(r["ci_hi"]) - float(r["attempt_rate"]))
            if xs:
                ax.errorbar(xs, ys, yerr=[lo, hi], **sty, **EB)
        ax.set_xticks(safes)
        ax.set_ylim(-0.02, 1.02)
        ax.set_title(f"{P.DISPLAY[m]}\n{p['stimulus_high'][:11]} vs {p['stimulus_low'][:11]}",
                     fontsize=6)
        if k % ncol == 0:
            ax.set_ylabel("P(ATTEMPT)")
        if k // ncol == nrow - 1:
            ax.set_xlabel("safe payoff")
    for k in range(n, nrow * ncol):
        axes[k // ncol][k % ncol].axis("off")
    axes[0][0].plot([], [], **HIGH, label="high true self-match")
    axes[0][0].plot([], [], **LOW, label="matched low")
    axes[0][0].legend(loc="lower left", fontsize=5.5)
    fig.tight_layout()
    save(fig, "fig2_primary_behavioral")


def fig3_summary(att):
    """x = true - auditor (policy-specific coordination); y = P(ATTEMPT), by model."""
    if not att:
        return
    fig, axes = plt.subplots(1, 2, figsize=(COL[0], COL[1]), sharey=True)
    for ax, model in zip(axes, ("gpt", "claude")):
        rs = [r for r in att if r["model"] == model and r["policy_specific"] != ""]
        by = defaultdict(list)
        for r in rs:
            by[r["stimulus"]].append(r)
        for sid, group in by.items():
            x = float(group[0]["policy_specific"])
            y = sum(float(g["attempt_rate"]) for g in group) / len(group)
            fb = str(group[0]["form_consistency"]) not in ("", "nan") and \
                float(group[0]["form_consistency"]) < P.FC_CLEAN
            ax.plot([x], [y], marker="s" if fb else "o",
                    markerfacecolor="white" if fb else "black",
                    markeredgecolor="black", markersize=4, linestyle="none")
        ax.axvline(0, color="black", linewidth=0.6, linestyle=":")
        ax.set_xlabel("true self-match - auditor prediction")
        ax.set_title(P.DISPLAY[model], fontsize=8)
        ax.set_ylim(-0.02, 1.02)
    axes[0].set_ylabel("mean P(ATTEMPT)")
    axes[0].plot([], [], marker="o", color="black", linestyle="none", markersize=4,
                 label="clean policy")
    axes[0].plot([], [], marker="s", markerfacecolor="white", markeredgecolor="black",
                 linestyle="none", markersize=4, label="position fallback")
    axes[0].legend(loc="lower right", fontsize=6)
    fig.tight_layout()
    save(fig, "fig3_summary")


def figS1(att):
    if not att:
        return
    fig, axes = plt.subplots(1, 2, figsize=(COL[0], COL[1]), sharey=True)
    safes = sorted({int(r["safe_payoff"]) for r in att})
    for ax, model in zip(axes, ("gpt", "claude")):
        by = defaultdict(dict)
        for r in att:
            if r["model"] == model:
                by[r["stimulus"]][int(r["safe_payoff"])] = float(r["attempt_rate"])
        for i, (sid, d) in enumerate(sorted(by.items())):
            xs = [s for s in safes if s in d]
            ax.plot(xs, [d[s] for s in xs], color="black", linewidth=0.7,
                    linestyle=["-", "--", "-.", ":"][i % 4],
                    marker=["o", "s", "^", "D"][i % 4], markersize=3,
                    markerfacecolor="black" if i % 2 else "white",
                    markeredgecolor="black", label=sid)
        ax.set_xticks(safes); ax.set_xlabel("safe payoff")
        ax.set_title(P.DISPLAY[model], fontsize=8); ax.set_ylim(-0.02, 1.02)
    axes[0].set_ylabel("P(ATTEMPT)")
    axes[1].legend(fontsize=5, ncol=2, loc="upper right")
    fig.tight_layout()
    save(fig, "figS1_attempt_curves")


def main():
    pairs = [r for r in read("matched_pairs.csv", P.EXP)
             if str(r.get("approved", "")).lower() in ("true", "1", "yes")]
    att = read("attempt_rates.csv")
    print("=== figures ===")
    fig1_matching(pairs)
    fig2_primary(pairs, att)
    fig3_summary(att)
    figS1(att)
    if not att:
        print("  (Stage C not yet run - figures 2, 3, S1 skipped)")


if __name__ == "__main__":
    main()
