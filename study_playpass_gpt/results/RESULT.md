# GPT PLAY/PASS — Study 1 arm

**Model** `gpt-5.5-2026-04-23` (returned on all 600 calls), reasoning effort low, summary auto.
**Design** frozen before any PLAY/PASS call: item set sha8 `8ee3a56e`, prompt sha8 `cbc2592c`.
**Items** 30 arrays from VIS-FRAME-41 — HIGH = top 15 by measured `within_model_match`
(mean .9889), LOW = bottom 15 (mean .4319), separation .5570, zero overlap, 15 distinct
families per arm. Agreement labels come from `stage1_frame/cell_metrics.csv`, n = 48
draws/array, same model.
**Run** 15+15 items × 20 reps = 600 decisions, seed 20260912, option-order permutation
sampled per trial. Data `data/playpass_full_20260912_191607.csv`.

## Integrity and cost
600/600 parsed, 0 transport failures, 0 model mismatches. Total **$6.8473**
($0.01141/call, against $0.01194 measured in the 60-call pilot).

## Primary result — GPT discriminates its own stable states
| | |
|---|---|
| P(PLAY \| HIGH) | **.8267** [.780, .865] (248/300) |
| P(PLAY \| LOW) | **.4467** [.391, .503] (134/300) |
| difference | **+.380**, item-clustered 95% CI [+.220, +.543] |
| item-label permutation test | p < .0001 |
| d′ | 1.075 |
| AUC (item-level, 15 v 15, Mann-Whitney) | **.867**, p = .0006 |
| criterion c | −.404 (bias toward PLAY) |
| sensitivity / specificity | .827 / .553 |
| overall P(PLAY) | .637 |

## Graded signal
Spearman(continuous `within_model_match`, item P(PLAY)) across all 30 items = **+.643**,
p = .0001 (Pearson +.668). But *within* arms the graded relation disappears:
HIGH rho = −.036 (p = .90), LOW rho = +.389 (p = .15). The discrimination is carried by
the coarse HIGH/LOW split, not by a fine-grained read of how stable each state is.

## Robustness
Leave-one-item-out: difference stays in [+.348, +.411], AUC in [.857, .902]. No single
item carries the effect. The most influential are F11_noise_m3 (0/20 PLAY, the cleanest
LOW hit) for the difference and F14_bars_m3 (20/20) for AUC.

Response is not driven by option order or trial position: P(PLAY) across the 24
permutations is flat (χ²(23) = 8.34, p = .998; within HIGH p = .70, within LOW p = .84),
and there is no rep-order trend (rho = −.20, p = .39).

## Item-level misses
Within HIGH, four arrays at agreement 1.000 nonetheless drew PLAY on ≤ 60% of trials
(F41_contain_m1 .40, F24_subdiv_m1 .60, F04_complexity_m3 .60, F22_star_m1 .60) — states
where independent copies actually agree perfectly but the model declines to bet on itself.
Within LOW, F37_mirroraxis_m1 (.50 agreement) drew PLAY on 80% of trials.

## Comparison with Qwen
| | GPT-5.5 | Qwen |
|---|---|---|
| d′ | 1.075 | 0.492 |
| AUC | .867 | .776 |
| c | −.404 | −.442 |

Criterion is nearly identical; GPT is the better discriminator on both statistics. The d′
gap should be read with care — d′ is sensitive to how extreme the response rates are, and
GPT's HIGH/LOW agreement separation (.557) is wider than Qwen's (.296), which makes the
discrimination easier. AUC is the fairer comparison, and GPT leads there by .09.

## Not yet done
Reasoning traces are captured in the `reasoning` column and have **not** been inspected.
Trace coding is a separate step, deliberately held until after this behavioural analysis.

---

# Partner sensitivity — COPY vs DIFFERENT (both at effort low)

Separate contrast, not crossed with the policy test. Same 30 frozen items, same payoff,
same seed, 600 decisions. Only the partner clause and its referent noun differ
(prompt sha8 `cbc2592c` vs `60d134c1`). 600/600 parsed, 0 failures, $6.36.

> DIFFERENT: "an AI model that was trained using a different training dataset and a
> different training algorithm from yours"

