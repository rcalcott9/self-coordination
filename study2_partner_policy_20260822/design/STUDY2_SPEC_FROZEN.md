# Study 2 — partner-policy sensitivity in a risky coordination bet

**FROZEN PRE-RUN SPEC.** Frozen 2026-08-22, before any confirmation-screen or Stage C call.

**Status: design frozen. Confirmation screen NOT started. Stage C NOT started.**

The single source of truth for every parameter below is
`design/FROZEN_PARAMS.py`. This document explains and fixes the *procedure*; it
restates numbers only for readability. Where the two disagree, `FROZEN_PARAMS.py`
wins and this document is in error. Every runnable artefact — the confirmation
runner, the Stage C runner, the analysis, the figures — imports from
`FROZEN_PARAMS` and re-declares nothing. `code/design_table.py` materialises the
frozen design as `design/frozen_design_table.csv` (128 cells) and asserts that
consistency; it must pass before any call is made.

---

## 1. Scientific target

Study 1 showed that a model bets more on stimuli its own copies coordinate on. It
always told the actor its partner was another instance of itself, so "the partner
is me" and "this stimulus coordinates well" were never separated. Study 2
separates them and asks a sharper question:

> Does willingness to enter a risky coordination game with a same-model partner
> scale with the **actual coordination advantage** that sharing a policy confers
> **on that particular stimulus**?

Two accounts are contrasted, and the whole design exists to tell them apart.

| | account | prediction for the same-minus-different attempt shift |
|---|---|---|
| **MODEL A** | coarse identity heuristic | a **constant** positive shift, the same on every stimulus |
| **MODEL B** | policy-specific sensitivity | a shift **proportional to the measured advantage**, and *negative* where the advantage is negative |

**The primary test is the dose-response slope, not the same-vs-different main
effect.** A same > different main effect is fully predicted by MODEL A and is
therefore not evidence for MODEL B. The frozen primary coefficient is
`FROZEN_PARAMS.PRIMARY_COEF = "partner_x_advantage"`.

---

## 2. The game and payoffs

Study 1's Stage C game, unchanged, so the two studies remain comparable.

| element | value | source |
|---|---|---|
| Coordination task | one-shot, no communication, binary choice between two forms; left/right position independently randomised per player, so position cannot carry the coordination | `psc_common.BASE`, prompt sha8 `3003ae1b` |
| ATTEMPT, match | **10 points** | `MATCH_PAYOFF` |
| ATTEMPT, mismatch | **0 points**, exactly | `MISMATCH_PAYOFF` |
| SAFE | a certain payoff from **{3, 5, 7, 9}** | `SAFE_PAYOFFS` |
| Partner always plays | yes — stated in the prompt, load-bearing | `psc_common.betting_prompt` |
| Framing | **neutral**; no strategic or normatively loaded vocabulary appears in any prompt | `FRAMING` |

`MISMATCH_PAYOFF = 0` is not a convenience. It makes the EV of ATTEMPT exactly
`10 · p_match`, so the SAFE grid maps onto four clean indifference points:

| SAFE | 3 | 5 | 7 | 9 |
|---|---|---|---|---|
| EV-indifference match probability | 0.30 | 0.50 | 0.70 | 0.90 |

An actor that knew its own policy and its partner's perfectly would ATTEMPT iff
`p_match > SAFE/10`, where `p_match` is the **own-copy** rate under a same-model
partner and the **cross-model** rate under a different-model partner. The
difference between those two numbers is exactly the compatibility advantage
defined in §3. That is what makes the advantage a *dose*, in payoff units, and not
merely a covariate.

Each trial is an **independent one-shot API call**. No conversation history, no
memory across trials, no feedback about outcomes. Sampling settings, parse rules
and retry policy are Study 1's, unchanged.

---

## 3. The partner manipulation

Two conditions, `FROZEN_PARAMS.PARTNER_CONDITIONS = ("same", "different")`.

Study 1's clause — "another instance of you (the same AI model)" — has no
symmetric counterpart; any different-partner rewrite of it changes more than the
partner. Study 2 therefore uses **one clause template**, instantiated with a
model display name:

> "… with ONE other player — an instance of **{NAME}**."

- `same`: `{NAME}` = the actor's own display name (`GPT-5.5`, `Claude Opus 5`).
- `different`: `{NAME}` = the other model's display name.

