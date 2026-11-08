# Study 2 — validation of the frozen analysis

`analyze_study2.py` was written **before any Study 2 data existed**, so that it can be
frozen as the pre-registered primary analysis. A frozen analysis that has never been
run is a frozen guess, so it was validated on simulated data whose ground truth we set.

This document records: the ground truths, what the analysis recovered for each, the
schema assumptions made about the runner and how they were reconciled once the runner
landed, and the two bugs the validation itself exposed.

Everything here is reproducible:

```
python3 simulate_study2_data.py --truth interaction          --out ../data/sim_interaction.csv
python3 simulate_study2_data.py --truth main_effect          --out ../data/sim_main_effect.csv
python3 simulate_study2_data.py --truth null                 --out ../data/sim_null.csv
python3 simulate_study2_data.py --truth main_effect_low_base --out ../data/sim_main_effect_low_base.csv
python3 analyze_study2.py --data ../data/sim_<truth>.csv --tag <truth>
python3 figure_study2.py  --tag <truth> --out ../figures/study2_interaction_<truth>
```

No API calls are made by any of it.

---

## 1. The generative model and the four ground truths

Simulated trials follow the same parameterisation the convergent Bayesian model fits,
so the recovery target is unambiguous:

```
logit p(ATTEMPT) = alpha[actor] + alpha_shift + bS*(S - Sbar) + u[pair]
                   + delta*is_high + gamma*is_same + theta*is_high*is_same
```

Structure copied from Study 1: the five approved matched pairs (3 GPT, 2 Claude), the
`{3,5,7,9}` payoff grid, n = 30 per cell, exact AB/BA balance, ~5 % of first attempts
unparseable and superseded, and a residual ~8 % of those lost on the retry as well —
so the validity filters are exercised, not assumed. 2 526 rows written, 2 385 valid,
15 trials lost, per dataset.

| id | name | delta | gamma | theta | alpha_shift | what it is |
|----|------|-------|-------|-------|-------------|------------|
| a | `interaction` | +0.30 | +0.25 | **+1.40** | 0 | a true Stimulus × Partner interaction |
| b | `main_effect` | +1.40 | +0.80 | **0** | 0 | a real stimulus effect and a real Partner main effect, no interaction |
| c | `null` | 0 | 0 | **0** | 0 | payoff response only |
| d | `main_effect_low_base` | +1.40 | +0.80 | **0** | −2.20 | (b) again, at a low base rate — the adversarial case, see §4 |

**The primary statistic is a risk difference, the generative truth is on the logit
scale, and these are not the same scale.** The simulator therefore computes the exact
population risk-difference contrasts implied by the generating probabilities (cell n is
equal, so the pooled cell rate is the unweighted mean of the cell probabilities) and
writes them to `sim_<truth>_truth.json`. Those, not `theta`, are what the frequentist
estimate must land on:

| truth | actor | true gap(SAME) | true gap(DIFF) | **true interaction (RD)** | true partner main (RD) |
|---|---|---|---|---|---|
| a | GPT-5.5 | +0.2381 | +0.0528 | **+0.1853** | +0.1368 |
| a | Claude Opus 5 | +0.2241 | +0.0515 | **+0.1726** | +0.1294 |
| b | GPT-5.5 | +0.1696 | +0.2205 | **−0.0508** | +0.1098 |
| b | Claude Opus 5 | +0.1569 | +0.2106 | **−0.0538** | +0.1037 |
| c | both | 0 | 0 | **0** | 0 |
| d | GPT-5.5 | +0.2516 | +0.2301 | **+0.0215** | +0.1348 |
| d | Claude Opus 5 | +0.2521 | +0.2368 | **+0.0153** | +0.1369 |

Note that **theta = 0 does not imply a zero risk-difference interaction**. A partner
main effect that is additive in log-odds is not additive in probabilities, so it induces
a small interaction on the RD scale whose *sign depends on where the base rate sits*:
negative above p = 0.5 (case b), positive below it (case d). Case (d) exists precisely
to measure that artefact when it points *towards* the hypothesis.

---

## 2. What the analysis recovered — single datasets, HOLDOUT (the pre-registered primary sample)

Pooled over pairs and payoffs. `p1` = one-sided permutation p (the pre-registered
primary for the interaction); `sens` = the pre-specified sensitivity permutation that
shuffles the stimulus label instead of the partner label; CI = 95 % trial bootstrap.

