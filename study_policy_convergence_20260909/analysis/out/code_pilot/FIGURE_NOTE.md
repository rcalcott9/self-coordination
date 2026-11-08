# Code-conventions determinism figure — what it rests on

Built by `figures/make_fig_decomposition_tight.py --code` from `analysis/out/code_pilot/`,
which is `runs/code_pilot/` put through the unmodified `analysis/run_stage1.py` via the new
adapter `runners/to_pipeline_code.py`. 12 items x 9 checkpoints x n=48 = 5,184 trials,
36 pairs x 12 items = 432 pair-item rows.

`chosen_item` is `canonical_index` (k=4), not `convention_group`. That keeps the estimator
identical to the visual arm so the two figures are comparable; the collapsed convention
coding stays in the raw file for a sensitivity check.

## Integrity

- prompt hash single-generation `0339bee6`, matches expected; checkpoint requested == returned
  on every row; no duplicates.
- 1 parse failure (gpt-4-turbo, `code_error_001`), leaving that cell at n=47 < floor 48.
  The pipeline RETAINED and flagged it rather than dropping it. It is the only blemish.

## Two things that differ from the visual arm

**Panel B.** Determinism is **63.3%** of the trend here (+0.0732 of +0.1157), not 99.1%.
Alignment carries +0.0425 — a real third of the rise, where in the visual arm it was +0.0019
and flat. The visual arm's headline does not transfer to code.

**Panel C is close to uninformative, and the reason is measurable.** 59 of 108 cells sit at
effective support exactly 1.000 — the model gives the same answer on all 48 trials — so the
determinism adjustment has nothing to divide. Median support by item:

| item | median effective support |
|---|---|
| fnname, iface | 1.75 |
| jsonname | 1.92 |
| error, tie | 1.09 |
| argorder, fileorg, outorder, return, sentinel, serial, varname | 1.00 |

Only three of twelve items carry real within-cell variation. Both intervals in panel C
straddle zero (within +0.0222 [-0.0399, +0.1038]; cross +0.0390 [-0.0238, +0.1287]), and
within-family is *smaller* than cross-family — the reverse of the visual arm's ordering.
Read panel C as "not estimable on this battery", not as "no effect".

## Suggested caption

> Code-convention agreement across nine checkpoints (2024-04 to 2026-07), 12 items, n = 48
> trials per model x item. (A) Log expected pairwise agreement rises with checkpoint vintage.
> (B) The exact decomposition log M_AB = .5 log M_AA + .5 log M_BB + log cos_raw splits the
> rise into a determinism channel (+0.073/yr) and an alignment channel (+0.043/yr); unlike the
> visual battery, both channels move. (C) Determinism-adjusted similarity slope by pair type,
> 95% item-clustered bootstrap CI. Both intervals contain zero; 8 of 12 items are fully
> deterministic (effective support 1.00), so this panel is underpowered by construction.
