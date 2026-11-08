# Study 1-HP v3 — single-focal-model confirmatory replication

**DESIGN AND SIMULATION ONLY. Nothing run, no stimuli generated, no API calls.**
Supersedes `DESIGN_v2_LOWCOST.md`. 2026-09-05.

## 0. Headline, including the part you will not like

**Recommended: 13,128 calls, $205–301 — a 21% cut** from the two-model design,
with 24 pairs and power **0.998 / 0.892 / 0.614** at mu = 0.145 / 0.10 / 0.07.

**The $150–200 target is not reachable without breaking one of your own
constraints.** Dropping to one focal model saves far less than half, because the
binding constraint is independent pair yield and a single model needs a **1.7x
larger battery** to reach the same pair count. Section 3 shows this quantitatively.
The cheapest design that still clears 20 pairs with unchanged thresholds is
**$172–252** (variant D). Anything below that buys the cost reduction with pair
count or matching quality.

## 1. Claim — now explicitly within-model

> Does **GPT-5.5** preferentially attempt coordination on stimuli where
> independent copies of GPT-5.5 actually coordinate more reliably, even when those
> stimuli are matched on externally observable coordinability?

Not a claim about cross-model generality. Claude Opus 5 appears only as the
external auditor and salience rater. Cross-model replication is a later extension.
No introspection language.

**The self-stated confidence arm is deleted entirely** — not in original Study 1,
not needed for matching, not needed for the primary claim. Not replaced.

## 2. Focal model: GPT-5.5

| criterion | GPT-5.5 | Claude Opus 5 |
|---|---|---|
| Study 1 pair effect | **+0.175** (n=3: .042, .183, .300) | +0.100 (n=2: .117, .083) |
| battery SD, auditor | **0.0724** | 0.0494 |
| auditor matching window \|d_aud\| | **0.0253** | 0.0173 |
| generation trend (ladder) | **monotone**: GPT-5 +0.008 → 5.4 +0.081 → 5.5 +0.175, p<0.0001 | flat/noisy: 4.7 +0.063, 4.8 +0.026, Opus 5 +0.100 |

GPT-5.5 has the larger effect to replicate, a **47% wider auditor matching
window** (so more admissible pairs per stimulus), and a monotone generation trend
supplying a genuine prior. Claude wins only on cost predictability — **GPT-5.5
pricing is still unverified and must be confirmed before launch**, which is the one
real risk this choice carries.

## 3. Battery size — do NOT halve it

Single-focal yield, simulated at GPT parameters (A2 depth 30, Stage B depth 20):

| stimuli | eligible | independent pairs (p10–p90) | P(≥20) | P(≥24) |
|---|---|---|---|---|
| 72 | 70 | 18 (15–22) | **0.34** | 0.04 |
| 90 | 109 | 24 (21–28) | 0.96 | 0.58 |
| **110** | 165 | 31 (27–34) | **1.00** | 0.99 |
| **120** | ~195 | ~34 | **1.00** | **1.00** |
| 130 | 229 | 38 (33–42) | 1.00 | 1.00 |

Conservative empirical anchor — Opus 4.6, 45 stimuli, one focal model, **8
observed** independent pairs = 0.178 per stimulus. That anchor comes from a
Claude-family model whose auditor window is 32% narrower, so it **understates**
GPT yield:

| stimuli | conservative anchor | simulated |
|---|---|---|
| 90 | 16.0 | 24.2 |
| 110 | 19.6 | 30.8 |
| **120** | **21.4** | ~34 |
| 130 | 23.1 | 37.8 |

On the conservative anchor, **113 stimuli are needed for ≥20 pairs and 135 for
≥24**. **72 stimuli would fail: P(≥20) = 0.34.**

**Chosen: 120 stimuli.** Conservative anchor gives 21.4 pairs (clears the floor),
simulation gives ~34. Composition: 15 original Study 1 + 30 frozen expansion + **75
new** under the expansion battery's frozen rules (families pitting two defensible
conventions against each other, written in one batch, frozen before any Stage A
call, no stimulus designed because a named model was observed to prefer a named
feature).

## 4. Sampling plan

| stage | shape | depth | purpose |
|---|---|---|---|
| **A1 screen** | 120 stimuli, focal only | **15** | drop only; never enters a pair estimate |
| retention rule | top 40% / bottom 40% of screened self-match; drop middle 20% | — | 96 cells retained |
| **A2 confirm** | 96 retained, **FRESH** draws | **30** | **selection uses A2 alone** |
| **B auditor** | 96 retained, Claude Opus 5 predicts GPT-5.5 | **20** | public baseline |
| **B salience** | 96 retained, **1 non-focal rater** | **20** | public baseline |
| **Stage C** | 24 pairs × 2 × {3,5,7,9} | **24** | ATTEMPT vs SAFE |

**Near-boundary top-up, capped.** A cell whose A2 self-match is within ±0.05 of
the eligibility boundary, or whose auditor difference to its candidate partner is
within ±0.005 of the 0.0253 window, gets **one** top-up of 20 draws. Maximum per
cell ever: 15 + 30 + 20 = **65**. Decided from A2 alone, before any Stage C call.

**Salience rater — a principled simplification, not a cost cut.** Study 1 pooled
both models as raters. With one focal model, using **only the non-focal model**
means the focal model never rates the stimuli it will later be tested on, which
removes a confound the two-model design had to live with. The 2-rater variant is
costed as variant A if you prefer strict fidelity (+$30–44).

