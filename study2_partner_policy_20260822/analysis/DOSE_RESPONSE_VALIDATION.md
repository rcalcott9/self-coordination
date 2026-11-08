# Study 2 (revised) — validation of the dose-response analysis

`analyze_dose_response.py` is the frozen primary analysis for the **revised** Study 2,
in which the primary test is no longer a Stimulus × Partner interaction but a
**dose–response relation**: does the same-vs-different partner effect on P(ATTEMPT)
scale with the empirically measured compatibility advantage of each stimulus?

```
MODEL A   coarse identity heuristic     partner effect = c            (no advantage term)
MODEL B   policy-specific sensitivity   partner effect = c + b·adv    (b > 0)
```

The primary coefficient is **b**, `FROZEN_PARAMS.PRIMARY_COEF = "partner_x_advantage"`.
It is not the average same-model effect. MODEL A predicts a positive average
same-model effect just as readily as MODEL B does, so that quantity discriminates
nothing; only the slope does. The analysis says so at every point where it prints a
partner main effect, and the verdict rule below never lets a positive intercept count
toward a MODEL B conclusion.

The analysis was written **before any Study 2 data exist**. A frozen analysis that has
never been run is a frozen guess, so it was run against simulated data whose ground
truth we set. This document records those truths, what was recovered, the
errors-in-variables versus plug-in comparison, and the schema assumptions.

Nothing here makes an API call.

## Reproducing everything

```
cd study2_partner_policy_20260822/code

python3 simulate_study2_data.py --truth dose_b       --out ../data/sim_dose_b.csv
python3 simulate_study2_data.py --truth dose_a_logit --out ../data/sim_dose_a_logit.csv
python3 simulate_study2_data.py --truth dose_a_rd    --out ../data/sim_dose_a_rd.csv
python3 simulate_study2_data.py --truth dose_null    --out ../data/sim_dose_null.csv

python3 analyze_dose_response.py --data ../data/sim_<truth>.csv \
                                 --confirm ../data/sim_<truth>_confirmA.csv --tag <truth>
python3 figure_dose_response.py  --tag <truth>
```

Each simulator run writes three files: the Stage C trials in the runner's schema, a
**confirmation-screen counts** file, and a `_truth.json` with the generating
parameters and the exact implied population quantities. Seeds are fixed
(`--seed 20260822`), so every number below is reproducible byte for byte.

---

## 1. What is reused, and what is new

`analyze_study2.py` (the interaction analysis) and `study2_schema.py` were already
validated. The dose-response analysis **extends** them rather than restating them. It
imports and calls, unchanged:

| reused from `analyze_study2` | what it does |
| --- | --- |
| `_resolve_aliases` | canonical-column resolution through the schema's alias table |
| the re-derived validity filter | `included_in_analysis` recomputed from `(not superseded_by_retry) and valid_response`, and the run **refused** if the runner's column disagrees |
| `check_partner_naming` | the anchored crossed-condition check — the single most damaging possible runner bug, caught by comparing `partner_model_named` against the row's own `actor_model_name` |
| `assign_halves` | Study 1's reproducible select/holdout cut, ordered by `run_id` within (cell × variant) so each half is exactly AB/BA balanced |
| `_hyper`, `_pvals` | exact conditional hypergeometric permutation draws on integer counts, with the `−1e-12` tie tolerance that Study 1's rounding bug made necessary |
| `resolve_data` | refuses to guess between unmerged runner part files |
| `_seed` | SHA-256 derived seeds, not salted `hash()` |

New, because the revised design has no matched HIGH/LOW pairs: a loader keyed on
stimulus and tier rather than `pair_id`/`stimulus_level`, the advantage estimator, the
trial-level dose-response model, the model comparison, and the errors-in-variables
sampler.

`analyze_study2.py` itself is untouched, and so is the simulator's original
matched-pair mode. Because `study2_schema.py` did change (new `DOSE_COLS`, new alias
entries), the interaction pipeline was **regression-tested** after the change:
`simulate_study2_data.py --truth interaction` followed by `analyze_study2.py` still runs
end to end and still recovers a significant interaction (+0.1864, one-sided permutation
p = 0.0070 on the holdout sample), so `analysis/VALIDATION.md`'s numbers still
reproduce.

---

## 2. Schema assumptions

`study2_schema.py` gained a documented block for the revised design. The assumptions
are listed here so a mismatch shows up as one explicit failure at load time rather
than as a silent mis-analysis.

### 2.1 Stage C additions

```
DOSE_COLS = ["compatibility_advantage", "tier"]
COLS_DOSE = COLS + DOSE_COLS
```

* **`compatibility_advantage`** — per (actor × stimulus). REQUIRED-OR-DERIVED. The
  runner may emit it for provenance; **the analysis never analyses it**. The analysed
  value always comes from the confirmation-screen counts, because that is the only
  version whose sampling error is available to the errors-in-variables model. The
  runner's column is compared against the confirmed value and any discrepancy above
  `study2_schema.ADVANTAGE_TOL = 0.02` is reported in the log. A per-trial rather than
  per-cell value is also detected and reported.