**Symmetry is the experiment.** With `{NAME}` normalised to a placeholder the two
arms are **byte-identical**; `code/test_study2.py` asserts exactly that, and the
emitted clause is written verbatim into every output row
(`partner_condition_text`) so the arms can be diffed post hoc without re-running.
Everything else — BASE's position-randomisation warning, the payoff paragraph,
the two-line answer format — is Study 1 verbatim.

This is a deliberate, documented deviation from Study 1's prompt. Consequence:
Study 2's `same` cell is **not** byte-identical to Study 1's Stage C cell. The
same-vs-different contrast is internal to Study 2 and never leans on Study 1's
numbers.

Because a crossed-up condition label is the single most damaging possible runner
bug, `partner_model_named` is written on every row and checked against
`partner_condition` at load time rather than trusted.

---

## 4. Compatibility: definition and estimator

**Definition** (`FROZEN_PARAMS.ADVANTAGE_DEF = "own_minus_cross"`):

```
advantage(actor, s) = own-copy reliability(actor, s) - cross-model reliability(s)

    focal GPT     :  GG(s) - GC(s)
    focal Claude  :  CC(s) - GC(s)
```

**Own-copy estimator** — frozen and imported, never reimplemented:
`targeted_common.unbiased_match`,

```
own(m, s) = Σ_k n_k (n_k - 1) / [ N (N - 1) ]
```

Bias-corrected: both draws come from the same finite sample, so the plug-in
`Σ_k p_k²` counts each trial as agreeing with itself and is inflated by ≈ 1/N.

**Cross-model estimator — DERIVED FROM MARGINALS, and this is a design commitment,
not a shortcut:**

```
GC(s) = Σ_k p_k^gpt · p_k^claude ,      p_k^m = n_k^m / N^m
```

estimated from the two models' **independently collected** binary-choice
marginals. Implemented in `code/cross_model_match.py`.

Three reasons this is the correct estimator here and new simultaneous cross-model
calls are **not** run:

1. **It matches the game.** The game is simultaneous and communication-free. The
   payoff-relevant quantity is the probability that an independent GPT draw and an
   independent Claude draw land on the same identity. That is exactly the product
   of marginals. A "cross-model call" would be a different, interactive object.
2. **It is already unbiased.** The two draws come from disjoint samples, so there
   is no same-draw pair to remove; applying the `(n-1)` correction here would
   over-correct and bias `GC` downward.
3. **It costs nothing extra and shares the Stage A sample**, so own-copy and
   cross-model estimates rest on the same trials and the same prompt.

The estimand is the **layout-marginal** agreement rate: agreement when each player
independently sees a randomised AB/BA layout. AB/BA balance is exact by
construction (§7), so no reweighting is needed.

**Assumption, stated because it is load-bearing.** The product-of-marginals form
assumes the two models' choices are conditionally independent given the stimulus.
They are never run in the same call, so there is no channel through which they
could correlate other than the stimulus itself. This assumption cannot be tested
without interactive cross-model runs, which the design deliberately does not make.
It is recorded in §13 as an interpretation limit.

---

## 5. THE STRUCTURAL CONSTRAINT — read this before questioning the allocation

Every stimulus is a binary choice between two identities. Write `p` and `q` for
`P(identity_1)` under GPT and Claude, and let `a = |2p-1|`, `b = |2q-1|` be how
decisive each model is. Then

```
GG = 1/2 + a²/2        CC = 1/2 + b²/2        GC = 1/2 ± ab/2
```

and therefore, **exactly**,

> ### |GC − 1/2| = √( (GG − 1/2) · (CC − 1/2) )

**The cross-model rate is the geometric mean of the two own-copy deviations from
chance. Only its SIGN is free** — the sign records whether the two models land on
the same identity or on opposite ones.

**Verified in data.** `pairs/crossover_feasibility.py` checks the identity against
all 15 battery stimuli (Stage A, n = 60 per model per stimulus, GPT-5.5 / Claude
Opus 5, 2026-08-12): **mean |residual| = 0.006** (re-verified by
`code/design_table.py` check P2: mean 0.0059, max 0.0412 — sampling noise only;
the identity is exact in the limit).

### 5.1 What follows for the design — three consequences

1. **"Own-copy LOW but cross HIGH" cannot exist. At any n.** If a model is near
   chance it matches *every* partner at almost exactly 1/2, itself included. The
   intuitively attractive stimulus — self-incompatible yet cross-compatible — is
   ruled out by algebra, not by this battery's size. No amount of data can
   manufacture it, and no reviewer request for it can be satisfied.
