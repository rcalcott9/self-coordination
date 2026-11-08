# Cross-model divergence vs prediction error: exploratory analysis

Existing data only, no new calls. Joins `item_table.csv` to the per-object VIS-FRAME-41 counts for GPT-5.5 and Opus 5 (48 draws per array, frame configuration). The join is verified to 1e-4 against the item table.

**Uncertainty:** 95% CIs come from a hierarchical bootstrap (B = 2,000). It resamples arrays, then within each array resamples both models' calibration draws and the self and auditor repeats.

**Split halves:** where the outcome and the predictor both contain the focal model's measured matching probability y_f, each model's 48 draws are split into two position-balanced halves of 24 (one draw per presentation order each). The error is scored on half 1 and the divergence on half 2, averaged over 200 random splits. This removes the spurious association that shared measurement noise in y_f would otherwise create.

**Reliability:** measured matching probability is highly reliable (Spearman–Brown split-half: GPT .98, Opus .99), so attenuation from calibration noise is small.

Nothing here selects on observed prediction errors. Code: `code/divergence.py`; outputs: `analysis/out/divergence/`.

## 1. Favourite-object agreement and distribution overlap

| | Estimate [95% CI] |
|---|---|
| Same favourite object | 31 / 41 arrays; calibration-adjusted rate .77 [.61, .88] (GPT has one tied favourite, F28) |
| Cross-model match, P(GPT draw = Opus draw) | .68 [.60, .77] |
| Distribution overlap, 1 − total variation distance | .77 [.70, .83] |

On all 10 arrays where the favourites differ, at least one model is diffuse. **No array has both models concentrated (y > .8) on different favourites.** In this set, favourite-object divergence therefore cannot be separated from low matching probability.

## 2. Matching-probability agreement

| | Estimate [95% CI] |
|---|---|
| r(y_GPT, y_Opus), Pearson / Spearman | .55 [.28, .74] / .59 [.31, .76] |
| Mean absolute difference \|y_GPT − y_Opus\| | .186 [.13, .24] |
| Same quantity if both models had identical true distributions (noise floor) | .046 [.03, .06] |
| Mean signed difference, GPT − Opus | −.096 [−.16, −.02] |

The divergence in matching probability is real, roughly four times the calibration-noise floor. 11 arrays differ by more than .3; in 8 of them Opus is the concentrated one, in 3 it is GPT.

## 3–4. Do auditor error, self error, and self-advantage change with divergence?

Slopes of absolute error, or of the paired advantage D = |A − y| − |S − y| (D > 0 means self is closer), on two divergence measures:
- **matching-probability divergence** \|Δy\| = \|y_auditor − y_focal\|;
- **favourite/distribution divergence**, total variation distance (TVD).

| Focal model → outcome | ~ \|Δy\|, unadjusted | ~ \|Δy\|, adjusted for focal y | ~ TVD, unadjusted | ~ TVD, adjusted for focal y |
|---|---|---|---|---|
| GPT: auditor error | −.23 [−.45, +.07] | +.01 [−.18, +.24] | −.27 [−.42, −.10] | +.12 [−.08, +.33] |
| GPT: self error | −.07 [−.19, +.08] | −.11 [−.25, +.09] | +.06 [−.08, +.14] | +.07 [−.06, +.21] |
| GPT: D (self advantage) | −.17 [−.37, +.07] | +.12 [−.06, +.25] | −.33 [−.47, −.12] | +.04 [−.13, +.20] |
| Opus: auditor error | +.04 [−.16, +.21] | +.08 [−.05, +.18] | −.25 [−.33, −.07] | −.00 [−.12, +.14] |
| Opus: self error | +.05 [−.11, +.21] | +.07 [−.07, +.21] | −.12 [−.22, +.05] | +.05 [−.08, +.18] |
| Opus: D (self advantage) | −.01 [−.15, +.11] | +.01 [−.11, +.12] | −.14 [−.21, −.02] | −.06 [−.13, +.07] |

