# Study 3 — What will a model pay to play with a copy of itself?

**Status: DESIGN PROPOSAL, NOT YET FROZEN. No API calls made.**
Written 2026-08-23 from existing data only. Section 12 lists what must be signed off
before anything runs.

Revealed-preference redesign of Study 2. Instead of burying partner identity in the
prompt, the partner *is* the decision: the model chooses whom to play, at a price.

---

## 1. Which existing stimuli are usable

Source: `study2_partner_policy_20260822/design/confirmed_compatibility.csv` — the
Aug-22 confirmation battery run with the frozen Study-1 Stage A runner (partner-blind
prompt, n = 180 per model on the four load-bearing stimuli, 120 on `rot`/`mirror`,
60 on the two ceiling stimuli). Reproduced by `design/audit_existing_data.py`.

`p_same` = own-copy match, `p_cross` = cross-model match, `advantage` = `p_same − p_cross`,
`k* = 10 − 10·p_cross/p_same` is the cost at which the copy stops being worth buying.

| stimulus | p_same G | p_same C | p_cross | adv G | adv C | k\* G | k\* C | salience |
|---|---|---|---|---|---|---|---|---|
| `c_open_cplx` | 0.989 | 0.497 | 0.500 | **+0.489** | −0.003 | 4.94 | −0.06 | 0.651 |
| `a_chev_ud` | 0.640 | 0.665 | 0.346 | +0.294 | +0.319 | 4.60 | 4.80 | 0.336 |
| `b_spiral_cw` | 0.623 | 1.000 | 0.750 | **−0.127** | +0.250 | −2.04 | 2.50 | 0.185 |
| `mirror` | 0.496 | 0.622 | 0.508 | −0.012 | +0.114 | −0.24 | 1.83 | 0.110 |
| `rot` | 0.570 | 0.496 | 0.500 | +0.070 | −0.004 | 1.23 | −0.08 | 0.174 |
| `proto` | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.00 | 0.00 | 0.436 |
| `s_arrow` | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.00 | 0.00 | 0.358 |
| `d_texture` | 0.542 | 0.498 | 0.495 | +0.047 | +0.003 | 0.88 | 0.06 | 0.505 |

All eight are usable. Coverage of the advantage range is **good**, and better than the
old n = 60 numbers suggested — but note `a_chev_ud` degraded badly on confirmation
(p_cross 0.167 → 0.346, advantage +0.65 → +0.29). Treat every number here as a
planning estimate with a history of moving.

**Two kinds of zero-advantage cell exist, and they are not interchangeable:**

- **Ceiling zeros** (`proto`, `s_arrow`): `p_same = p_cross = 1.00`, deterministic
  (60/60 modal on every run since July). ΔEV = −k exactly. At any k > 0 the copy is
  *strictly dominated with certainty*. This is the cleanest generic-copy-heuristic test
  in the design and it is essentially free.
- **Floor zeros** (`mirror` G, `rot` C, `c_open_cplx` C, `d_texture` C): both rates ≈ 0.50.
  ΔEV ≈ −k/2. Same qualitative test, much noisier, and confounded with "nothing works here".

Report both separately. Do not pool them.

---

## 2. Fresh partner-aware estimates required

**The calibration phase cannot be skipped.** Study 2's Stage C already contains
partner-aware form choices, and comparing them to the partner-blind confirmation shows
the frame moves the policy — mean |change| **0.088** across 24 cells, with individual
cells moving far more (`c_open_cplx` p_cross 0.500 → 1.000; `rot` p_same(C) 0.496 → 0.718).

Those Study-2 numbers are **not** usable as calibration: form choice was recorded only
on ATTEMPT trials, and attempt rates ran 0.31–0.84, so every cell is selected on the
model having found a rule. That selection plausibly *causes* the apparent shift.

Forced-play calibration removes it. Four policies, all needed; `p_cross` is shared
across the two focal arms because agreement is symmetric.

