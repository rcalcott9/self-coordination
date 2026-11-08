# ANALYSIS SPEC — Stage 1 policy convergence

T5 (analysis-engineer). Proposed; the lead owns acceptance. This document specifies every
Stage 1 metric and analysis with exact formulas, and argues the determinism/similarity
separation that MASTER_DESIGN S5 makes mandatory.

Names and formulas follow `DATA_DICTIONARY.md` exactly. Where the dictionary marks a
statistic **TBD (T5)** this document supplies it; nothing here changes a frozen
definition.

Implementation: `convergence_metrics.py` (estimators), `run_stage1.py` (pipeline),
`synthetic_validation.py` (ground-truth validation). Validation results:
`synthetic_validation.md`. Worked run on existing data: `out/worked_run/SUMMARY.md`.
**No component makes API calls.**

---

## 1. Notation

For a model `m` and item `t` with `K = 4` canonical options:

| symbol | meaning |
|---|---|
| `n_i` | count of trials on which `m` chose canonical option `i` |
| `N = sum_i n_i` | valid trials in the cell (the n=48 floor, MASTER_DESIGN S5) |
| `p_i = n_i / N` | the empirical **policy** |
| `p~` | the **standardised** policy (S4.3) |
| `M_AB = sum_i p_A(i) p_B(i)` | expected agreement of one draw from each of A and B |
| `M_AA = sum_i p_A(i)^2` | plug-in self-match |
| `S(p) = 1 / sum_i p_i^2` | effective choice support, in [1, K] |

A **policy** is a distribution over canonical option identities. `display_position` is
recorded but never used to score coordination (DATA_DICTIONARY); it enters only the
position diagnostics of S3.

**Smoothing.** Any statistic requiring a nonlinear transform of the policy uses add-alpha
smoothing `p_i = (n_i + alpha) / (N + K*alpha)` with `alpha = 0.5` (Krichevsky-Trofimov),
applied once and uniformly. The raw count statistics — `modal_share`, `modal_margin`,
`within_model_match`, `cross_model_match` — are computed unsmoothed. Sensitivity to
alpha in {0.25, 0.5, 1.0} is reported for every headline number.

---

## 2. Data contract and integrity gates (pipeline stage 0)

One row per attempted trial, with the identity/provenance fields of DATA_DICTIONARY.
Gates, all applied before any metric is computed; every failure is recorded in
`integrity.json` with the affected cells, and is never silently repaired:

| gate | rule | rationale |
|---|---|---|
| `single_prompt_generation` | one distinct `prompt_hash` across the whole analysis set | threat 6 — never combine prompt generations |
| `expected_prompt_hash` | matches the frozen hash for the run | threat 6 |
| `checkpoint_requested_eq_returned` | `checkpoint_returned` contains `checkpoint_requested` on every row; violating rows dropped | DATA_DICTIONARY: "a mismatch stops the run" |
| duplicate trial | unique on `(item_id, trial, source_file)` | **trial, not `presentation_id`**: n=48 is two complete cycles of the 24 permutations, so each `presentation_id` legitimately appears twice. Keying on presentation would silently halve every cell. |
| parse / transport | `parse_ok and transport_ok`; all raw attempts preserved | DATA_DICTIONARY |
| n floor | `N >= 48`; cells below the floor are flagged, never re-weighted, never pooled up | MASTER_DESIGN S5 frozen floor |
| item in manifest | `item_id` present in the frozen battery manifest | threat 6 |

A cell that fails the n floor is **retained and flagged** rather than deleted, so the
report shows what was short; it is excluded from any headline estimate.

---

## 3. Per model x item metrics

Exactly the DATA_DICTIONARY list.

```
choice_distribution   (n_0, ..., n_{K-1})
modal_identity        argmax_i n_i, ties broken to the LOWEST canonical index
modal_share           max_i n_i / N
modal_margin          modal_share - runner_up_share
within_model_match    sum_i n_i (n_i - 1) / [N (N - 1)]          <- UNBIASED
effective_support     1 / sum_i p_i^2                             in [1, K]
entropy_bits          - sum_i p_i log2 p_i
n_live_options        #{ i : p_i >= 0.10 }                        (threat 3 diagnostic)
```

`within_model_match` uses the unbiased n_k(n_k-1) form because the two draws being
compared come from the SAME sample; the plug-in `sum p_i^2` is biased upward by ~1/N.
This is the estimator already in `LLM_Coordination/Name_game_experiment/targeted_common.py`
(`unbiased_match`) and this spec reuses it unchanged.

