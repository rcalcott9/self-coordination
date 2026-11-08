# Opus 4.7 robustness extension

Prospective test of whether the original -0.103 Stage C estimate was driven by the
`rot > b_spiral_cw` reversal, or reflects a general property of Opus 4.7.

The original 3-pair result, its raw data and the `rot` reversal are preserved unchanged.
The new sample shares **no stimulus** with it (the six original stimuli were excluded
from the candidate pool; verified by assertion).

Selector thresholds, held-out validation, ranking and the non-reuse rule are unchanged.
Two parameters were set explicitly: `PSC_EXCLUDE_STIMULI` (a restriction) and
`PSC_TARGET_PAIRS=8` (allocation for a single-model sample; the default 3+2 was built
for a two-model study). The candidate battery is the same frozen 30-stimulus,
10-cue-family expansion used for GPT-5 and Opus 4.5, generated before this question
arose; nothing `rot`-like was added.

Payoff-saturation screen on the actual new stimuli: ATTEMPT at SAFE=9 = **0.531**
(limit 0.95) -> ample outcome variance, so a null would have been interpretable.

## 1. New prospective sample (PRIMARY)

8 pairs, 1920 trials.
**Mean gap +0.0625**, positive in
5/8 pairs,
permutation p = 0.00005.
Payoff-specific gaps: {'3': 0.0083, '5': 0.025, '7': 0.1333, '9': 0.0833}

| pair | gap |
|---|---|
| `x6_oi_b > x4_db_sub` | +0.250 |
| `s_contrast > x8_contr_c` | +0.475 |
| `x4_db_b > x5_cs_a` | +0.042 |
| `x3_tex_sd > x10_cen_b` | +0.017 |
| `d_texture > x2_lg_ct` | +0.008 |
| `x5_cs_sub > c_open_cplx` | -0.125 |
| `x10_cen_a > b_tee_ell` | +0.000 |
| `x8_contr_a > c_contr_subtle` | -0.167 |

## 2. Comparison with the original sample

| sample | pairs | mean gap | positive | permutation p |
|---|---|---|---|---|
| original | 3 | -0.1028 | 1/3 | 1.00000 |
| **new (primary)** | 8 | **+0.0625** | 5/8 | 0.00005 |

The two samples disagree in sign. Both are reported; neither is averaged away.

## 3. Combined descriptive

| set | pairs | mean gap | positive | permutation p |
|---|---|---|---|---|
| all pairs | 11 | +0.0174 | 6/11 | 0.04615 |
| excluding `rot > b_spiral_cw` (sensitivity) | 10 | +0.0467 | 6/10 | 0.00005 |

The exclusion line quantifies `rot`'s contribution. It is **not** a justification for
dropping it, and the combined all-pairs row remains the descriptive estimate.

## 4. `rot` diagnostic (explanatory, secondary)

| metric | `rot` | `b_spiral_cw` |
|---|---|---|
| stage a self match | 1.0 | 0.4938 |
| form consistency | 1.0 | 0.0667 |
| p left stage a | 0.5 | 0.967 |
| held out self match | 1.0 | 0.4851 |
| generic salience | 0.1953 | 0.231 |
| auditor prediction | 0.6677 | 0.672 |
| stage c attempt | 0.408 | 0.683 |
| nofeature rate stage c | 0.508 | 0.108 |
| nofeature rate stage a | 0.0 | 0.0 |

`rot` has a perfect, position-independent convention (60/60 same form, P(LEFT)=0.50)
that survives held-out validation at 1.000. `b_spiral_cw` is position fallback
(P(LEFT)=0.967, form consistency 0.067) and coordinates at chance. The model bets the
wrong way on both. Its Stage C rationales call `rot` featureless on 50.8% of trials -
while its Stage A rationales for the same image do so on 0%.

## 5. Implication for the Anthropic ladder

The preferred Opus 4.7 estimate is the prospective 8-pair sample. The original 3-pair
estimate is retained in text as the initial sample containing the `rot` anomaly.
