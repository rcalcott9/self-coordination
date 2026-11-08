"""Stage C pilot figure: additive partner effect, and what it costs."""
import os, csv, json, glob
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import s4_common as S

plt.style.use("academic")
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "figures"); os.makedirs(FIG, exist_ok=True)
rows = [r for r in csv.DictReader(open(os.path.join(S.DATA, "stageC_pilot_results.csv")))
        if r["parse_ok"] == "True"]
mean = lambda v: float(np.mean(v)) if len(v) else float("nan")

dist = {}
for f in sorted(glob.glob(os.path.join(S.DATA, "cell_metrics_discovery_batch*.csv"))):
    for r in csv.DictReader(open(f)):
        c = json.loads(r["item_counts"]); n = sum(c.values())
        dist[(r["stimulus_id"], r["model"])] = {int(k): v/n for k, v in c.items()}

fig, axes = plt.subplots(1, 3, figsize=(6.9, 2.6))
X = [0, 1]

# A / B: attempt rate, HIGH vs LOW, by partner
for ax, focal in zip(axes[:2], ("gpt", "claude")):
    for same, mk, mfc, lab in ((("1"), "o", "k", "same-model partner"),
                               (("0"), "s", "none", "different model")):
        y, e = [], []
        for lev in ("LOW", "HIGH"):
            v = [int(r["attempt"]) for r in rows if r["focal"] == focal
                 and r["level"] == lev and r["partner_same"] == same]
            y.append(mean(v)); e.append(np.std(v, ddof=1)/np.sqrt(len(v)))
        ax.errorbar(X, y, yerr=e, fmt=mk, mfc=mfc, mec="k", mew=0.9, ms=5,
                    color="k", lw=0.9, capsize=2.5, ls="-" if same == "1" else "--",
                    label=lab)
    ax.set_xticks(X); ax.set_xticklabels(["weak\nconvention", "strong\nconvention"])
    ax.set_xlim(-0.35, 1.35); ax.set_ylim(0, 1)
    ax.set_ylabel("P(attempt)" if focal == "gpt" else "")
    ax.text(0.03, 0.96, "A" if focal == "gpt" else "B", transform=ax.transAxes,
            fontsize=10, va="top")
    ax.text(0.97, 0.97, S.DISPLAY[focal], transform=ax.transAxes, ha="right",
            va="top", fontsize=8)
axes[0].legend(frameon=False, fontsize=7, loc="lower left",
               handletextpad=0.5, borderaxespad=0.3)

# C: realized EV vs safe EV
ax = axes[2]
cells, ev, sev = [], [], []
for focal in ("gpt", "claude"):
    other = S.OTHER[focal]
    for lev in ("HIGH", "LOW"):
        for same in ("1", "0"):
            sel = [r for r in rows if r["focal"] == focal and r["level"] == lev
                   and r["partner_same"] == same]
            att = [r for r in sel if r["attempt"] == "1" and r["chosen_item"] != ""]
            pm = [dist.get((r["stimulus_id"], focal if same == "1" else other), {})
                  .get(int(r["chosen_item"]), 0.0) for r in att]
            rate = mean([int(r["attempt"]) for r in sel])
            ev.append(rate * 10 * mean(pm) if pm else 0)
            sev.append(mean([(1-int(r["attempt"]))*int(r["safe"]) for r in sel]))
            cells.append(f"{'G' if focal=='gpt' else 'C'}·{lev[0]}·{'S' if same=='1' else 'D'}")
ax.plot([0, 8], [0, 8], color="0.6", lw=0.8, ls=(0, (4, 3)))
for i, c in enumerate(cells):
    win = ev[i] > sev[i]
    ax.plot(sev[i], ev[i], "o" if win else "s", mfc="k" if win else "none",
            mec="k", mew=0.9, ms=5)
    off = [(5, 3), (5, 3), (5, 3), (-5, 6), (5, -9), (6, 2), (-6, -9), (5, 5)][i]
    ax.annotate(c, (sev[i], ev[i]), xytext=off, textcoords="offset points",
                fontsize=6, ha="left" if off[0] > 0 else "right")
ax.set_xlabel("EV forgone by taking SAFE"); ax.set_ylabel("realized EV from ATTEMPT")
ax.set_xlim(0, 6); ax.set_ylim(0, 8.6)
ax.text(0.03, 0.96, "C", transform=ax.transAxes, fontsize=10, va="top")
fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(FIG, f"pilot_beta3.{ext}"), dpi=300)
print("wrote", os.path.join(FIG, "pilot_beta3.[png|pdf]"))