* **`tier`** — the frozen gradient tier. Derived from `FROZEN_PARAMS.GRADIENT` when
  absent. Any (actor, stimulus) that resolves to no tier is named in the log.

`DOSE_COLS` is a *separate* list rather than an addition to `COLS`, because the
original simulator writes exactly `S.COLS` and would raise on a column its row dict
does not have. Adding to `ALIASES` is safe and was done, so alias resolution picks the
new columns up.

### 2.2 The confirmation screen — the load-bearing assumption

`FROZEN_PARAMS` section 4 specifies the confirmation screen but not its file format,
so the analysis accepts **either** form and logs which it used:

1. **per-trial**, Stage-A shaped: `actor_model` (or `model`/`focal_model`),
   `stimulus`, `parsed_choice_identity`, plus the usual validity columns. Counts are
   aggregated here against the manifest.
2. **aggregated**: `model, stimulus, n, k_identity1`.

Both paths are exercised (`--confirm-per-trial` in the simulator) and give the same
answer.

**Canonical identity labelling.** `k_identity1` counts the valid trials on which the
model named `identity_1` **as `stimulus_manifest.csv` defines it**, the same labelling
for both models. This is not a formatting detail. For a binary stimulus,

```
own[m]   = pi_m^2 + (1 - pi_m)^2
cross    = pi_g·pi_c + (1 - pi_g)(1 - pi_c)
adv[m]   = own[m] - cross
```

and the **sign** of `cross − 1/2` is the only free quantity in the structural
constraint of `FROZEN_PARAMS` section 2. Counting each model against its own modal
identity instead would destroy that sign and turn an anti-coordinating stimulus into a
compatible one. `a_chev_ud` is exactly such a case: GPT's mode is *up*, Claude's is
*down*, and the whole reason it is the large-advantage stimulus for both actors is that
they are decisive on **opposite** identities.

**Estimators.** The point estimate uses the frozen definitions inherited from
`cross_model_match.py`: the `(n−1)`-corrected `unbiased_match` for own-copy, the plain
plug-in for cross-model (the documented asymmetry — the correction belongs where the
two draws come from one cell, and would over-correct across two independent cells).
The copy is checked at run time against `pairs/cross_model_table.csv`; over the 16
(actor × stimulus) cells the reproduction error is **max |diff| = 0.0008** against
`FROZEN_PARAMS.GRADIENT`'s provisional values.

In the *latent* model the `(n−1)` correction is deliberately **not** applied: `own` and
`cross` there are exact functions of the latent `pi`, so there is no finite-sample bias
to correct and applying it would introduce one.

### 2.2b Reconciliation with the real confirmation screen (2026-08-22)

`code/confirm_compat.py` landed **while this analysis was being validated** and has now
run. It writes `design/confirmed_compatibility.csv`, and its schema is not either of the
two forms assumed above: it publishes `GG`, `CC`, `GC`, both advantages and their
bootstrap CIs — plus `modal_gpt` / `modal_claude` — but **no raw identity counts**. It
has, however, already done the provenance-guarded merge across the four resume part
files and self-checked its code path against `pairs/cross_model_table.csv`.

Redoing that merge here would duplicate it and risk disagreeing with it, so the analysis
reads its **output** and recovers the counts the errors-in-variables model needs. The
recovery is **exact, not an approximation**, for the same reason the design works at all
— every stimulus is a binary choice:

```
sum_k p_k²  = (own_unbiased·(n−1) + 1) / n        invert the frozen (n−1) correction
            = ½ + u²/2                             so |u| = √(2·(sum p² − ½))
sign(u)     from modal_gpt / modal_claude against the manifest's identity_1
```

The reconstruction is then **verified** by recomputing `GG`, `CC`, `GC` and both
advantages from the recovered counts and comparing against the table's own columns. On
the real file the **maximum residual is 0.00007** across all eight stimuli and both
actors. A residual above 0.005 makes the analysis refuse rather than proceed on a
reconstruction it cannot vouch for.

Recovered counts (identity-1 successes out of n), against the table's advantages:

| stimulus | GPT k/n | Claude k/n | adv GPT (recovered / table) | adv Claude (recovered / table) |
| --- | --- | --- | --- | --- |
| `a_chev_ud` | 138/180 | 38/180 | +0.2943 / +0.2943 | +0.3191 / +0.3192 |
| `b_spiral_cw` | 45/180 | 0/180 | −0.1271 / −0.1271 | +0.2500 / +0.2500 |
| `c_open_cplx` | 1/180 | 90/180 | +0.4889 / +0.4889 | −0.0028 / −0.0028 |
| `d_texture` | 117/180 | 87/180 | +0.0475 / +0.0475 | +0.0028 / +0.0028 |
| `mirror` | 58/120 | 30/120 | −0.0120 / −0.0119 | +0.1135 / +0.1135 |
| `proto` | 60/60 | 60/60 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| `rot` | 83/120 | 60/120 | +0.0699 / +0.0699 | −0.0042 / −0.0042 |
| `s_arrow` | 60/60 | 60/60 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