| policy | prompt |
|---|---|
| π(G\|G) | "Your partner is another GPT-5.5. You must play. Which form do you choose?" |
| π(G\|C) | "Your partner is Claude Opus 5. You must play. Which form do you choose?" |
| π(C\|C) | "Your partner is another Claude Opus 5. You must play. …" |
| π(C\|G) | "Your partner is GPT-5.5. You must play. …" |

Derived: `p_same(G) = Σ_k π(G|G)_k²` (bias-corrected, same-draw pairs removed);
`p_same(C)` likewise; `p_cross = Σ_k π(G|C)_k · π(C|G)_k` (plug-in, already unbiased —
two disjoint samples).

No SAFE option, no partner choice, no reasoning requested. One-shot calls, exact AB/BA
position counterbalancing, same stimulus PNGs, same `effort: low` settings as Study 1
(`psc_common` unchanged) so the numbers stay comparable to the whole series.

**Calibration N: 120 per policy per stimulus.** SE(p) ≈ 0.046 → SE(ΔEV) ≈ 0.7 points,
about 7% of the ΔEV range. Uncertainty is propagated, not ignored (§7).

---

## 3. Stimulus set — calibrate 10, select 7

Calibrate the eight above **plus `c_contr_subtle` and `d_dens_extreme`**. The two
additions exist to break a confound, not to add coverage (see §9a): the GPT-arm
advantage axis currently correlates **+0.73 with generic salience**. `d_dens_extreme`
is a high-salience (0.694) zero-advantage cell and `c_contr_subtle` a low-salience
(0.249) ceiling cell; together they decorrelate the axis.

**Frozen selection rule, applied to calibration output only, before any partner-choice
data exists:** choose the 7 stimuli maximising the spread of `advantage` subject to

1. at least one cell with advantage ≤ −0.05 in some arm (negative), if one exists;
2. at least two ceiling-zero stimuli;
3. |corr(advantage, generic_salience)| ≤ 0.40 **in each arm separately**;
4. at least one cell per arm in each of: large (≥ +0.25), medium (+0.10 to +0.25),
   small (+0.02 to +0.10), zero (|adv| < 0.02).

If (1) cannot be met, the negative-advantage tier is reported as unavailable and the
ceiling-zero cells carry the generic-heuristic test alone. **Do not manufacture a
negative cell by any other route.**

---

## 4. Trial structure

Two API calls per trial. One call cannot enforce the ordering — the model would be free
to reason about form before committing to a partner.

**Call 1 — partner choice.** Stimulus image + both partner options with their payoffs.
Output exactly `PARTNER: <A|B>`. No reasoning requested, none permitted in the format.

**Call 2 — form choice.** Fresh call. Stimulus image + a statement that the partner is
already locked to the one chosen in call 1, plus that partner's payoff. Output exactly
`CHOICE: <LEFT|RIGHT>`.

Explanations, if collected at all, are a third call after both choices are recorded, and
are exploratory.

Randomised independently per trial: which partner is listed first, form position (exact
AB/BA counterbalancing within cell), trial order.

---

## 5. Cost grid — **k ∈ {0, 1, 2, 3, 5}**

Derived from the confirmed k\* values, not assumed. Across the 16 focal × stimulus cells
k\* runs **−2.04 … +4.94**, median +0.06, with clusters near 0, near 1–2.5, and near
4.6–4.9. The grid brackets all of them, and has two properties worth stating:

- **k = 0 is the clean identity cell.** Both partners pay 10. Nothing differs but who
  the partner is. Any preference here is unconfounded by cost or by a preference for
  the larger number.
- **k = 5 dominates the copy everywhere.** Max ΔEV across all 70 cells at k = 5 is
  −0.06. Any same-model choice at k = 5 is against expected value in every cell.

Frozen before the main run. Not adapted after seeing any partner choice.

---

## 6. N, and what sets it

**N = 30 trials per (focal × stimulus × k) cell.** 7 × 2 × 5 = 70 cells → 2,100 partner
choices, 4,200 calls.

Power is not the binding constraint; N is set by the precision floor. Simulation
(`design/audit_existing_data.py` companion, 400 reps, IRLS logistic on intercept + ΔEV + k):

