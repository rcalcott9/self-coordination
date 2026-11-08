# Power for beta3 - family as the unit of independence

`1500` simulations per cell, permutation test with `600` re-labellings, alpha = 0.05.

Parameters anchored in this project's own data:

- baseline P(ENTER) on LOW x DIFFERENT, mid payoff: 0.4
- main effect of strong own convention: 0.25
- main effect of same-model partner: 0.1 (manipulation check flat discount ~0.11)
- safe-payoff effect: 0.055/point (Study 1 betting logistic)
- between-family sd of attempt rate: 0.12

**Empirically anchored beta3 = +0.033 (GPT) / +0.043 (Claude)**, from the manipulation check's own-convention gradient. The prior Study 2's GPT arm excluded partner effects above +0.118, bounding the range from above.

## 20 trials per focal x stimulus x partner x payoff cell

| pairs/model | b3=0.000 | b3=0.033 | b3=0.043 | b3=0.060 | b3=0.100 | b3=0.150 | b3=0.200 |
|---|---|---|---|---|---|---|---|
| **4** (2,560 calls) | 0.03 | 0.04 | 0.07 | 0.09 | 0.21 | 0.37 | 0.53 |
| **6** (3,840 calls) | 0.04 | 0.08 | 0.10 | 0.18 | 0.39 | 0.67 | 0.85 |
| **7** (4,480 calls) | 0.05 | 0.10 | 0.12 | 0.21 | 0.48 | 0.77 | 0.92 |
| **8** (5,120 calls) | 0.05 | 0.10 | 0.15 | 0.25 | 0.54 | 0.85 | 0.95 |
| **10** (6,400 calls) | 0.05 | 0.11 | 0.16 | 0.30 | 0.65 | 0.92 | 0.99 |
| **12** (7,680 calls) | 0.04 | 0.14 | 0.19 | 0.36 | 0.75 | 0.96 | 0.99 |
| **15** (9,600 calls) | 0.05 | 0.13 | 0.27 | 0.46 | 0.85 | 0.99 | 1.00 |
| **20** (12,800 calls) | 0.05 | 0.19 | 0.32 | 0.55 | 0.94 | 1.00 | 1.00 |
| **30** (19,200 calls) | 0.06 | 0.26 | 0.45 | 0.73 | 0.99 | 1.00 | 1.00 |
| **40** (25,600 calls) | 0.06 | 0.36 | 0.55 | 0.86 | 1.00 | 1.00 | 1.00 |

First column (b3=0) is the empirical SIZE of the test; it should sit near 0.05.

## 30 trials per focal x stimulus x partner x payoff cell

| pairs/model | b3=0.000 | b3=0.033 | b3=0.043 | b3=0.060 | b3=0.100 | b3=0.150 | b3=0.200 |
|---|---|---|---|---|---|---|---|
| **4** (3,840 calls) | 0.03 | 0.06 | 0.08 | 0.12 | 0.27 | 0.51 | 0.65 |
| **6** (5,760 calls) | 0.05 | 0.09 | 0.12 | 0.24 | 0.56 | 0.83 | 0.94 |
| **7** (6,720 calls) | 0.05 | 0.12 | 0.18 | 0.29 | 0.66 | 0.91 | 0.97 |
| **8** (7,680 calls) | 0.06 | 0.14 | 0.16 | 0.35 | 0.72 | 0.94 | 0.99 |
| **10** (9,600 calls) | 0.05 | 0.15 | 0.25 | 0.39 | 0.82 | 0.98 | 1.00 |
| **12** (11,520 calls) | 0.05 | 0.18 | 0.29 | 0.49 | 0.89 | 0.99 | 1.00 |
| **15** (14,400 calls) | 0.04 | 0.21 | 0.34 | 0.58 | 0.94 | 1.00 | 1.00 |
| **20** (19,200 calls) | 0.06 | 0.25 | 0.45 | 0.74 | 0.99 | 1.00 | 1.00 |
| **30** (28,800 calls) | 0.06 | 0.40 | 0.61 | 0.89 | 1.00 | 1.00 | 1.00 |
| **40** (38,400 calls) | 0.05 | 0.48 | 0.70 | 0.95 | 1.00 | 1.00 | 1.00 |

First column (b3=0) is the empirical SIZE of the test; it should sit near 0.05.

## Families needed for 80% / 90% power

| b3 | reps | families/side for 80% | for 90% |
|---|---|---|---|
| 0.033 | 20 | >40 | >40 |
| 0.033 | 30 | >40 | >40 |
| 0.043 | 20 | >40 | >40 |
| 0.043 | 30 | >40 | >40 |
| 0.060 | 20 | 40 | >40 |
| 0.060 | 30 | 30 | 40 |
| 0.100 | 20 | 15 | 20 |
| 0.100 | 30 | 10 | 15 |
| 0.150 | 20 | 8 | 10 |
| 0.150 | 30 | 6 | 7 |
| 0.200 | 20 | 6 | 7 |
| 0.200 | 30 | 6 | 6 |

## At the battery we actually have

Discovery yielded **8** distinct-family pairs for GPT and **7** for Claude.

| focal | pairs | anchored b3 | power @20 reps | power @30 reps |
|---|---|---|---|---|
| GPT-5.5 | 8 | 0.033 | 0.10 | 0.14 |
| Claude Opus 5 | 7 | 0.043 | 0.12 | 0.18 |

| focal | pairs | power @ b3=0.10 | @ b3=0.15 | @ b3=0.20 |
|---|---|---|---|---|
| GPT-5.5 | 8 | 0.72 | 0.94 | 0.99 |
| Claude Opus 5 | 7 | 0.66 | 0.91 | 0.97 |

