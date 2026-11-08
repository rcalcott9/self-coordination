# Study 1b: crossed object-level prediction results (v2)

v2 adds a post hoc family-level sensitivity analysis and edits the interpretation. The frozen primary analysis and all numbers from v1 are unchanged; v1 is preserved as `RESULTS_v1.md`.

Collected 2026-10-07/08 under `FROZEN_SCREEN 4c411796` → `SELECTION 26eb30e6` → `FROZEN_MAIN 9e11e56e` (Amendment 1, sha256 `49564e9d…`, frozen before screening). Models: GPT-5.5 (`gpt-5.5-2026-04-23`, reasoning effort low) and Claude Opus 5 (`claude-opus-5`, thinking disabled). Prompts, selection rules, scoring draws, response counts and gates were unchanged.

## Bottom line

Two claims need to be kept apart.

| Claim | Status |
|---|---|
| **Predictive self-advantage:** on arrays where the two models' choice policies differ, each model's predictions about itself are more accurate than the other model's predictions about it. | **Demonstrated.** Pre-registered primary: pooled self-minus-cross Brier advantage +.258, 95% CI [.126, .399], exact sign-flip p = .004, 9 of 10 arrays. It holds for each target separately, is zero on shared-policy controls (+.000 [−.014, +.013]), and survives family-level aggregation (7 families, +.246, exact p = .031). |
| **Relational self-knowledge:** a model represents that its own policy differs from the other model's, and predicts the two targets differently in the measured direction. | **Not demonstrated.** In an exploratory, non-pre-specified diagnostic, each predictor gave nearly the same distribution to both targets, and predicted target differences did not line up with measured ones. The data are compatible with self-projection, where each model predicts its own preference for any target. This design was not built to test projection against relational self-knowledge, so it neither establishes nor rules out either account. |

## Collection, counts, cost

| Stage | Calls | Parsed | Model mismatches | Cost | Cap |
|---|---|---|---|---|---|
| Screen (57 arrays × 2 models × 24) | 2,736 | 2,736 | 0 | $19.45 | $25 |
| Preflight (gate passed: 6/6) | 6 | 6 | 0 | $0.06 | |
| Parse pilot (gate ≥ .95 passed: 8/8 in each of the 4 cells; excluded from analysis) | 32 | 32 | 0 | $0.33 | |
| Main: fresh targets 1,920 + predictions 640 | 2,560 | 2,560 | 0 | $19.50 | $40 |
| **Total** | **5,334** | **5,334** | **0** | **$39.34** | |

**Selected arrays.** Selection used screening draws only, with the rules frozen beforehand.

| Stratum | Quota | Selected | Note |
|---|---|---|---|
| S1, opposing concentrated | 8 | **5** | fewer than 4 qualified at .75, so the pre-registered ≥ .70 fallback was used; 3 of the 5 entered via the fallback |
| S2_G, GPT concentrated / Opus diffuse | 6 | **3** | |
| S2_O, Opus concentrated / GPT diffuse | 8 | **2** | |
| **Primary sample (S1 + S2)** | | **10** | |
| S3, shared-policy controls | 10 | 10 | |

No array was excluded: every cell had 8 of 8 parsed responses.

## Primary result (Amendment 1)

**Contrast.** For each array j, using Brier scores B̄ against 48 fresh target draws per model (lower is better):

Δ_j = ½[(B̄_Opus→GPT + B̄_GPT→Opus) − (B̄_GPT→GPT + B̄_Opus→Opus)]

Δ > 0 means self-predictions are more accurate.

