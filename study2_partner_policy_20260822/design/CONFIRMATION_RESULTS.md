# Study 2 — confirmation screen results

**Stage C MUST NOT PROCEED as frozen — the gate FAILS.**

Critical cells that did not replicate:

- `claude` / `mirror` (zero_floor): |adv|=0.114 > 0.1, no longer a floor cell; sign uninformative at n=60 (|prov|<0.05)
- `claude` / `__ORDER__` (critical_order): critical-tier order does not hold

## What was run

A Stage-A-style re-estimation of own-copy choice rates, at the per-stimulus n frozen in `FROZEN_PARAMS.CONFIRM_N`, on both actors in `CONFIRM_MODELS`. The frozen Study-1 runner `stage_a_ground_truth.py` was reused unchanged (`PSC_EXP_DIR` redirected all output under `data/confirmation/`, so Study 1's tree was never written to): independent one-shot calls, exact AB/BA balance, prompt sha8 `3003ae1b`, unchanged parse rules, unchanged API settings. One invocation per n-group per actor.

Part files (6):

- `stageA_20260822_170510.csv`
- `stageA_20260822_170511.csv`
- `stageA_20260822_171248.csv`
- `stageA_20260822_171329.csv`
- `stageA_20260822_171616.csv`
- `stageA_20260822_171733.csv`

## Estimators

Nothing was reimplemented. Own-copy is `targeted_common.unbiased_match` (bias-corrected: same-draw pairs removed). Cross-model is `cross_model_match.cross_match`, the plug-in product of the two INDEPENDENT marginals, `GC = sum_k p_k^gpt * p_k^claude` — derived, never measured with new simultaneous cross-model calls. Bootstrap CIs are percentile, B=5000, seed base 20260807; the two cells are resampled independently. The advantage CI comes from one joint bootstrap that recomputes `unbiased_match(focal) - cross_match(gpt, claude)` per draw.

Self-check: this code path applied to the n=60 file `stageA_20260812_150823.csv` reproduces `pairs/cross_model_table.csv` on 45/45 cells exactly.

## Own-copy rates, n=60 -> confirmed, with CIs on both

Every cell reached its planned n exactly, with exact AB/BA balance, zero API errors, zero lost trials and zero unparseable responses.

| stimulus | actor | n=60 [95% CI] | confirmed n | confirmed [95% CI] | shift | CIs overlap |
|---|---|---|---|---|---|---|
| `a_chev_ud` | gpt | 0.817 [0.696, 0.934] | 180 | 0.640 [0.582, 0.713] | -0.177 | yes |
| `a_chev_ud` | claude | 0.845 [0.718, 0.967] | 180 | 0.665 [0.602, 0.736] | -0.179 | yes |
| `b_spiral_cw` | gpt | 0.655 [0.560, 0.790] | 180 | 0.623 [0.569, 0.692] | -0.032 | yes |
| `b_spiral_cw` | claude | 1.000 [1.000, 1.000] | 180 | 1.000 [1.000, 1.000] | +0.000 | yes |
| `c_open_cplx` | gpt | 1.000 [1.000, 1.000] | 180 | 0.989 [0.967, 1.000] | -0.011 | yes |
| `c_open_cplx` | claude | 0.528 [0.492, 0.619] | 180 | 0.497 [0.497, 0.511] | -0.030 | yes |
| `d_texture` | gpt | 0.501 [0.491, 0.573] | 180 | 0.542 [0.509, 0.597] | +0.042 | yes |
| `d_texture` | claude | 0.845 [0.741, 0.967] | 180 | 0.498 [0.497, 0.513] | -0.347 | **NO - disjoint** |
| `rot` | gpt | 0.573 [0.506, 0.696] | 120 | 0.570 [0.519, 0.648] | -0.003 | yes |
| `rot` | claude | 0.491 [0.491, 0.537] | 120 | 0.496 [0.496, 0.516] | +0.004 | yes |
| `mirror` | gpt | 0.497 [0.491, 0.560] | 120 | 0.496 [0.496, 0.519] | -0.000 | yes |
| `mirror` | claude | 0.512 [0.491, 0.587] | 120 | 0.622 [0.552, 0.709] | +0.110 | yes |
| `proto` | gpt | 1.000 [1.000, 1.000] | 60 | 1.000 [1.000, 1.000] | +0.000 | yes |
| `proto` | claude | 1.000 [1.000, 1.000] | 60 | 1.000 [1.000, 1.000] | +0.000 | yes |
| `s_arrow` | gpt | 1.000 [1.000, 1.000] | 60 | 1.000 [1.000, 1.000] | +0.000 | yes |
| `s_arrow` | claude | 1.000 [1.000, 1.000] | 60 | 1.000 [1.000, 1.000] | +0.000 | yes |

**Non-overlapping CIs** - a change larger than either sample's own uncertainty, so not attributable to n=60 sampling error:

- `d_texture` / claude: 0.845 -> 0.498 (-0.347)

Cross-model rate, derived from the two independent marginals:

| stimulus | GC n=60 | GC confirmed [95% CI] | variant-balanced GC |
|---|---|---|---|
| `a_chev_ud` | 0.167 | 0.346 [0.296, 0.391] | 0.304 |
| `b_spiral_cw` | 0.783 | 0.750 [0.683, 0.811] | 0.750 |
| `c_open_cplx` | 0.633 | 0.500 [0.428, 0.571] | 0.494 |
| `d_texture` | 0.444 | 0.495 [0.472, 0.517] | 0.815 |
| `rot` | 0.500 | 0.500 [0.466, 0.536] | 0.347 |
| `mirror` | 0.490 | 0.508 [0.463, 0.553] | 0.386 |
| `proto` | 1.000 | 1.000 [1.000, 1.000] | 1.000 |
| `s_arrow` | 1.000 | 1.000 [1.000, 1.000] | 1.000 |

## Compatibility advantage (own − cross), provisional → confirmed

### Focal GPT-5.5

| stimulus | tier | provisional (n=60) | confirmed [95% CI] | shift | critical |
|---|---|---|---|---|---|
| `a_chev_ud` | large | +0.650 | +0.294 [+0.193, +0.406] | -0.356 | yes |
| `c_open_cplx` | medium | +0.367 | +0.489 [+0.412, +0.566] | +0.122 |  |
| `d_texture` | small | +0.057 | +0.048 [+0.009, +0.108] | -0.010 |  |
| `proto` | zero_ceil | +0.000 | +0.000 [+0.000, +0.000] | +0.000 |  |
| `s_arrow` | zero_ceil | +0.000 | +0.000 [+0.000, +0.000] | +0.000 |  |
| `rot` | zero_floor | +0.073 | +0.070 [+0.012, +0.158] | -0.003 | yes |
| `mirror` | zero_floor | +0.007 | -0.012 [-0.039, +0.044] | -0.019 | yes |
| `b_spiral_cw` | negative | -0.128 | -0.127 [-0.127, -0.116] | +0.001 | yes |

### Focal Claude Opus 5

| stimulus | tier | provisional (n=60) | confirmed [95% CI] | shift | critical |
|---|---|---|---|---|---|
| `a_chev_ud` | large | +0.678 | +0.319 [+0.217, +0.431] | -0.359 | yes |
| `d_texture` | medium | +0.401 | +0.003 [-0.015, +0.043] | -0.398 |  |
| `b_spiral_cw` | small | +0.217 | +0.250 [+0.189, +0.317] | +0.033 |  |
| `proto` | zero_ceil | +0.000 | +0.000 [+0.000, +0.000] | +0.000 |  |
| `s_arrow` | zero_ceil | +0.000 | +0.000 [+0.000, +0.000] | +0.000 |  |
| `rot` | zero_floor | -0.009 | -0.004 [-0.026, +0.046] | +0.005 | yes |
| `mirror` | zero_floor | +0.022 | +0.114 [+0.038, +0.214] | +0.091 | yes |
| `c_open_cplx` | negative | -0.106 | -0.003 [-0.065, +0.080] | +0.103 | yes |

## Gate

`GATE_CRITICAL_TIERS` = ('large', 'negative', 'zero_floor'). FROZEN_PARAMS names the tiers but does not numerically define "sign and qualitative order", so the reading applied here is stated explicitly:

- **large** — must stay positive with a 95% CI excluding 0.
- **negative** — must stay negative. A positive point estimate fails only if its CI also excludes 0; a sign change inside the CI is reported, not failed.
- **zero_floor** — the cell's design role is a near-zero dose, and its provisional value (±0.01–0.07) means its SIGN carries no information at n=60. The requirement is therefore that it remains a floor cell: |advantage| ≤ 0.1 (the project's existing negligible-difference bar, `cross_model_match.CROSS_TOL`).
- **order** — within each actor, negative < zero_floor < large.

