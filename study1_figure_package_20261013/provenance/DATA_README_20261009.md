# Study 1 figure data (2 × 3: GPT-5.5 | Claude Opus 5 | Qwen)

Built 2026-10-09 by `code/export.py` from raw run files; no API calls. Every frontier value was cross-checked against each study's own item table; the maximum absolute difference is 5e-5, which is the item tables' 4-decimal rounding (`data/panel_summary.json → cross_checks`).

## Top row — reliability curves: `data/reliability_items.csv`

One row per model × setting × sample × item.
- **x** = measured agreement.
- **y** = P(PLAY) from the symmetric reliability judgement (`n_play / n_judgements_parsed`).
- Where they exist, the row also carries calibration data: mean self-predicted and auditor matching probability, with their counts.

| column | setting | sample | sample_type | items | x estimand / source | judgements | calibration |
|---|---|---|---|---|---|---|---|
| GPT-5.5 | low (effort low) | frontier Study 1a, all 41 VIS-FRAME arrays | observational | 41 | independent-order match, 4 options; **reused frame calibration**, 48/array | 492/492 parsed | self 328, auditor (Opus) 328 |
| GPT-5.5 | high (effort high) | same 41 arrays | observational | 41 | same estimand; **fresh REF**, 48/array | 492/492 | self 328, auditor (Opus high) 328 |
| Claude Opus 5 | low (thinking disabled) | same | observational | 41 | reused frame calibration, 48/array | 492/492 | self 328, auditor (GPT) 328 |
| Claude Opus 5 | high (adaptive, effort high) | same | observational | 41 | fresh REF, 48/array | 492/492 | self 328, auditor (GPT high) 328 |
| Qwen step-316 | thinking off | Study 1: top/bottom 15 of 100 trained scenarios | **observational, extreme-group selected; truth = selection data** | 30 | same-presentation within-pair agreement, 2 options, mean of 5 fixed pairs × 40 draws | 589/600 | none exists |
| Qwen replica 12f8e1b3 (baseline step 316) + continuations V1/V2 (step 157) | thinking off | counterbalanced continuation experiment: 100 trained scenarios (clean vs 70/30 targets; V1/V2 swap halves) + 50 untrained, 4 items each | **intervention (counterbalanced continuation)** | 600 items × 2 orders × 3 checkpoints = 3,600 rows | **sampled** same-order agreement over underlying options, 20 draws per item × order × checkpoint (71,986 valid draws) | 13,928/14,400 valid (4 per cell) | none exists |

Notes:
- The `group` column holds:
  - for frontier rows, the old HIGH/LOW/MID labels;
  - for Qwen Study 1, HIGH/LOW;
  - for the α rows, the condition.
- Continuation rows carry `checkpoint` (baseline / V1 / V2), `sampler`, `assignment` (CLEAN / NOISY / untrained / pre-continuation baseline), `order` (canonical / swapped), `provenance`, `half` and `family` (= scenario). Agreement and PLAY are per item × order × checkpoint; the PLAY/PASS prompt is the Study 1 prompt.
- The two Qwen samples (observational Study 1 on step-316; continuation intervention on replica 12f8e1b3) are different models and item sets. Plot them as separate series; do not pool them.
- **α adapter scaling is EXPLORATORY** and is no longer in the main export. It is in `data/reliability_items_qwen_alpha_EXPLORATORY.csv` (analytic, not sampled, agreement; generic decisiveness manipulation).
- Qwen x values are 2-option agreements (chance .5); frontier x values are 4-option (chance .25). Put both on the same "measured matching probability" axis only with this stated in the caption.

## Bottom row — option-choice self advantage

- **`data/crossed_prediction_cells.csv`**: one row per setting × array × predictor × target. It gives the number of parsed predictions, mean and SD Brier (expected Brier against the target's fresh REF distribution; lower is better), mean log score, number of scoring draws, and the target distribution.
- **`data/self_advantage_items.csv`**: one row per setting × array. It gives D_pooled = ½[(B_O→G + B_G→O) − (B_G→G + B_O→O)] and the target-specific D. It also gives the current divergence: TVD, modal shares and whether the modal shape is shared.
- **Coverage:** 20 arrays × 2 settings (low = original 1b; high = Study 1 high-reasoning replication).
  - Sample "primary" = the 10 arrays **selected for cross-model divergence under low reasoning** (S1, S2_G, S2_O). They are not necessarily divergent now: under high reasoning only 3/10 still meet their original stratum definition.
  - "S3" = the 10 shared-policy controls.
- **Qwen:** crossed study step-316 × untuned base (`~/Desktop/Superrationality/Stag/qwen_crossed_prediction_20261009`, RESULTS.md); 20 items (10 selected for divergence on the selection draws + 10 shared-choice controls), 2 options, thinking off.
- **`data/crossed_prediction_cells_all.csv`**: frontier (low, high) and Qwen cells in one long table, with `n_options`.
- **`data/self_advantage_by_column.csv`**: one row per figure column × setting × item. `D_self_target` = (comparator → column model) − (column model → itself), the column's target-specific self-advantage; `D_pooled` = the study's pooled contrast. Comparators: GPT column ← Claude Opus 5; Claude column ← GPT-5.5; Qwen column ← untuned base Qwen.

## Annotation numbers: `data/panel_summary.json`

These are copied from each study's results files, not refit:
- frontier 1a: P1 and P2 (both settings), and the GLMM output (low from the audit, high from the replication);
- frontier 1b: primary and S3 contrasts (both settings);
- Qwen Study 1: d′, AUC, r and denominators;
- the Qwen α full-study result.
