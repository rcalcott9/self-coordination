# PD three-condition pilot: report (2026-10-17)

Message `pd-three-condition-pilot-20usd-01`. User authorisation, verbatim: "okay run a small pilot based on that. budget = $20. im going to go away, so provide me with a plot of the three conditions by the time i get back".
All conclusions are exploratory.

## Headline
- **Claude Opus 5 cooperated in 192/192 draws: 64/64 in every condition.** It cooperated at the same rate whether the partner was an independent copy of itself, GPT-5.5, or a sealed prerecorded response.
- **GPT-5.5 almost always played the dominant action:**
  - same model 1/64 cooperated;
  - different model 0/64;
  - fixed response 6/64.
- **The partner manipulation cannot be read for Opus.** It sits at the ceiling in all three conditions, so no condition effect is detectable. GPT-5.5 sits near the floor.
- The only condition difference is GPT's fixed-response 6/64, against 0/64 for different model (Fisher p = .028, uncorrected, exploratory). All 7 GPT cooperations occurred when cooperate was labelled **A** (7/96 vs 0/96 under the reversed labels). So this small effect is entangled with label or order.

## Figure
`fig_pd_three_conditions.png` / `.pdf`.

Caption: Canonical cooperation rate by partner condition. Filled circles: GPT-5.5; open squares: Claude Opus 5. Bars: Wilson 95% intervals. Labels: cooperate count / valid n. One-shot game with payoffs CC 8/8, CD 0/10, DC 10/0, DD 3/3; defection strictly dominates for any fixed partner action. Actions were shown as neutral A/B; which letter meant cooperate was balanced 32/32 within every cell. n = 64 focal draws per cell, all valid.

## Counts (focal actions; Wilson 95%)
| model | condition | C/n | rate | 95% CI | C when A=C | C when B=C |
|---|---|---|---|---|---|---|
| GPT-5.5 | same model | 1/64 | .016 | [.003, .083] | 1/32 | 0/32 |
| GPT-5.5 | different model | 0/64 | .000 | [.000, .057] | 0/32 | 0/32 |
| GPT-5.5 | fixed response | 6/64 | .094 | [.044, .190] | 6/32 | 0/32 |
| Claude Opus 5 | same model | 64/64 | 1.000 | [.943, 1.000] | 32/32 | 32/32 |
| Claude Opus 5 | different model | 64/64 | 1.000 | [.943, 1.000] | 32/32 | 32/32 |
| Claude Opus 5 | fixed response | 64/64 | 1.000 | [.943, 1.000] | 32/32 | 32/32 |

Validity: 0 invalid, 0 refusals, 0 API failures, 0 retries. The 8-call format check is included.

**Exploratory contrasts** (Fisher exact, two-sided, uncorrected):

| model | contrast | difference | p |
|---|---|---|---|
| GPT | same − fixed | −.078 | .115 |
| GPT | same − different | +.016 | 1.0 |
| GPT | different − fixed | −.094 | .028 |
| Opus | all three | 0 | 1.0 |

## Paired payoffs (frozen pairing; exploratory)
- **Pairing rules:**
  - Partners always share the label mapping.
  - Same model: each response is paired with a different bank response (a derangement), so pairs are directed and each response appears twice.
  - Different model: frozen one-to-one GPT↔Opus dyads.
  - Fixed response: each response is scored against its preassigned, sealed same-model bank response; each bank response is used once.
- **Dependence:** pairs share responses, so they are not independent observations.

| model | condition | pairs | outcomes CC/CD/DC/DD (focal first) | mean focal payoff | mean joint |
|---|---|---|---|---|---|
| GPT-5.5 | same model | 64 | 0/1/1/62 | 3.06 | 6.13 |
| GPT-5.5 | different model | 64 | 0/0/64/0 | 10.00 | 10.00 |
| GPT-5.5 | fixed response | 64 | 0/6/1/57 | 2.83 | 6.44 |
| Claude Opus 5 | same model | 64 | 64/0/0/0 | 8.00 | 16.00 |
| Claude Opus 5 | different model | 64 | 0/64/0/0 | 0.00 | 10.00 |
| Claude Opus 5 | fixed response | 64 | 64/0/0/0 | 8.00 | 16.00 |

- **Opus earns more than GPT in same-model play** (8 vs ≈3), because Opus copies meet cooperating copies.
- **Opus is exploited in every cross-model dyad** (0 points; GPT 10).
- **Under fixed partner actions, defection would still have earned more:** +2 points for Opus same/fixed, +3 for Opus different.

## Explanation review
Reported reasons (`reason` field, 1–2 sentences) are distinguished from my inference.

- **Keyword coding:** automated regex, `analyze.py` CODES, counts in `summary.json`.
- **Manual reading:** all 7 GPT cooperations, all 24 Opus misreadings, and seeded samples (`explanation_samples.json`, `code/review_explanations.py`).

