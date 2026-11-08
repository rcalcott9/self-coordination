# Claude chooser arm on the 58-stimulus GPT-characterized pool — results

> ## REVISION 2026-09-08 — position-fallback cases reclassified
>
> **The original §3.2/§7 treated Claude's position-fallback cases as disqualifying. That was
> wrong and is superseded by §R below.** Under independently randomized layouts a stable
> positional policy produces **chance-level identity coordination**, which is exactly the
> asymmetry Study 4 tests: the focal model's canonical-object convention predicts a COPY but
> not the OTHER. The OTHER does not need to be uncertain or policy-free — its policy only
> needs to be **nontransferable at the level on which coordination is scored**.
>
> Terminology used from here: **form-policy / position-policy**, **identity-level
> nontransfer**, **chance-level identity coordination under independent layouts**. The words
> "diffuse", "uncertain" and bare "near chance" are not used for these cases.
>
> Superseded text is retained below §R for provenance. Raw data is unchanged.
> Current inventory: `claude_arm_20260908/candidate_inventory_tiered.csv` (73 rows, 72 cols).

---

## R. Revised classification

### R.1 Both policy levels are now measured separately

For every model × stimulus the inventory carries, from the same raw calls:

| form (canonical-object) policy | position (screen-coordinate) policy |
|---|---|
| `obj_modal`, `obj_modal_share`, Wilson interval | `pos_modal`, `pos_modal_share`, Wilson interval |
| `obj_margin` (modal − runner-up) | `position_match` (dyadic, screen level) |
| `identity_match` + bootstrap CI | `p_left` |
| `form_consistency` (across AB/BA) | |
| `cross_model_identity_match` (across models) | `policy_type` ∈ {form, position, mixed} |

`policy_type` = **form** if FC ≥ .80; else **position** if `pos_modal_share` ≥ .75; else
**mixed** (neither clean).

### R.2 Tiers

Two batteries, never pooled, both prompt sha8 `3003ae1b`, both current models:
`hp58` (58 stimuli, GPT n=30 / Claude n=60) and `psc15` (15 stimuli, both n=60).

| tier | ≥ .75 | ≥ .90 | families |
|---|---|---|---|
| **T1 competing form** | **1** | **1** | 1 |
| **T2 form vs position** | **10** (9 GPT-focal, 1 Claude-focal) | **10** | 8 |
| T3 shared form control | 53 | 52 | 30 |
| T0 both position-driven (no focal) | 5 | 5 | 3 |
| T0 OTHER mixed policy | 4 | 4 | 3 |

**Tier assignment is identical at .75 and .90** except one T3 item dropping to unqualified.
The asymmetric tiers do not depend on the threshold at all.

### R.3 Tier 1 — competing form policies

| stimulus | GPT | Claude | cross-model identity match |
|---|---|---|---|
| **`a_chev_ud`** [psc15] `A_semantic` | **up** .900, FC .80, id-match .817 [.70,.93] | **down** .917, FC .83, id-match .845 [.72,.97] | **0.167** |

One array, one family. Both models form-driven, opposite canonical objects, and each model's
own-copy identity match exceeds the cross-model match by ~+0.65.

**Borderline (flagged, not promoted):** `x8_contr_c` [hp58] `X8_contrast` — GPT `darker`
1.000 FC 1.00 vs Claude `lighter` .883 FC **.77**, cross-model identity match **0.117** (the
lowest in either battery). It fails T1 only on Claude's form consistency, and fails T2
because Claude is not cleanly positional either (`pos_modal_share` .62). It is a **mixed
policy**, and it is the single most divergent array measured. Its sibling `x8_contr_b` has
Claude on `darker` .933 agreeing with GPT — a within-family crossover.

### R.4 Tier 2 — focal form policy vs OTHER position policy

Promotion criteria applied: focal `obj_modal_share` ≥ th, focal FC ≥ .80, focal
`identity_match` CI lower bound > .50 (binary floor), OTHER FC < .80, OTHER
`pos_modal_share` ≥ .75, focal `identity_match` − cross ≥ .20, no parse/render artifact,
AB/BA balanced independently.

