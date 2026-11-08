# SYNTHETIC VALIDATION — does the analysis separate determinism from similarity?

Produced by `synthetic_validation.py` (`--reps 150 --boot-b 300 --null-reps 25
--null-b 300`), raw numbers in `out/synthetic_validation.json`, console transcript in
`out/synthetic_validation.log`. **No API calls.** Seeded (`seed = 20260909`, deterministic
per-case offsets), so the numbers below reproduce exactly.

This is the deliverable that answers MASTER_DESIGN S5: any similarity increase must be
decomposable into (a) models becoming individually more deterministic and (b) models
becoming more similar to one another, and reporting (a) as convergence is the primary
inferential error the study must avoid.

---

## 1. The generator and its ground truth

A policy is `p = temper(q, beta)` where `q` is the model's **convention** — a point on the
simplex standardised to effective support `S* = 2.0` — and `beta` its **determinism**.
Ground truth is therefore two independent coordinates, and the true adjusted similarity is
`das_true = S* * <q_A, q_B>`, known exactly by construction and independent of `beta`.

Design: `K = 4` options, 24 items, **n = 48 per cell** (the MASTER_DESIGN S5 frozen
floor), 5 vintage levels, 150 replicate studies per case.

All four cases put both models' modal mass on the **same** canonical option and let them
differ only in the tail. That is the exact configuration MASTER_DESIGN S5 warns about —
"if both models sharpen toward the same option, expected match rises with no change in
mutual similarity" — and it is what the existing 4-option data actually looks like
(worked run: 52 of 122 cells at `modal_share >= 0.99`).

| case | determinism (`beta`) | convention (`q_B`) | TRUE `das` slope |
|---|---|---|---|
| **A** pure determinism | 1.0 -> 6.0 | **fixed** | **+0.0000** |
| **B** pure similarity | fixed at 1.0 | moves toward `q_A`, restandardised so support stays 2.0 | **+0.0238** |
| **C** both | 1.0 -> 6.0 | moves toward `q_A` | **+0.0224** |
| **D** adversarial | 1.0 -> 6.0 | moves AWAY from `q_A` (toward its reversal) | **-0.2176** |

Case D is included because it is the case a merely *rescaled* statistic cannot pass: true
similarity falls while determinism rises, so a statistic that has not really removed
determinism will understate the divergence or miss it.

---

## 2. Case A — pure determinism increase, similarity exactly constant

True `das` is 0.9318 at **every** vintage. Only `beta` moves.

| vintage | 0 | 1 | 2 | 3 | 4 | slope |
|---|---|---|---|---|---|---|
| true effective support | 2.000 | 1.504 | 1.215 | 1.077 | 1.025 | |
| **true `das`** | 0.9318 | 0.9318 | 0.9318 | 0.9318 | 0.9318 | **+0.0000** |
| `cross_model_match` (raw) | 0.466 | 0.637 | 0.802 | 0.912 | 0.966 | **+0.1274** |
| TRUE `distribution_distance` (JS) | 0.304 | 0.286 | 0.239 | 0.168 | 0.098 | |
| estimated `distribution_distance` | 0.265 | 0.247 | 0.199 | 0.133 | 0.062 | -0.0519 |
| `cos_raw` | 0.918 | 0.950 | 0.974 | 0.989 | 0.996 | +0.0195 |
| `rank_similarity` | 0.772 | 0.783 | 0.809 | 0.877 | 0.942 | +0.0434 |
| `das` (point estimate) | 0.925 | 0.944 | 0.966 | 0.985 | 0.994 | +0.0179 |

**What a naive analysis concludes.** Using an item-clustered bootstrap CI on the raw
metric, **100% of the 150 simulated studies declare "similarity rises with vintage"** —
the exact error MASTER_DESIGN S5 forbids. Raw expected match more than doubles (0.47 ->
0.97) while mutual similarity does not move at all. The JS distance halves, `cos_raw`
falls by three quarters, `cos_raw` rises, and `rank_similarity` rises: **every unadjusted
statistic fails this case**, and `cos_raw` fails it too, which is why the exact
decomposition of S4.2 is a diagnostic and not the adjustment.

Note what the two `distribution_distance` rows show. The estimate tracks the TRUE JS
distance closely (Miller-Madow is doing its job), and the true distance itself falls from
0.304 to 0.098. **This is not estimator bias.** Two policies that both sharpen onto the
same option really do become closer *as distributions*, while the conventions behind them
have not moved at all. `distribution_distance` is therefore an accurate measurement of a
quantity that is not the one Stage 1 is asking about, and it must never be read as
convergence on its own. The same is true of `modal_agreement`, which rises from 0.973 to
1.000 here.

