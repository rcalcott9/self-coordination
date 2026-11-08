"""Monitored Schelling Phase 1 -- figures. Frozen before sampling."""
import csv, json
from collections import Counter
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
F, G = ROOT / "data", ROOT / "figures"


def main():
    G.mkdir(exist_ok=True)
    items = list(csv.DictReader(open(F / "ms_item_summary.csv")))
    opts = list(csv.DictReader(open(F / "ms_option_level.csv")))
    S = np.load(F / "ms_null_study.npz")
    plt.style.use("academic")
    plt.rcParams.update({"font.size": 9, "font.family": "sans-serif",
                         "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"]})

    def finish(ax):
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(0.8); ax.spines["bottom"].set_linewidth(0.8)
        ax.tick_params(direction="out", width=0.8, length=3); ax.grid(False)

    # 1 observed vs null max-gap
    obs = np.array([float(r["max_gap"]) for r in items])
    fig, ax = plt.subplots(figsize=(4.2, 3.3))
    bins = np.linspace(0, max(0.6, obs.max() * 1.1), 26)
    ax.hist(S["mean_gap"], bins=bins, color="0.85", edgecolor="0.6", lw=0.6,
            density=True, label="full-study null (mean gap)")
    ax.hist(obs, bins=bins, histtype="step", color="k", lw=1.2, density=True,
            label="observed item max gaps")
    ax.set_xlabel("item-level max gap  (p$_{copy}$ − p$_{monitor}$)")
    ax.set_ylabel("density"); ax.legend(frameon=False, fontsize=7.5)
    finish(ax); fig.tight_layout(); fig.savefig(G / "fig1_gap_vs_null.pdf"); fig.savefig(G / "fig1_gap_vs_null.png", dpi=300)

    # 2 scatter p_copy vs p_monitor
    pc = np.array([float(r["p_copy"]) for r in opts])
    pm = np.array([float(r["p_monitor"]) for r in opts])
    fig, ax = plt.subplots(figsize=(3.6, 3.5))
    ax.plot([0, 1], [0, 1], "--", color="0.7", lw=0.8)
    ax.scatter(pm, pc, s=9, facecolors="none", edgecolors="k", linewidths=0.6)
    ax.set_xlabel("p$_{monitor}$"); ax.set_ylabel("p$_{copy}$")
    ax.set_xlim(-0.02, 1); ax.set_ylim(-0.02, 1)
    finish(ax); fig.tight_layout(); fig.savefig(G / "fig2_pcopy_vs_pmonitor.pdf"); fig.savefig(G / "fig2_pcopy_vs_pmonitor.png", dpi=300)

    # 3 rank composition of qualifying items
    q = [r for r in items if r["qualifies"] == "1"]
    rk = Counter(min(int(r["copy_rank"]), 3) for r in q)
    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    ax.bar([1, 2, 3], [rk[1], rk[2], rk[3]], color="0.55", edgecolor="k", lw=0.7, width=0.6)
    ax.set_xticks([1, 2, 3]); ax.set_xticklabels(["rank 1", "rank 2", "rank 3+"])
    ax.set_ylabel("qualifying items"); ax.set_xlabel("copy rank of max-gap option")
    finish(ax); fig.tight_layout(); fig.savefig(G / "fig3_rank_composition.pdf"); fig.savefig(G / "fig3_rank_composition.png", dpi=300)

    # 4 top candidate items: copy vs monitor distributions
    top = sorted(items, key=lambda r: -float(r["max_gap"]))[:6]
    fig, axes = plt.subplots(2, 3, figsize=(7.6, 4.4))
    for ax, r in zip(axes.ravel(), top):
        rows = [o for o in opts if o["item_id"] == r["item_id"]]
        rows = sorted(rows, key=lambda o: -float(o["p_copy"]))
        x = np.arange(len(rows))
        ax.bar(x - 0.2, [float(o["p_copy"]) for o in rows], width=0.4, color="0.35",
               edgecolor="none", label="copy")
        ax.bar(x + 0.2, [float(o["p_monitor"]) for o in rows], width=0.4, color="0.78",
               edgecolor="none", label="monitor")
        k = [i for i, o in enumerate(rows) if o["option"] == r["max_gap_option"]]
        if k:
            ax.plot(k[0], max(float(rows[k[0]]["p_copy"]), float(rows[k[0]]["p_monitor"])) + .04,
                    "v", color="k", markersize=4)
        ax.set_title(f"{r['item_id']}  gap={r['max_gap']}  p={r['null_p_value']}",
                     fontsize=7.5, loc="left")
        ax.set_xticks([]); ax.set_ylim(0, 1); finish(ax)
        ax.tick_params(labelsize=7)
    axes[0, 0].legend(frameon=False, fontsize=7)
    fig.supylabel("probability", fontsize=9)
    fig.tight_layout(); fig.savefig(G / "fig4_top_items.pdf"); fig.savefig(G / "fig4_top_items.png", dpi=300)
    # 5 displayed-position distribution (order-artifact verification)
    raw = {t: json.load(open(F / f"ms_raw_{t}.json")) for t in ("focal", "monitor")}
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    w = 0.4
    for i, (t, mk) in enumerate((("focal", "0.35"), ("monitor", "0.75"))):
        c = Counter(r["displayed_position"] for r in raw[t] if r.get("choice"))
        n = sum(c.values())
        ax.bar(np.arange(1, 13) + (i - 0.5) * w, [c.get(k, 0) / n for k in range(1, 13)],
               width=w, color=mk, edgecolor="none", label=t)
    ax.axhline(1 / 12, ls="--", color="k", lw=0.8)
    ax.set_xticks(range(1, 13)); ax.set_xlabel("displayed position of chosen option")
    ax.set_ylabel("proportion"); ax.legend(frameon=False, fontsize=7.5)
    finish(ax); fig.tight_layout()
    fig.savefig(G / "fig5_position_check.pdf"); fig.savefig(G / "fig5_position_check.png", dpi=300)
    print(f"figures -> {G}")


if __name__ == "__main__":
    main()
