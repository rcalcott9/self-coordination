# T1 — recommended visual sampling frame for Stage 1

Recommendation only. The lead freezes. No API calls were made in producing this.

---

## 1. Recommendation in one line

**`VIS-FRAME-41` — 41 arrays, one per family, drawn from the 203-array `study2_4opt_20260830`
battery by a fixed index rule that is blind to every model result. 41 families = 41 mechanisms,
no family represented twice, no array selected for any model property.**

The array list is `recommended_frame_arrays.csv` (which also carries the 82-array extension).

---

## 2. Every candidate source, and what it was conditioned on

This is the section the brief asks for. Each entry states the conditioning **explicitly**.

| candidate | arrays | conditioned on | admissible as a similarity frame? |
|---|---|---|---|
| **B203 batch 1** (`F01`–`F16`, 16 families x 8) | 128 | **NOTHING.** Written in one batch, frozen, rendered 2026-08-30 11:59–12:01, and the first API call against it was at 12:02. `make_battery.py`: "No stimulus was designed because a named model was observed to prefer a named feature… There is no generate-test-regenerate loop." T1 verified the render timestamps precede the run. | **YES — unconditioned.** |
| **B203 batch 2** (`F17`–`F41`, 25 families x 3) | 75 | **Aggregate battery yield, not a model relationship.** `make_battery2.py` was written after batch-1 Stage A and explicitly targets more families and more *weak-convention* items ("roughly half the families deliberately present four near-equivalent options… which is where battery 1's non-positional lows came from"). It names four batch-1 families as the pattern to imitate. It does **not** condition on GPT-vs-Claude, on which model is strong, or on divergence. | **YES, with a stated caveat.** Conditioning is on *within-model determinism*, which is exactly the quantity `MASTER_DESIGN` §5 requires be separated from similarity. Carry `batch` as a covariate and report the estimate with and without batch 2. |
| **B7 `stimuli4`** | 7 | **A model relationship, per array.** Every array was built from a binary result already labelled Track A (GPT/Claude divergent) or Track B (focal form policy vs OTHER positional policy). `BATTERY4_BUILD.md` names the source binary contrast and the focal model for each. | **NO.** |
| **B42 `stimuli5`** | 42 | **A model relationship, at the generative level.** `STIMULUS_SEARCH_REPORT.md` §1: the 6 mechanisms were chosen after "re-scanning the already-measured 203-array battery" and finding "36 arrays across 16 families already met the asymmetry bar"; the cue-conflict construction is an explicit attempt to manufacture GPT/Claude asymmetry. All 42 were then measured, so there is no *post-hoc* array selection — but the item universe is divergence-seeking by construction. | **NO as a frame.** Usable as a labelled contrast stratum. |
| **B8 `stimuli6`** | 8 | **Two named previously-failed arrays.** `GPT_EXPANSION_REPORT.md`: built to repair `m4_contour_v1` and `m1_nesting_v3`, both GPT-focal near-misses, plus a texture split. | **NO.** |
| **FROZEN_22** | 22 | **GPT-5.5 strength.** Selection rule, verbatim from `OLDER_CLAUDE_AUDIT.md` §4: arrays where "GPT-5.5 already holds a strong policy (share >= .75, FC >= .80)". | **NO — and this is the sharpest case.** It is the ONLY four-option set on which `claude-opus-4-7` and `claude-opus-4-6` exist. **A GPT-Claude similarity estimated on FROZEN_22 is conditioned on GPT being strong and is not an estimate of similarity.** |
| **B203 Stage C (29 arrays)** | 29 | HIGH (>= .75 and own−cross >= .15) or LOW (<= .45) — an extremity criterion on *both* tails. | **NO.** |
| **B203 manipulation check (8)** | 8 | HIGH / LOW / shared-control extremes. | **NO.** |
| **`stimuli_pilot` (15)** | 15 | Confirmed asymmetric candidates; stimuli carry a **green marker**. | **NO.** |
| **`proto4` / `noise4`** | 2 | Nothing — but **never rendered into a run**. Zero data. | Not usable (no measurements, and 2 arrays is not a frame). |

