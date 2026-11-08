# SHAPES SELF pilot: reasoning summaries, corrected interpretation, bootstrap check (2026-10-14)

Local analysis only. No API calls were made, and existing results and spending records are unchanged (cumulative Study 3 M07/SHAPES spend is still $1.32999). The fixed-partner pilot was not run.

## Plain-language findings

1. **Corrected interpretation.** Both models' forecasts differ from what was observed:
   - GPT predicted P(KEEP) = .727 on average, against .15 observed (TVD .655).
   - Opus predicted .613, against 1.00 observed (TVD .388).

   The difference between the models is whether actions match the best response implied by their own predictions:
   - **Opus agrees.** Every one of its 20 forecasts implies KEEP, and it chose KEEP in 40/40 actions.
   - **GPT mostly does not.** Every one of its 20 forecasts also implies KEEP, but it chose KEEP in only 6/40 actions; the other 34 were labels.

   Predictions and actions came from separate calls in separate roles. No action call is linked to any prediction call, so this compares two populations of calls, not a single instance contradicting itself.
2. **What GPT's summaries mention.** Action summaries refer to copy symmetry far more often than prediction summaries do: 16/23 vs 3/13. Both roles mention shape salience, option order and safety/expected payoff. This is a description of the text only. Summaries are generated digests, not the full reasoning. 17/40 action and 7/20 prediction calls returned an empty summary even though reasoning tokens were > 0.
3. **Bootstrap check.** The reported CI does resample responses and recompute the all-pairs U-statistic; it reproduces exactly. However, resampling with replacement also pairs duplicate copies of the same response with each other, and those pairs always match. This shifts the interval upward (details in section 3). The recorded result is unchanged; I am raising this as an issue, not applying a fix.

## 1. GPT-5.5 reasoning summaries: action vs prediction calls

**Coding scheme**
- Single coder (Claude); categories can overlap.
- A code requires an explicit reference in the text. Where the text is silent, nothing is coded.
- The scheme has not been reliability-tested. The earlier Study 3 trace coding failed reliability (AC1 .27), so these counts are descriptive only.
- Definitions, per-call codes and the borderline cases (coded 0) are in `code_reasoning.py`.

**Coverage**

| | calls | with non-empty summary | empty summary (reasoning tokens > 0) |
|---|---|---|---|
| action | 40 | 23 | 17 |
| prediction | 20 | 13 | 7 |

**Counts** (denominator: calls with a summary)

| explicit reference to | action (n = 23) | prediction (n = 13) |
|---|---|---|
| Copy symmetry (same model / identical instance / same reasoning / clone / superrationality) | 16 (.70) | 3 (.23) |
| Shape salience (a named shape described as standing out, focal, simplest, canonical, culturally special) | 19 (.83) | 7 (.54) |
| Option order (randomization, position, first-listed option) | 12 (.52) | 10 (.77) |
| Safety / expected payoff (KEEP safe, guaranteed or risk-dominant; expected value; the .7 threshold) | 15 (.65) | 8 (.62) |
| *Supplementary:* alphabetical tie-breaker | 8 (.35) | 2 (.15) |
| None of the four | 0 | 2 (prediction 16, 19) |

**Actions within each category (action calls with a summary)**

| category | calls | KEEP | STAR | CIRCLE |
|---|---|---|---|---|
| all with a summary | 23 | 3 | 11 | 9 |
| Copy symmetry | 16 | 3 | 7 | 6 |
| Shape salience | 19 | 2 | 10 | 7 |
| Option order | 12 | 2 | 4 | 6 |
| Safety / expected payoff | 15 | 3 | 6 | 6 |
| Alphabetical | 8 | 1 | 1 | 6 |

Calls without a summary chose STAR 10, CIRCLE 4, KEEP 3.

**Representative excerpts**

*Action calls*
- Copy symmetry leading to a label: *"Given the identical model may lean towards CIRCLE due to its alphabetical placement, I think it's best for me to also choose CIRCLE."* (action 9 → CIRCLE)
- Shape salience: *"the star is distinct and represents success, which many models tend to recognize as unique. I'll finalize with STAR."* (action 22 → STAR)
- Safety threshold leading to KEEP: *"I lack sufficient confidence—over 70%—that the counterpart will choose 'CIRCLE.' So, 'KEEP' maximizes my expected outcome here."* (action 2 → KEEP)
- Order: *"the order is randomized, and I'm trying to select a unique label based on its semantic meaning."* (action 9)

