# Study 1b: crossed object-level prediction results

Collected 2026-10-07/08 under `FROZEN_SCREEN 4c411796` → `SELECTION 26eb30e6` → `FROZEN_MAIN 9e11e56e` (Amendment 1, sha256 `49564e9d…`, frozen before screening). Models: GPT-5.5 (`gpt-5.5-2026-04-23`, reasoning effort low) and Claude Opus 5 (`claude-opus-5`, thinking disabled). Prompts, selection rules, scoring draws, response counts and gates were unchanged.

## Bottom line

- **On arrays where the two models' choice policies differ, each model predicts its own choices more accurately than the other model predicts them.** The pooled self-minus-cross Brier advantage is +.258, 95% CI [.126, .399], exact sign-flip p = .004, with 9 of 10 arrays favouring self. It holds for each target separately.
- **On shared-policy controls the advantage is zero:** +.000 [−.014, +.013].
- **Exploratory diagnostic:** the advantage is explained by **projection**, not by knowing *how* the other model differs.
  - Each predictor gives nearly the same distribution for both targets.
  - Its predictions about the other model sit closer to its own policy than to the other model's.
  - Predicted target differences do not line up with measured ones.
  - Each model is right about itself because it predicts its own preference for everyone.

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

**Continuous divergence moderation (all 20 arrays):**
- Δ_j on screening total variation distance: slope +.485 [.241, .715], permutation p < .001.
- Target GPT: slope +.459, p = .001. Target Opus: slope +.512, p = .002.
- Screen-vs-fresh reliability of the distance measure: r = .97.

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
- **Reading:** the primary result shows that each model's predictions encode *its own* policy (consistent with Study 1, where auditors projected their own matching probabilities). It shows **no evidence that either model knows the other model's policy differs from its own.** The pre-registered primary is met, but it does not establish privileged self-knowledge beyond self-projection.

## Power for the actual primary sample (n = 10, frozen assumptions)

| Between-array SD (τ) | δ = .03 | δ = .05 | δ = .08 |
|---|---|---|---|
| .085 | .13 | .28 | .58 |
| .05 | .19 | .45 | .83 |

The observed effect (+.258) is far above the design's minimum detectable effect, so low power did not limit the primary test. It does limit the target-specific and stratum-level estimates, which have wide CIs.

## Limitations

1. **Small primary sample:** 10 arrays against a planned 22–32 (shortfalls S1 −3, S2_G −3, S2_O −6). Divergent policies are rare in this battery.
2. **S1 depends on the fallback:** 3 of the 5 S1 arrays entered under the pre-registered ≥ .70 threshold.
3. **Family clustering:** F12_mirror contributes 3 primary arrays (one in S2_G twice, one in S2_O) and F10_curvature contributes 2. The family cap applies per stratum, not across the primary sample, so families are not independent units.
4. **Construct:** projection fully accounts for the self-advantage (exploratory diagnostic). Separating it from target-aware self-knowledge would need a condition where projection and self-knowledge predict different things. None was added.
5. **Opus identity:** Opus is served under an alias, so weights identity is certified only to the alias on the run date.
6. **Moderation is partly built in by design:** S3 has low distance and Δ ≈ 0, while S1 has high distance and large Δ. The slope mostly reflects the contrast between strata.
7. **Selection metric:** strata were selected on screening draws (24 per model). Targets came from fresh draws, and the distance measure replicated (r = .97).

## Files

- **`~/Downloads/Study1b_results/`:**
  - `fig_selfcross.pdf` / `.png`: per-array Δ, with the mean and 95% CI;
  - `results.json`, `item_table.csv`, `projection_diagnostic.json`.
- **Study folder:** `analysis/out/` and `code/analyze.py`. The Study 1 matching-probability results are kept separate and were not pooled.