| stimulus | battery | family | focal | focal object (share, FC) | OTHER position policy | cross | **gap** |
|---|---|---|---|---|---|---|---|
| `y9_numer_lo` | hp58 | Y9_numerosity | GPT | many_small 1.000, FC 1.00 | RIGHT .767 | .267 | **+0.733** |
| `y7_nested_hi` | hp58 | Y7_nesting | GPT | many_rings .967, FC .93 | RIGHT .933 | .438 | **+0.495** |
| `c_open_cplx` | hp58 | compete | GPT | closed_cplx .967, FC .93 | **RIGHT 1.000** | .500 | **+0.433** |
| **`d_texture`** | psc15 | D_density | **CLAUDE** | coarse .917, FC .90 | GPT RIGHT .933 | .444 | **+0.400** |
| `y17_sizerank_hi` | hp58 | Y17_size_rank | GPT | ascending 1.000, FC 1.00 | LEFT .900 | .600 | +0.400 |
| `c_open_cplx` | psc15 | compete | GPT | closed_cplx 1.000, FC 1.00 | RIGHT .867 | .633 | +0.367 |
| `y21_localglob_mid` | hp58 | Y21_global_form | GPT | square_of_discs 1.000, FC 1.00 | LEFT .783 | .650 | +0.350 |
| `y17_sizerank_mid` | hp58 | Y17_size_rank | GPT | ascending 1.000, FC 1.00 | LEFT .783 | .717 | +0.283 |
| `y18_symaxis_mid` | hp58 | Y18_symmetry_axis | GPT | vertical_axis 1.000, FC 1.00 | RIGHT .783 | .717 | +0.283 |
| `x7_close_fine` | hp58 | X7_closure | GPT | closed .967, FC .93 | LEFT .833 | .656 | +0.278 |

**`c_open_cplx` appears in both batteries** — an independent replication of the same
form-vs-position asymmetry (Claude RIGHT 1.000 in `hp58`, RIGHT .867 in `psc15`). It is the
best-evidenced Tier-2 candidate.

**`d_texture` supplies the Claude-focal direction**, which the GPT-conditioned `hp58` pool is
structurally incapable of producing.

### R.5 The identity-match floor is not automatic

For a pure position responder under balanced independent layouts the binary identity floor is
**.50**. Observed Tier-2 cross-model identity match ranges **.267–.717**, median .617:

- **3 of 10 fall below .50** — the OTHER's *residual* identity preference is anti-aligned
  with the focal object (`y9_numer_lo`: Claude leans `few_large` while GPT is `many_small`).
- **6 of 10 sit above .50** — residual preference partly aligned.

So the floor is a reference point, not a guarantee. The **projected four-option floor of .25**
is carried in the CSV as `projected_4opt_identity_floor` with
`projected_floor_status = "HYPOTHESIS - requires 4-option premeasurement"`. It assumes
balanced placement and no residual identity preference, and the binary data show residual
preference is real and signed in both directions. It must be measured, never assumed.

### R.6 What did not change

Run integrity (§1), the protocol check (§1.1), the agreement headline (§2 — 54/58 same modal
object, mean cross-model identity match .895), and the conditioning caveat (§6) all stand.
What changed is that 10 arrays previously written off are now the **largest substantive
candidate class**, and the pool yields asymmetric candidates in **8 families**, not one.

---

<details>
<summary>Superseded original text (2026-09-08, pre-revision)</summary>

# Claude chooser arm on the 58-stimulus GPT-characterized pool — results

Run `2026-09-08`. Data: `claude_arm_20260908/data/stageA_CLAUDE58_20260908_172722.csv`
(+ `.jsonl`). Inventory: `claude_arm_20260908/current_model_inventory_58.csv` (58 rows).
Analysis: `claude_arm_20260908/analyze_claude58.py`.

Nothing under `study1_hp_replication_20260905/` or any prior study was modified. The Claude
data lives only in the new run directory and is not pooled with any prior measurement.

---

## 1. Run provenance

| | |
|---|---|
| checkpoint | `claude-opus-5` **requested and returned** on all 3,480 rows |
| prompt | sha8 **`3003ae1b`**, byte-identical to the GPT A1/A2 runs |
| stimuli | 58, all present, 33 families |
| n | **60** per stimulus (GPT was 30) |
| AB/BA balance | exactly 30/30 on every stimulus, **0 violations** |
| seed | `20260812` (same as GPT) |
| trials | 3,480 planned, 3,480 valid |
| **unparseable** | **0** |
| **trials lost** | **0** |
| **API errors** | **0** |
| wall clock | 2,341 s (39 min) |
| cost | **not measured** — the runner logs no token usage. Pre-run estimate $31–68, central ≈$41, stands unverified |

Both models were re-estimated **from raw calls through the identical estimator**
(`targeted_common.cell_metrics`, `unbiased_match`, `boot_draws`, `BOOT_SEED 20260807`), so no
estimator difference can masquerade as a model difference. GPT was *not* read from
`a2_stimulus_level.csv`.

### 1.1 Protocol check on the 4 stimuli with prior Claude data