### (a) `interaction` — RECOVERED

| actor | interaction (true) | estimate | 95 % CI | **p1** | p2 | sens p1 |
|---|---|---|---|---|---|---|
| GPT-5.5 | +0.1853 | **+0.1719** | [+0.0614, +0.2778] | **0.0023** | 0.0037 | 0.0029 |
| Claude Opus 5 | +0.1726 | **+0.1864** | [+0.0603, +0.3124] | **0.0053** | 0.0089 | 0.0027 |

Simple gaps recovered correctly too — GPT +0.2036 under SAME vs +0.0317 under
DIFFERENT; Claude +0.1597 vs −0.0267. `select` (+0.1329 / +0.1607) and `full`
(+0.1536 / +0.1744) agree, so the effect is not a holdout artefact.

### (b) `main_effect` — CORRECTLY NOT AN INTERACTION

| actor | interaction (true) | estimate | 95 % CI | **p1** | p2 | partner main (true) | partner main est. | main p2 |
|---|---|---|---|---|---|---|---|---|
| GPT-5.5 | −0.0508 | −0.1246 | [−0.2250, −0.0193] | **0.9935** | 0.0169 | +0.1098 | +0.0545 | 0.0511 |
| Claude Opus 5 | −0.0538 | −0.0725 | [−0.1905, +0.0383] | **0.9091** | 0.2079 | +0.1037 | +0.0506 | 0.1228 |

The pre-registered one-sided interaction test is nowhere near significance (p1 = 0.99,
0.91). The Partner main effect is recovered directionally but is **underpowered on the
holdout half** (p2 = 0.051 / 0.123); on the full sample it is unambiguous (+0.0762,
p2 = 0.0001; +0.0624, p2 = 0.0080). This is a genuine, reportable cost of the
select/holdout split for the secondary test — see §6.

Note the GPT two-sided interaction p of 0.0169: the estimate is significantly
**negative**, in the direction *opposite* the hypothesis. That is not a false positive
for the primary test (which is one-sided and directional), and it is partly real —
the true RD interaction under (b) is −0.05 by the scale argument above.

### (c) `null` — CORRECTLY NULL

| actor | interaction est. | 95 % CI | **p1** | p2 | partner main est. | main p2 |
|---|---|---|---|---|---|---|
| GPT-5.5 | +0.0069 | [−0.1090, +0.1230] | 0.4678 | 0.8778 | −0.0337 | 0.3105 |
| Claude Opus 5 | +0.0526 | [−0.0891, +0.1943] | 0.2497 | 0.4805 | −0.0211 | 0.5960 |

### (d) `main_effect_low_base` — CORRECTLY NOT AN INTERACTION, despite the artefact pointing the right way

| actor | interaction (true) | estimate | 95 % CI | **p1** | partner main est. | main p2 |
|---|---|---|---|---|---|---|
| GPT-5.5 | +0.0215 | −0.1042 | [−0.2204, +0.0068] | 0.9664 | +0.1445 | 0.0001 |
| Claude Opus 5 | +0.0153 | −0.0366 | [−0.1782, +0.1056] | 0.7315 | +0.1398 | 0.0003 |

---

## 3. Repeated-sampling check — 40 independent datasets per truth

A single dataset shows the analysis *can* get the right answer once. The operating
characteristics need replication. 40 independently seeded datasets per truth, HOLDOUT,
pooled, 5 000 permutations each:

| truth | actor | mean interaction | sd | **one-sided p < .05** | two-sided p < .05 | mean partner main | main p2 < .05 |
|---|---|---|---|---|---|---|---|
| a | GPT | +0.1915 | 0.0633 | **36/40 (0.90)** | 35/40 | +0.1373 | 40/40 |
| a | Claude | +0.1406 | 0.0780 | **24/40 (0.60)** | 20/40 | +0.1354 | 38/40 |
| b | GPT | −0.0512 | 0.0545 | **1/40 (0.025)** | 10/40 | +0.1068 | 40/40 |
| b | Claude | −0.0886 | 0.0682 | **0/40 (0.000)** | 13/40 | +0.1074 | 35/40 |
| c | GPT | +0.0026 | 0.0672 | **4/40 (0.100)** | 2/40 | −0.0002 | 0/40 |
| c | Claude | −0.0307 | 0.0875 | **1/40 (0.025)** | 3/40 | +0.0087 | 3/40 |
| d | GPT | +0.0207 | 0.0590 | **2/40 (0.050)** | 2/40 | +0.1375 | 39/40 |
| d | Claude | −0.0036 | 0.0671 | **2/40 (0.050)** | 1/40 | +0.1378 | 39/40 |

