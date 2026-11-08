## Stage 2 — Self-model vs shared salience
## Does partner identity change channel-free coordination, or is it all stimulus salience?
##
## Revised 2026-08-04. Two changes, both about using the data we already have:
##   (1) run 20260730_150646 (salience-absent, self/other/neutral, n = 24/cell) was
##       previously unused. It is the same model, stimuli and n as 154134 and is the
##       ONLY salience-absent `other` arm, so it is pooled into the lower panel.
##   (2) the self-vs-unknown contrast is now ESTIMATED (bootstrap CI + permutation p)
##       instead of being eyeballed off overlapping cell CIs. Overlapping per-cell
##       intervals are not a test of the difference.
## Pooling assumes the `self` and `neutral` opener wording was unchanged between the
## two runs (only the third arm was swapped, other -> shared_dist). The runs are 35
## minutes apart on the same script.
suppressPackageStartupMessages({library(ggplot2); library(patchwork)})

## Paths resolve from this script's own location, so the project can be moved.
.script_dir <- function() {
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f)) normalizePath(dirname(f)) else normalizePath(getwd())
}

HERE <- dirname(.script_dir())   # source/
OUT  <- .script_dir()
set.seed(20260803)

## coordination = pairwise match rate: P(two independent draws from the cell's
## choice policy agree) = sum_k p_k^2.  Chance (2 options) = 0.5.
mrate <- function(x) { p <- as.numeric(table(x)) / length(x); sum(p^2) }
boot  <- function(x, B = 5000) {
  d <- replicate(B, mrate(sample(x, length(x), replace = TRUE)))
  as.numeric(quantile(d, c(.025, .975)))
}

## one global identity scale so a hue always means the same framing in both panels;
## the "unknown" baseline is deliberately the muted ink, not a series hue.
IDENT <- c(self = "copies of you", shared_dist = "same distribution",
           other = "a different AI", neutral = "unknown")
COL <- c("copies of you" = "#2a78d6", "same distribution" = "#1baf7a",
         "a different AI" = "#eb6834", "unknown" = "#898781")

readrun <- function(files) {
  d <- do.call(rbind, lapply(files, function(f) {
    x <- read.csv(file.path(HERE, f), stringsAsFactors = FALSE)
    x$run <- gsub("^selfcoord_identity_|\\.csv$", "", f)   # gsub: strip BOTH ends
    x
  }))
  d[!d$chosen_shape %in% c("", "?"), ]
}

cellify <- function(d) {
  out <- do.call(rbind, lapply(split(d, list(d$pair, d$identity), drop = TRUE), function(g) {
    ci <- boot(g$chosen_shape)
    data.frame(pair = g$pair[1], type = g$type[1], identity = g$identity[1],
               n = nrow(g), m = mrate(g$chosen_shape), lo = ci[1], hi = ci[2])
  }))
  out$identity <- factor(unname(IDENT[out$identity]), levels = unname(IDENT))
  ord <- tapply(out$m, out$pair, mean)
  out$pair <- factor(out$pair, levels = names(sort(ord)))
  out
}

## run A: 4-stimulus salience battery, n=12/cell, self / other / neutral
rawA <- readrun("selfcoord_identity_20260730_144039.csv")
## run B: the two salience-absent runs, n=24/cell each, pooled.
##   150646 -> self / other   / neutral
##   154134 -> self / shared_dist / neutral
rawB <- readrun(c("selfcoord_identity_20260730_150646.csv",
                  "selfcoord_identity_20260730_154134.csv"))
A <- cellify(rawA)
B <- cellify(rawB)

## ---------------------------------------------------------------- contrasts ----
## Matched sets only: the focal control (proto) is at ceiling in every arm and can
## only dilute. Each contrast is the mean over matched stimuli of
## match(identity) - match(unknown), so a stimulus cannot dominate by cell size.
MATCHED <- c("noise", "mirror")

adv <- function(d, a, b) mean(vapply(MATCHED, function(p) {
  mrate(d$chosen_shape[d$pair == p & d$identity == a]) -
  mrate(d$chosen_shape[d$pair == p & d$identity == b])
}, numeric(1)))

