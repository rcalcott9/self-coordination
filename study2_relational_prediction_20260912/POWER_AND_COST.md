# Study 2 — sampling, power, cost

## Effect size assumption
The brief asks to power for **G ~ 0.2**, not a full reversal. That is the right target: a full
reversal (prediction moving all the way from SELF to OTHER) would be G ~ 2 x mean TVD ~ 1.3,
which no prior result in this project suggests. Four partner manipulations on Qwen produced
effects of 0.00-0.05; a 0.2 TVD shift here would be a large, clearly interpretable effect.

## Where the variance is
Between **items**, not within. Items differ in how separable the two models' distributions are
(TVD range .50-.88 in the frozen pool). So items are the clustering unit and the sample-size
question is "how many items", with repetitions only reducing per-item measurement noise.

With 13 items and an assumed between-item sd of G ~ 0.25:
`SE = 0.25 / sqrt(13) = 0.069`, 95% CI halfwidth ~ **0.136**. That detects G = 0.2 but not
G = 0.1.

## Repetitions
Predictions at temperature 0 would give one point per cell and no measurement-error estimate.
**10 repetitions per (item x focal x condition)** at temperature 1.0 gives a stable mean
distribution (SE of each probability ~0.15/sqrt(10) ~ 0.05) while keeping cost low. Going to 20
reps halves within-cell noise but leaves the CI essentially unchanged, because between-item
variance dominates.

## Total calls
13 items x 2 focal models x 2 partner conditions x 10 reps = **520 calls**

## Cost
Prior 4-option runs in this project cost ~$0.0153/call for gpt-5.5 + claude-opus-5 combined
(3,600 calls ~ $55 on battery5), with comparable image prefill and shorter completions.
Study 2 completions are ~40 tokens (four percentages).

**Estimated: 520 x $0.0153 ~ $8.00.** Call it **$8-10** with retry overhead.

## Third-party baseline (specified, NOT run)
A model that is neither target predicts both. Cheapest defensible version: **Claude Opus 4.8**
(same family as one target but a different checkpoint) or **GPT-4.1**, predicting each target
family on the same 13 items, 10 reps => 13 x 2 targets x 10 = 260 calls ~ $4.

Purpose: separates "knows its own policy" from "knows what a generic capable model does with
these stimuli". If a third party predicts GPT and Opus about as well as they predict
themselves, the relational result is about stimulus legibility, not self-knowledge.
Recommend running it **only if the primary shows G > 0**; otherwise it answers a question
that no longer arises.
