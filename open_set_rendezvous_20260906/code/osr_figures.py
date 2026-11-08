"""Open-set online rendezvous -- FIGURES.

Written AFTER the strategic analysis was read. Not a frozen artifact and not part
of the pre-registration: it plots numbers already computed by the frozen
`osr_analyze.py` / `osr_strategic.py`, it does not compute a new endpoint. Every
per-context value here is recomputed with the frozen helpers imported from
`osr_strategic` so a figure cannot silently disagree with the log.

Figures (all canon_host unless noted, monitor depth k=5 where a depth is fixed):
  fig1  baseline: within-context vs cross-context match, per context
  fig2  strategic: paired baseline -> monitored slopes for p_match and p_evade
  fig3  strategic: joint-payoff difference by monitor depth x canonicalization level
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import osr_strategic as ST                                            # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIGS = ROOT / "figures"
FIGS.mkdir(exist_ok=True)

plt.style.use("academic")
K_MAIN = 5
LEVEL_MAIN = "canon_host"


def save(fig, stem):
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{stem}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> figures/{stem}.pdf + .png")


# ---------------------------------------------------------------- fig 1
def fig1():
    rows = [r for r in json.loads((DATA / "osr_context_summary.json").read_text())
            if r["level"] == LEVEL_MAIN]
    rows.sort(key=lambda r: r["p_match"])
    y = np.arange(len(rows))
    within = np.array([r["p_match"] for r in rows])
    cross = np.array([r["p_cross"] for r in rows])

    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    ax.hlines(y, cross, within, color="0.75", lw=0.6, zorder=1)
    ax.plot(within, y, "o", ms=4, mfc="black", mec="black", zorder=3,
            label="within context")
    ax.plot(cross, y, "s", ms=4, mfc="white", mec="black", mew=0.8, zorder=3,
            label="across contexts")
    ax.set_yticks(y)
    ax.set_yticklabels([r["context_id"] for r in rows])
    ax.set_xlabel("pairwise match rate")
    ax.set_xlim(-0.02, 1.02)
    ax.tick_params(axis="y", length=0)
    ax.legend(frameon=False, loc="lower right", handletextpad=0.4)
    save(fig, "fig1_baseline_within_vs_cross")
    return within.mean(), cross.mean()


# ---------------------------------------------------------------- fig 2
def per_context(level, k):
    base_a = ST.load("baseline")
    mon_a = ST.load("monitored")
    bs = ST.monitor_sets(ST.load("monitor_baseline"), level, k)
    ms = ST.monitor_sets(ST.load("monitor_monitored"), level, k)
    ba = ST.agent_by_ctx(base_a, level)
    ma = ST.agent_by_ctx(mon_a, level)
    out = []
    for c in sorted(set(ba) & set(ma)):
        jb, pmb, peb = ST.joint(ba[c], bs.get(c, set()))
        jm, pmm, pem = ST.joint(ma[c], ms.get(c, set()))
        out.append(dict(ctx=c, joint_b=jb, match_b=pmb, evade_b=peb,
                        joint_m=jm, match_m=pmm, evade_m=pem))
    return out


def fig2(rows):
    panels = [("match", "coordination  $p_{match}$"),
              ("evade", "evasion  $p_{evade}$")]
    fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.2), sharey=True)
    for ax, (key, lab) in zip(axes, panels):
        b = np.array([r[f"{key}_b"] for r in rows])
        m = np.array([r[f"{key}_m"] for r in rows])
        for bi, mi in zip(b, m):
            ax.plot([0, 1], [bi, mi], "-", color="0.65", lw=0.6, zorder=1)
        ax.plot(np.zeros_like(b), b, "o", ms=3.5, mfc="black", mec="black", zorder=3)
        ax.plot(np.ones_like(m), m, "s", ms=3.5, mfc="white", mec="black",
                mew=0.8, zorder=3)
        ax.plot([0, 1], [b.mean(), m.mean()], "k-", lw=1.6, zorder=4)
        ax.plot([0, 1], [b.mean(), m.mean()], "kD", ms=4.5, zorder=5)
        ax.set_xlim(-0.25, 1.25)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["baseline", "monitored"])
        ax.set_ylim(-0.03, 1.03)
        ax.set_title(lab, fontsize=9, pad=6)
    axes[0].set_ylabel("rate")
    save(fig, "fig2_strategic_match_evade_slopes")


# ---------------------------------------------------------------- fig 3
def fig3():
    res = json.loads((DATA / "osr_strategic_results.json").read_text())
    levels = [("exact", "o", "-", "black", "black"),
              ("canon_page", "s", "--", "white", "black"),
              ("canon_host", "^", ":", "0.55", "black")]
    depths = ST.DEPTHS
    x = np.arange(len(depths))

    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.axhline(0, color="black", lw=0.6)
    for i, (lv, mk, ls, mfc, mec) in enumerate(levels):
        off = (i - 1) * 0.13
        d = np.array([res[f"{lv}|k{k}|joint"]["diff"] for k in depths])
        lo = np.array([res[f"{lv}|k{k}|joint"]["lo"] for k in depths])
        hi = np.array([res[f"{lv}|k{k}|joint"]["hi"] for k in depths])
        ax.errorbar(x + off, d, yerr=[d - lo, hi - d], fmt=mk, ls=ls,
                    color="black", mfc=mfc, mec=mec, mew=0.8, ms=4.5,
                    lw=0.8, elinewidth=0.7, capsize=2, capthick=0.7,
                    label=lv.replace("canon_", ""))
    ax.set_xticks(x)
    ax.set_xticklabels([f"k = {k}" for k in depths])
    ax.set_xlabel("monitor prediction depth")
    ax.set_ylabel("joint payoff, monitored $-$ baseline")
    ax.legend(frameon=False, title="canonicalization", title_fontsize=9,
              handletextpad=0.5, loc="upper right")
    save(fig, "fig3_joint_payoff_by_depth")


if __name__ == "__main__":
    print(f"figures at level={LEVEL_MAIN}, k={K_MAIN}")
    w, c = fig1()
    print(f"  fig1 mean within {w:.3f}  cross {c:.3f}")
    rows = per_context(LEVEL_MAIN, K_MAIN)
    fig2(rows)
    mb = np.mean([r["match_b"] for r in rows]); mm = np.mean([r["match_m"] for r in rows])
    eb = np.mean([r["evade_b"] for r in rows]); em = np.mean([r["evade_m"] for r in rows])
    jb = np.mean([r["joint_b"] for r in rows]); jm = np.mean([r["joint_m"] for r in rows])
    print(f"  fig2 p_match {mb:.3f} -> {mm:.3f}   p_evade {eb:.3f} -> {em:.3f}"
          f"   joint {jb:.3f} -> {jm:.3f}")
    fig3()
