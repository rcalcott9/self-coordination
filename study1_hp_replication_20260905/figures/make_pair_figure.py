"""
Study 1-HP replication — the matched pair is the unit of evidence.

Recomputed from raw Stage C rows and asserted against data/stage_c_primary.json
before anything is drawn.
"""
import csv, json, os, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("academic")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
PAY = ["3", "5", "7", "9"]

rows = [r for r in csv.DictReader(open(os.path.join(D, "stageC_20260905_200932.csv")))
        if r["included_in_analysis"] == "True"]
pairs = list(csv.DictReader(open(os.path.join(HERE, "..", "matched_pairs_FROZEN.csv"))))
prim = json.load(open(os.path.join(D, "stage_c_primary.json")))

att = collections.defaultdict(list)
for r in rows:
    att[(r["stimulus"], r["safe_payoff"])].append(r["participation_decision"] == "ATTEMPT")
P = {k: float(np.mean(v)) for k, v in att.items()}

delta, byp = [], {p: [] for p in PAY}
for pr in pairs:
    hi, lo = pr["stimulus_high"], pr["stimulus_low"]
    d = [P[(hi, p)] - P[(lo, p)] for p in PAY]
    delta.append((pr["pair_id"], float(np.mean(d))))
    for p, x in zip(PAY, d):
        byp[p].append(x)
delta.sort(key=lambda t: t[1])
dv = np.array([d for _, d in delta])

# ---- assertions against the frozen primary ----
assert len(delta) == prim["n_pairs"] == 24, len(delta)
assert int((dv > 0).sum()) == prim["k_positive"] == 17, (dv > 0).sum()
assert abs(dv.mean() - 0.1168) < 5e-4, dv.mean()
# RESULTS.md prints these to 3 dp, so compare at that precision, not tighter:
# safe=7 recomputes to 0.18750 and is printed +0.188.
for p, want in zip(PAY, (0.000, 0.028, 0.188, 0.252)):
    assert abs(round(np.mean(byp[p]), 3) - want) < 1e-9, (p, np.mean(byp[p]))
print(f"assertions pass — mean delta {dv.mean():+.4f}, {int((dv>0).sum())}/24 positive")

MU, CI = prim["mu"], prim["ci"]
fig, (axA, axB) = plt.subplots(1, 2, figsize=(7.3, 3.9),
                               gridspec_kw=dict(width_ratios=[1.55, 1]))
fig.subplots_adjust(bottom=.26, wspace=.30)

# ---- A: per-pair differences -------------------------------------------------
y = np.arange(len(dv))
axA.axvspan(CI[0], CI[1], color="#D8DBE0", zorder=1)
axA.axvline(MU, color="#1D2027", lw=1.0, zorder=2)
axA.axvline(0, color="#1D2027", lw=.9, ls=(0, (4, 3)), zorder=2)
for i, d in enumerate(dv):
    axA.plot([0, d], [i, i], "-", color="#8A8F98", lw=.8, zorder=3)
axA.scatter(dv, y, s=20, marker="o", zorder=4,
            facecolors=["#1D2027" if d > 0 else "white" for d in dv],
            edgecolors="#1D2027", linewidths=.9)
axA.set_yticks([]); axA.set_ylim(-1.4, len(dv) + .4)
axA.set_xlabel("P(attempt | higher self-coordination)\n− P(attempt | matched lower)")
axA.set_ylabel("24 matched stimulus pairs\n(sorted)")
axA.set_xlim(-.33, .55)
axA.annotate(f"µ = {MU:+.4f}\n95% CI [{CI[0]:+.4f}, {CI[1]:+.4f}]\n"
             f"{int((dv>0).sum())}/24 pairs positive",
             xy=(-.325, len(dv) - .6), fontsize=7.4, va="top", family="monospace")

# ---- B: payoff-resolved ------------------------------------------------------
x = np.arange(len(PAY))
hi_r = [float(np.mean([P[(p["stimulus_high"], s)] for p in pairs])) for s in PAY]
lo_r = [float(np.mean([P[(p["stimulus_low"], s)] for p in pairs])) for s in PAY]
axB.plot(x, hi_r, "-o", color="#1D2027", lw=1.2, ms=6, markerfacecolor="#1D2027",
         markeredgecolor="#1D2027", label="higher self-coordination")
ln, = axB.plot(x, lo_r, "--s", color="#1D2027", lw=1.2, ms=6, markerfacecolor="white",
               markeredgecolor="#1D2027", label="matched lower")
ln.set_dashes((4, 2.4))
for i in (2, 3):
    axB.annotate("", xy=(x[i], hi_r[i]), xytext=(x[i], lo_r[i]),
                 arrowprops=dict(arrowstyle="<->", lw=.8, color="#1D2027",
                                 shrinkA=4, shrinkB=4))
    axB.annotate(f"{hi_r[i]-lo_r[i]:+.3f}", xy=(x[i] + .10,
                 (hi_r[i] + lo_r[i]) / 2), fontsize=7.5, va="center")
axB.set_xticks(x); axB.set_xticklabels(PAY)
axB.set_xlabel("Safe payoff (points offered to walk away)")
axB.set_ylabel("P(attempt coordination)")
axB.set_ylim(-.04, 1.08); axB.set_xlim(-.35, 3.85)
axB.legend(frameon=False, fontsize=7.5, loc="lower left", handlelength=2.4)

for ax in (axA, axB):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axA.spines["left"].set_visible(False)
fig.text(.5, .045, "GPT-5.5 focal, 24 matched pairs, 4,608 Stage C decisions.\n"
         "Pairs matched on externally observable coordinability, rated by Claude Opus 5.",
         ha="center", fontsize=7.3, style="italic", linespacing=1.5)

for ext, kw in ((".pdf", {}), (".png", dict(dpi=300))):
    fig.savefig(os.path.join(HERE, "study1_matched_pairs" + ext),
                facecolor="white", bbox_inches="tight", pad_inches=.06, **kw)
print("wrote figures/study1_matched_pairs.pdf / .png")
