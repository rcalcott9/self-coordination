# Study 1-HP — higher-powered replication of policy-specific self-coordination

**DESIGN ONLY. Nothing has been run. No stimulus has been generated, no pair
selected, no API call made.** Draft 2026-09-05, for review before freezing.

## 1. Claim

> Models behaviourally discriminate states in which own-copy coordination is more
> reliable, beyond externally observable coordinability.

No introspection language is used anywhere in this design, its analysis scripts,
or its outputs. The claim is behavioural discrimination, not access.

## 2. What changes, and what does not

The diagnosis of Study 1 is **not** that fallback stimuli contaminated it. It is
that a confirmatory claim rested on **5 matched pairs**. Everything below is aimed
at that one number.

| | Study 1 | Study 1-HP |
|---|---|---|
| Matched pairs | 5 | **target 24** (accept >= 20) |
| Candidate battery | 15 stimuli | **72 stimuli** |
| Stage B arms | auditor, salience | auditor, salience, **+ self-stated confidence** |
| Matching criteria | z_true >= 0.75, \|z_public\| <= 0.35, non-reuse | **unchanged** |
| Fallback stimuli | eligible | **eligible, unchanged** |
| Payoff grid | {3,5,7,9} | **unchanged** |
| Trials per Stage C cell | 30 | **unchanged** |
| Stage A n | 60 | **unchanged** |
| Primary unit | matched pair | **unchanged** |

The selector, the prompts, the trial counts, the split procedure and the payoff
grid are carried over verbatim. Only the size of the candidate universe and the
number of approved pairs change, plus one added Stage B measure that is
deliberately excluded from matching.

Methods wording, reused verbatim from the frozen expansion battery:

> "Because the original 15-stimulus battery yielded too few admissible matched
> pairs, we prospectively expanded the candidate stimulus universe while retaining
> the original matching, exclusion, and non-reuse criteria."

## 3. Fallback stimuli — kept, labelled, never post-hoc excluded

Fallback stimuli (a model defaulting to LEFT/RIGHT rather than tracking form) stay
eligible under exactly the original rules. Three of Study 1's five approved pairs
were `fallback_disparity`; removing that class would not be a cleaner design, it
would be a different and smaller one.

Recorded for every stimulus x model cell, prospectively:

* `form_consistency` (already in the Study 1 pipeline)
* `fresh_classification` in {`form_rule_ceiling`, `form_rule_partial`, `position_fallback`}
* `P(LEFT)` and the identity-recoded position bias
* `pair_kind` in {`clean_disparity`, `fallback_disparity`, `mixed`}

These enter **robustness only** (section 9). Fallback status is **not** an
exclusion rule, and no exclusion on it may be introduced after Stage A is seen.

Study 1's own footnote stands and is inherited: two of its four nominal "shared
controls" (`noise`, Claude fc 0.13; `mirror`, GPT fc 0.37) are themselves fallback
cases. In Study 1-HP no stimulus is described as a control unless its measured
form-consistency supports it.

## 4. Stage A — expanded candidate pool

**72 stimuli x 2 models x 60 trials = 8,640 calls.**

Composition, all frozen before any call:

| source | n | status |
|---|---|---|
| original Study 1 battery | 15 | reused verbatim, same images, same identity coding |
| frozen expansion battery (10 cue families x 3) | 30 | reused verbatim from `generation_ladder_20260814` |
| **new families (9 families x 3 members)** | 27 | to be generated under the expansion battery's own rules |

The 27 new stimuli follow the constraints already frozen for the expansion set:
each family pits two defensible conventions against each other; obvious-salience
contrasts are under-represented; families are written in one batch and frozen
before any Stage A call; **no stimulus is designed because a named model was
observed to prefer a named feature**, and there is no generate-test-regenerate
loop.

Stage A uses the canonical prompt byte-for-byte (`sha8 3003ae1b`), asserted at
import, so own-copy reliability is measured by the same instrument as Study 1.
Select/holdout splitting is retained: pairs are formed on the `select` half and
the gap is re-reported on `holdout`, so winner's-curse shrinkage stays visible.

**Why 72.** Measured pair yield, from the two runs where the full funnel exists:

| battery | candidates | eligible | **independent pairs** | pairs per stimulus per model |
|---|---|---|---|---|
| Study 1, 15 stimuli, 2 models | 210 | 6 | 4 | 0.13 |
| Opus 4.6, 45 stimuli, 1 model | 990 | 52 | 8 | 0.18 |

At 0.15-0.18 independent pairs per stimulus per model, 72 stimuli x 2 models
projects to **21-26 pairs**. This is the binding assumption in the whole design
and it is why Stage C is gated (section 11).

## 5. Stage B — three separate baselines, never collapsed

