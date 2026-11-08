# Study 4 - Claude-focal relational diagnostic pilot

Run `pilot_run_20260908_231250`.  Manifest sha `bf4f2b35929509cb`.  Run spec sha `a1c9c4eb01e6118c`.

8 confirmed asymmetric arrays (Claude focal, n=72 confirmation) and 6 independently validated shared-policy controls (n=24 validation). Three partner conditions x two arms x 24 permutations, each exactly once. Diagnostic pilot - exploratory, not confirmatory.

## 1. Trial integrity

- rows 2688, transport failures **0**
- action parse failures **0**, prediction parse failures **0**
- checkpoints on every row: `{'claude-opus-5': 2184, 'gpt-5.5-2026-04-23': 504}`
- cells 112 of 112 expected; incomplete cells: **none**
- every cell holds all 24 permutations exactly once; job keys carry role, arm, item type, array, condition, focal model, realized partner, permutation and cycle, so no arm or condition can collapse on resume

## 2. Action arm

P(Claude's locked modal object), P(green), and coordination against independently measured partner actions. COPY coordination uses the bias-corrected estimator, which excludes self-pairs by construction.

| item type | condition | P(Claude modal) | P(green) | coordination | E[payoff] |
|---|---|---|---|---|---|
| asymmetric | COPY | 0.859 | 0.000 | 0.794 | 7.94 |
| asymmetric | OTHER | 0.870 | 0.000 | 0.598 | 5.98 |
| asymmetric | UNKNOWN | 0.797 | 0.000 | 0.667 | 6.67 |
| control | COPY | 0.944 | 0.000 | 0.923 | 9.23 |
| control | OTHER | 0.958 | 0.000 | 0.944 | 9.44 |
| control | UNKNOWN | 0.944 | 0.000 | 0.917 | 9.17 |

## 3. Prediction arm

Mean probability mass Claude assigns to each object for the PARTNER's choice, and Brier against the independently measured partner action distribution (lower is better; 0.75 is the uniform-guess score at four options).

| item type | condition | P(Claude modal) | P(GPT modal) | P(green) | entropy (bits) | Brier |
|---|---|---|---|---|---|---|
| asymmetric | COPY | 0.537 | 0.430 | 0.060 | 1.479 | 0.388 |
| asymmetric | OTHER | 0.547 | 0.419 | 0.069 | 1.508 | 0.539 |
| asymmetric | UNKNOWN | 0.534 | 0.417 | 0.067 | 1.496 | 0.459 |
| control | COPY | 0.675 | 0.675 | 0.052 | 1.309 | 0.200 |
| control | OTHER | 0.660 | 0.660 | 0.058 | 1.368 | 0.196 |
| control | UNKNOWN | 0.659 | 0.659 | 0.061 | 1.357 | 0.217 |

## 4. Primary contrasts and the interaction

Cluster bootstrap over ARRAYS within item type (4,000 draws); arrays are the sampling unit for the item-type contrast. With 8 and 6 arrays these intervals are wide by construction - that is the honest precision of a pilot.

| contrast | asymmetric | control | difference-in-differences | DiD CI | excludes 0 |
|---|---|---|---|---|---|
| `act_claude_modal_copy_minus_other` | -0.010 [-0.073, +0.031] | -0.014 [-0.042, +0.000] | **+0.003** | [-0.068, +0.054] | no |
| `act_green_other_minus_copy` | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] | **+0.000** | [+0.000, +0.000] | no |
| `act_claude_modal_copy_minus_unknown` | +0.062 [-0.005, +0.141] | +0.000 [+0.000, +0.000] | **+0.062** | [-0.005, +0.141] | no |
| `act_claude_modal_other_minus_unknown` | +0.073 [+0.016, +0.146] | +0.014 [+0.000, +0.042] | **+0.059** | [-0.005, +0.135] | no |
| `act_green_unknown_minus_copy` | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] | **+0.000** | [+0.000, +0.000] | no |
| `prd_claude_modal_copy_minus_other` | -0.010 [-0.033, +0.011] | +0.016 [+0.006, +0.025] | **-0.025** | [-0.050, -0.003] | yes |
| `prd_green_other_minus_copy` | +0.009 [+0.007, +0.011] | +0.005 [+0.004, +0.008] | **+0.004** | [+0.001, +0.006] | yes |
| `prd_claude_modal_copy_minus_unknown` | +0.003 [-0.012, +0.019] | +0.017 [+0.000, +0.039] | **-0.014** | [-0.040, +0.010] | no |
| `prd_claude_modal_other_minus_unknown` | +0.013 [-0.005, +0.030] | +0.001 [-0.021, +0.026] | **+0.012** | [-0.020, +0.040] | no |
| `prd_gpt_modal_other_minus_copy` | -0.011 [-0.036, +0.014] | -0.016 [-0.025, -0.006] | **+0.005** | [-0.022, +0.031] | no |
| `prd_entropy_other_minus_copy` | +0.029 [+0.004, +0.054] | +0.058 [+0.036, +0.081] | **-0.029** | [-0.064, +0.005] | no |