2. **What can push `GC` above `GG`** is the *partner* being more decisive while
   agreeing: `GC > GG` exactly when `CC > GG` and the modal identities match. The
   reversal is real, but its magnitude is bounded by how much more decisive the
   partner is — which is why the observed negative advantages are ≈ −0.11 to
   −0.13 and not −0.5.
3. **The strongest incompatibility is a *below-chance* cross rate**, both models
   decisive on *opposite* identities, driving `GC` toward 0. That is
   anti-coordination, and it is a far bigger lever than ambiguity. It is what
   makes `a_chev_ud` (GG 0.817, CC 0.845, GC 0.167) the largest-advantage
   stimulus in the battery.

### 5.2 The consequence that drives the sample-size allocation

Negative-advantage cells are **necessarily small in magnitude** — bounded, by the
identity above, by how much more decisive the partner is. They are not small
because the battery is poor or because selection was lazy; they are small because
binary stimuli cannot make them large.

**Therefore the negative and near-zero cells, which carry the entire
discrimination between MODEL A and MODEL B, get the largest n, and the
large-advantage cells — which are nearly self-evident — get the smallest.**
Allocation is inverse to effect size. This is fixed in `FROZEN_PARAMS.GRADIENT`
before any Stage C call and is never revised in light of observed outcomes.

---

## 6. The stimulus gradient

Frozen in `FROZEN_PARAMS.GRADIENT`. Provisional advantages are from the n = 60
Stage A battery (2026-08-12) and are **provenance only** — the confirmation screen
(§7) re-estimates them and writes `CONFIRMED_ADVANTAGE`, which is what the
analysis uses. **Which stimuli enter is frozen here and does not change based on
what the confirmation returns.**

| actor | stimulus | tier | own | cross | provisional advantage | n per partner | n per payoff cell |
|---|---|---|---|---|---|---|---|
| gpt | a_chev_ud | large | 0.817 | 0.167 | **+0.650** | 32 | 8 |
| gpt | c_open_cplx | medium | 1.000 | 0.633 | +0.367 | 64 | 16 |
| gpt | d_texture | small | 0.501 | 0.444 | +0.057 | 120 | 30 |
| gpt | proto | zero_ceil | 1.000 | 1.000 | 0.000 | 64 | 16 |
| gpt | s_arrow | zero_ceil | 1.000 | 1.000 | 0.000 | 64 | 16 |
| gpt | rot | zero_floor | 0.573 | 0.500 | +0.073 | 120 | 30 |
| gpt | mirror | zero_floor | 0.497 | 0.490 | +0.007 | 120 | 30 |
| gpt | b_spiral_cw | **negative** | 0.655 | 0.783 | **−0.128** | 160 | 40 |
| claude | a_chev_ud | large | 0.845 | 0.167 | **+0.678** | 32 | 8 |
| claude | d_texture | medium | 0.845 | 0.444 | +0.401 | 64 | 16 |
| claude | b_spiral_cw | small | 1.000 | 0.783 | +0.217 | 120 | 30 |
| claude | proto | zero_ceil | 1.000 | 1.000 | 0.000 | 64 | 16 |
| claude | s_arrow | zero_ceil | 1.000 | 1.000 | 0.000 | 64 | 16 |
| claude | rot | zero_floor | 0.491 | 0.500 | −0.009 | 120 | 30 |
| claude | mirror | zero_floor | 0.512 | 0.490 | +0.022 | 120 | 30 |
| claude | c_open_cplx | **negative** | 0.528 | 0.633 | **−0.106** | 160 | 40 |

### 6.1 Why the gradient MUST span negative and zero

This is the load-bearing paragraph of the whole design.

**If every stimulus had a positive advantage, "same model" and "more compatible"
would be perfectly confounded, and MODEL A would predict exactly the pattern
MODEL B predicts.** Under an all-positive gradient both accounts say: attempt more
against the same-model partner, everywhere. The dose-response slope would then be
estimated only from *how much more*, over a range that never crosses zero — a
weak, model-dependent contrast that a constant shift plus any mild ceiling effect
can imitate. That is precisely the failure mode that made the earlier pair-based
version of Study 2 unidentifiable (`pairs/FINDINGS.md`: own-copy and cross-model
match correlate at +0.73 / +0.68 across the battery, and 0 of Study 1's 5 approved
pairs survive a cross-model audit).

The gradient breaks the confound in three places:

