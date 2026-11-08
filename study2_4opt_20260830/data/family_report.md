# 4-option battery - family-level report

`203` stimuli across `41` families, discovery n=24/model/stimulus.

Criteria: HIGH self-match >= 0.75 and own-cross >= 0.15; LOW self-match <= 0.45 and non-positional; pair gap >= 0.3; family is the unit of independence.

## GPT-5.5 as focal model

- qualifying HIGH stimuli (>= 0.75, model-specific): **16** across **8** families
- qualifying LOW stimuli (<= 0.45, non-positional) : **22** across **11** families
- families supplying BOTH a high and a low          : **4**

- **high/low pairs with DISTINCT families on both sides: 8**
- distinct families represented across those pairs: 13

| # | HIGH stimulus | self | own-cross | LOW stimulus | self | pos.bias | gap |
|---|---|---|---|---|---|---|---|
| 1 | `F10_curvature_m5` | 1.000 | **+0.875** | `F12_mirror_m3` | 0.254 | 0.292 | 0.746 |
| 2 | `F12_mirror_m7` | 0.917 | **+0.832** | `F27_linecount_m1` | 0.293 | 0.250 | 0.623 |
| 3 | `F06_density_m0` | 0.772 | **+0.522** | `F41_contain_m2` | 0.293 | 0.167 | 0.478 |
| 4 | `F09_convexity_m5` | 1.000 | **+0.333** | `F11_noise_m0` | 0.297 | 0.250 | 0.703 |
| 5 | `F31_overlap_m1` | 0.772 | **+0.329** | `F35_gradang_m1` | 0.315 | 0.250 | 0.457 |
| 6 | `F01_oddone_m6` | 1.000 | **+0.208** | `F36_split_m1` | 0.373 | 0.167 | 0.627 |
| 7 | `F07_contrast_m7` | 1.000 | **+0.208** | `F31_overlap_m0` | 0.380 | 0.167 | 0.620 |
| 8 | `F41_contain_m1` | 1.000 | **+0.208** | `F33_hole_m0` | 0.380 | 0.208 | 0.620 |

## Claude Opus 5 as focal model

- qualifying HIGH stimuli (>= 0.75, model-specific): **43** across **22** families
- qualifying LOW stimuli (<= 0.45, non-positional) : **20** across **7** families
- families supplying BOTH a high and a low          : **2**

- **high/low pairs with DISTINCT families on both sides: 7**
- distinct families represented across those pairs: 12

| # | HIGH stimulus | self | own-cross | LOW stimulus | self | pos.bias | gap |
|---|---|---|---|---|---|---|---|
| 1 | `F10_curvature_m2` | 1.000 | **+0.750** | `F11_noise_m1` | 0.232 | 0.125 | 0.768 |
| 2 | `F20_corner_m0` | 1.000 | **+0.750** | `F12_mirror_m4` | 0.243 | 0.208 | 0.757 |
| 3 | `F12_mirror_m3` | 0.917 | **+0.712** | `F35_gradang_m2` | 0.265 | 0.208 | 0.652 |
| 4 | `F11_noise_m0` | 1.000 | **+0.708** | `F05_orient_m1` | 0.283 | 0.292 | 0.717 |
| 5 | `F27_linecount_m1` | 1.000 | **+0.708** | `F41_contain_m2` | 0.373 | 0.125 | 0.627 |
| 6 | `F28_dotarrange_m0` | 1.000 | **+0.625** | `F31_overlap_m1` | 0.438 | 0.208 | 0.562 |
| 7 | `F03_symmetry_m6` | 1.000 | **+0.542** | `F37_mirroraxis_m0` | 0.438 | 0.292 | 0.562 |

## Family-level yield

| family | GPT high | GPT low | Claude high | Claude low |
|---|---|---|---|---|
| `F01_oddone` | 2 | 0 | 0 | 0 |
| `F02_size` | 0 | 0 | 1 | 0 |
| `F03_symmetry` | 0 | 0 | 1 | 0 |
| `F05_orient` | 0 | 2 | 0 | 5 |
| `F06_density` | 1 | 0 | 2 | 0 |
| `F07_contrast` | 1 | 0 | 0 | 0 |
| `F09_convexity` | 6 | 0 | 0 | 0 |
| `F10_curvature` | 2 | 1 | 6 | 0 |
| `F11_noise` | 0 | 4 | 2 | 3 |
| `F12_mirror` | 2 | 3 | 1 | 6 |
| `F13_count` | 0 | 0 | 2 | 0 |
| `F15_ring` | 0 | 0 | 2 | 0 |
| `F16_aspect` | 0 | 4 | 5 | 0 |
| `F18_stroke` | 0 | 0 | 2 | 0 |
| `F20_corner` | 0 | 0 | 2 | 0 |
| `F21_notch` | 0 | 0 | 1 | 0 |
| `F22_star` | 0 | 0 | 1 | 0 |
| `F25_nested` | 0 | 0 | 2 | 0 |
| `F26_bumploc` | 0 | 0 | 1 | 0 |
| `F27_linecount` | 0 | 1 | 2 | 0 |
| `F28_dotarrange` | 0 | 0 | 3 | 0 |
| `F31_overlap` | 1 | 1 | 0 | 2 |
| `F33_hole` | 0 | 1 | 3 | 0 |
| `F34_jitter` | 0 | 0 | 1 | 0 |
| `F35_gradang` | 0 | 3 | 0 | 2 |
| `F36_split` | 0 | 1 | 1 | 0 |
| `F37_mirroraxis` | 0 | 0 | 0 | 1 |
| `F39_spacing` | 0 | 0 | 1 | 0 |
| `F40_crossang` | 0 | 0 | 1 | 0 |
| `F41_contain` | 1 | 1 | 0 | 1 |

