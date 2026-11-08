## =====================================================================
## Partner-specific coordination — Task 2: full coordination matrix
## =====================================================================
## Estimates GPT-GPT, Claude-Claude, and GPT-Claude pairwise match
## probabilities per stimulus from Arm-1 semantic-choice MARGINALS
## (never by pairing rows), with orientation-stratified bootstrap CIs,
## self-advantage quantities, and a transparent diagnostic classification.
##
## IMPORTANT SCOPE NOTE: Arm-1 was collected under the ORIGINAL GENERIC
## framing ("another instance of you"), NOT a named GPT-vs-Claude partner.
## These are therefore GENERIC-FRAMING coordination probabilities. The
## named-partner ground truth for the follow-up must be recomputed from
## policies elicited under naming (see README).
## =====================================================================

suppressPackageStartupMessages({
  library(dplyr); library(tidyr); library(readr); library(purrr)

## Paths resolve from this script's own location, so the project can be moved.
.script_dir <- function() {
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f)) normalizePath(dirname(f)) else normalizePath(getwd())
}
  library(tibble); library(ggplot2); library(patchwork); library(ggrepel); library(stringr)
})

## ---- CONFIG (edit freely) -------------------------------------------
ROOT <- "/Users/calypsocalcott/LLM_Coordination/Name_game_experiment"
OUT  <- .script_dir()
DATA <- file.path(ROOT, "confidence_calib_20260801_160108.csv")   # authoritative 2,520-row file
SEED <- 20260802
B    <- 5000                       # bootstrap draws (>= 5000)

# diagnostic-classification thresholds (explicit + easy to change)
TH_WITHIN_HIGH    <- 0.75   # within-model match considered "high"
TH_CROSS_HIGH     <- 0.75   # cross-model match considered "high" (shared focal)
TH_ADV_MEANINGFUL <- 0.10   # |self-advantage| considered "meaningful"
TH_FLAT_CEIL      <- 0.60   # all pairings below this -> "universally flat"
WEAK_PREF_MARGIN  <- 0.05   # DESCRIPTIVE ONLY (not used for inference)

MCOL <- c("GPT-5.4"="#eb6834", "Claude Opus 4.8"="#2a78d6")

## ---- STIMULUS OPTION MAP (canonical reporting referent = option A) ---
stim_map <- tribble(
  ~stimulus, ~type,      ~canonical_option_A, ~canonical_option_B,
  "proto",   "focal",    "circle",   "square",
  "nd2",     "focal",    "p2a",      "p2b",
  "inkblot", "matched",  "ib-A",     "ib-B",
  "rot",     "matched",  "blob",     "blob-rot90",
  "noise",   "matched",  "noise-A",  "noise-B",
  "mirror",  "matched",  "blob",     "blob-mirror") |>
  mutate(
    raw_position_labels = "raw_choice in {LEFT, RIGHT}",
    recoding_rule = "AB: LEFT=A, RIGHT=B ; BA: LEFT=B, RIGHT=A  (column chosen_shape holds the semantic option)",
    note = if_else(canonical_option_A == "blob",
      "option A 'blob' is the SAME base blob image in rot & mirror; distinct choice context per stimulus", ""))
STIM_LEVELS <- stim_map$stimulus
write_csv(stim_map, file.path(OUT, "stimulus_option_map.csv"))

## ---- LOAD & RECODE (use semantic chosen_shape, never raw position) ---
mlabel <- function(m) if_else(m == "gpt-5.4", "gpt", "claude")
raw <- read_csv(DATA, show_col_types = FALSE) |>
  filter(arm == 1, chosen_shape != "") |>
  transmute(model = mlabel(model), stimulus = pair, variant, chosen_shape) |>
  left_join(select(stim_map, stimulus, canonical_option_A), by = "stimulus") |>
  mutate(chose_A = as.integer(chosen_shape == canonical_option_A),
         stimulus = factor(stimulus, levels = STIM_LEVELS))

