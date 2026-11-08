# Study 1 (frontier, minimal): results (v2, corrected after analysis audit)

v2 changes wording and the S1 estimator only; no data or primary numbers changed. The full corrections log is in `ANALYSIS_AUDIT.md`. v1 is preserved as `SUMMARY_v1.md`.

Collected 2026-10-07/08 · GPT-5.5 (`gpt-5.5-2026-04-23`, reasoning effort low) and Claude Opus 5 (`claude-opus-5`, thinking disabled) · all 41 VIS-FRAME-41 arrays · frozen design `18853f3e`.

## Bottom line

- **No self-prediction advantage was detected for GPT-5.5.** Mean advantage +.007, 95% CI [−.041, +.059], 22 of 41 arrays favour self, p = .77. The CI is compatible with small advantages or disadvantages of up to about 5–6 points of absolute error, so this is not evidence of equal accuracy.
- **For Opus 5 the self-advantage is borderline and not established.** The point estimate favours self: +.033, unadjusted CI [+.003, +.065] with lower bound ≈ 0 across bootstrap variants. 27 arrays favour self vs 13 against; sign-flip p = .026; Holm p ≈ .05 (.051–.054 across permutation seeds, robust to how the test family is defined).
- **The upward trends are not evidence of privileged self-knowledge.** Self-predictions and auditor predictions track actual matching about equally well (Spearman: GPT .55 vs .51; Opus .65 vs .64).
- **The old HIGH/LOW split is confounded with externally legible information.** Auditors predict higher matching for old HIGH than old LOW arrays: GPT +.16 [+.08, +.25], Opus +.12 [+.06, +.18].
- **Corrected PLAY/PASS tracks actual matching for both models.** For GPT the association remains after adjusting for the auditor's prediction (GLMM 3.73 [2.17, 5.48]). For Opus the adjusted association is not established (GLMM 3.81 [−2.30, 9.43]).

## Collection and integrity

| Stage | Calls | Parsed | Model mismatches | Cost |
|---|---|---|---|---|
| Preflight | 8 | 8 | 0 | $0.06 |
| Parse pilot (excluded from analysis) | 48 | 48 | 0 | $0.40 |
| Calibration drift check | 328 | 328 | 0 | $2.30 |
| Main: PLAY/PASS 984, self-prediction 656, auditor 656 | 2,296 | 2,296 | 0 | $20.84 |
| **Total** | **2,680** | **2,680** | **0** | **$23.60** |

- **Calibration:** reused from the frame run (48 draws per array, prompt `d40ea45d`, same settings).
- **Drift check:** the pre-specified test did not detect drift (p = .95 / .94), so calibration was reused under the frozen rule. The test is conservative. It had high power against broad randomisation (≥ .99 at 20% or more of choices replaced) and against favourite changes on a quarter or more of arrays (1.00), but almost none against changes in concentration with the favourite unchanged (≤ .09). A supplementary comparison rules out average matching shifts of about ±.04 or larger. Drift on individual arrays cannot be excluded, and Opus weights identity is not verifiable (alias).
- **Shape order:** every new prompt states that left-to-right order is randomized independently for each player. Shape orders were balanced Latin squares: each shape appeared in each slot equally often.
- **Old PLAY/PASS data:** preserved untouched and recorded by hash.

## Primary results

Each analysis uses array as the unit, with 95% CIs from a hierarchical bootstrap (B = 2,000). The bootstrap resamples arrays with pairing kept, then within each array resamples the 48 calibration draws and the self, auditor and PLAY/PASS repeats.

### P1. Self vs auditor accuracy (key test)

The paired difference is D = |auditor − actual| − |self − actual|, so D > 0 means the self-prediction was closer.