## bootstrap the difference: resample WITHIN each cell, both arms, per draw
adv_ci <- function(d, a, b, B = 5000) {
  dr <- replicate(B, mean(vapply(MATCHED, function(p) {
    xa <- d$chosen_shape[d$pair == p & d$identity == a]
    xb <- d$chosen_shape[d$pair == p & d$identity == b]
    mrate(sample(xa, length(xa), TRUE)) - mrate(sample(xb, length(xb), TRUE))
  }, numeric(1))))
  as.numeric(quantile(dr, c(.025, .975)))
}

## one-sided permutation test: shuffle the identity label within stimulus
perm_p <- function(d, a, b, B = 10000) {
  d <- d[d$pair %in% MATCHED & d$identity %in% c(a, b), ]
  obs <- adv(d, a, b)
  hit <- 0L
  for (i in seq_len(B)) {
    dd <- d
    for (p in MATCHED) {
      k <- which(dd$pair == p)
      dd$identity[k] <- sample(dd$identity[k])
    }
    if (adv(dd, a, b) >= obs) hit <- hit + 1L
  }
  (hit + 1) / (B + 1)
}

## self is pooled across both runs; other / shared_dist exist in one run each and
## are contrasted against THAT run's own unknown arm, never the pooled one.
r1 <- rawB[rawB$run == "20260730_150646", ]
r2 <- rawB[rawB$run == "20260730_154134", ]

CONTRASTS <- list(
  list(lab = "copies of you  vs unknown\npooled, n = 48 per arm", d = rawB, a = "self",        b = "neutral", key = "copies of you",     hl = TRUE),
  list(lab = "copies of you  vs unknown\nrun 1 only, n = 24",     d = r1,   a = "self",        b = "neutral", key = "copies of you",     hl = FALSE),
  list(lab = "copies of you  vs unknown\nrun 2 only, n = 24",     d = r2,   a = "self",        b = "neutral", key = "copies of you",     hl = FALSE),
  list(lab = "a different AI vs unknown\nrun 1 only, n = 24",     d = r1,   a = "other",       b = "neutral", key = "a different AI",    hl = FALSE),
  list(lab = "same distribution vs unknown\nrun 2 only, n = 24",  d = r2,   a = "shared_dist", b = "neutral", key = "same distribution", hl = FALSE))

C <- do.call(rbind, lapply(CONTRASTS, function(x) {
  ci <- adv_ci(x$d, x$a, x$b)
  data.frame(lab = x$lab, key = x$key, hl = x$hl,
             d = adv(x$d, x$a, x$b), lo = ci[1], hi = ci[2],
             p = if (x$hl) perm_p(x$d, x$a, x$b) else NA_real_)
}))
C$lab <- factor(C$lab, levels = rev(C$lab))
C$key <- factor(C$key, levels = names(COL))

cat("\n=== salience-absent cells (pooled where noted) ===\n")
print(within(B[order(B$pair, B$identity), c("pair", "identity", "n", "m", "lo", "hi")],
             {m <- round(m, 3); lo <- round(lo, 3); hi <- round(hi, 3)}), row.names = FALSE)
cat("\n=== contrasts on matched sets (noise + mirror), vs the unknown baseline ===\n")
print(within(C[, c("lab", "d", "lo", "hi", "p")],
             {lab <- gsub("\n", " | ", lab); d <- round(d, 3)
              lo <- round(lo, 3); hi <- round(hi, 3); p <- round(p, 4)}), row.names = FALSE)

## ------------------------------------------------------------------ panels ----
panel <- function(d, tag) {
  ggplot(d, aes(m, pair, colour = identity)) +
    geom_vline(xintercept = .5, linetype = "dashed", colour = "#898781", linewidth = .4) +
    geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0, linewidth = 2,
                   alpha = .28, position = position_dodge(width = .62)) +
    geom_point(size = 2.6, position = position_dodge(width = .62)) +
    scale_colour_manual(values = COL, name = NULL, drop = FALSE) +
    scale_x_continuous(limits = c(.42, 1.03), breaks = c(.5, .75, 1),
                       labels = c("0.5\nchance", "0.75", "1.0")) +
    scale_y_discrete(labels = function(p) paste0(p, "  ")) +
    labs(subtitle = tag, x = NULL, y = NULL) +
    theme_minimal(base_size = 11) +
    theme(panel.grid.minor = element_blank(),
          panel.grid.major.y = element_line(colour = "#e1e0d9", linewidth = .3),
          panel.grid.major.x = element_line(colour = "#e1e0d9", linewidth = .3),
          plot.subtitle = element_text(size = 9.5, colour = "#52514e"),
          axis.text.y = element_text(face = "bold", colour = "#0b0b0b"),
          axis.text.x = element_text(colour = "#898781"),
          legend.position = "none", legend.key.height = unit(9, "pt"),
          legend.text = element_text(size = 9.5))
}