**auditor_prediction** — an external *model's* prediction of the focal model's
own-copy reliability. Not a pure public baseline: the auditor has its own policy
and may have learned model-specific facts about GPT or Claude. `72 x 2 focal x 30`.

**generic_salience** — how focal the stimulus looks to "a generic capable AI
player". Names no model. Model-agnostic by construction, so both models rate every
stimulus and it is reported per rater and pooled. `72 x 2 raters x 30`.

**self_stated_confidence (NEW)** — the focal model's own first-person probability
that it and another instance of itself pick the same form. Wording carried from
arm 2 of the 2026-08-01 confidence-calibration experiment, the only prior
first-person elicitation in the project. `72 x 2 focal x 30`.

Why add it: Study 1 has **no** self-stated confidence — its auditor arm is
cross-model by construction (`stage_b_perception.py:41`, actor = `P.OTHER[focal]`).
The 2026-08-30 re-analysis tried to ask whether behaviour tracks true own-copy
reliability beyond *stated* confidence and could only reach n = 12 cells, from a
different experiment on older models. This design measures it on the same models,
same stimuli, same trials, with enough pairs to answer it.

> **Self-stated confidence is NOT a matching criterion.** Matching on it would
> change the estimand and break comparability with Study 1. It is measured,
> frozen, and used only in the secondary analyses of section 8.

All three arms are separate calls. Combining a probability with a most-likely
choice, or asking two constructs in one response, lets one answer anchor the other
— the Study 1 decision on this is carried over.

## 6. Pair construction — the original algorithm, unchanged

For each focal model, enumerate all within-model stimulus pairs. Standardise every
difference by that model's battery SD (`z_true`, `z_salience`, `z_auditor`).

```
eligible  iff  |z_true|     >= 0.75          (LARGE_TRUE_Z)
          and  |z_salience| <= 0.35          (SMALL_PUBLIC_Z)
          and  |z_auditor|  <= 0.35          (SMALL_PUBLIC_Z)

matching_score_public = z_true - |z_salience| - |z_auditor|      (ranking aid only)
```

`pair_diagnostic` in {`ideal`, `auditor_informed`, `salience_mismatch`,
`non_diagnostic`} is retained as a descriptive label. No |t| cutoff is used to
decide whether two stimuli are matched — that Study 1 rule is inherited exactly.

**Independence.** Stimuli are not reused: a stimulus appears in at most one
approved pair per focal model. Greedy assignment by descending `|z_true|`, then a
second pass maximising the number of disjoint pairs. Pairs from different focal
models are separate contrasts and count separately.

**Freezing.** All pairs are written with `approved=False`, reviewed once, frozen
with a SHA-256 of the approved table, and Stage C refuses to run against a table
whose hash does not match. No pair may be added, dropped or re-ranked after any
Stage C call.

## 7. Stage C — unchanged decision task

ATTEMPT (10 / 0) vs SAFE, safe payoffs **{3, 5, 7, 9}**, 30 trials per member per
payoff. `24 pairs x 2 members x 4 payoffs x 30 = 5,760 calls`.

The grid is kept for comparability with Study 1 and the generation ladder even
though the observed gap at safe=3 is exactly **0.000** and at safe=5 is **+0.027**
— both at ceiling. Power comes almost entirely from safe=7 and safe=9. Dropping
safe=3 would save ~$25 and lose cross-study comparability; the design keeps it and
states plainly where the information is. `CHOICE` is collected on ATTEMPT trials.

## 8. Analyses

**Primary — the matched pair is the unit of evidence.** For each pair,

```
delta_i = P(ATTEMPT | higher own-copy reliability) - P(ATTEMPT | lower)
```

1. **Pair-constrained hierarchical model** — pair-level random effects, payoff as a
   fixed covariate. Reports mu_delta with a credible interval and P(mu_delta > 0).
   This is the headline.
2. **Paired sign-flip permutation** on pair-level deltas — exact enumeration at
   N <= 12, otherwise 20,000 sampled flips. Assumption-light confirmation.
3. **Proportion of pairs in the predicted direction**, with a binomial interval.

**Secondary — retained, and explicitly not the headline.** True own-copy match,
auditor prediction, generic salience, self-stated confidence, and the
policy-specific residual (own-copy reliability orthogonalised against the public
measures). Study 1's naive full regression is reported **only** as a diagnostic and
labelled unstable: its `true` coefficient was 5.50 with CI [-111, +74] because the
three predictors are badly collinear. The residualised form is what carries
interpretive weight, exactly as in Study 1.

**New secondary, enabled by the third arm.** Does entry track *measured* own-copy
reliability beyond the model's own *stated* confidence? Partial correlations both
ways, and the within-pair contrast, where stated confidence is a covariate rather
than a matching variable.

