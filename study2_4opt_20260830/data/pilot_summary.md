# Stage C pilot - decision-scale beta3

`4,800` of `4,800` trials parsed. 8 GPT pairs + 7 Claude pairs, 20 reps per focal x stimulus x partner x safe payoff. **Pilot, not the confirmatory sample.**

## Primary: beta3 by focal model

| focal | payoffs | n HIGH fam | n LOW fam | mean gap HIGH | mean gap LOW | **beta3** | perm p |
|---|---|---|---|---|---|---|---|
| GPT-5.5 | all {3,5,7,9} | 8 | 8 | +0.388 | +0.409 | **-0.022** | 0.6579 |
| Claude Opus 5 | all {3,5,7,9} | 7 | 7 | +0.109 | +0.134 | **-0.025** | 0.5134 |
| GPT-5.5 | informative {5,7} | 8 | 8 | +0.491 | +0.616 | **-0.125** | 0.1754 |
| Claude Opus 5 | informative {5,7} | 7 | 7 | +0.193 | +0.236 | **-0.043** | 0.5532 |

| focal | payoffs | beta3 | 95% CI (family bootstrap) |
|---|---|---|---|
| GPT-5.5 | all {3,5,7,9} | -0.022 | [-0.102, +0.069] |
| Claude Opus 5 | all {3,5,7,9} | -0.025 | [-0.089, +0.041] |
| GPT-5.5 | informative {5,7} | -0.125 | [-0.281, +0.034] |
| Claude Opus 5 | informative {5,7} | -0.043 | [-0.182, +0.089] |

## Main effects (context for beta3)

| focal | level | partner | attempt rate |
|---|---|---|---|
| GPT-5.5 | HIGH | SAME | 0.852 |
| GPT-5.5 | HIGH | DIFF | 0.464 |
| GPT-5.5 | LOW | SAME | 0.733 |
| GPT-5.5 | LOW | DIFF | 0.323 |
| Claude Opus 5 | HIGH | SAME | 0.616 |
| Claude Opus 5 | HIGH | DIFF | 0.507 |
| Claude Opus 5 | LOW | SAME | 0.405 |
| Claude Opus 5 | LOW | DIFF | 0.271 |

## Payoff response (is the grid censoring?)

| focal | level | safe=3 | safe=5 | safe=7 | safe=9 |
|---|---|---|---|---|---|
| GPT-5.5 | HIGH | 0.99 | 0.81 | 0.57 | 0.27 |
| GPT-5.5 | LOW | 0.95 | 0.64 | 0.35 | 0.17 |
| Claude Opus 5 | HIGH | 0.96 | 0.89 | 0.39 | 0.01 |
| Claude Opus 5 | LOW | 0.80 | 0.48 | 0.07 | 0.00 |

## Nuisance parameters the power simulation had to guess

- **GPT-5.5** between-family SD of attempt rate: **0.135** (simulation assumed 0.12), 13 families
- **Claude Opus 5** between-family SD of attempt rate: **0.167** (simulation assumed 0.12), 12 families
- baseline P(ATTEMPT) on LOW x DIFFERENT: **0.299** (simulation assumed 0.40)

## Realized coordination (scored against held-out Stage A, no extra API cost)

| focal | level | partner | P(match) on ATTEMPT trials | realized EV | SAFE EV |
|---|---|---|---|---|---|
| GPT-5.5 | HIGH | SAME | 0.901 | 7.67 | 1.25 |
| GPT-5.5 | HIGH | DIFF | 0.468 | 2.17 | 4.05 |
| GPT-5.5 | LOW | SAME | 0.374 | 2.74 | 2.16 |
| GPT-5.5 | LOW | DIFF | 0.328 | 1.06 | 4.83 |
| Claude Opus 5 | HIGH | SAME | 0.994 | 6.13 | 3.11 |
| Claude Opus 5 | HIGH | DIFF | 0.303 | 1.53 | 3.82 |
| Claude Opus 5 | LOW | SAME | 0.356 | 1.44 | 4.34 |
| Claude Opus 5 | LOW | DIFF | 0.377 | 1.02 | 5.01 |

## Verdict

- decision-scale beta3: GPT **-0.022**, Claude **-0.025**
- prediction-scale anchor was +0.033 / +0.043

**The gradient does NOT amplify.** beta3 is at or below the prediction-scale anchor, where >40 families/side are needed for 80% power - infeasible. The honest output is a bounded null: the data rule out an interaction larger than roughly the CI upper limit above. Do not spend on the confirmatory.
