# Paper assembly from existing data (2026-10-10)

- **No API calls.** Every number here is computed from data on disk.
- **Frozen primaries are unchanged.** New analyses are labelled **SENSITIVITY**.
- Code is in `code/`, outputs in `figures/` and `tables/`, the errata in `docs/`. `MANIFEST.sha256` hashes every input and output.
- Rebuild with `~/.venvs/research/bin/python code/<script>.py`. The scripts are deterministic (seed 20261010).

## Study 1: figure and repackage

**Figure:** `figures/fig_study1_2x3.{pdf,png}` (`code/fig_study1.py`, built from `../study1_figure_data_20261009/data/`).

> **Figure 1.** Own-coordinability knowledge.
>
> **(a–c)** P(PLAY) in the symmetric reliability judgement against measured agreement.
> - (a, b) Frontier models: each point is one of the 41 VIS-FRAME arrays; 12 judgements per array per setting. Filled circles and solid lines are low reasoning; open squares and dashed lines are high reasoning. Lines are binomial logistic fits. Agreement is the unbiased independent-order copy–copy match, 4 options, chance .25; low reasoning reuses the frame calibration (48 draws), high reasoning has its own (48 draws).
> - (c) Qwen step-316, thinking off, 2 options (chance .5).
>   - Filled circles: observational Study 1. These are the 30 extreme-group scenarios; truth comes from the selection data, so the same draws are used to select the items and to score them.
>   - Open squares (clean targets) and triangles (70/30 targets): the counterbalanced continuation experiment (V1/V2 step 157). These are binned means over trained items (quintiles of sampled same-order agreement), ±1.96 SE.
>   - The two Qwen series are different checkpoints and item sets and are not pooled.
>
> **(d–f)** Option-choice self advantage, (comparator → model) − (model → itself) expected Brier, one point per item. Large symbols are the mean, with 95% item-bootstrap CI.
> - "Divergent" items were selected for cross-model divergence on independent draws: frontier under low reasoning, Qwen on the selection draws. "Control" items share a policy.
> - Comparators: (d) Claude Opus 5, (e) GPT-5.5, (f) untuned base Qwen3.5-397B-A17B.
> - Qwen has 2 options and the frontier models 4, so compare effects within a panel, not raw Brier values across panels.

Bottom-row values match each study's frozen results:

| panel | divergent | control |
|---|---|---|
| GPT-5.5, low | +.216 | −.036 |
| Claude Opus 5, low | +.299 | +.036 |
| Qwen step-316 (target-specific) | +.594 | −.029 |

The Qwen **pooled** control contrast is not zero (+.072 [.048, .100]), because step-316 predicts the base model poorly even on shared items. State this in the text. Values: `tables/fig_study1_bottom_row_summary.json`.

**Repackage.** The low-reasoning package (`../Study1_frontier_package_20261008`, which reproduces 20 of 22 outputs) is unchanged. The high-reasoning run (`../study1_highreason_20261009`, FROZEN `933aa87d`, $171.40), the Qwen crossed study (`Stag/qwen_crossed_prediction_20261009`, FROZEN `2da6c591`) and the figure export are hashed into `MANIFEST.sha256`. This is a provenance manifest, **not** a second sandboxed reproduction.

**Audit fixes:** `docs/ERRATA_STUDY1_AUDIT_FLAGS.md`. The six flags are resolved and the 20 uncoded traces are explained (one failed coder batch).

## Study 2: sensitivity checks (labelled)

Script: `code/study2_sensitivity.py`. Outputs: `tables/study2_sensitivity.json` and `tables/study2_sensitivity_items.csv`.

**(a) SENSITIVITY: same-presentation agreement.**
- Why: the legacy PLAY/PASS prompts describe a partner who sees the options "presented the same way", but the item labels used independent-order agreement.
- Method: same-presentation agreement is recomputed from the frame calibration (2 draws per ordering × 24 orderings).
- Check: independent-order agreement reproduces the frozen labels to 5e-5.

| model | LOW-arm agreement: independent → same-presentation | HIGH arm | relabelling | ρ(agreement, item P(PLAY)), independent vs same, across cells |
|---|---|---|---|---|
| GPT-5.5 | .43 → .63 | .99 → .99 | 0 of 30 items move; every cell's HIGH−LOW contrast is unchanged | .64–.78 vs .57–.74 |
| Claude Opus 5 | .52 → .87 | 1.00 → 1.00 | undefined: 18 items tie at the top-15 boundary | .59–.78 vs .46–.62 |

Reading:
- Under the estimand the prompt actually describes, Opus's LOW items are mostly coordinable (.87).
- The Opus HIGH/LOW contrast therefore separates "perfect" from "high" same-presentation agreement, not reliable from unreliable.
- The frozen contrasts stand. Opus Study 2 claims should be worded in terms of independent-order agreement.

**(b) SENSITIVITY: Opus labels from adaptive Stage A agreement.** The 2×2 cells are thinking-adaptive, while the frozen labels came from the thinking-disabled frame.
- Relabelling the same 30 items by adaptive Stage A agreement (n = 24) **moves no item**: exactly 15 items sit at 1.0 under both configurations.
- So every cell's HIGH−LOW contrast is identical to the frozen value. LOW-arm adaptive agreement is .65.
- ρ with adaptive agreement is .58–.74, against .59–.78 for the frozen labels.

## Study 3: battery table, figure and Qwen sensitivity

Script: `code/study3_battery.py`. Outputs: `tables/study3_battery_table.csv`, `tables/study3_battery_items.csv` and `figures/fig_study3_vhat_vs_B.{pdf,png}`.

