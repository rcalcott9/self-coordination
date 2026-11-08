# Study 1 high-reasoning replication (1a + 1b) — results

2026-10-09 · FROZEN `933aa87d` (`design/FROZEN.json`) · cost projection `design/COST_PROJECTION.json` · code `code/`.
All new data live in this folder; nothing was written to the low-reasoning studies.

## Settings and wording

| | GPT-5.5 | Claude Opus 5 |
|---|---|---|
| model returned | `gpt-5.5-2026-04-23` (dated snapshot; 0 mismatches) | `claude-opus-5` (alias, no snapshot; 0 mismatches) |
| settings | `reasoning.effort=high`, summary auto; effort echoed "high" in preflight | thinking adaptive (display summarized), `output_config.effort=high`, max_tokens 16,000 |
| preflight | 12/12 passed: accepted, parsed, no max_tokens stops; Opus returned a thinking block on every call | |

Prompts are the frozen low-reasoning texts with one change, verified character by character in `hi_common.build_prompts`:
- REF (`d40ea45d`), PLAYPASS (`3b5fe054`) and SELFPRED (`433b4569`) are identical.
- The AUDITOR (1a) and PRED (1b) prompts name the target's configuration. That clause was changed from "reasoning effort set to low" / "extended thinking turned off" to "reasoning effort set to high" / "extended thinking turned on, effort set to high", so that it describes the model actually being run.

Stimuli, Latin-square orderings (new seeds), parsers, the exclusion rules and the 1b array selection are all reused unchanged; no array was reselected.

## Collection, counts, cost

The global cap of $150 included preflight, pilot and retries. Spend was $149.22.

| stage | calls | parsed | transport fail | mismatch | cost |
|---|---|---|---|---|---|
| preflight | 12 | 12 | 0 | 0 | $0.32 |
| parse pilot (gate ≥ .95 per cell: 12/12 cells 8/8) | 96 | 96 | 0 | 0 | $2.51 |
| main | 6,879 of 8,216 | 6,879 | 0 | 0 | $146.39 |

Main ran in a frozen priority order. **Block A**, the 1b primary sample (10 divergent arrays: 48 REF per model + 8 predictions per cell), completed in full. **Block B**, Study 1a, ran in array-major order and completed **39/41 arrays**; F40_crossang_m1 is partial (7/48 REF) and F30_pairratio_m1 was never started, so both are excluded. **Block C**, the 1b S3 shared-policy controls, was not reached.

1,337 jobs remain resumable (`code/run.py --stage main` with a new cap), estimated at $28.73 at observed rates. The cost projection from the pilot ($137.6) underestimated, because the main arrays needed more reasoning than the two easy pilot arrays: REF calls cost about 1.4×, and GPT auditor calls about 1.5×, the pilot rate.

Mean pessimistic cost per call ($5 / $30 per M for both providers):

| | REF | PLAYPASS | SELFPRED | AUDITOR (answered by) | PRED |
|---|---|---|---|---|---|
| GPT | .0203 | .0362 | .0337 | .0790 | .0602 |
| Opus | .0104 | .0142 | .0110 | .0136 | .0152 |

## Study 1a (39 arrays per model; y = fresh high-reasoning REF, 48/array)

| | GPT-5.5 high | GPT-5.5 low (ref.) | Opus 5 high | Opus 5 low (ref.) |
|---|---|---|---|---|
| mean y / self / auditor | .727 / .743 / .609 | | .841 / .617 / .719 | |
| **P1** D = \|A−y\| − \|S−y\| (+ = self better) | **+.014** [−.032, .057], p = .53, 22+/17− | +.007, p = .77 | **−.055** [−.094, −.016], p = .008 (Holm .016), 11+/28− | +.033, p = .026 (Holm .052) |
| MAE self / auditor | .165 / .178 | .198 / .206 | **.255** / .200 | .205 / .238 |
| P2 self: slope, mean signed error, ρ | .29 [.19, .37], +.016, .79 | | .35 [.16, .54], **−.224** [−.29, −.16], .59 | |
| P2 auditor: slope, mean signed error, ρ | .38 [.23, .52], −.118, .69 | | .26 [.11, .40], −.122, .59 | |
| S1 GLMM PLAY ~ y (primary) | 7.07 [4.90, 9.88] | | 11.52 [5.32, 21.30] | |
| S1 GLMM adjusted for auditor A | 3.07 [0.81, 5.48] | | 3.24, Wald [−1.29, 7.76] (profile CI failed) | |
| S1 GLM (population-averaged) | 5.41 [3.18, 8.61] | 5.10 | 4.63 [1.52, 8.20] | 5.39 |
| overall P(PLAY) | .677 | | .827 | |
| S2 auditor prediction, old HIGH − LOW | +.198 [.12, .28] | | +.128 [.07, .19] | |
| S4 legacy d′ / AUC / c | 1.55 / .95 / −.39 | 1.57 / .93 | 1.63 / .78 / −1.17 | 1.74 / .78 |