**Bottom line, stated plainly as the brief requires:** every four-option battery in this tree
except `study2_4opt_20260830` was selected or generated for a model relationship. A frame built
from `stimuli4`, `stimuli5`, `stimuli6`, FROZEN_22, the Stage C set, or the strategic pilot set
**inherits a selection criterion and cannot estimate policy similarity.** B203 is the only
defensible source, and within it batch 1 is the only fully unconditioned stratum.

---

## 3. The frame

### `VIS-FRAME-41` (primary)

- **41 arrays**, one per B203 family.
- **Member selection rule, fixed a priori and blind to results:** the middle rung of the
  family's parametric ladder, index `(n_members − 1) // 2`. That is member **m3** for the 16
  eight-member batch-1 families and member **m1** for the 25 three-member batch-2 families.
  The rule is a property of the generator's parameter sweep, not of any measurement.
- **41 mechanisms, one array each.** No family contributes twice, so family — the unit of
  independence used throughout this tree — is not double-counted.
- **Strata:** `batch1` (16 arrays, unconditioned) and `batch2` (25 arrays, conditioned on
  aggregate weak-convention yield). Both carried as a covariate.
- Rendered images unchanged since 2026-08-30; prompt `d40ea45d`; permutation schedule
  `s4_common.position_schedule(48)` = 2 complete 24-permutation cycles, giving every canonical
  option every screen position exactly 12 times, which is precisely the `n = 48` floor's
  justification in `MASTER_DESIGN` §5.

### Extension ladder, in the order the lead should spend into

| frame | arrays | rule | when |
|---|---|---|---|
| `VIS-FRAME-41` | 41 | 1 per family, middle rung | **default** |
| `VIS-FRAME-82` | 82 | 2 per family, rungs at `(n−1)//3` and `2(n−1)//3` | if the panel is <= 4 checkpoints, or budget frees up |
| `VIS-FRAME-203` | 203 | the whole battery | only if the panel collapses to 2 checkpoints |
| `VIS-FRAME-16` | 16 | batch 1 only, 1 per family | **fallback if batch 2's determinism conditioning is judged fatal** — fully unconditioned, but 16 mechanisms and no batch covariate |

Reducing *within* a mechanism before reducing the number of mechanisms is exactly the tradeoff
order in `MASTER_DESIGN` §6 (item cuts before panel cuts, redundant-within-mechanism first).
`VIS-FRAME-41` is the maximal application of that rule: it removes **all** within-family
redundancy and keeps **all** 41 mechanisms.

---

## 4. What exists, what is missing, what it costs

Per-cell detail in `missing_cells.csv` (1,968 rows: both frames x T4's 16 vision-eligible
checkpoints).

At `VIS-FRAME-41` x the 16 vision-capable checkpoints in T4's panel:

- **PARTIAL: 82 cells** — `gpt-5.5-2026-04-23` and `claude-opus-5`, each with an existing
  n = 24, prompt `d40ea45d`, exact 24-permutation balance, on the exact images.
- **MISSING: 574 cells** — every other checkpoint, on every frame array.
- **`claude-opus-4-6` and `claude-opus-4-7` have four-option data but ZERO overlap with this
  frame.** Their 4-option rows are entirely on FROZEN_22, which is GPT-strong-selected.
- **No GPT checkpoint other than `gpt-5.5-2026-04-23` has ever produced a four-option response
  in this tree.** The entire GPT vintage ladder at four options must be collected from scratch.

Cost at T4's per-visual-call estimates, `VIS-FRAME-41`, n = 48 per cell:

| checkpoint | additional calls | est. cost |
|---|---|---|
| `gpt-5.5-2026-04-23` (top-up 24) | 984 | $7.48 |
| `claude-opus-5` (top-up 24) | 984 | $5.05 |
| any other `gpt-5.x` reasoning model | 1,968 | $14.96 |
| any `gpt-4x` sampling model | 1,968 | $12.00 |
| `claude-opus-4-6 / 4-7 / 4-8` | 1,968 | $9.90–$10.10 |
| `claude-opus-4-5-20251101` | 1,968 | $10.82 (temperature surface) |
| `claude-sonnet-4-5` | 1,968 | $6.49 |
| `claude-haiku-4-5` | 1,968 | $2.16 |
| **all 16** | 29,520 | **$169.95 — does not fit** |

Two illustrative panels that **do** fit (panel choice is T4's, not T1's):

