# Study 1-HP v2 — cost-optimised design

**DESIGN AND SIMULATION ONLY. Nothing run, no stimuli generated, no API calls.**
Supersedes `DESIGN.md` on cost and sampling; the estimand, claim, selector and
fallback handling are unchanged. 2026-09-05.

## 1. Headline

**16,568 calls, $259–380 all-in — a 39% reduction** from the $428–627 design, with
power at 24 pairs of **0.998 / 0.882 / 0.625** at mu = 0.145 / 0.10 / 0.07.

The estimand, the claim, the eligibility rule, the payoff grid and fallback
eligibility are untouched. The savings come from not spending precision on
stimuli that never enter a pair, and from moving the confidence arm behind
pairing.

## 2. Where the money actually goes

Simulated call volume by component, current design:

| component | calls | share |
|---|---|---|
| Stage A | 17,280 | 38% |
| auditor | 8,640 | 19% |
| salience | 8,640 | 19% |
| confidence | 4,320 | 9% |
| Stage C | 7,200 | 16% |

**Stage A dominates**, and it is the one measured at depth 60 on all 144
model×stimulus cells regardless of whether a cell can ever enter a pair. That is
the target.

## 3. Strategy comparison (200 simulated batteries per row)

| strategy | stim | pairs (p10–p90) | P(≥20) | mis-class | mean true gap | calls | $ all-in |
|---|---|---|---|---|---|---|---|
| 1 current fixed-depth | 72 | 37 (33–41) | 1.00 | 0.38 | 0.390 | 46,080 | $720–1,056 |
| 2 reduced fixed-depth | 72 | 38 (33–42) | 1.00 | 0.45 | 0.378 | 28,800 | $450–660 |
| 3 two-stage adaptive | 72 | 37 (32–43) | 1.00 | 0.44 | 0.380 | 22,999 | $359–527 |
| 4 aggressive breadth-first | 110 | 62 (57–68) | 1.00 | 0.46 | 0.381 | 29,320 | $458–672 |

Power at the realised pair count:

| strategy | Stage C n/cell | mu=.145 | mu=.10 | mu=.07 |
|---|---|---|---|---|
| 1 | 30 | 1.000 | 0.967 | 0.820 |
| 2 | 24 | 1.000 | 0.940 | 0.717 |
| 3 | 24 | 1.000 | 0.950 | 0.760 |
| 4 | 24 | 1.000 | 0.970 | 0.753 |

Strategy 4 buys 62 pairs but spends 28% more than strategy 3 for +0.02 power —
beyond ~25 pairs the curve is flat and extra breadth is wasted. **Strategy 3 is
the efficient point**, and the recommendation below is strategy 3 with the
remaining fat removed.

## 4. What "mis-classification" is, and is not

The 38–46% figure is not 38–46% spurious contrasts. Decomposed by which criterion
a confirmed pair actually violates on its true values (Stage A depth 30):

| Stage B depth | fails \|d_true\| | fails \|d_aud\| | fails \|d_sal\| | mean true gap | p10 gap |
|---|---|---|---|---|---|
| 10 | 0.081 | 0.293 | 0.345 | 0.380 | 0.208 |
| **20** | **0.092** | **0.235** | **0.230** | **0.377** | 0.190 |
| 30 | 0.103 | 0.182 | 0.204 | 0.371 | 0.161 |
| 60 | 0.109 | 0.125 | 0.161 | 0.372 | 0.161 |

The substantive criterion is robust: **only ~9%** of confirmed pairs fail the
own-copy-reliability gap, and the mean true gap is **0.377** against a 0.1725
threshold — more than double. The failures are almost entirely *imperfect
matching* on the public baselines, which weakens the "beyond externally
observable coordinability" control for a minority of pairs rather than
manufacturing an effect.

Some of that is irreducible: the auditor window is |d_aud| <= 0.021 while genuine
between-stimulus auditor variation is SD 0.060, so even at depth 60 (SE 0.0067)
13% of pairs remain imperfectly matched. Depth 20 gives SE 0.0082; going to 60
triples the auditor spend to recover ~10 percentage points. **Not worth it**, and
the robustness analyses report matching quality per pair regardless.

