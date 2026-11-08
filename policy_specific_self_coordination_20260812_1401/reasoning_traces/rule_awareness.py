#!/usr/bin/env python3
"""
Do the models ACKNOWLEDGE having / not having a form rule, and USE that to decide?

Three questions, in increasing order of how hard they are to fake:

  Q1 CALIBRATION  Does the rate of "no clear rule" language track the stimulus's
                  TRUE coordinability (own-copy match, form_consistency)?

  Q2 USE          Within a fixed cell, does a hedged trial go SAFE more often?
                  (Near-tautological on its own -- declining to play and declining
                  to claim a focal point are close to the same speech act. Reported,
                  but not treated as evidence by itself.)

  Q3 THE HARD ONE On ATTEMPT trials only -- where the model has already committed to
                  play, so the tautology is broken -- does hedging predict that this
                  particular trial went OFF the model's own modal form? That is the
                  trial the model would actually have lost. If expressed uncertainty
                  is real self-knowledge, hedged attempts should be off-mode more often.

Reuses the FROZEN Aug-13 lexicon and corpus verbatim. No new lexicon, no API calls.
"""
import csv, glob, os, math, random
from collections import Counter, defaultdict

EXP = ("/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/"
       "policy_specific_self_coordination_20260812_1401")
random.seed(20260825)

# ---- frozen per-trial lexicon corpus (Aug-13) ------------------------------
corpus = list(csv.DictReader(open(os.path.join(EXP, "reasoning_traces/trace_corpus.csv"))))

# ---- ground truth per (actor, stimulus) ------------------------------------
truth = {}
for r in csv.DictReader(open(os.path.join(EXP, "data/attempt_rates.csv"))):
    truth[(r["model"], r["stimulus"])] = dict(
        self_match=float(r["true_self_match"]),
        fc=float(r["form_consistency"]),
        salience=float(r["salience"]))

# ---- Stage C rows, to recover the identity chosen on each ATTEMPT ----------
stage_c = []
for f in glob.glob(os.path.join(EXP, "data/stageC_*.csv")):
    stage_c += [r for r in csv.DictReader(open(f))
                if r.get("included_in_analysis") in ("True", "1", "true")]

# modal identity per (actor, stimulus), from the Stage A ground truth run
modal = {}
counts = defaultdict(Counter)
for f in glob.glob(os.path.join(EXP, "data/stageA_*.csv")):
    for r in csv.DictReader(open(f)):
        if r.get("included_in_analysis") in ("True", "1", "true"):
            ident = r.get("parsed_choice_identity")
            if ident and ident != "NONE":
                counts[(r["actor_model"], r["stimulus"])][ident] += 1
for k, c in counts.items():
    modal[k] = c.most_common(1)[0][0]

# join corpus rows to Stage C by position within (actor, stimulus, payoff, decision)
sc_index = defaultdict(list)
for r in stage_c:
    sc_index[(r["actor_model"], r["stimulus"], r["safe_payoff"],
              r["participation_decision"])].append(r)
cur = Counter()
for row in corpus:
    key = (row["actor_model"], row["stimulus"], row["safe_payoff"],
           row["participation_decision"])
    i = cur[key]; cur[key] += 1
    lst = sc_index.get(key, [])
    row["_ident"] = lst[i].get("parsed_choice_identity") if i < len(lst) else None

def boot_ci(vals, b=4000):
    if not vals: return (float("nan"),) * 2
    n = len(vals); d = sorted(sum(random.choice(vals) for _ in range(n)) / n
                              for _ in range(b))
    return d[int(.025 * b)], d[int(.975 * b)]

def pearson(x, y):
    n = len(x); mx = sum(x)/n; my = sum(y)/n
    num = sum((a-mx)*(b-my) for a, b in zip(x, y))
    den = (sum((a-mx)**2 for a in x) * sum((b-my)**2 for b in y)) ** .5
    return num/den if den else float("nan")

LBL = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
H = "hedge_no_rule"
S = "asserts_salient"
hit = lambda r, k: r[k] in ("1", "True", "true", "1.0")

# ============================================================== Q1 ==========
print("=" * 104)
print("Q1  IS THE 'NO CLEAR RULE' LANGUAGE CALIBRATED TO THE ACTUAL RULE?")
print("=" * 104)
print("hedge rate computed on ATTEMPT trials only, so it is not just a restatement")
print("of a decision to decline.\n")
print(f"{'actor':14s}{'stimulus':17s}{'self_match':>11}{'form_cons':>10}"
      f"{'hedge|ATT':>11}{'hedge|SAFE':>11}{'asserts|ATT':>12}{'n_ATT':>7}")
