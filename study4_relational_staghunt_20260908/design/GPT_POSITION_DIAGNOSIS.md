# Phase 1 — GPT position-sensitivity diagnosis

Written before any variant was generated. Sources: confirmation run (n = 72, 18 trials per
screen position) and discovery run (n = 24, 6 per position).

## 0. Two corrections to the brief

**There is no third failed GPT-focal candidate.** The three confirmation failures were
`m1_nesting_v3` (GPT), `m4_contour_v1` (GPT) and `m2_texture_v3` — which is
**Claude-focal**. Only two repairable GPT targets exist. `m2_texture_v3` is diagnosed
below anyway, and `noise_texture` is carried forward as an independent *source*
mechanism for new GPT-focal arrays, not as a repairable candidate.

**"At least 8 GPT targets" is not reachable in this round.** Observed rates: 42 arrays → 3
GPT-focal candidates (7.1%) → 1 confirmed, i.e. **2.4% end-to-end**. Reaching +7 at that
rate needs roughly 290 arrays (~$215 of discovery alone). Targeted repair should beat the
blind rate substantially, but 6–10 arrays realistically yields +2 to +4 — which is what the
brief's own stopping target says. This round measures the repair yield; a second round can
then be sized from that instead of from the blind rate.

## 1. The conditional-choice tables

P(focal chooses the locked object | locked object displayed at screen position p), n = 18
per cell at confirmation.

### `m4_contour_v1` — GPT, locked `closed1_lw10`

| position | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| P(locked) | **0.72** | 0.94 | 1.00 | 0.94 |
| replaced by | crossing4_lw5 ×5 | ×1 | — | ×1 |

### `m1_nesting_v3` — GPT, locked `n5_lw5_geom_r92`

| position | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| P(locked) | **0.56** | 1.00 | 1.00 | 0.78 |
| replaced by | n2_lw9_even ×8 | — | — | ×4 |

### `m2_texture_v3` — Claude, locked `n160_r34_clustered`

| position | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| P(locked) | **0.67** | 0.83 | 0.72 | 1.00 |
| replaced by | n60_r56_lattice ×6 | ×3 | ×5 | — |

## 2. What the tables show

**(a) The loss concentrates at screen position 1 in all three arrays** — 0.72 / 0.56 / 0.67
against 0.94–1.00 at the best position. Position 1 is the leftmost panel, i.e. first in
reading order and adjacent to only one neighbour.

**(b) A single specific competitor absorbs the entire loss in each array** — `crossing4_lw5`,
`n2_lw9_even_r92`, `n60_r56_lattice` respectively. Not a diffuse spread across the
other three objects. This is a **competition-context effect**, not a generic position bias:
the target loses to one particular rival, and only when it sits at the edge.

**(c) The discovery screen could not have caught this.** All three arrays showed discovery
FC = **0.833**; confirmation revealed **0.56–0.72**. At n = 24 there are 6 trials per slot,
so FC is quantised to 1/6 and its sampling error is large — a cell that truly sits at 0.56
frequently reads 0.83 on 6 draws.

## 3. Diagnosis, against the four candidate causes

| candidate cause | verdict |
|---|---|
| rendering / layout problem | **Contributing, in nesting only.** `m1_nesting_v3` has unmatched extent: outer radii .62, .98, .92, .92, so object 0 is a visible size outlier and the objects differ in visual mass. Contour and texture objects are well centred and comparable. |
| competition-context effect | **Primary.** One named rival absorbs the whole loss in every array (§2b). |
| intrinsic position heuristic | **Secondary and real.** The edge position is position 1 in all three, across three different mechanisms and both models. |
| sampling noise | **Rejected as the explanation of the failure**, but it *is* the explanation of why discovery passed them: discovery FC at 6 trials/slot is too noisy to screen on (§2c). |

**Summary.** These arrays are not weak — all three kept modal share .81–.90 and
COPY-minus-OTHER advantage +.39 to +.58. They are **position-sensitive at one edge slot
against one specific rival**, and the discovery screen lacked the power to detect it.

## 4. What this implies for the repair

1. **Equalise extent and visual mass across all four objects** — same outer radius, matched
   ink. Directly addresses the nesting layout confound.
2. **Weaken the specific rival that absorbs the loss** (`crossing4`, the thick 2-ring,
   the coarse lattice) without making the locked object an odd-one-out.
3. **Modestly strengthen the locked object's distinguishing cue**, one dimension only.
4. **Remove any directional or orientation cue** that could interact with slot order.
5. **Raise discovery n so FC is screened with real power.** This is the one change that
   addresses the *screen* rather than the stimuli, and §2c says it is the leak.
