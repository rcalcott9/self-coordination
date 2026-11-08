# SENSITIVITY (exploratory, 2026-10-13; no API calls): is the Study 2 policy x partner interaction
# a probability-scale ceiling artefact? Logit-scale GLMM per model x configuration:
#   play ~ cls * partner + (1 + partner | item)   (falls back to (1 | item) if singular / non-convergent)
# Input: tables/study2_playpass_trials.csv (written by study2_freeze.py).
# Output: tables/study2_logit_interaction.csv. Sign convention matches study2_freeze.py:
# interaction > 0 means the COPY - DIFFERENT shift is larger on LOW items.
suppressPackageStartupMessages(library(lme4))
args <- commandArgs(trailingOnly = FALSE)
here <- dirname(dirname(normalizePath(sub("--file=", "", args[grep("--file=", args)]))))
d <- read.csv(file.path(here, "tables/study2_playpass_trials.csv"))
d$cls <- factor(d$cls, levels = c("HIGH", "LOW"))
d$partner <- factor(d$partner, levels = c("DIFFERENT", "COPY"))
set.seed(20261010)
ctl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
rows <- list()
for (key in unique(paste(d$model, d$config, sep = "|"))) {
  s <- d[paste(d$model, d$config, sep = "|") == key, ]
  fits <- list(
    slope = tryCatch(glmer(play ~ cls * partner + (1 + partner | item), s, binomial, control = ctl), error = function(e) NULL),
    intercept = glmer(play ~ cls * partner + (1 | item), s, binomial, control = ctl))
  use <- if (!is.null(fits$slope) && !isSingular(fits$slope) && is.null(fits$slope@optinfo$conv$lme4$messages)) "slope" else "intercept"
  m <- fits[[use]]
  b <- fixef(m); V <- vcov(m)
  term <- "clsLOW:partnerCOPY"
  se <- sqrt(V[term, term])
  # parametric bootstrap CI for the interaction (200 refits; Wald reported alongside)
  pb <- tryCatch({
    bb <- bootMer(m, function(x) fixef(x)[term], nsim = 200, seed = 20261010)
    quantile(bb$t[, 1], c(.025, .975), na.rm = TRUE)
  }, error = function(e) c(NA, NA))
  warn <- paste(c(m@optinfo$conv$lme4$messages, if (isSingular(m)) "singular"), collapse = "; ")
  rows[[key]] <- data.frame(model = s$model[1], config = s$config[1], status = s$status[1],
    re_structure = if (use == "slope") "(1 + partner | item)" else "(1 | item)",
    partner_shift_HIGH_logit = unname(b["partnerCOPY"]),
    partner_shift_LOW_logit = unname(b["partnerCOPY"] + b[term]),
    interaction_logit = unname(b[term]), se = se,
    wald_lo = unname(b[term] - 1.96 * se), wald_hi = unname(b[term] + 1.96 * se),
    pboot_lo = unname(pb[1]), pboot_hi = unname(pb[2]),
    p_wald = 2 * pnorm(-abs(b[term] / se)), n_trials = nrow(s), n_items = length(unique(s$item)),
    warnings = ifelse(warn == "", "none", warn))
}
out <- do.call(rbind, rows); rownames(out) <- NULL
write.csv(out, file.path(here, "tables/study2_logit_interaction.csv"), row.names = FALSE)
print(format(out, digits = 3), row.names = FALSE)