*Prediction calls*
- Safety: *"Without a robust focal point, 'KEEP' stands out as unique, making it a likely choice with a probability of around 85-95%."* (prediction 3 → KEEP 91%)
- Order: *"I'm considering the model's order bias and wondering if averaging would eliminate that bias."* (prediction 0 → KEEP 95%)
- Self-as-player statement: *"If I were in the same situation, I would definitely choose KEEP."* (prediction 4 → KEEP 90%)

**Counterexamples**
- Copy symmetry cited, KEEP chosen (3 actions):
  - action 16: *"If I have the same model, I might be able to achieve a probability greater than 0.7"*, then *"keeping the strategy is the safest"*. Choice: KEEP.
  - Also actions 2 and 26.
- The .7 threshold cited, label chosen:
  - action 27: *"I need to believe that the probability of someone choosing my label is greater than 0.7 to beat KEEP. That's challenging. However, if there's a high correlation in identical instances, it could work."* Choice: CIRCLE.
  - action 34: similar, choice STAR.
- Copy symmetry cited in a prediction call that still forecasts mostly KEEP:
  - prediction 14: *"players know they're using the same model"*, then *"many might just default to KEEP"*. Forecast: KEEP 78%.
  - Also prediction 6 (KEEP 70%).
- Label-heavy forecasts. Most GPT forecasts are KEEP-heavy, but predictions 16 (STAR 45%, KEEP 35%) and 17 (STAR 65%, KEEP 20%) are not, and neither summary refers to any of the four categories. Among the empty-summary forecasts, prediction 1 gives CIRCLE 35% and prediction 7 gives CIRCLE 45%, KEEP 35%.
- Salience without a label choice: actions 2 and 26 discuss CIRCLE/STAR standing out, then choose KEEP.

**Not inferred.** The text does not say why the two roles differ. Copy-symmetry references are rarer in prediction summaries; whether that reflects the role framing, summary compression, or anything else is not established. Opus summaries were not coded; the request covered GPT action vs prediction only.

## 2. Corrected interpretation (replaces "GPT predicts 73% KEEP but plays 15%")

| | mean predicted P(KEEP) | observed KEEP | TVD | forecasts implying KEEP | actions that are KEEP |
|---|---|---|---|---|---|
| Opus 5 | .613 | 1.00 (40/40) | .388 | 20/20 | 40/40: agree with implied best response |
| GPT-5.5 | .727 | .15 (6/40) | .655 | 20/20 | 6/40: 34/40 do not agree |

Both forecasts are miscalibrated against observed play; they err in opposite directions on KEEP. Prediction and action are elicited in different calls and roles, so the comparison is between populations of calls and is not evidence about any single call.

## 3. All-pairs CI: method and verification

**Method, as implemented** (`code/selfplay.py`, `allpairs` and `boot`)
- Nonparametric percentile bootstrap.
- 2,000 replicates; RNG seeded with `"20261014-boot-0"`.
- Each replicate draws n = 40 valid action choices with replacement and recomputes the all-pairs U-statistic: mean points over all C(40,2) unordered pairs, both players.
- The CI is the sorted replicates at indices 50 and 1949, i.e. approximately the 2.5th and 97.5th percentiles.

**Verification**
- Recomputing reproduces the recorded intervals exactly:
  - GPT [4.4769, 5.7340];
  - Opus [7.00, 7.00], degenerate because all choices are KEEP.

**Issue: pairs between duplicated draws**
- Within a replicate, two copies of the same original response are paired with each other, and those pairs always match.
- This inflates the coordination estimate:
  - bootstrap mean 4.868 vs point estimate 4.742;
  - only 42.9% of replicates fall below the point estimate.
- **Diagnostic only, not adopted:** excluding copy-to-copy pairs gives mean 4.748 and a 95% interval of [4.35, 5.60].
- **Decision needed from the user:** keep the recorded CI with a note, or adopt the copy-excluded version, before reporting.

## Evidence

All files are in `study3_item_SHAPES_20261014/results/run_20261014_002715/analysis_reasoning_20261014/`:
- `code_reasoning.py`: definitions, per-call codes, borderline notes; it reruns the counts.
- `gpt_reasoning_coded.json`: the 60 GPT calls with summary text and codes.
- `counts.json`

Source: `pilot_responses.jsonl` (unchanged).