`effective_support` deliberately keeps the plug-in form, because it is defined as a
transform of the reported policy rather than as an estimate of a dyadic probability.
Where a near-unbiased read of the underlying support is needed — the determinism match of
S4.6 — the pipeline uses `support_target = 1 / within_model_match` instead, and says so.

### Position dependence (visual items)

```
position_counts        counts over DISPLAY position 0..K-1
position_modal_share   max position count / N                     (chance = 1/K = .25)
position_match         unbiased dyadic self-match over positions
form_consistency       1 - ( max_p h(p) - min_p h(p) )
                       h(p) = P(choose modal identity | modal identity displayed at slot p)
```

`form_consistency` is NaN unless the modal identity was displayed at all four slots. At
n=48 each canonical option occupies each slot exactly 12 times, so `h(p)` is quantised to
1/12 and `form_consistency` to 1/12 — the reason for the n=48 floor (threat 5). The full
conditional choice distribution by slot is retained alongside, not just the hit rate.

The worked run shows the quantisation directly: the 84 cells at n=24 take only multiples
of 1/6 (0.167, 0.333, 0.500, 0.667, 0.833, 1.000), while the 38 cells at n=48 also take
0.083, 0.417, 0.583 and 0.917. At n=24 a single trial moves `form_consistency` by 0.167,
which is why threat 5 says it cannot certify position invariance for a selected item.

The code domain has no screen geometry; `presentation_id` is the option-order seed and
the same machinery applies with "slot" meaning position in the presented option list.

---

## 4. Per model-pair x item metrics, and the determinism/similarity separation

### 4.0 The four dictionary metrics

```
modal_agreement    1 if modal_identity_A == modal_identity_B
cross_model_match  M_AB = sum_i p_A(i) p_B(i)
p_other_modal      p_A( modal_identity_B )   and   p_B( modal_identity_A )   [directed, both]
distribution_distance   see S4.1
```

**`cross_model_match` needs no small-sample correction and must not be given one.** The
two cells are independent samples, so `E[ ph_A(i) ph_B(i) ] = p_A(i) p_B(i)` exactly: the
plug-in is already unbiased. Applying the `n_k(n_k-1)` correction here — by analogy with
`within_model_match` — would introduce a bias, not remove one. Only the WITHIN term needs
it. This asymmetry is verified in `run_stage1.py --selftest`.

### 4.1 `distribution_distance`: Jensen-Shannon distance (chosen statistic)

**Primary:** `distribution_distance = sqrt( JSD(p_A, p_B) )`, JSD in bits,

```
JSD(P,Q) = H( (P+Q)/2 ) - 1/2 H(P) - 1/2 H(Q),     H in bits
```

with a Miller-Madow correction applied to each of the three entropy terms
(`H_MM = H_plugin + (Khat - 1)/(2N)`). Because the mixture term is estimated from
`N_A + N_B` draws and the two marginals from `N_A` and `N_B`, the net additive correction
is negative — it removes the upward small-sample bias that plug-in JSD carries. Clamped
to [0,1]. Measured at K=4, n=48, alpha=0.5, over 3000 draws:

| true JS distance | plug-in estimate (bias) | Miller-Madow (bias) |
|---|---|---|
| 0.0908 | 0.1549 (+0.064) | 0.0666 (-0.024) |
| 0.0517 | 0.1365 (+0.085) | 0.0540 (+0.002) |
| 0.0000 (identical, collapsed) | 0.1102 (+0.110) | 0.0512 (+0.051) |
| 0.8169 | 0.7962 (-0.021) | 0.7875 (-0.029) |

The correction cuts the bias by roughly 3x in the regime this battery occupies. It cannot
reach zero at `true distance = 0`, because the estimate is a square root of a non-negative
noisy quantity; distances near zero are therefore reported with their bootstrap CI and
never as evidence of exact identity. `run_stage1.py --selftest` asserts that the corrected
estimator's bias is less than half the plug-in's.

Why JS distance:

1. **It is a true metric.** The triangle inequality holds for `sqrt(JSD)`. Stage 1 wants
   to average distances across items, order models by dissimilarity and potentially
   embed or cluster the panel; a non-metric divergence makes all of that incoherent.
2. **Bounded and finite with zeros.** `distribution_distance = 0` iff the policies are
   identical, `= 1` iff their supports are disjoint. KL is unusable here — behavioural
   collapse (threat 3) puts exact zeros in most cells and KL diverges. Chi-square has the
   same defect.