**False-positive rate on the primary test, pooled over every no-interaction cell
(truths b, c, d × 2 actors × 40 datasets = 240 tests): 10/240 = 0.042.** At the nominal
0.05. The individual cells range 0.000–0.100, but 40 replicates give a standard error
of 0.034 per cell, so none of those departs meaningfully from nominal.

**Power on the primary test at n = 30/cell on the HOLDOUT half: 0.90 for GPT (3 pairs),
0.60 for Claude (2 pairs).** Claude is underpowered by design — it contributes one
fewer matched pair. On the full sample both are near ceiling. This is a real planning
input, not a defect of the analysis, and it is the number the power analysis should be
reconciled against.

Mean estimates are unbiased: with dropout switched off (`--clean`), the full-sample
means over 40 replicates are GPT +0.1878 (true +0.1853) and Claude +0.1791 (true
+0.1726), MC standard errors 0.0061 and 0.0081.

---

## 4. Does it discriminate (a) from (b)? Yes — and here is the margin

This was the stated bar. It is cleared on both the point estimate and the test:

- estimates: (a) +0.17/+0.19 vs (b) −0.12/−0.07 — opposite signs, non-overlapping CIs;
- primary test: (a) p1 = 0.0023/0.0053 vs (b) p1 = 0.9935/0.9091;
- across 40 replicates: (a) rejects 36/40 and 24/40, (b) rejects 1/40 and 0/40;
- the Bayesian model separates them on the parameter that *defines* the difference —
  see §5 — with `gamma` (the main effect) large and `theta` (the interaction) at zero
  under (b), and the reverse under (a).

**Case (d) is the harder discrimination and it also passes.** Under (d) the logit→RD
scale artefact pushes the true risk-difference interaction to **+0.02 in the predicted
direction** while `theta` is exactly zero. The analysis does not reject (2/40 at each
actor, exactly nominal) because the artefact is ~0.35 of the sampling SD at this n.
That is a quantitative limit, not a guarantee: **at a much larger n, or a much larger
partner main effect, a risk-difference interaction test would eventually declare a
scale artefact significant.** This is the concrete reason the design carries a
convergent Bayesian model on the log-odds scale rather than a decorative one, and it is
why the two should be read together. If the real data ever show a significant RD
interaction with `theta`'s posterior sitting on zero and `gamma` large, the scale
artefact is the explanation to reach for first.

---

## 5. Convergent Bayesian model

Trial-level hierarchical logistic with an explicit `theta[actor]` interaction, in the
style of Study 1's *replacement* pair-constrained model. Partner is coded `is_same`, not
`is_diff`, so every parameter the hypothesis predicts points positive and there is no
sign flip between the Bayesian and frequentist reports.

### Identifiability gate

The first Study 1 Bayesian model was overparameterised — Claude's 4 stimuli exactly
saturated 4 parameters, one scale unidentifiable — and was replaced rather than
reported. This model is gated *before* sampling and refuses rather than printing a
number from an unidentified posterior. On all four datasets:

```
distinct data cells (actor x pair x level x partner x payoff) : 80
free parameters                                               : 22
  = 5 x 2 actors (alpha,bS,delta,gamma,theta) + 2 x (1 + 5 pairs)
GATE 1  params < cells                                    : PASS  (22 < 80)
GATE 2  fixed-effects cell design matrix rank 10 of 10    : PASS
GATE 3  Claude Opus 5  2x2 fully crossed, 4/4 cells       : PASS  (2 pairs)
GATE 3  GPT-5.5        2x2 fully crossed, 4/4 cells       : PASS  (3 pairs)
GATE 4  post-fit div=0, max R-hat < 1.01, min ESS > 400   : PASS  (see below)
GATE 5  prior->posterior 90% width ratio < 0.9            : PASS  (0.32-0.45)
```