Stage A depth is the one that governs the substantive criterion:

| Stage A confirm depth | fails \|d_true\| | mean true gap |
|---|---|---|
| 15 | 0.135 | 0.356 |
| 20 | 0.131 | 0.356 |
| **30** | **0.099** | **0.373** |
| 45 | 0.052 | 0.394 |
| 60 | 0.044 | 0.392 |

Depth 30 is the knee. Below it mis-direction rises sharply; above it costs double
for 5 percentage points.

## 5. Recommended design

| step | shape | calls | $ all-in |
|---|---|---|---|
| **A1 screen** | 72 stim × 2 models × **20** | 2,880 | $45–66 |
| **A2 confirm** | 116 retained cells × **30** (FRESH) | 3,480 | $54–80 |
| **B auditor** | 116 retained cells × **20** | 2,320 | $36–53 |
| **B salience** | 58 retained stimuli × 2 raters × **20** | 2,320 | $36–53 |
| **B confidence** | 24 pairs × 2 members × **20** | 960 | $15–22 |
| **Stage C** | 24 pairs × 2 × 4 payoffs × **24** | 4,608 | $72–106 |
| **TOTAL** | | **16,568** | **$259–380** |

Phase 1 (gated) 11,960 calls, $187–274. Phase 2 (Stage C) 4,608 calls, $72–106.

## 6. Adaptive sampling rules — frozen in advance

**A1 screen, depth 20, all 144 cells.** Its output is used for **one purpose
only**: dropping cells. It never enters a pair estimate.

**Retention rule (prospective, fixed before any call).** Per focal model, retain
cells whose screened self-match falls in the **top 40% or bottom 40%** of that
model's screened distribution; drop the middle 20%. Rationale: a large-gap pair
needs one clearly-high and one clearly-low member, so mid-band cells cannot be
either. Expected retention 116 of 144 cells.

**A2 confirmation, depth 30, FRESH draws, retained cells only.** These estimates —
and only these — determine pair eligibility. Screening draws are discarded from
the selection statistic. This is the S/C separation, and it is what keeps the
adaptation unbiased: selection is made on data that played no part in the drop
decision.

**Stage B, depth 20, retained cells only.** No B1/B2 split: the simulation shows
a Stage B screen saves little because nearly every retained cell is a plausible
pair member, and splitting Stage B would only add a second peek.

**Sequential top-up, capped.** A cell whose A2 self-match lands within ±0.05 of
the eligibility boundary, or whose auditor difference to its candidate partner
lands within ±0.005 of the 0.021 window, receives **one** top-up of 20 further
draws. Maximum per cell: A1 20 + A2 30 + top-up 20 = **70 draws**, never more.
Top-ups are decided from A2 alone, before any Stage C call, and the topped-up
estimate replaces the A2 estimate for that cell.

**No peeking at Stage C.** Pair eligibility is frozen and SHA-256 hashed before
the first Stage C call. Stage C refuses to run against a table whose hash does not
match. Nothing about Stage C behaviour can feed back into selection.

## 7. Confidence arm placement — option A

Measured on **final matched-pair stimuli only** (48 cells), depth 20, after
freezing and before Stage C. Justification: confidence is secondary, is not a
matching criterion, and plays no part in eligibility, so paying screening cost on
discarded stimuli buys nothing. Cost falls from 4,320 calls to **960** — an 78%
saving on that arm.

The trade-off, stated: no confidence data on non-paired stimuli, so
battery-wide calibration of stated confidence against true self-match cannot be
computed. That analysis was never part of the confirmatory design, and if it is
wanted later it can be added as a standalone arm.

## 8. Stage C depth — 24 per cell

