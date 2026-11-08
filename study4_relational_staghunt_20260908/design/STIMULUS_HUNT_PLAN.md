# Study 4 (relational stag hunt) — stimulus hunt plan, **v2**

Revised `2026-09-08` after the Claude chooser arm and the position-fallback correction.
v1 is preserved verbatim as `STIMULUS_HUNT_PLAN_v1_superseded.md`. No raw data was modified.

**Status: PLAN. No stimuli generated, no API calls in this revision.**

---

## 0. The correction that drives v2

v1 excluded position-fallback cases as "diffuse" or "near chance". **That was wrong.**

The study does not require the OTHER model to be uncertain or policy-free. It requires the
focal model's **canonical-object** convention to predict a COPY substantially better than it
predicts the OTHER. A model with a deterministic *screen-position* policy is highly
predictable in screen coordinates and **unpredictable over canonical object identity** once
layouts are randomized independently between players — which is exactly the asymmetry the
design tests.

```
GPT   → canonical object X, on every layout          (form policy)
Claude→ whichever object is on the RIGHT             (position policy)
layouts randomized independently per player
⇒ GPT's object policy transfers to a GPT COPY (identity match ≈ 1.0)
⇒ GPT's object policy does NOT transfer to Claude   (identity match ≈ chance)
```

**Required vocabulary.** `form-policy` / `position-policy`; `identity-level nontransfer`;
`chance-level identity coordination under independent layouts`. Do not write "diffuse",
"uncertain", or bare "near chance" for a position-policy case — it is a *policy*, just not a
transferable one.

---

## 1. Measurement contract — both policy levels, always

For every model × stimulus, from the same raw calls, the inventory carries:

| form (canonical-object) policy | position (screen-coordinate) policy |
|---|---|
| `obj_modal`, `obj_modal_share` + Wilson interval | `pos_modal`, `pos_modal_share` + Wilson interval |
| `obj_margin` (modal − runner-up) | `position_match` (dyadic, screen level) |
| `identity_match` (unbiased dyadic) + bootstrap CI | `p_left` |
| `form_consistency` across position permutations | |
| `cross_model_identity_match` | `policy_type` ∈ {form, position, mixed} |

`policy_type` = **form** if FC ≥ .80; else **position** if `pos_modal_share` ≥ .75; else
**mixed**. The mixed state is real and must not be collapsed into either (see `x8_contr_c`).

Coordination is **never** scored by screen position, at any stage.

---

## 2. Three substantive tiers — kept separate everywhere

They support related but non-identical mechanism claims and must never be pooled.

**Tier 1 — competing form policies.** Both models reliably form-driven, both with stable
canonical-object policies, **different** modal objects.

**Tier 2 — focal form policy vs OTHER position policy.** Focal has a strong canonical-object
convention; OTHER has a stable positional policy; independent layouts make OTHER's
canonical-object choice chance-level or substantially less predictable; focal own-copy
identity match substantially exceeds focal–OTHER identity match.

**Tier 3 — shared form policy controls.** Both reliably form-driven, **same** canonical modal
object.

### 2.1 Tier-2 promotion criteria (as applied)

- focal `obj_modal_share` ≥ threshold (.75; sensitivity at .90)
- focal `form_consistency` ≥ .80
- focal `identity_match` 95% CI lower bound **> .50** (the binary identity floor)
- OTHER `pos_modal_share` ≥ .75 **or** other clear position-fallback evidence
- OTHER `form_consistency` < .80
- focal `identity_match` − `cross_model_identity_match` ≥ **.20**
- no parsing or rendering artifact
- position permutations balanced independently (AB/BA exactly n/2 each)

---

## 3. Current inventory — what qualifies now

Source: `claude_arm_20260908/candidate_inventory_tiered.csv` (73 rows, 72 cols). Two
batteries, never pooled, both prompt sha8 `3003ae1b`, both current models:
`hp58` (GPT n=30 / Claude n=60) and `psc15` (both n=60).

| tier | ≥ .75 | ≥ .90 | families | focal |
|---|---|---|---|---|
| **T1 competing form** | **1** | **1** | 1 | both |
| **T2 form vs position** | **10** | **10** | **8** | 9 GPT, 1 Claude |
| T3 shared form control | 53 | 52 | 30 | both |
| T0 both position-driven | 5 | 5 | 3 | — |
| T0 OTHER mixed policy | 4 | 4 | 3 | — |

**The asymmetric tiers are completely insensitive to the .75 → .90 threshold change.** Only
one T3 item moves.

### 3.1 Tier 1 (1 array, 1 family)