**The exact decomposition attributes it correctly.**
`log M_AB = .5 log M_AA + .5 log M_BB + log cos_raw`, slopes per vintage step:

| channel | slope | share of total |
|---|---|---|
| determinism (`.5 log M_AA + .5 log M_BB`) | **+0.1563** | **88%** |
| alignment (`log cos_raw`) | +0.0211 | 12% |
| total (`log M_AB`) | +0.1774 | 100% |
| residual | 0 (exact) | |

**The `das` point estimate is close but not clean**, and the residual +0.0179 is the
identifiability artefact of ANALYSIS_SPEC S4.5, measured directly here:

| true effective support | 2.000 | 1.504 | 1.215 | 1.077 | 1.025 |
|---|---|---|---|---|---|
| true `das` | 0.9318 | 0.9318 | 0.9318 | 0.9318 | 0.9318 |
| estimated `das` | 0.9237 | 0.9439 | 0.9654 | 0.9851 | 0.9939 |
| bias | -0.008 | +0.012 | +0.034 | +0.053 | **+0.062** |

The estimator is essentially unbiased while a cell keeps two live options and degrades
smoothly as the cell collapses, because at support 1.03 an n=48 sample is `(48,0,0,0)`
almost every time and carries no information about the ORDER of the tail. Parametric
bootstrap bias correction was implemented and tested against this table and does not fix
it — it moves the estimate the wrong way — because the information is absent, not noisy.

**The determinism-matched null band gives the right answer.**

| quantity | value |
|---|---|
| observed `das` slope | +0.0180 |
| determinism-matched null band | [+0.0014, +0.0257] |
| **`excess_slope` (observed - null mean)** | **+0.0043**  (truth: +0.0000) |
| **rejection rate over 25 simulated studies** | **0.00** |

The null band reproduces the artefact (its centre is +0.0137, not 0), so the artefact
cancels and the test correctly reports **no similarity change**, in every replicate.

---

## 3. Case B — pure similarity increase, determinism exactly constant

Effective support is 2.000 at every vintage; only `q_B` moves toward `q_A`.

| vintage | 0 | 1 | 2 | 3 | 4 | slope |
|---|---|---|---|---|---|---|
| **true `das`** | 0.9030 | 0.9407 | 0.9687 | 0.9881 | 0.9984 | **+0.0238** |
| `cross_model_match` (raw) | 0.452 | 0.469 | 0.483 | 0.495 | 0.497 | +0.0117 |
| `das` (point estimate) | 0.897 | 0.933 | 0.960 | 0.979 | 0.989 | **+0.0229** |

- `das` recovers the truth: slope +0.0229 against a true +0.0238, **bias -0.0009**.
- Decomposition: determinism channel **-0.0006 (-2% of total)**, alignment channel
  +0.0257. The identity attributes all of it to alignment, correctly.
- Null-band test: `excess_slope` **+0.0232** (truth +0.0238), **rejection rate 1.00**.
- The raw metric is not merely confounded, it is **insensitive**: its slope is +0.0117,
  about half the true change, and **11% of simulated studies using it would have called
  the effect flat**. A study relying on `cross_model_match` would under-detect real
  convergence at the same time as over-detecting fake convergence in Case A.

---

## 4. Case C — both rising together

| vintage | 0 | 1 | 2 | 3 | 4 | slope |
|---|---|---|---|---|---|---|
| true effective support | 2.000 | 1.533 | 1.269 | 1.138 | 1.082 | |
| **true `das`** | 0.9091 | 0.9438 | 0.9704 | 0.9889 | 0.9985 | **+0.0224** |
| `cross_model_match` (raw) | 0.456 | 0.648 | 0.833 | 0.926 | 0.956 | +0.1280 |
| `das` (point estimate) | 0.904 | 0.950 | 0.981 | 0.993 | 0.998 | **+0.0230** |

- `das` recovers the truth: +0.0230 against +0.0224, **bias +0.0006**.
- The raw metric moves **5.7x** as fast as the true similarity change; the decomposition
  assigns **85%** of the raw log-trend to determinism (+0.1529) and 15% to alignment
  (+0.0264). Reporting the raw slope here would inflate a genuine but modest convergence
  by nearly six-fold.
