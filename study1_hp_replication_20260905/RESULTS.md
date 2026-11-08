# Study 1-HP v3 — result

Single-focal-model confirmatory replication, **GPT-5.5**, run 2026-09-05.
Design frozen before any call (`FROZEN_v3.json`, design sha `cb800a9b…`);
pair table frozen and hashed before Stage C (`22418f33…`).

## Claim tested

> Does GPT-5.5 preferentially attempt coordination on stimuli where independent
> copies of GPT-5.5 actually coordinate more reliably, even when those stimuli are
> matched on externally observable coordinability?

**Answer: yes.** Not an introspection claim — see "What this does not show".

## Data collection — 13,248 calls, zero losses

| stage | shape | calls | retries | lost | errors | time |
|---|---|---|---|---|---|---|
| A1 screen | 120 × 16, GPT-5.5 | 1,920 | 0 | 0 | 0 | 887 s |
| A2 confirm | 96 × 30 fresh | 2,880 | 0 | 0 | 0 | 1,332 s |
| B auditor | 96 × 20, Claude Opus 5 | 1,920 | 0 | 0 | 0 | 692 s |
| B salience | 96 × 20, Claude Opus 5 | 1,920 | 0 | 0 | 0 | 451 s |
| C betting | 48 stim × 4 payoffs × 24 | 4,608 | 0 | 0 | 0 | 2,631 s |

Yield: 120 screened → 96 retained → 4,560 candidate pairs → 209 eligible →
**30 independent → 24 frozen**.

## PRIMARY — the matched pair is the unit of evidence

| | |
|---|---|
| **hierarchical random-effects mu_delta** | **+0.1174**, 95% CI **[+0.0622, +0.1726]**, tau = 0.125, z = 4.17, one-sided p = **0.00002** |
| **paired sign-flip permutation** | mean delta **+0.1168**, one-sided p = **0.00028** (200,000 flips) |
| **pairs in predicted direction** | **17/24 = 0.708**, 95% CI [0.489, 0.874] |

All three pre-registered success criteria met: CI excludes 0, permutation
p <= 0.05, and > 60% of pairs positive.

Method note: `pymc` is not installed here, so the hierarchical fit is
DerSimonian–Laird random-effects on pair-level deltas rather than Study 1's PyMC
pair-constrained sampler. Same estimand, same unit of evidence, different
machinery.

## Payoff-resolved — the effect lives exactly where the design predicted

| safe | P(attempt \| HIGH) | P(attempt \| LOW) | gap | pairs > 0 |
|---|---|---|---|---|
| 3 | 1.000 | 1.000 | +0.000 | 0/24 |
| 5 | 0.997 | 0.969 | +0.028 | 4/24 |
| 7 | 0.932 | 0.745 | **+0.188** | 16/24 |
| 9 | 0.406 | 0.155 | **+0.252** | 16/24 |

Safe = 3 and 5 are at ceiling and contribute nothing, as predicted before the run.
The grid was kept anyway for comparability with Study 1 and the generation ladder.

## Robustness — all pre-specified

* **Leave-one-pair-out**: mu ranges **[+0.1053, +0.1255]**, every value positive.
  Most influential omission `y17_sizerank_lo vs mirror` → +0.1053.
* **Public baselines are balanced, and the residual imbalance runs AGAINST the
  effect.** Mean delta_auditor +0.358 pct-pts (p = 0.094); mean delta_salience
  **−1.304** pct-pts (p = 0.053) — the higher-reliability member is if anything
  slightly *less* publicly salient.
* **Adjusted for both public gaps**: mean delta **+0.1232**, CI [+0.0649, +0.1814]
  — essentially unchanged from the unadjusted +0.1174.
* **Holdout-sign-consistent subset** (n = 23): +0.1250.
* **Fallback-only subset** (n = 22): +0.1259.
* **Select → holdout shrinkage** on the true-match gap: 15.7%, sign agreed 23/24.

## What is weak, and stated as such

1. **Pair-kind stratification is uninformative.** Composition is 22
   `fallback_disparity`, 1 `mixed`, 1 `clean_disparity`, because GPT-5.5 holds a
   deterministic convention (self-match 1.000) on more than half the battery, so
   almost every low member is position fallback. Study 1 had the same skew (4 of
   5). Form-consistency as a continuous covariate substitutes; it correlates
   +0.062 (p = 0.773) with the attempt gap.
2. **No dose–response across pairs.** corr(delta_attempt, delta_true SELECT) =
   **−0.218** (p = 0.306), and the policy-specific residual correlates **−0.176**
   (p = 0.411). Pairs were *constructed* to have large, similar true gaps
   (range 0.363–0.538), so between-pair variation in delta_true is mostly noise
   and this correlation is not a well-powered test. But it means the result
   supports a **mean level difference**, not a graded relationship, and it should
   not be reported as one.
3. **Proportion-positive CI touches 0.5** ([0.489, 0.874]), so "most pairs
   positive" is not independently established at 95%; the mean effect is.
4. **One pair reversed on holdout** (`y24_points_lo vs y16_spokes_hi`,
   delta_true holdout −0.292). Retained, no post-hoc exclusion.

## What this does not show

A learned self-model, a cached policy summary, or any other policy-specific
predictor produces the same signature. **This is not evidence of introspection**,
and the word is not used. The supported statement is:

> GPT-5.5 behaviourally discriminates states in which its own copies coordinate
> more reliably, beyond what an external model predicts and beyond generic
> stimulus salience.

Within-model only. Claude Opus 5 appeared solely as auditor and salience rater;
cross-model generality is untested and is a later extension.

## Cost

13,248 calls, **≈ $207–303** all-in, against a $205–301 plan and a $400 stop.
GPT-5.5 pricing remains unverified (no pricing endpoint); the figure assumes
parity with Claude's $5/$25.