| Contrast (primary sample, n = 10) | Mean | 95% CI (array bootstrap) | Sign-flip p, (k+1)/(B+1), B = 10,000 flips | Exact p (all 1,024 sign patterns) | Arrays + / − |
|---|---|---|---|---|---|
| **Pooled self − cross** | **+.258** | **[.126, .399]** | **.0033** | **.0039** | 9 / 1 |
| Target GPT: Opus→GPT minus GPT→GPT | +.217 | [.079, .394] | .0066 (Holm .013) | .0059 | 9 / 1 |
| Target Opus: GPT→Opus minus Opus→Opus | +.299 | [.138, .464] | .0096 (Holm .013) | .0117 | 8 / 2 |
| Predictor main effect | +.041 | [−.042, +.124] | .39 | | 5 / 5 |
| Target main effect | +.008 | [−.094, +.119] | .86 | | 5 / 5 |

Mean cell Brier scores on the primary sample:

| Predictor ↓ / Target → | GPT | Opus |
|---|---|---|
| GPT | **.572** | .821 |
| Opus | .788 | **.522** |

**Sensitivity analyses, all agreeing:**
- hierarchical bootstrap CI [.111, .421];
- log score (floored at .01): Δ = +.417 [.223, .638], 10 of 10 arrays positive, p = .002;
- linear mixed model interaction −.515 [−.728, −.303], i.e. Δ = +.258. A Hessian warning applies to the random-effect variance only.

The sign-flip p-values divide by the number of simulated flip vectors (B = 10,000), as Amendment 1 requires. With n = 10 the exact enumeration over 1,024 sign patterns is also reported.

## Secondary results

**S3, shared-policy controls (n = 10):**
- pooled +.000 [−.014, +.013], p = .97;
- target GPT −.036 [−.091, +.027];
- target Opus +.036 [−.039, +.103].

**By stratum (descriptive):**

| Stratum | n | Pooled Δ | Target GPT | Target Opus |
|---|---|---|---|---|
| S1 | 5 | +.391 | +.349 | +.434 |
| S2_G | 3 | +.068 | +.137 | −.002 |
| S2_O | 2 | +.208 | +.003 | +.413 |
| S3 | 10 | +.000 | −.036 | +.036 |

The target-specific advantage appears mainly where *that target* is the concentrated model. That is the pattern projection predicts.

**Continuous divergence moderation (all 20 arrays; descriptive, partly built into the design):**
- Δ_j on screening total variation distance: slope +.485 [.241, .715], permutation p < .001.
- Target GPT: slope +.459, p = .001. Target Opus: slope +.512, p = .002.
- Screen-vs-fresh reliability of the distance measure: r = .97.
- **Interpretation:** S3 arrays have low distance and Δ ≈ 0 by construction, and S1 arrays have high distance, so the slope largely restates the contrast between strata. It shows that the predictive advantage is confined to divergent arrays. It is not separate evidence that the advantage scales with divergence, and it is not evidence of relational self-knowledge.

## Exploratory diagnostic: projection vs differentiated self-knowledge (not pre-specified)

| | GPT as predictor | Opus as predictor |
|---|---|---|
| Mean total variation distance between its predictions for the two targets | .067 | .048 |
| Arrays where its two target predictions differ by more than .10 | 3 / 10 | 0 / 10 |
| Cross-prediction scored against the predictor's own policy vs the target's (Brier gap; > 0 = closer to own) | +.275 | +.264 |
| Arrays where the cross-prediction is closer to the predictor's own policy | 10 / 10 | 6 / 10 |
| Cosine between predicted and measured target difference | −.26 | +.12 |

- Both models predict essentially the same distribution for "GPT-5.5" and for "Claude Opus 5", and that distribution follows their own preference.
- Where policies diverge, this makes self-predictions accurate and cross-predictions wrong.
- **Reading:** this pattern is *compatible with* self-projection: each model predicts its own preference for both targets, which is accurate for itself and inaccurate for the other where policies diverge. It matches Study 1, where auditors' predictions tracked their own matching probabilities.
- This is an exploratory description, not a test. It does not show that projection is the mechanism, and it does not rule out some relational knowledge. What it shows is that the predictive self-advantage **does not by itself demonstrate relational self-knowledge**, because the predictors barely differentiate the two targets.

## Family-level sensitivity (post hoc; the frozen primary is unchanged)