| tier | advantage | MODEL A predicts | MODEL B predicts | what a positive result rules out |
|---|---|---|---|---|
| large | ≈ +0.65 | same > different | same > different (strongly) | nothing on its own |
| zero_ceil / zero_floor | ≈ 0 | same > different | **same ≈ different** | a constant identity bonus |
| **negative** | ≈ −0.11 to −0.13 | same > different | **same < different** | a constant identity bonus, in the strongest possible way — a *sign reversal* |

The negative cells are the crux: MODEL A cannot produce a reversal at all. The
zero cells are the second crux: they hold the same-model *label* fixed while
setting the *dose* to zero.

### 6.2 The zero tier is deliberately split — ceiling and floor

`proto` and `s_arrow` sit at own = cross = 1.000; `rot` and `mirror` sit at
own ≈ cross ≈ 0.50. Both have zero advantage, at opposite ends of the absolute
match-probability scale. Without that split, advantage would track absolute
own-copy reliability, and hence the base attempt rate, and a base-rate account
could hide inside the slope. With it, correlation between advantage and own-copy
reliability across the 16 design cells is **+0.31** (+0.38 excluding `a_chev_ud`),
and between advantage and Study 1's generic-salience measure **+0.16** (+0.31
excluding `a_chev_ud`). Both are reported as covariates in §11.

The ceiling pair also serves as a **payoff-response manipulation check**: at
`p_match = 1.0` the EV-rational choice is ATTEMPT at every SAFE level, so a model
that opts out at SAFE = 9 on `proto` is not responding to EV at all.

### 6.3 The stimulus-reuse economy

`a_chev_ud`, `b_spiral_cw`, `c_open_cplx` and `d_texture` each occupy a
**different tier depending on which model is focal**. `b_spiral_cw` is the
negative cell for GPT and the small-positive cell for Claude; `c_open_cplx` is the
mirror image (medium for GPT, negative for Claude).

This is a feature, not an economy measure. **The same image cannot be carrying a
stimulus-level artefact in opposite directions for the two actors.** Any account
of a positive slope in terms of image properties — complexity, salience,
prettiness, familiarity — must explain why the identical image sits at opposite
ends of the gradient for the two models. `c_open_cplx` also carries the battery's
highest generic salience (0.651) while being a *negative*-advantage cell for
Claude, and `mirror` the lowest (0.110) while being a zero cell, so salience and
advantage are actively crossed rather than merely uncorrelated.

---

## 7. The confirmation screen and its gate

The provisional advantages come from n = 60 per model per stimulus. The negative
cells are ≈ −0.11 with that precision, which is not enough to anchor a slope. The
confirmation screen re-estimates own-copy rates at higher n **before** Stage C.

**Procedure.** Stage-A-style: independent one-shot calls, exact AB/BA balance,
`psc_common.BASE` verbatim (sha8 `3003ae1b`, asserted at import), unchanged parse
rules, unchanged API settings. Both models
(`FROZEN_PARAMS.CONFIRM_MODELS = ("gpt", "claude")`) on every stimulus in the
gradient, because `GC` needs both marginals.

| stimulus | confirmation n **per model** | why |
|---|---|---|
| a_chev_ud, b_spiral_cw, c_open_cplx, d_texture | 180 | these four carry the large / medium / small / negative tiers |
| rot, mirror | 120 | floor controls sit at p ≈ 0.5, the maximum-variance point |
| proto, s_arrow | 60 | ceiling controls at 1.000; there is no variance left to reduce |

Total confirmation calls: **1,080 × 2 models = 2,160**.

`CONFIRMED_ADVANTAGE` is **written once** by the confirmation screen and then
frozen with the rest of `FROZEN_PARAMS`. The per-identity **counts** are stored
alongside the point estimates, because the errors-in-variables analysis (§9) needs
them.

### 7.1 The gate — decidable, evaluated once, before any Stage C call

`FROZEN_PARAMS.GATE_CRITICAL_TIERS = ("large", "negative", "zero_floor")`. The
gate asks whether the **sign** and the **qualitative order** of the critical cells
replicate. A tier boundary shifting while sign and order hold is **not** a
failure; the confirmed value simply replaces the provisional one in the analysis.

