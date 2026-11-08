# Main figure — Study 4, Open-Set Online Rendezvous

File: `osr_fig_main.pdf` / `osr_fig_main.png` (300 dpi)
Script: `code/osr_fig_main.py`
Plot data: `osr_fig_main_panelA_data.csv`, `osr_fig_main_panelB_data.csv`

## Caption

Two independent GPT-5.5 copies selected public online rendezvous locations in an
open action space, while a third instance of the same checkpoint
(`gpt-5.5-2026-04-23`, `reasoning_effort = low` throughout) attempted to predict
their choice. **(A)** When monitoring was introduced, copy–copy coordination fell
from .839 to .374, while monitor evasion rose from .012 to .463. Successful
unpredicted coordination therefore increased only modestly, from .002 to .096, at
canonical-host matching with monitor depth *k* = 5 (Δ = .094, 95% CI [.039,
.164]). Faint lines are the 18 individual contexts; heavy markers are means
(filled circle = baseline, open square = monitored). **(B)** The joint-success
advantage is sensitive to monitor depth and location canonicalization: it is not
robust for exact-string matching, where it straddles zero at every depth, and not
robust at *k* = 1 at any matching level. Error bars are 95% bootstrap CIs (20,000
resamples over the 18 contexts).

## Notes for the methods text

- Panel A uses the canonical-host, *k* = 5 definition — the headline definition,
  shown in blue in panel B. Blue carries only that one meaning in this figure.
- Depths *k* = 1, 5, 10, 50 are the pre-specified set from the frozen strategic
  analysis and are read verbatim from `data/osr_strategic_results.json`.
  **`k` = 25 was not pre-specified**; it is computed here with the same frozen
  `joint()` / `monitor_sets()` / `boot_diff()` functions and the frozen seed, and
  is flagged `prespecified = 0` in the panel B plot-data CSV.
- Δ values quoted in panel A are the paired context-level bootstrap means from the
  frozen results file, not differences of the plotted marginal means.
- Deliberately excluded from this figure and belonging in text or supplement: the
  pre-registered diversity criterion and Amendment 01, distinct-count bookkeeping
  by canonicalization level, the baseline convergence gate, cost, and the C13
  parser caveat.