| stimulus | new (n=60) | prior `policy_specific` (n=60) | prior `study2_partner_policy` (n=180) | verdict |
|---|---|---|---|---|
| `b_tee_ell` | tee .967 | tee .967 | — | **exact** |
| `proto` | circle 1.000 | circle 1.000 | circle 1.000 | **exact** |
| `s_contrast` | dark 1.000 | dark 1.000 | — | **exact** |
| `c_open_cplx` | open_simple .500 | closed_cplx .633 | **.500, mode flipped** | reproduces the *larger* replication |

Three reproduce exactly. The fourth reproduces the n=180 replication rather than the n=60
primary — which is the expected direction, and independently confirms the audit's conclusion
that Claude has no policy on `c_open_cplx`.

---

## 2. Headline: the pool is overwhelmingly agreement

| | GPT (n=30) | Claude (n=60) |
|---|---|---|
| modal share, median | 1.000 | 1.000 |
| modal share, mean | 0.983 | 0.933 |
| ≥ .75 | 58/58 | **49/58** |
| ≥ .90 | 58/58 | **46/58** |
| position fallback (FC < 0.80) | **0/58** | **12/58** |
| near chance (Wilson covers .50) | 0/58 | 3/58 |

**Same modal item on 54 of 58. Mean cross-model match 0.895.**

Conditioned on GPT holding a form convention, Claude usually holds the *same* one.

### 2.1 The four classes

| class | at ≥ .75 | at ≥ .90 | stimuli |
|---|---|---|---|
| **1 · GPT strong / Claude near chance** | **3** (3 fam) | **3** (3 fam) | `c_open_cplx`, `y7_nested_hi`, `y17_sizerank_hi` |
| **2 · both strong / different modes** | **1** (1 fam) | 0 | `x8_contr_c` |
| **3 · both strong / same mode** | 48 (30 fam) | 46 (29 fam) | — |
| 1b · GPT strong / Claude intermediate | 6 (6 fam) | 9 (8 fam) | — |
| 4 · unusable / positional | see §4 | | |

---

## 3. The candidates in detail

### 3.1 Class 2 — the only both-strong divergent array

| | modal | share | margin | FC | p_left | self-match [95% CI] | counts |
|---|---|---|---|---|---|---|---|
| **`x8_contr_c`** GPT | darker | 1.000 | +1.000 | 1.00 | .50 | 1.000 [1.00, 1.00] | darker 30 |
| **`x8_contr_c`** Claude | **lighter** | 0.883 | +0.767 | **0.77** | .38 | 0.790 [0.67, 0.90] | lighter 53 / darker 7 |

**Cross-model match 0.117.** Opposite poles of a contrast pair, both mostly form-driven.

Its sibling is the informative part: **`x8_contr_b` — same family, same two identities —
has Claude on `darker` at .933, agreeing with GPT (cross-match .933).** So within
`X8_contrast` there is a **crossover** between members: one agrees, one diverges. That is
the same parametric signature as `F10_curvature` in the 4-option battery, and it is the only
place in this pool where it appears.

**Caveat, not resolved:** Claude's form consistency on `x8_contr_c` is 0.77, just under the
project's `FC_CLEAN = 0.80` bar. It is not a position responder (p_left .38, and it picks
"lighter" across both presentations), but it is not clean either.

### 3.2 Class 1 — and why "near chance" here does not mean "no policy"

| stimulus | GPT | Claude | Claude FC | Claude p_left |
|---|---|---|---|---|
| `c_open_cplx` | closed_cplx .967 | open_simple **.500** | **0.00** | **0.00** |
| `y7_nested_hi` | many_rings .967 | one_thick_ring .567 | **0.13** | 0.07 |
| `y17_sizerank_hi` | ascending 1.000 | ascending .600 | **0.20** | **0.90** |

**All three are Claude reverting to position, not choosing diffusely over forms.**

On `c_open_cplx` Claude picked **RIGHT on all 60 trials**. Its identity counts are exactly
30/30 *because the AB/BA schedule is 30/30* — the .500 is an artifact of a balanced design
meeting a pure position responder, and its self-match 0.491 is the binary floor.
`y17_sizerank_hi` is the same thing mirrored (LEFT on 90%).

This distinction matters for Study 4. A partner that is at chance **on identity** but
deterministic **on position** is not unpredictable — it is perfectly predictable by a rule the
design declared irrelevant. "Claude has no form convention" is supported; "Claude is diffuse"
is not.

### 3.3 All four divergent-mode arrays share one property