GATE 2 is a **rank** check on the cell-level fixed-effects design matrix, not just a
parameter count, so a structurally collinear specification is caught rather than
counted. GATE 3 is per actor: an actor missing any of its four cells has no identified
`theta` and is refused individually. GATE 5 is the empirical check — a posterior as
wide as its prior is stamped PRIOR-DOMINATED / NOT IDENTIFIED BY THE DATA; observed
width ratios were 0.32–0.45, i.e. the data are doing the work.

GATE 4 is enforced with **`target_accept` escalation, not by weakening the gate**. Two
hierarchical scales over 5 pairs make a tight funnel and the default 0.95 produced 2–9
divergences on every dataset. The script retries at 0.99 and then 0.995 and stops at the
first clean fit — a sampler setting, not a model or prior change — and still refuses if
0.995 diverges. Observed: 0.99 sufficed for (a), (b), (c); (d) needed 0.995.

### Recovered posteriors (HOLDOUT, `theta` = log-odds interaction)

| truth | true theta | actor | median | 90 % CI | P(θ > 0) | width ratio |
|---|---|---|---|---|---|---|
| a | **+1.40** | GPT-5.5 | **+1.040** | [+0.491, +1.595] | 0.9985 | 0.34 |
| a | **+1.40** | Claude Opus 5 | **+1.166** | [+0.461, +1.877] | 0.9981 | 0.42 |
| b | **0** | GPT-5.5 | −0.551 | [−1.143, +0.029] | 0.0617 | 0.36 |
| b | **0** | Claude Opus 5 | −0.229 | [−0.977, +0.533] | 0.3204 | 0.45 |
| c | **0** | GPT-5.5 | −0.004 | [−0.538, +0.517] | 0.4955 | 0.32 |
| c | **0** | Claude Opus 5 | +0.194 | [−0.430, +0.835] | 0.6956 | 0.38 |
| d | **0** | GPT-5.5 | −0.532 | [−1.050, +0.015] | 0.0545 | 0.32 |
| d | **0** | Claude Opus 5 | −0.067 | [−0.686, +0.556] | 0.4299 | 0.37 |

Every no-interaction case has a 90 % interval covering zero and P(θ > 0) far from 1;
the interaction case has P(θ > 0) ≈ 0.998 for both actors. The nuisance parameters are
recovered correctly too — under (b) and (d), `gamma` (the SAME main effect, true +0.80)
comes back at +0.610/+0.527 and +1.075/+0.777 with P(>0) ≥ 0.96, and `delta` (true
+1.40) at +1.370/+1.110 and +1.546/+1.206. **The model attributes the (b) and (d)
effects to the main effect and not to the interaction, which is the whole point of
including it.**

The alpha/pair-intercept ridge documented for Study 1's B2 is present here too and is
reported, not gated: refitting with `alpha` fixed at 0 moves `theta` by ≤ 0.09
(e.g. (a) GPT +1.040 → +0.989, Claude +1.166 → +1.082), confirming the ridge does not
contaminate a within-pair within-actor contrast.

---

## 6. Design and inference choices that the validation confirmed or qualified

**Which label is permuted.** PARTNER, within each (pair × stimulus level × payoff)
stratum, for both the interaction and the main effect. The full argument is in the
module docstring of `analyze_study2.py`; the short version is that the interaction
contrast is *orthogonal to an additive partner main effect* (so the test is unbiased
under the weaker null being tested, not just the sharp null being permuted) and that
pooling over the small partner effect to build the reference distribution costs far
less variance than pooling over the large stimulus effect would. Permuting the stimulus
label is the mirror image; it is computed and reported as a pre-specified sensitivity
check and agreed with the primary on every dataset above (e.g. (a) GPT 0.0029 vs 0.0023).

**Raw counts, never rounded rates.** Study 1's earlier bug reported p = 0.0485 where the
exact hypergeometric was p = 0.1334, because the observed statistic came from a
`round(k/n, 4)` column and every permutation replicate tying with it was dropped from
the tail. Everything here is computed in integers; the permutation reference is drawn
as exact conditional hypergeometrics of those integers, which for a single 2×2 stratum
*is* Fisher's exact test; and every `>=` carries a `-1e-12` tolerance so ties count.

**Bootstrap CIs.** The headline CI resamples trials within cell (exactly Binomial(n,
k/n)) and is conditional on this stimulus set. A pair-clustered CI is also printed as
the generalisation interval, and is labelled as extremely coarse — with 2–3 pairs per
actor it has very few distinct resamples and should not be read as a normal CI.

