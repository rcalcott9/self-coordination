## =====================================================================
## Partner-specific coordination — Task 3: follow-up analysis PLAN
## NOT RUNNABLE YET (no follow-up data). Model specs + data structure
## for the primary tests. Run after the partner-identity collection.
## =====================================================================
## Expected long-format follow-up data (one row per trial), keys:
##   predictor_model, partner_model, self_partner (0/1), stimulus,
##   orientation, replicate, measure, safe_payoff,
##   chosen_shape, stated_p, decision ("attempt"/"opt_out")
##
## Join, per (predictor_model, partner_model, stimulus), the NAMED-FRAMING
## ground truth (recomputed from measure=="choice" policies, NOT the generic
## Arm-1 rate) into columns:
##   empirical_match_probability          -- overlap of the two named policies
##   empirical_self_advantage             -- within-model minus cross-model match
##                                           for THIS predictor & stimulus, under naming
##   self_partner                         -- 1 if predictor_model == partner_model
## Also carry the GENERIC Arm-1 quantities as a covariate/robustness check.

suppressPackageStartupMessages({library(dplyr); library(lme4); library(broom.mixed); library(ggplot2)})

## ------------------------------------------------------------------
## (0) NAMED-FRAMING ground truth from measure=="choice"
## ------------------------------------------------------------------
## pA_named[predictor, partner, stimulus] = P(choose A | acting=predictor, told partner)
## match(pred=X, part=Y, stim) = pA_named[X,Y]*pA_named[Y,X] + (1-.)*(1-.)   # overlap of the two elicited policies
## self match  = match(X, X, stim);  cross match = match(X, Y, stim)
## empirical_self_advantage[X, stim] = self match - cross match
## (bootstrap over choice trials within predictor x partner x stimulus x orientation,
##  mirroring 01_coordination_matrix.R, to get CIs on the named-framing matrix.)

## ------------------------------------------------------------------
## (1) STATED-CONFIDENCE model
## ------------------------------------------------------------------
## Decisive test = does the SELF-vs-OTHER confidence gap track empirical self
## advantage -- NOT a bare self_partner main effect.
stated_full <- lmer(
  stated_p_prop ~ empirical_match_probability
                + self_partner * empirical_self_advantage   # <-- the calibration interaction
                + predictor_model
                + (1 | stimulus),
  data = filter(dat, measure == "stated"))
## Small #stimuli -> also fit stimulus as FIXED and report per-stimulus estimates
## directly rather than leaning on the random effect:
stated_fixed <- lm(stated_p_prop ~ empirical_match_probability
                   + self_partner * empirical_self_advantage
                   + predictor_model + stimulus,
                   data = filter(dat, measure == "stated"))
## Key coefficient: self_partner:empirical_self_advantage  (> 0 => calibrated).

## ------------------------------------------------------------------
## (2) REVEALED-CONFIDENCE model (attempt = 1, opt_out = 0)
## ------------------------------------------------------------------
## Transform safe payoff to the rational probability threshold (safe/10) and
## fit the full response curve -- do NOT read raw attempt rate at safe=9 as a
## subjective probability.
rev <- dat |> filter(measure == "revealed") |>
  mutate(attempt = as.integer(decision == "attempt"),
         thresh  = safe_payoff / 10)
revealed <- glmer(
  attempt ~ thresh + empirical_match_probability
          + self_partner * empirical_self_advantage         # partner sensitivity tracks actual advantage?
          + predictor_model
          + (1 | stimulus),
  family = binomial, data = rev)
## Minimum test: self_partner:empirical_self_advantage interaction on attempt.

## ------------------------------------------------------------------
## (3) STRONGEST TEST -- observed vs empirical self advantage (n = 6/predictor)
## ------------------------------------------------------------------
## observed self-partner confidence advantage, per (stimulus, predictor):
##   conf(self) - conf(other)   [for stated: mean stated_p; for revealed: an
##   indifference-point / fitted-threshold difference from the safe curve]
strongest <- obs_adv |>                         # cols: predictor_model, stimulus,
  left_join(named_self_adv, by = c("predictor_model","stimulus"))  # empirical_self_advantage (+CI)
## correlation / regression WITH the n=6 caveat surfaced loudly:
fit  <- lm(observed_conf_advantage ~ empirical_self_advantage, data = strongest)
ct   <- with(strongest, cor.test(empirical_self_advantage, observed_conf_advantage))
ggplot(strongest, aes(empirical_self_advantage, observed_conf_advantage,
                      color = predictor_model)) +
  geom_hline(yintercept = 0, linetype = "dashed") +
  geom_abline(slope = 1, intercept = 0, linetype = "dotted") +
  geom_errorbarh(aes(xmin = esa_lo, xmax = esa_hi), height = 0) +
  geom_point(size = 3) + ggrepel::geom_text_repel(aes(label = stimulus)) +
  labs(subtitle = "n = 6 stimuli per predictor model - interpret slope cautiously",
       x = "empirical self-coordination advantage (named framing)",
       y = "observed self-vs-other confidence advantage")
## Report slope, CI, and cor.test; do NOT over-interpret with 6 points/model.

## ------------------------------------------------------------------
## DECISION RULE
## ------------------------------------------------------------------
## GENERIC self-bias        : self_partner main effect > 0 but the
##                            self_partner:empirical_self_advantage interaction
##                            ~ 0 (confidence higher with self regardless of
##                            whether self actually helps).
## CALIBRATED partner sens. : self_partner:empirical_self_advantage > 0 and the
##                            strongest-test slope > 0 with CI excluding 0
##                            (self-vs-other confidence gap scales WITH the real
##                            self-coordination advantage, e.g. large on inkblot
##                            for GPT and on rot for Claude, ~0 where advantage~0).