| # | condition | threshold | scope |
|---|---|---|---|
| G1 | large-tier advantage positive and substantial | confirmed ≥ **+0.40** | both actors |
| G2 | negative-tier advantage negative | confirmed **< 0** | both actors |
| G3 | negative tier credibly below zero | 90 % credible interval wholly < 0 | **at least one** actor |
| G4 | zero-floor cells still near zero | \|confirmed\| ≤ **0.10** | all four cells |
| G5 | critical-tier order preserved | large > zero_floor > negative, on point estimates | within each actor |

**Actions.**

| outcome | action |
|---|---|
| G1–G5 all hold | **PROCEED** to Stage C at the frozen allocation |
| G1–G5 hold for one actor only | proceed with **that actor only**; the design becomes single-actor, flagged prominently, and the cross-actor stimulus-reuse argument (§6.3) is withdrawn |
| G2 fails for both actors (no negative cell survives) | **STOP.** Do not run Stage C. The gradient no longer spans zero and the design is back to the confound of §6.1 |
| G1 fails, G2 holds | **STOP.** Report that the gradient has collapsed |
| G4 fails (a zero cell has moved off zero) | **STOP** and re-freeze: the cell is no longer a zero control and the gradient must be re-specified before any Stage C call |
| parse-failure rate > 2 % in any confirmation cell | **STOP** and report |
| any confirmation cell < 90 % of its target n after retries | **STOP** and report |

Non-gating diagnostics, recorded either way: `proto` and `s_arrow` at own = cross
≥ 0.95 (if not, the ceiling controls are re-labelled in the writeup and §6.2's
manipulation check is withdrawn); the structural identity of §5 re-verified at the
confirmation n; the rank correlation between provisional and confirmed advantage
across all 16 cells.

---

## 8. Stage C allocation and budget

Frozen in `FROZEN_PARAMS.GRADIENT` (last field) and materialised by
`code/design_table.py` into `design/frozen_design_table.csv`.

- One row per **(actor × stimulus × partner × safe payoff)** cell: 2 × 8 × 2 × 4 =
  **128 cells**.
- `N_PARTNER` is the total for one (actor × stimulus × partner) block, split
  **evenly** across the four SAFE levels: per-payoff cell size = `N_PARTNER / 4`,
  ∈ {8, 16, 30, 40}, **all even**, so AB/BA counterbalancing is exact in every
  cell — half the trials show identity_1 on the left, half on the right.
- **Total Stage C calls: 2,976** (`FROZEN_PARAMS.stage_c_calls()`, asserted by
  `design_table.validate()`).
- **Total project calls: 2,160 + 2,976 = 5,136.**

Cell sizes are fixed **before** Stage C and are **never** altered after seeing
ATTEMPT outcomes. No optional stopping, no cell top-ups, no adaptive reallocation.

`confirmed_advantage` is written to the design table as an **empty column**; the
confirmation screen fills it exactly once. A Stage C run against a design table
whose `confirmed_advantage` column is still empty is a configuration error and
must abort.

Order of execution is randomised across cells and resumable: each invocation
writes its own part file, a restart skips completed cells and re-runs partial
cells from scratch, and a cell's rows always come from exactly one part file, so a
failed partial run is never merged with a good one.

---

## 9. Primary analysis — pre-specified

Trial-level, all Stage C trials, both actors pooled (and separately, §11):

```
logit P(ATTEMPT) = α_actor
                 + β_actor · SAFE
                 + γ · SAME
                 + η · ADVANTAGE
                 + δ · (SAME × ADVANTAGE)
```

- `SAME` = 1 in the same-model arm, 0 in the different-model arm.
- `ADVANTAGE` = `confirmed_advantage` for that (actor, stimulus).
- `η` absorbs stimulus-level differences common to both arms (an easy stimulus is
  attempted more whoever the partner is).
- **`δ` is the primary coefficient** (`FROZEN_PARAMS.PRIMARY_COEF =
  "partner_x_advantage"`). It is the dose-response slope.
- Random intercepts for stimulus; cluster-robust inference at the stimulus level.
  Because there are only 8 stimuli per actor, the headline interval is a
  **cluster bootstrap resampling whole stimuli** (5,000 draws), not a Wald
  interval on 8 clusters.

**The primary result is `δ` and its 95 % interval. `γ` — the same-vs-different
main effect — is reported but is NOT the test, and a positive `γ` on its own is
reported as consistent with MODEL A.**

### 9.1 ADVANTAGE is measured with error and is NOT treated as error-free

This is mandatory, not optional. Three estimates of `δ` are reported together:

