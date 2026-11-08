# Study 1 high-reasoning replication (1a + 1b) — complete battery

2026-10-09 · FROZEN `933aa87d` (`design/FROZEN.json`) · Amendment 1 (`design/AMENDMENT_1_resume.md`: budget only) · code `code/`.

The report written at the $150 cap stop is preserved unchanged as `RESULTS_incomplete_cap150.md`, with its outputs in `analysis/_incomplete_cap150/`. All new data live in this folder; nothing was written to the low-reasoning studies.

## Settings and wording (unchanged from the freeze)

| | GPT-5.5 | Claude Opus 5 |
|---|---|---|
| model returned | `gpt-5.5-2026-04-23` (dated snapshot) | `claude-opus-5` (alias; no dated snapshot exists) |
| settings | `reasoning.effort=high`, summary auto (preflight echoed "high") | adaptive thinking (display summarized), `output_config.effort=high`, max_tokens 16,000 |

Prompts are the frozen low-reasoning texts, with one exception:
- REF `d40ea45d`, PLAYPASS `3b5fe054` and SELFPRED `433b4569` are identical.
- AUDITOR (1a) and PRED (1b) are identical except the clause naming the target's configuration. It now reads "reasoning effort set to high" / "extended thinking turned on, effort set to high", so it describes the model actually being run.

Stimuli, balanced Latin-square orderings (new seeds), parsers, gates and exclusion rules are reused; no array was reselected.

## Collection, counts, total cost

| run | calls | parsed | transport fail | model mismatch | cost |
|---|---|---|---|---|---|
| preflight (12/12 passed) | 12 | 12 | 0 | 0 | $0.32 |
| parse pilot (all 12 cells 8/8; excluded from analysis) | 96 | 96 | 0 | 0 | $2.51 |
| main, original run (stopped at the $150 cap) | 6,879 | 6,879 | 0 | 0 | $146.39 |
| main, Amendment 1 resume (cap $184.22 = $149.22 + $35 authorised) | 1,337 | 1,337 | 0 | 0 | $22.17 |
| **total** | **8,324** | **8,324** | **0** | **0** | **$171.40** |

All 8,216 frozen main jobs are complete. Duplicates were checked by job_id: none (8,324 unique job_ids across 8,324 rows). The resume completed:
- Study 1a: F30_pairratio_m1 (152 jobs) and F40_crossang_m1 (97 outstanding).
- Study 1b: the 10 S3 controls (1,088 jobs). F29_arcdir_m1 and F32_tilt_m1 needed only predictions, because their REF draws were shared with Study 1a.

Costs use the pessimistic $5 / $30 per M rate for both providers; thinking and reasoning tokens are counted as output. The pilot-based projection ($137.6) underestimated the main run, because the pilot arrays needed less reasoning.

**Final counts**
- Study 1a: 41 arrays × 2 models, with 48 REF, 12 PLAYPASS, 8 SELFPRED and 8 reciprocal AUDITOR per model × array.
- Study 1b: 20 arrays × 4 predictor × target cells × 8 PRED, plus 48 REF per model × array.
- 55 arrays carry fresh REF draws. 6 arrays share them between the two studies (same prompt and settings).
- Exclusions under the frozen rules: none.

## Study 1a (41 arrays per model; y = fresh high-reasoning REF, 48/array)