**Select/holdout.** Study 1's `assign_halves` is carried over verbatim in logic and
HOLDOUT is the pre-registered primary sample. The honest qualification, printed by the
script and confirmed by the validation: the matched pairs were selected on **Study 1**
data, so Study 2's own split is not correcting a within-study winner's curse, and the
partner factor was not used in any selection. What the split costs is visible in §2(b):
the secondary Partner main effect is underpowered on half the data (p2 = 0.051 / 0.123)
where the full sample gives 0.0001 / 0.0080. SELECT and FULL are printed alongside
HOLDOUT for exactly this reason.

**Pooled vs stratum-mean contrasts.** Under a balanced design these are identical, and
the script checks rather than assumes it. It now distinguishes two kinds of imbalance:
*designed* (the runner accepts a non-uniform per-payoff allocation from `design/*.json`,
e.g. 10/10/40/40 — harmless to validity, since the permutation strata by payoff, but it
makes the pooled estimand n-weighted across payoffs) from *ragged* (n varying **within**
a payoff level). Both values are printed for every contrast. On the simulated data the
holdout sample is mildly ragged (cell n 14–16) — dropout plus the select/holdout cut
landing on an odd cell count — and the two versions differ by ~0.005 (e.g. Claude
pooled +0.1864 vs stratum-mean +0.1818). That is the expected size of the effect; a
large gap would mean an unfinished run, and is worth checking before reading any
effect.

---

## 7. Runner schema — assumptions made, and the reconciliation

`analyze_study2.py`, `study2_schema.py` and `simulate_study2_data.py` were written
before `study2_betting.py` existed. The runner landed **during** this validation and
every assumption was checked against it.

### Confirmed exactly as assumed

| assumption | status |
|---|---|
| `COLS = psc_common.COLS + extras`, psc_common's 30 columns unchanged and in order | CONFIRMED |
| `stimulus_level` ∈ {`high`, `low`} | CONFIRMED |
| `partner_condition` ∈ {`same`, `different`} | CONFIRMED |
| `partner_model_named` = display name of (actor if same else other actor) | CONFIRMED |
| `included_in_analysis` = `(not superseded_by_retry) and valid_response` | CONFIRMED |
| `run_id` / `variant` emitted with Study 1's AB/BA convention | CONFIRMED |
| payoff grid defaults to `{3,5,7,9}`, n = 30 per cell | CONFIRMED |

`study2_schema.assert_matches_psc_common()` verifies the copied column list against the
real `psc_common.py` by **parsing it with `ast`** rather than importing it (importing
would pull in dotenv, the API clients and a prompt-hash assertion the analysis does not
need). It reports `PSC_COLS verified identical to psc_common.COLS (30 columns)` on
every run above.

### Assumptions that were WRONG and are now corrected

1. **Output file stem.** Assumed `study2_<ts>.csv`; the runner writes
   `study2C_<ts>.csv` per invocation (it is resumable) plus a
   `study2C_MERGED_<ts>.csv` when several parts contribute. `resolve_data()` now
   prefers the newest MERGED, accepts a single bare part, and **refuses** when several
   unmerged parts exist with no merge — concatenating them would double-count the cells
   an interrupted run left partially complete.
2. **Pairs table path.** Assumed `pairs/matched_pairs.csv`; the runner reads
   `pairs/study2_candidate_pairs.csv`. The analysis now tries that first and falls back
   to `matched_pairs.csv`. This path is a **fallback only** — the runner emits `pair_id`
   and `stimulus_level` directly, and the fallback was verified to produce
   *bit-identical* cell counts and contrasts to the runner-column path.
   At time of writing all 210 candidate rows are `approved=False` (approval is a human
   decision, as in Study 1), which the analysis now reports explicitly instead of
   treating the file as absent.

### One property that changes interpretation but not validity

The runner accepts a **non-uniform per-payoff allocation** from `design/*.json`. The
permutation test strata by payoff and stays exact under any allocation; only the pooled
point estimate becomes n-weighted across payoffs. `balance_report()` names which case
it is looking at and both weightings are printed. **This is the one place the analysis
and the power analysis must be reconciled before the run**: if the power analysis
prescribes, say, 10/10/40/40, the pre-registered pooled estimand is the n-weighted one.

### Extra runner columns

