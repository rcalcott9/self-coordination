library(ggplot2); library(patchwork); library(ggrepel)

## Paths resolve from this script's own location, so the project can be moved.
.script_dir <- function() {
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f)) normalizePath(dirname(f)) else normalizePath(getwd())
}

HERE <- .script_dir()
calib   <- read.csv(file.path(HERE, "viz_calib.csv"))
attempt <- read.csv(file.path(HERE, "viz_attempt.csv"))

nice <- function(x) ifelse(x=="gpt-5.4","GPT-5.4","Claude Opus 4.8")
calib$Model   <- factor(nice(calib$model),   levels=c("GPT-5.4","Claude Opus 4.8"))
attempt$Model <- factor(nice(attempt$model), levels=c("GPT-5.4","Claude Opus 4.8"))
MCOL <- c("GPT-5.4"="#eb6834", "Claude Opus 4.8"="#2a78d6")

pairlv <- c("proto","nd2","rot","inkblot","noise","mirror")   # easy -> hard
calib$pair   <- factor(calib$pair, levels=pairlv)
attempt$pair <- factor(attempt$pair, levels=pairlv)
PCOL <- c(proto="#1baf7a", nd2="#2a78d6", rot="#4a3aa7",
          inkblot="#eda100", noise="#e34948", mirror="#eb6834")

# ---- Panel 1: calibration (confidence vs ground truth) ----
long <- rbind(
  data.frame(Model=calib$Model, pair=calib$pair, trueP=calib$trueP,
             conf=calib$statedP, measure="Stated confidence  (arm 2 - self-report)"),
  data.frame(Model=calib$Model, pair=calib$pair, trueP=calib$trueP,
             conf=calib$impliedP, measure="Revealed confidence  (arm 3 - when it stops betting)"))
long$measure <- factor(long$measure,
  levels=c("Stated confidence  (arm 2 - self-report)","Revealed confidence  (arm 3 - when it stops betting)"))

p1 <- ggplot(long, aes(trueP, conf, color=Model)) +
  annotate("polygon", x=c(0,1,0), y=c(0,1,1), fill="grey85", alpha=.35) +
  annotate("text", x=.03, y=.97, label="overconfident", hjust=0, vjust=1,
           size=3, fontface="italic", colour="grey45") +
  geom_abline(slope=1, intercept=0, linetype="dashed", colour="grey55") +
  geom_point(size=2.6) +
  geom_text_repel(aes(label=pair), size=2.6, seed=1, min.segment.length=0,
                  segment.color="grey70", show.legend=FALSE, max.overlaps=20) +
  facet_wrap(~measure) +
  scale_color_manual(values=MCOL, name=NULL) +
  scale_x_continuous(limits=c(0,1.02), breaks=c(.5,.75,1),
                     labels=c("0.5\n(chance)","0.75","1.0")) +
  scale_y_continuous(limits=c(0,1.02), breaks=c(0,.25,.5,.75,1)) +
  labs(x="true coordination likelihood  (pairwise match rate, arm 1)",
       y="model's confidence") +
  theme_minimal(base_size=12) +
  theme(legend.position="top", panel.grid.minor=element_blank(),
        strip.text=element_text(face="bold", size=10.5),
        strip.background=element_rect(fill="grey95", colour=NA))

# ---- Panel 2: attempt-rate vs safe value (the revealed-confidence engine) ----
lab9 <- attempt[attempt$safe==9,]
p2 <- ggplot(attempt, aes(safe, attempt_rate, color=pair, group=pair)) +
  geom_hline(yintercept=.5, linetype="dashed", colour="grey60") +
  geom_line(linewidth=.9) + geom_point(size=1.9) +
  geom_text_repel(data=lab9, aes(label=pair), size=2.6, direction="y",
                  hjust=0, nudge_x=.35, segment.color="grey75", seed=2, show.legend=FALSE) +
  facet_wrap(~Model) +
  scale_color_manual(values=PCOL, guide="none") +
  scale_x_continuous(breaks=c(3,5,7,9), limits=c(3,10.2),
                     labels=c("3","5","7","9\n(need P>0.9)")) +
  scale_y_continuous(limits=c(0,1.02), breaks=c(0,.5,1), labels=c("0","50%","100%")) +
  labs(x="safe (opt-out) payoff  -  attempt payoff fixed at 10",
       y="attempt rate  (vs. take the safe payoff)") +
  theme_minimal(base_size=12) +
  theme(panel.grid.minor=element_blank(),
        strip.text=element_text(face="bold", size=10.5),
        strip.background=element_rect(fill="grey95", colour=NA))

fig <- (p1 / p2) +
  plot_annotation(
    title="Do LLMs know when they can coordinate?  Confidence calibration on a graded stimulus battery",
    subtitle=paste0("6 stimuli (easy to hard) x 2 models, one-shot dyadic coordination, position-counterbalanced. ",
                    "Points above the dashed line = overconfident.\n",
                    "Top: confidence vs. true match likelihood.   Bottom: willingness to bet on coordination as the safe payoff rises."),
    caption=paste0("Arm 1 choice (N=60/cell) -> true pairwise match.  Arm 2 stated P (N=50).  ",
                   "Arm 3 attempt-vs-opt-out sweep (N=25/cell x safe in {3,5,7,9}).  2,520 calls.  ",
                   "gpt-5.4 and claude-opus-4-8 at low reasoning effort."),
    theme=theme(plot.title=element_text(face="bold", size=14),
                plot.subtitle=element_text(colour="grey35", size=9.5),
                plot.caption=element_text(colour="grey50", size=7.5, hjust=0)))

pdf(file.path(HERE, "confidence_calibration.pdf"), width=11, height=9.2)
print(fig)
invisible(dev.off())
png(file.path(HERE, "confidence_calibration.png"), width=2100, height=1760, res=190)
print(fig); invisible(dev.off())
cat("wrote confidence_calibration.pdf and .png\n")
