# E18 FULL RUN — code-battery expansion
2026-09-10. Frozen procedure completed on the 5 pilot survivors.
**Expansion spend $11.26 of the $50 cap. Runtime 550 s across both stages.**

---

## 1. Collection integrity

All eight pre-dispatch gates PASS: exactly 5 frozen items · exactly 9 checkpoints · n = 48 per
model × item cell · exactly two complete 24-permutation cycles · exact option-position balance
(every option at every label 12× in every cell) · prompt hash `0339bee6` matches frozen v2 ·
prompt file unedited since freezing · checkpoint ids identical to the Stage 1 ladder.

| | expected | returned | parse fail | transport fail | retries | model-ID mismatch | duplicate trials | missing cells |
|---|---|---|---|---|---|---|---|---|
| pilot | 816 | 816 | 0 | 0 | 0 | 0 | 0 | 0 |
| **full** | **2,160** | **2,160** | **0** | **0** | **0** | **0** | **0** | **0** |

45 of 45 cells complete at n = 48. No integrity gate failed, so interpretation proceeds.

## 2. Cost and runtime

| stage | calls | cost | wall clock | rate |
|---|---|---|---|---|
| pilot | 816 | $2.66 | 182 s | 4.5 calls/s |
| full | 2,160 | $8.60 | 368 s | 5.9 calls/s (peak 15.3) |
| **total** | **2,976** | **$11.26** | **550 s** | — |

Projected full-run cost from pilot token usage was $9.75; actual $8.60. Cap $50; **$38.74 unspent**.
The per-endpoint scheduler (9 independent pools, cap 4 each, 36 workers) produced **zero transport
failures across both stages**, against 59 at the comparable Stage 1 stage.

## 3–5. Results, three datasets

| | A original 12 | B expansion 5 | C combined 17 |
|---|---|---|---|
| cells / pairs | 108 / 432 | 45 / 180 | 153 / 612 |
| **fully deterministic cells** | **55%** | **9%** | **41%** |
| cross-family modal agreement | .846 | **.500** | .744 |
| within-family modal agreement | .932 | .838 | .904 |

The screen did what it was for: the expansion battery is six times less collapsed than the original,
and its cross-family modal agreement is at chance-adjacent levels rather than near-unanimity.

## 6. Determinism / alignment decomposition

`log M_AB = ½ log M_AA + ½ log M_BB + log cos θ`, mean residual < 1e-7 in every dataset.

| dataset | total slope | determinism channel | alignment channel | determinism share |
|---|---|---|---|---|
| A original 12 | +0.1214 | +0.0758 | +0.0456 | **62%** |
| **B expansion 5** | **+0.3640** | **+0.1591** | **+0.2050** | **44%** |
| C combined 17 | +0.1928 | +0.1003 | +0.0925 | 52% |

**The expansion does not reproduce the pattern.** In B the alignment channel is the *larger* of the
two. For reference, the Stage 1 visual battery was 99% determinism. So the "agreement rises because
models sharpen" account is battery-dependent, not a general property of the panel.

## 7. Within-family vs cross-family

Determinism-adjusted similarity slope per year, 95% item-clustered bootstrap:

| dataset | within family | cross family |
|---|---|---|
| A original 12 | +0.0222 [−0.0397, +0.1027] | +0.0390 [−0.0258, +0.1332] |
| B expansion 5 | +0.0685 [−0.0452, +0.2530] | +0.1060 [−0.0063, +0.2964] |
| C combined 17 | +0.0358 [−0.0267, +0.1099] | +0.0588 [−0.0095, +0.1455] |

**Every interval contains zero.** No determinism-adjusted convergence is detectable in the code
domain, within family or across it, on any of the three datasets. B's cross-family interval comes
closest to excluding zero but does not, and with 5 items the item-clustered bootstrap is wide by
construction.

## 8. The ceiling result — reported as a finding, with one caveat that weakens it

12 of 17 audited candidates failed the preregistered ceiling screen; 5 survived; 0 near-random,
0 order-sensitive, 0 malformed. Every candidate had minimum effective support exactly 1.000 across
the four boundary checkpoints, and **no item remained live at all four**.