## one legend for the whole figure. Panel A has no `shared_dist` cells, so its
## key would come out blank -- seed the legend from an off-scale dummy layer
## (x = -1 is outside the panel limits and is clipped away).
key <- data.frame(m = -1, pair = levels(A$pair)[1],
                  identity = factor(unname(IDENT), levels = unname(IDENT)))
pA <- panel(A, "salience battery · n = 12 per cell") +
  geom_point(data = key, size = 2.6) +
  guides(colour = guide_legend(nrow = 1)) +
  theme(legend.position = "top", legend.margin = margin(b = 2))
pB <- panel(B, "salience removed · runs pooled · n = 48 (blue, grey) / 24 (green, orange)") +
  labs(x = "pairwise match rate")

## Panel C: the contrast the eye cannot read off overlapping cell CIs.
plab <- sprintf("permutation p = %.2f", C$p[C$hl])
pC <- ggplot(C, aes(d, lab, colour = key)) +
  geom_vline(xintercept = 0, linetype = "dashed", colour = "#898781", linewidth = .4) +
  geom_errorbarh(aes(xmin = lo, xmax = hi, alpha = hl), height = 0, linewidth = 2) +
  geom_point(aes(size = hl)) +
  annotate("text", x = C$hi[C$hl] + .012, y = 5, label = plab,
           hjust = 0, size = 3, colour = "#52514e") +
  scale_colour_manual(values = COL, guide = "none") +
  scale_alpha_manual(values = c(`FALSE` = .18, `TRUE` = .3), guide = "none") +
  scale_size_manual(values = c(`FALSE` = 2.2, `TRUE` = 3.2), guide = "none") +
  scale_x_continuous(limits = c(-.16, .34), breaks = c(-.1, 0, .1, .2, .3)) +
  labs(subtitle = "the contrast itself · matched sets only (noise + mirror)",
       x = "difference in match rate vs the unknown baseline", y = NULL) +
  theme_minimal(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        panel.grid.major.y = element_blank(),
        panel.grid.major.x = element_line(colour = "#e1e0d9", linewidth = .3),
        plot.subtitle = element_text(size = 9.5, colour = "#52514e"),
        axis.text.y = element_text(size = 8.2, colour = "#0b0b0b", lineheight = .95),
        axis.text.x = element_text(colour = "#898781"))

fig <- (pA / pB / pC) +
  plot_layout(heights = c(4, 3, 3.4)) +
  plot_annotation(
    title = "Coordination is set by the stimulus; identity moves it a little, if at all",
    subtitle = paste("GPT-5.4, 6 players, one shot, no communication · shape position",
                     "randomized per player"),
    caption = paste0("Bars = 95% bootstrap CI (5,000 draws). Coordination = P(two independent",
                     " draws agree); chance = 0.5.\nContrasts are the mean over matched stimuli",
                     " of match(framing) - match(unknown); permutation test shuffles the identity",
                     "\nlabel within stimulus (10,000 draws, one-sided)."),
    theme = theme(plot.title = element_text(face = "bold", size = 14, colour = "#0b0b0b"),
                  plot.subtitle = element_text(colour = "#52514e", size = 9.5),
                  plot.caption = element_text(colour = "#898781", size = 7.5, hjust = 0)))

pdf(file.path(OUT, "stage2_identity_vs_salience.pdf"), width = 7.4, height = 8.6)
print(fig); invisible(dev.off())
png(file.path(OUT, "stage2_identity_vs_salience.png"), width = 1480, height = 1720, res = 190)
print(fig); invisible(dev.off())
cat("\nwrote stage2_identity_vs_salience.pdf/.png\n")
