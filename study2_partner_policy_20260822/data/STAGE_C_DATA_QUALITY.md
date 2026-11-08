# Stage C — DATA QUALITY REPORT

Factual only: collection completeness, validity, AB/BA balance and raw per-cell
ATTEMPT rates. **No dose-response analysis, no partner contrast, no model fit,
no interpretation.** The primary analysis is pre-specified in
`design/STUDY2_SPEC_FROZEN.md` §9–10 and implemented in
`code/analyze_dose_response.py`; it is deliberately not run here.

- design table: `design/frozen_design_table.csv` (128 cells, re-frozen on the CONFIRMED advantages — see `design/RE_FREEZE_RECORD.md`)
- planned trials: **2,832**  (FROZEN_PARAMS.stage_c_calls() = 2,832)
- part files read: 2
    - `study2C_20260822_173758.csv`
    - `study2C_20260822_173757.csv`

## 0. Run outcome

Both actors were launched live in parallel on 2026-08-22 from the re-frozen
design table.

| actor | trials attempted | wall time | API errors | trials lost (retry also failed) | cells complete |
|---|---|---|---|---|---|
| GPT-5.5 | 1,424 | 1,184 s | **0** | **0** | **64/64** |
| Claude Opus 5 | 1,408 | 883 s | **358** | **179** | **6/64** |

**The Claude arm was cut short by an account-level Anthropic API usage limit,
not by anything in the design or the runner.** Every one of the 358 errors is the
same HTTP 400 `invalid_request_error`:

> You have reached your specified API usage limits. You will regain access on
> 2026-09-01 at 00:00 UTC.

A single probe call after the run confirmed the cap is still in force, so the
Claude arm was **not** retried — a resume would only have produced more errors.
The GPT arm was allowed to complete in full first; it did, cleanly.

**To finish the Claude arm:** re-run `python3 code/study2_betting.py --live
--models claude` on or after 2026-09-01. The runner is resumable and will skip
the 6 complete Claude cells and re-run the 58 short ones from scratch. Rows for a
cell always come from exactly one part file, so the completed re-run will not be
merged with the partial file left by today's run.

## 1. Rows collected vs planned

| actor | planned trials | analysed rows | complete cells | partial cells | not started |
|---|---|---|---|---|---|
| GPT-5.5 | 1,424 | 1,424 | 64/64 | 0 | 0 |
| Claude Opus 5 | 1,408 | 86 | 6/64 | 58 | 0 |
| **TOTAL** | **2,832** | **1,510** | **70/128** | **58** | **0** |

## 2. Valid / invalid responses

`valid_response` is the parse verdict on a single API response; a first response
that failed to parse is retried and marked `superseded_by_retry`. `included_in_analysis` is the one row per trial that the analysis reads.

| actor | rows written | valid | invalid | superseded by retry | included in analysis |
|---|---|---|---|---|---|
| GPT-5.5 | 1,424 | 1,424 | 0 | 0 | 1,424 |
| Claude Opus 5 | 1,587 | 1,229 | 358 | 179 | 1,229 |

## 3. AB/BA balance per cell

The design requires exactly n/2 AB and n/2 BA in every cell. Counted over the
`included_in_analysis` rows of each cell's single source file.

**All 70 cells that reached their frozen n are exactly n/2 AB and
n/2 BA.** Balance is exact wherever collection completed.

The cells that did not reach their n (section 4) lost trials to API errors that
fell wherever they fell in the randomised order, so their AB/BA split is not
guaranteed. It is reported here rather than assumed:

- 49 of the 58 short cells have unequal AB/BA:

| cell | target n | AB | BA | AB−BA |
|---|---|---|---|---|
| `claude|a_chev_ud|different|3` | 8 | 3 | 2 | +1 |
| `claude|a_chev_ud|different|9` | 8 | 3 | 4 | -1 |
| `claude|a_chev_ud|same|5` | 8 | 4 | 3 | +1 |
| `claude|a_chev_ud|same|7` | 8 | 4 | 3 | +1 |
| `claude|a_chev_ud|same|9` | 8 | 4 | 3 | +1 |
| `claude|b_spiral_cw|different|3` | 16 | 7 | 6 | +1 |
| `claude|b_spiral_cw|different|5` | 16 | 6 | 7 | -1 |
| `claude|b_spiral_cw|different|9` | 16 | 4 | 8 | -4 |
| `claude|b_spiral_cw|same|3` | 16 | 8 | 6 | +2 |
| `claude|b_spiral_cw|same|5` | 16 | 7 | 5 | +2 |
| `claude|b_spiral_cw|same|7` | 16 | 4 | 7 | -3 |
| `claude|b_spiral_cw|same|9` | 16 | 7 | 5 | +2 |
| `claude|c_open_cplx|different|3` | 30 | 13 | 12 | +1 |
| `claude|c_open_cplx|different|5` | 30 | 15 | 11 | +4 |
| `claude|c_open_cplx|different|9` | 30 | 12 | 13 | -1 |
| `claude|c_open_cplx|same|3` | 30 | 14 | 15 | -1 |
| `claude|c_open_cplx|same|7` | 30 | 11 | 13 | -2 |
| `claude|c_open_cplx|same|9` | 30 | 13 | 14 | -1 |
| `claude|d_texture|different|3` | 30 | 13 | 12 | +1 |
| `claude|d_texture|different|9` | 30 | 11 | 14 | -3 |
| `claude|d_texture|same|3` | 30 | 11 | 14 | -3 |
| `claude|d_texture|same|7` | 30 | 14 | 15 | -1 |
| `claude|mirror|different|3` | 30 | 13 | 12 | +1 |
| `claude|mirror|different|5` | 30 | 12 | 14 | -2 |
| `claude|mirror|different|7` | 30 | 13 | 15 | -2 |
| `claude|mirror|different|9` | 30 | 13 | 11 | +2 |
| `claude|mirror|same|3` | 30 | 13 | 14 | -1 |
| `claude|mirror|same|5` | 30 | 13 | 14 | -1 |
| `claude|mirror|same|7` | 30 | 11 | 13 | -2 |
| `claude|mirror|same|9` | 30 | 12 | 14 | -2 |
| `claude|proto|different|7` | 16 | 7 | 6 | +1 |
| `claude|proto|same|3` | 16 | 8 | 7 | +1 |
| `claude|proto|same|5` | 16 | 8 | 6 | +2 |
| `claude|proto|same|7` | 16 | 8 | 7 | +1 |
| `claude|proto|same|9` | 16 | 6 | 8 | -2 |
| `claude|rot|different|3` | 30 | 13 | 14 | -1 |
| `claude|rot|different|5` | 30 | 14 | 15 | -1 |
| `claude|rot|different|7` | 30 | 14 | 12 | +2 |
| `claude|rot|different|9` | 30 | 13 | 11 | +2 |
| `claude|rot|same|3` | 30 | 13 | 12 | +1 |
| `claude|rot|same|5` | 30 | 13 | 14 | -1 |
| `claude|rot|same|7` | 30 | 12 | 14 | -2 |
| `claude|rot|same|9` | 30 | 15 | 13 | +2 |
| `claude|s_arrow|different|3` | 16 | 8 | 5 | +3 |
| `claude|s_arrow|different|5` | 16 | 8 | 7 | +1 |
| `claude|s_arrow|different|7` | 16 | 6 | 8 | -2 |
| `claude|s_arrow|different|9` | 16 | 7 | 8 | -1 |
| `claude|s_arrow|same|3` | 16 | 7 | 8 | -1 |
| `claude|s_arrow|same|5` | 16 | 8 | 7 | +1 |

## 4. Cells short of target

**58 of 128 cells did not reach their frozen n** — all of
them Claude, all for the reason in section 0. `analysable rows` counts the
`included_in_analysis` rows in the SINGLE best part file for that cell; counts
are never summed across files.

Across the short cells: **1,143 analysable rows against a target of 1,322** (86.5%).