Array contrasts are averaged within each stimulus family, and each family is weighted equally. There are **7 independent families** among the 10 primary arrays. The exact two-sided sign-flip uses all 2⁷ = 128 sign patterns, so the minimum attainable p is .016. Code: `code/family_sensitivity.py`; output: `analysis/out/family_sensitivity.json`.

**Family means:**

| Family (arrays; strata) | Pooled Δ | Target GPT | Target Opus |
|---|---|---|---|
| F10_curvature (m2, m3; S1) | +.581 | +.582 | +.580 |
| F20_corner (m0; S1) | +.542 | +.355 | +.729 |
| F27_linecount (m1; S2_O) | +.233 | −.024 | +.490 |
| F30_pairratio (m2; S1) | +.161 | +.179 | +.142 |
| F12_mirror (m0, m3, m6; S2_G, S2_O, S2_G) | +.136 | +.147 | +.124 |
| F05_orient (m7; S1) | +.093 | +.049 | +.137 |
| F31_overlap (m1; S2_G) | −.019 | +.001 | −.039 |

**Summary:**

| | Pooled Δ | Target GPT | Target Opus |
|---|---|---|---|
| Equally weighted family mean | **+.246** | +.184 | +.309 |
| Exact family-level sign-flip p | **.031** | .047 | .031 |
| Families + / − | 6 / 1 | 6 / 1 | 6 / 1 |
| Leave-one-family-out, family mean (range) | +.191 to +.291 | +.118 to +.219 | +.239 to +.367 |
| Leave-one-family-out, array mean (range) | +.177 to +.310 | +.125 to +.246 | +.229 to +.374 |

- The predictive self-advantage survives treating families as the unit.
- No single family drives it. The smallest leave-one-family-out estimate (+.191, dropping F10_curvature) is still large.
- The family-level p is necessarily weaker than the array-level p, because there are only 7 units.

## Power for the actual primary sample (n = 10, frozen assumptions)

| Between-array SD (τ) | δ = .03 | δ = .05 | δ = .08 |
|---|---|---|---|
| .085 | .13 | .28 | .58 |
| .05 | .19 | .45 | .83 |

The observed effect (+.258) is far above the design's minimum detectable effect, so low power did not limit the primary test. It does limit the target-specific and stratum-level estimates, which have wide CIs.

## Limitations

1. **Small primary sample:** 10 arrays against a planned 22–32 (shortfalls S1 −3, S2_G −3, S2_O −6). Divergent policies are rare in this battery.
2. **S1 depends on the fallback:** 3 of the 5 S1 arrays entered under the pre-registered ≥ .70 threshold.
3. **Family clustering:** the 10 primary arrays come from **7 independent stimulus families**. F12_mirror contributes 3 arrays (2 in S2_G, 1 in S2_O) and F10_curvature 2, because the family cap applies per stratum, not across the primary sample. The family-level sensitivity analysis below addresses this. Its minimum attainable exact p is 2/128 = .016.
4. **Construct:** the primary contrast measures predictive self-advantage. It cannot by itself separate self-projection from relational self-knowledge, because both predict self > cross on divergent arrays. The exploratory diagnostic is compatible with projection. Separating the two would need a condition where they predict different things; none was added.
5. **Opus identity:** Opus is served under an alias, so weights identity is certified only to the alias on the run date.
6. **Moderation is partly built in by design:** S3 has low distance and Δ ≈ 0, while S1 has high distance and large Δ. The slope mostly reflects the contrast between strata.
7. **Selection metric:** strata were selected on screening draws (24 per model). Targets came from fresh draws, and the distance measure replicated (r = .97).

## Files

- **`~/Downloads/Study1b_results/`:**
  - `fig_selfcross.pdf` / `.png`: per-array Δ, with the mean and 95% CI;
  - `results.json`, `item_table.csv`, `projection_diagnostic.json`.
- **Study folder:** `analysis/out/`, `code/analyze.py` and `code/family_sensitivity.py`. The Study 1 matching-probability results are kept separate and were not pooled.