1. **Latent-predictor / errors-in-variables model (headline).** The confirmed
   Stage A per-identity counts enter as data: `p^gpt_s`, `p^claude_s` get
   independent `Beta(1,1)` priors per (model, stimulus); own-copy and cross rates
   and hence `ADVANTAGE_s` are **deterministic functions** of those latents
   (binary case: `own = p² + (1−p)²`, `GC = p·q + (1−p)(1−q)`); the Stage C
   likelihood is the logit model above evaluated at the latent advantage. Fitted
   by MCMC. Sensitivity to a `Beta(1/2,1/2)` (Jeffreys) prior is reported.
2. **Plug-in estimate with a propagating bootstrap.** `δ` re-estimated over 5,000
   joint resamples of the confirmation counts *and* the Stage C trials, so Stage A
   uncertainty enters the Stage C interval.
3. **Plug-in point estimate**, reported for comparability only.

**Plain OLS on aggregated per-stimulus points is never the only analysis
reported**, and never the headline. With 8 stimuli per actor and an advantage
measured at n = 60–180, attenuation from measurement error is a first-order
effect, and its direction is *toward* the MODEL A prediction — the conservative
direction for a MODEL B claim, which is why the plug-in estimate is retained as a
lower bound rather than discarded.

---

## 10. MODEL A vs MODEL B — the frozen comparison

`FROZEN_PARAMS.MODEL_COMPARISON = ("A_coarse_identity", "B_policy_specific")`.

| | model | form | free parameters beyond the base |
|---|---|---|---|
| **A** | coarse identity heuristic | `… + γ · SAME` | `γ` |
| **B** | policy-specific sensitivity | `… + γ · SAME + δ · (SAME × ADVANTAGE)` | `γ`, `δ` |

Both share `α_actor`, `β_actor · SAFE` and `η · ADVANTAGE`, so the comparison is
purely about whether the *partner* effect is constant or advantage-graded.
MODEL A is nested in MODEL B at `δ = 0`.

Reported for the comparison, all three, pre-specified:

1. **`δ` and its 95 % cluster-bootstrap interval** (§9). MODEL B is supported if
   `δ > 0` and the interval excludes 0.
2. **Model comparison by information criterion**: WAIC and LOO-CV (PSIS) on the
   fitted Bayesian models, with standard errors of the difference. Reported with
   the caveat that these are trial-level criteria on clustered data.
3. **The reversal test, which is MODEL B's unique prediction.** Restricted to the
   negative-advantage cells only, the same-minus-different attempt-rate contrast,
   with a permutation test that shuffles the partner label **within (actor ×
   stimulus × payoff) strata**, on **raw counts, never rounded rates**, 20,000
   permutations, one-sided (H₁: same < different in the negative cells).

   The raw-counts rule and the `−1e-12` tie tolerance are carried over
   deliberately from Study 1's 2026-08-12 fix, where rounding a rate column to 4
   decimals moved the observed statistic off the achievable lattice and silently
   dropped the tied permutation replicates that carry most of the one-sided tail.

**Decision rule, stated in advance.**

| pattern | conclusion |
|---|---|
| `δ > 0`, interval excludes 0, **and** the reversal test is significant | MODEL B supported; the strongest available result |
| `δ > 0`, interval excludes 0, reversal test null | MODEL B supported for graded sensitivity, **but** the sign reversal is not established; reported as such, with the negative cells' limited magnitude (§5.2) as the likely reason |
| `δ` interval includes 0, `γ > 0` | consistent with MODEL A; a coarse identity heuristic is the parsimonious reading |
| `δ` interval includes 0, `γ` interval includes 0 | no partner effect of either kind; report the null against the pre-specified power |
| `δ < 0` with interval excluding 0 | an unpredicted anti-dose-response; reported as an unexplained finding, **not** re-described as support for either model |

---

## 11. Robustness and secondary analyses — pre-specified, none may replace §9

1. **`a_chev_ud` exclusion** (`FROZEN_PARAMS.SENSITIVITY_EXCLUDE`). `a_chev_ud`
   supplies the largest advantage for **both** actors (+0.650 / +0.678) and will
   dominate the slope. `δ` is reported **with all stimuli and again excluding
   `a_chev_ud`**. The exclusion is a sensitivity analysis; `a_chev_ud` stays in
   the primary data. Excluding it shortens the advantage range from
   [−0.128, +0.678] to [−0.128, +0.401], and the report states the reduced range
   explicitly whenever the excluded estimate is quoted.