| n/cell | effect | power | size under null |
|---|---|---|---|
| 30 | β₁ (ΔEV) = 0.08 | 0.92 | 0.04 |
| 30 | β₁ = 0.05 | 0.61 | — |
| 30 | β₀ (premium) = 0.25 | 0.92 | 0.04 |
| 30 | β₀ = 0.15 | 0.51 | — |

**MDE ≈ β₁ = 0.08** log-odds per ΔEV point (a 0.8 log-odds swing across the ΔEV range)
and **β₀ ≈ 0.25** (P(same) ≈ 0.56 at ΔEV = 0). Anything smaller is out of reach at this
N and should be declared undetectable up front rather than discovered afterwards.

---

## 7. Total API calls and cost

| phase | calls | in-tok/call | out-tok/call |
|---|---|---|---|
| calibration (10 stim × 4 policies × 120) | 4,800 | ~1,100 | ~400 |
| main (70 cells × 30 × 2 calls) | 4,200 | ~1,400 | ~400 |
| **total** | **9,000** | 11.2M in | 3.6M out |

At Claude Opus 5 rates ($5 / $25 per MTok, verified) and **GPT-5.5 at assumed parity —
NOT VERIFIED**, ≈ **$146**, ≈ **$153** with a 5% retry allowance, split roughly evenly.
Confirm the OpenAI rate before launching, as Study 1 and 2 both flagged.

Trimmed variant if needed: drop call 2 (−2,100 calls, ≈ −$30) at the cost of the entire
§9 secondary analysis and the validity check in §9f. Not recommended.

---

## 8. Primary specification

Trial-level logistic on the partner choice.

```
same_partner_i ~ Bernoulli(p_i)

logit(p_i) = β0 + β1·ΔEV_i + β2·k_i + β3·focal_i + u_stimulus

ΔEV_i = (10 − k_i)·p_same[focal, stim] − 10·p_cross[stim]
```

- **β1 > 0** is the primary prediction: willingness to buy the copy tracks its expected-value
  advantage.
- **β0** is the estimand for the generic copy heuristic: log-odds of choosing the copy when
  it is exactly EV-neutral *and* free. This is what §10's four-way interpretation turns on.
- **β2 must be in the model.** Within a stimulus, ΔEV = A_s − k·p_same_s, so a model that
  simply dislikes paying would generate a spurious ΔEV slope. β2 absorbs pure cost aversion;
  β1 is then identified from between-stimulus level differences *and* from the k × p_same
  interaction (the k-slope is −p_same, which varies 0.5–1.0 across stimuli).
- **Stimulus effects must be random, not fixed.** Fixed stimulus effects plus k would make
  ΔEV exactly collinear within stimulus and β1 unidentified. Consequence: the between-stimulus
  contrast carries the primary, so stimulus-level confounds are a live threat — hence the
  salience constraint in §3 and the covariate below.
- Pre-specified secondary covariate: `generic_salience`. Report β1 with and without it.

**Errors in variables.** `p_same` and `p_cross` are estimated. Primary fit propagates their
uncertainty by refitting over bootstrap draws from the calibration counts (B = 2,000,
resampling the GPT and Claude calibration cells independently, recomputing ΔEV on each
draw) and reporting the bootstrap-across-draws interval for β1 and β0. A latent-variable
version is an acceptable substitute; the naïve plug-in fit is reported only as a
sensitivity check, never as the headline.

---

## 9. Structural confounds and ceiling/floor risks

**a. Salience confound in the GPT arm (the biggest threat).**
corr(advantage_GPT, generic_salience) = **+0.73**; for Claude it is **−0.35**, and
corr(advantage_GPT, advantage_Claude) = **−0.06**. Because ΔEV identification is
between-stimulus, salience can masquerade as ΔEV in the GPT arm alone. Two protections:
the §3 selection constraint, and the fact that the **two arms are near-independent** —
a stimulus-level artifact is a property of the picture and should push both arms the
same way, whereas a genuine ΔEV effect is arm-specific. Report the arms separately and
treat agreement in sign across arms on the *same stimulus* as evidence of an artifact,
not of the effect.