3. **Symmetric,** as a "distance between two models" must be. KL is not.
4. **Interpretable.** JSD equals the mutual information between "which model produced this
   trial" and "which option was chosen", for a 50/50 mixture of the two models. That is
   exactly the Stage 1 question — how much does knowing the model tell you about the
   choice — expressed in bits.
5. **Sensitive to the whole distribution,** not just the mode, which `modal_agreement`
   already covers.

**Secondary (pre-registered):** Hellinger distance `sqrt(1 - sum_i sqrt(p_A(i) p_B(i)))`
— also a metric, bounded, and the most stable of the candidates at small counts.
**Third, descriptive only:** total variation `0.5 * sum_i |p_A(i) - p_B(i)|`. TV is a
metric, but it is piecewise linear and insensitive to how mass is redistributed inside
the agreeing region, which is precisely the tail structure Stage 1 needs. It is reported
because it is easy to read, and is never used for inference.

Any conclusion that reverses between JS and Hellinger is reported as unstable rather than
resolved by picking a winner.

---

### 4.2 The confound, stated exactly

For any two policies, Cauchy-Schwarz gives `M_AB <= sqrt(M_AA * M_BB)`, with equality iff
`p_A = p_B`. Define

```
cos_raw(A,B) = M_AB / sqrt( M_AA * M_BB )        in [0,1], = 1 iff p_A == p_B
```

which yields the **exact accounting identity**

```
    log M_AB  =  1/2 log M_AA  +  1/2 log M_BB  +  log cos_raw(A,B)
                 \___________________________/     \______________/
                    DETERMINISM CHANNEL              ALIGNMENT CHANNEL
```

with zero residual, by construction. Every change in raw cross-model match decomposes,
additively and without remainder, into a part driven by the two models' own self-matches
(`within_model_match` — the metric already in the dictionary) and a part driven by their
mutual alignment. **This decomposition is reported for every convergence analysis**: a
rise in raw match whose determinism channel accounts for all of it is not convergence.

`cos_raw` is NOT sufficient as the adjusted statistic, and Stage 1 must not treat it as
one. It removes the SCALE part of determinism but not the MODE-COLLAPSE part: if two
models share a modal option and both sharpen toward it, `cos_raw -> 1`. Measured on
synthetic Case A (determinism rising, true similarity exactly constant), `cos_raw` rose
with a slope of +0.0195 per vintage step and a single study would have called it
convergence 100% of the time. Worse, its direction is data-dependent — when the modes
differ it falls instead. `cos_raw` is a diagnostic, reported as the alignment channel of
the identity above, never as the adjusted similarity.

---

### 4.3 `das` — determinism-adjusted similarity (PRIMARY)

**Model.** A policy is a tempering of an underlying convention:

```
p  =  temper(q, beta)  ,   temper(q, tau)_i  =  q_i^tau / sum_j q_j^tau
```

`q` is the model's **convention** — which options it prefers and in what order — and
`beta > 0` its **determinism** (inverse temperature). `beta -> inf` gives a point mass on
`argmax q`; `beta -> 0` gives the uniform policy. The two are separate coordinates of the
same object, which is exactly the separation MASTER_DESIGN S5 demands.

**Standardisation.** `S(temper(p, tau))` is strictly decreasing in `tau` for non-uniform
`p` (`-> K` as `tau -> 0`, `-> 1` as `tau -> inf`), so for any target `S*` in (1, K) there
is a unique `tau*(p)` with `S(temper(p, tau*)) = S*`. Define

```
p~  =  temper( p, tau*(p) )         the STANDARDISED policy
beta_hat  =  1 / tau*(p)            the cell's determinism relative to the reference
```

`tau*` is found by bisection on log tau over [1e-3, 1e3] to machine tolerance.

**Exact invariance.** The tempering family is a one-parameter group: `(q^b)^t = q^(bt)`.
So if `p = temper(q, beta)` for any `beta > 0`, then `temper(p, t) = temper(q, beta*t)`,
and the unique exponent that lands on support `S*` is `t = tau*(q)/beta`, giving

```
    standardize( temper(q, beta) )  =  standardize(q)      for EVERY beta > 0.
```

Standardisation therefore removes the determinism coordinate exactly and returns the
convention coordinate untouched. Asserted numerically in `run_stage1.py --selftest`
(max deviation 6.7e-13 over beta in {0.3, 1, 2, 7, 25}).

**The statistic.**