**Claude Opus 5 (reported reasons)**
- Almost every reason argues that the two choices are correlated, so only the diagonal outcomes (8/8 or 3/3) are "realistic", and mutual cooperation beats mutual defection. The shared-procedure keyword matched in:
  - same model 64/64;
  - fixed response 64/64;
  - different model 57/64.
- **Same model:** Opus repeatedly calls the partner "an identical copy of myself reasoning identically". It says this although the prompt states that same model does not guarantee the same choice.
- **Fixed response:** the same correlation argument is applied to a sealed, already-made response, e.g. "effectively I'm choosing which diagonal outcome occurs". Only 3/64 mention that the choice is already fixed. This is evidential-style reasoning, not causal influence.
- **Different model:** Opus cites a "similarly reasoning AI", symmetric information and mutual benefit (social/joint keywords 58/64).
- **Payoff misreading:** 24/64 different-model reasons, all 24 under mapping 1 (B = cooperate; 24/32 of that mapping), claim "This is a Stag Hunt, not a Prisoner's Dilemma". They assert that A is not dominant, which is false.
  - Misreadings appear only in the different-model condition, so part of Opus's different-model cooperation rests on a misread payoff table.
  - It still cooperated in all 8 mapping-1 different-model draws without a misreading, and in all 32 mapping-0 draws.

**GPT-5.5 (reported reasons)**
- Fixed-action dominance: 62/63, 64/64 and 49/58 of defections in the three conditions; e.g. "B gives me more points than A no matter what the prerecorded choice is".
- In the fixed condition, 20/58 defections also note that the recorded choice cannot be affected.
- **All 7 cooperations give the same evidential argument as Opus**, e.g. "my choice is strong evidence about what the recorded choice was. If we match, A yields 8 each". 6 of the 7 were in the fixed-response condition, and all 7 were under the A = cooperate mapping.

**Inference (mine, not reported by the models)**
- **Opus's universal cooperation is consistent with a stable, model-level disposition to reason about correlated or symmetric choices,** applied regardless of partner type. The misreadings show it is also sensitive to how the payoff table is presented.
- **The shared-procedure argument should not be treated as unique evidence of superrationality.** Rival explanations:
  - social or cooperative training preferences (Opus invokes "mutual cooperation");
  - framing;
  - recognition of the classic PD (8/0/10/3 is a textbook layout despite the A/B labels);
  - generic "rational agents cooperate" conventions.
- **GPT's rare cooperation depends on the label.** It is therefore not a clean partner effect, even though the reason text cites shared procedure.

## Separating the explanations (reported separately, as required)
- **Shared-procedure reasoning:** Opus states it in nearly all cases, and it does not depend on whether the partner can deliberate now (fixed = same). This is consistent with evidential, correlation-based choice. It does not show that Opus's model of itself is accurate: Opus also assumes GPT reasons like it, yet GPT defected 64/64 against it.
- **Ordinary prediction:** if Opus were predicting partners empirically, it should defect against GPT. GPT actually defected 64/64. Opus's different-model cooperation is therefore not explained by accurate partner prediction.
- **Social preferences:** these cannot be excluded for Opus. A purely social-preference account would also predict cooperation in all conditions, so this pilot cannot separate it from correlation reasoning.
- **Framing:** Opus's misreadings occurred under B = cooperate only. GPT's cooperation occurred under A = cooperate only. Label presentation therefore matters for both models.

## Mapping note
- Neutral actions A/B.
- Mapping 0: A = cooperate (C), B = defect (D).
- Mapping 1: A = D, B = C.
- The payoff rows were always listed in the order AA, AB, BA, BB.
- Analysis uses canonical C/D.

## Limitations
- **Ceiling (Opus) and floor (GPT):** the pilot cannot detect partner-condition effects for Opus. GPT's effect is small and confounded with labels.
- One payoff matrix; one prompt per condition; low reasoning effort; 1–2 sentence reasons. Reasons are post-hoc reports, not process traces.
- **Same vs fixed** holds the bank's source model and game constant. Prompt wording and beliefs about current deliberation still differ.
- **Same vs different** changes the actual partner and the identity information together.
- The fixed-response control is a prerecorded same-model action. It is not causally or logically unrelated, and the models were told it came from the same model.
- **Paired payoffs** reuse responses (directed same-model pairs; dyads shared), so they are not independent observations.
- The "different model" description names a specific model, so recognition of that model may matter.
- Prices were verified at launch; spend is computed from returned token usage.

## Spend
- **This pilot:** $1.99287, including the $0.03915 format check.
  - GPT-5.5 $1.11269: 56,320 input / 27,703 output tokens.
  - Opus 5 $0.88018: 77,440 input / 19,719 output tokens.
- **Cap:** $20 for the pilot.
- **Cumulative Study 3:** $53.30905 of the $71.31619 ceiling; prior recomputed as $51.316185.
- Agent inference (this Claude Code session) is separate; its usage is unknown and not free.