`a_chev_ud` [psc15, `A_semantic`] — GPT **up** .900 FC .80 vs Claude **down** .917 FC .83,
cross-model identity match **.167**.

**Borderline, flagged not promoted:** `x8_contr_c` [hp58, `X8_contrast`] — GPT **darker**
1.000 FC 1.00 vs Claude **lighter** .883 FC **.77**, cross-model identity match **.117**, the
lowest measured. Fails T1 on Claude's FC and T2 because Claude is not cleanly positional
either (`pos_modal_share` .62): a genuine **mixed policy**. Its sibling `x8_contr_b` has
Claude agreeing (`darker` .933) — a within-family crossover.

### 3.2 Tier 2 (10 arrays, 8 families)

Ordered by gap = focal `identity_match` − `cross_model_identity_match`.

| stimulus | battery | family | focal | focal object | OTHER position | cross | gap |
|---|---|---|---|---|---|---|---|
| `y9_numer_lo` | hp58 | Y9_numerosity | GPT | many_small 1.000 | RIGHT .767 | .267 | **+.733** |
| `y7_nested_hi` | hp58 | Y7_nesting | GPT | many_rings .967 | RIGHT .933 | .438 | **+.495** |
| `c_open_cplx` | hp58 | compete | GPT | closed_cplx .967 | **RIGHT 1.000** | .500 | **+.433** |
| **`d_texture`** | psc15 | D_density | **CLAUDE** | coarse .917 | GPT RIGHT .933 | .444 | **+.400** |
| `y17_sizerank_hi` | hp58 | Y17_size_rank | GPT | ascending 1.000 | LEFT .900 | .600 | +.400 |
| `c_open_cplx` | psc15 | compete | GPT | closed_cplx 1.000 | RIGHT .867 | .633 | +.367 |
| `y21_localglob_mid` | hp58 | Y21_global_form | GPT | square_of_discs 1.000 | LEFT .783 | .650 | +.350 |
| `y17_sizerank_mid` | hp58 | Y17_size_rank | GPT | ascending 1.000 | LEFT .783 | .717 | +.283 |
| `y18_symaxis_mid` | hp58 | Y18_symmetry_axis | GPT | vertical_axis 1.000 | RIGHT .783 | .717 | +.283 |
| `x7_close_fine` | hp58 | X7_closure | GPT | closed .967 | LEFT .833 | .656 | +.278 |

`c_open_cplx` appears in **both batteries** — an independent replication of the same
asymmetry. `d_texture` is the only **Claude-focal** candidate anywhere; the GPT-conditioned
`hp58` pool cannot produce that direction by construction.

### 3.3 Counts by mechanism

| family / mechanism | T2 arrays | focal |
|---|---|---|
| `compete` (open/simple vs closed/complex) | 2 (replicated) | GPT |
| `Y17_size_rank` | 2 | GPT |
| `Y9_numerosity` | 1 | GPT |
| `Y7_nesting` | 1 | GPT |
| `Y18_symmetry_axis` | 1 | GPT |
| `Y21_global_form` | 1 | GPT |
| `X7_closure` | 1 | GPT |
| `D_density` | 1 | **Claude** |

### 3.4 Identity-match floors — reference points, not guarantees

| | binary | four-option (projected) |
|---|---|---|
| pure position responder, balanced placement, no residual identity preference | **.50** | **.25** |

Observed Tier-2 cross-model identity match spans **.267 – .717** (median .617):

- **3 of 10 below .50** — the OTHER's residual identity preference is *anti-aligned* with the
  focal object (`y9_numer_lo`: Claude leans `few_large`, GPT is `many_small`).
- **6 of 10 above .50** — residual preference partly aligned.

Residual identity preference is real and signed in **both** directions. The four-option
projection of .25 is therefore carried as
`projected_floor_status = "HYPOTHESIS - requires 4-option premeasurement"` and must be
measured, never assumed.

---

## 4. Four-object extension — two tracks

### Track A — competing form policies

1. **`X8_contrast` first.** The only within-family crossover in either battery
   (`x8_contr_b` agrees, `x8_contr_c` diverges at cross-match .117). Cross **tone × (fill vs
   outline)** or **tone × stroke weight** — four crossed cells, not a four-tone ladder.
2. **`A_semantic` (`a_chev_ud`)** — the only clean Tier 1. Natural extension to the four
   canonical chevron orientations (up/down/left/right): identical ink, no distractor by
   construction. Risk to measure: the 4-way version may pull both models to one canonical
   orientation and destroy the divergence.