A tier boundary moving while sign and order hold is not a failure; the confirmed value simply replaces the provisional one.

| actor | cell | tier | provisional | confirmed | verdict | note |
|---|---|---|---|---|---|---|
| gpt | `a_chev_ud` | large | +0.650 | +0.294 | **PASS** | positive, CI excludes 0 |
| gpt | `rot` | zero_floor | +0.073 | +0.070 | **PASS** | \|adv\|=0.070 <= 0.1, still a floor cell |
| gpt | `mirror` | zero_floor | +0.007 | -0.012 | **PASS** | \|adv\|=0.012 <= 0.1, still a floor cell; sign uninformative at n=60 (\|prov\|<0.05) |
| gpt | `b_spiral_cw` | negative | -0.128 | -0.127 | **PASS** | negative, CI excludes 0 |
| gpt | `__ORDER__` | critical_order |  |  | **PASS** | negative(-0.127) < zero_floor(-0.012..+0.070) < large(+0.294) |
| claude | `a_chev_ud` | large | +0.678 | +0.319 | **PASS** | positive, CI excludes 0 |
| claude | `rot` | zero_floor | -0.009 | -0.004 | **PASS** | \|adv\|=0.004 <= 0.1, still a floor cell; sign uninformative at n=60 (\|prov\|<0.05) |
| claude | `mirror` | zero_floor | +0.022 | +0.114 | **FAIL** | \|adv\|=0.114 > 0.1, no longer a floor cell; sign uninformative at n=60 (\|prov\|<0.05) |
| claude | `c_open_cplx` | negative | -0.106 | -0.003 | **PASS** | negative; CI includes 0 |
| claude | `__ORDER__` | critical_order |  |  | **FAIL** | negative(-0.003) < zero_floor(-0.004..+0.114) < large(+0.319) |