| | GPT-5.5 | Claude Opus 5 |
|---|---|---|
| Mean D [95% CI] | +.007 [−.041, +.059] | +.033 [+.003, +.065] |
| Arrays D > 0 / = 0 / < 0 | 22 / 0 / 19 | 27 / 1 / 13 |
| Sign-flip p (raw → Holm) | .77 → .77 | .026 → .052 |
| Mean absolute error, self vs auditor | .198 vs .206 | .205 vs .238 |

GPT shows no self-advantage. For Opus the point estimate is small and positive (about 3 percentage points of absolute error), but it is not significant after Holm correction. The per-array differences are noisy in both directions (Figure 2).

### P2. Calibration of each predictor against actual matching

| | GPT self | Auditor of GPT (Opus) | Opus self | Auditor of Opus (GPT) |
|---|---|---|---|---|
| Slope [95% CI] | .15 [.06, .24] | .28 [.12, .42] | .35 [.20, .51] | .26 [.14, .38] |
| Intercept | .61 | .37 | .38 | .41 |
| Mean signed error | +.006 [−.07, +.07] | −.14 [−.22, −.08] | −.14 [−.20, −.09] | −.19 [−.25, −.13] |
| Spearman | .55 | .51 | .65 | .64 |

All four Spearman correlations are positive (permutation p ≤ .001, GPT auditor .0015; all survive Holm). That is expected for any informed predictor and is not evidence of self-knowledge on its own.
- **GPT's self-predictions** are nearly flat: about .65 at the low end and .76 at agreement 1.0. They are right on average, but they hardly discriminate, with a shallower slope than the auditor's.
- **Both auditors and Opus's self-predictions** underpredict matching on average.
- **Self and auditor predictions are strongly correlated** with each other: r = .64 for GPT, .79 for Opus.

## Secondary results (exploratory)

### S1. Corrected PLAY/PASS

| | GPT-5.5 | Claude Opus 5 |
|---|---|---|
| Overall P(PLAY) | .71 | .83 |
| Spearman, P(PLAY) vs actual matching | .75 | .49 |
| Logit slope on actual matching [95% CI] | 5.1 [2.9, 8.0] | 5.4 [2.5, 9.7] |
| Slope adjusted for auditor prediction | **3.3 [1.5, 6.1]** | **2.8 [−1.1, 8.0]** |
| **GLMM, pre-specified (primary): slope on y** | 6.09 [4.28, 8.24] | 10.20 [4.95, 17.61] |
| **GLMM: slope on y adjusted for A** | **3.73 [2.17, 5.48]** | **3.81 [−2.30, 9.43]**, standardised predictors, parametric bootstrap |
| Self-prediction on actual, adjusted for auditor (OLS) | .08 [−.01, +.17] | .13 [−.02, +.33] |

- **GPT:** PLAY tracks its own matching probability beyond what the auditor can predict.
- **Opus:** the adjusted association is not established; its CI includes 0 under both the GLMM and the GLM.
- **Neither model:** no information in self-predictions beyond the auditor's prediction was detected (CIs include 0).
- **Opus is bimodal on low-agreement arrays.** It passes almost always on six (F05_orient_m3, F11_noise_m3, F37_mirroraxis_m1, F12_mirror_m3, F41_contain_m1, F35_gradang_m1) and plays almost always on the rest. Its PLAY choices line up with its own low self-predictions on those six, but the auditor's predictions are also low there.

### S2. Auditor predictions on the old HIGH/LOW split

| | GPT-5.5 | Claude Opus 5 |
|---|---|---|
| Auditor prediction, old HIGH vs LOW | .64 vs .48 | .66 vs .54 |
| Difference [95% CI] | +.16 [+.08, +.25] | +.12 [+.06, +.18] |
| Actual matching, old HIGH vs LOW | .99 vs .43 | 1.00 vs .52 |

The old arms differ in externally legible predictability, so the original HIGH/LOW PLAY/PASS contrasts were not salience-controlled.

### S3. Old vs corrected PLAY/PASS on the 30 old items (descriptive; wording change only)

