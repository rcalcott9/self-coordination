# Study 1 frontier minimal: analysis audit and corrections log

Audit date: 2026-10-07. Analysis only: no new calls, no added samples. The original outputs are untouched: `results.json`, `item_table.csv`, the figures, `code/analyze.py`, and `SUMMARY_v1.md` / `Study1_frontier_results_v1.pdf` in Downloads.

The audit ran in four parallel workstreams. Scripts and outputs are in `analysis/audit/{A_bootstrap, B_ordering_multiplicity, C_glm, D_drift}/`.

## Verdict

- **No conclusion changes.**
- **One stated rationale was wrong (the GLM substitution).**
- **Several items needed relabelling:**
  - p-values reported as 0;
  - "no drift" wording;
  - definitive-null wording;
  - the multiplicity family, which was ambiguous.

The Opus self-advantage is borderline (Holm p ≈ .05) and is not established.

## A. Agreement estimation, bootstrap bias, test and CI definitions

| Check | Finding | Correction |
|---|---|---|
| y estimator | Unbiased dyadic `within_model_match` on 48 draws for every model × array. It recomputes from the raw frame CSV, maximum gap 4.7e-5 (rounding). | None |
| Where bootstrap y* is centred | y* centres on the plug-in Σp̂², offset exactly (1 − Σp̂²)/47. Mean offset: GPT +.006, Opus +.004 (maximum .015). | Documented |
| Bias in statistics | Mean signed error is biased by −.004 to −.006 (CI widths .12–.14). Slopes ≤ .005. Mean D: GPT +.002, Opus −.0005. | Documented; negligible |
| Two-stage bootstrap | Within-array resampling double-counts noise, so the CIs are conservative. SD of mean D is 5% wider for GPT and 19% wider for Opus than an array-only bootstrap. | Labelled conservative; pre-specified version kept as primary |
| P1 CI, sensitivity variants | GPT [−.039 to −.048, +.055 to +.059]: always includes 0. Opus lower bound +.0004 to +.007: always near 0. | Opus lower bound described as ≈ 0 |
| P1 test vs CI | The sign-flip test treats D as fixed; the CI includes calibration noise. A calibration-aware sign-flip gives Opus p = .022 (post hoc). | Mismatch documented; frozen test remains primary |
| p-values reported as 0 | P2 Spearman p was printed as 0.0. Recomputed with (k+1)/(N+1): GPT self .0010, GPT auditor .0015, Opus self .0005, Opus auditor .0005. | Reported as ≤ .001 / .0015 |
| Holm implementation | Correct step-down procedure. | None |
| S2 CI | An initial version resampled repeats only (too narrow). It was replaced *before reporting* by a version that resamples arrays within each arm. Reported values: GPT [.078, .248], Opus [.059, .179]. | Logged |

## B. Ordering, data inclusion, multiplicity

| Check | Finding | Correction |
|---|---|---|
| Executed vs frozen orderings | Exact match in all 348 cells (preflight 8, pilot 48, anchor 328, main 2,296 rows). | None |
| Slot balance | Exact everywhere: PLAYPASS 3×, SELFPRED and AUDITOR 2×, anchor 1×. Displayed order matches the manifest; stimulus and prompt hashes match. | None |
| Data inclusion | `analyze.py` reads only `runs/main`, so the pilot is excluded and the anchor unused. The calibration source sha256 matches FROZEN. | None |
| Position effects (exploratory) | PLAY/PASS: none (p = .65 / .26). Opus self-prediction: small slot effect (p = .015, about 2 pp). None of the 12 tests survives correction. Balance keeps slot independent of y. | Reported as exploratory |
| Plan timing | The plan was final at 21:14. FROZEN.json was written at 21:19 and main data at 21:37–21:43. The plan was never hash-frozen or referenced in FROZEN.json. | **Provenance gap.** The plan is now hashed retrospectively (below) and labelled as such |
| Multiplicity family | The plan says "Holm across P1 and P2 × 2 models", but P2 was defined without a test. The analysis used a family of 6. Opus P1 Holm p is about .05 under every reading of the family: {P1×2}, {P1×2 + P2-self}, {P1 + one P2 per model}, {6}. Values range .051–.054 across permutation seeds with (k+1)/(N+1). | Reported as "Holm p ≈ .05; robust to family definition" |

## C. GLM substitution (S1)

