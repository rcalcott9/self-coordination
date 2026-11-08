## Stage 3 — Confidence calibration
## Do the models know when they can coordinate?
suppressPackageStartupMessages({library(ggplot2); library(patchwork); library(ggrepel)})

## Paths resolve from this script's own location, so the project can be moved.
.script_dir <- function() {
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f)) normalizePath(dirname(f)) else normalizePath(getwd())
}

HERE <- dirname(.script_dir())   # source/
OUT  <- .script_dir()

calib   <- read.csv(file.path(HERE, "viz_calib.csv"))
attempt <- read.csv(file.path(HERE, "viz_attempt.csv"))

nice <- function(x) ifelse(x == "gpt-5.4", "GPT-5.4", "Claude Opus 4.8")
MCOL <- c("GPT-5.4" = "#eb6834", "Claude Opus 4.8" = "#2a78d6")
pairlv <- c("proto", "nd2", "rot", "inkblot", "noise", "mirror")   # easy -> hard
for (nm in c("calib", "attempt")) {
  d <- get(nm)
  d$Model <- factor(nice(d$model), levels = names(MCOL))
  d$pair  <- factor(d$pair, levels = pairlv)
  assign(nm, d)
}

## ---- Panel 1: confidence vs. ground truth ----
long <- rbind(
  data.frame(Model = calib$Model, pair = calib$pair, trueP = calib$trueP,
             conf = calib$statedP,  measure = "stated  (what it says)"),
  data.frame(Model = calib$Model, pair = calib$pair, trueP = calib$trueP,
             conf = calib$impliedP, measure = "revealed  (when it stops betting)"))
long$measure <- factor(long$measure,
  levels = c("stated  (what it says)", "revealed  (when it stops betting)"))

## annotate the left facet only -- in the right facet these labels land on data
zone <- data.frame(measure = factor("stated  (what it says)", levels = levels(long$measure)),
                   x = c(.53, .99), y = c(.99, .53), hj = c(0, 1), vj = c(1, 0),
                   lab = c("overconfident", "underconfident"))

p1 <- ggplot(long, aes(trueP, conf, colour = Model)) +
  annotate("polygon", x = c(.5, 1, .5), y = c(.5, 1, 1), fill = "#e1e0d9", alpha = .45) +
  geom_text(data = zone, aes(x, y, label = lab, hjust = hj, vjust = vj),
            inherit.aes = FALSE, size = 2.9, fontface = "italic", colour = "#898781") +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", colour = "#898781", linewidth = .4) +
  geom_point(size = 2.6) +
  geom_text_repel(aes(label = pair), size = 2.5, seed = 1, min.segment.length = 0,
                  segment.colour = "#c3c2b7", colour = "#52514e",
                  show.legend = FALSE, max.overlaps = 20) +
  facet_wrap(~measure) +
  scale_colour_manual(values = MCOL, name = NULL) +
  scale_x_continuous(limits = c(.45, 1.03), breaks = c(.5, .75, 1),
                     labels = c("0.5\nchance", "0.75", "1.0")) +
  scale_y_continuous(limits = c(.2, 1.02), breaks = c(.25, .5, .75, 1)) +
  labs(x = "true coordination likelihood", y = "confidence") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "top", panel.grid.minor = element_blank(),
        panel.grid.major = element_line(colour = "#e1e0d9", linewidth = .3),
        strip.text = element_text(face = "bold", size = 9.5, colour = "#0b0b0b"),
        axis.text = element_text(colour = "#898781"),
        axis.title = element_text(colour = "#52514e", size = 9.5),
        legend.key.height = unit(9, "pt"), legend.text = element_text(size = 9.5))

## ---- Panel 2: what it bets, as the safe payoff rises ----
## small multiples by stimulus so identity stays on the two model hues
p2 <- ggplot(attempt, aes(safe, attempt_rate, colour = Model, group = Model)) +
  geom_line(linewidth = .8) + geom_point(size = 1.8) +
  facet_wrap(~pair, nrow = 1) +
  scale_colour_manual(values = MCOL, guide = "none") +
  scale_x_continuous(breaks = c(3, 5, 7, 9), limits = c(2.6, 9.4)) +
  scale_y_continuous(limits = c(0, 1.02), breaks = c(0, .5, 1), labels = c("0", "50%", "100%")) +
  labs(x = "safe payoff  (attempt pays 10)", y = "attempt rate") +
  theme_minimal(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        panel.grid.major = element_line(colour = "#e1e0d9", linewidth = .3),
        panel.spacing.x = unit(9, "pt"),
        strip.text = element_text(face = "bold", size = 9.5, colour = "#0b0b0b"),
        axis.text = element_text(colour = "#898781", size = 8),
        axis.title = element_text(colour = "#52514e", size = 9.5))

fig <- (p1 / p2) +
  plot_layout(heights = c(5, 4)) +
  plot_annotation(
    title = "Neither model knows when it can coordinate",
    subtitle = "6 stimuli x 2 models, one-shot dyadic coordination, position counterbalanced",
    caption = "Arm 1 choice n=60/cell (ground truth) · arm 2 stated P n=50 · arm 3 sweep n=25 per safe value. 2,520 calls.",
    theme = theme(plot.title = element_text(face = "bold", size = 14, colour = "#0b0b0b"),
                  plot.subtitle = element_text(colour = "#52514e", size = 9.5),
                  plot.caption = element_text(colour = "#898781", size = 7.5, hjust = 0)))

pdf(file.path(OUT, "stage3_confidence_calibration.pdf"), width = 8.2, height = 7.4)
print(fig); invisible(dev.off())
png(file.path(OUT, "stage3_confidence_calibration.png"), width = 1640, height = 1480, res = 190)
print(fig); invisible(dev.off())
cat("wrote stage3_confidence_calibration.pdf/.png\n")