- **Unadjusted:** auditor error and self-advantage *fall* as favourite divergence rises. This comes from agreement level. Divergent arrays are the low-agreement ones, and the largest errors sit at y ≈ 1, where auditors underpredict.
- **Adjusted for the focal model's matching level** (half 2, independent of the outcome's noise): **no association is detected** for either divergence measure, for auditor error, self error, or D. All CIs include zero. These are 41-array analyses with only 11 strongly divergent arrays, so moderate effects cannot be ruled out.

## 5. Auditors vs a simple baseline (the auditor's own measured matching probability)

The baseline predicts the focal model's y using the auditor model's own measured y on the same array, i.e. "assume they behave like me". It is an oracle-style baseline, because it uses measured behaviour the auditor never sees.

| Focal model | Auditor MAE | Self MAE | Baseline MAE | Baseline − auditor | Self − baseline |
|---|---|---|---|---|---|
| GPT (auditor = Opus) | .206 | .198 | .186 | −.020 [−.10, +.05] | +.012 [−.05, +.08] |
| Opus (auditor = GPT) | .238 | .205 | .186 | −.052 [−.12, +.004] | +.019 [−.04, +.08] |

Neither auditor beats the baseline; both point estimates favour the baseline, though the CIs include zero. Self-predictions do not beat it either.

**Projection.** Regressing the auditor's prediction on both models' measured y:

| Prediction | Coefficient on focal model's y | Coefficient on predictor's own model's y |
|---|---|---|
| Auditor of GPT (Opus) | .15 [−.00, +.31] | .26 [.11, .40] |
| Auditor of Opus (GPT) | .15 [.04, .25] | .19 [.09, .31] |
| GPT self-prediction | .11 [.03, .20] | (Opus's y) .09 [.00, .17] |
| Opus self-prediction | .26 [.09, .42] | (GPT's y) .16 [.01, .34] |

Auditor predictions load at least as much on the auditor's own model's matching as on the focal model's, which is consistent with projection. Self-predictions also load on the *other* model's matching. Both kinds of prediction track array-level difficulty that both models share, plus the predictor's own tendency, more than anything specific to the focal model.

Note: the signed-error slope (auditor's signed error vs auditor-minus-focal y: +.56 and +.45) is not reported as evidence. It is partly mechanical, because −y_f appears on both sides and the predictions are compressed. The joint regression above is the cleaner test.

## Reading (exploratory)

- The two models share favourite objects on most arrays, but they differ substantially in *how reliably* they converge.
- In the existing arrays, neither auditor nor self error is detectably related to either kind of divergence once agreement level is controlled.
- Auditors behave like "projection plus generic legibility" and are not better than simply using their own model's measured matching probability. Self-predictions also do not beat that baseline.
- This agrees with the primary result (no detected self advantage for GPT; a small, non-significant one for Opus) and gives no sign of privileged, model-specific self-knowledge.

## Should new arrays be added?

- **Favourite-object divergence: not justified for the current measures.** The predictions target matching probability, not which object is chosen. The empty cell (both models concentrated on different favourites) matters only for object-level predictions, which Study 1 does not collect.
- **Matching-probability divergence: weakly justified, as a targeted follow-up rather than for significance.** This is where privileged self-knowledge and projection make opposite predictions, and the current set has only 3 arrays where GPT is concentrated and Opus diffuse.
  - The existing 4-option battery already has 162 non-frame arrays with prior data for both models: 12 with GPT > Opus by more than .3, and 27 the other way.
  - That prior data used Opus with **adaptive thinking** (s4_common), not the frame's thinking-off setting. Any such arrays would need fresh frame-configuration calibration before use, and the selection would rest on that calibration, never on prediction errors.
- **Not recommended now.** The existing primary and exploratory results are interpretable as they stand; adding arrays to chase the non-significant Opus effect would be sample-hunting.
