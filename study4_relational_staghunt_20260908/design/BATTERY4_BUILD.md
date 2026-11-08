# Study 4 four-object arrays — build record

Built `2026-09-08`. Generator `code/make_battery4.py`. Output `stimuli4/`.
**7 arrays × 4 objects × 24 permutations = 168 images.**
`BATTERY4_SHA256.txt` = `14e5ec0b5418d5a8e9d5cc37bdb8d78ab6d4c93b25b156b5300adecdc897ec27`

**Not yet measured.** No API calls have been made against these arrays.

---

## 1. What was built

Each array crosses **two factors** rather than lengthening a perceptual ladder — the rule
from `STIMULUS_HUNT_PLAN.md` v2 §4. A ladder produces endpoint-only responding
(`F10_curvature` put 99.2% of draws on its two extreme rungs); a 2×2 gives four defensible
corners and, as a bonus, the model's modal corner identifies *which* factor its convention
tracks.

| array | track | mechanism | from | objects |
|---|---|---|---|---|
| `q_closure_cplx` | B | closure × complexity | `c_open_cplx` (compete) | open_simple, closed_simple, open_complex, closed_complex |
| `q_nesting_weight` | B | ring count × stroke weight | `y7_nested_hi` (Y7_nesting) | many_thin, many_thick, one_thin, one_thick |
| `q_sizerank_tone` | B | size-gradient × tone-gradient | `y17_sizerank_hi` (Y17_size_rank) | size_up_tone_up, size_up_tone_down, size_down_tone_up, size_down_tone_down |
| `q_grain_arrange` | B | grain × arrangement | `d_texture` (D_density) — **Claude-focal** | fine_random, fine_periodic, coarse_random, coarse_periodic |
| `q_tone_fill_edge` | A | fill tone × edge tone | `x8_contr_c` (X8_contrast) | lightfill_lightedge, lightfill_darkedge, darkfill_lightedge, darkfill_darkedge |
| `q_chevron_4way` | A | four canonical orientations | `a_chev_ud` (A_semantic) | up, down, left, right |
| `q_numer_arrange` | A | count × arrangement | `y9_numer_lo` (Y9_numerosity) | few_block, few_ring, many_block, many_ring |

`q_closure_cplx` is the one that also **breaks a confound**: the binary contrast varied
closure and complexity together, so GPT's `closed_cplx` convention could have been about
either. The 2×2 separates them.

Geometry, palette and panel ground are inherited from `study2_4opt/make_battery.py`, and the
per-array `manifest.json` maps permutation → item order in the same format, so the existing
4-option runner reads these unchanged.

---

## 2. Three defects caught at render review, and the assertions added for them

The first build passed every check I had written and was still wrong in three places. Each
fix added a permanent assertion.

**(a) Second factor swamping the first — `q_tone_stroke` → `q_tone_fill_edge`.**
v1 crossed fill tone with *stroke weight*. Stroke weight is far more salient than a subtle
tone difference, so the array would have been organised on stroke and the tone divergence
that motivates it (GPT `darker` / Claude `lighter` on `x8_contr_c`) swamped — the F10 failure
in a new guise. Both factors are now tonal (fill × edge) and comparable in salience.

**(b) Fill indistinguishable from the panel ground.** v1 used `VLIGHT` `#E8EAEE` against
`PANEL` `#F1F2F4` — a luminance delta of ~0.02, and the disc nearly vanished into its own
panel. → `check_ground_contrast()` asserts every declared fill tone differs from the ground
by ≥ 0.035 luminance.

**(c) Overlapping elements, in two separate layouts.** The size-rank row merged its two
largest neighbours into one blob, and the 9-element block overlapped heavily.
→ `check_no_overlap()` now checks the size-rank row, the element blocks and the element rings
analytically, before any image is written.

The size-rank second factor was also changed from element **shape** (disc vs square, far more
salient than rank direction) to a **tone gradient** — two ordered cues of comparable
salience, which is what the crossing needs.

### Full assertion set (all hard failures, run before any image is written)

1. exactly 4 objects, 4 distinct object names
2. no two objects render byte-identically
3. per-object ink within [0.45×, 2.10×] of the array mean — observed range **0.93–1.08**
4. every fill tone ≥ 0.035 luminance from the panel ground
5. no touching or overlapping elements (rows, blocks, rings)
6. `nested()` draws exactly the requested ring count
7. all 24 permutation renders pairwise distinct
8. deterministic — fixed seeds, no unseeded RNG

---

## 3. What must happen before these enter Study 4

Per plan §5, **a binary result nominates a mechanism; it does not certify a four-object
policy.** Premeasurement must use these exact arrays:

- all four objects present, **no green marker**;
- the same coordination-policy prompt (4-option arity);
- all 24 permutations balanced via `position_schedule`;
- **canonical object identity and screen position both recorded** on every trial;
- discovery n = 24/model/array, confirmation n ≥ 60/model/array in a **separate** file,
  never pooled.

Two things have to survive that are only hypotheses right now:

- whether each **focal** model keeps its form policy over four objects, and
- whether each **OTHER** model keeps its positional policy — the projected four-option
  identity-match floor of **.25** is carried in the inventory as
  `projected_floor_status = "HYPOTHESIS - requires 4-option premeasurement"`. The binary data
  already show residual identity preference is real and signed in both directions
  (observed cross-model identity match .267–.717 against a .50 binary floor), so the .25 is a
  reference point, not a guarantee.

Green is assigned only **after** four-object policies are established, to an object that is
neither model's modal choice, and coordination is never scored by screen position.

Cost for premeasurement, at the measured $0.0153/call anchor:
7 arrays × 2 models × 24 = **336 calls ≈ $5** for discovery;
7 × 2 × 60 = **840 calls ≈ $13** for confirmation on whatever survives.