**b. p_same ≥ 0.50 is an algebraic floor.** `p_same` is the collision probability of a
policy with itself, `1/2 + a²/2`. A model can never match a copy *below* chance, so
negative-advantage cells cannot be built by making the focal model erratic — they
require the *other* model to be more decisive and to agree. Exactly **one** such cell
survives confirmation (focal GPT on `b_spiral_cw`, advantage −0.127, k\* = −2.04) and it
depends entirely on Claude staying at 1.000 on spirals. **Do not let the negative-advantage
test rest on it.** The ceiling-zero cells at k > 0 are the robust version of the same test.

**c. Calibration-to-main drift.** These numbers have moved substantially every time they
have been re-measured (`a_chev_ud` advantage +0.65 → +0.29 on confirmation; `d_texture`
p_same(C) 0.845 → 0.498). Run calibration and the main experiment in the same session,
against the same model ids, and re-freeze ΔEV from the calibration actually used.

**d. Assigned vs chosen partner.** Calibration measures the form policy under an *assigned*
partner; the main run has a *chosen* one. If choosing changes the policy, ΔEV is
mis-specified. The call-2 form data is the check: compare main-run form choice against
the calibration policy for the same (focal, partner, stimulus). Flag as a validity
diagnostic, pre-specified, not a nuisance parameter.

**e. Payoff-magnitude confound.** At k > 0 the same-model option pays a smaller number,
so a naïve larger-number heuristic mimics rejecting the copy. k = 0 is the control: equal
payoffs, identity the only difference.

**f. Partner-identity main effect.** For focal GPT "same" means GPT; for focal Claude it
means Claude. A general preference for one lab's model is confounded with "same" *within*
an arm but flips sign *across* arms, while a same-preference keeps its sign. β3 plus the
arm-wise split identifies it. This is why both arms must run.

**g. Ceiling on the outcome.** If models pick the copy at near 100% regardless, there is
no gradient to fit. k = 5 is the guard (ΔEV ≤ −0.06 everywhere). If P(same) > 0.95 at
k = 5, the design has failed and the correct report is "insensitive to price", not a
null on β1.

**h. Floor/ceiling zeros are not equivalent** (§1). Reported separately.

---

## 10. Interpretation, pre-committed

| pattern | reading |
|---|---|
| β1 > 0, β0 ≈ 0 | **A.** Policy-specific strategic valuation |
| β1 ≈ 0, β0 > 0 | **B.** Generic identity heuristic |
| β1 > 0, β0 > 0 | **C.** Both |
| β1 ≈ 0, β0 ≈ 0 | **D.** No evidence partner identity is strategically valued |

Outcome D is only interpretable if the §9g ceiling check passes and the manipulation
check in §11 passes.

---

## 11. Manipulation check (cheap, run first)

Before the main run, and separable from it: **can the focal model predict the other
model's convention at all?** ~200 forced-choice calls asking GPT-5.5 which form Claude
Opus 5 would pick on each calibration stimulus, and vice versa.

This is the step the Study 2 post-mortem identified as untested. Using partner identity
requires notice → knowledge → action. Study 3 fixes *notice* structurally, but if the
model has no knowledge of the other model's conventions, β1 will be zero for a reason
that has nothing to do with strategic valuation, and outcome D would be misread.

If prediction is at chance, ΔEV is a quantity the model cannot compute, and the honest
version of this study replaces the *label* with *evidence* — showing the partner's actual
choices on other stimuli — before spending on the main run.

---

## 12. Sign-off checklist — nothing runs until these are settled

1. OpenAI price confirmed (§7 assumes parity, unverified).
2. §11 manipulation check run and passed, or the design pivoted to evidence-based partners.
3. Calibration N = 120 and stimulus set of 10 approved.
4. §3 selection rule approved **as written**, before calibration output is seen.
5. k grid {0, 1, 2, 3, 5} and N = 30 frozen.
6. §8 model, including β2 and the random-stimulus decision, frozen.
7. Approval file written, as in Study 1 and 2 — the runner refuses to launch on
   `approved=False`, and no script approves anything.