| | GPT-5.5 high | GPT-5.5 low (ref.) | Opus 5 high | Opus 5 low (ref.) |
|---|---|---|---|---|
| mean y / self S / auditor A | .729 / .743 / .609 | | .841 / .619 / .719 | |
| **P1** D = \|A−y\| − \|S−y\| (+ = self better) | **+.009** [−.035, .053], p = .67 (Holm .67), 23+/18− | +.007, p = .77 | **−.055** [−.093, −.017], p = .005 (Holm .010), 12+/29− | +.033, p = .026 (Holm .052) |
| MAE self / auditor | .170 / .179 | .198 / .206 | .251 / .196 | .205 / .238 |
| P2 self: slope, mean signed error, Spearman | .27 [.17, .36], +.014 [−.05, .07], .74 | | .35 [.17, .52], −.222 [−.28, −.17], .57 | |
| P2 auditor: slope, mean signed error, Spearman | .37 [.23, .51], −.120 [−.18, −.07], .70 | | .25 [.11, .40], −.122 [−.18, −.07], .59 | |
| S1 GLMM play ~ y (primary per 1a audit), profile CI | 6.55 [4.41, 9.27] | | 11.27 [5.37, 20.44] | |
| S1 GLMM, adjusted for A | 2.49 [0.17, 4.91] | | 3.29, Wald [−1.10, 7.68] (profile CI failed) | |
| S1 GLM (population-averaged) | 4.92 [2.89, 7.64] | 5.10 | 4.71 [1.38, 8.19] | 5.39 |
| S ~ y adjusted for A | .14 [.04, .24] | | .07 [−.08, .26] | |
| overall P(PLAY) | .679 | | .833 | |
| S2 auditor, old HIGH − LOW | +.193 [.12, .27] | | +.121 [.06, .18] | |
| S4 legacy d′ / AUC / c | 1.46 / .94 / −.43 | 1.57 / .93 | 1.61 / .79 / −1.21 | 1.74 / .78 |

**GPT.** No self-over-auditor advantage, as at low reasoning. PLAY/PASS tracks measured agreement, and the association survives adjustment for the auditor's prediction (GLMM 2.49 [0.17, 4.91]).

**Opus.** The low-reasoning self-advantage (+.033, borderline after Holm) becomes an auditor advantage (−.055, Holm .010).
- Under high reasoning Opus underpredicts its own matching probability by .22 on average (.62 predicted vs .84 measured).
- PLAY/PASS tracks agreement (GLMM 11.27), but the association is not established after adjustment for the auditor's prediction, as at low reasoning.

Study 1a's S3 (the old-wording PLAY/PASS comparison) was not repeated; it concerned the low-reasoning legacy data only. (This is unrelated to the 1b S3 controls below.)

## Study 1b

**Primary sample.** These are the 10 arrays (strata S1, S2_G, S2_O) that were *selected for cross-model divergence under low reasoning* in the original screen. They are not necessarily divergent under high reasoning (see current divergence below); the selection was not redone. Scoring uses fresh high-reasoning REF draws.

| contrast | n | mean | 95% CI | p (sign-flip; exact) | + / − |
|---|---|---|---|---|---|
| **Pooled self − cross Brier advantage** | 10 arrays | **+.235** | [.127, .358] | .0024; exact .0020 | 10 / 0 |
| target GPT (Opus→GPT − GPT→GPT) | 10 | +.180 | [.062, .319] | .016 (Holm .016) | 9 / 1 |
| target Opus (GPT→Opus − Opus→Opus) | 10 | +.290 | [.132, .458] | .007 (Holm .014) | 8 / 2 |
| predictor main effect | 10 | +.055 | [−.040, .147] | .31 | 6 / 4 |
| target main effect | 10 | +.003 | [−.090, .106] | .95 | 4 / 6 |
| log score, pooled | 10 | +.360 | [.207, .537] | exact .0020 | 10 / 0 |
| family level | 7 families | +.212 | [.091, .357] | exact .016 | 7 / 0 |
| **S3 shared-policy controls, pooled** | 10 arrays | **−.0004** | [−.013, .010] | .94 | 5 / 5 |
| S3 target GPT / target Opus | 10 | +.059 / −.059 | [−.002, .126] / [−.115, −.003] | .13 / .074 | |

Cell mean Brier on the primary sample (lower is better):

| | GPT→GPT | GPT→Opus | Opus→GPT | Opus→Opus |
|---|---|---|---|---|
| Brier | .547 | .779 | .728 | .489 |

The self-advantage replicates under high reasoning (low reasoning: +.258). It is zero on the shared-policy controls (low reasoning: +.000).

**Current divergence under high reasoning** (descriptive; no reselection):
- On the primary sample, mean TVD between the two models' fresh REF distributions is .55 (low reasoning: .61).
  - 3/10 still meet their original stratum definition at the strict .75 cut: F10_curvature_m3 (S1), F12_mirror_m3 (S2_O), F27_linecount_m1 (S2_O).
  - On 3/10 the two models now share a modal shape (F12_mirror_m0, F12_mirror_m6, F31_overlap_m1).
  - All 10 still differ substantially (TVD .31–.75).
