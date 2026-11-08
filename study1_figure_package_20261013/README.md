# Study 1 figure package (2026-10-13)

The current Study 1 figure (2 × 3), its plotting script, the exact input files that script reads, and the annotation JSON. Assembled from existing outputs only; no API calls and no new analysis. Raw traces are not included because the plotting script does not read them.

## Regenerate

From this folder (Python 3.12, matplotlib 3.11.1, pandas 2.3.3, numpy 2.4.6, statsmodels 0.14.6):

```
MPLCONFIGDIR=$PWD/mplconfig ~/.venvs/research/bin/python paper_assembly_20261010/code/fig_study1.py
```

- `MPLCONFIGDIR` points matplotlib at the bundled `academic` style (`mplconfig/stylelib/academic.mplstyle`). Without it the script uses the copy in `~/.matplotlib/stylelib/`.
- The script is unmodified. It resolves its inputs relative to itself, which is why the original folder layout is kept.
- It writes `paper_assembly_20261010/figures/fig_study1_2x3.{pdf,png}` and `paper_assembly_20261010/tables/fig_study1_bottom_row_summary.json`. It is deterministic (seed 20261010).
- **Verified 2026-10-13 in a clean copy:** the PNG and JSON are byte-identical. The PDF differs only in its embedded `/CreationDate`.

## Contents

| path | role |
|---|---|
| `paper_assembly_20261010/figures/fig_study1_2x3.pdf`, `.png` | current figure (PDF is vector; PNG 300 dpi) |
| `paper_assembly_20261010/code/fig_study1.py` | plotting script |
| `study1_figure_data_20261009/data/reliability_items.csv` | input: top row (a–c) |
| `study1_figure_data_20261009/data/self_advantage_by_column.csv` | input: bottom row (d–f) |
| `study1_figure_data_20261009/data/panel_summary.json` | annotation numbers for captions and text (P1/P2, GLMM, 1b contrasts, Qwen d′/AUC/r, Qwen crossed prediction), copied from each study's frozen results. The script does not read it. |
| `paper_assembly_20261010/tables/fig_study1_bottom_row_summary.json` | script output: n, mean and 95% item-bootstrap CI for every bottom-row group |
| `mplconfig/stylelib/academic.mplstyle` | figure style |
| `provenance/` | `export.py` and `merge_bottom_row.py`, which built the input CSVs from the raw runs, plus the data README (estimands, sources, coverage). **Not runnable here**: they read raw run files that are not packaged. |
| `MANIFEST.sha256` | hashes of every file in this package |

## Panel mapping

| panel | model (column) | content | input rows | series |
|---|---|---|---|---|
| a | GPT-5.5 | P(PLAY) vs measured agreement; binomial logistic fit per setting | `reliability_items.csv`, `column == gpt`, settings low/high, 41 arrays each | filled circle + solid = low reasoning; open square + dashed = high |
| b | Claude Opus 5 | same | `column == claude`, low (thinking disabled) / high (adaptive, effort high) | same |
| c | Qwen step-316 | same, 2 options (chance .5) | `column == qwen`: observational Study 1 (30 items; filled circles + fit); continuation experiment CLEAN / NOISY targets (quintile-binned means ± 1.96 SE) | filled circle = observational; open square + solid = clean targets; triangle + dotted = 70/30 targets. Different checkpoints and items, not pooled. |
| d | GPT-5.5 | self advantage per item = (Opus → GPT) − (GPT → GPT), expected Brier | `self_advantage_by_column.csv`, `column == gpt`, `D_self_target` | Divergent vs Control; low vs high markers as above; large symbol = mean with 95% item-bootstrap CI |
| e | Claude Opus 5 | (GPT → Opus) − (Opus → Opus) | `column == claude` | same |
| f | Qwen step-316 | (base → step-316) − (step-316 → step-316), thinking off | `column == qwen` | Divergent vs Control, single setting |

Frozen bottom-row means (low reasoning; Qwen thinking off): GPT divergent +.216, control −.036; Opus +.299, +.036; Qwen +.594, −.029 (target-specific). Full values are in `fig_study1_bottom_row_summary.json`.

## Caveats for captions

- Frontier x values are 4-option agreement (chance .25); Qwen x values are 2-option (chance .5). Compare within a panel only.
- Qwen observational items were selected and scored on the same draws.
- The Qwen **pooled** control contrast is +.072 [.048, .100], not zero. The panel plots the target-specific contrast.
- The figure has no title. The caption in `paper_assembly_20261010/README.md` is headed "Own-coordinability knowledge". For Opus that framing is currently unsupported (see the ledger, "Most consequential unsupported claim"), so the caption heading awaits the wording decision.
- Sources: low-reasoning package `Study1_frontier_package_20261008`; high-reasoning run `study1_highreason_20261009` (FROZEN `933aa87d`); Qwen crossed study `Stag/qwen_crossed_prediction_20261009` (FROZEN `2da6c591`). Corrections in `paper_assembly_20261010/docs/ERRATA_STUDY1_AUDIT_FLAGS.md` are already applied.