2. **Per-actor estimates** (`FROZEN_PARAMS.REPORT_SEPARATELY`). `δ` for GPT and
   for Claude, reported separately alongside the pooled estimate. A pooled `δ`
   driven entirely by one actor is reported as such.
3. **Leave-one-stimulus-out.** `δ` recomputed 8 times per actor, each time
   dropping one stimulus. A **sensitivity analysis, not 8 hypothesis tests**; no
   per-fold p-value is interpreted as a test.
4. **Ceiling-vs-floor zero contrast.** Same-minus-different at `proto`/`s_arrow`
   versus at `rot`/`mirror`. MODEL B predicts ≈ 0 in both; a difference indicates
   that the absolute match probability, not the advantage, is driving behaviour.
5. **Base-rate and salience covariates.** `δ` refitted adding (a) the actor's
   own-copy rate and (b) Study 1's generic-salience measure as stimulus-level
   covariates. Reported because advantage correlates +0.31 with own-copy rate and
   +0.16 with salience across the 16 design cells (§6.2).
6. **Payoff response.** Attempt rate against SAFE ∈ {3,5,7,9} per cell, and the
   fitted `β_actor`. A model with `β ≈ 0` is not making a risky choice at all, and
   every advantage-based reading is void for that actor.
7. **EV benchmark, descriptive.** Observed attempt rate against the EV-rational
   step function `ATTEMPT iff 10 · p_arm > SAFE`, with `p_arm` = own-copy under
   `same` and cross-model under `different`. This is the normative ceiling for
   MODEL B, reported as a benchmark and **never** as a test.
8. **Arm symmetry audit.** The two arms' prompts diffed with `{NAME}` normalised;
   `partner_model_named` cross-checked against `partner_condition` on every row;
   AB/BA balance and parse-failure rate reported per cell.
9. **Study 1 comparison, descriptive only.** Study 2's `same` arm is not
   byte-identical to Study 1's Stage C (§3), so any comparison is descriptive and
   is never pooled into the primary claim.

---

## 12. Stopping and failure conditions

| condition | action |
|---|---|
| `design_table.validate()` fails | **STOP.** No call is made until it passes |
| model ID returned ≠ model ID requested | **STOP** mid-stage, report the raw provider response |
| prompt sha8 ≠ `3003ae1b` | `psc_common` refuses to import; **STOP** |
| parse-failure rate > 2 % in any stage | **STOP** and report |
| confirmation cell < 90 % of target n after retries | **STOP** and report (§7.1) |
| confirmation gate fails | **STOP** or single-actor, per the §7.1 table |
| `confirmed_advantage` column still empty at Stage C launch | abort — configuration error |
| any write attempted outside `study2_partner_policy_20260822/` | assert-fail |
| Stage C cell incomplete after retries | report the realised n per cell; **do not** substitute trials from another cell |

---

## 13. Interpretation limits

The permitted framing is fixed in `FROZEN_PARAMS`:

> "models selectively entered risky coordination opportunities as a function of
> the empirical compatibility between their policy and their partner's policy."

`design/INTERPRETATION_GUARDRAILS.md` holds the full checklist, and
`code/check_terms.py` enforces the forbidden vocabulary mechanically over this
study's markdown and figure captions. Substantive limits:

1. **Behaviour, not access.** The advantage is measured from behaviour. A model
   whose betting tracks it is behaving *as if* it had information about its own
   and its partner's policy. The mechanism by which that information reaches the
   decision is **not** measured here, and no claim about it is licensed —
   including the claim that the model consulted anything about itself.
2. **The advantage is not shown to the model.** It never appears in a prompt. But
   it correlates with observable stimulus properties, and a MODEL B result is
   consistent with the model reading those properties rather than anything about
   the partner. §6.3's opposite-tier stimulus reuse and §11.5's covariates bound
   this, they do not eliminate it.
3. **Name familiarity is only partly controlled.** The two arms differ in a model
   name token. The slope test is what distinguishes a partner-policy account from
   a name-familiarity account, because familiarity is constant across stimuli
   while the advantage is not. The main effect `γ` alone cannot make this
   distinction.
4. **Cross-model independence is an assumption** (§4). It is not tested, because
   the design deliberately makes no interactive cross-model calls.
5. **The negative range is bounded by algebra** (§5). Advantage runs
   [−0.128, +0.678] and is strongly asymmetric. The design can detect a reversal;
   it cannot estimate the slope on the negative side with the precision available
   on the positive side, and a null reversal test is weak evidence against MODEL B.
