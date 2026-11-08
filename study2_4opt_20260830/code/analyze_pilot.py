"""
Stage C pilot -> decision-scale beta3, plus the two nuisance parameters the power
simulation had to guess.

PRIMARY. beta3 = mean(gap | HIGH stimuli) - mean(gap | LOW stimuli), where
gap = P(ATTEMPT | same partner) - P(ATTEMPT | different partner) per stimulus.
Inference by permuting the HIGH/LOW label across FAMILIES, which is the unit of
independence (distinct families sit on the two sides of every pair).

Reported pooled over payoffs AND at the informative payoffs only. The smoke test
showed the grid censors: HIGH stimuli sit at ceiling for safe 3-5, LOW stimuli at
floor for safe 7-9, so pooling over all four dilutes the contrast. Censored cells
add noise, not bias - but the confirmatory should allocate against this.

ALSO MEASURED (these were guessed in power_simulation.py):
  - between-family SD of the attempt rate
  - baseline P(ATTEMPT) on LOW x DIFFERENT
so power can be recomputed on measured rather than assumed nuisance parameters.

SECONDARY. Realized coordination, scored at zero API cost against the held-out
Stage A choice distributions: partners are fresh independent draws, so
P(match) = sum_k p_k q_k with q from Stage A for the true partner model.
"""
import os, csv, glob, json, math
import numpy as np
import s4_common as S

SEED = 20260830
NPERM = 20000
SRC = os.path.join(S.DATA, "stageC_pilot_results.csv")
OUT = os.path.join(S.DATA, "pilot_summary.md")
L = []


def p(s=""):
    print(s); L.append(s)


def mean(v):
    return float(np.mean(v)) if len(v) else float("nan")


def load_stageA():
    """Item distribution per (stimulus, model) from discovery."""
    dist = {}
    for f in sorted(glob.glob(os.path.join(S.DATA, "cell_metrics_discovery_batch*.csv"))):
        for r in csv.DictReader(open(f)):
            c = json.loads(r["item_counts"])
            n = sum(c.values())
            dist[(r["stimulus_id"], r["model"])] = {int(k): v / n for k, v in c.items()}
    return dist


rows = [r for r in csv.DictReader(open(SRC)) if r["parse_ok"] == "True"]
allr = list(csv.DictReader(open(SRC)))
p("# Stage C pilot - decision-scale beta3")
p()
p(f"`{len(rows):,}` of `{len(allr):,}` trials parsed. 8 GPT pairs + 7 Claude pairs, "
  "20 reps per focal x stimulus x partner x safe payoff. **Pilot, not the "
  "confirmatory sample.**")
p()

# ------------------------------------------------------------------ gaps -----
def gaps(subset_payoffs=None):
    g = {}
    for r in rows:
        if subset_payoffs and int(r["safe"]) not in subset_payoffs:
            continue
        k = (r["focal"], r["family"], r["level"], r["stimulus_id"])
        g.setdefault(k, {"1": [], "0": []})[r["partner_same"]].append(int(r["attempt"]))
    out = {}
    for k, d in g.items():
        if d["1"] and d["0"]:
            out[k] = mean(d["1"]) - mean(d["0"])
    return out


def beta3(g, focal):
    hi = [v for k, v in g.items() if k[0] == focal and k[2] == "HIGH"]
    lo = [v for k, v in g.items() if k[0] == focal and k[2] == "LOW"]
    return mean(hi) - mean(lo), hi, lo


def perm_p(hi, lo, rng):
    obs = mean(hi) - mean(lo)
    pool = np.array(hi + lo)
    n = len(hi)
    idx = np.argsort(rng.random((NPERM, len(pool))), axis=1)
    pm = pool[idx]
    stat = pm[:, :n].mean(axis=1) - pm[:, n:].mean(axis=1)
    return obs, float((np.abs(stat) >= abs(obs)).mean())


rng = np.random.default_rng(SEED)
p("## Primary: beta3 by focal model")
p()
p("| focal | payoffs | n HIGH fam | n LOW fam | mean gap HIGH | mean gap LOW | "
  "**beta3** | perm p |")
p("|---|---|---|---|---|---|---|---|")
res = {}
for label, sub in (("all {3,5,7,9}", None), ("informative {5,7}", {5, 7})):
    g = gaps(sub)
    for focal in ("gpt", "claude"):
        b3, hi, lo = beta3(g, focal)
        if not hi or not lo:
            continue
        obs, pv = perm_p(hi, lo, rng)
        res[(focal, label)] = (b3, pv, len(hi), len(lo))
        p(f"| {S.DISPLAY[focal]} | {label} | {len(hi)} | {len(lo)} | "
          f"{mean(hi):+.3f} | {mean(lo):+.3f} | **{b3:+.3f}** | {pv:.4f} |")
p()

# bootstrap CI on beta3, resampling FAMILIES
p("| focal | payoffs | beta3 | 95% CI (family bootstrap) |")
p("|---|---|---|---|")
for label, sub in (("all {3,5,7,9}", None), ("informative {5,7}", {5, 7})):
    g = gaps(sub)
    for focal in ("gpt", "claude"):
        b3, hi, lo = beta3(g, focal)
        if not hi or not lo:
            continue
        d = []
        for _ in range(10000):
            a = rng.choice(hi, len(hi), replace=True)
            b = rng.choice(lo, len(lo), replace=True)
            d.append(a.mean() - b.mean())
        d = np.sort(d)
        p(f"| {S.DISPLAY[focal]} | {label} | {b3:+.3f} | "
          f"[{d[250]:+.3f}, {d[9750]:+.3f}] |")