| stimulus | GPT FC | Claude FC | cross |
|---|---|---|---|
| `x8_contr_c` | 1.00 | 0.77 | 0.117 |
| `y9_numer_lo` | 1.00 | 0.47 | 0.267 |
| `y7_nested_hi` | 0.93 | 0.13 | 0.438 |
| `c_open_cplx` | 0.93 | 0.00 | 0.500 |

**Every divergence in this pool has Claude below the 0.80 form-consistency bar, and GPT above
0.93.** Divergence here is not two competing form conventions; it is GPT holding a convention
while Claude falls back to position — with `x8_contr_c` the only marginal exception.

---

## 4. Flags

- **12 of 58** Claude cells are position fallbacks (FC < 0.80); **0** GPT cells are.
- `y17_sizerank_hi` and `y17_sizerank_mid` also trip the rationale-position lexical check
  (> 50% of Claude rationales mention position).
- No ceiling-artifact exclusions were needed beyond the usual: 46 arrays have both models
  ≥ .90 on the same item, so one option is effectively never chosen — fine as stag-hunt
  controls, useless for detecting relational adaptation.
- **Zero** malformed responses, so no parsing artifact can explain any difference.

---

## 5. By family

33 families. The 8 with any non-agreement:

| family | n | GPT mean | Claude mean | cross | classes |
|---|---|---|---|---|---|
| `X8_contrast` | 2 | 1.000 | 0.908 | **0.525** | 1×class 2, 1×class 3 |
| `Y7_nesting` | 1 | 0.967 | 0.567 | 0.438 | 1×class 1 |
| `Y9_numerosity` | 1 | 1.000 | 0.733 | **0.267** | 1×class 1b |
| `compete` | 1 | 0.967 | 0.500 | 0.500 | 1×class 1 |
| `Y17_size_rank` | 3 | 1.000 | 0.761 | 0.761 | 1×class 1, 1×1b, 1×3 |
| `Y25_aspect_vertex` | 2 | 0.983 | 0.750 | 0.741 | 1×1b, 1×3 |
| `Y21_global_form` | 2 | 1.000 | 0.825 | 0.825 | 1×1b, 1×3 |
| `Y18_symmetry_axis` | 2 | 1.000 | 0.858 | 0.858 | 1×1b, 1×3 |

The other 25 families are uniformly class 3 with cross-match ≥ 0.83.

---

## 6. What this pool can and cannot estimate

**Conditioned on GPT being strong.** All 58 were selected as `form_rule_ceiling` for GPT-5.5.

Supported: *given* GPT holds a form convention, Claude holds the same one about 93% of the
time (54/58), holds a different one about 7% (4/58), and reverts to position about 21% of the
time (12/58).

**Not supported, and not claimed:** the prevalence of Claude-strong/GPT-weak policies. That
cell is structurally absent from this pool — no stimulus here was selected for Claude, and
GPT is at ceiling on all of them by construction. Estimating the reverse asymmetry requires a
Claude-first screen, which does not exist.

Also not established: whether the 4 divergences are stable. Each is a single n=60 estimate
under one prompt; `c_open_cplx` is the only one with independent corroboration.

---

## 7. Recommendation on four-object extension

**One mechanism merits it: `X8_contrast`.** It is the only family where both models are
form-driven and their modal choices cross over between members — GPT is `darker` at 1.000 on
both `x8_contr_b` and `x8_contr_c`, while Claude moves from `darker` .933 to `lighter` .883.
That is a parametric boundary, the same shape as `F10_curvature`, and it is the only candidate
in 33 families.

Per the audit's rule, the extension should **cross a second factor rather than lengthen the
tone ladder** — four cells of tone × (fill vs outline), or tone × stroke weight — so no object
is a trivial distractor and interiors stay live. A four-tone ladder would reproduce the F10
failure.

**Do not extend on the class-1 arrays.** `c_open_cplx`, `y7_nested_hi` and `y17_sizerank_hi`
are Claude-positional, not Claude-diffuse. Adding two objects changes the position structure
entirely and there is no reason to expect the binary behaviour to survive; more importantly,
a positional partner is the wrong control for a stag hunt about form conventions.

**`Y9_numerosity` is a near-miss worth one cheap probe before committing** — Claude at .733
on the opposite item, but FC 0.47, so it is half position. A denser sweep of that family on
the binary battery (~6 members × 60 × 2 models ≈ 720 calls ≈ $10) would establish whether a
form-driven divergence exists there before any four-object work.

**Every four-object array requires fresh premeasurement of both models.** Nothing above
assumes the binary policy transfers.

---

## 8. Not done, per instruction

No Study 4 items selected. No stimulus generator modified. No four-object arrays generated.
No API calls beyond the 3,480 reported here.

</details>
