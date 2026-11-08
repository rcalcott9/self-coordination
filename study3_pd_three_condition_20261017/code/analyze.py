#!/usr/bin/env python3
"""Analyse the PD three-condition pilot. Usage: analyze.py [run|mock]  -> results/<dir>/analysis/"""
import json, math, random, re, sys, csv
from collections import Counter
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import fisher_exact

HERE = Path(__file__).resolve().parent.parent
tag = sys.argv[1] if len(sys.argv) > 1 else "run"
D = HERE / "results" / tag; OUT = D / "analysis"; OUT.mkdir(exist_ok=True)
FZ = json.loads((HERE / "design/FROZEN.json").read_text())
R = {x["job_key"]: x for x in map(json.loads, open(D / "responses.jsonl"))}
MODELS = ["GPT-5.5", "Claude Opus 5"]; CONDS = ["same_model", "different_model", "fixed_response"]
CLAB = {"same_model": "Same model", "different_model": "Different model", "fixed_response": "Fixed response"}
PAY = {k: v for k, v in FZ["payoffs_canonical"].items()}

def wilson(k, n, z=1.959964):
    if n == 0: return (float("nan"),) * 2
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)

# per-cell counts (primary unit = focal action)
cells = {}
for mo in MODELS:
    for c in CONDS:
        rs = [r for r in R.values() if r["model"] == mo and r["condition"] == c]
        nC = sum(r["action_canonical"] == "C" for r in rs); nD = sum(r["action_canonical"] == "D" for r in rs)
        inv = sum(r["status"] != "ok" for r in rs); n = nC + nD; lo, hi = wilson(nC, n)
        bymap = {m: (sum(r["action_canonical"] == "C" for r in rs if r["mapping"] == m), sum(r["status"] == "ok" for r in rs if r["mapping"] == m)) for m in (0, 1)}
        cells[(mo, c)] = dict(model=mo, condition=c, records=len(rs), n_valid=n, nC=nC, nD=nD, invalid=inv, coop=nC / n if n else float("nan"),
                              wilson_lo=lo, wilson_hi=hi, C_when_A_is_C=f"{bymap[0][0]}/{bymap[0][1]}", C_when_B_is_C=f"{bymap[1][0]}/{bymap[1][1]}")