p()

# --------------------------------------------------------- main effects ------
p("## Main effects (context for beta3)")
p()
p("| focal | level | partner | attempt rate |")
p("|---|---|---|---|")
for focal in ("gpt", "claude"):
    for lev in ("HIGH", "LOW"):
        for same in ("1", "0"):
            v = [int(r["attempt"]) for r in rows if r["focal"] == focal
                 and r["level"] == lev and r["partner_same"] == same]
            if v:
                p(f"| {S.DISPLAY[focal]} | {lev} | "
                  f"{'SAME' if same=='1' else 'DIFF'} | {mean(v):.3f} |")
p()

p("## Payoff response (is the grid censoring?)")
p()
p("| focal | level | safe=3 | safe=5 | safe=7 | safe=9 |")
p("|---|---|---|---|---|---|")
for focal in ("gpt", "claude"):
    for lev in ("HIGH", "LOW"):
        cells = []
        for s in (3, 5, 7, 9):
            v = [int(r["attempt"]) for r in rows if r["focal"] == focal
                 and r["level"] == lev and int(r["safe"]) == s]
            cells.append(f"{mean(v):.2f}" if v else "-")
        p(f"| {S.DISPLAY[focal]} | {lev} | " + " | ".join(cells) + " |")
p()

# ------------------------------------------- measured nuisance parameters ----
p("## Nuisance parameters the power simulation had to guess")
p()
famrate = {}
for r in rows:
    famrate.setdefault((r["focal"], r["family"]), []).append(int(r["attempt"]))
for focal in ("gpt", "claude"):
    v = [mean(x) for k, x in famrate.items() if k[0] == focal]
    if len(v) > 1:
        p(f"- **{S.DISPLAY[focal]}** between-family SD of attempt rate: "
          f"**{np.std(v, ddof=1):.3f}** (simulation assumed 0.12), {len(v)} families")
base = [int(r["attempt"]) for r in rows if r["level"] == "LOW"
        and r["partner_same"] == "0"]
p(f"- baseline P(ATTEMPT) on LOW x DIFFERENT: **{mean(base):.3f}** "
  "(simulation assumed 0.40)")
p()

# ----------------------------------------------- realized coordination -------
p("## Realized coordination (scored against held-out Stage A, no extra API cost)")
p()
dist = load_stageA()
p("| focal | level | partner | P(match) on ATTEMPT trials | realized EV | SAFE EV |")
p("|---|---|---|---|---|---|")
for focal in ("gpt", "claude"):
    other = S.OTHER[focal]
    for lev in ("HIGH", "LOW"):
        for same in ("1", "0"):
            sel = [r for r in rows if r["focal"] == focal and r["level"] == lev
                   and r["partner_same"] == same]
            att = [r for r in sel if r["attempt"] == "1" and r["chosen_item"] != ""]
            if not sel:
                continue
            pm = []
            for r in att:
                pmod = focal if same == "1" else other
                q = dist.get((r["stimulus_id"], pmod), {})
                pm.append(q.get(int(r["chosen_item"]), 0.0))
            rate = mean([int(r["attempt"]) for r in sel])
            ev = rate * 10 * mean(pm) if pm else 0.0
            safe_ev = mean([(1 - int(r["attempt"])) * int(r["safe"]) for r in sel])
            p(f"| {S.DISPLAY[focal]} | {lev} | {'SAME' if same=='1' else 'DIFF'} | "
              f"{mean(pm) if pm else float('nan'):.3f} | {ev:.2f} | {safe_ev:.2f} |")
p()

# ------------------------------------------------------------- verdict -------
p("## Verdict")
p()
b3g = res.get(("gpt", "all {3,5,7,9}"), (float('nan'),))[0]
b3c = res.get(("claude", "all {3,5,7,9}"), (float('nan'),))[0]
big = max(abs(b3g), abs(b3c))
p(f"- decision-scale beta3: GPT **{b3g:+.3f}**, Claude **{b3c:+.3f}**")
p(f"- prediction-scale anchor was +0.033 / +0.043")
p()
if big >= 0.15:
    p("**The gradient AMPLIFIES from prediction to decision.** At this size the "
      "existing 8/7-pair battery is already at ~0.94/0.91 power, so the "
      "confirmatory at 30 reps is worth running as designed.")
elif big >= 0.08:
    p("**Intermediate.** beta3 sits in the band where power depends steeply on "
      "family count (10-15 families/side for 80%). Neither launching nor "
      "abandoning is clearly right - recompute power on the MEASURED nuisance "
      "parameters above before deciding.")
else:
    p("**The gradient does NOT amplify.** beta3 is at or below the prediction-scale "
      "anchor, where >40 families/side are needed for 80% power - infeasible. The "
      "honest output is a bounded null: the data rule out an interaction larger "
      "than roughly the CI upper limit above. Do not spend on the confirmatory.")

open(OUT, "w").write("\n".join(L) + "\n")
print(f"\nwrote {OUT}")