`partner_model_id`, `partner_condition_text`, `n_per_cell`, `cell_key`, `study` are
carried for provenance and ignored by the analysis. The simulator emits all of them, so
the simulated files are the runner's schema exactly rather than a subset of it.

---

## 8. Two bugs the validation itself caught

Both were found by deliberately corrupting a simulated file, and both are now fixed and
re-tested.

**1. The partner-label check could be fooled by a global relabelling.** The first
version verified only *structural* consistency: each arm names one model, the two arms
differ, and an actor's SAME partner is the other actor's DIFFERENT partner. A file with
`partner_condition` swapped on **every** row — the crossing that would silently invert
the primary contrast — passed all three, because a global relabelling is internally
consistent by construction. The check is now **anchored** on `actor_model_name`, the
actor's own display string on the same row: under `partner_condition="same"` the
partner named must equal it. The anchor is taken from the data, not hard-coded, so it
survives a `PSC_GPT_NAME` / `PSC_CLAUDE_NAME` override. On the corrupted file the
analysis now exits with:

```
REFUSING TO RUN: actor claude under partner_condition='same' is told its partner is
'GPT-5.5', but its own name (actor_model_name) is 'Claude Opus 5'.
```

**2. Reproducibility was broken by `hash()`.** The permutation and bootstrap RNGs were
seeded from `abs(hash((seed, actor, pair)))`. Python salts `str.__hash__` per process
(`PYTHONHASHSEED`), so a frozen analysis would have produced a *different* reference
distribution on every invocation. Replaced with a SHA-256-derived `_seed()` helper.

### Other refusal paths, tested

| corruption | result |
|---|---|
| `included_in_analysis` disagreeing with its two components on 3 rows | `REFUSING TO RUN: 3 rows where included_in_analysis != (not superseded_by_retry) and valid_response` |
| `partner_condition` crossed on every row | refuses, anchored check (above) |
| `pair_id`/`stimulus_level` columns removed | falls back to the pairs table, reports which file, produces identical numbers |
| several unmerged part files, no MERGED | refuses and names them rather than concatenating |

---

## 9. Figure

`figure_study2.py` renders the 2×2 interaction plot, one panel per actor, PNG and PDF at
300 dpi. `plt.style.use("academic")` is applied **once at import**. Series are
distinguished by **marker and linetype as well as tone** — SAME is a solid line with a
filled circle, DIFFERENT a dashed line with an open square — so the figure survives
greyscale. Error bars are thin capped lines, not translucent bands. Top and right spines
are removed, ticks point outward, there are no gridlines, and **no title or subtitle sits
inside the axes**: each panel carries only the actor's name as a plain left-aligned
panel label, and n, the CI definition, the test and the effect sizes are written to a
`_caption.txt` sidecar. The legend sits **below** the panels rather than inside one:
rendering (a) and (b) showed that no in-axes corner is reliably empty — in the
interaction case the lower right holds the DIFFERENT series' error bar, in the
main-effect case the lower left does — so an outside legend is the placement that is
correct for whatever the real result turns out to be.

Rendered on both (a) and (b) as a check that the figure *shows* the difference the
statistics found: (a) gives visibly non-parallel lines (a flat DIFFERENT series against
a rising SAME series), (b) gives converging lines offset at Low — the main-effect
signature. A reader should be able to tell the two apart without reading a p-value.

---

## 10. Bottom line

The analysis discriminates all four cases. It recovers the interaction when there is
one (36/40 and 24/40 at α = .05 on the holdout half), and it does **not** produce a
significant interaction when there is a pure Partner main effect (1/40, 0/40), a pure
null (4/40, 1/40), or a main effect whose logit→risk-difference scale artefact points
in the hypothesised direction (2/40, 2/40) — 10/240 = 0.042 overall, at nominal.

Two caveats worth carrying forward rather than burying:

1. **Claude is underpowered at n = 30 on the holdout half** (0.60 vs GPT's 0.90),
   because it contributes 2 matched pairs to GPT's 3. Reconcile with the power analysis
   before the run.
2. **The risk-difference interaction is not scale-free.** A large partner main effect at
   a base rate far from 0.5 induces a real RD interaction with `theta` exactly zero;
   at the planned n it is ~0.35 SD and harmless, at a much larger n it would not be.
   Read the frequentist RD contrast and the Bayesian log-odds `theta` together.
