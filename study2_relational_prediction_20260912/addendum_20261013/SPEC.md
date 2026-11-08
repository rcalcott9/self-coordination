# Relational prediction: planned analyses completed after the original report (2026-10-13)

Written before any of these quantities was computed. No API calls; saved responses only.
Original outputs are inputs only and are not modified:

| file | sha256 |
|---|---|
| `data/frozen_items.json` (reference distributions, n = 100 per model) | `9403d84302d9166ed201f9e964093837bfd87cd5f2b01d0b2d1bd8c7d519abe7` |
| `results/run_20260912_154308/raw/parsed.jsonl` (440 responses) | `00b7e1fc589fd4525ed4334100c26f725e49ea88f3cea44068637c632dec7ef9` |
| `results/run_20260912_154308/report_rows.json` | `6b0b1c1ce539718606e3844596f6ad93fc890b1e0091404ab36d4e1a64e599cf` |
| `results/run_20260912_154308/item_level.json` | `caab46a63427eeb1924f8de44c542e21daaa228320e31c4f1532fa04406bc586` |
| `RESULTS.md` | `f20008af438f324a885b063e744dd4958930bcfd22b595d3ce68b0a44cc13f5a` |

## Recovered definitions (`ANALYSIS_PLAN.md`, written 2026-09-12 19:14:22 UTC, before any collection)
- "Multiclass Brier against the stated partner's empirical distribution … Reported alongside a
  log score as robustness."
- "Reported at: item level …; model level …; with per-item CIs and a leave-one-item-out check,
  since 13 items is few." (11 items were retained.)
- Original implementation (`code/report_study2.py`): metrics computed on the **mean predicted
  distribution** per item × focal × condition; reference distributions held fixed; model-level
  CI = item bootstrap, 4,000 resamples, percentile.

## Choices the plan did not specify (fixed here, before computing)
1. **Log score.** Log loss L = −Σ_k q_k ln p̂_k (natural log; lower is better, same orientation
   as Brier). p̂ = mean predicted distribution per item × focal × condition (as for Brier);
   q = stated target's reference distribution (COPY → SELF, DIFFERENT → OTHER).
   - Zero handling: p̂ is smoothed as (p̂ + ε)/(1 + 4ε) with **ε = 0.01** (primary). ε = 0.001
     is reported as a sensitivity. The number of item cells where p̂_k = 0 while q_k > 0 is
     reported.
   - Model level: mean over the 11 items, point estimate only (as for the original Brier). The
     COPY and DIFFERENT scores have different targets and are not contrasted.
2. **Per-item CIs** for G, Brier and log loss: 95% percentile bootstrap, 10,000 resamples,
   numpy seed 20261013. Each resample (a) redraws the 10 prediction responses with replacement
   within each item × focal × condition, independently by condition (they are independent
   calls), and (b) redraws each reference distribution as a multinomial sample of 100 from its
   observed proportions. Both sources of sampling error are included.
3. **Leave-one-item-out** for model-level G: for each focal model and each omitted item, the
   mean G over the remaining 10 items with the original CI method (item bootstrap, 4,000
   resamples, percentile; numpy seed 20261013). Reported: range of the 11 means, and the number
   of omissions whose CI excludes zero.
4. Nothing else is computed. These results are labelled "completed 2026-10-13, after the
   original report" and do not replace any original number.
