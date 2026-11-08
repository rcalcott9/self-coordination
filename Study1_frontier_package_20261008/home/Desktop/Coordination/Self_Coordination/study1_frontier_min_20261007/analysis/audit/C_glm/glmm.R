suppressMessages(library(lme4))
d <- read.csv("trials.csv")
set.seed(20261009)
out <- list()
for (m in c("gpt","claude")) {
  dm <- subset(d, model==m)
  for (f in c("play ~ y + (1|array)", "play ~ y + A + (1|array)")) {
    w <- character(0)
    fit <- withCallingHandlers(glmer(as.formula(f), data=dm, family=binomial,
             control=glmerControl(optimizer="bobyqa")),
             warning=function(x){w <<- c(w, conditionMessage(x)); invokeRestart("muffleWarning")})
    b <- fixef(fit)["y"]; se <- sqrt(diag(vcov(fit)))["y"]
    sd_re <- as.data.frame(VarCorr(fit))$sdcor[1]
    pr <- tryCatch(confint(fit, parm="y", method="profile", quiet=TRUE), error=function(e) c(NA,NA))
    pb <- tryCatch({bb <- bootMer(fit, function(x) fixef(x)["y"], nsim=500, type="parametric")
                    quantile(bb$t[,1], c(.025,.975), na.rm=TRUE)}, error=function(e) c(NA,NA))
    bA <- if ("A" %in% names(fixef(fit))) fixef(fit)["A"] else NA
    cat(sprintf("%s | %s | slope_y %.3f | Wald [%.3f, %.3f] | profile [%.3f, %.3f] | parboot [%.3f, %.3f] | slope_A %.3f | RE_sd %.3f | singular %s | warnings: %s\n",
        m, f, b, b-1.96*se, b+1.96*se, pr[1], pr[2], pb[1], pb[2], bA, sd_re, isSingular(fit),
        if (length(w)) paste(unique(w), collapse="; ") else "none"))
  }
}