## ---- MATCH FUNCTIONS (binary + general sum-over-categories) ----------
m_within <- function(pA) pA^2 + (1 - pA)^2
m_cross  <- function(pAa, pAb) pAa * pAb + (1 - pAa) * (1 - pAb)
# general form for future >2-category stimuli: da, db are named prob vectors
m_general <- function(da, db) {
  ks <- union(names(da), names(db))
  sum(vapply(ks, function(k) (if (is.na(da[k])) 0 else da[k]) *
                              (if (is.na(db[k])) 0 else db[k]), numeric(1)))
}

## ---- POINT-ESTIMATE MARGINALS + COORDINATION MATRIX ------------------
marg <- raw |>
  group_by(model, stimulus) |>
  summarise(n = n(), pA = mean(chose_A), .groups = "drop")

wide <- marg |>
  pivot_wider(names_from = model, values_from = c(pA, n)) |>
  left_join(select(stim_map, stimulus, canonical_option_A, canonical_option_B, type),
            by = "stimulus")

modal_lab  <- function(pA, A, B) if_else(pA >= 0.5, A, B)
modal_prob <- function(pA) pmax(pA, 1 - pA)

cmat <- wide |>
  mutate(
    stimulus = factor(stimulus, levels = STIM_LEVELS),
    p_choose_A_gpt = pA_gpt, p_choose_A_claude = pA_claude,
    match_gpt_gpt        = m_within(pA_gpt),
    match_claude_claude  = m_within(pA_claude),
    match_gpt_claude     = m_cross(pA_gpt, pA_claude),
    gpt_self_advantage    = match_gpt_gpt - match_gpt_claude,
    claude_self_advantage = match_claude_claude - match_gpt_claude,
    modal_choice_gpt    = modal_lab(pA_gpt, canonical_option_A, canonical_option_B),
    modal_choice_claude = modal_lab(pA_claude, canonical_option_A, canonical_option_B),
    modal_prob_gpt    = modal_prob(pA_gpt),  modal_prob_claude = modal_prob(pA_claude),
    margin_gpt        = abs(pA_gpt - 0.5),   margin_claude     = abs(pA_claude - 0.5),
    nA_gpt = round(pA_gpt * n_gpt), nA_claude = round(pA_claude * n_claude),
    exact_tie_gpt    = nA_gpt    == (n_gpt - nA_gpt),
    exact_tie_claude = nA_claude == (n_claude - nA_claude),
    weak_modal_pref_gpt    = margin_gpt    < WEAK_PREF_MARGIN,   # descriptive only
    weak_modal_pref_claude = margin_claude < WEAK_PREF_MARGIN,   # descriptive only
    same_modal_choice = modal_choice_gpt == modal_choice_claude)

## ---- ORIENTATION-STRATIFIED NONPARAMETRIC BOOTSTRAP ------------------
## Resample independent Arm-1 calls within model x stimulus x orientation
## (strata are 30 each -> large enough), pool after (already-semantic)
## recoding, recompute marginals & all match / self-advantage quantities.
## GPT and Claude are resampled INDEPENDENTLY (never paired by row/rep);
## a common draw index only combines two independent bootstrap replicates.
cells <- raw |>
  group_by(model, stimulus, variant) |>
  summarise(x = list(chose_A), .groups = "drop")

boot_pA <- function(model_, stim_) {                 # returns length-B vector of pA*
  v <- filter(cells, model == model_, stimulus == stim_)
  xAB <- v$x[v$variant == "AB"][[1]]; xBA <- v$x[v$variant == "BA"][[1]]
  nAB <- length(xAB); nBA <- length(xBA)
  sAB <- colSums(matrix(sample(xAB, nAB * B, replace = TRUE), nrow = nAB))
  sBA <- colSums(matrix(sample(xBA, nBA * B, replace = TRUE), nrow = nBA))
  (sAB + sBA) / (nAB + nBA)
}

set.seed(SEED)   # reproducible; documented
bp <- tibble(stimulus = factor(STIM_LEVELS, levels = STIM_LEVELS)) |>
  mutate(pA_gpt    = map(as.character(stimulus), ~ boot_pA("gpt", .x)),
         pA_claude = map(as.character(stimulus), ~ boot_pA("claude", .x)))