`design/confirmed_compatibility.csv` is now the **first** path the analysis tries, ahead
of the aggregated and per-trial forms, which remain supported.

### 2.3 What happens with no confirmation screen

The analysis **exits** unless `--allow-provisional` is passed. With that flag it runs
on `FROZEN_PARAMS.GRADIENT`'s provisional values, **disables the EIV model** (those
values carry no sampling error to propagate), and stamps every slope as a plug-in
estimate. It will not silently substitute the provisional gradient for the confirmed
one. All three paths were exercised.

### 2.4 Sample splitting — a declared departure

The interaction analysis reported HOLDOUT as primary. This one reports **FULL**, for an
arithmetic reason: the frozen allocation gives the large-advantage cells
`N_PARTNER = 32`, i.e. 8 trials per payoff cell, and halving leaves 4. The split is
still computed and all three samples printed. `--sample holdout` restores the older
convention.

---

## 3. The four ground truths

The generator builds `pi` for every (model × stimulus) by **inverting** the provisional
advantages. With `u = 2(pi_g − ½)`, `v = 2(pi_c − ½)` and `w = u − v`:

```
adv_g + adv_c = w²/2      →      w = √(2(adv_g + adv_c)),  u = 2·adv_g/w,  v = u − w
```

so the marginals are recovered exactly up to a global sign that only relabels the two
identities. Two stimuli push a fraction past the `|u| ≤ 1` boundary on the rounded
provisional values and are clipped; the residual is printed — **max |reconstructed −
provisional advantage| = 0.0204**, at `c_open_cplx`. The zero-advantage ceiling
controls are the degenerate `w = 0` case and are set to `pi = 1`.

The confirmation screen is then **simulated as binomial counts** at
`FROZEN_PARAMS.CONFIRM_N`. The analysis is never handed the true advantage; it must
re-estimate it from those counts, with real sampling error. That is what makes the
errors-in-variables machinery testable rather than decorative.

Stage C uses the frozen allocation exactly: 2 976 planned calls, 3 126 rows written
(retries included), 2 960 valid trials, 16 lost to a failed retry, per dataset.

| truth | scale | generating parameters | what it tests |
| --- | --- | --- | --- |
| `dose_b` | logit | `g0 = +0.10`, `g1 = +1.40` | **MODEL B true.** The shift is proportional to advantage. |
| `dose_a_logit` | logit | `g0 = +0.60`, `g1 = 0` | **MODEL A true, adversarial.** A constant log-odds shift, `g1` exactly zero. |
| `dose_a_rd` | risk difference | constant `+0.10` on P(ATTEMPT) | **MODEL A true**, on the other scale — the literal "constant same-model shift". |
| `dose_null` | — | no partner effect at all | payoff response only. |

### The scale trap, and why `dose_a_logit` is built the way it is

"A constant same-model shift" is scale-dependent. A shift constant in **log odds** is
not constant in **risk difference**: it is largest where the baseline attempt rate is
near 0.5 and shrinks toward the 0/1 ceilings. So a pure MODEL A process manufactures a
nonzero risk-difference slope whenever the baseline varies systematically with
advantage — and the induced slope is **positive**, i.e. it mimics MODEL B, precisely
when the low-advantage stimuli sit further from 0.5 than the high-advantage ones.

The generator therefore sets the baseline attempt rate to fall from **0.88 at the most
negative advantage to 0.50 at the largest**. That is the arrangement that makes the
artefact point the *dangerous* way. Any other choice would make `dose_a_logit` easier
to pass than it should be. It is the same failure mode the interaction validation named
`main_effect_low_base`, generalised to a gradient.

**Consequence, and it is the central result of this validation: a risk-difference slope
alone cannot separate MODEL A from MODEL B.** Under `dose_a_logit` the *true* population
risk-difference slope is **+0.0627**, not zero, with `g1` exactly zero in the generating
model. Anything that reads a positive risk-difference slope as evidence for MODEL B
would be wrong here. The analysis handles this three ways: the model comparison runs on
the **logit** scale where MODEL A's constant is genuinely constant; a
**baseline-artefact diagnostic** prints how much slope the fitted MODEL A produces by
itself; and the verdict rule requires the out-of-sample comparison, not the slope, to
decide.

`dose_a_rd` carries a related honesty note. A constant *additive* shift is not
well-defined near the ceiling — 0.974 + 0.10 does not exist — so the generator clips,
and the clipping bites hardest at the high-baseline, low-advantage stimuli. Its true
risk-difference slope is therefore **+0.0382** rather than 0. That is a property of the
estimand, not of the analysis, and it is reported rather than engineered away.

---

## 4. What was recovered

Pooled scope (shared slope, actor-specific intercepts and payoff slopes), FULL sample,
all stimuli. `g1` is the risk-difference-scale Partner × Advantage slope; `p₁` is the
one-sided permutation p from 20 000 exact hypergeometric replicates; LOSO is
leave-one-stimulus-out predictive log-loss on the held-out same-partner cells, lower is
better.