- **GPT:** self-prediction and the Opus auditor are equally accurate, as at low effort.
- **Opus:** under high reasoning it underestimates its own matching probability by .22 on average, and the GPT auditor predicting Opus is now more accurate. The low-reasoning self-advantage (+.033, borderline) reverses to an auditor advantage (−.055, Holm .016).
- **PLAY/PASS:** it still tracks own agreement (GLMM slopes exclude 0 for both models). After adjusting for the auditor prediction, the association remains for GPT and is not established for Opus, as at low reasoning.
- S3 (old-wording PLAY/PASS) was not repeated; it concerned the low-reasoning legacy data only.

## Study 1b (original 10 divergent arrays; no reselection)

| contrast (n = 10 arrays) | mean | 95% CI | p (sign-flip; exact) | + / − |
|---|---|---|---|---|
| **Pooled self − cross Brier advantage** | **+.235** | [.127, .358] | .0024; exact .0020 | 10 / 0 |
| target GPT | +.180 | [.062, .319] | .016 (Holm .016) | 9 / 1 |
| target Opus | +.290 | [.132, .458] | .007 (Holm .014) | 8 / 2 |
| predictor main effect | +.055 | [−.040, .147] | .31 | |
| target main effect | +.003 | [−.090, .106] | .95 | |
| log score, pooled | +.360 | [.204, .534] | exact .0020 | 10 / 0 |
| family level (7 families) | +.212 | [.090, .354] | exact .016 | 7 / 0 |

Cell mean Brier (lower is better):

| | GPT→GPT | GPT→Opus | Opus→GPT | Opus→Opus |
|---|---|---|---|---|
| Brier | .547 | .779 | .728 | .489 |

The self-advantage replicates under high reasoning (low reasoning: +.258).

**Current divergence of the original arrays** (descriptive only). Mean TVD on the 10 primary arrays is .55 (low reasoning: .61).
- Only 3/10 still meet their original stratum definition at the strict .75 cut: F10_curvature_m3 S1, F12_mirror_m3 S2_O, F27_linecount_m1 S2_O.
- On 3/10 the two models now share a modal shape (F12_mirror_m0 / m6, F31_overlap_m1).
- S3 controls were not collected, so no shared-policy control exists under high reasoning.

## Secondary: high vs low reasoning (paired by array; family-cluster bootstrap and family sign-flip)

| | GPT high − low | Opus high − low |
|---|---|---|
| y (measured match), 39 arrays | +.007 [−.02, .04], r(low, high) = .94 | +.031 [−.03, .10], r = .61 |
| self-prediction S | +.024 [.009, .038] | **−.046** [−.064, −.029] |
| auditor prediction A (about this model) | +.039 [.021, .057] | **+.101** [.086, .115] |
| P(PLAY) | −.024 [−.07, .02] | +.006 [−.05, .07] |
| P1 D | +.001 [−.03, .03] | **−.089** [−.13, −.04], p = .0007 |
| \|S − y\| | −.036 [−.06, −.01] | +.050 [.00, .10] |
| 1b pooled Δ, 10 arrays / 7 families | −.034 [−.09, .02], p = .36 | |

**Caveats on the comparison:**
- The two settings differ in more than reasoning.
  - y comes from a different source: the low-reasoning y is the reused September frame calibration, while the high-reasoning y is fresh.
  - The auditor's description of the target changed with it.
  - Opus's low-reasoning arm was thinking-disabled; its high-reasoning arm is adaptive thinking at high effort. These are different modes, not two effort levels of one mode.
- The Opus P1 reversal combines two shifts:
  - Opus's self-predictions fell.
  - GPT's predictions about Opus rose by .10. The auditor prompt changed with it ("thinking turned on, effort set to high"), and GPT itself ran at high reasoning.

## Files

- `runs/{preflight,pilot,main}/*.csv`: every raw reply, reasoning summary, token count and cost
- `analysis/out_1a/`: results.json, item_table.csv, glmm_trials.csv, figures
- `analysis/out_1b/`: results.json, item_table.csv
- `analysis/out_compare/results.json`
- Deviation from the 1a audit's GLMM: profile CIs reported, the parametric-bootstrap CI omitted