draws <- bp |>
  transmute(stimulus,
            draw = map(pA_gpt, ~ seq_len(B)),
            p_choose_A_gpt = pA_gpt, p_choose_A_claude = pA_claude,
            match_gpt_gpt       = map(pA_gpt,    m_within),
            match_claude_claude = map(pA_claude, m_within),
            match_gpt_claude    = map2(pA_gpt, pA_claude, m_cross)) |>
  unnest(c(draw, p_choose_A_gpt, p_choose_A_claude,
           match_gpt_gpt, match_claude_claude, match_gpt_claude)) |>
  mutate(gpt_self_advantage    = match_gpt_gpt      - match_gpt_claude,
         claude_self_advantage = match_claude_claude - match_gpt_claude)
write_csv(draws, file.path(OUT, "bootstrap_draws.csv"))     # retained for later contrasts

qlo <- function(x) unname(quantile(x, 0.025)); qhi <- function(x) unname(quantile(x, 0.975))
ci <- draws |>
  group_by(stimulus) |>
  summarise(across(c(p_choose_A_gpt, p_choose_A_claude,
                     match_gpt_gpt, match_claude_claude, match_gpt_claude,
                     gpt_self_advantage, claude_self_advantage),
                   list(lo = qlo, hi = qhi), .names = "{.col}__{.fn}"),
            .groups = "drop")

## ---- DIAGNOSTIC CLASSIFICATION (explicit thresholds) -----------------
classify <- function(GG, CC, GC, gadv, cadv) {
  if (GG >= TH_WITHIN_HIGH && CC >= TH_WITHIN_HIGH && GC >= TH_CROSS_HIGH) return("shared_focal")
  if (GG <  TH_FLAT_CEIL  && CC <  TH_FLAT_CEIL  && GC <  TH_FLAT_CEIL)  return("universally_flat")
  labs <- character(0)
  if (gadv >= TH_ADV_MEANINGFUL) labs <- c(labs, "GPT_specific")
  if (cadv >= TH_ADV_MEANINGFUL) labs <- c(labs, "Claude_specific")
  if (length(labs) == 0) "mixed_other" else paste(labs, collapse = "+")
}

final <- cmat |>
  left_join(ci, by = "stimulus") |>
  rowwise() |>
  mutate(classification = classify(match_gpt_gpt, match_claude_claude,
                                    match_gpt_claude, gpt_self_advantage, claude_self_advantage),
         gpt_self_adv_ci_excl0    = gpt_self_advantage__lo    > 0 | gpt_self_advantage__hi    < 0,
         claude_self_adv_ci_excl0 = claude_self_advantage__lo > 0 | claude_self_advantage__hi < 0) |>
  ungroup() |>
  arrange(desc((match_gpt_gpt + match_claude_claude) / 2))

col_order <- c("stimulus","type","classification",
  "p_choose_A_gpt","p_choose_A_claude","n_gpt","n_claude",
  "match_gpt_gpt","match_gpt_gpt__lo","match_gpt_gpt__hi",
  "match_claude_claude","match_claude_claude__lo","match_claude_claude__hi",
  "match_gpt_claude","match_gpt_claude__lo","match_gpt_claude__hi",
  "gpt_self_advantage","gpt_self_advantage__lo","gpt_self_advantage__hi","gpt_self_adv_ci_excl0",
  "claude_self_advantage","claude_self_advantage__lo","claude_self_advantage__hi","claude_self_adv_ci_excl0",
  "modal_choice_gpt","modal_prob_gpt","margin_gpt","exact_tie_gpt","weak_modal_pref_gpt",
  "modal_choice_claude","modal_prob_claude","margin_claude","exact_tie_claude","weak_modal_pref_claude",
  "same_modal_choice")
final_out <- final |> select(any_of(col_order))
write_csv(final_out |> mutate(across(where(is.numeric), ~ round(.x, 4))),
          file.path(OUT, "coordination_matrix.csv"))