| cell | target n | analysable rows | short by |
|---|---|---|---|
| `claude|a_chev_ud|different|3` | 8 | 5 | 3 |
| `claude|a_chev_ud|different|9` | 8 | 7 | 1 |
| `claude|a_chev_ud|same|5` | 8 | 7 | 1 |
| `claude|a_chev_ud|same|7` | 8 | 7 | 1 |
| `claude|a_chev_ud|same|9` | 8 | 7 | 1 |
| `claude|b_spiral_cw|different|3` | 16 | 13 | 3 |
| `claude|b_spiral_cw|different|5` | 16 | 13 | 3 |
| `claude|b_spiral_cw|different|9` | 16 | 12 | 4 |
| `claude|b_spiral_cw|same|3` | 16 | 14 | 2 |
| `claude|b_spiral_cw|same|5` | 16 | 12 | 4 |
| `claude|b_spiral_cw|same|7` | 16 | 11 | 5 |
| `claude|b_spiral_cw|same|9` | 16 | 12 | 4 |
| `claude|c_open_cplx|different|3` | 30 | 25 | 5 |
| `claude|c_open_cplx|different|5` | 30 | 26 | 4 |
| `claude|c_open_cplx|different|7` | 30 | 28 | 2 |
| `claude|c_open_cplx|different|9` | 30 | 25 | 5 |
| `claude|c_open_cplx|same|3` | 30 | 29 | 1 |
| `claude|c_open_cplx|same|5` | 30 | 26 | 4 |
| `claude|c_open_cplx|same|7` | 30 | 24 | 6 |
| `claude|c_open_cplx|same|9` | 30 | 27 | 3 |
| `claude|d_texture|different|3` | 30 | 25 | 5 |
| `claude|d_texture|different|7` | 30 | 28 | 2 |
| `claude|d_texture|different|9` | 30 | 25 | 5 |
| `claude|d_texture|same|3` | 30 | 25 | 5 |
| `claude|d_texture|same|5` | 30 | 26 | 4 |
| `claude|d_texture|same|7` | 30 | 29 | 1 |
| `claude|d_texture|same|9` | 30 | 26 | 4 |
| `claude|mirror|different|3` | 30 | 25 | 5 |
| `claude|mirror|different|5` | 30 | 26 | 4 |
| `claude|mirror|different|7` | 30 | 28 | 2 |
| `claude|mirror|different|9` | 30 | 24 | 6 |
| `claude|mirror|same|3` | 30 | 27 | 3 |
| `claude|mirror|same|5` | 30 | 27 | 3 |
| `claude|mirror|same|7` | 30 | 24 | 6 |
| `claude|mirror|same|9` | 30 | 26 | 4 |
| `claude|proto|different|3` | 16 | 14 | 2 |
| `claude|proto|different|5` | 16 | 14 | 2 |
| `claude|proto|different|7` | 16 | 13 | 3 |
| `claude|proto|same|3` | 16 | 15 | 1 |
| `claude|proto|same|5` | 16 | 14 | 2 |
| `claude|proto|same|7` | 16 | 15 | 1 |
| `claude|proto|same|9` | 16 | 14 | 2 |
| `claude|rot|different|3` | 30 | 27 | 3 |
| `claude|rot|different|5` | 30 | 29 | 1 |
| `claude|rot|different|7` | 30 | 26 | 4 |
| `claude|rot|different|9` | 30 | 24 | 6 |
| `claude|rot|same|3` | 30 | 25 | 5 |
| `claude|rot|same|5` | 30 | 27 | 3 |
| `claude|rot|same|7` | 30 | 26 | 4 |
| `claude|rot|same|9` | 30 | 28 | 2 |
| `claude|s_arrow|different|3` | 16 | 13 | 3 |
| `claude|s_arrow|different|5` | 16 | 15 | 1 |
| `claude|s_arrow|different|7` | 16 | 14 | 2 |
| `claude|s_arrow|different|9` | 16 | 15 | 1 |
| `claude|s_arrow|same|3` | 16 | 15 | 1 |
| `claude|s_arrow|same|5` | 16 | 15 | 1 |
| `claude|s_arrow|same|7` | 16 | 12 | 4 |
| `claude|s_arrow|same|9` | 16 | 12 | 4 |

## 5. Raw per-cell ATTEMPT rates

Raw proportions over `included_in_analysis` rows from a single part file per cell.
Descriptive only — no contrast, no test, no ordering by advantage. A rate shown as
`0.750 (6/8)` comes from a cell that did NOT reach its frozen n and is reported
only for completeness; `target n` is the frozen allocation.

### GPT-5.5