| truth | true g1 | **recovered g1** | 95 % CI | p₁ | LRT p | ΔAIC (A−B) | LOSO 0 / A / B | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dose_b` | **+0.2418** | **+0.2422** | [+0.108, +0.382] | **0.0007** | 0.0017 | **+7.86** | 645.1 / 649.4 / **642.7** | **MODEL B** |
| `dose_a_logit` | **+0.0627** | **+0.0664** | [−0.071, +0.207] | 0.1896 | 0.8489 | −1.96 | 588.5 / **569.3** / 572.3 | **MODEL A** |
| `dose_a_rd` | **+0.0382** | **+0.0529** | [−0.084, +0.187] | 0.2383 | 0.9753 | −2.00 | 521.1 / **498.7** / 502.5 | **MODEL A** |
| `dose_null` | **0.0000** | **+0.0366** | [−0.104, +0.181] | 0.3247 | 0.5076 | −1.56 | **680.4** / 680.6 / 684.2 | indistinguishable |

**The separation the design exists to make is achieved.** A constant same-model shift
does **not** produce a significant slope (p₁ = 0.19 and 0.24), does **not** move the
likelihood toward MODEL B (LRT p = 0.85 and 0.98, ΔAIC negative in both), and is
correctly identified out of sample. A true dose-response is recovered essentially
without bias (+0.2422 against a true +0.2418) and is decisively preferred.

Point-estimate accuracy across all four truths: the largest error in the recovered
risk-difference slope is **+0.037** (`dose_null`, where the truth is exactly 0 and the
bootstrap CI is [−0.104, +0.181]), and the errors on the two informative cases are
**+0.0004** (`dose_b`) and **+0.0037** (`dose_a_logit`).

### The baseline-artefact diagnostic does its job

The diagnostic takes the **fitted MODEL A**, which has no advantage term at all, reads
off the per-stimulus risk difference it implies, and regresses those on advantage:

| truth | observed g1 | artefact from fitted MODEL A | excess |
| --- | --- | --- | --- |
| `dose_b` | +0.2422 | **+0.0055** | +0.2367 |
| `dose_a_logit` | +0.0664 | **+0.0467** | +0.0197 |
| `dose_a_rd` | +0.0529 | **+0.0451** | +0.0078 |
| `dose_null` | +0.0366 | −0.0110 | +0.0476 |

Under both MODEL A truths the diagnostic attributes ~70–85 % of the observed
risk-difference slope to the link nonlinearity alone, and under MODEL B it attributes
2 %. This is the number that tells a reader whether to trust the risk-difference slope
or to read the logit-scale comparison instead, and the analysis prints an explicit
warning when the artefact exceeds a quarter of the observed slope.

### Model comparison, in detail

Three criteria, all reported, because they answer different questions.

* **LRT / AIC / BIC**, in-sample on the trial-level binomial likelihood. Under `dose_b`:
  χ² = 9.86 on 1 df, p = 0.0017, ΔAIC = +7.86, ΔBIC = +1.87. Under both MODEL A truths
  the LRT is nowhere near significance and ΔAIC and ΔBIC both favour A. Note BIC is much
  harsher than AIC throughout — with ~2 960 trials the BIC penalty is ≈ 8 nats per
  parameter — so BIC favours A even in `dose_b` at some scopes. Both are printed; the
  kinder one is not selected after the fact.
* **Leave-one-stimulus-out**, the criterion to read. Each stimulus is held out; A and B
  are fitted on the rest; the held-out stimulus's baseline is refitted **from its
  different-partner cells only** — those contain no partner-effect information, so
  nothing about the predicted quantity leaks into the baseline — and each model predicts
  the held-out **same-partner** cells. This asks exactly the design question: *given a
  new stimulus of known compatibility, does knowing its advantage predict how much more
  willing the model is to enter against a copy of itself?* It separates the four truths
  cleanly, as the table shows.
* **MODEL 0**, no partner effect, as the floor. Under `dose_null` MODEL 0 wins, which is
  correct and is the reason it is in the race at all.

### The verdict rule (fixed in advance)

The leave-one-stimulus-out winner decides, with MODEL 0 included. A margin under
`LOSO_TIE_NATS = 2.0` nats is reported as a **tie**, not a result. A verdict of MODEL B
additionally requires one-sided permutation p < 0.05 on `g1` **and** the likelihood
moving the right way. **A positive same-model shift `g0` never counts toward MODEL B on
its own**, because MODEL A predicts one too. Under `dose_b` the fitted intercepts are
`g0[gpt] = −0.0045`, `g0[claude] = −0.0065` — essentially zero — while the slope is
+0.2422; under `dose_a_logit` the intercepts carry the whole effect and the slope does
not survive. The two cases are not confusable under this rule.

### Robustness — and one honest limitation

`FROZEN_PARAMS` section 14 requires the slope with all stimuli **and** excluding
`a_chev_ud`, plus per-actor results. All are computed. The exclusion is severe:

| truth | true g1 excl. `a_chev_ud` | recovered | p₁ | verdict |
| --- | --- | --- | --- | --- |
| `dose_b` | +0.2319 | +0.1229 [−0.077, +0.325] | 0.1195 | no partner effect survives |
| `dose_a_logit` | +0.0779 | −0.0041 [−0.198, +0.195] | 0.5104 | tie |
| `dose_a_rd` | +0.0491 | −0.0279 [−0.217, +0.164] | 0.6072 | tie |
| `dose_null` | 0.0000 | −0.0694 [−0.274, +0.141] | 0.7427 | tie |

**This is a power finding and it should be read as one.** `a_chev_ud` supplies the
largest advantage for both actors, and removing it collapses the x-range from
[−0.13, +0.72] to [−0.13, +0.42] while also removing the highest-leverage points. Under a
*true* MODEL B the sensitivity analysis then fails to detect the slope it is looking
for — the recovered value drops from +0.1229 against a true +0.2319, with a CI that
covers zero. The exclusion is therefore a genuine sensitivity check on **leverage**, and
a null result there is **not** evidence against MODEL B; it is evidence that seven
stimuli spanning a narrower range cannot resolve a slope of this size at this
allocation. The frozen spec's instruction to report both is exactly right, and the
right reading is "the primary result depends on the large-advantage stimulus", not
"the primary result is fragile".

The per-actor split is similarly power-limited. Under `dose_b`, GPT alone gives
`g1 = +0.3102 [+0.110, +0.511]`, p₁ = 0.0031 — a clearly detected slope — but MODEL 0
still wins its leave-one-stimulus-out comparison (318.3 against A 321.1 and B 321.8), so
its verdict is the conservative "no partner effect survives out of sample". Claude alone
gives `g1 = +0.1905`, p₁ = 0.0327, and does reach a MODEL B verdict (LOSO 326.8 / 328.4 /
**324.8**). Half the trials is not enough for the out-of-sample criterion to see a
half-sized effect; pooling is the primary for a reason, and the per-actor numbers are
printed so the reader can see the disagreement rather than being told there is none.

Every stimulus's partner effect is printed with the **raw integer cells**, including
zero and negative cells, both flagged in the log (`ZERO-CELL`, `NEG`). A rate never
appears without the `k/n` it came from. Under `dose_b`, **7 of the 16** per-stimulus
effects are negative — `claude/c_open_cplx`, `claude/proto`, `claude/rot`,
`gpt/b_spiral_cw`, `gpt/d_texture`, `gpt/mirror`, `gpt/s_arrow` — and all seven are
shown with their counts rather than being absorbed into the fitted line. No cell hit
`k = 0` at this allocation, so the `ZERO-CELL` flag is present and exercised but did not
fire; the negative cells, which `FROZEN_PARAMS` gives the *largest* n precisely because
they carry the discrimination, all did.

---

## 5. Errors-in-variables versus plug-in

Four estimators of the same slope, always reported together.

1. **Plug-in** — advantage fixed at its point estimate, bootstrap over Stage C trials.
   **Attenuated**: biased toward zero by regression dilution. The analysis prints that
   sentence, in those words, at every plug-in slope.
2. **Plug-in + Stage A bootstrap** — also resamples the confirmation counts. It
   **widens** the interval and does **not** undo the attenuation. Propagating
   uncertainty and correcting bias are different operations and neither substitutes for
   the other.
3. **Regression calibration** — `g1 / λ`, method of moments.
4. **Full joint Bayesian EIV** — the fix.

### The EIV model

```
Stage A   k[m,s] ~ Binomial(n[m,s], pi[m,s]),   pi ~ Uniform(0,1)
latent    own[m,s] = pi² + (1-pi)²
          cross[s] = pi_g·pi_c + (1-pi_g)(1-pi_c)
          adv[m,s] = own[m,s] - cross[s]                     deterministic