- **3 GPT + 3 Claude, top-ups reused:** `gpt-4o` + `gpt-5` + `gpt-5.5`(top-up) + `opus-4-6` +
  `opus-4-8` + `opus-5`(top-up) = **$60.7**.
- **3 GPT + 3 Claude, fresh n = 48 on all six** (no pooling across dates):
  `gpt-4o` $12.00 + `gpt-5` $14.96 + `gpt-5.5` $14.96 + `opus-4-6` $10.10 + `opus-4-8` $10.10 +
  `opus-5` $10.10 = **$72.2**.

Both leave $60–$75 of the $135 planned ceiling for the code domain.

**T1 recommends the fresh-n=48 option**, at a $11.50 premium, for two reasons: (a) it avoids
pooling a 2026-08-30 block with a 2026-09 block on the two most load-bearing checkpoints, where
serving-stack drift would sit exactly on the recent end of the vintage trend; and (b) it makes
the existing n = 24 a **free within-checkpoint stability check** — a 9-day retest on the same
images and the same prompt, which nothing else in this study supplies. If the lead prefers the
top-up, the two blocks must be tested for homogeneity (per-array permutation test on the 24 vs
24 choice distributions) and the block indicator retained, never silently merged.

---

## 5. Constraints this frame must be run under

1. **Do not pool `V4A-BLIND` with `V4A-SELECTED`.** B7/B42/B8/FROZEN_22 cells are technically
   `V4A`-compatible (same images pipeline, same prompt, same balance, same parser) and will
   merge cleanly if anyone tries. They must be carried as a separately labelled stratum and
   never entered into the central similarity estimate.
2. **Determinism adjustment is mandatory, not optional.** Median effective support on B203 is
   1.28 (GPT) and 1.09 (Claude) out of 4; on B42 Claude is at 1.00 on the median array. Raw
   cross-model match on this battery is dominated by how deterministic Claude is. Report
   `within_model_match` per cell alongside every similarity number, and report the
   determinism-adjusted statistic as the headline.
3. **Measure position sensitivity, do not assume it away.** 3 of 406 B203 cells reach
   `position_modal_share` >= .75 (max .917). The existing claim in
   `DISCOVERY4_REPORT.md` §4.1 that no four-option positional policy exists was derived from 14
   cells and is an over-generalisation.
4. **n = 48, never 24.** At n = 24 form consistency is quantised to 1/6 and the tree already
   contains two documented cases (`GPT_POSITION_DIAGNOSIS.md`) of position-sensitive arrays
   passing a discovery screen because 6 trials/slot could not detect it.
5. **Set `thinking` explicitly on every Claude call** (per `DECISION_LOG` D-015(a)). All
   existing four-option data was collected with `thinking={"type":"adaptive","display":
   "summarized"}` set explicitly in `s4_common.py:281`; an omission would silently flip
   behaviour between Opus 4.x and Opus 5 and place the discontinuity on the newest checkpoint.
6. **Freeze a B203 battery hash and add a `mechanism` column** before collection. The battery
   currently has neither. T1's content hash of the 4,872 perm images is
   `56e4eed8d6f5948146d4c5d6192230fe8c424ff67acab8d32f192706ebb11d47`.
7. **`claude-opus-4-5-20251101` is a separate compatibility stratum**, not an availability
   failure — it rejects adaptive thinking with HTTP 400 and would need the temperature surface.
   Include it only with the stratum labelled, per `MASTER_DESIGN` §4.

---

## 6. Honest statement of what this frame can and cannot support

**Can:** an estimate of pairwise policy similarity across checkpoints on a fixed,
unconditioned four-option visual battery of 41 mechanisms; a descriptive comparison of that
similarity against checkpoint vintage; a determinism-adjusted version of both.

**Cannot:** a claim about general convergence (this is one battery, one modality, one prompt);
a causal attribution to training; anything about divergent conventions — §4a of the tree's own
durability inventory shows that when both models hold a strong convention on B203 they agree
90 times out of 92, and T1's recomputation confirms modal agreement of **.764** with mean
expected cross-match **.698** across all 203 arrays. The interesting Stage 1 result on this
frame will most likely be *how high similarity already is*, and how much of that is shared
determinism rather than shared convention. That is a finding, not a problem, and the frame is
built so it can be reported as one.
