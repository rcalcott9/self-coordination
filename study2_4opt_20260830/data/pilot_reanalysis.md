# Stage C pilot - corrected analysis

`4,800` parsed trials. **Pre-specified pilot, not a confirmatory sample.** Estimates and intervals carry the argument; the sensitivity simulation only bounds what this design could have detected.

## 1. Trial-level regret

For every ATTEMPTED trial: `regret = S - 10 * P(match | stimulus, partner)`, with `S` that trial's own offered safe payoff and `P(match)` the partner model's held-out Stage A probability of the item the focal actually chose. Positive regret = the safe payoff was worth more than the attempt.

Uncertainty propagated by Dirichlet(counts + 1/2) posterior draws over the partner's Stage A distribution (n=24 per stimulus x model).

| focal | level | partner | n attempts | mean regret | 95% CI | total regret | % EV-negative | 95% CI |
|---|---|---|---|---|---|---|---|---|
| GPT-5.5 | HIGH | SAME | 545 | **-2.93** | [-3.21, -2.59] | -1598 | 13% | [8, 18] |
| GPT-5.5 | HIGH | DIFF | 297 | **-0.30** | [-0.81, +0.21] | -89 | 47% | [41, 55] |
| GPT-5.5 | LOW | SAME | 469 | **+1.60** | [+1.32, +1.89] | +752 | 73% | [66, 79] |
| GPT-5.5 | LOW | DIFF | 207 | **+0.39** | [+0.22, +0.57] | +82 | 62% | [57, 69] |
| Claude Opus 5 | HIGH | SAME | 345 | **-4.68** | [-4.99, -4.29] | -1616 | 0% | [0, 1] |
| Claude Opus 5 | HIGH | DIFF | 284 | **+1.31** | [+0.64, +1.97] | +373 | 76% | [58, 93] |
| Claude Opus 5 | LOW | SAME | 227 | **+0.61** | [+0.42, +0.83] | +139 | 63% | [55, 71] |
| Claude Opus 5 | LOW | DIFF | 152 | **-0.01** | [-0.31, +0.32] | -2 | 52% | [43, 59] |

- **total regret across all 2,526 attempts: -1960 points** [-2307, -1604]
- overall share of attempts that were EV-negative: 44%

## 2. Is HIGH-vs-LOW own-policy reliability, or visible coordinability?

**Stage B (auditor / generic-salience) was never run on this battery.** So HIGH and LOW are not matched on how coordinable the stimulus looks to an outside observer. Cross-model match is the only available proxy:

| focal | level | mean own-copy match | mean cross-model match |
|---|---|---|---|
| GPT-5.5 | HIGH | 0.933 | 0.493 |
| GPT-5.5 | LOW | 0.323 | 0.352 |
| Claude Opus 5 | HIGH | 0.988 | 0.303 |
| Claude Opus 5 | LOW | 0.325 | 0.331 |

Cross-model match differs between HIGH and LOW as well, so a generic 'this stimulus is easy to coordinate on' account is **not excluded**. The supported statement is that entry is higher on stimuli classified HIGH by own-copy match - not that the model is reading its own policy.

## 3. Per-pair interaction estimates and leave-one-family-out

Pooled zero could be consistent nulls or cancellation. Per-pair interaction = `gap(HIGH) - gap(LOW)`, gap = P(attempt|SAME) - P(attempt|DIFF).

### GPT-5.5

| pair | HIGH family | LOW family | gap HIGH | gap LOW | interaction | 95% CI |
|---|---|---|---|---|---|---|
| gpt_0 | `F10_curvature` | `F12_mirror` | +0.338 | +0.312 | **+0.025** | [-0.163, +0.213] |
| gpt_1 | `F12_mirror` | `F27_linecount` | +0.387 | +0.537 | **-0.150** | [-0.341, +0.041] |
| gpt_2 | `F06_density` | `F41_contain` | +0.300 | +0.412 | **-0.112** | [-0.296, +0.071] |
| gpt_3 | `F09_convexity` | `F11_noise` | +0.325 | +0.263 | **+0.063** | [-0.121, +0.246] |
| gpt_4 | `F31_overlap` | `F35_gradang` | +0.338 | +0.475 | **-0.138** | [-0.337, +0.062] |
| gpt_5 | `F01_oddone` | `F36_split` | +0.350 | +0.375 | **-0.025** | [-0.226, +0.176] |
| gpt_6 | `F07_contrast` | `F31_overlap` | +0.500 | +0.487 | **+0.013** | [-0.165, +0.190] |
| gpt_7 | `F41_contain` | `F33_hole` | +0.562 | +0.412 | **+0.150** | [-0.030, +0.330] |

- 4 of 8 pairs positive; mean -0.022, SD across pairs 0.106
- range -0.150 to +0.150
- leave-one-pair-out mean interaction: -0.046 to -0.004 (no single pair drives the pooled estimate)

### Claude Opus 5

| pair | HIGH family | LOW family | gap HIGH | gap LOW | interaction | 95% CI |
|---|---|---|---|---|---|---|
| claude_0 | `F10_curvature` | `F11_noise` | +0.075 | +0.013 | **+0.063** | [-0.071, +0.196] |
| claude_1 | `F20_corner` | `F12_mirror` | +0.138 | +0.188 | **-0.050** | [-0.244, +0.144] |
| claude_2 | `F12_mirror` | `F35_gradang` | +0.125 | +0.263 | **-0.138** | [-0.348, +0.073] |
| claude_3 | `F11_noise` | `F05_orient` | +0.137 | +0.213 | **-0.075** | [-0.277, +0.127] |
| claude_4 | `F27_linecount` | `F41_contain` | +0.062 | +0.088 | **-0.025** | [-0.243, +0.193] |
| claude_5 | `F28_dotarrange` | `F31_overlap` | +0.062 | +0.075 | **-0.013** | [-0.230, +0.205] |
| claude_6 | `F03_symmetry` | `F37_mirroraxis` | +0.162 | +0.100 | **+0.062** | [-0.147, +0.272] |

