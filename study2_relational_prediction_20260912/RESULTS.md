# Study 2 — relational prediction. Both models: null.

Frozen manifest `data/frozen_items.json`, sha256
`9403d84302d9166ed201f9e964093837bfd87cd5f2b01d0b2d1bd8c7d519abe7` (verified before launch).
11 items x 2 focal x 2 conditions x 10 reps = **440 calls. 440/440 parsed, 0 transport
failures, 0 parse failures. ~$6.70.** Nothing about the item set, prompts, model configs,
conditions, analysis plan or shape-identity anchoring was altered.

## Primary — G (relational gating)

| | GPT-5.5 focal | Opus 5 focal |
|---|---|---|
| **G** | **+0.0206** | **−0.0004** |
| 95% CI, item-clustered | [−0.015, +0.046] | [−0.056, +0.064] |
| 95% CI, **family**-clustered | [−0.037, +0.043] | [−0.026, +0.039] |
| items with G > 0 | **10 / 11** | 3 / 11 |

Neither model shows relational gating. Every interval contains zero under both clustering
schemes.

**GPT is the more interesting cell.** G is small but 10 of 11 items point the same way — a sign
pattern that would be unlikely by chance — yet the magnitude (~0.02 TVD units) is an order below
the 0.2 the study was powered for, and one item (`F36_split_m2`, G = −0.140) is large enough to
pull the mean on its own. **Opus is flatly null**: 3/11 positive, mean −0.0004.

## Distances (3-6) — the finding behind the null

| | GPT focal | Opus focal |
|---|---|---|
| COPY -> SELF | **0.371** | 0.510 |
| COPY -> OTHER | 0.616 | **0.417** |
| DIFFERENT -> SELF | 0.395 | 0.503 |
| DIFFERENT -> OTHER | 0.619 | **0.410** |

**GPT predicts SELF-like in both conditions** (0.371 vs 0.616 — much closer to its own policy),
and relabelling the partner moves it by 0.024. It behaves as though every partner is a copy.

**Opus predicts OTHER-like in both conditions** (0.417 vs 0.510 — closer to *GPT's* distribution
than to its own), and relabelling moves it by 0.007. That is not a failure to condition on the
partner so much as a systematically mis-centred prediction: when asked to predict a copy of
itself, Opus's best guess is closer to GPT's behaviour than to its own.

## Accuracy (7) — Brier against the stated target

| | COPY -> SELF | DIFFERENT -> OTHER |
|---|---|---|
| GPT focal | **0.190** | 0.541 |
| Opus focal | 0.382 | **0.239** |

GPT is accurate about itself and poor about Opus; Opus is the reverse. Total COPY->DIFFERENT
distribution shift is tiny in both (TVD 0.048 / 0.054).

## Descriptives for plotting

| | mass on SELF modal | mass on OTHER modal |
|---|---|---|
| GPT: COPY -> DIFFERENT | 0.420 -> 0.390 (**−0.030**) | 0.216 -> 0.212 (−0.003) |
| Opus: COPY -> DIFFERENT | 0.322 -> 0.329 (+0.007) | 0.322 -> 0.327 (+0.005) |

GPT does shed a little mass from its own modal choice under DIFFERENT — the right direction —
but does not move it onto Opus's modal choice. The mass goes to the other two options, i.e. it
hedges rather than re-targets. Opus moves neither.

## Robustness — F10_curvature collapsed

4 of 11 items are `F10_curvature`, all sharing the GPT->3 / Opus->0 pattern, so they are not
independent observations. Treating each family as one unit (n = 6 families):

| | G (family means) | 95% CI |
|---|---|---|
| GPT-5.5 | +0.0016 | [−0.056, +0.040] |
| Opus 5 | +0.0024 | [−0.020, +0.031] |

**GPT's +0.0206 falls to +0.0016 once F10 is collapsed** — i.e. most of the apparent signal was
four correlated measurements of one stimulus property. This is the robustness check earning its
keep, and it is why the 10/11 sign pattern should not be over-read.

## Verdict

Neither GPT-5.5 nor Opus 5 conditions its prediction of another agent on whether that agent is
described as a copy of itself or as the other model family. The frozen items are genuinely
discriminating (re-measured TVD 0.42-0.83 at n = 100), so the null is not a stimulus failure.