Read plainly: many coding conventions that remain contested or variable among human programmers are
already collapsed onto highly deterministic model conventions. **This design does not distinguish
why.** Prevalence in training data, ecosystem standardisation, instruction tuning, optimisation
toward canonical answers and other shared inductive pressures are all consistent with it, and
nothing here separates them.

**The caveat, which is material and was found by the full run.** The pilot screened at n = 12, where
the finest observable variation is 1/12. On the same 5 items at the same 4 boundary checkpoints,
**12 of 20 cells looked fully deterministic at n = 12 and only 2 of 20 are at n = 48.** The ceiling
rate of 12/17 is therefore an **upper bound**: some excluded items would likely show variation at
n = 48. The screen was applied exactly as frozen and is not being revisited, but the ceiling figure
must be quoted with this attached.

## 9. `x_optional_type` — the control, and its failed prediction

Preregistered qualitative prediction: older checkpoints split, newer checkpoints collapsed.
Observed: **all four boundary checkpoints chose `str | None` unanimously, 12/12 each**, including
`gpt-4-turbo-2024-04-09`.

This **falsifies the specific design assumption** that historical human contestation necessarily
produces detectable policy variation across model generations. PEP 604's union syntax was a live
human argument in 2021 and is not a live model policy in any checkpoint tested, including one whose
training predates the syntax's dominance. The item is retained in the record and named; it is
evidence against the battery-design premise, not a construction failure.

## 10. Limitations

1. **Five items.** Item-clustered bootstrap CIs on B are wide by construction; the dataset can
   exclude little.
2. **The n = 12 ceiling screen overstates determinism** (§8). This bounds the ceiling claim, not the
   full-run results, which are all at n = 48.
3. **Selection.** The 5 items were chosen on a within-model liveness criterion measured at four
   checkpoints, two of which are in the panel. Selection was blind to effect direction and to every
   cross-model statistic, but it is not selection-free.
4. **The expansion items were authored and audited by the same author.** The rubric was independent;
   its application was not.
5. **Common training data is not separable** from independent convergence anywhere in this design.
6. **Thinking off / low effort throughout.** All results are the low-effort policy.
7. **The GPT control surface changes mid-ladder** at 2025-08 and cannot be held fixed.
8. **Convention on this fixed battery only** — 17 code loci, one prompt generation, one n.

## 11. Interpretation — the six questions, answered directly

**1. Does the expansion replicate the original battery's pattern?** **Partly, and not on the thing
that matters.** Modal agreement is directionally similar but much lower (.500 vs .846 cross-family);
the decomposition does **not** replicate — alignment is 56% of B's trend against 38% of A's.

**2. Is increasing agreement again mostly explained by increasing determinism?** **In A yes (62%),
in B no (44%), combined 52%.** The Stage 1 visual finding of 99% determinism does not generalise to
the code domain, and within the code domain the answer depends on which items are in the battery.

**3. Evidence of determinism-adjusted convergence within model families?** **No.** All three
within-family intervals contain zero.

**4. Evidence of cross-family GPT–Claude convergence?** **No.** All three cross-family intervals
contain zero. B's is the closest (+0.1060, lower bound −0.0063) but does not exclude it.

**5. Does the expansion support the claim that many code conventions are already highly stabilised
in model policies?** **Yes, with the §8 bound.** 12 of 17 deliberately contested loci screened out
at ceiling, and even the survivors reach 41% deterministic cells when combined. The n = 12 caveat
means the true rate is lower than 12/17.

**6. Does the full trajectory support the pilot's suggestion that most determinism growth occurred
early?** **No, not as stated.** On the combined battery at n = 48 the fraction of fully deterministic
cells runs GPT 12% → 24% → 47% → **59%**, still rising at the newest checkpoint; Claude runs 53% →
47% → 53% → 35% → **41%**, flat to declining. The pilot's boundary contrast (29% vs 76–82%) conflated
a real GPT trend with the n = 12 artefact of §8 and with Claude's flat profile. **The pilot
interpretation did not survive the full run.**

---

### Outputs
`analysis/out/e18/` — `cell_metrics.csv`, `pair_metrics.csv`, `temporal_slopes.csv`,
`effective_support.csv`, `item_modal_choices.csv`, `summary.json`;
figures `e18_fig1_determinism`, `e18_fig2_decomposition`, `e18_fig3_das_slopes`,
`e18_fig4_modal_matrix` (PDF + 300 dpi PNG).