## Structural identity

`FROZEN_PARAMS` section 2 asserts |GC − 1/2| = sqrt((GG − 1/2)(CC − 1/2)) for binary stimuli. Confirmed residuals:

A blank residual means the sampled (GG - 1/2)(CC - 1/2) was negative — one own-copy rate landed a hair below chance — so the square root is undefined; that happens only at floor cells and is sampling noise, not a violation.

| stimulus | predicted \|dev\| | observed \|dev\| | residual |
|---|---|---|---|
| `a_chev_ud` | 0.1521 | 0.1541 | 0.0019 |
| `b_spiral_cw` | 0.2479 | 0.2500 | 0.0021 |
| `c_open_cplx` |  | 0.0000 |  |
| `d_texture` |  | 0.0050 |  |
| `rot` |  | 0.0000 |  |
| `mirror` |  | 0.0083 |  |
| `proto` | 0.5 | 0.5000 | 0.0 |
| `s_arrow` | 0.5 | 0.5000 | 0.0 |

## Position fallback, and why `d_texture` moved

`pos_rate` is the share of a cell's trials taking its modal SIDE, pooled over AB and BA. Near 1.0 means the model answered by position rather than by form; the AB/BA randomization then splits its identity choices ~50/50 and own-copy collapses to chance. This is the mechanism behind the one non-overlapping shift, and it is the same form-rule instability the 2026-08-14 version-stability analysis reported.

| stimulus | pos_rate gpt | own-copy gpt | pos_rate claude | own-copy claude |
|---|---|---|---|---|
| `a_chev_ud` | 0.600 | 0.640 | 0.711 | 0.665 |
| `b_spiral_cw` | 0.539 | 0.623 | 0.500 | 1.000 |
| `c_open_cplx` | 0.506 | 0.989 | 1.000 | 0.497 |
| `d_texture` | 0.839 | 0.542 | 0.972 | 0.498 |
| `rot` | 0.742 | 0.570 | 0.817 | 0.496 |
| `mirror` | 0.833 | 0.496 | 0.683 | 0.622 |
| `proto` | 0.500 | 1.000 | 0.500 | 1.000 |
| `s_arrow` | 0.500 | 1.000 | 0.500 | 1.000 |

The `cross_variant_balanced` column in `confirmed_compatibility.csv` diverges from the pooled `GC` at exactly these position-driven cells. That is expected and is not an estimator disagreement: the pooled estimator is the frozen one and answers the question the game asks — two players who each receive an INDEPENDENTLY randomized layout — whereas the variant-balanced diagnostic conditions on both players receiving the SAME layout, which two position responders would trivially match on. The pooled value is the one used everywhere.

## The confirmed gradient, in rank order

Tier labels come from the provisional n=60 values and are frozen; the confirmed numbers are what the primary analysis actually uses as the predictor. Where the rank order no longer matches the label order, the label is stale, not the number.

**Focal GPT-5.5**

| rank | stimulus | frozen tier label | confirmed advantage |
|---|---|---|---|
| 1 | `c_open_cplx` | medium | +0.489 |
| 2 | `a_chev_ud` | large | +0.294 |
| 3 | `rot` | zero_floor | +0.070 |
| 4 | `d_texture` | small | +0.048 |
| 5 | `proto` | zero_ceil | +0.000 |
| 6 | `s_arrow` | zero_ceil | +0.000 |
| 7 | `mirror` | zero_floor | -0.012 |
| 8 | `b_spiral_cw` | negative | -0.127 |