pts = []
for (actor, stim), t in sorted(truth.items()):
    sub = [r for r in corpus if r["actor_model"] == actor and r["stimulus"] == stim]
    att = [r for r in sub if r["participation_decision"] == "ATTEMPT"]
    saf = [r for r in sub if r["participation_decision"] == "SAFE"]
    if len(att) < 10: continue
    h_a = sum(hit(r, H) for r in att) / len(att)
    h_s = sum(hit(r, H) for r in saf) / len(saf) if saf else float("nan")
    a_a = sum(hit(r, S) for r in att) / len(att)
    pts.append((t["self_match"], t["fc"], h_a, a_a))
    print(f"{LBL[actor]:14s}{stim:17s}{t['self_match']:>11.3f}{t['fc']:>10.3f}"
          f"{h_a:>11.3f}{h_s:>11.3f}{a_a:>12.3f}{len(att):>7}")

sm = [p[0] for p in pts]; fc = [p[1] for p in pts]
ha = [p[2] for p in pts]; aa = [p[3] for p in pts]
print(f"\n  corr(hedge|ATTEMPT , true self-match)   = {pearson(ha, sm):+.3f}"
      "     negative = calibrated")
print(f"  corr(hedge|ATTEMPT , form_consistency)  = {pearson(ha, fc):+.3f}")
print(f"  corr(asserts|ATTEMPT, true self-match)  = {pearson(aa, sm):+.3f}"
      "     positive = calibrated")

# ============================================================== Q2 ==========
print()
print("=" * 104)
print("Q2  WITHIN A FIXED CELL, DOES A HEDGED TRIAL GO SAFE?  (near-tautological)")
print("=" * 104)
tot = Counter()
for r in corpus:
    tot[(hit(r, H), r["participation_decision"] == "SAFE")] += 1
n_h = tot[(True, True)] + tot[(True, False)]
n_n = tot[(False, True)] + tot[(False, False)]
print(f"  P(SAFE | hedged)     = {tot[(True, True)]/n_h:.3f}   (n = {n_h})")
print(f"  P(SAFE | not hedged) = {tot[(False, True)]/n_n:.3f}   (n = {n_n})")
print("  -> the association is huge, and uninformative: on a SAFE trial the model is")
print("     explaining why it declined, so 'no clear rule' IS the decision restated.")

# ============================================================== Q3 ==========
print()
print("=" * 104)
print("Q3  ON ATTEMPT TRIALS, DOES HEDGING PREDICT GOING OFF THE MODEL'S OWN MODAL FORM?")
print("=" * 104)
print("Committed to play in both arms, so the tautology is broken. An off-mode pick is")
print("the trial that would actually have failed to coordinate.\n")
print(f"{'actor':14s}{'stimulus':17s}{'offmode|hedge':>15}{'offmode|no':>12}"
      f"{'diff':>9}{'n_h':>6}{'n_n':>6}")
pooled = {True: [], False: []}
for (actor, stim), t in sorted(truth.items()):
    m = modal.get((actor, stim))
    if not m: continue
    att = [r for r in corpus
           if r["actor_model"] == actor and r["stimulus"] == stim
           and r["participation_decision"] == "ATTEMPT" and r["_ident"]
           and r["_ident"] != "NONE"]
    if len(att) < 20: continue
    g = {True: [], False: []}
    for r in att:
        g[hit(r, H)].append(0 if r["_ident"] == m else 1)
    if len(g[True]) < 5 or len(g[False]) < 5: continue
    ph, pn = sum(g[True])/len(g[True]), sum(g[False])/len(g[False])
    pooled[True] += g[True]; pooled[False] += g[False]
    print(f"{LBL[actor]:14s}{stim:17s}{ph:>15.3f}{pn:>12.3f}{ph-pn:>+9.3f}"
          f"{len(g[True]):>6}{len(g[False]):>6}")

if not pooled[True]:
    print("  *** NO HEDGED ATTEMPT TRIALS EXIST. Q3 cannot be computed --")
    print("      and that emptiness is the result, not a limitation. ***")
    raise SystemExit
ph = sum(pooled[True])/len(pooled[True])
pn = sum(pooled[False])/len(pooled[False])
lo_h, hi_h = boot_ci(pooled[True]); lo_n, hi_n = boot_ci(pooled[False])
diff = [1]*0
# bootstrap the difference directly
db = sorted((sum(random.choice(pooled[True]) for _ in range(len(pooled[True])))/len(pooled[True])
             - sum(random.choice(pooled[False]) for _ in range(len(pooled[False])))/len(pooled[False]))
            for _ in range(4000))
print(f"\n  POOLED  off-mode | hedged      = {ph:.3f}  [{lo_h:.3f}, {hi_h:.3f}]  n = {len(pooled[True])}")
print(f"          off-mode | not hedged  = {pn:.3f}  [{lo_n:.3f}, {hi_n:.3f}]  n = {len(pooled[False])}")
print(f"          difference             = {ph-pn:+.3f}  [{db[100]:+.3f}, {db[3900]:+.3f}]")
print("\n  A positive, CI-excluding-zero difference = expressed uncertainty is real")
print("  self-knowledge. A difference at zero = the hedge is decoration.")