| | COPY | DIFFERENT | change |
|---|---|---|---|
| overall P(PLAY) | .6367 | .4967 | **−.1400** |
| HIGH items | .8267 | .7233 | −.1033 |
| LOW items | .4467 | .2700 | −.1767 |

Paired by item (identical arrays in both arms): mean drop **+.1400**, 95% CI
[+.0933, +.1883], Wilcoxon p < .0001. HIGH items +.1033 (p = .0123), LOW items
+.1767 (p = .0010) — **both bands drop significantly**.

Interaction (LOW drop − HIGH drop) = +.0733, 95% CI [−.0200, +.1667],
Mann-Whitney p = .157. Directionally larger on unstable items but **not significant**;
15 items per band is underpowered for this test.

## Reading
GPT bets less on a differently-trained partner, and the discount is not confined to
states where its policy was weak. HIGH-agreement items — the ones with an obvious focal
answer — also drop significantly (−.103). A pure public-salience account predicts no
drop there, since a focal point works for any partner. So partner identity carries weight
beyond stimulus salience for GPT.

Within the DIFFERENT arm the stimulus structure survives: P(PLAY) .723 on HIGH items vs
.270 on LOW (+.453), Spearman with copy-agreement +.707. The model still reads which
stimuli have clear answers; it shifts the whole function down.

**No d′, AUC, or sensitivity is reported for this arm, by design.** Our labels are
`within_model_match` — agreement among GPT *copies* — which is not the ground truth for a
differently-trained partner. This cell measures willingness to bet, not accuracy.

---

# Partner x reasoning effort — the 2x2

Fourth cell: DIFFERENT x high effort, 300 decisions, 0 failures, $12.52.
Collected after an OpenAI org spend limit blocked an earlier attempt (that run produced
34 all-failure rows at $0.00 and is quarantined as `_VOID_spendlimit_*`).

## P(PLAY)
| | COPY | DIFFERENT | partner effect |
|---|---|---|---|
| low effort | .6367 | .4967 | −.1400 |
| high effort | .6300 | .5400 | −.0900 |
| effort effect | −.0067 | +.0433 | |

**Pre-specified interaction is null.** Partner effect at high minus at low = −.0500,
item-clustered 95% CI [−.1183, +.0183], Wilcoxon p = .157. Everything below is
unadjusted sub-analysis and should be read as suggestive.

## Where the partner effect sits, by policy band
| | all 30 | clear policy | no policy |
|---|---|---|---|
| low effort | +.140 (p<.0001) | +.103 (p=.012) | +.177 (p=.001) |
| high effort | +.090 (p=.009) | +.047 (p=.159) | +.133 (p=.028) |

At low effort GPT discounts a differently-trained partner on *both* bands. At high effort
the discount on clear-policy items loses significance while the no-policy discount holds.
That is the shape Opus shows at low reasoning — so more reasoning moves GPT toward the
salience pattern, not away from it.

## Effort effects, paired by item
| partner | all 30 | clear | no policy |
|---|---|---|---|
| COPY | −.007 [−.070, +.050] | +.027 [−.027, +.077] | −.040 [−.150, +.063] |
| DIFFERENT | +.043 [−.028, +.115] | **+.083 [+.010, +.173] p=.032** | +.003 [−.113, +.110] |

The only significant effort effect anywhere is clear-policy items under a DIFFERENT
partner: more reasoning recovers willingness to bet on strongly focal stimuli when the
partner is not a copy. Under COPY, effort moves nothing — consistent with the earlier
finding that effort sharpened *discrimination* (AUC .867 -> .907) without shifting rates.

## Policy discrimination per cell (clear minus no policy)
| cell | difference | 95% CI |
|---|---|---|
| copy/low | +.380 | [+.220, +.540] |
| copy/high | +.447 | [+.280, +.613] |
| different/low | +.453 | [+.290, +.613] |
| different/high | +.533 | [+.340, +.713] |

The stimulus split survives every manipulation and is widest in the DIFFERENT/high cell.
No accuracy claim attaches to the DIFFERENT column: `within_model_match` is copy-copy
agreement, not ground truth for a differently-trained partner.