- All 10 S3 controls still meet their S3 definition (TVD mean .04; same modal shape on 10/10).

## Secondary: high vs low reasoning, paired by array

The paired change is reported two ways:
- **array-level**: the mean of per-array differences;
- **family-level**: the mean of per-family means, which weights each stimulus family equally.

The CI is a family-cluster bootstrap of the array-level mean. The p-value is a family-level sign-flip (exact for ≤ 16 families).

| | GPT high − low (41 arrays) | Opus high − low (41 arrays) |
|---|---|---|
| y (measured match) | +.017 [−.015, .049]; r(low, high) = .91 | +.032 [−.026, .092]; r = .62 |
| self-prediction S | +.024 [.010, .038], p .003 | **−.046** [−.063, −.029], p .0001 |
| auditor prediction A (about this model) | +.037 [.020, .055], p .0001 | **+.100** [.087, .113], p .0001 |
| P(PLAY) | −.026 [−.071, .014] | +.006 [−.047, .069] |
| P1 D | +.002 [−.026, .029], p .90 | **−.087** [−.129, −.044], p .0004 |
| \|S − y\| | −.029 [−.055, −.002] | +.046 [−.001, .096] |

In Study 1a every array belongs to its own family, so the array-level and family-level means coincide.

**Study 1b, 10 primary arrays (7 families):**

| | low | high | array-level change | family-level change | CI (array mean, family-cluster) | family sign-flip p |
|---|---|---|---|---|---|---|
| pooled Δ | .258 | .235 | **−.023** | −.034 | [−.085, .025] | .36 (exact) |
| Δ target GPT | .216 | .180 | −.036 | −.041 | [−.114, .038] | .38 |
| Δ target Opus | .299 | .290 | −.009 | −.028 | [−.091, .029] | .84 |
| TVD between models | .610 | .550 | −.060 | −.048 | [−.095, .008] | .22 |

**Why −.034 and not −.023.** The headline means differ by .2350 − .2577 = **−.023**. Because the same 10 arrays are paired, this equals the array-level mean of the per-array changes exactly.

The −.034 reported earlier is the family-level mean: each of the 7 families' mean change, averaged with equal weight.
- **F12_mirror** contributes 3 arrays with changes of +.106, +.046 and −.060 (family mean +.031). Its weight falls from 3/10 to 1/7.
- **The single-array families** each get 1/7, including F27_linecount (−.175), F20_corner (−.086) and F30_pairratio (−.068).

Giving equal weight to the families with mostly negative changes moves the mean from −.023 to −.034.

The earlier summary printed the family-level mean as "diff" next to a CI and p-value computed for different quantities. It is corrected here; both are now reported and labelled. Neither changes the conclusion: there is no detectable change in the 1b self-advantage with reasoning setting.

**Caveats on the comparison:**
- Low and high differ in more than reasoning.
  - The source of y changed: low = reused September frame calibration, high = fresh REF.
  - The auditor's description of the target changed with the setting.
  - Opus's low arm was thinking disabled and its high arm is adaptive thinking at high effort, so these are different modes, not two effort levels of one mode.
- The Opus P1 reversal combines two shifts:
  - Opus's self-predictions fell by .046.
  - GPT's predictions about Opus rose by .100, under a changed configuration clause and with GPT itself at high reasoning.

## Files

- `runs/{preflight,pilot,main}/*.csv`: every raw reply, reasoning summary, token count and cost.
  - Original main run: `main_20261009_165940.csv`
  - Amendment 1 resume: `main_20261009_182002.csv`
- `analysis/out_1a/`: results.json, item_table.csv, glmm_trials.csv, figures
- `analysis/out_1b/`: results.json, item_table.csv
- `analysis/out_compare/results.json`: contains both `mean_array` and `mean_family`
- Deviation from the 1a audit's GLMM: profile CIs reported, the parametric-bootstrap CI omitted