Cells with |advantage| > 0.10 (i.e. carrying a usable dose): 3 of 8.

**Focal Claude Opus 5**

| rank | stimulus | frozen tier label | confirmed advantage |
|---|---|---|---|
| 1 | `a_chev_ud` | large | +0.319 |
| 2 | `b_spiral_cw` | small | +0.250 |
| 3 | `mirror` | zero_floor | +0.114 |
| 4 | `d_texture` | medium | +0.003 |
| 5 | `proto` | zero_ceil | +0.000 |
| 6 | `s_arrow` | zero_ceil | +0.000 |
| 7 | `c_open_cplx` | negative | -0.003 |
| 8 | `rot` | zero_floor | -0.004 |

Cells with |advantage| > 0.10 (i.e. carrying a usable dose): 3 of 8.

## Cells whose confirmed value departs materially from the provisional one

Listed for every tier, critical or not, at a |shift| above 0.15.

| actor | stimulus | tier | provisional | confirmed [95% CI] | shift |
|---|---|---|---|---|---|
| gpt | `a_chev_ud` | large | +0.650 | +0.294 [+0.193, +0.406] | -0.356 |
| claude | `a_chev_ud` | large | +0.678 | +0.319 [+0.217, +0.431] | -0.359 |
| claude | `d_texture` | medium | +0.401 | +0.003 [-0.015, +0.043] | -0.398 |

## What the failure is, and what it does not touch

**Holding.** The GPT-focal gradient replicates on every criterion: `a_chev_ud` stays a clear positive advantage, `b_spiral_cw` stays negative with a CI excluding zero and a point estimate essentially unchanged (-0.128 to -0.127), both floor cells stay at the floor, and the critical order negative < zero_floor < large holds. Both ceiling controls remain at exactly 1.000 for both actors.

**Failing.** The Claude-focal gradient no longer has a usable low end. Three things happened at once:

1. `mirror` rose from +0.022 to +0.114 [+0.038, +0.214] — a floor cell that is now a small-positive dose with a CI excluding zero, so it is no longer the zero anchor the design assigned it.
2. `c_open_cplx`, Claude's ONLY negative cell and by the spec's own allocation the one carrying most of the discrimination between the coarse-identity and policy-specific accounts, collapsed from -0.106 to -0.003 [-0.065, +0.080]. The sign survives, but the dose does not. The mechanism is visible in the position-fallback table: Claude answers `c_open_cplx` by position on 1.000 of trials, so its identity choices split 50/50 by construction and its own-copy rate is pinned at chance. A negative advantage then requires GC to sit ABOVE 0.5, which under a position rule is pure noise around 0.5 — the n=60 value of 0.633 was that noise. A cell whose focal model is a position responder cannot carry a stable negative dose at any n.
3. Consequently the critical order fails: the negative cell (-0.003) is no longer below the floor cells (-0.004 and +0.114).

**Also worth seeing, though not gated.** `d_texture`, Claude's medium cell, fell from +0.401 to +0.003 — the one shift whose CIs do not overlap the n=60 estimate, driven by Claude switching to a near-pure position rule on that stimulus. Claude's frozen allocation therefore now spends 64 Stage C trials on a cell labelled `medium` whose true dose is zero. And for GPT the `large` and `medium` labels have swapped (`c_open_cplx` +0.489 now exceeds `a_chev_ud` +0.294); that is a tier-boundary move with sign and order intact, which the spec explicitly does not treat as a failure, but it does mean `a_chev_ud` no longer dominates the GPT slope the way section 14 anticipated.

**What this does not undermine.** The estimators, the balance, the prompt and the API settings are all unchanged and verified; the structural identity |GC - 1/2| = sqrt((GG - 1/2)(CC - 1/2)) holds to a residual of 0.002 wherever it is defined; and the confirmation itself did exactly what it was for. The predictor was measured with error at n=60, the re-estimation at n=180/120/60 found that error to be large enough to move design-critical cells, and it found it BEFORE Stage C was paid for rather than after.

**Decision required before Stage C.** The gate is a human decision point and this report does not resolve it. Stage C is not run. The Claude-focal arm needs either a replacement negative cell and a replacement floor cell drawn from the confirmed values, or an explicit decision to run the slope on the confirmed doses as they now stand and accept that Claude contributes no negative arm.

## Files

- `design/confirmed_compatibility.csv` — GG, CC, GC and both advantages, with CIs
- `design/confirmation_gate.csv` — the per-cell gate verdicts above
- `data/confirmation/data/stageA_*.csv|.jsonl` — raw trials
