# Partner-specific coordination

Extends the three-arm confidence-calibration experiment to ask:

> **Do models track their model-specific self-coordination advantages?**
> Not "are they more confident with self?" but: does the **self-vs-other
> confidence gap track the empirically measured, stimulus-specific
> self-coordination advantage**?

Nothing here overwrites existing repo files.

## Contents
| File | What it is |
|---|---|
| `01_coordination_matrix.R` | **Task 2** — GG / CC / GC match matrix + self-advantage, bootstrap CIs, classification, figures |
| `stimulus_option_map.csv` | canonical option-A/B labels + recoding rule per stimulus |
| `coordination_matrix.csv` | point estimates + 95% CIs + modal/tie info + classification |
| `groundtruth_generic_framing.csv` | stimulus-level ground truth for the follow-up (**generic framing**) |
| `bootstrap_draws.csv` | all 5,000 bootstrap draws (for later derived contrasts) |
| `coordination_matrix_figures.pdf/.png` | 4-panel figure |
| `02_followup_design.R` → `followup_trial_design.csv` | **Task 3** — cell-level design |
| `prompt_templates.md` | exact choice / stated / revealed prompts (named partner) |
| `03_followup_analysis_plan.R` | model specs for the follow-up (not runnable yet) |

## How cross-model match is computed (and why not by pairing)
Match is computed from the **empirical choice marginals**, not by pairing rows.
For a binary semantic choice with `P(A)=p_X` for model X:

```
within-model:  P(match X,X) = p_X^2 + (1 - p_X)^2
cross-model:   P(match X,Y) = p_X*p_Y + (1 - p_X)*(1 - p_Y)
general (>2 categories):  P(match X,Y) = sum_k p_X(k) * p_Y(k)
```

**Why not pair GPT and Claude observations 1-to-1:** the two models were run in
separate, independent API calls; there is no meaningful trial-level pairing.
Pairing by row/replicate would (a) invent dependence that isn't there and (b)
make the estimate depend on arbitrary row order. The marginal-overlap formula is
the population match rate between two independent draws and uses all the
information the samples actually carry. Use the counterbalanced **semantic**
category (`chosen_shape`), never raw `LEFT/RIGHT`.

## Bootstrap
Nonparametric, **orientation-stratified**: resample the independent Arm-1 calls
within `model × stimulus × orientation` (strata = 30 each, large enough), pool
after the already-semantic recoding, recompute marginals → GG/CC/GC → both
self-advantages. GPT and Claude are resampled **independently** (never paired by
row/replicate); a shared draw index only combines two independent replicates.
5,000 draws, percentile 95% CIs, `set.seed(20260802)`. Draws retained in
`bootstrap_draws.csv`. (Because recoding is orientation-invariant by
construction, stratification is a variance-control belt-and-suspenders; plain
`model × stimulus` resampling gives the same expectation.)

## Diagnostic classification (thresholds at top of `01`, easily changed)
`shared_focal` (all pairings high) · `GPT_specific` / `Claude_specific`
(self-advantage ≥ `TH_ADV_MEANINGFUL`) · `universally_flat` (all near chance).
Data-determined, **not hard-coded**. Current result:

| stimulus | class | GG | CC | GC | GPT self-adv | Claude self-adv |
|---|---|---|---|---|---|---|
| proto | shared_focal | 1.00 | 1.00 | 1.00 | 0.00 | 0.00 |
| nd2 | shared_focal | 0.97 | 1.00 | 0.98 | −0.02 | +0.02 |
| **inkblot** | **GPT_specific** | 0.97 | 0.50 | 0.50 | **+0.47** | 0.00 |
| **rot** | **Claude_specific** | 0.58 | 0.77 | 0.65 | −0.07 | **+0.12** |
| mirror | universally_flat | 0.51 | 0.50 | 0.50 | +0.01 | 0.00 |
| noise | universally_flat | 0.50 | 0.50 | 0.50 | 0.00 | 0.00 |

So the battery contains one GPT-specific focal point (**inkblot**) and one
Claude-specific one (**rot**) — the two stimuli whose confidence should diverge
by partner identity if models are calibrated.

## ⚠️ Generic-framing limitation (important)
The Arm-1 choices analysed here were elicited under the **original generic
framing** ("another instance of you") — **not** a named GPT-vs-Claude partner.
Naming the partner may change the acting model's *own* choice policy. Therefore:

- These outputs are labelled **generic-framing** coordination probabilities and
  are only a first, exploratory matrix.
- For a **named-partner** condition, the correct ground truth is the overlap of
  the **two policies elicited under that same naming** (from the follow-up's
  `measure=="choice"` cells), *not* the generic Arm-1 rate. `03_..._plan.R` step
  (0) computes it that way; the generic rate is retained only as a covariate /
  robustness check.

## Follow-up design (`followup_trial_design.csv`)
Crosses `predictor_model × partner_model × stimulus × measure × safe_payoff ×
orientation`, with `self_partner`, `partner_relation`, and a `cell_id`. Three
measures: `choice` (named-framing ground-truth policy), `stated`, `revealed`
(safe ∈ {3,5,7,9}). A runner expands each row into `n_replicates_proposed`
trials. **Allocation is pending approval** (see the script's printed call
totals). Open decisions before launch: common-knowledge/symmetry of naming, and
exact partner-description wording (`prompt_templates.md`).

## What each result would mean
- **Generic self-bias:** a positive `self_partner` main effect on confidence
  **with ~zero** `self_partner × empirical_self_advantage` interaction — the
  model is more confident with "self" *regardless of whether self actually
  coordinates better*. Not calibrated.
- **Calibrated model-specific partner sensitivity:** the
  `self_partner × empirical_self_advantage` interaction is **positive**, and the
  strongest-test slope (observed self-vs-other confidence advantage **vs**
  empirical self advantage) is positive with CI excluding 0 — the confidence gap
  is large exactly where the real advantage is large (GPT↑ on inkblot, Claude↑
  on rot) and ~0 where it isn't. **Caveat: only 6 stimuli per predictor model**
  — report stimulus-level estimates directly and interpret the slope cautiously.

## Reproduce
```
Rscript analysis/partner_specific_coordination/01_coordination_matrix.R   # Task 2
Rscript analysis/partner_specific_coordination/02_followup_design.R       # design CSV
# 03 is a plan; run after follow-up collection.
```