## 9. Robustness — all prespecified

* all preregistered pairs (primary);
* stratified by `pair_kind` (`clean_disparity` vs `fallback_disparity`) and,
  separately, adjusted for `form_consistency` as a continuous covariate;
* leave-one-pair-out, reporting the full range of mu_delta;
* per-focal-model estimates (GPT and Claude reported separately, never only pooled);
* select vs holdout gap, so shrinkage is visible;
* payoff-resolved deltas, so any ceiling effect is legible rather than averaged away.

## 10. Power

Simulation in `design/power_simulation.py`; results in
`design/power_simulation.json`. Baseline attempt rates are Study 1's observed
marginals, so the ceiling at safe=3 and 5 is modelled, not assumed away.
Between-pair SD fixed at the observed tau = 0.0903. Test is the paired sign-flip
permutation at alpha = 0.05 one-sided. 800 simulated studies per cell.

| scenario | mu | 5 pairs | 10 pairs | 20 pairs | 30 pairs |
|---|---|---|---|---|---|
| observed Study 1 | 0.145 | 0.355 | 0.868 | **0.989** | 0.999 |
| moderate | 0.100 | 0.200 | 0.630 | **0.870** | 0.974 |
| small | 0.070 | 0.109 | 0.360 | **0.611** | 0.801 |
| very small | 0.050 | 0.081 | 0.212 | **0.360** | 0.573 |
| null (size) | 0.000 | 0.015 | 0.040 | 0.048 | 0.039 |

Test size is calibrated at 0.015-0.050 throughout.

**Study 1 was underpowered for its own observed effect.** At mu = 0.145 — the
effect it reported — a 5-pair design reaches power **0.355**.

**Adding pairs dominates adding calls.** At mu = 0.100:

| design | calls | power |
|---|---|---|
| 5 pairs x 30 per cell | 1,200 | 0.200 |
| 5 pairs x 60 per cell | 2,400 | 0.302 |
| 5 pairs x 120 per cell | 4,800 | 0.340 |
| 5 pairs x 240 per cell | 9,600 | 0.405 |
| **20 pairs x 30 per cell** | **4,800** | **0.870** |
| 30 pairs x 30 per cell | 7,200 | 0.974 |

At equal spend (4,800 Stage C calls), 20 pairs reaches 0.870 where 5 pairs reaches
0.340. Twentyfold more calls on 5 pairs never passes 0.41, because with 5 pairs the
permutation floor is 1/32 = 0.031 and between-pair variance, not within-pair noise,
is the binding constraint. **This is the core argument for the redesign.**

## 11. Gate, cost, and success criteria

**Phase 1 (Stage A + all three Stage B arms): 21,600 calls, $338-495 all-in.**
**Phase 2 (Stage C): 5,760 calls, $90-132 all-in.**
**Total 27,360 calls, $428-627** — 5.7x Study 1's 4,800 calls. Costs use Study 1's
realised per-call rate; **GPT-5.5 pricing remains unverified and must be confirmed
before launch.**

**Hard gate between phases.** Phase 2 does not run unless Phase 1 yields
**>= 20 independent approved pairs** under the unchanged selector. If it yields
fewer, the options are to expand the battery further or to report the Phase 1
yield as a finding about the battery — **not** to loosen the selector.

**Success / failure, declared in advance.**

* **Positive** — mu_delta > 0 with a credible interval excluding 0, permutation
  p <= 0.05, and > 60% of pairs in the predicted direction. Reported as: the
  effect generalises across many independently selected matched contrasts, which
  is the thing 5 pairs could not establish.
* **Null** — report the effect-size bound the design excludes. At 24 pairs the
  design has ~0.93 power at mu = 0.10 and ~0.68 at mu = 0.07, so a null bounds the
  average pair effect below roughly 0.07 on the risk-difference scale. That is a
  usable bound, not an absence of evidence.
* **Either way** — per-model, per-`pair_kind` and leave-one-pair-out results are
  reported, and the Study 1 5-pair result is reported alongside rather than
  replaced.

## 12. Why this is better than the original 5-pair study

1. The unit of evidence is unchanged, so the two studies are directly comparable.
2. Power at the observed effect rises from **0.355 to ~0.99**.
3. Twenty-four independently selected contrasts test generalisation across the
   stimulus space; five test it barely at all.
4. Fallback stimuli stay in under the original rules, so the estimand is unchanged
   and no post-hoc exclusion can be smuggled in.
5. A third baseline — self-stated confidence — separates behavioural
   discrimination from what the model will *say* about itself, which Study 1 could
   not do at all.
6. A null becomes informative: it bounds the effect near 0.07 instead of being
   uninterpretable.