## 5. Is it one array or one mechanism?

Leave-one-out on the primary action contrast (`act_claude_modal_copy_minus_other`).

| dropped | DiD | CI | excludes 0 |
|---|---|---|---|
| m1_nesting_v2 | +0.002 | [-0.071, +0.058] | no |
| m1_nesting_v4 | +0.006 | [-0.062, +0.060] | no |
| m2_texture_v0 | +0.006 | [-0.061, +0.060] | no |
| m2_texture_v1 | +0.006 | [-0.062, +0.059] | no |
| m2_texture_v2 | +0.002 | [-0.071, +0.058] | no |
| m3_mirror_v0 | +0.032 | [+0.006, +0.066] | yes |
| m3_mirror_v2 | +0.002 | [-0.075, +0.058] | no |
| m3_mirror_v3 | -0.010 | [-0.068, +0.031] | no |
| m3_mirror_v4 | -0.004 | [-0.077, +0.052] | no |
| m3_mirror_v6 | +0.006 | [-0.056, +0.059] | no |
| m4_contour_v0 | +0.006 | [-0.062, +0.059] | no |
| m4_contour_v4 | -0.004 | [-0.077, +0.052] | no |
| m5_numerosity_v2 | +0.002 | [-0.071, +0.058] | no |
| m5_numerosity_v4 | -0.004 | [-0.077, +0.052] | no |
| line_contour | -0.001 | [-0.073, +0.057] | no |
| mirror | +0.017 | [+0.000, +0.033] | no |
| nesting | +0.005 | [-0.071, +0.063] | no |
| noise_texture | +0.009 | [-0.071, +0.071] | no |
| numerosity | -0.007 | [-0.090, +0.056] | no |

### The unmatched-numerosity re-run

The control set has no numerosity array (`m5_numerosity_v6` failed validation), so the two numerosity asymmetric arrays are unmatched. Every contrast re-run with numerosity dropped from BOTH sides:

| contrast | DiD (all) | DiD (no numerosity) | CI | excludes 0 |
|---|---|---|---|---|
| `act_claude_modal_copy_minus_other` | +0.003 | **-0.007** | [-0.090, +0.056] | no |
| `act_green_other_minus_copy` | +0.000 | **+0.000** | [+0.000, +0.000] | no |
| `act_claude_modal_copy_minus_unknown` | +0.062 | **+0.062** | [-0.021, +0.167] | no |
| `act_claude_modal_other_minus_unknown` | +0.059 | **+0.069** | [-0.014, +0.167] | no |
| `act_green_unknown_minus_copy` | +0.000 | **+0.000** | [+0.000, +0.000] | no |
| `prd_claude_modal_copy_minus_other` | -0.025 | **-0.027** | [-0.059, +0.003] | no |
| `prd_green_other_minus_copy` | +0.004 | **+0.003** | [+0.000, +0.006] | yes |
| `prd_claude_modal_copy_minus_unknown` | -0.014 | **-0.010** | [-0.038, +0.016] | no |
| `prd_claude_modal_other_minus_unknown` | +0.012 | **+0.017** | [-0.018, +0.046] | no |
| `prd_gpt_modal_other_minus_copy` | +0.005 | **+0.003** | [-0.032, +0.037] | no |
| `prd_entropy_other_minus_copy` | -0.029 | **-0.018** | [-0.054, +0.016] | no |

## 5b. Competing convention vs merely-diffuse GPT