| stimulus | tier | partner | safe 3 | safe 5 | safe 7 | safe 9 | target n |
|---|---|---|---|---|---|---|---|
| c_open_cplx | large | different | 1.000 | 1.000 | 0.625 | 0.250 | 8 |
| c_open_cplx | large | same | 1.000 | 1.000 | 1.000 | 0.000 | 8 |
| a_chev_ud | large | different | 1.000 | 1.000 | 0.750 | 0.000 | 8 |
| a_chev_ud | large | same | 1.000 | 1.000 | 0.750 | 0.000 | 8 |
| rot | small | different | 1.000 | 0.700 | 0.200 | 0.000 | 30 |
| rot | small | same | 1.000 | 0.867 | 0.000 | 0.000 | 30 |
| d_texture | small | different | 1.000 | 1.000 | 0.433 | 0.000 | 30 |
| d_texture | small | same | 1.000 | 1.000 | 0.100 | 0.000 | 30 |
| mirror | zero_floor | different | 1.000 | 0.400 | 0.033 | 0.000 | 30 |
| mirror | zero_floor | same | 1.000 | 0.233 | 0.000 | 0.000 | 30 |
| b_spiral_cw | negative | different | 1.000 | 0.300 | 0.000 | 0.000 | 40 |
| b_spiral_cw | negative | same | 1.000 | 0.475 | 0.000 | 0.000 | 40 |
| proto | zero_ceil | different | 1.000 | 1.000 | 0.500 | 0.000 | 16 |
| proto | zero_ceil | same | 1.000 | 1.000 | 0.688 | 0.000 | 16 |
| s_arrow | zero_ceil | different | 1.000 | 1.000 | 0.562 | 0.000 | 16 |
| s_arrow | zero_ceil | same | 1.000 | 0.938 | 0.688 | 0.000 | 16 |

### Claude Opus 5

| stimulus | tier | partner | safe 3 | safe 5 | safe 7 | safe 9 | target n |
|---|---|---|---|---|---|---|---|
| a_chev_ud | large | different | 1.000 (5/8) | 1.000 | 1.000 | 0.143 (7/8) | 8 |
| a_chev_ud | large | same | 1.000 | 1.000 (7/8) | 1.000 (7/8) | 0.143 (7/8) | 8 |
| b_spiral_cw | medium | different | 1.000 (13/16) | 0.923 (13/16) | 0.750 | 0.000 (12/16) | 16 |
| b_spiral_cw | medium | same | 1.000 (14/16) | 1.000 (12/16) | 0.909 (11/16) | 0.000 (12/16) | 16 |
| mirror | small | different | 1.000 (25/30) | 0.808 (26/30) | 0.321 (28/30) | 0.000 (24/30) | 30 |
| mirror | small | same | 1.000 (27/30) | 0.630 (27/30) | 0.250 (24/30) | 0.000 (26/30) | 30 |
| c_open_cplx | zero_floor | different | 1.000 (25/30) | 1.000 (26/30) | 1.000 (28/30) | 0.120 (25/30) | 30 |
| c_open_cplx | zero_floor | same | 1.000 (29/30) | 1.000 (26/30) | 0.958 (24/30) | 0.407 (27/30) | 30 |
| d_texture | zero_floor | different | 1.000 (25/30) | 1.000 | 0.929 (28/30) | 0.000 (25/30) | 30 |
| d_texture | zero_floor | same | 1.000 (25/30) | 1.000 (26/30) | 0.897 (29/30) | 0.038 (26/30) | 30 |
| rot | zero_floor | different | 1.000 (27/30) | 1.000 (29/30) | 0.731 (26/30) | 0.000 (24/30) | 30 |
| rot | zero_floor | same | 1.000 (25/30) | 1.000 (27/30) | 0.769 (26/30) | 0.000 (28/30) | 30 |
| proto | zero_ceil | different | 1.000 (14/16) | 1.000 (14/16) | 1.000 (13/16) | 0.438 | 16 |
| proto | zero_ceil | same | 1.000 (15/16) | 1.000 (14/16) | 1.000 (15/16) | 0.214 (14/16) | 16 |
| s_arrow | zero_ceil | different | 1.000 (13/16) | 1.000 (15/16) | 1.000 (14/16) | 0.200 (15/16) | 16 |
| s_arrow | zero_ceil | same | 1.000 (15/16) | 1.000 (15/16) | 1.000 (12/16) | 0.000 (12/16) | 16 |

## 6. Notes

- Rows for a cell are taken from exactly one part file — the newest that completed
  it at that cell's own n. Partial files are discarded, never merged.
- Retried trials appear twice in the raw file: the unparseable first response
  (`superseded_by_retry=True`) and the retry. Only one row per trial carries
  `included_in_analysis=True`.
- Any lost trial (retry also failed) shows up in section 4 as a shortfall.
