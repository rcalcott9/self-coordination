# [exploratory, 2026-10-15] Study 1 S1, Opus 5: joint low + high reasoning GLMM.
# Combines two Opus configurations, so it is exploratory, not frozen or planned.
# Specification fixed before fitting (see ledger, 2026-10-15):
#   primary : play ~ y + A + effort + (1|array) + (1|array:effort)
#   effort  : play ~ (y + A) * effort + (1|array) + (1|array:effort); focal term y:effort
#   sens.   : same fixed effects with (1|array) only
# y, A = each setting's own array-level agreement and auditor prediction; effort coded
# low = -0.5, high = +0.5, so the y main effect is the average of the two setting slopes.
# y and A are standardised on the pooled Opus rows for convergence (the raw-scale per-setting
# fit failed to converge in the 10-09 audit) and slopes are reported on the original scale.
# No equivalence bound is chosen or tested here.
# Inputs (read-only): the trial files used by the existing per-setting S1 GLMMs.
# Output: ../tables/study1_opus_joint_glmm.csv and study1_opus_joint_glmm.txt
suppressMessages(library(lme4))
args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- normalizePath(file.path(here, "..", ".."))
LOW  <- file.path(root, "study1_frontier_min_20261007/analysis/audit/C_glm/trials.csv")
HIGH <- file.path(root, "study1_highreason_20261009/analysis/out_1a/glmm_trials.csv")
out_csv <- file.path(here, "..", "tables", "study1_opus_joint_glmm.csv")
out_txt <- file.path(here, "..", "tables", "study1_opus_joint_glmm.txt")
sink(out_txt, split = TRUE)

lo <- subset(read.csv(LOW), model == "claude"); lo$setting <- "low"
hi <- subset(read.csv(HIGH), model == "claude"); hi$setting <- "high"
d <- rbind(lo, hi)
stopifnot(nrow(lo) == 492, nrow(hi) == 492, setequal(lo$array, hi$array),
          all(tapply(d$y, paste(d$array, d$setting), function(v) length(unique(v))) == 1),
          all(tapply(d$A, paste(d$array, d$setting), function(v) length(unique(v))) == 1))
d$effort <- ifelse(d$setting == "high", 0.5, -0.5)
d$cell <- interaction(d$array, d$setting, drop = TRUE)
sy <- sd(d$y); sA <- sd(d$A)
d$yz <- (d$y - mean(d$y)) / sy; d$Az <- (d$A - mean(d$A)) / sA
cat(sprintf("n = %d judgements, %d arrays x 2 settings; P(PLAY) low %.3f high %.3f; sd(y) %.3f sd(A) %.3f\n",
            nrow(d), length(unique(d$array)), mean(lo$play), mean(hi$play), sy, sA))
cat(sprintf("array-level r(y, A): low %.2f, high %.2f; r(y_low, y_high) %.2f\n",
            cor(tapply(lo$y, lo$array, `[`, 1), tapply(lo$A, lo$array, `[`, 1)),
            cor(tapply(hi$y, hi$array, `[`, 1), tapply(hi$A, hi$array, `[`, 1)),
            cor(tapply(lo$y, lo$array, `[`, 1), tapply(hi$y, hi$array, `[`, 1))))

ctl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
fitw <- function(f, data) {
  w <- character(0)
  fit <- withCallingHandlers(eval(bquote(glmer(.(as.formula(f)), data = .(data), family = binomial, control = ctl))),
           warning = function(x) { w <<- c(w, conditionMessage(x)); invokeRestart("muffleWarning") })
  attr(fit, "warn") <- if (length(w)) paste(unique(w), collapse = "; ") else "none"
  fit
}
scale_of <- function(term) if (grepl("^yz", term)) sy else if (grepl("^Az", term)) sA else 1

# 0. reproduction check of the existing per-setting adjusted fits (3.807 low, 3.29 high)
for (s in c("low", "high")) {
  ds <- subset(d, setting == s); ds$yz <- (ds$y - mean(ds$y)) / sd(ds$y); ds$Az <- (ds$A - mean(ds$A)) / sd(ds$A)
  f <- fitw("play ~ yz + Az + (1|array)", ds)
  cat(sprintf("reproduce %s: slope_y %.3f (warnings: %s)\n", s, fixef(f)["yz"] / sd(ds$y), attr(f, "warn")))
}