All rows are COPY partner; the frozen benchmark is B = max(7, 10·c). Rows marked exploratory are not part of the frozen pilots.

| model | setting | status | items × draws | P(PLAY) COPY | P(PLAY) DIFF | mean V̂ | mean B | V̂ − B [95% CI] | items V̂ < B |
|---|---|---|---|---|---|---|---|---|---|
| GPT-5.5 | low | frozen pilot | 10 × 20 | .93 | .74 | 7.85 | 8.12 | −0.27 [−1.08, 0.69] | 5 |
| Claude Opus 5 | low | frozen pilot | 10 × 20 | .28 | .26 | 7.08 | 8.20 | −1.12 [−2.15, −0.26] | 5 |
| GPT-5.5 | high | exploratory (own Stage 0) | 10 × 10 | .90 | — | 8.83 | 8.70 | +0.13 [−0.63, 0.90] | 2 |
| Claude Opus 5 | high | exploratory (own Stage 0) | 10 × 10 | .21 | — | 7.15 | 8.40 | −1.25 [−2.22, −0.40] | 5 |
| Claude Fable 5.1 | adaptive, effort low | frozen (Opus arrays, own Stage 0) | 10 × 20 | .24 | .16 | 6.90 | 8.94 | −2.04 [−3.11, −1.00] | 8 |
| Qwen step-316 | thinking off | frozen pilot | 10 × 20 | .80 | .75 | 6.08 | 7.86 | −1.78 [−2.23, −1.32] | 10 |
| Qwen step-316 | thinking on | exploratory | 10 × 20 | .98 | .97 | 8.35 | 8.65 | −0.30 [−1.25, 0.71] | 4 |

**SENSITIVITY: Qwen B using same-order agreement.**
- Why: the Qwen game prompt implies a same-presentation partner.
- Method: c_same is the mean over the two orders of the within-order unbiased agreement, from 10 Stage 0 draws per order. The recomputed c_pool matches the frozen value exactly.
- Thinking off: c .719 → .759, B 7.86 → 7.93, V̂ − B −1.78 → **−1.85 [−2.27, −1.40]**, 10/10 items below B.
- Thinking on: c .856 → .863, V̂ − B −0.30 → **−0.34 [−1.31, 0.65]**, 4/10 items below B.
- The conclusions are unchanged.

> **Figure 3.** Realised COPY payoff V̂ against the benchmark B = max(7, 10·ĉ) for each array or item.
> - Points below the dotted identity line fall short of what copies could secure by jointly choosing the better of PASS and coordinated PLAY.
> - Filled circles are the frozen or primary setting; open squares are the second setting: high reasoning for GPT and Opus, thinking on for Qwen.
> - Fable has one setting. B values are jittered horizontally by ±0.06.
> - Frontier panels: 4 options, independent order. Qwen: 2 options, frozen pooled-order B.

---

## Update 2026-10-13: Study 2 freeze, new sensitivities, methods/results draft (no API calls)

- **Draft:** `docs/METHODS_RESULTS_DRAFT.md`. Every number is labelled [frozen], [sensitivity] or [exploratory].
- **Rebuild:** run `code/study2_freeze.py` first, then `Rscript code/study2_logit_interaction.R` (it reads the trials CSV that `study2_freeze.py` writes), then `code/study3_benchmark_bias.py` (it reads `tables/study3_battery_items.csv`). Seed 20261010.
- **Check:** each output was regenerated in a clean copy and matched byte for byte.

**Study 2 freeze** (`code/study2_freeze.py`):
- Outputs: `figures/fig_study2.{pdf,png}` and the CSVs `tables/study2_playpass_{trials,cells,contrasts}.csv` and `tables/study2_relational_G_{items,summary}.csv`.
- The script asserts that it reproduces the frozen values before writing anything: GPT +.140 / +.073; Opus adaptive-low +.155; Qwen +.155, +.133, +.193 and ∓.059.
- The Qwen primary is `plunkett_qwen/results/s2_20260912_181428` (the symmetry-fixed run). The earlier `pp2x2_20260912_173541` run is superseded.

> **Figure 2.** Partner identity.
> - **(a–c)** P(PLAY) by own-agreement class (HIGH/LOW; Qwen: CLEAR/WEAK, 15 items each) for a copy partner (filled circles, solid line) and a different-model partner (open squares, dashed line). Error bars are 95% item-cluster bootstrap CIs.
> - Configurations: (a) GPT-5.5, effort low; (b) Claude Opus 5, adaptive thinking at effort low; (c) Qwen step-316, thinking off.
> - **(d)** Relational gating G with 95% bootstrap CIs. Filled circles: 11 items. Open squares: 6 families, with the four F10 arrays collapsed.

**SENSITIVITY (exploratory): Study 2 interaction on the logit scale** (`code/study2_logit_interaction.R` → `tables/study2_logit_interaction.csv`):
- Opus's probability-scale interaction is +.263 [.147, .390], with HIGH cells near ceiling. On the logit scale it is +1.11, Wald [−0.44, 2.66].
- GPT: +0.19 [−0.40, 0.79]. Qwen: +0.18 [−0.32, 0.68].
- No interaction survives both scales.

**SENSITIVITY (exploratory): Study 3 benchmark bias** (`code/study3_benchmark_bias.py` → `tables/study3_benchmark_bias{,_items}.csv`):
- B = max(7, 10ĉ) is biased upward by +0.02 to +0.15 points on average.
- Bias-corrected and cross-fitted B leave every frozen-primary conclusion unchanged. Cross-fitted: Opus −1.05 [−2.13, −0.16], Fable −1.88, Qwen off −1.52. GPT-low −0.08 [−0.88, 0.82] was never significant.
