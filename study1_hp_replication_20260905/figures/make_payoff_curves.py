"""
Deck slide 5, rebuilt on the full pair sets.

The version in llm-self-coordination-v2.pptx plots ONE hand-picked exemplar pair per
model with binomial error bars. This plots every pair: 24 for GPT-5.5, 27 for Opus 5.
Error bars are SE across pairs, because the matched pair is the unit of evidence.
"""
import csv, json, os, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("academic")

HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
PAY = ["3", "5", "7", "9"]

def arm(stagec, pairs_csv, model_id):
    rows = [r for r in csv.DictReader(open(os.path.join(EXP, "data", stagec)))
            if r["included_in_analysis"] == "True"]
    assert {r["actor_model_id_returned"] for r in rows} == {model_id}
    att = collections.defaultdict(list)
    for r in rows:
        att[(r["stimulus"], r["safe_payoff"])].append(r["participation_decision"] == "ATTEMPT")
    P = {k: float(np.mean(v)) for k, v in att.items()}
    prs = [r for r in csv.DictReader(open(pairs_csv)) if r["approved"] == "True"]
    hi = np.array([[P[(p["stimulus_high"], s)] for s in PAY] for p in prs])
    lo = np.array([[P[(p["stimulus_low"], s)] for s in PAY] for p in prs])
    return hi, lo, len(prs)

G = arm("stageC_20260905_200932.csv", os.path.join(EXP, "matched_pairs_FROZEN.csv"),
        "gpt-5.5-2026-04-23")
C = arm("stageC_20260910_162358.csv",
        os.path.join(EXP, "opus5", "matched_pairs_FROZEN_opus5.csv"), "claude-opus-5")

# assert against the frozen primaries before drawing
for (hi, lo, n), want in ((G, (0.000, 0.028, 0.188, 0.252)),
                          (C, (0.000, -0.004, 0.000, 0.137))):
    got = (hi - lo).mean(axis=0)
    assert all(abs(round(g, 3) - w) < 1e-9 for g, w in zip(got, want)), (got, want)
print(f"assertions pass — GPT n={G[2]} pairs, Opus 5 n={C[2]} pairs")

fig, axes = plt.subplots(1, 2, figsize=(6.9, 3.5), sharey=True)
fig.subplots_adjust(bottom=.30, top=.80, wspace=.10)
for ax, (hi, lo, n), lab, mdl in ((axes[0], G, "A", "GPT-5.5"),
                                  (axes[1], C, "B", "Claude Opus 5")):
    x = np.arange(4)
    for arr, mk, fc, ls in ((hi, "o", "k", "-"), (lo, "o", "white", "--")):
        m = arr.mean(axis=0); se = arr.std(axis=0, ddof=1) / np.sqrt(n)
        ln, = ax.plot(x, m, ls, color="k", lw=1.2, marker=mk, ms=6.5,
                      markerfacecolor=fc, markeredgecolor="k", markeredgewidth=1.1)
        if ls == "--": ln.set_dashes((4, 2.4))
        ax.errorbar(x, m, yerr=se, fmt="none", ecolor="k", elinewidth=.9, capsize=2.6)
    ax.set_xticks(x); ax.set_xticklabels(PAY)
    ax.set_xlabel("safe payoff (points offered to walk away)")
    ax.set_xlim(-.35, 3.35); ax.set_ylim(-.05, 1.09)
    ax.text(0, 1.06, f"{lab}  {mdl}", transform=ax.transAxes, fontsize=10, va="bottom")
    ax.text(.03, .06, f"{n} matched pairs", transform=ax.transAxes, fontsize=8,
            color="#5D6572")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
axes[0].set_ylabel("P(attempt coordination)")
h = [plt.Line2D([], [], color="k", marker="o", ls="-", ms=6, lw=1.2,
                markerfacecolor="k", label="higher own-copy match"),
     plt.Line2D([], [], color="k", marker="o", ls="--", ms=6, lw=1.2,
                markerfacecolor="white", label="lower own-copy match")]
fig.legend(handles=h, frameon=False, ncol=2, fontsize=9, loc="upper center",
           bbox_to_anchor=(.5, 1.0), columnspacing=2.6, handlelength=2.8)
fig.text(.5, .055, "Points are means over all matched pairs; bars are SE across pairs "
         "(the pair is the unit of evidence).", ha="center", fontsize=7.4, style="italic")
for ext, kw in ((".pdf", {}), (".png", dict(dpi=300))):
    fig.savefig(os.path.join(HERE, "study1_payoff_curves" + ext), facecolor="white", **kw)
    fig.savefig(os.path.expanduser(
        "~/Downloads/self-coordination-figures/study1_payoff_curves" + ext),
        facecolor="white", **kw)
print("wrote figures/study1_payoff_curves.{pdf,png} and to ~/Downloads/self-coordination-figures/")