| | 20/cell | 24/cell | 30/cell |
|---|---|---|---|
| mu = 0.145 | 0.988 | **0.998** | 1.000 |
| mu = 0.10 | 0.858 | **0.882** | 0.940 |
| mu = 0.07 | 0.605 | **0.625** | 0.665 |

30 → 24 costs 0.058 power at mu = 0.10 and saves 1,152 calls; 24 → 20 costs a
further 0.024 for 768 calls. **24 is the recommendation.** Going to 20 is
defensible if the total must come down further.

**Payoff grid stays {3,5,7,9}.** Dropping safe=3 and 5 would save 2,304 calls
(~$36–53) but is a *substantive* design change — it redefines the decision task
the estimand is measured on and breaks comparability with Study 1 and the
generation ladder. Not taken. That the previous effect concentrated at 7 and 9 is
an observation about that sample, not a prospective justification.

## 9. Pair yield — the one assumption that matters

Two empirical anchors, and they disagree:

| source | stimuli | eligible | independent pairs | per stimulus per model |
|---|---|---|---|---|
| Study 1 (observed) | 15 | 6 | 4 | 0.13 |
| Opus 4.6 ladder (observed) | 45 | 52 | 8 | 0.18 |
| this simulation | 72 | ~67 | ~37 | 0.26 |

The simulator reproduces Study 1's 15-stimulus funnel closely (3.05 eligible /
1.91 independent per model vs 3 / 2 observed) but **over-predicts** independent
pairs at 45 (9.9 vs 8 observed), because real eligible pairs cluster on a few hub
stimuli more than family random effects capture.

**The design therefore anchors on the conservative empirical ratio, not the
simulation:** 0.178 independent pairs per stimulus per model gives
**72 × 2 × 0.178 ≈ 26 pairs**, with the simulation's 37 as an upper bound. Range
carried forward: **21–37, planning value 24.**

At 60 stimuli the conservative anchor gives 21 — too close to the floor. **Do not
cut the battery below 72.**

## 10. Decision rule and gate

**Hard gate.** Stage C does not run unless Phase 1 yields **≥20 independent
approved pairs** under the unchanged selector. If it yields fewer: expand the
battery, or report the yield as a finding about the battery. **Never loosen the
selector, and never reuse a stimulus to manufacture a pair.**

Success/failure criteria, effect-size bounds on a null, and all robustness
analyses (`pair_kind` stratification, form-consistency adjustment,
leave-one-pair-out, per-model, select-vs-confirm shrinkage, payoff-resolved
deltas) are unchanged from `DESIGN.md` §9 and §11.

## 11. Scientific trade-offs, stated plainly

1. **Stage A 60 → 30 confirmation draws** raises wrong-direction pairs from 4% to
   ~10%. Mitigated by the near-boundary top-up rule and by reporting the true-gap
   distribution per pair. This is the single real cost of the savings.
2. **Stage B 30 → 20** raises imperfect public-baseline matching by ~5 percentage
   points. It weakens the control on a minority of pairs, and is visible in the
   per-pair matching diagnostics rather than hidden.
3. **Confidence on final pairs only** forecloses battery-wide calibration of
   stated confidence. Secondary analysis only; not part of the confirmatory claim.
4. **Stage C 30 → 24** costs 0.058 power at mu = 0.10.
5. **Adaptation adds a selection step.** Controlled by S/C separation: the screen
   drops, fresh confirmation data selects, and Stage C is hash-frozen before it
   runs. The residual risk — that the drop rule discards a cell that fresh data
   would have shown eligible — is bounded by the 40/40 retention band being far
   wider than the screening noise at depth 20.

## 12. Cost reduction summary

| | calls | $ all-in |
|---|---|---|
| current design | 27,360 | $428–627 |
| **recommended** | **16,568** | **$259–380** |
| **reduction** | **−39%** | **−39%** |

with power at 24 pairs of 0.998 / 0.882 / 0.625 at mu = 0.145 / 0.10 / 0.07,
against 1.000 / 0.940 / 0.717 for the more expensive version. **GPT-5.5 pricing
remains unverified and must be confirmed before launch.**