Stage C   k ~ Binomial(n, sigmoid(mu[a,s] + bS[a]·(S-Sbar) + SAME·(g0[a] + g1·adv[a,s])))
priors    mu ~ N(0, 2.5),  bS ~ N(0, 1),  g0 ~ N(0, 1),  g1 ~ N(0, 2)
```

Advantage is **latent**, so `g1` is not diluted. Parameterising by the identity-level
marginals is not a convenience: it makes the structural constraint
`|cross − ½| = √((own_g − ½)(own_c − ½))` hold automatically rather than being imposed,
and it makes the measurement errors in GPT's and Claude's advantage on the *same*
stimulus correlated through the shared `cross` term — which they genuinely are, and
which no per-actor correction can see.

**pymc is not importable in this environment** (numpy ABI clash:
`module 'numpy' has no attribute '_core'`), and the primary analysis must not depend on
an optional package, so the sampler is written out. It is two **independence**
Metropolis–Hastings blocks:

* `pi | theta` — proposed one coordinate at a time from `Beta(1+k, 1+n−k)`, *exactly* the
  Stage A conditional posterior. The Stage A likelihood and the uniform prior cancel
  identically against the proposal, so the acceptance ratio is just the Stage C
  likelihood ratio.
* `theta | pi` — proposed from the Laplace approximation at the current advantage;
  penalised IRLS gives the exact MAP and its Hessian.

An earlier **random-walk** version was written, run, and discarded: it gave min bulk ESS
of 5 at 400 draws and GATE E5 refused to report it. That is the gate working. The fix
was a better kernel, not a lower bar. The independence sampler achieves acceptance
0.82–0.85 (theta) and 0.94–0.98 (latent `pi`), max split R-hat **1.0028–1.0035**, and min
bulk ESS **2 572–3 444** across the four truths — recorded in
`dose_eiv_status_<truth>.json`.

Gates, run before any sampling and enforced after: E1 params < cells, E2 outcome design
matrix full rank, E3 at least three distinct advantage values and both partner arms per
actor, E4 confirmation counts present for **both** models on every stimulus (`cross[s]`
needs both marginals, so one missing kills the advantage for both actors), E5 post-fit
R-hat < 1.01, bulk ESS > 400, acceptance ≥ 0.10; plus the prior-domination check —
posterior 90 % width / prior 90 % width came out **0.24–0.26**, comfortably data-driven.

### Recovery of the logit-scale `g1`

| truth | true logit `g1` | **EIV posterior median** | 95 % CI | P(g1 > 0) |
| --- | --- | --- | --- | --- |
| `dose_b` | **+1.40** | **+1.4885** | [+0.490, +2.439] | 0.9993 |
| `dose_a_logit` | **0.00** | **+0.1099** | [−0.906, +1.035] | 0.5885 |
| `dose_a_rd` | 0.00 (not a logit-scale truth) | +0.0373 | [−1.024, +0.998] | 0.5227 |
| `dose_null` | **0.00** | **+0.2940** | [−0.686, +1.207] | 0.7232 |

The EIV recovers the MODEL B truth (+1.49 against +1.40) and stays at zero under both
MODEL A truths and the null, with P(g1 > 0) at 0.52–0.72 — i.e. no evidence either way,
which is the correct answer.

### The comparison, honestly

Measurement-error reliability, pooled scope, all stimuli:

```
lambda = (Var(adv_hat) - mean SE²) / Var(adv_hat) = 0.9855
Var(adv_hat) = 0.0669,  mean SE(adv) = 0.0312
```

so the attenuation at `FROZEN_PARAMS.CONFIRM_N` is **1.5 %**, and `1/λ = 1.015`.
Excluding `a_chev_ud` the range collapses and reliability falls to **λ = 0.9739**
(2.6 % attenuation); per-actor it runs 0.967–0.989. Like-for-like, same link, the only
difference being whether advantage is latent or plugged in:

| truth | logit `g1` plug-in | logit `g1` EIV | ratio |
| --- | --- | --- | --- |
| `dose_b` | +1.5301 | +1.4885 | 0.973 |
| `dose_a_logit` | +0.0938 | +0.1099 | (not reported — both within noise of zero) |
| `dose_a_rd` | +0.0158 | +0.0373 | (not reported — both within noise of zero) |
| `dose_null` | +0.3169 | +0.2940 | (not reported — both within noise of zero) |

**Read the size, not the sign of the difference.** A 1.5 % correction is an order of
magnitude below `g1`'s own sampling noise — the EIV posterior is +0.49 to +2.44 at 95 %
under `dose_b` — so plug-in and EIV land on either side of one another by Monte Carlo
chance. The attenuation is real and its **direction is not in doubt**; it is simply
small *because the confirmation screen is large*. That is a statement about
`CONFIRM_N`, not a licence to drop the EIV. At the provisional n = 60 the same
calculation gives a correction several times bigger, and the reliability is the quantity
that says so.

The analysis suppresses the ratio when the plug-in estimate is smaller than the EIV
posterior's own 90 % width, rather than printing a ratio of two near-zero numbers as if
it were a correction — a raw ratio of 2.36 appeared under `dose_a_rd` before that guard
was added, and it means nothing.

Risk-difference-scale push-through of the EIV posterior (each draw's fitted
probabilities regressed on **that draw's own** latent advantage) gives **+0.2317
[+0.0906, +0.3839]** under `dose_b` against a plug-in +0.2422 and a truth of +0.2418.
These two use different links and their difference is **not** an attenuation correction;
the analysis says so where it prints them.

### The plain-OLS comparison the spec asks for

Plain OLS on the 16 aggregated per-stimulus points is computed and printed as a
descriptive figure-companion, **never as the analysis**: `dose_b` +0.3024,
`dose_a_logit` +0.1019, `dose_a_rd` +0.0981, `dose_null` +0.0909. It weights a 32-trial
stimulus the same as a 160-trial one, so it targets the *unweighted* estimand (true
+0.2482 for `dose_b`) and is not size-comparable with the weighted slope; its sampling
variance is also far larger, which is visible in `dose_null`, where it reports +0.0909
against a truth of exactly zero — more than twice the trial-level estimate's error.
Attenuation applies to it as to every plug-in estimate.

---

## 5b. Re-validation on the gradient the study actually has

The confirmation screen came back with a **substantially flatter and re-ordered**
gradient than the provisional n = 60 battery:

| | provisional GPT / Claude | confirmed GPT / Claude |
| --- | --- | --- |
| `a_chev_ud` | +0.650 / +0.678 | **+0.294 / +0.319** |
| `c_open_cplx` | +0.367 / −0.106 | **+0.489 / −0.003** |
| `d_texture` | +0.057 / +0.401 | **+0.048 / +0.003** |
| `b_spiral_cw` | −0.128 / +0.217 | −0.127 / +0.250 |
| `mirror` | +0.007 / +0.022 | −0.012 / +0.114 |
| `rot` | +0.073 / −0.009 | +0.070 / −0.004 |

Validating only against the provisional spread would **overstate the design's power**,
so the simulator gained `--use-confirmed`, which takes the true marginals from
`design/confirmed_compatibility.csv` by the same exact inversion and re-runs the same
ground truths on the range the study actually has. `dose_b`'s true weighted
risk-difference slope is +0.2469 on this gradient (against +0.2418 on the provisional
one); the x-range narrows from [−0.13, +0.72] to roughly [−0.13, +0.49].

Pooled, FULL sample, all stimuli:

| truth | true g1 | recovered g1 | 95 % CI | p₁ | LRT p | LOSO 0 / A / B | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `dose_b` | **+0.2469** | **+0.3302** | [+0.113, +0.547] | **0.0014** | 0.0026 | 705.6 / 710.0 / **703.4** | **MODEL B** |
| `dose_a_logit` | **+0.0755** | +0.1323 | [−0.072, +0.347] | 0.1222 | 0.5795 | 631.1 / **606.0** / 608.4 | **MODEL A** |
| `dose_null` | **0.0000** | +0.0553 | [−0.163, +0.276] | 0.3213 | 0.5441 | **724.1** / 727.0 / 730.5 | no partner effect |

**The separation holds on the real gradient**, with two things worth recording.

* **The `a_chev_ud` exclusion is much better behaved here.** On the confirmed gradient
  `c_open_cplx` (GPT, +0.489) supplies the largest advantage, not `a_chev_ud` (+0.294),
  so removing `a_chev_ud` barely changes the true slope (+0.2469 → +0.2462) and the
  recovered slope survives: +0.2472 [+0.025, +0.486], p₁ = 0.0223. `FROZEN_PARAMS`
  section 14's concern that `a_chev_ud` "will dominate the slope" was written against
  the provisional values and **the confirmation screen has largely defused it**. The
  sensitivity analysis is still reported, and is now much less likely to be the
  headline.
* **Attenuation is larger here**, because the collapsed range shrinks the signal
  variance without shrinking the measurement error: λ falls from 0.9855 to **0.9663**,
  i.e. 3.4 % rather than 1.5 %. Still small, still an order of magnitude under the
  sampling noise, but moving in the direction the reliability formula predicts.

EIV on the confirmed gradient, all three sampled cleanly (max split R-hat 1.0017–1.0021,
min bulk ESS 3 312–3 618):

| truth | true logit g1 | EIV posterior median | 95 % CI | P(g1 > 0) |
| --- | --- | --- | --- | --- |
| `dose_b` | +1.40 | **+1.8228** | [+0.602, +3.094] | 0.9973 |
| `dose_a_logit` | 0.00 | +0.3376 | [−0.888, +1.603] | 0.6993 |
| `dose_null` | 0.00 | +0.3374 | [−0.880, +1.584] | 0.7053 |

Like-for-like on the logit scale under `dose_b`: plug-in +1.9885 → EIV +1.8228, ratio
0.917 against a predicted 1/λ = 1.035 — again, a 3 % correction inside a posterior that
runs from +0.60 to +3.09, so the two land either side of one another by chance. The
risk-difference push-through is +0.2985 [+0.1152, +0.4890] against a plug-in +0.3302 and
a truth of +0.2469.

Reproduce with:

```
python3 simulate_study2_data.py --truth <dose_b|dose_a_logit|dose_null> --use-confirmed \
        --out ../data/simc_<truth>.csv
