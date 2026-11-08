## =====================================================================
## Partner-specific coordination — Task 3: follow-up trial design
## Emits a CELL-LEVEL design CSV (one row per condition cell). A runner
## matching confidence_calibration_probe.py expands each row into
## `n_replicates_proposed` trials. Allocation is a single editable column
## and is PENDING APPROVAL before any collection code is written.
## =====================================================================
suppressPackageStartupMessages({library(dplyr); library(tidyr); library(readr)})
OUT <- "/Users/calypsocalcott/LLM_Coordination/Name_game_experiment/analysis/partner_specific_coordination"

MODELS   <- c("gpt-5.4", "claude-opus-4-8")
STIMULI  <- c("proto","nd2","inkblot","rot","noise","mirror")
STIM_TYPE<- c(proto="focal", nd2="focal", inkblot="matched",
              rot="matched", noise="matched", mirror="matched")
SAFES    <- c(3, 5, 7, 9)
ORIENT   <- c("AB", "BA")

## proposed replicates PER CELL (per orientation) -- edit / approve before launch
N_CHOICE   <- 30   # -> 60 per predictor x partner x stimulus (matches Arm-1 N)
N_STATED   <- 25   # -> 50 per predictor x partner x stimulus (matches Arm-2 N)
N_REVEALED <- 13   # -> 26 per predictor x partner x stimulus x safe (~Arm-3 N)

base <- function(measure, safes, nrep)
  expand_grid(predictor_model = MODELS, partner_model = MODELS,
              stimulus = STIMULI, orientation = ORIENT, safe_payoff = safes) |>
  mutate(measure = measure, n_replicates_proposed = nrep)

design <- bind_rows(
  base("choice",   NA_real_, N_CHOICE),   # named-partner CHOICE -> named-framing ground-truth policy
  base("stated",   NA_real_, N_STATED),   # stated P of matching a draw from partner's distribution
  base("revealed", SAFES,    N_REVEALED)  # attempt vs opt-out; safe swept
) |>
  mutate(
    stimulus_type = unname(STIM_TYPE[stimulus]),
    self_partner  = as.integer(predictor_model == partner_model),
    partner_relation = if_else(self_partner == 1L, "self", "other"),
    cell_id = sprintf("%s__pred-%s__part-%s__%s__saf-%s__%s",
                      measure,
                      recode(predictor_model, "gpt-5.4"="gpt", "claude-opus-4-8"="cla"),
                      recode(partner_model,   "gpt-5.4"="gpt", "claude-opus-4-8"="cla"),
                      stimulus, ifelse(is.na(safe_payoff), "na", safe_payoff), orientation)) |>
  select(cell_id, measure, predictor_model, partner_model, self_partner, partner_relation,
         stimulus, stimulus_type, safe_payoff, orientation, n_replicates_proposed) |>
  arrange(measure, predictor_model, partner_model, stimulus, safe_payoff, orientation)

write_csv(design, file.path(OUT, "followup_trial_design.csv"))

## summary for approval
cat("cells by measure:\n"); print(count(design, measure, name = "cells"))
tot <- design |> group_by(measure) |>
  summarise(cells = n(), calls = sum(n_replicates_proposed), .groups = "drop")
cat("\nproposed call counts (pending approval):\n"); print(as.data.frame(tot))
cat(sprintf("\nTOTAL proposed API calls: %d\n", sum(design$n_replicates_proposed)))