## ground-truth CSV for the follow-up (labelled generic-framing)
gt <- final |>
  transmute(stimulus, type, framing = "generic_self_instance",
            p_choose_A_gpt, p_choose_A_claude, n_gpt, n_claude,
            match_gpt_gpt, match_claude_claude, match_gpt_claude,
            gpt_self_advantage, gpt_self_advantage__lo, gpt_self_advantage__hi,
            claude_self_advantage, claude_self_advantage__lo, claude_self_advantage__hi,
            classification)
write_csv(gt |> mutate(across(where(is.numeric), ~ round(.x, 4))),
          file.path(OUT, "groundtruth_generic_framing.csv"))

## =====================================================================
## FIGURES
## =====================================================================
theme_pc <- theme_minimal(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        plot.title = element_text(face = "bold", size = 12),
        legend.position = "top")
ord <- as.character(final$stimulus)   # easy -> hard order

## Fig 1: coordination matrix (GG / CC / GC) with bootstrap CIs
f1d <- final |>
  transmute(stimulus,
    `GPT-GPT.est` = match_gpt_gpt,             `GPT-GPT.lo` = match_gpt_gpt__lo,             `GPT-GPT.hi` = match_gpt_gpt__hi,
    `Claude-Claude.est` = match_claude_claude, `Claude-Claude.lo` = match_claude_claude__lo, `Claude-Claude.hi` = match_claude_claude__hi,
    `GPT-Claude.est` = match_gpt_claude,       `GPT-Claude.lo` = match_gpt_claude__lo,       `GPT-Claude.hi` = match_gpt_claude__hi) |>
  pivot_longer(-stimulus, names_to = c("pairing", ".value"), names_sep = "\\.") |>
  mutate(stimulus = factor(stimulus, levels = ord),
         pairing = factor(pairing, levels = c("GPT-GPT","Claude-Claude","GPT-Claude")))
PAIRCOL <- c("GPT-GPT"="#eb6834","Claude-Claude"="#2a78d6","GPT-Claude"="#6b7280")
f1 <- ggplot(f1d, aes(stimulus, est, color = pairing)) +
  geom_hline(yintercept = 0.5, linetype = "dashed", colour = "grey60") +
  geom_point(position = position_dodge(.55), size = 2.4) +
  geom_errorbar(aes(ymin = lo, ymax = hi), width = .18, position = position_dodge(.55)) +
  scale_color_manual(values = PAIRCOL, name = NULL) +
  scale_y_continuous(limits = c(0.4, 1.02), breaks = c(.5,.75,1)) +
  labs(title = "A. Coordination matrix by stimulus (generic framing)",
       x = NULL, y = "pairwise match probability") + theme_pc

## Fig 2: self-advantage by stimulus, both models, CIs, zero line
f2d <- bind_rows(
  transmute(final, stimulus, Model = "GPT-5.4", adv = gpt_self_advantage,
            lo = gpt_self_advantage__lo, hi = gpt_self_advantage__hi),
  transmute(final, stimulus, Model = "Claude Opus 4.8", adv = claude_self_advantage,
            lo = claude_self_advantage__lo, hi = claude_self_advantage__hi)) |>
  mutate(stimulus = factor(stimulus, levels = ord))
f2 <- ggplot(f2d, aes(stimulus, adv, color = Model)) +
  geom_hline(yintercept = 0, linetype = "dashed", colour = "grey50") +
  geom_point(position = position_dodge(.5), size = 2.4) +
  geom_errorbar(aes(ymin = lo, ymax = hi), width = .18, position = position_dodge(.5)) +
  scale_color_manual(values = MCOL, name = NULL) +
  labs(title = "B. Self-coordination advantage  (within - cross match)",
       x = NULL, y = "self advantage") + theme_pc

## Fig 3: option-choice distributions (p choose A) by model x stimulus
f3d <- bind_rows(
  transmute(final, stimulus, Model = "GPT-5.4", pA = p_choose_A_gpt,
            lo = p_choose_A_gpt__lo, hi = p_choose_A_gpt__hi),
  transmute(final, stimulus, Model = "Claude Opus 4.8", pA = p_choose_A_claude,
            lo = p_choose_A_claude__lo, hi = p_choose_A_claude__hi)) |>
  mutate(stimulus = factor(stimulus, levels = ord))
