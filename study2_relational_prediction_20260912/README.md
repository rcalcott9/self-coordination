# Study 2 — relational prediction (GPT-5.5 and Opus 5)

**Status: design complete, frozen item set PROPOSED but not frozen. Nothing run. No API calls.**

Do GPT-5.5 and Opus 5 know when their own policy is informative about another agent?
Prediction only — no game, no payoffs, no coordination choice.

## Concurrency — what I checked and avoided

Two other Claude Code instances are live on this project (PIDs 65861, 40241). Before writing
anything I inspected the repo for active writes:

- **`study_playpass_gpt/`** — last modified **minutes before this directory was created**
  (`code/run_playpass.py` 15:11, `data/frozen_items.json` 15:09). **Actively being written.
  Not read, not modified, not reused.**
- A `study_playpass_opus*` directory is likely to appear; the same applies.

This study writes **only** inside `study2_relational_prediction_20260912/`. Everything else is
read-only: `study2_4opt_20260830/data` (Stage A ground truth), `study2_4opt_20260830/stimuli`
(images), `study2_4opt_20260830/code/s4_common.py` (imported, not modified).

## Design

| | |
|---|---|
| ground truth | Stage A 4-option battery, 203 stimuli, gpt-5.5 + claude-opus-5, **n = 24 per cell** |
| focal models | GPT-5.5 and Opus 5, run symmetrically |
| COPY | another independent instance of the same model |
| DIFFERENT | the other model family |
| task | predict the other model's distribution over the four shapes |
| repetitions | 10 per item x focal x condition; no temperature parameter was sent (neither API accepts one for these configurations; corrected 2026-10-13, POWER_AND_COST.md planned 1.0) |
| calls | 13 x 2 x 2 x 10 = **520** |
| cost | **~$8-10** |

## Selection metric (fixed before any Study 2 data)

    stability_m = max_k p_m(k)                      modal share within model m
    divergence  = TVD(p_gpt, p_claude)              between-model distance
    score       = min(stability_gpt, stability_claude) x divergence

`min()` because an item is only usable if **both** models are individually predictable.
TVD because it is bounded, linear in probability mass, and reads as "fraction of mass that
would have to move". Full ranking in `data/candidates_ranked.csv`.

## Proposed frozen set — 13 items

Threshold: `min_stability >= 0.60` and `TVD >= 0.50`. Mean min-stability 0.728, mean TVD 0.679.

| stimulus | stab gpt/claude | TVD | modal g/c |
|---|---|---|---|
| F10_curvature_m5 | 1.00 / 0.88 | 0.88 | 3 / 0 |
| F10_curvature_m3 | 0.96 / 0.88 | 0.83 | 3 / 0 |
| F10_curvature_m2 | 0.75 / 1.00 | 0.75 | 3 / 0 |
| F20_corner_m0 | 0.75 / 1.00 | 0.75 | 3 / 0 |
| F06_density_m0 | 0.88 / 0.83 | 0.71 | 3 / 0 |
| F05_orient_m6 | 0.67 / 0.75 | 0.71 | 0 / 2 |
| F26_bumploc_m0 | 0.67 / 0.96 | 0.67 | 3 / 1 |
| F05_orient_m7 | 0.75 / 0.62 | 0.67 | 0 / 2 |
| F10_curvature_m6 | 0.75 / 0.88 | 0.62 | 3 / 0 |
| F12_mirror_m5 | 0.75 / 0.71 | 0.62 | 3 / 2 |
| F06_density_m4 | 0.67 / 0.83 | 0.62 | 3 / 2 |
| F36_split_m2 | 0.67 / 0.71 | 0.50 | 1 / 3 |
| F40_crossang_m2 | 0.62 / 0.83 | 0.50 | 0 / 3 |

Same item set for both focal models. `F10_curvature` supplies 4 of 13 — the single largest
family concentration and worth noting when reading item-level results.

## Two design risks, stated up front

**1. n = 24 is thin, and this project has already been burned by it.** At n = 24 a modal share
of 0.70 has SE ~ 0.094, and TVD between two 24-draw distributions has SE ~ 0.144 *even when the
true TVD is zero*. Ranking 203 items by `stability x TVD` and taking the top 13 therefore
selects partly on noise. This is exactly the failure that produced the 8-draw → 40-draw
regression earlier in this project, where a +0.240 separation collapsed to +0.041 on
re-measurement.

**Recommendation: re-measure the 13 candidates at n >= 100 per model before freezing.**
13 x 2 models x 100 = 2,600 calls ~ $40. If that is too expensive, the alternative is to accept
that the *selection* is noisy and interpret only the model-level aggregate, never item ranks.

**2. Tighter thresholds do not help.** `min_stability >= 0.75 AND TVD >= 0.50` leaves only 6
items, which is too few for item-clustered inference. 13 at the looser bar is the better
trade, but it is a genuinely small pool.

## Primary metric

    G = [TVD(P_copy, OTHER) - TVD(P_copy, SELF)] - [TVD(P_diff, OTHER) - TVD(P_diff, SELF)]

G > 0 = the prediction moved away from the focal's own policy and toward the partner's when
the partner was relabelled. Full plan in `ANALYSIS_PLAN.md`; sampling and cost in
`POWER_AND_COST.md`.

## Files

```
code/select_items.py     selection metric, reads Stage A read-only
code/prompts.py          exact prompts, all four focal x condition cells
code/run_study2.py       runner; refuses to start without data/frozen_items.json
code/analyze_study2.py   G plus secondaries, item-clustered bootstrap
data/candidates_ranked.{csv,json}     all 203 scored
data/frozen_candidates_PROPOSED.json  the 13 above - NOT yet frozen
```

## Not done, awaiting review

- item set is **proposed**, not frozen (`data/frozen_items.json` does not exist, and the runner
  refuses to start without it)
- no API calls of any kind
- third-party baseline specified in `POWER_AND_COST.md`, not run

## Addendum 2026-10-13: planned analyses completed after the original report
`ANALYSIS_PLAN.md` planned a log score, per-item CIs and a leave-one-item-out check; `RESULTS.md`
omitted them. They were computed from the saved responses (no API calls) in `addendum_20261013/`.
Unspecified choices were fixed in `SPEC.md` (sha256 `8504bb62…`) before computing. Original
outputs and `RESULTS.md` are unchanged. Interpretation change: GPT's model-level G null depends
on `F36_split_m2`; omitting it gives +.037 [.025, .048] (item bootstrap, 10 items).
