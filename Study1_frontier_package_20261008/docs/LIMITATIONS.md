# Limitations

## Both studies

1. **Opus identity.** `claude-opus-5` is an alias with no dated snapshot, so weights identity is certified only to the alias on each run date. GPT used a dated snapshot.
2. **Two models, one configuration each.** Results apply to GPT-5.5 with reasoning effort low and Opus 5 with thinking disabled. Other settings were not tested.
3. **Stimulus battery.** All arrays come from one existing four-option visual battery. Divergent policies are rare in it.

## Study 1

4. **Plan provenance.** The analysis plan was final before data collection (21:14 vs 21:37) but was never hash-frozen. It was hashed retrospectively after the data were in.
5. **Calibration drift test.** The drift test is conservative: simulated size is about 0. It had high power against broad randomisation and favourite changes, and almost none against concentration-only change. Drift on individual arrays, and average shifts smaller than about ±.04 in matching level, cannot be excluded.
6. **Uncertainty model.** The two-stage bootstrap double-counts within-array noise, so CIs are conservative (5–19% wider than an array-only bootstrap). The sign-flip test treats per-array D as fixed, while the CI includes calibration noise.
7. **Opus P1 is borderline.** Holm p ≈ .05 under every definition of the test family. It is not established.
8. **The S1 estimator was substituted in v1.** That report used a pooled GLM on an untested claim that the planned GLMM was unstable. On audit the GLMM fit, and it is now the primary S1 estimate; conclusions were unchanged. The GLM-bootstrap diagnostic table in the audit was produced inline and has no packaged script (see the README).
9. **PLAY/PASS construct.** "Reliable" is undefined in the prompt, so PLAY/PASS is analysed as a graded relation. There is no lottery anchor.
10. **Auditors.** Each auditor is a single other model, so auditor predictability is a proxy for externally legible information, not a measure of salience.

## Study 1b

11. **Small primary sample.** 10 arrays against a planned 22–32. Power at the frozen assumptions was .28–.45 for δ = .05; the observed effect was far larger.
12. **S1 depends on the fallback.** 3 of the 5 S1 arrays entered under the pre-registered ≥ .70 threshold.
13. **Family clustering.** There are 7 independent families. F12_mirror contributes 3 arrays and F10_curvature 2. The family-level analysis (exact p = .031) has a minimum attainable p of .016.
14. **Construct.** The primary contrast measures predictive self-advantage. It cannot separate self-projection from relational self-knowledge. The projection diagnostic is post hoc and exploratory.
15. **Moderation is built into the design.** The S3 vs S1 strata make the slope on distance largely mechanical.