**Screening/confirmation separation.** A1 only drops; fresh A2 draws alone
determine eligibility; the pair table is SHA-256 hashed and frozen before the
first Stage C call, and Stage C refuses to run against a non-matching hash. Stage C
behaviour never feeds back into selection.

## 5. Unchanged from Study 1

Eligibility `|z_true| >= 0.75`, `|z_salience| <= 0.35`, `|z_auditor| <= 0.35`, all
on that model's own battery SD. No |t| cutoff. Non-reuse of stimuli. Fallback
stimuli fully eligible, with `form_consistency`, `fresh_classification` and
`pair_kind` recorded for robustness only and **never** as a post-hoc exclusion.
Payoff grid **{3,5,7,9}**. Canonical Stage A prompt `sha8 3003ae1b`, asserted at
import. Primary unit is the pair.

## 6. Power (single focal, grid {3,5,7,9}, tau = 0.0903)

| Stage C n/cell | pairs | mu=.145 | mu=.10 | mu=.07 |
|---|---|---|---|---|
| 20 | 15 | 0.890 | 0.680 | 0.408 |
| 20 | 20 | 0.966 | 0.820 | 0.546 |
| 20 | 24 | 0.992 | 0.858 | 0.626 |
| 20 | 30 | 1.000 | 0.950 | 0.680 |
| **24** | 15 | 0.960 | 0.716 | 0.508 |
| **24** | **20** | 0.986 | **0.820** | 0.556 |
| **24** | **24** | **0.998** | **0.892** | 0.614 |
| **24** | 30 | 1.000 | 0.920 | 0.722 |
| 30 | 20 | 1.000 | 0.882 | 0.640 |
| 30 | 24 | 0.996 | 0.932 | 0.708 |

**Stage C depth 24** clears 0.80 at mu = 0.10 from 20 pairs onward. Dropping to 20
costs ~0.03 and saves 768 calls; that is variant D.

## 7. Cost

| component | calls | $ all-in |
|---|---|---|
| Stage A1 screen (focal) | 1,800 | $28–41 |
| Stage A2 confirm (focal, fresh) | 2,880 | $45–66 |
| Stage B auditor (non-focal rates focal) | 1,920 | $30–44 |
| Stage B salience (1 non-focal rater) | 1,920 | $30–44 |
| Stage C (focal) | 4,608 | $72–106 |
| **TOTAL** | **13,128** | **$205–301** |

Phase 1 (gated) 8,520 calls, $133–195. Phase 2 4,608 calls, $72–106.

| variant | pairs | stim | calls | $ all-in | vs 16,568 | power @ mu=.10 |
|---|---|---|---|---|---|---|
| A — 2 salience raters | 24 | 120 | 15,048 | $235–345 | −9% | 0.892 |
| **B — RECOMMENDED** | **24** | **120** | **13,128** | **$205–301** | **−21%** | **0.892** |
| C — 20-pair floor | 20 | 110 | 11,650 | $182–267 | −30% | 0.820 |
| D — C with Stage C 20/cell | 20 | 110 | 11,010 | $172–252 | −34% | 0.820 |

## 8. Why one focal model saves only ~21%

Removing the second model deletes its Stage A, Stage C and focal-specific Stage B
— but pair yield is per-model, so the battery must grow from 72 to 120 stimuli to
recover the pair count. Stage A and Stage B costs scale with the battery, and they
are 65% of Phase 1. Net effect: **calls fall 21%, not 50%.**

Reaching $150–200 would require one of:

* **fewer than 20 pairs** — power falls to 0.68–0.72 at mu = 0.10 (15 pairs);
* **a smaller battery** — 90 stimuli gives P(≥24) = 0.58 and, on the conservative
  anchor, only 16 pairs;
* **dropping the salience arm** — removes a public baseline the claim depends on;
* **dropping safe = 3 and 5** — changes the decision task and breaks comparability.

Each is explicitly forbidden by your own constraints, so **I am not recommending
any of them.** Variant D at **$172–252** is the cheapest design I would actually
trust, and it sits just above your target.

## 9. Analyses

**Primary** — pair-constrained hierarchical model (headline); paired sign-flip
permutation, exact at N ≤ 12 else 20,000 sampled; proportion of pairs in the
predicted direction with a binomial interval.

**Secondary robustness** — auditor prediction, generic salience, policy-specific
residual, fallback status / form consistency, payoff interaction,
leave-one-pair-out, and A2-vs-top-up shrinkage. Study 1's naive collinear
regression is reported only as a labelled diagnostic. **No new exploratory
measures before the confirmatory replication is complete.**

## 10. GO / NO-GO

**GO to Stage C iff Phase 1 yields ≥ 20 independent approved pairs** under the
unchanged selector, with the pair table frozen and hashed.

**NO-GO** → expand the battery and re-run pairing on the enlarged candidate set,
or report the yield as a finding about the battery. **Never** loosen a threshold,
reuse a stimulus, or drop a Stage B control to manufacture pairs.

**Success** — mu_delta > 0 with a credible interval excluding 0, permutation
p ≤ 0.05, and > 60% of pairs in the predicted direction. Reported as a
**within-GPT-5.5** replication.

**Null** — report the bound. At 24 pairs and Stage C 24/cell the design has 0.892
power at mu = 0.10, so a null bounds the average pair effect below roughly **0.10**
on the risk-difference scale, and below ~0.07 with 60% confidence.