rows <- list()
report <- function(label, fit, terms, boot = 0, seed = 20261015) {
  b <- fixef(fit); se <- sqrt(diag(vcov(fit)))
  pr <- tryCatch(confint(fit, parm = terms, method = "profile", quiet = TRUE),
                 error = function(e) { cat("  profile CI unavailable:", conditionMessage(e), "\n")
                                       matrix(NA, length(terms), 2, dimnames = list(terms, NULL)) })
  bt <- NULL
  if (boot > 0) {
    set.seed(seed)
    bt <- bootMer(fit, function(x) fixef(x)[terms], nsim = boot, type = "parametric")$t
    bt <- matrix(bt, ncol = length(terms), dimnames = list(NULL, terms))
  }
  vc <- as.data.frame(VarCorr(fit))
  cat(sprintf("\n[%s] logLik %.3f | singular %s | warnings: %s\n  RE sd: %s\n", label, logLik(fit),
              isSingular(fit), attr(fit, "warn"), paste(sprintf("%s %.3f", vc$grp, vc$sdcor), collapse = ", ")))
  for (t in terms) {
    k <- scale_of(t)
    pb <- if (!is.null(bt)) quantile(bt[, t], c(.025, .975), na.rm = TRUE) / k else c(NA, NA)
    cat(sprintf("  %-10s %7.3f  Wald [%.3f, %.3f]  profile [%.3f, %.3f]  parboot [%.3f, %.3f] (n_ok %s)  p_Wald %.3f\n",
        t, b[t] / k, (b[t] - 1.96 * se[t]) / k, (b[t] + 1.96 * se[t]) / k, pr[t, 1] / k, pr[t, 2] / k,
        pb[1], pb[2], if (is.null(bt)) "-" else sum(!is.na(bt[, t])), 2 * pnorm(-abs(b[t] / se[t]))))
    rows[[length(rows) + 1]] <<- data.frame(model = label, term = t, est = b[t] / k,
        wald_lo = (b[t] - 1.96 * se[t]) / k, wald_hi = (b[t] + 1.96 * se[t]) / k,
        prof_lo = pr[t, 1] / k, prof_hi = pr[t, 2] / k, pboot_lo = pb[1], pboot_hi = pb[2],
        p_wald = 2 * pnorm(-abs(b[t] / se[t])), singular = isSingular(fit), warnings = attr(fit, "warn"))
  }
  invisible(fit)
}

f_main <- fitw("play ~ yz + Az + effort + (1|array) + (1|cell)", d)
report("primary", f_main, c("yz", "Az", "effort"), boot = 1000)
af <- tryCatch(summary(allFit(f_main, verbose = FALSE)), error = function(e) conditionMessage(e))
if (is.character(af)) cat("  allFit unavailable:", af, "\n") else {
  cat("  allFit slope_y (orig units):", paste(sprintf("%s %.3f", rownames(af$fixef), af$fixef[, "yz"] / sy), collapse = "; "), "\n")
  cat("  allFit logLik range:", paste(round(range(af$llik), 4), collapse = " to "), "\n") }

f_int <- fitw("play ~ (yz + Az) * effort + (1|array) + (1|cell)", d)
report("effort_interaction", f_int, c("yz", "Az", "effort", "yz:effort", "Az:effort"), boot = 1000)
cat("  implied slope_y: low", round((fixef(f_int)["yz"] - .5 * fixef(f_int)["yz:effort"]) / sy, 3),
    " high", round((fixef(f_int)["yz"] + .5 * fixef(f_int)["yz:effort"]) / sy, 3), "\n")
f_noy  <- fitw("play ~ yz + Az * effort + (1|array) + (1|cell)", d)
lr <- anova(f_noy, f_int)
cat(sprintf("  LRT for y:effort (A:effort retained): chisq %.3f, df %d, p %.3f\n", lr$Chisq[2], lr$Df[2], lr$`Pr(>Chisq)`[2]))

f_sens <- fitw("play ~ yz + Az + effort + (1|array)", d)
report("sens_array_only_RE", f_sens, c("yz", "Az", "effort"))

# array-cluster bootstrap: resample whole arrays (both settings together), refit primary
set.seed(20261015)
arr <- unique(d$array); B <- 1000; bs <- rep(NA_real_, B)
for (i in seq_len(B)) {
  pick <- sample(arr, length(arr), replace = TRUE)
  db <- do.call(rbind, lapply(seq_along(pick), function(j) { x <- d[d$array == pick[j], ]; x$array <- paste0(x$array, "#", j); x }))
  db$cell <- interaction(db$array, db$setting, drop = TRUE)
  fb <- tryCatch(suppressWarnings(glmer(play ~ yz + Az + effort + (1|array) + (1|cell), data = db,
                 family = binomial, control = ctl)), error = function(e) NULL)
  if (!is.null(fb)) bs[i] <- fixef(fb)["yz"] / sy
}
cq <- quantile(bs, c(.025, .975), na.rm = TRUE)
cat(sprintf("\n[primary] array-cluster bootstrap slope_y: [%.3f, %.3f], n_ok %d/%d, P(slope<=0) %.3f\n",
            cq[1], cq[2], sum(!is.na(bs)), B, mean(bs <= 0, na.rm = TRUE)))
rows[[length(rows) + 1]] <- data.frame(model = "primary_cluster_boot", term = "yz", est = fixef(f_main)["yz"] / sy,
    wald_lo = NA, wald_hi = NA, prof_lo = NA, prof_hi = NA, pboot_lo = cq[1], pboot_hi = cq[2],
    p_wald = NA, singular = NA, warnings = sprintf("array-cluster bootstrap, n_ok %d/%d", sum(!is.na(bs)), B))
write.csv(do.call(rbind, rows), out_csv, row.names = FALSE)
sink()