| | GPT-5.5 | Claude Opus 5 |
|---|---|---|
| P(PLAY), old → corrected | .64 → .67 | .81 → .79 |
| Spearman with actual matching, old → corrected | .64 → .75 | .59 → .63 |
| Old P(PLAY) vs same-order matching (re-scored) | .57 | .46 |

Correcting the shape-order statement left PLAY rates about the same and made them track actual matching slightly more closely for both models. This is not a controlled comparison: the runs were on different dates, with different reps and orderings.

### S4. Legacy metrics on the corrected data (for comparability only)

| | GPT-5.5 (old run) | Claude Opus 5 (old run) |
|---|---|---|
| P(PLAY), HIGH / LOW | .92 / .43 (.83 / .45) | .98 / .61 (.96 / .66) |
| d′ | 1.57 (1.08) | 1.74 (1.32) |
| AUC | .93 (.87) | .78 (.77) |
| Criterion c | −.60 (−.40) | −1.14 (−1.07) |

The Opus HIGH set comes from an undocumented tie-break among 21 arrays at agreement 1.000.

## Figures

All figures are in `Study1_frontier_results/` as PDF and PNG, 5.5 × 3.2 in at 300 dpi.

1. **`fig1_calibration`:** mean predicted vs measured matching probability, by model. Filled circles are self-predictions; open squares are reciprocal-auditor predictions. A grey segment joins each array's pair. The solid black line is y = x. Fitted calibration lines are solid for self and dashed for auditor, with dotted 95% bootstrap bounds. Thin capped bars are per-array 95% intervals: horizontal for calibration uncertainty, vertical for prediction uncertainty. n = 41 arrays per panel, 8 predictions per array, 48 calibration draws.
2. **`fig2_paired_error`:** per-array self-prediction advantage D, ordered by D, with 95% hierarchical-bootstrap intervals. The solid line is 0. The dashed line and the diamond at the right are the mean D and its 95% CI, resampling arrays with pairing preserved and including calibration uncertainty.
3. **`fig3_playpass`:** proportion choosing PLAY (12 per array, Wilson 95% intervals) vs measured matching probability, with the fitted logistic curve and dotted 95% bootstrap bounds. Colour (cividis) shows the auditor-predicted matching probability for description only. Statistical adjustment is in S1.
4. **`figS3_old_vs_corrected`:** item-level P(PLAY) under the old vs corrected wording on the 30 old items. Filled circles are old HIGH arrays; open squares are old LOW. Descriptive only.

## Notes and deviations

- **Bootstrap:** the two-stage design double-counts within-array noise, so CIs are conservative: SD of mean D is 5% wider for GPT and 19% wider for Opus. Bias is negligible (mean D shifts by ≤ .002). Array-only and bias-corrected variants give the same conclusions.
- **Ordering:** executed orderings match the frozen schedule exactly in all 348 cells, with exact slot balance.
- **Plan provenance:** the analysis plan was final before data (21:14 vs 21:37) but was never hash-frozen. It was hashed retrospectively after the data; see the audit.

- **S1 model (corrected):** S1 was pre-specified as a random-intercept GLMM. v1 substituted an array-level binomial GLM with hierarchical-bootstrap CIs, on the claim that the GLMM was unstable. That claim was untested, and on audit it was false: the GLMM fits, the Opus adjusted model after standardising predictors. GLMM estimates are now primary. The GLM rows (slopes averaged over arrays, hence smaller) are kept as a sensitivity analysis. Conclusions are unchanged.
- **Permutation p-values:** computed as (k+1)/(N+1). v1 printed 0.0 for P2.
- **Auditor framing:** auditor predictions are a proxy for externally legible information, not a measure of salience. Each auditor is a single other model, so "auditor" here means that model's view.
- **Files:** `item_table.csv` has every array (actual, self, auditor, D, PLAY rate, old PLAY rate, same-order match). `results.json` has all statistics. Code is `code/analyze.py` in the study folder.