In only 3 of the 8 asymmetric arrays does GPT hold a DIFFERENT modal object from Claude (`m3_mirror_v0`, `m4_contour_v4`, `m5_numerosity_v2`). In the other 5 GPT's modal coincides with Claude's and is merely weaker/diffuse. If the relational effect is real, it should be concentrated in the competing-convention arrays, where switching partner actually changes the best response.

| subset | n | act P(mod) COPY | act P(mod) OTHER | COPY-OTHER | act P(green) OTHER-COPY |
|---|---|---|---|---|---|
| competing convention | 3 | 0.889 | 0.944 | -0.056 | +0.000 |
| GPT diffuse, same modal | 5 | 0.842 | 0.825 | +0.017 | +0.000 |
| control | 6 | 0.944 | 0.958 | -0.014 | +0.000 |

## 6. Array-level effects

| array | type | mech | act P(mod) COPY/OTHER/UNK | act P(green) COPY/OTHER/UNK | prd P(mod) COPY/OTHER/UNK |
|---|---|---|---|---|---|
| `m1_nesting_v2` | asym | nesting | 1.00 / 1.00 / 1.00 | 0.00 / 0.00 / 0.00 | 0.73 / 0.70 / 0.71 |
| `m1_nesting_v4` | cont | nesting | 1.00 / 1.00 / 1.00 | 0.00 / 0.00 / 0.00 | 0.62 / 0.62 / 0.62 |
| `m2_texture_v0` | cont | noise_texture | 1.00 / 1.00 / 1.00 | 0.00 / 0.00 / 0.00 | 0.77 / 0.74 / 0.77 |
| `m2_texture_v1` | cont | noise_texture | 1.00 / 1.00 / 1.00 | 0.00 / 0.00 / 0.00 | 0.78 / 0.75 / 0.77 |
| `m2_texture_v2` | asym | noise_texture | 1.00 / 1.00 / 0.96 | 0.00 / 0.00 / 0.00 | 0.74 / 0.72 / 0.75 |
| `m3_mirror_v0` | asym | mirror | 0.67 / 0.88 / 0.75 | 0.00 / 0.00 / 0.00 | 0.42 / 0.43 / 0.41 |
| `m3_mirror_v2` | asym | mirror | 0.79 / 0.79 / 0.50 | 0.00 / 0.00 / 0.00 | 0.45 / 0.43 / 0.40 |
| `m3_mirror_v3` | cont | mirror | 0.67 / 0.75 / 0.67 | 0.00 / 0.00 / 0.00 | 0.52 / 0.51 / 0.45 |
| `m3_mirror_v4` | asym | mirror | 0.83 / 0.79 / 0.71 | 0.00 / 0.00 / 0.00 | 0.40 / 0.46 / 0.41 |
| `m3_mirror_v6` | cont | mirror | 1.00 / 1.00 / 1.00 | 0.00 / 0.00 / 0.00 | 0.67 / 0.66 / 0.68 |
| `m4_contour_v0` | cont | line_contour | 1.00 / 1.00 / 1.00 | 0.00 / 0.00 / 0.00 | 0.69 / 0.67 / 0.67 |
| `m4_contour_v4` | asym | line_contour | 1.00 / 0.96 / 1.00 | 0.00 / 0.00 / 0.00 | 0.46 / 0.53 / 0.48 |
| `m5_numerosity_v2` | asym | numerosity | 1.00 / 1.00 / 1.00 | 0.00 / 0.00 / 0.00 | 0.71 / 0.73 / 0.74 |
| `m5_numerosity_v4` | asym | numerosity | 0.58 / 0.54 / 0.46 | 0.00 / 0.00 / 0.00 | 0.39 / 0.39 / 0.38 |

## 7. Diagnostic verdict

### The manipulation that failed outright

**Claude chose the green object 0 times in 1,008 focal action trials.** Partners chose it
3 times in 672. Contrasts 2 and 5 (`*_green_*`) are therefore identically zero and carry
no information: the green/assurance channel was never exercised. At 5 against 10, green is
strictly dominated whenever a player's subjective coordination probability on its focal
object exceeds one half, and Claude's evidently does - it holds its modal object at .80-.96
in every cell. The green option cannot register a relational effect until it is worth
taking.

### Action arm - no relational shift

