# Study 4 — targeted four-object asymmetric-policy stimulus search

Discovery run `discovery5_20260909_011211`; confirmation run `confirm5_20260909_012018`. 2026-09-09.
Generator `code/make_battery5.py`; battery `stimuli5/` sha256 `65b086da…`.
**No green marker at any stage. Nothing prior was overwritten or pooled.**

## VERDICT

**9 confirmed asymmetric focal-model × array candidates on 8 distinct arrays, spanning
5 mechanisms.** The minimum stimulus-diversity requirement (≥6 confirmed arrays, ≥3
mechanisms) is **MET**. The *preference* for ≥2 usable cases per focal model is met for
Claude (8) and **not** for GPT (1).

**All 12 locked predictions held** — the unconstrained confirmation mode equalled the locked
focal identity in 12/12 cases, so no confirmed result rests on a post-hoc winner.

---

## 1. Phase 1 — what the existing evidence already showed

Before generating anything I re-scanned the already-measured 203-array four-option battery
through the same estimator path. **36 arrays across 16 families already met the asymmetry
bar** (10 GPT-focal, 26 Claude-focal); 7 met the strict diffuse-OTHER prioritisation.

The mechanism hypothesis this produced, and which drove the battery design:

> The arrays that generate the asymmetry are the **near-equivalence** families —
> `fam_noise` ("no focal point by construction"), `fam_mirror` ("the same form up to
> isometry"), `F27_linecount`, `F36_split`. The earlier `q_*` factorial arrays
> failed because each had a corner that dominated every dimension (`closed_simple`,
> `one_thick`, `darkfill_darkedge`) and both models simply took it.

So: cue conflict, not designed salience. Every object favoured by at least one plausible
rule, none by all.

## 2. Battery

42 arrays, 6 mechanisms × 7 structurally distinct variants, 1,008 images, 217 cue-table
rows. Largest mechanism share **16.7%** (cap 25%).

Build-time assertions, all hard failures: exactly 4 objects; distinct object renders; every
object favoured by ≥1 rule and none by >2; ≥4 rules per array; on-palette colour; no
uniquely coloured object (cross-object hue-outlier test); minimum contrast vs panel ground;
no clipping; no overlapping elements (analytic — rows, blocks, rings); 24 distinct
permutation renders; every object in every screen position exactly 6 times.

### 2.1 Defects caught at render review — two of them in my own checks

| defect | fix |
|---|---|
| my "achromatic" test rejected the project's own blue-grey palette (`#3A4152` spread 0.094) | cross-object hue-outlier test, which is what "no uniquely coloured object" means |
| my ink measure counted the white backing disc of bounded texture patches — an unbounded patch looked 4× lighter than an identical bounded one | measure dark marks by luminance |
| one texture object was sparsest **and** coarsest **and** most regular — a dominant object | decoupled density from grain |
| rows of ≥5 elements rendered as chains of merged discs (pitch 0.32 vs 2r 0.45) | adaptive row radius + hard pairwise-distance assertion |
| numerosity elements clipped at the panel edge at low n | placement radius adapts to element radius |
| one cue table left an object un-credited | added the missing rule |

**Recorded, not fixed:** row elements are visibly smaller than ring/block/scatter ones, so
`linear` and "smallest elements" are confounded for row objects. Every row object is
still credited by the `linear` rule, so no object is un-credited.

## 3. Collection

| stage | calls | integrity | est. cost |
|---|---|---|---|
| discovery | **2,016** (42 × 2 × 24) | 2016/2016 parsed, 0 dupes, 0 missing, 0 checkpoint substitutions | ~$31 |
| confirmation | **1,584** (11 × 2 × 72) | 1584/1584 parsed, 0 missing, 0 checkpoint substitutions | ~$24 |

Prompt `d40ea45d` unchanged throughout; `gpt-5.5` / `claude-opus-5` returned on
every row. Confirmation n = 72 = 3 full permutation cycles, so every object sat in every
screen position exactly 18 times per cell. Discovery and confirmation live in separate
directories and are never pooled.

## 4. Confirmed candidates

`shr` = share of the **locked** object; `FC` = form consistency w.r.t. the locked
object; `ADV` = focal COPY identity match − focal–OTHER cross-model match.

| array | mechanism | focal | locked object | shr | FC | ADV | OTHER share | OTHER eff. support | OTHER subtype |
|---|---|---|---|---|---|---|---|---|---|
| `m4_contour_v4` | line_contour | **claude** | `crossing2_lw7` | 1.00 | 1.00 | **+0.958** | 0.96 | 1.09 | strong_competing_identity |
| `m4_contour_v4` | line_contour | **gpt** | `closed1_lw6` | 0.96 | 0.89 | **+0.877** | 1.00 | 1.00 | strong_competing_identity |
| `m5_numerosity_v4` | numerosity | **claude** | `n9_ring` | 1.00 | 1.00 | **+0.611** | 0.39 | 2.91 | weak_competing_identity |
| `m3_mirror_v0` | mirror | **claude** | `sym1` | 0.88 | 0.89 | **+0.473** | 0.69 | 1.83 | weak_competing_identity |
| `m2_texture_v2` | noise_texture | **claude** | `n90_r46_lattice` | 1.00 | 1.00 | **+0.444** | 0.56 | 2.02 | weak_competing_identity |
| `m5_numerosity_v2` | numerosity | **claude** | `n7_row` | 0.94 | 0.83 | **+0.419** | 0.51 | 2.05 | weak_competing_identity |
| `m3_mirror_v2` | mirror | **claude** | `sym3` | 0.96 | 0.83 | **+0.401** | 0.53 | 2.52 | diffuse_identity |
| `m3_mirror_v4` | mirror | **claude** | `sym1` | 0.93 | 0.83 | **+0.384** | 0.49 | 2.17 | diffuse_identity |
| `m1_nesting_v2` | nesting | **claude** | `n3_lw12_even_r92` | 0.99 | 0.94 | **+0.271** | 0.71 | 1.80 | weak_competing_identity |

**By focal model:** Claude 8, GPT 1.
**By mechanism:** {'nesting': 1, 'noise_texture': 1, 'mirror': 3, 'line_contour': 2, 'numerosity': 2}.
**By OTHER subtype:** {'weak_competing_identity': 5, 'diffuse_identity': 2, 'strong_competing_identity': 2}.

`m4_contour_v4` is the standout: it supplies **both focal directions on one array**
(Claude → `crossing2_lw7`, GPT → `closed1_lw6`) at a cross-model identity match of
**.083**. It is the only competing-form array in the set and the only source of a confirmed
GPT-focal case.

## 5. Failures

Three candidates failed, all on the **same single criterion** — focal form consistency below
.80 at n = 72:

| array | focal | locked object | shr | FC | ADV |
|---|---|---|---|---|---|
| `m1_nesting_v3` | gpt | `n5_lw5_geom_r92` | 0.83 | **0.56** | +0.413 |
| `m2_texture_v3` | claude | `n160_r34_clustered` | 0.81 | **0.67** | +0.389 |
| `m4_contour_v1` | gpt | `closed1_lw10` | 0.90 | **0.72** | +0.579 |

All three kept a strong modal share (.81–.90) and a large COPY-minus-OTHER advantage
(+.39 to +.58). They are **position-sensitive, not weak**. Two of the three are the only
other GPT-focal candidates, which is why the GPT side ends at one confirmed case.

## 6. Shared-policy controls

15 retained at discovery, spanning all 6 mechanisms — {'nesting': 1, 'noise_texture': 4, 'mirror': 2, 'line_contour': 3, 'numerosity': 1, 'size_rank': 4}.
No single family dominates. Per the brief these were **not** taken to confirmation.

## 7. Green assignment (not performed)

Green is assigned only after confirmation and must avoid the focal model's locked modal
identity and any strong OTHER modal identity. `green_eligibility.csv` records the
eligible objects: **all 8 confirmed arrays have ≥2 eligible objects**, so green assignment
is unblocked. `m4_contour_v4`, carrying two focal directions, has 2 eligible
(`segments6_lw3`, `continuous1_lw9`); the other seven have 3 each.

## 8. Recommendation

**Proceed.** The search meets its stopping rule — 9 confirmed asymmetric cases on 8 arrays
across 5 mechanisms, past the ≥6 arrays / ≥3 mechanisms bar, with every locked prediction
holding.

The one shortfall is **GPT-focal coverage: 1 confirmed case against a preference for 2.**
Two options:

1. **Relax nothing; re-target the two near-miss GPT arrays.** `m4_contour_v1` (FC .72)
   and `m1_nesting_v3` (FC .56) both held share and advantage; their failure is position
   sensitivity, a property of those particular objects rather than of the mechanism.
   Building 3–4 further `line_contour` and `nesting` variants that keep the winning
   object but vary its position-invariance costs ~4 arrays × 48 discovery calls ≈ $3.
2. **Accept a Claude-heavy design** and report the GPT direction as a single-array proof of
   concept resting on `m4_contour_v4`.

I recommend (1): cheap, targeted at a diagnosed cause, and it touches no threshold.

## 9. Deviations

- **Prompt hash.** The four-option prompt is `d40ea45d`; `3003ae1b` is its binary
  parent ("one of the **two** shapes") and cannot address a four-object array.
- **Confirmation n.** The analysis agent initially set n = 48 (2 cycles); corrected to the
  specified **72** (3 cycles, equally balanced) before anything locked.
- **Job-key collision.** The derived confirmation runner keyed jobs on (array, model, perm),
  which collides across the 3 cycles and would have silently deduplicated two-thirds of the
  run on resume. Re-keyed on trial, with a per-cell assertion that every permutation appears
  exactly 3 times.
- **FC quantisation.** At n = 24 form consistency can only take values 1 − k/6, so the .667
  borderline rung is stored as `0.6667`; a literal `.667` cutoff would have made the
  borderline band empty in practice.
- **Token usage not recorded** — `s4_common.run_stage` does not expose it and the frozen
  runner was not modified. Costs are estimates at the measured $0.0153/call anchor.