```
    das(A,B)  =  S* * sum_i  p~_A(i) p~_B(i)          with S* = 2.0 by default
```

Both standardised policies have self-match exactly `1/S*`, so this equals the cosine of
the standardised policies: it lies in [0,1] and equals 1 iff the two conventions are
identical. It is the same functional form as `cross_model_match`, evaluated after both
models have been put on a common determinism footing — so it is directly comparable to
the raw metric it replaces. Being a function of `q` alone, it is invariant to any
per-model change in determinism (selftest: max deviation 6.7e-11 across beta pairs up to
(30, 30)).

**Companion on the metric scale.** `dajs(A,B) = 1 - sqrt(JSD(p~_A, p~_B))`, so the primary
distance and the primary similarity are adjusted the same way.

**Choice of `S*`.** Default 2.0 — the midpoint of the K=4 support range, and the level at
which a policy has "two live options", the regime this battery was built to probe.
`S*` is a reporting convention, not a substantive claim, so every headline result is
re-reported at `S*` in {1.5, 2.0, 2.5, 3.0}. A conclusion that only survives at one `S*`
is reported as unstable.

---

### 4.4 `rank_similarity` — the assumption-free floor (tier 3)

Kendall tau-b between the two option rankings, rescaled to [0,1]. Invariant under ANY
strictly monotone per-model transform of the policy, not only tempering, so it does not
rely on the tempering model being right. With K=4 it has only 6 pairwise comparisons and
is coarse; it is reported as a floor beneath `das`, and a `das` result that
`rank_similarity` contradicts is reported as model-dependent.

---

### 4.5 Finite-sample behaviour: an identifiability limit, not a bias

`das` is exactly invariant in the population. It is **not** invariant in a finite sample,
and the failure is not a bias a bootstrap can remove. Measured on synthetic Case A, where
the true `das` is 0.932 at every vintage and only determinism moves:

| true effective support | 2.00 | 1.51 | 1.23 | 1.08 | 1.02 |
|---|---|---|---|---|---|
| estimated `das` | 0.925 | 0.941 | 0.968 | 0.984 | 0.995 |

The mechanism: a cell whose true support is ~1.02 produces `(48,0,0,0)` on nearly every
draw. That sample carries essentially no information about the ORDER of the tail. After
add-alpha smoothing every such cell standardises to nearly the same vector, so `das`
between two of them is driven toward 1 whatever the truth. This is an **identifiability
limit** — the information is absent, not merely noisy. Parametric bootstrap bias
correction was implemented and tested and does not fix it; it moves the estimate the wrong
way.

Three consequences, all binding on Stage 1:

1. **`das` must not be tested against zero slope.** See S4.6.
2. **Estimability must be reported per pair.** The pipeline reports
   `support_target_a/b = 1 / within_model_match` for every cell, the count of
   "reference rows" (both cells at `>= 0.9 * S*` observed support), and an explicit
   `identifiable` flag. Below the threshold, `das` is reported as an upper bound driven
   by the prior, not as an estimate.
3. **It is a design constraint on the battery.** If the checkpoint panel is uniformly
   near-deterministic on the chosen items, determinism and similarity cannot be separated
   *at any n that Stage 1 can afford*, and no adjustment can rescue it. Items must be
   selected to keep effective support alive. This is a reportable outcome about the
   battery, not a failure to engineer around, and it is exactly what the worked run on
   existing 4-option data finds (S6).

---

### 4.6 The determinism-matched null band (PRIMARY INFERENCE)

Because the artefact in S4.5 is a trajectory rather than a constant, the `das` slope is
tested not against zero but against **the slope this same pipeline produces when
alignment is genuinely constant and determinism follows the observed trajectory**. The
artefact then appears in the null band as well, and cancels.

```
H0 : true convention alignment does not change with checkpoint vintage;
     determinism is whatever was observed.
```

Construction, per analysis set:

1. **Determinism target per cell:** `S_target = 1 / within_model_match(counts)`, clipped
   to (1, K). `within_model_match` is unbiased for `sum_i p_i^2`, so its reciprocal reads
   the cell's true support with far less bias than the plug-in. Using the observed
   standardising exponent instead puts estimation noise into the null twice and shrinks
   the band; this was measured (Case A rejected 67-100% of the time) and rejected.
2. **Reference rows:** pairs where BOTH cells sit at `>= 0.9 * S*` observed support —
   the rows where standardisation interpolates rather than extrapolates, hence where the
   standardised policies are trustworthy.