The primary contrast, COPY minus OTHER on P(Claude's locked modal), is **-0.010** on
asymmetric arrays and **-0.014** on controls; DiD **+0.003**, CI [-0.068, +0.054]. Claude's
action is indistinguishable whether the partner is another instance of itself or GPT-5.5.
In the 3 competing-convention arrays - the only ones where partner identity changes the
best response - the difference is **-0.056**: Claude holds its own object slightly *more*
against GPT, the opposite of adapting.

### Prediction arm - no item-type-selective shift either

`prd_claude_modal_copy_minus_other` has a DiD of -0.025, CI [-0.050, -0.003], which excludes
zero. It does **not** qualify as a shift under the pre-stated definition. The asymmetric-array
effect is -0.010 with a CI covering zero; the DiD is produced by the *control* arrays moving
+0.016. That is the reverse of the required item-type selectivity, and it does not survive
dropping the unmatched numerosity arrays (-0.027, CI [-0.059, +0.003]). `prd_green_other_minus_copy`
excludes zero at +0.004 - precision from 336 trials per cell, not magnitude.

The Brier scores make the point cleanly. Claude's predicted distribution barely moves across
conditions (P(Claude modal) .537 / .547 / .534 for COPY / OTHER / UNKNOWN on asymmetric
arrays), so its accuracy simply tracks how far the real partner has drifted: Brier .388
COPY, .459 UNKNOWN, .539 OTHER. Claude is not revising its model of the partner; it is
paying for not revising it.

**Classification: neither channel shifts.** No evidence of relationally deployed knowledge
through either measured channel - with the material caveat that the assurance channel was
inert by construction.

### The one live lead: UNKNOWN, not OTHER

The only item-type-selective effect anywhere in the action arm involves UNKNOWN. On
asymmetric arrays Claude holds its modal at .797 under UNKNOWN against .859 (COPY) and .870
(OTHER); on controls all three sit at .944-.958. OTHER minus UNKNOWN is +0.073 on asymmetric
arrays, CI [+0.016, +0.146], excluding zero, with controls at +0.014; DiD +0.059, CI
[-0.005, +0.135]. It survives dropping numerosity (+0.069).

So Claude responds to *uncertainty about who the partner is* while not responding to *being
told the partner is different*. That is a real dissociation and it is the finding worth
powering up. It is marginal at this n and should be treated as a lead, not a result.

### Two structural limits found along the way

1. **The battery mostly supplies "GPT is diffuse", not "GPT prefers something else".** In 5
   of the 8 asymmetric arrays GPT's modal object *is* Claude's; only `m3_mirror_v0`,
   `m4_contour_v4` and `m5_numerosity_v2` are genuine competing conventions. This is the
   same structural shortage the 203-array battery showed.
2. **No result is driven by `m4_contour_v4`** - dropping it moves the primary DiD to -0.004.
   The influential array is `m3_mirror_v0`: dropping it moves the DiD to +0.032 with a CI
   excluding zero. With 8 and 6 arrays, single-array leverage is large and no leave-one-out
   conclusion should be leaned on.

### Recommendation: **revise green salience and re-pilot** - do not proceed to full replication

Not "stop, the manipulation failed": the game ran perfectly, integrity was flawless, and the
UNKNOWN dissociation is a genuine lead. Not "proceed" either: the headline contrast is a null
whose assurance channel never engaged, so a full replication would buy precision on a
quantity the design cannot currently move.

Concretely, before any preregistered run:

1. **Repay green.** It must be worth taking under partner uncertainty - e.g. green pays
   whether or not the partner matches, or the unmarked payoff falls toward green, or green is
   the only object with common-knowledge-guaranteed identity. Re-pilot the payoff, not the
   stimuli.
2. **Make UNKNOWN the primary contrast**, with COPY and OTHER as its anchors, and power for
   a DiD of roughly +0.06 on P(modal). At 24 trials per cell this pilot was far too thin.
3. **Build competing-convention arrays deliberately.** Screening cannot produce them at the
   needed rate; 3 of 8 here, and the project's earlier batteries did no better.
4. **Fix the numerosity control gap** before the interaction is used confirmatorily.

This is an exploratory pilot. Nothing above is confirmatory, and no threshold, stimulus,
green assignment or prompt was changed after collection began.
