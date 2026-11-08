# GPT-focal expansion — result

Battery `stimuli6` sha256 `5a7d0a0d…`; discovery `discovery6_20260909_014626` (768 calls, n = 48);
confirmation `confirm6_20260909_015106` (576 calls, n = 72). Diagnosis: `design/GPT_POSITION_DIAGNOSIS.md`.

## VERDICT — the expansion did not add a GPT target

**0 GPT-focal candidates promoted at discovery; 0 confirmed.** The stopping target (≥2
additional confirmed GPT-focal arrays) is **not met**. Study 4 still stands at **1 confirmed
GPT-focal array** (`m4_contour_v4`) against **9 Claude-focal**.

The expansion did add one Claude-focal array (`r_nesting_v2`), which was not its purpose.

## Why it failed — the repair removed the effect it was protecting

This is the substantive result, and it argues the two failed arrays were **not repairable by
layout normalisation**.

| mechanism | intended repair | what happened |
|---|---|---|
| line_contour | weaken the radial-spoke rival, equalise extent | Both models converged on `closed_ring` at .98–1.00, cross-model match **.979–1.000**. The array became a **shared control**. Weakening the competition removed the asymmetry along with the position sensitivity. |
| nesting | equalise outer extent (v3 had radii .62/.98/.92/.92) | GPT's preference **flipped to `thick_pair`** — the former rival — in 2 of 3 variants. GPT's original preference for `geom_rings` was partly constituted by the extent imbalance the diagnosis told me to normalise. |
| noise_texture | independent third mechanism, two lattices so regularity is not unique | GPT did take the intended `fine_lattice` and Claude took `coarse_lattice` — a genuine split at cross-match .23/.28 — but far too weak (GPT share .52/.58, FC .25/.42). |

**Generalisation:** in these mechanisms the position sensitivity and the GPT-focal asymmetry
are not separable defects. The competition-context imbalance that produces the asymmetry is
the same imbalance that produces the edge-slot loss. Normalising one removes the other.

## Discovery (n = 48, 2 full cycles)

Ran at n = 48 rather than the briefed 24 — a deliberate deviation, because the diagnosis
(§2c) established that FC at 6 trials/slot is too noisy to screen on and was the reason the
original arrays passed discovery. At 12 trials/slot the screen is materially sharper.
768 calls, 768/768 parsed, 0 failures, every object in every position exactly 12× per cell.

| array | GPT modal | shr | FC | Claude modal | shr | cross | GPT adv | intended object? |
|---|---|---|---|---|---|---|---|---|
| `r_line_contour_v0` | closed_ring | .98 | .92 | closed_ring | 1.00 | .979 | −.021 | yes |
| `r_line_contour_v1` | closed_ring | .98 | .92 | closed_ring | 1.00 | .979 | −.021 | yes |
| `r_line_contour_v2` | closed_ring | 1.00 | 1.00 | closed_ring | 1.00 | 1.000 | +.000 | yes |
| `r_nesting_v0` | **thick_pair** | .73 | .75 | thick_pair | 1.00 | .729 | −.133 | **no** |
| `r_nesting_v1` | geom_rings | .62 | .50 | thick_pair | .85 | .411 | +.110 | yes |
| `r_nesting_v2` | **thick_pair** | .54 | .25 | thick_pair | .96 | .538 | −.045 | **no** |
| `r_noise_texture_v0` | fine_lattice | .52 | .42 | coarse_lattice | .83 | .226 | +.158 | yes |
| `r_noise_texture_v1` | fine_lattice | .58 | .25 | coarse_lattice | .92 | .278 | +.141 | yes |

Promoted: 4 Claude-focal, 3 shared controls, **0 GPT-focal**. No threshold was relaxed.

## Confirmation (n = 72)

576 calls, 576/576 parsed, 0 failures. All 4 locked predictions held. **1 of 4 confirmed.**

| array | focal | locked | shr | FC | ADV | verdict |
|---|---|---|---|---|---|---|
| `r_nesting_v2` | claude | thick_pair | .97 | .89 | +.353 | **CONFIRMED** |
| `r_noise_texture_v1` | claude | coarse_lattice | .92 | .78 | +.601 | failed — FC .78 |
| `r_nesting_v0` | claude | thick_pair | 1.00 | 1.00 | +.250 | failed — Claude and GPT share the strong convention |
| `r_nesting_v1` | claude | thick_pair | .81 | .78 | +.242 | failed — FC and advantage |

## Updated Study 4 confirmed table

**10 confirmed cases on 9 distinct arrays: 1 GPT-focal, 9 Claude-focal.**
Full table in `design/STUDY4_CONFIRMED_TABLE.csv`.

- GPT mechanisms: line_contour (1).
- Claude mechanisms: mirror (3), numerosity (2), nesting (2), line_contour (1), noise_texture (1).
- **Arrays supporting both focal directions: 1** — `m4_contour_v4`.

## Recommendation — GPT coverage is NOT sufficient to proceed

A GPT-focal arm resting on a single array in a single mechanism cannot support a relational
claim; any GPT result would be a statement about `m4_contour_v4`, not about GPT.

Three routes, in order of what the evidence supports:

1. **Stop repairing and start from what worked.** `m4_contour_v4` is the only GPT success
   and it is a **strong-competing** array — GPT and Claude hold *different strong*
   conventions. Every repair here pushed toward removing competition; the one success has
   maximal competition. Generate 8–10 arrays deliberately built as two-strong-rivals
   (not one target plus weakened distractors), across contour, mirror and texture.
   ~10 × 2 × 48 = 960 calls ≈ $15.
2. **Strengthen the texture split rather than equalising it.** Texture is the only mechanism
   where the two models chose *different* objects (`fine_lattice` vs
   `coarse_lattice`). The cue is too weak, and the fix is to widen the grain contrast —
   the opposite of what was done here. ~4 arrays ≈ $6.
3. **Accept an asymmetric design.** Run Study 4 with a strong Claude-focal arm (9 arrays,
   5 mechanisms) and report GPT as a single-array proof of concept, stating plainly that the
   GPT direction is not established.

Route 1 is the one the data actually points at. It is also the opposite of this round's
strategy, which is why this round was worth running.

## Deviations

- **Discovery n = 48, not 24** — deliberate, driven by the Phase 1 diagnosis; recorded above.
- **No third GPT-focal failure existed** — the brief assumed three; only two were GPT-focal
  (`m2_texture_v3` is Claude-focal). Texture was used as a source mechanism instead.
- **"At least 8 GPT targets" was flagged as unreachable before spending** and remains so:
  the blind end-to-end rate is 2.4%, and the targeted repair rate measured here is **0%**.
- **A dupe-counter false alarm**: the integrity check keys on (array, model, permutation),
  which legitimately repeats at 2 cycles; verified as exactly 2 per permutation with correct
  position balance, not a real duplication.
- **A battery5 defect found and fixed locally**: the lattice took the first n raster-scan
  points, biasing the mark centroid 0.029 off centre. Corrected in battery6 only; battery5
  and its results were not touched.