The asymmetry is the substantive result: GPT defaults to predicting itself, Opus defaults to
predicting something closer to GPT than to itself. Both are insensitive to the partner label.

## Not done
- reasoning traces not inspected or coded (as instructed)
- third-party baseline specified in `POWER_AND_COST.md`, not run — and per that document it is
  recommended only if the primary showed G > 0, which it did not

---

# Reasoning-trace analysis (exploratory, run after the prediction analysis)

280 / 440 responses carried reasoning content — **GPT 186, Opus 94**. Coverage is asymmetric
and not under our control (GPT returns a reasoning summary, Opus a thinking block; both only
when the API emits one). Regex coder, multi-label, hand-validated on 20 random traces.

## The two models fail the manipulation for completely different reasons

| code | GPT COPY | GPT DIFF | Δ | | Opus COPY | Opus DIFF | Δ |
|---|---|---|---|---|---|---|---|
| partner mentioned | 0.604 | 0.578 | −0.026 | | **0.000** | **0.000** | 0.000 |
| **names the other family** | 0.052 | **0.322** | **+0.270** | | 0.000 | 0.000 | 0.000 |
| reasons about model *difference* | 0.021 | 0.033 | +0.013 | | 0.000 | 0.000 | 0.000 |
| reasons about model *sameness* | 0.135 | 0.022 | −0.113 | | 0.000 | 0.015 | +0.015 |
| **stimulus salience** | 0.885 | 0.822 | −0.063 | | 0.862 | **0.938** | +0.076 |
| Schelling / focal point | 0.469 | 0.244 | **−0.224** | | 0.345 | 0.354 | +0.009 |
| position / randomisation | 0.698 | 0.444 | **−0.253** | | 0.000 | 0.015 | +0.015 |

**Opus never mentions the partner. Not once in 94 traces**, in either condition. Its traces
average **198 characters** against GPT's **918**, and consist almost entirely of salience
judgements:

> "Comparing the fill levels across the shapes, D stands out as the most densely filled at
> around 60%, while A is the least filled at roughly 38%. D's extremity likely makes it the
> most distinctive choice."

That is a complete explanation of Opus's exact null (G = −0.0004): the partner label never
enters the computation. Opus answers "which shape is most distinctive", not "what will *that
agent* choose".

**GPT registers the label but does not use it.** Naming Opus rises from 0.05 to 0.32 under
DIFFERENT — the manipulation is read. But reasoning about how Opus *differs* stays at 0.03 in
both conditions, and salience reasoning dominates at 0.85 throughout. GPT substitutes the
partner's name into the same salience computation:

> "**Evaluating options for Opus.** I'm considering the options Opus tends to pick, focusing
> on what's distinct and interesting. Option 3 stands out with its vertical spiky
> protrusions…"

It says "for Opus" and then reasons about distinctiveness exactly as it would for itself.

## A tempting correlation that does not survive

Across the 11 items, GPT's rate of naming Opus correlates with item-level gating at
**r = +0.50**. But it is carried entirely by one point: `F36_split_m2` has a naming rate of
0.00 and G = −0.140. **Dropping it gives r = −0.30.** Among the other ten items naming rate
and gating are unrelated. Reported because it looked like a mechanism and is not one.

## What the trace-level picture adds to the behavioural null

The behavioural result said partner identity does not move predictions. The traces say why,
and the two answers differ by model:

- **Opus** — the label is never represented. This is a failure of *encoding*.
- **GPT** — the label is represented and even verbalised, but does not propagate into the
  inference. This is a failure of *use*.

Both models are doing the same underlying thing: predicting whichever shape is most salient,
for any agent. That is consistent with the distance results, where GPT predicts SELF-like
regardless and Opus predicts OTHER-like regardless — both are really predicting
*stimulus-like*, and the apparent SELF/OTHER alignment follows from whose own behaviour
happens to be closer to the salience heuristic.

## Limitations

- Coverage is partial (280/440) and asymmetric (GPT 186 vs Opus 94); Opus traces are ~4.6x
  shorter, so its zero counts partly reflect less text to match against. The claim "Opus never
  mentions the partner" is exactly true of the traces we have, not of Opus's computation.
- Regex coder, no negation handling. Hand-check found one false negative class: "another AI"
  is not matched by the `partner_mentioned` pattern, so that code is a slight undercount for
  GPT.
- Single automated coder, no second rater.
- Exploratory throughout. None of this revises the preregistered G result.