with open(OUT / "cells.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(next(iter(cells.values())).keys())); w.writeheader(); [w.writerow(v) for v in cells.values()]

# paired payoffs under the frozen pairing (exploratory; partners shared / dependent)
pay = {}
for mo in MODELS:
    for c in CONDS:
        rs = [r for r in R.values() if r["model"] == mo and r["condition"] == c and r["status"] == "ok"]
        pairs = [(r["action_canonical"], R[r["partner_job_key"]]["action_canonical"]) for r in rs
                 if r["partner_job_key"] in R and R[r["partner_job_key"]]["status"] == "ok"]
        oc = Counter(a + b for a, b in pairs)
        pay[(mo, c)] = dict(n_pairs=len(pairs), mean_focal=sum(PAY[a + b][0] for a, b in pairs) / len(pairs) if pairs else float("nan"),
                            mean_joint=sum(sum(PAY[a + b]) for a, b in pairs) / len(pairs) if pairs else float("nan"),
                            outcomes={k: oc.get(k, 0) for k in ("CC", "CD", "DC", "DD")},
                            dominance_gain=sum(PAY["D" + b][0] - PAY[a + b][0] for a, b in pairs if a == "C") / len(pairs) if pairs else float("nan"))

# exploratory contrasts (Fisher exact, two-sided; not corrected; focal actions)
contr = []
for mo in MODELS:
    for a_, b_ in (("same_model", "fixed_response"), ("same_model", "different_model"), ("different_model", "fixed_response")):
        A, B = cells[(mo, a_)], cells[(mo, b_)]
        if A["n_valid"] and B["n_valid"]:
            p = fisher_exact([[A["nC"], A["nD"]], [B["nC"], B["nD"]]])[1]
            contr.append(dict(model=mo, contrast=f"{CLAB[a_]} - {CLAB[b_]}", diff=A["coop"] - B["coop"], fisher_p=p))

# explanation coding: keyword inference on the model's REPORTED reason (not its internal process)
CODES = {
 "shared_procedure": r"correlat|identical|same model|copy|copies|mirror|symmetr|same reasoning|reason(?:s|ing)? the same|same (?:way|choice|decision|logic|conclusion)|likely (?:to )?(?:choose|pick|make) the same|similar(?:ly)? reason|decision procedure|superrational",
 "fixed_action_dominance": r"dominat|regardless|whatever the other|no matter|either way|in both cases|in every case|whichever",
 "social_or_joint": r"mutual|joint|collective|fair|both (?:of us|get|receive|players|participants)|together|cooperat|trust",
 "prerecorded_or_causal": r"already (?:been )?(?:made|recorded|fixed|determined)|prerecorded|cannot (?:change|influence|affect)|can't (?:change|influence)|sealed|fixed choice|causal",
 "misreads_game": r"stag hunt|not a prisoner|coordination game",
}
expl = {}
for mo in MODELS:
    for c in CONDS:
        rs = [r for r in R.values() if r["model"] == mo and r["condition"] == c and r["status"] == "ok"]
        row = {}
        for code, pat in CODES.items():
            for act in ("C", "D"):
                sub = [r for r in rs if r["action_canonical"] == act]
                row[f"{code}|{act}"] = f"{sum(bool(re.search(pat, r['reason'] or '', re.I)) for r in sub)}/{len(sub)}"
        expl[(mo, c)] = row
rng = random.Random(7); samples = {}
for mo in MODELS:
    for c in CONDS:
        rs = sorted([r for r in R.values() if r["model"] == mo and r["condition"] == c and r["status"] == "ok"], key=lambda r: r["job_key"])
        samples[(mo, c)] = rng.sample(rs, min(4, len(rs)))

# figure
plt.style.use("academic")
fig, ax = plt.subplots(figsize=(5.5, 3.2))
STY = {"GPT-5.5": dict(marker="o", mfc="black", mec="black", ls="-", off=-0.12),
       "Claude Opus 5": dict(marker="s", mfc="white", mec="black", ls="--", off=0.12)}
for mo in MODELS:
    s = STY[mo]; xs = [i + s["off"] for i in range(3)]
    ys = [100 * cells[(mo, c)]["coop"] for c in CONDS]
    lo = [100 * cells[(mo, c)]["wilson_lo"] for c in CONDS]; hi = [100 * cells[(mo, c)]["wilson_hi"] for c in CONDS]
    ax.errorbar(xs, ys, yerr=[[y - l for y, l in zip(ys, lo)], [h - y for y, h in zip(ys, hi)]], fmt="none", ecolor="black", elinewidth=0.8, capsize=2.5, capthick=0.8)
    ax.plot(xs, ys, color="black", ls="none", marker=s["marker"], mfc=s["mfc"], mec=s["mec"], ms=5, label=mo, zorder=3)
    for x, c, y, l, h in zip(xs, CONDS, ys, lo, hi):
        v = cells[(mo, c)]; lab = f"{v['nC']}/{v['n_valid']}"
        if y > 50: ax.text(x, l - 3, lab, ha="center", va="top", fontsize=7.5)      # label below the interval near the ceiling
        else: ax.text(x, h + 3, lab, ha="center", va="bottom", fontsize=7.5)
ax.set_xticks(range(3)); ax.set_xticklabels([CLAB[c] for c in CONDS]); ax.set_xlim(-0.5, 2.5)
ax.set_ylim(-3, 103); ax.set_yticks(range(0, 101, 20)); ax.set_ylabel("Cooperation (%)"); ax.set_xlabel("Partner condition")
ax.spines["left"].set_bounds(0, 100)
ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, handlelength=1.2)
fig.tight_layout()
for ext in ("png", "pdf"): fig.savefig(OUT / f"fig_pd_three_conditions.{ext}", dpi=300)

# machine-readable summary
summ = dict(cells={f"{k[0]}|{k[1]}": v for k, v in cells.items()}, paired_payoffs={f"{k[0]}|{k[1]}": v for k, v in pay.items()},
            contrasts=contr, explanation_codes={f"{k[0]}|{k[1]}": v for k, v in expl.items()},
            spend=dict(run_usd=round(sum(r["cost_usd"] for r in R.values()), 5)),
            status_counts=dict(Counter(r["status"] for r in R.values())))
(OUT / "summary.json").write_text(json.dumps(summ, indent=1))
(OUT / "explanation_samples.json").write_text(json.dumps({f"{k[0]}|{k[1]}": [dict(job_key=r["job_key"], action_canonical=r["action_canonical"], action_label=r["action_label"], mapping=r["mapping"], reason=r["reason"]) for r in v] for k, v in samples.items()}, indent=1))
print(json.dumps(summ["cells"], indent=0)[:3000]); print(json.dumps(summ["paired_payoffs"])[:2000]); print(json.dumps(contr))