python3 analyze_dose_response.py --data ../data/simc_<truth>.csv \
        --confirm ../data/simc_<truth>_confirmA.csv --tag confirmed_<truth>
```

---

## 6. Permutation inference

The **partner** label is permuted within each (actor × stimulus × safe payoff) stratum —
the finest cell the same/different contrast crosses over. The shuffle preserves exactly
and by construction: the payoff response, every stimulus's own baseline attempt
propensity, every stimulus's advantage, and every cell size. Draws are exact conditional
hypergeometrics on the integer counts (`analyze_study2._hyper`), reducing to Fisher's
exact test for a single 2×2 stratum, with ties counted via the `−1e-12` tolerance.

The permuted sharp null ("the partner label had no effect at all") is stronger than
`g1 = 0`, which MODEL A also satisfies. Two arguments license it, and the algebra is
cleaner here than for the old interaction:

1. **Orthogonality.** A partner effect constant on the risk-difference scale adds the
   same amount to every stimulus's partner effect, which moves the intercept `g0` and
   leaves `g1` identically unchanged. The reference distribution is centred on zero under
   MODEL A as well as under the sharp null. **Confirmed empirically**: under `dose_a_rd`,
   with a real constant shift of +0.084 mean partner effect present, p₁ = 0.2383.
2. **Conservatism.** Within-stratum variance under the permutation is that of the
   same/different-pooled cell, which a real main effect inflates, so the reference
   distribution is slightly too wide and p slightly too large.

Argument 1 is exact on the risk-difference scale and only approximate on the logit
scale — the scale trap again — which is why the baseline-artefact diagnostic is printed
beside the permutation p rather than after it.

Because the design matrix and every cell n are invariant under this permutation, `g1` is
a fixed linear functional of the cell rates, so a replicate costs one dot product and
20 000 exact replicates cost less than a single IRLS fit. Permutation null SD for the
pooled slope: **0.0752**.

---

## 7. The figure

`figure_dose_response.py` plots x = measured same-model coordination advantage,
y = same-minus-different partner effect, one point per (actor × stimulus), with x = 0 and
y = 0 reference lines and the fitted line plus a pointwise 95 % bootstrap band.

`plt.style.use("academic")` is applied **once at import**. GPT-5.5 is a filled circle on
a solid line, Claude Opus 5 an open square on a dashed line — marker, linetype and tone
are three redundant cues, so the figure survives greyscale. Error bars are thin capped
lines in **both** directions: vertical are the 95 % bootstrap interval on the partner
effect, horizontal are 1.96 × the advantage's own confirmation-screen sampling error —
drawn precisely because the x variable is measured, which is the visible reason the
analysis carries an EIV model. The band is the single filled region and is a regression
interval, drawn in light grey with thin dotted boundaries; one band is drawn rather than
one per actor, since the slope is shared and the intercepts differ by far less than the
band is wide. There is no title or subtitle inside the axes; n, the slope, its interval,
the permutation p and the verdict go in the `_caption.txt` sidecar. PDF and PNG are both
written at 300 dpi, 5.5 × 3.2 in.

The four rendered figures make the validation visible at a glance: `dose_b` shows a
clear rising line, `dose_a_logit` and `dose_a_rd` show a nearly flat line sitting above
zero (a constant shift), and `dose_null` shows a flat line on zero.

---

## 8. Bugs and issues this validation exposed

1. **The EIV's first sampler did not mix.** A blocked adaptive random walk gave min bulk
   ESS = 5 and max R-hat = 1.35 at 400 draws. GATE E5 refused to report it. Replaced with
   two independence-MH blocks (exact Beta conditional for the latent, Laplace proposal for
   the outcome block), which give ESS ≈ the number of draws.
2. **The confirmation gate fired on noise.** The frozen gate checks that the sign of the
   critical tiers replicates, but the `zero_floor` tier sits at advantage ≈ 0 *by design*,
   so its sign is noise: the gate flagged `mirror` for "flipping" from +0.007 to −0.0004.
   The check is now applied only where the provisional **and** confirmed values are both
   more than 2 SE from zero, and the unresolved cells are listed explicitly instead of
   being silently skipped.
3. **The naive-OLS caption was wrong.** It claimed the aggregated-points OLS was "the most
   attenuated estimate", but it came out *larger* than the weighted slope (+0.3024 vs
   +0.2422). The two target different estimands (unweighted vs allocation-weighted); the
   text now says that instead of a false comparison.
4. **The EIV/plug-in ratio was meaningless at small slopes.** `dose_a_rd` produced a ratio
   of 2.356 from +0.0158 → +0.0373, both indistinguishable from zero. The ratio is now
   suppressed unless the plug-in estimate exceeds the EIV posterior's 90 % width.
5. **A verdict of "MODEL A" was being returned for the pure null.** MODEL 0 was in the
   likelihood table but not in the decision rule, so a null dataset in which nothing
   predicted anything was reported as supporting the coarse identity heuristic. MODEL 0
   now competes, and a leave-one-stimulus-out margin under 2 nats is reported as a tie.

## 9. Known limitations, stated plainly

* **The `a_chev_ud` exclusion is underpowered on the PROVISIONAL gradient** — under a
  true MODEL B it recovers +0.1229 against a true +0.2319 with p₁ = 0.12. On the
  **confirmed** gradient the same exclusion recovers +0.2472 with p₁ = 0.0223, because
  `c_open_cplx` has taken over as the highest-leverage point. Either way, read a null
  there as a leverage statement, not as evidence against MODEL B.
* **Per-actor analyses are underpowered for the out-of-sample criterion.** Under a true
  MODEL B, GPT alone reaches p₁ = 0.0031 on the slope but MODEL 0 still wins its LOSO
  comparison.
* **The attenuation correction is small at `CONFIRM_N`** (1.5 %) and is not separately
  visible above sampling noise. The EIV is retained because the correction's direction is
  known and its size is a property of the confirmation screen's n, not of the design.
* **`dose_a_rd`'s true slope is +0.0382, not 0**, because a constant additive shift is not
  representable near the ceiling. The logit-scale MODEL A truth (`dose_a_logit`) is the
  cleaner test of the coarse identity heuristic.
* Everything here is simulated. It establishes that the analysis recovers what it is
  pointed at and refuses what it should refuse. It establishes nothing about the models.