- **Planned:** trial-level random-intercept logistic model, PLAY ~ y (+ A) + (1 | array).
- **First report:** an array-level binomial GLM, i.e. pooled logistic regression on proportions with weight 12, with hierarchical-bootstrap CIs.
- **The stated reason was wrong.** The report claimed the GLMM was "unstable because arrays sit at 0/12 or 12/12". That was never tested, and it is false.

On audit (lme4 1.1.35.5):

| Model | GLMM slope on y | 95% CI | Random-intercept SD | Fit |
|---|---|---|---|---|
| GPT, PLAY ~ y | 6.09 | profile [4.28, 8.24] | 1.11 | clean |
| GPT, PLAY ~ y + A | **3.73** | profile [2.17, 5.48] | 0.68 | clean |
| Opus, PLAY ~ y | 10.20 | profile [4.95, 17.61] | 3.51 | clean |
| Opus, PLAY ~ y + A, standardised | **3.81** | parametric bootstrap [−2.30, 9.43] | 2.62 | clean (the raw-scale fit failed to converge because of predictor scaling, not 0/12 arrays) |

- **Different quantities:** GLMM slopes are conditional on an array's random intercept; the GLM slope is averaged over arrays and shrinks accordingly (GPT 6.09 → about 5.1, which matches the GLM's 5.10).
- **GLM uncertainty:** overdispersion is 1.7–5.3, so model-based GLM standard errors would be far too narrow. They were never used; the bootstrap CIs are valid and slightly conservative. Bootstrap medians sit within about 0.1 of the point estimates, and there were no separation failures.
- **Conclusion is unchanged:** GPT's adjusted slope excludes 0, and Opus's includes 0, under every valid method.
- **Correction:** the GLMM is now the primary S1 estimate, and the GLM is kept as a population-averaged sensitivity analysis.

## D. Calibration drift gate

- **Re-derived:** p = .954 / .941 (the reported values).
- **Why the observed fit sits above the null median:** smoothing at α = .5 gives every never-chosen option about 1% mass. The null therefore expects about 2.9 (GPT) or 3.6 (Opus) picks of such options. 0 (GPT) and 1 (Opus) occurred.
- **The test is conservative:** its simulated false-alarm rate is about 0.
- **Deviation from the frozen design:** the gate text says "parametric draws", but the implementation draws a distribution per array and then the choices (posterior-predictive). The plug-in variant reaches the same decision.

Power at p < .01, by simulation (500 per cell):

| Drift alternative | GPT | Opus |
|---|---|---|
| 10% of choices replaced by random picks | .34 | .48 |
| 20% or more replaced | ≥ .99 | ≥ .99 |
| Favourite swapped on 10% of arrays | .63 | .80 |
| Favourite swapped on 25% or more of arrays | 1.00 | 1.00 |
| Concentration change, favourite kept (τ = 0.5 / 2) | .09 / .00 | .00 / .00 |

**Supplementary, not pre-specified:** anchor–frame cross-match minus frame within-match is GPT +.006 [−.015, +.025] and Opus +.001 [−.023, +.024]. That is inconsistent with average matching shifts of about ±.04.

## Wording corrections applied in SUMMARY v2

| v1 wording | v2 wording |
|---|---|
| "no drift" / "drift check passed" | "the pre-specified drift test did not detect drift (p = .95/.94). It is conservative, with high power against broad randomisation or favourite changes and almost none against concentration-only change. Drift on individual arrays, and average matching shifts smaller than about ±.04, cannot be excluded. Opus weights identity is not verifiable." |
| "GPT-5.5 shows no self-prediction advantage" | "no self-prediction advantage was detected for GPT-5.5. The 95% CI [−.041, +.059] is compatible with small advantages or disadvantages of up to about 5–6 points of absolute error." |
| "Opus shows a small self-advantage, but it is not significant after correction" | "for Opus 5 the point estimate favours self (+.033; unadjusted CI lower bound ≈ 0). Holm p ≈ .05, so the advantage is borderline and not established." |
| "Neither model: self-predictions carry no reliable information beyond the auditor" | "no information beyond the auditor's prediction was detected (CIs include 0)." |
| S1: "For Opus it does not [survive adjustment]" | "for Opus the adjusted association is not established (GLMM 3.81, 95% CI [−2.30, 9.43])." |
| P2 "p = 0" | "p ≤ .001" (GPT auditor .0015) |
| S1 GLM given as primary, with an untested instability claim | GLMM primary; the GLM substitution is explained and corrected |

## Retrospective hashes (recorded 2026-10-07, after data)

See `analysis/audit/RETRO_HASHES.txt`.