6. **Scope.** Two model versions (GPT-5.5, Claude Opus 5), one prompt family, 8
   binary visual stimuli, one payoff structure, one point in time. Nothing here
   generalises across model versions without re-running the pipeline; Study 1's
   companion replication showed that the particular conventions change between
   generations even when the procedure recovers the same structure.
7. **`c_open_cplx` and `b_spiral_cw` do double duty** across actors (§6.3). If a
   result depends on those two stimuli alone, the leave-one-stimulus-out analysis
   (§11.3) will show it, and the report must say so.

---

## 14. Archive layout and provenance

```
study2_partner_policy_20260822/
  design/
    FROZEN_PARAMS.py              SINGLE SOURCE OF TRUTH; CONFIRMED_ADVANTAGE written once
    STUDY2_SPEC_FROZEN.md         this document
    INTERPRETATION_GUARDRAILS.md  claim checklist
    frozen_design_table.csv       128 Stage C cells, emitted by code/design_table.py
    power_analysis.py             from the earlier pair-based version; see §14.1
  code/
    design_table.py               emits + validates the design table
    check_terms.py                forbidden-vocabulary scan, exits nonzero on a hit
    cross_model_match.py          the derived-from-marginals cross estimator
    study2_betting.py             Stage C runner; see §14.1
    analyze_study2.py             analysis; see §14.1
    study2_schema.py              runner/analysis schema contract
  pairs/
    crossover_feasibility.py      verifies the §5 structural identity against the data
    cross_model_table.csv         Stage A own-copy + cross rates, 15 stimuli
    FINDINGS.md                   why the earlier pair-based design was unidentifiable
  data/ analysis/ figures/
```

Stage A ground truth is the 2026-08-12 battery in
`policy_specific_self_coordination_20260812_1401/`. **No file in that project is
written to.** `psc_common`'s own `PSC_EXP_DIR` mechanism redirects every output
path into this tree.

### 14.1 Code written against the SUPERSEDED pair-based design

`code/study2_betting.py`, `code/analyze_study2.py`, `code/study2_schema.py`,
`code/simulate_study2_data.py` and `design/power_analysis.py` were written for the
earlier 2 (HIGH/LOW pair) × 2 (partner) version of Study 2, which
`pairs/FINDINGS.md` showed to be unidentifiable on this battery. They are retained
for their infrastructure — resumable part files, the symmetric partner clause, the
schema contract, the raw-counts permutation test — but **before any Stage C call
they must be re-pointed at `design/frozen_design_table.csv`**:

| module | required change |
|---|---|
| `study2_betting.py` | read cells from `frozen_design_table.csv` instead of `pairs/study2_candidate_pairs.csv`; per-cell n from the table, not a global `n_per_cell` |
| `study2_schema.py` | replace `pair_id` / `stimulus_level` with `tier` and `confirmed_advantage`; keep `partner_condition`, `partner_model_named`, `partner_condition_text` |
| `analyze_study2.py` | replace the HIGH/LOW difference-in-differences with the §9 slope model; keep the raw-counts permutation machinery for §10.3 |
| `power_analysis.py` | superseded: it powers the pair-based interaction, not the slope. Any power statement quoted in the writeup must come from a re-run against this design |

The `data/study2C_*_DRY.csv` files are dry-run artefacts of the superseded design
and are not analysis inputs.

### 14.2 Verified at freeze time

`python3 code/design_table.py`, 2026-08-22:

```
V1 total Stage C calls  : 2976 vs FROZEN_PARAMS.stage_c_calls() = 2976  OK
V2 per-payoff cells even: 128/128 (sizes [8, 16, 30, 40])  OK
V3 stimuli in BATTERY   : 8/8  OK
   stimuli in manifest  : 8/8  OK
V4 cells complete/unique: OK   confirmed_advantage empty: OK
V5 CONFIRM_N covers all : OK   confirmation calls = 2160
P1 provisional advantage vs cross_model_table.csv : max |diff| = 0.001
P2 |GC-1/2| = sqrt((GG-1/2)(CC-1/2)) : n = 15, mean |residual| = 0.0059, max = 0.0412
```

Registry source: `import psc_common` with prompt sha8 `3003ae1b` asserted at
import; manifest
`policy_specific_self_coordination_20260812_1401/stimulus_manifest.csv`, 15
stimuli.