f3 <- ggplot(f3d, aes(stimulus, pA, color = Model)) +
  geom_hline(yintercept = 0.5, linetype = "dashed", colour = "grey60") +
  geom_point(position = position_dodge(.5), size = 2.4) +
  geom_errorbar(aes(ymin = lo, ymax = hi), width = .18, position = position_dodge(.5)) +
  scale_color_manual(values = MCOL, name = NULL) +
  scale_y_continuous(limits = c(0,1), breaks = c(0,.5,1)) +
  labs(title = "C. Option-choice distribution  P(choose option A) by model",
       subtitle = "0.5 = no modal focal point; extreme = strong shared focal option",
       x = NULL, y = "P(choose A)") + theme_pc +
  theme(plot.subtitle = element_text(size = 8.5, colour = "grey40"))

## Fig 4: design schematic (x known now, y measured in follow-up)
f4d <- f2d |> rename(empirical_self_adv = adv)
f4 <- ggplot(f4d, aes(empirical_self_adv, 0, color = Model)) +
  annotate("rect", xmin = -Inf, xmax = Inf, ymin = -Inf, ymax = Inf, fill = "grey97") +
  geom_vline(xintercept = 0, linetype = "dashed", colour = "grey60") +
  geom_abline(slope = 1, intercept = 0, linetype = "dotted", colour = "grey45") +
  annotate("text", x = 0.38, y = 0.40, label = "calibrated model-specific\nsensitivity (slope ~ 1)",
           size = 2.7, colour = "grey40", hjust = 1, fontface = "italic") +
  annotate("text", x = -0.28, y = 0.02, label = "generic self-bias = flat (slope ~ 0)",
           size = 2.7, colour = "grey40", hjust = 0, vjust = 0, fontface = "italic") +
  geom_point(size = 2.4) +
  ggrepel::geom_text_repel(aes(label = stimulus), size = 2.4, seed = 1, show.legend = FALSE) +
  scale_color_manual(values = MCOL, name = NULL) +
  coord_cartesian(xlim = c(-0.3, 0.55), ylim = c(-0.15, 0.55)) +
  labs(title = "D. Strongest-test schematic  (y measured in the follow-up)",
       x = "empirical self-coordination advantage (arm 1, this figure)",
       y = "observed self-vs-other confidence advantage\n(to be collected)") + theme_pc

fig <- (f1 | f2) / (f3 | f4) +
  plot_annotation(
    title = "Partner-specific coordination: generic-framing ground-truth matrix",
    subtitle = paste0("Arm-1 semantic choices (N=60/model/stimulus), match probs from marginals (not row-pairing); ",
                      "orientation-stratified bootstrap, ", format(B, big.mark=","), " draws, 95% percentile CIs, seed ", SEED, ".\n",
                      "Ground truth is under GENERIC 'another instance of you' framing; named-partner ground truth is recomputed in the follow-up."),
    caption = "analysis/partner_specific_coordination/01_coordination_matrix.R",
    theme = theme(plot.title = element_text(face="bold", size=13),
                  plot.subtitle = element_text(colour="grey35", size=9),
                  plot.caption = element_text(colour="grey55", size=7)))

pdf(file.path(OUT, "coordination_matrix_figures.pdf"), width = 12, height = 9.4)
print(fig); invisible(dev.off())
png(file.path(OUT, "coordination_matrix_figures.png"), width = 2300, height = 1800, res = 190)
print(fig); invisible(dev.off())

cat("== wrote ==\n",
    "stimulus_option_map.csv, coordination_matrix.csv, groundtruth_generic_framing.csv,\n",
    "bootstrap_draws.csv, coordination_matrix_figures.pdf/.png\n")
print(final |> select(stimulus, classification, match_gpt_gpt, match_claude_claude,
                      match_gpt_claude, gpt_self_advantage, claude_self_advantage) |>
      mutate(across(where(is.numeric), ~round(.x,3))) |> as.data.frame())
