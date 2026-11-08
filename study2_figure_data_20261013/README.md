# Study 2 figure inputs (primary configurations)

Built 2026-10-13 by `code/export.py` from the raw run files. **No API calls.** The script checks every table against the frozen reports and the current figure tables before writing anything. Rebuild with `~/.venvs/research/bin/python code/export.py`.

**Primary configurations:**
- GPT-5.5 at effort low.
- Claude Opus 5 with adaptive thinking at effort low.
- Qwen step-316 with thinking off, **run B** (`plunkett_qwen/results/s2_20260912_181428`, symmetric wording).

Run A, GPT at effort high, Opus at adaptive high and the Opus thinking-disabled cell are not included.

## PLAY/PASS partner 2×2 (figure panels a–c)

| file | one row per | contents |
|---|---|---|
| `data/playpass_items_long.csv` | model × item × partner (180) | item/scenario ID, family, agreement, group (HIGH/LOW; `group_label` gives CLEAR/WEAK for Qwen), partner, attempted / transport-ok / parsed / PLAY counts, P(PLAY), source file |
| `data/playpass_items_paired.csv` | model × item (90) | COPY and DIFFERENT counts side by side and `partner_shift` = P(PLAY \| COPY) − P(PLAY \| DIFFERENT); keeps each item's pairing |
| `data/playpass_qwen_option_pairs.csv` | Qwen scenario × option pair × partner (300) | the within-scenario sampling unit (5 fixed pairs × 4 samples) |
| `data/playpass_cells.csv` | model × group × partner (12) | the plotted cell P(PLAY) and 95% CI, with the CI method |
| `data/playpass_contrasts_harmonised.csv` | model × contrast (18) | partner, policy and interaction contrasts under one method, with p values and tests |
| `data/playpass_contrasts_frozen.csv` | model × contrast (12) | the frozen-report values, each with its **original** resampling method and source |
| `data/model_configs.csv` | model (3) | model ID requested and returned, API, reasoning/thinking setting, temperature, max tokens, system prompt, prompt hashes, run directories, trials per cell, item set, agreement source |

**Counts.**
- GPT and Opus: 20 attempted per item × partner, all parsed (300 per class × partner cell).
- Qwen run B: 20 attempted per scenario × partner. Parsed 298 / 295 / 296 / 297 (CLEAR-COPY, CLEAR-DIFF, WEAK-COPY, WEAK-DIFF), 1,186 of 1,200.
- Unparsed rows are counted in `n_attempted` and excluded from P(PLAY), as in the frozen analyses.

**Agreement and group.** Group labels were frozen before any PLAY/PASS call.
- GPT: independent-order copy agreement, 48 frame draws at effort low.
- Opus: the same estimand, measured **with thinking disabled**, not in the adaptive configuration used for the 2×2. Relabelling by adaptive Stage A agreement moves no item (sensitivity, `paper_assembly_20261010`).
- Qwen: Study 1 selection draws, 40 per option pair. The same draws define the classes.
- Qwen agreements are over 2 options (chance .5); GPT and Opus agreements are over 4 (chance .25).

**Means and CIs.**
- `playpass_cells.csv` holds the values plotted in the current figure: P(PLAY) pools parsed trials, with an item-cluster percentile bootstrap within class × partner (10,000 resamples, seed 20261010; for Qwen the cluster is the scenario).
- The harmonised contrasts use a paired item-cluster bootstrap that keeps each item's COPY and DIFFERENT cells together. Their point estimates reproduce the frozen reports.
- The frozen CIs used different methods:
  - GPT: item-paired bootstrap.
  - Opus: **unpaired** item bootstrap. This is why its frozen partner CI [.025, .292] is wider than the paired [.097, .218].
  - Qwen: scenario-cluster bootstrap.

  Report the frozen ones as primary. `playpass_contrasts_frozen.csv` lists each method next to its value.

## Relational G (figure panel d)

| file | contents |
|---|---|
| `data/relational_G_items.csv` | 11 items × 2 focal models: G, the four TVDs, Brier COPY→SELF and DIFFERENT→OTHER, modal masses, family |
| `data/relational_G_summary.csv` | G with its CIs under each resampling scheme, labelled by status |

| focal | G | item-clustered CI (frozen) | **family-clustered CI** | F10 collapsed, 6 family means (sensitivity) |
|---|---|---|---|---|
| GPT-5.5, effort low | +.021 | [−.015, .046] | **[−.037, .043]** | +.002 [−.056, .040] |
| Opus 5, adaptive low | −.000 | [−.056, .064] | **[−.026, .039]** | +.002 [−.020, .031] |

- **Family-clustered CI:** resamples the 6 stimulus families, pools the items of the drawn families and takes the item mean (4,000 resamples, seed 8). This is the `report_study2.py` function; the export reruns it and reproduces the reported values.
- **Status:** `RESULTS.md` reports the family-clustered CI next to the frozen primary, but the methods draft classes it as a sensitivity that was not planned in advance.
- **Current figure:** panel d plots the item-cluster CI and the **F10-collapsed family-means** CI, recomputed under numpy seed 20261010. It does **not** plot the family-clustered CI of the 11-item mean. Those rows are labelled in the summary file.

## Plotting script

`code/plot_study2_CURRENT_study2_freeze.py` is a verbatim copy of `paper_assembly_20261010/code/study2_freeze.py`, the script that builds `figures/fig_study2.{pdf,png}`. It reads the raw files listed above, not this folder.