3. **H0 pseudo-truth:** for each row, draw a reference row at random and adopt **its PAIR
   of standardised policies wholesale**. Resampling the *pair* — not a mean alignment
   level — preserves the data's joint structure (modal-agreement rate, alignment spread,
   shape family) while carrying no vintage information. An earlier construction that
   matched only the mean alignment failed calibration badly, because the size of the
   artefact depends on the modal-agreement rate.
4. Temper each to its row's `S_target`, resample at the observed `N`, recompute `das`,
   refit the vintage slope. Repeat B times.

Report: observed slope, null band [2.5%, 97.5%], **`excess_slope = observed - null_mean`**
(the headline convergence quantity), two-sided p, and the `identifiable` flag.

Validated size and power (`synthetic_validation.md`): Case A (no similarity change)
rejection 0.00; Case B (pure similarity increase) 1.00; Case D (similarity decrease behind
rising determinism) 1.00; Case C (both) lower, because when determinism rises far enough
the ceiling effect eats the signal. The test is mildly conservative by construction (the
reference pairs are themselves estimated, so the null's alignment distribution is slightly
over-dispersed and the band slightly wide) — conservative in the safe direction for a
study whose primary inferential error would be a false convergence claim.

**Secondary confirmation.** Where enough reference rows exist, the same slope is refit on
the estimable subset alone (both cells above the support threshold), where `das` is
nearly unbiased and an ordinary item-clustered bootstrap CI is valid. Agreement between
the two is reported; disagreement is reported, not reconciled.

---

## 5. Convergence analyses

**Vintage coordinate.** `v(pair) = mean of the two checkpoints' CALENDAR release dates`,
expressed in years since 2025-01, so every slope reads "per year". `vintage_min` (the
older of the two) is reported as a robustness alternative.

> T4's `audits/models/checkpoint_panel_verified.csv` supplies both `vintage` (YYYY-MM) and
> `release_order`. **Use the calendar date, not `release_order`:** that counter restarts
> within each family (GPT 1..10, Claude 1..7), so averaging it across a cross-family pair
> compares two different scales. The pipeline reads `vintage_date` when present and falls
> back to an integer `vintage_rank` only for a single-family analysis or a worked run.
> `stratum` is carried through from the same file, and `same_stratum` is reported as a
> grouping variable, because MASTER_DESIGN S4/S4.1 makes compatibility strata a real
> boundary rather than a nuisance.

Every slope below is an OLS slope of the metric on `v` with an **item-clustered bootstrap**
CI (2000 resamples, items are the resampling unit because the same item contributes a row
at every vintage; treating pair x item rows as independent would understate the SE).

| # | analysis | statistic |
|---|---|---|
| 1 | similarity by checkpoint vintage | slope of every ladder rung on `v`, with the S4.2 decomposition of the raw trend |
| 2 | within-family similarity | slope restricted to `pair_type == within_family` |
| 3 | cross-family similarity | slope restricted to `pair_type == cross_family` |
| 4 | domain interaction | slopes within `domain` in {visual, code}; contrast = spread of group slopes |
| 5 | mechanism interaction | slopes within `mechanism`; contrast = spread of group slopes |
| 6 | **determinism-adjusted similarity** | S4.6 null band; `excess_slope` and p |
| 7 | item-level exceptions and reversals | per-item `das` slope; items whose sign OPPOSES the pooled sign; `modal_agreement` reversals (agree at the lowest vintage, disagree at the highest) |
| 8 | leave-one-family-out | pooled slope with each `family` dropped in turn |
| 9 | leave-one-mechanism-out | pooled slope with each `mechanism` dropped in turn |
| 10 | compatibility-stratum check | slopes within `same_stratum` in {0,1}; a trend carried only by cross-stratum pairs is a request-surface artefact, not convergence |

`family` and `mechanism` are kept separate throughout, per DATA_DICTIONARY, so cosmetic
variants are not counted as independent mechanisms. Leave-one-out is the guard against a
single family or mechanism carrying the whole trend; a pooled slope whose CI excludes zero
only when one level is present is reported as driven by that level.

**Chance floors** (DATA_DICTIONARY): modal share, cross-model match and within-model match
all sit at .25 under K=4. `das` is normalised so that 1 = identical conventions; its
"chance" value under independent conventions is not 0.25 and is reported empirically from
the null band, not assumed.

**Multiplicity.** Analyses 1 and 6 are the pre-registered primary; everything else is
explicitly secondary and reported with unadjusted CIs and an explicit "descriptive, not
tested" label. Analysis 7 is a screen, not a set of hypothesis tests.