3. **Inspect the `Y9_numerosity` sweep** before committing — it is Tier 2 with the largest
   gap, but Claude is `mixed`-leaning (FC .47, `pos_modal_share` .767). A denser binary sweep
   of that family (~6 members × 60 × 2 models ≈ 720 calls) would establish whether the
   divergence is form-driven or position-driven before any four-object work.
4. **Retain `F10_curvature` as a separate crossover mechanism.** It is a 4-option finding
   (GPT spiky / Claude smooth across 6 of 8 members) and is independent of everything above.
   Its known defect — 0.8% of draws on interior rungs — is precisely why extensions must be
   crossed-factor, not laddered.

### Track B — focal form vs OTHER position

Extend the strongest form-vs-position mechanisms: **`compete`** (replicated, Claude RIGHT
1.000), **`Y7_nesting`**, **`Y17_size_rank`**, and **`D_density`** for the Claude-focal
direction.

Construction rules:

- **Four legitimate objects** — all four must be defensible members of the contrast, never
  filler. For `compete`, break the open/closed × simple/complex confound into its four
  corners; for `Y17_size_rank`, cross rank direction with a second factor rather than adding
  ladder rungs.
- **Canonical-object positions randomized independently across calls *and* across players**,
  using the existing balanced `position_schedule` (every object in every position exactly
  n/4 times).
- **No screen position visually distinctive** — uniform panel geometry, uniform numeric
  labels, uniform ground. A layout where one slot is salient converts a position policy into
  a form policy and destroys the contrast.
- **Remeasure both halves**: whether the focal model preserves its form policy over four
  objects, and whether the OTHER preserves its positional policy. Either can break.

---

## 5. Four-object premeasurement contract

Premeasurement must use **the exact arrays later used in the game**:

- all four objects present;
- **no green marker** at premeasurement;
- the **same coordination-policy prompt** (sha8 `3003ae1b` lineage, arity adapted);
- all **24 position permutations balanced**;
- **canonical object identity and screen position both recorded** on every trial.

A binary result **nominates a mechanism; it does not certify a four-object policy.** No array
enters Study 4 on binary evidence alone.

Discovery n = 24/model/array; confirmation n ≥ 60/model/array in a separate file. Discovery
and confirmation are never pooled for a final estimate.

---

## 6. Green assignment

Only **after** four-object policies are established:

1. Designate a green object that is **not** either model's relevant canonical modal choice.
2. Apply the green marker **only in the strategic experiment**, never at premeasurement.
3. Verify position balancing remains **independent between players** after green is added.
4. **Never score coordination by screen position** — the estimand is canonical object identity
   at every stage.

---

## 7. Interpretation for Study 4

| partner condition | prediction |
|---|---|
| **COPY** | The focal model's stable canonical-object policy predicts its partner; the 10-point object equilibrium is reachable and should be pursued. |
| **OTHER, position-policy** (Tier 2) | The focal model's object policy does not predict the partner's canonical choice — identity-level nontransfer. Assurance is absent, so the 5-point green equilibrium should become more attractive. |
| **OTHER, competing-form** (Tier 1) | The partner has a different stable object target. Assurance is again absent, for a different reason. |
| **Shared-form control** (Tier 3) | Both policies point at the same object, so partner identity should matter less. |

**The OTHER model need not lack a policy.** Its policy only needs to be nontransferable from
the focal model's policy at the level on which coordination is scored. Tier 1 and Tier 2
remove assurance by different mechanisms — a competing target versus a target defined in the
wrong coordinate system — and their results must be reported separately.

---

## 8. Feasibility, revised

v1 judged the hunt near-infeasible on the strength of Tier-1-style items alone. With Tier 2
admitted that judgement changes:

- **11 substantive asymmetric candidates across 9 families** (1 T1 + 10 T2), against v1's one.
- Tier assignment is **threshold-insensitive** (.75 vs .90).
- One candidate is **replicated across two batteries** (`c_open_cplx`).
- Both focal directions are represented (9 GPT-focal, 1 Claude-focal).
- 53 Tier-3 controls in 30 families are available at no additional cost.

The remaining constraints are unchanged and real: the Claude-focal direction rests on a
**single** array; every candidate is a **binary** result that four-object premeasurement may
not reproduce; and the `hp58` pool is conditioned on GPT being strong, so it cannot estimate
the prevalence of Claude-strong/GPT-position policies. A Claude-first screen remains the only
way to get that cell, and does not exist.

**Recommended order:** Track B on `compete` (replicated, cleanest position policy), then
Track A on `X8_contrast`, then the `Y9_numerosity` binary sweep, then `A_semantic`.