- 2 of 7 pairs positive; mean -0.025, SD across pairs 0.072
- range -0.138 to +0.063
- leave-one-pair-out mean interaction: -0.040 to -0.006 (no single pair drives the pooled estimate)

## 4. Binomial mixed-effects model

Specification, per focal model:

```
attempt ~ high * same + safe_c + (1 + same | family)
```

- **repeated calls**: 20 independent one-shot trials per stimulus x partner x payoff cell; no context carried across trials, so trials are conditionally independent given the cell.
- **stimulus**: within a focal model each stimulus is unique, and within the selected set each family contributes at most one stimulus per role, so stimulus and family coincide except where a family serves both roles.
- **pair**: the HIGH-LOW pairing is a greedy construction, not a physical unit, so no pair-level random effect is fitted; pairs enter only through the stimuli they contain.
- **family**: random intercept AND random slope on `same`, because the per-family gap is exactly the quantity the interaction contrasts. 3 GPT and 2 Claude families appear as both HIGH and LOW, so `high` is partly within-family.
- `safe_c` = safe payoff centred at 6.

| focal | term | estimate (logit) | SE | 95% CI |
|---|---|---|---|---|
| GPT-5.5 | `high` | +0.413 | 0.098 | [+0.221, +0.606] |
| GPT-5.5 | `same` | +4.366 | 0.101 | [+4.169, +4.564] |
| GPT-5.5 | `high:same` | +0.099 | 0.152 | [-0.199, +0.398] |
| Claude Opus 5 | `high` | +4.813 | 0.121 | [+4.576, +5.050] |
| Claude Opus 5 | `same` | +2.206 | 0.121 | [+1.969, +2.443] |
| Claude Opus 5 | `high:same` | -0.304 | 0.167 | [-0.632, +0.024] |

Variational-Bayes GLMM (statsmodels `BinomialBayesMixedGLM`); SDs are posterior, so intervals are credible intervals.

Cross-check - GLM with family-clustered robust SEs (few clusters, so anti-conservative; shown for comparison only):

| focal | term | estimate (logit) | cluster SE | z |
|---|---|---|---|---|
| GPT-5.5 | `high` | +1.256 | 0.462 | +2.72 |
| GPT-5.5 | `same` | +3.671 | 0.450 | +8.15 |
| GPT-5.5 | `high:same` | -0.044 | 0.467 | -0.09 |
| Claude Opus 5 | `high` | +2.286 | 0.789 | +2.90 |
| Claude Opus 5 | `same` | +1.308 | 0.524 | +2.50 |
| Claude Opus 5 | `high:same` | -0.263 | 0.380 | -0.69 |

Permutation on the risk-difference scale (family as the unit, HIGH/LOW label permuted across families) - the assumption-light benchmark:

| focal | beta3 (risk diff) | 95% CI (family bootstrap) | perm p |
|---|---|---|---|
| GPT-5.5 | **-0.022** | [-0.102, +0.067] | 0.6589 |
| Claude Opus 5 | **-0.025** | [-0.093, +0.041] | 0.5094 |

## 5. Is the GPT-Claude difference real?

GPT's SAME premium (+0.39) looks far larger than Claude's (+0.12), but a difference in significance is not a significant difference. Tested directly.

| term | estimate (logit) | cluster SE | z | p |
|---|---|---|---|---|
| `same` | +1.262 | 0.383 | +3.30 | 0.0010 |
| `same:is_gpt` | +2.549 | 0.423 | +6.03 | 0.0000 |
| `high:same` | -0.257 | 0.345 | -0.75 | 0.4562 |
| `high:same:is_gpt` | +0.200 | 0.568 | +0.35 | 0.7247 |

- SAME premium, stimulus-level: GPT **+0.398** (n=16), Claude **+0.121** (n=14)
- difference **+0.277**, permutation p = **0.0000** (labels permuted across stimuli)

Caveat: 7 families appear in both focal models' sets but the stimuli differ, so the two arms are not fully independent samples of the same battery.

## 6. Sensitivity, not post hoc power

The estimate and its interval are the result. The simulation below only answers: **what interaction would this design have detected?** It uses the OBSERVED family SDs, the OBSERVED cell means, the actual 8/7-family structure, and the same family-level permutation used for inference.

- observed between-family SD of attempt rate: GPT **0.135**, Claude **0.167** (the earlier simulation assumed 0.12)

| true beta3 | GPT (8 pairs) | Claude (7 pairs) |
|---|---|---|
| 0.00 | 0.04 | 0.06 |
| 0.05 | 0.12 | 0.22 |
| 0.10 | 0.35 | 0.66 |
| 0.15 | 0.51 | 0.91 |
| 0.20 | 0.56 | 0.98 |
| 0.25 | 0.61 | 0.99 |

**Headline bound, from the intervals rather than the simulation:** under this design the data exclude average interactions larger than approximately **+0.07 (GPT)** and **+0.04 (Claude)** on the risk-difference scale.

