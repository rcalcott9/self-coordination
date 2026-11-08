# Partner-identity manipulation check

`384` parsed trials, 8 stimuli x 2 focal x 2 partner x 12 reps. Fresh one-shot calls, Study 2 inference settings.

Wording is the most explicit available ("running the same underlying policy" vs "a different underlying policy"), so this is a CEILING test.

## Q1. Does predicted P(match) move with partner identity?

| focal | stimulus | kind | true own | true cross | pred SAME | pred DIFF | gap | 95% CI |
|---|---|---|---|---|---|---|---|---|
| gpt | `F01_oddone_m0` | shared_control | - | 1.000 | 0.908 | 0.817 | **+0.092** | [+0.046, +0.142] |
| gpt | `F02_size_m2` | shared_control | - | 1.000 | 0.825 | 0.657 | **+0.168** | [+0.118, +0.217] |
| gpt | `F06_density_m0` | anti_coordinated | - | 0.250 | 0.747 | 0.472 | **+0.275** | [+0.212, +0.342] |
| gpt | `F10_curvature_m3` | anti_coordinated | - | 0.156 | 0.758 | 0.508 | **+0.250** | [+0.192, +0.304] |
| gpt | `F10_curvature_m5` | anti_coordinated | - | 0.125 | 0.737 | 0.557 | **+0.181** | [+0.118, +0.243] |
| gpt | `F11_noise_m0` | one_sided_claude | - | 0.292 | 0.502 | 0.391 | **+0.111** | [+0.045, +0.174] |
| gpt | `F12_mirror_m6` | one_sided_gpt | - | 0.458 | 0.621 | 0.458 | **+0.163** | [+0.105, +0.218] |
| gpt | `F12_mirror_m7` | one_sided_gpt | - | 0.085 | 0.642 | 0.410 | **+0.232** | [+0.176, +0.285] |
| claude | `F01_oddone_m0` | shared_control | - | 1.000 | 0.803 | 0.714 | **+0.089** | [+0.027, +0.152] |
| claude | `F02_size_m2` | shared_control | - | 1.000 | 0.779 | 0.684 | **+0.095** | [+0.064, +0.128] |
| claude | `F06_density_m0` | anti_coordinated | - | 0.250 | 0.739 | 0.599 | **+0.140** | [+0.096, +0.186] |
| claude | `F10_curvature_m3` | anti_coordinated | - | 0.156 | 0.736 | 0.641 | **+0.095** | [+0.044, +0.138] |
| claude | `F10_curvature_m5` | anti_coordinated | - | 0.125 | 0.754 | 0.662 | **+0.092** | [+0.040, +0.137] |
| claude | `F11_noise_m0` | one_sided_claude | - | 0.292 | 0.413 | 0.333 | **+0.079** | [+0.021, +0.133] |
| claude | `F12_mirror_m6` | one_sided_gpt | - | 0.458 | 0.443 | 0.392 | **+0.052** | [+0.037, +0.066] |
| claude | `F12_mirror_m7` | one_sided_gpt | - | 0.085 | 0.442 | 0.408 | **+0.033** | [+0.013, +0.050] |

- **GPT-5.5** pooled: SAME 0.718 vs DIFF 0.534, gap **+0.184** [+0.141, +0.223]
- **Claude Opus 5** pooled: SAME 0.639 vs DIFF 0.554, gap **+0.084** [+0.037, +0.129]

## Q2. Is the movement calibrated, or a flat discount?

If the gap is real policy knowledge it should be LARGE where true cross-match is low and ~ZERO on the shared controls, where two different models genuinely do agree (true cross = 1.000).

| stimulus kind | true cross | mean gap | n cells |
|---|---|---|---|
| anti_coordinated | 0.13-0.25 | **+0.172** | 6 |
| one_sided_gpt | 0.09-0.46 | **+0.120** | 4 |
| one_sided_claude | 0.29 | **+0.095** | 2 |
| shared_control | 1.000 | **+0.111** | 4 |

- gap on stimuli where identity SHOULD matter : **+0.142**
- gap on shared controls (should be ~0)       : **+0.111**
- calibration contrast                        : **+0.031**

## Q3. Does it predict the OTHER model's actual choice?

Strongest form: under a different-model partner, does the predicted partner pick shift toward that model's true modal item (from discovery)?

| focal | stimulus | own modal | other modal | pred=OTHER's modal (SAME) | (DIFF) | shift |
|---|---|---|---|---|---|---|
| gpt | `F06_density_m0` | 3 | 0 | 0.167 | 0.583 | **+0.417** |
| gpt | `F10_curvature_m3` | 3 | 0 | 0.083 | 0.000 | **-0.083** |
| gpt | `F10_curvature_m5` | 3 | 0 | 0.000 | 0.000 | **+0.000** |
| gpt | `F11_noise_m0` | 2 | 1 | 0.417 | 0.167 | **-0.250** |
| gpt | `F12_mirror_m7` | 3 | 2 | 0.000 | 0.000 | **+0.000** |
| claude | `F06_density_m0` | 0 | 3 | 0.000 | 0.250 | **+0.250** |
| claude | `F10_curvature_m3` | 0 | 3 | 0.167 | 0.083 | **-0.083** |
| claude | `F10_curvature_m5` | 0 | 3 | 0.167 | 0.250 | **+0.083** |
| claude | `F11_noise_m0` | 1 | 2 | 0.000 | 0.000 | **+0.000** |
| claude | `F12_mirror_m7` | 2 | 3 | 0.083 | 0.083 | **+0.000** |

- mean shift toward the other model's true modal item: **+0.033** over 10 discriminating cells

## Q4. Does the model change its OWN pick when the partner differs?

- fidelity to own modal item, SAME minus DIFF: **+0.036** (positive = abandons its own convention when facing the other model)

## Q5. The actual precondition for beta3

beta3 = convention_strength x partner_same. It does not require a model of the OTHER policy - it requires the SAME-minus-DIFF gap to grow with the focal model's OWN convention strength.

- **corr(gap, own convention strength) = +0.383**  <- beta3's precondition
- corr(gap, true cross-match) = -0.236  (negative = calibrated)

| focal | corr(gap, own) | corr(gap, cross) | n |
|---|---|---|---|
| GPT-5.5 | +0.190 | -0.600 | 8 |
| Claude Opus 5 | +0.580 | +0.132 | 8 |

- permutation p (within-focal shuffle, B=20000): **0.1247** at n=16 cells

The two models get there differently: GPT's discount tracks TRUE CROSS-MATCH (it discounts more where the two policies really do diverge), while Claude's tracks its OWN convention strength. Both n=8, so this split is suggestive only.

## Verdict

- partner identity moves predicted P(match): **YES** (pooled gap +0.134)
- movement is calibrated, not a flat discount: **NO** (contrast +0.031)
- predicts the other model's actual choice: **NO** (shift +0.033)

- gap grows with own convention strength (beta3 precondition): **YES** (r = +0.383, p = 0.125, n = 16)

**GATE PASSES, WITH A CAVEAT.** Partner identity registers robustly - every cell positive, both models, all CIs excluding zero. That is a real improvement on the previous Study 2, where the partner label never reached the rationale at all. beta3's precondition is present with the right sign but is not significant at this n.

The caveat: a large part of the effect is a FLAT DISCOUNT. On shared controls, where two different models genuinely agree 100% of the time, the models still discount by +0.111. Neither can predict the other model's actual choice (shift +0.033). So Stage C should be expected to show a partner MAIN effect for sure; the interaction is plausible but modest, which is exactly the case for maximising independent stimulus families rather than trials per cell.
