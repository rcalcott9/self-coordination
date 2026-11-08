## Stage 4 · Partner-specific coordination
## The battery contains model-specific focal points: coordination depends on WHO the partner is.
suppressPackageStartupMessages({library(ggplot2); library(patchwork)})

## Paths resolve from this script's own location, so the project can be moved.
.script_dir <- function() {
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f)) normalizePath(dirname(f)) else normalizePath(getwd())
}

SRC <- file.path(dirname(.script_dir()), "partner_specific_coordination")
OUT <- .script_dir()
cm  <- read.csv(file.path(SRC, "coordination_matrix.csv"), stringsAsFactors = FALSE)

## order stimuli by how much the pairings disagree, then by level
cm$spread <- with(cm, pmax(match_gpt_gpt, match_claude_claude) - match_gpt_claude)
cm$pair   <- factor(cm$stimulus, levels = cm$stimulus[order(cm$spread, cm$match_gpt_gpt)])

## ---- Panel A: the 3 pairings ----
lv <- c("GPT + GPT", "Claude + Claude", "GPT + Claude")
A <- rbind(
  data.frame(pair = cm$pair, k = lv[1], m = cm$match_gpt_gpt,
             lo = cm$match_gpt_gpt__lo, hi = cm$match_gpt_gpt__hi),
  data.frame(pair = cm$pair, k = lv[2], m = cm$match_claude_claude,
             lo = cm$match_claude_claude__lo, hi = cm$match_claude_claude__hi),
  data.frame(pair = cm$pair, k = lv[3], m = cm$match_gpt_claude,
             lo = cm$match_gpt_claude__lo, hi = cm$match_gpt_claude__hi))
A$k <- factor(A$k, levels = lv)
KCOL <- c("GPT + GPT" = "#eb6834", "Claude + Claude" = "#2a78d6", "GPT + Claude" = "#1baf7a")

## aqua sits below 3:1 on the light surface -> the named legend is the relief
pA <- ggplot(A, aes(m, pair, colour = k)) +
  geom_vline(xintercept = .5, linetype = "dashed", colour = "#898781", linewidth = .4) +
  geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0, linewidth = 2,
                 alpha = .28, position = position_dodge(width = .62)) +
  geom_point(size = 2.6, position = position_dodge(width = .62)) +
  scale_colour_manual(values = KCOL, name = NULL) +
  scale_x_continuous(limits = c(.45, 1.02), breaks = c(.5, .75, 1),
                     labels = c("0.5\nchance", "0.75", "1.0")) +
  scale_y_discrete(labels = function(p) paste0(p, "  ")) +
  labs(subtitle = "who coordinates with whom", x = NULL, y = NULL) +
  theme_minimal(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        panel.grid.major = element_line(colour = "#e1e0d9", linewidth = .3),
        plot.subtitle = element_text(size = 9.5, colour = "#52514e"),
        axis.text.y = element_text(face = "bold", colour = "#0b0b0b"),
        axis.text.x = element_text(colour = "#898781"),
        legend.position = "top", legend.key.height = unit(9, "pt"),
        legend.text = element_text(size = 9.5))

## ---- Panel B: self-advantage (own-model pairing minus cross-model) ----
MCOL <- c("GPT-5.4" = "#eb6834", "Claude Opus 4.8" = "#2a78d6")
B <- rbind(
  data.frame(pair = cm$pair, Model = "GPT-5.4", m = cm$gpt_self_advantage,
             lo = cm$gpt_self_advantage__lo, hi = cm$gpt_self_advantage__hi,
             sig = cm$gpt_self_adv_ci_excl0),
  data.frame(pair = cm$pair, Model = "Claude Opus 4.8", m = cm$claude_self_advantage,
             lo = cm$claude_self_advantage__lo, hi = cm$claude_self_advantage__hi,
             sig = cm$claude_self_adv_ci_excl0))
B$Model <- factor(B$Model, levels = names(MCOL))

pB <- ggplot(B, aes(m, pair, colour = Model)) +
  geom_vline(xintercept = 0, linetype = "dashed", colour = "#898781", linewidth = .4) +
  geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0, linewidth = 2,
                 alpha = .28, position = position_dodge(width = .62)) +
  geom_point(aes(shape = sig), size = 2.6, position = position_dodge(width = .62)) +
  scale_colour_manual(values = MCOL, name = NULL) +
  scale_shape_manual(values = c(`FALSE` = 1, `TRUE` = 19), guide = "none") +
  scale_x_continuous(limits = c(-.12, .56), breaks = c(0, .25, .5)) +
  scale_y_discrete(labels = NULL) +
  labs(subtitle = "self-advantage  (own-model pairing - cross-model)", x = NULL, y = NULL) +
  theme_minimal(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        panel.grid.major = element_line(colour = "#e1e0d9", linewidth = .3),
        plot.subtitle = element_text(size = 9.5, colour = "#52514e"),
        axis.text.x = element_text(colour = "#898781"),
        legend.position = "top", legend.key.height = unit(9, "pt"),
        legend.text = element_text(size = 9.5))

fig <- (pA | pB) +
  plot_layout(widths = c(1.15, 1)) +
  plot_annotation(
    title = "Two stimuli are focal for one model and invisible to the other",
    subtitle = "inkblot is a GPT-only focal point; rot is a Claude-only one · the rest are shared or flat",
    caption = paste0("Hollow points: 95% CI includes 0. Match computed from choice marginals, ",
                     "orientation-stratified bootstrap (5,000 draws), n=60 per model x stimulus.\n",
                     "Elicited under generic \"another instance of you\" framing · exploratory, not named-partner."),
    theme = theme(plot.title = element_text(face = "bold", size = 14, colour = "#0b0b0b"),
                  plot.subtitle = element_text(colour = "#52514e", size = 9.5),
                  plot.caption = element_text(colour = "#898781", size = 7.5, hjust = 0)))

pdf(file.path(OUT, "stage4_partner_specific.pdf"), width = 9.4, height = 5.2)
print(fig); invisible(dev.off())
png(file.path(OUT, "stage4_partner_specific.png"), width = 1880, height = 1040, res = 190)
print(fig); invisible(dev.off())
cat("wrote stage4_partner_specific.pdf/.png\n")