**Required language** (MASTER_DESIGN S2) is enforced in the report template: "convergence
on this fixed battery"; "associated with checkpoint vintage"; "policy similarity";
"descriptive historical pattern".

---

## 6. Worked run on existing data

`run_stage1.py` with `sources_worked_run.json` reads four existing checkpoints
(`claude-opus-4-6`, `claude-opus-4-7`, `claude-opus-5`, `gpt-5.5-2026-04-23`) on the 19
`battery5` arrays they share, all at one prompt generation (`d40ea45d`), strictly
read-only. This is a pipeline demonstration on a convenience sample, **not** the Stage 1
panel (T4 owns that, MASTER_DESIGN S4 marks it TBD) and the vintage ranks are
analyst-supplied. Full output: `out/worked_run/SUMMARY.md`.

Pipeline behaviour: all three integrity gates PASS (one prompt generation `d40ea45d`
across all four checkpoints; `checkpoint_requested == checkpoint_returned` on every row;
zero parse failures). Three `r_line_contour_*` arrays present in the Opus runs but absent
from `battery5_manifest.csv` are correctly excluded by the manifest gate, and the 84 cells
from `discovery5` at n=24 are flagged against the n=48 floor rather than silently used.

The substantive finding that matters for Gate 1: **the existing 4-option visual battery is
already too deterministic to separate determinism from similarity.**

| | |
|---|---|
| median `effective_support` over 122 cells | **1.180** (IQR 1.000-1.669) |
| cells at `modal_share >= 0.99` | **52 / 122** |
| median `effective_support`, `claude-opus-4-7` | **1.000** |
| median `effective_support`, `claude-opus-5` | **1.000** |
| pair x item rows meeting the strict reference threshold (both cells at support >= 1.8) | **3 / 137** |
| pair x item rows in the estimable subset (both cells at support >= 1.5) | **12 / 137** |
| determinism-adjusted test | `identifiable = False` |

If the Stage 1 visual frame is drawn from arrays like these, no adjustment — this one or
any other — will make the central question answerable, at n=48 or at any n Stage 1 can
afford. **T1's broad sampling frame should be screened on `effective_support` as well as
on selection-bias grounds**, and the code battery's pilot gate should add "retains more
than one live option for the sharper checkpoints" to its pass criteria. Reported here as
an empirical property of the existing stimuli, not as a result about the models.

---

## 7. Outputs and reproducibility

```
out/<run>/integrity.json      every gate, every excluded cell, with the reason
out/<run>/cell_metrics.csv    one row per model x item, S3 metrics
out/<run>/pair_metrics.csv    one row per model-pair x item, S4 metrics + raw counts
out/<run>/convergence.json    every S5 analysis
out/<run>/SUMMARY.md          the human-readable report
```

All randomness is seeded (`seed = 20260909`, per-analysis offsets are deterministic
integers, never `hash()`). `run_stage1.py --selftest` asserts the eight properties this
spec claims and exits non-zero on any failure. It should be run before any result is
reported.

1. `standardize(temper(q, beta)) == q` for every beta (S4.3 exact invariance)
2. `das` invariant to per-model tempering (S4.3)
3. `log M_AB = .5 log M_AA + .5 log M_BB + log cos_raw` exactly (S4.2)
4. `cross_model_match` is unbiased as a plug-in (S4.0)
5. `within_model_match` is unbiased and the plug-in is biased upward (S3)
6. JS distance is 0 on identical and 1 on disjoint policies (S4.1)
7. Miller-Madow more than halves the JS distance bias at n=48 (S4.1)
8. the vectorised fast paths agree with the scalar estimators to 1e-9

---

## 8. What this analysis cannot do

- It cannot establish that a temporal pattern is a causal effect of training
  (MASTER_DESIGN S2). Vintage is an observational ordering over a survivorship-biased set
  of callable checkpoints.
- It cannot separate determinism from similarity in cells that have collapsed to a single
  live option. S4.5 gives the boundary; the pipeline reports which side of it each pair
  is on. Reporting a `das` estimate from below that boundary as evidence of convergence
  would be the same error the study is built to avoid, one level down.
- It cannot rescue a battery selected on a model relationship (threat 1). The estimators
  are unbiased for the frame they are given; they say nothing about how the frame was
  chosen.
- With four options and n=48, `form_consistency` is quantised to 1/12 and cannot certify
  position invariance for an individual item; it supports aggregate statements only.