- Null-band test: `excess_slope` **+0.0208** (truth +0.0224) — the right answer — but
  **rejection rate only 0.32**. This is the honest limitation: when determinism rises far
  enough, few pairs remain at reference support (19 reference rows here, against 79 in
  Case B), the null band widens to [-0.0196, +0.0233], and power collapses even though the
  point estimate is unbiased. **Detecting real convergence requires items that stay
  behaviourally live**; this is a design requirement, not a tuning parameter.

---

## 5. Case D — adversarial: determinism up, similarity DOWN

| vintage | 0 | 1 | 2 | 3 | 4 | slope |
|---|---|---|---|---|---|---|
| **true `das`** | 0.9215 | 0.8880 | 0.7185 | 0.2525 | 0.1512 | **-0.2176** |
| `cross_model_match` (raw) | 0.461 | 0.602 | 0.541 | 0.004 | 0.000 | -0.1520 |
| `das` (point estimate) | 0.916 | 0.907 | 0.760 | 0.300 | 0.304 | **-0.1831** |

- The raw metric first **rises** (0.461 -> 0.602 between vintages 0 and 1) while true
  similarity is already falling: determinism briefly overwhelms a real divergence. Over
  the full range its slope (-0.1520) understates the true divergence by 30%.
- `das` reports the right sign and roughly the right magnitude throughout.
- Null-band test: `excess_slope` **-0.1936** (truth -0.2176), **rejection rate 1.00**.
- Residual attenuation at the sharpest vintage is visible and expected: at support 1.09
  the estimate is 0.304 against a truth of 0.151 (bias +0.152), the same identifiability
  ceiling as Case A, pulling toward 1.

---

## 6. Summary — does the statistic report the right answer?

| | TRUTH | raw `cross_model_match` slope | `das` slope | **`excess_slope` (primary)** | reject H0 | verdict |
|---|---|---|---|---|---|---|
| **A** determinism only | 0.0000 | **+0.1274** (wrong) | +0.0179 | **+0.0043** | **0.00** | **correct: no similarity change** |
| **B** similarity only | +0.0238 | +0.0117 (half) | +0.0229 | **+0.0232** | **1.00** | **correct: similarity rises** |
| **C** both | +0.0224 | **+0.1280** (5.7x) | +0.0230 | **+0.0208** | 0.32 | **correct estimate, low power** |
| **D** adversarial | -0.2176 | -0.1520 (understates) | -0.1831 | **-0.1936** | **1.00** | **correct: similarity falls** |

`excess_slope` recovers the ground-truth similarity trend in all four cases, and the
determinism-matched test gives size 0.00 where the truth is "no change" and power 1.00
where the truth is a change of realistic size at constant or moderately rising
determinism. The one weak cell — Case C's power of 0.32 — is a genuine information limit,
not a defect of the statistic, and is reported as such.

## 7. What this validation establishes, and what it does not

**Establishes**

1. Every unadjusted statistic — `cross_model_match`, JS distance, `cos_raw`,
   `rank_similarity`, `modal_agreement` — declares convergence in Case A, where by
   construction there is none. The confound is not hypothetical; at n=48 with K=4 it is
   overwhelming (raw match 0.47 -> 0.97). For the distance and the modal-agreement rate
   this is not even a small-sample artefact: the population quantities themselves move
   with determinism, so no amount of data would fix them.
2. The exact decomposition `log M_AB = .5 log M_AA + .5 log M_BB + log cos_raw` attributes
   88% of the Case A trend and 85% of the Case C trend to determinism, and 0% of Case B.
   It is a correct, residual-free accounting of where a raw trend came from.
3. `das` is exactly tempering-invariant in the population (asserted to 1e-11 in
   `run_stage1.py --selftest`) and its finite-sample bias at n=48 is below 0.01 while a
   cell keeps two live options.
4. Tested against the determinism-matched null band rather than against zero, the
   procedure returns the correct verdict in all four ground-truth cases.

**Does not establish**

1. That the tempering model is the right description of how a real checkpoint's policy
   changes between generations. It is a modelling assumption; `rank_similarity` is
   reported alongside as a monotone-invariant floor that does not need it.
2. That the procedure has usable power on the actual Stage 1 panel. Power depends on how
   many pairs retain effective support near the reference level. On the existing 4-option
   visual battery the worked run finds `identifiable = False` — median effective support
   1.18, and a median of exactly 1.000 for both `claude-opus-4-7` and `claude-opus-5`.
   **On a battery like that, the central Stage 1 question cannot be answered by any
   adjustment.** Item selection for behavioural liveness is a precondition, not a
   refinement.
