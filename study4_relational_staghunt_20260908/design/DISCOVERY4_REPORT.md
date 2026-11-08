# Study 4 — four-object discovery premeasure: report

Run `discovery_4opt_20260909_003952`. **336 calls, 2026-09-08.**
Machine-readable inventory: `discovery4_inventory.csv` / `.json` (7 arrays × all metrics).
Track table: `discovery4_tracks.csv`. Integrity: `trial_integrity.json`.
Locked candidates: `CONFIRMATION_CANDIDATES_LOCKED.json` (sha256[:16] `3d8d774f78b3cb96`).

**Headline: the hypothesised policies did not survive the move to four objects.
Track A = 0 arrays. Track B = 0 arrays. Shared control = 1. Six arrays fail.**

---

## 1. Preflight

| check | result |
|---|---|
| 7 arrays / 4 objects / 24 perms / 168 images | PASS |
| battery sha256 `14e5ec0b` | PASS |
| all 7 array IDs | PASS |
| every object × every position = 6 over 24 perms | PASS |
| no green marker (chromatic-pixel scan, 28 images) | PASS — green-ish fraction 0.00000 |
| object identity stable across permutations (672 panel crops) | PASS |
| 4 objects mutually distinct at every position | PASS |
| checkpoints `gpt-5.5` / `claude-opus-5` | PASS, returned on 336/336 rows |
| identity **and** screen position recorded | PASS |
| new run directory, nothing overwritten | PASS |

### 1.1 Two recorded deviations

**Prompt hash.** The brief asked to verify hash `3003ae1b` *and* that the existing
four-option prompt is used unchanged. These are mutually exclusive: `3003ae1b` is the
**binary** prompt ("one of the **two** shapes") and cannot address a four-object array. The
four-option prompt is **`d40ea45d`**, its arity-adapted sibling — `s4_common` records the
lineage explicitly. `d40ea45d` was used unchanged and is stamped on every row.

**Token usage unavailable.** `s4_common.run_stage` records raw text, reasoning, returned
checkpoint, timing and errors, but not usage; `ASK[]` does not return it. The frozen runner
was not modified. Cost remains an estimate (~$5 at the $0.0153/call anchor).

---

## 2. Trial integrity

| | |
|---|---|
| rows | **336 / 336** |
| transport ok | **336** |
| parsed ok | **336** — zero parse failures |
| duplicate (array, model, permutation) | **0** |
| missing trials | **0** — every cell exactly 24 |
| checkpoint substitutions | **0** |

No stop condition was triggered.

---

## 3. Per-cell results (n = 24, all 24 permutations once)

Four-option chance: modal share .25, dyadic identity match .25.
`FC` = form consistency, generalised to four slots as `1 − (max − min)` of
`P(choose modal object | modal object displayed at slot p)`.

| array | model | modal object | share | margin | FC | identity match | pos modal | pos share | live | policy |
|---|---|---|---|---|---|---|---|---|---|---|
| `q_closure_cplx` | GPT | **closed_simple** | 1.000 | +1.000 | 1.00 | 1.000 | 2 | .250 | **1** | form |
| | Claude | **closed_simple** | 1.000 | +1.000 | 1.00 | 1.000 | 2 | .250 | **1** | form |
| `q_nesting_weight` | GPT | many_thick | .667 | +.417 | 0.50 | .493 | 3 | .417 | 3 | mixed |
| | Claude | **one_thick** | **1.000** | +1.000 | **1.00** | **1.000** | 4 | .250 | 1 | form |
| `q_sizerank_tone` | GPT | size_up_tone_up | .542 | +.083 | 0.67 | .482 | 2 | .333 | 2 | mixed |
| | Claude | size_up_tone_up | .792 | +.625 | 0.67 | .641 | 1 | .417 | 2 | mixed |
| `q_grain_arrange` | GPT | fine_periodic | .792 | +.583 | 0.50 | .656 | 4 | .333 | 2 | mixed |
| | Claude | coarse_periodic | .500 | +.125 | 0.33 | .380 | 4 | .375 | 3 | mixed |
| `q_tone_fill_edge` | GPT | darkfill_darkedge | .750 | +.500 | 0.33 | .609 | 3 | .375 | 2 | mixed |
| | Claude | darkfill_darkedge | .542 | +.083 | 0.33 | .482 | 4 | .458 | 2 | mixed |
| `q_chevron_4way` | GPT | **up** | .958 | +.917 | **0.83** | .917 | 4 | .292 | 1 | form |
| | Claude | up | .833 | +.750 | 0.50 | .696 | 1 | .292 | 3 | mixed |
| `q_numer_arrange` | GPT | many_block | .792 | +.625 | 0.67 | .641 | 3 | .333 | 2 | mixed |
| | Claude | many_ring | .542 | +.083 | 0.50 | .482 | 2 | .375 | 2 | mixed |

### 3.1 Array-level

| array | same modal | cross-model identity match | GPT COPY−OTHER | Claude COPY−OTHER |
|---|---|---|---|---|
| `q_closure_cplx` | YES | 1.000 | +.000 | +.000 |
| `q_nesting_weight` | **NO** | **.083** | +.409 | **+.917** |
| `q_sizerank_tone` | YES | .448 | +.034 | +.193 |
| `q_grain_arrange` | **NO** | .401 | +.255 | −.021 |
| `q_tone_fill_edge` | YES | .521 | +.088 | −.039 |
| `q_chevron_4way` | YES | .802 | +.115 | −.106 |
| `q_numer_arrange` | **NO** | .453 | +.188 | +.029 |

---

## 4. The two findings that decide the outcome

### 4.1 Position policies did not survive — Track B has no OTHER side

`pos_modal_share` across all 14 cells: min .250, median .333, **max .458**.
**0 of 14 reach .75.** Chance is .25.

At two options, "always take the right-hand shape" was available and used — Claude ran it at
`pos_modal_share` **1.000** on `c_open_cplx`. At four options nobody does. A four-slot
positional rule is apparently not a natural fallback in the way a two-slot one is.

**Track B is empty by measurement, not by threshold choice.** No relaxation of the `.75`
position bar rescues it: the highest observed value is .458, barely above chance.

### 4.2 Focal form policies mostly did not transfer either

Only **4 of 14** cells reach FC ≥ .80; median FC is 0.58. Comparing each array's focal side
against its binary source:

| array | binary focal | binary share / FC | four-object share / FC |
|---|---|---|---|
| `q_closure_cplx` | `c_open_cplx` GPT | .967 / .93 | **1.000 / 1.00** ✓ |
| `q_chevron_4way` | `a_chev_ud` GPT | .900 / .80 | **.958 / 0.83** ✓ |
| `q_nesting_weight` | `y7_nested_hi` GPT | .967 / .93 | .667 / 0.50 ✗ |
| `q_sizerank_tone` | `y17_sizerank_hi` GPT | 1.000 / 1.00 | .542 / 0.67 ✗ |
| `q_grain_arrange` | `d_texture` Claude | .917 / .90 | .500 / 0.33 ✗ |
| `q_tone_fill_edge` | `x8_contr_c` GPT | 1.000 / 1.00 | .750 / 0.33 ✗ |
| `q_numer_arrange` | `y9_numer_lo` GPT | 1.000 / 1.00 | .792 / 0.67 ✗ |

Five of seven focal policies degraded substantially. This is exactly the risk the plan
flagged: **a binary result nominates a mechanism; it does not certify a four-object policy.**

### 4.3 Effective support — four displayed objects, rarely four live ones

Objects receiving ≥ 5% of draws: **1 object in 4 cells, 2 in 7 cells, 3 in 3 cells, 4 in
none.** Median 2.

Crossed factors did **not** solve the dead-interior problem that killed `F10_curvature`.
Models reduce the 2×2 to a one-dimensional preference and take a corner.

### 4.4 A precision caveat that cuts the other way

At n = 24 with all 24 permutations, FC rests on **6 trials per slot**, so it is quantised to
1/6 steps — the observed values are exactly {0.33, 0.50, 0.67, 0.83, 1.00}. The `.80` bar
therefore means "slot spread ≤ 1/6", which is demanding at this n.

Three cells sit at FC = 0.667, **one step below the bar**: `q_sizerank_tone` (both models)
and `q_numer_arrange` (GPT). Those classifications are the least secure in the table and
could move at higher n. This does **not** affect §4.1 — position shares are far from the bar
in absolute terms, not by one quantisation step.

---

## 5. Two substantive results from breaking confounds

**`q_closure_cplx` answers the question it was built to ask.** The binary `c_open_cplx`
confounded closure with complexity, so GPT's `closed_cplx` preference could have been about
either. Offered the four corners, **both models take `closed_simple` 24/24**. The operative
factor is **closure, not complexity** — and once a closed *simple* option exists, complexity
is not wanted. Clean answer, negative for the study's purposes.

**The two Track-A divergences were binary artifacts.** `a_chev_ud` (GPT `up` / Claude
`down`) becomes GPT `up` .958 / Claude `up` .833 with four orientations — cross-model match
.802. `x8_contr_c` (GPT `darker` / Claude `lighter`) becomes both on `darkfill_darkedge`.
Neither divergence survives once the forced binary choice is removed.

---

## 6. Promotion, at .75 and at .90

| array | hypothesised | at ≥ .75 | at ≥ .90 | why |
|---|---|---|---|---|
| `q_closure_cplx` | B | **shared_control** | **shared_control** | both form-driven, same modal object |
| `q_nesting_weight` | B | fail | fail | GPT share .667 < .75 and **mixed** (FC 0.50, pos .417) — diffuse, not position-driven |
| `q_sizerank_tone` | B | fail | fail | both mixed (FC 0.67); GPT share .542 |
| `q_grain_arrange` | B | fail | fail | both mixed; Claude share .500 — *exploratory array, expected fragile* |
| `q_tone_fill_edge` | A | fail | fail | both mixed (FC 0.33); Claude share .542 |
| `q_chevron_4way` | A | fail | fail | same modal object, and Claude FC 0.50 < .80 |
| `q_numer_arrange` | A | fail | fail | both mixed; Claude share .542 |

Track assignment is **identical at .75 and .90**. No threshold was relaxed.

### 6.1 The one near-miss, reported not promoted

**`q_nesting_weight`** carries the largest asymmetry measured: Claude is form-driven and
perfect (`one_thick`, share **1.000**, FC **1.00**, live 1), GPT is spread over three
objects (`many_thick` .667, FC 0.50), cross-model identity match **.083**, and Claude's
COPY-minus-OTHER advantage is **+0.917**.

It fails Track B on one criterion only: GPT is **diffuse**, not position-driven
(`pos_modal_share` .417 < .75). That is precisely the distinction drawn in the plan — a
position policy is nontransferable *and stable*; a diffuse partner is nontransferable and
*unstable*. Promoting it would silently redefine Track B.

If a **Track B′ — focal form policy vs OTHER diffuse** is wanted, this array is a strong
candidate and the decision should be made explicitly, in advance, not by relaxing B.

---

## 7. Locked confirmation candidates

`CONFIRMATION_CANDIDATES_LOCKED.json`, sha256[:16] **`3d8d774f78b3cb96`** — **1 record**:

- `q_closure_cplx`, track **shared_control**, focal both, predicted canonical modal object
  **`closed_simple`** for both models, with the discovery statistics and the intended
  confirmation tests. Stable at .90.

Confirmation may not redefine the predicted modal identity, focal direction, or track.
Unconstrained confirmation modes, if any, are to be reported separately.

**Note on the locked record's value.** This is a ceiling control: both models are at 24/24
with **one live object**. Confirming it re-verifies a ceiling and carries little information.

---

## 8. Recommendation

**Track A: none. Track B: none. Shared-policy control: 1 (`q_closure_cplx`, at ceiling).
Failures: 6.**

**Proposed confirmation calls: 0 — I do not recommend running the confirmation stage on this
battery.** The single qualifying array is a ceiling shared-control; confirming it would cost
2 × 60 = 120 calls (~$2) and would establish only that a unanimous choice is still unanimous.
It should be run only if the design specifically needs a certified shared-policy control, in
which case use **n = 72** (three full permutation cycles) rather than 60, so permutation
balance stays exact.

The binding result is §4.1: **at four options neither model runs a stable positional policy**,
so the form-vs-position asymmetry that motivated Track B does not exist in this action space.
That is a fact about the models, not about these seven arrays, and no further crossed-factor
construction will change it.

What the evidence supports doing next, in order:

1. **Decide explicitly whether Track B′ (focal form vs OTHER diffuse) is admissible.** If it
   is, `q_nesting_weight` is a genuine candidate with a +0.917 COPY-minus-OTHER advantage,
   and a targeted confirmation at n = 72 (2 × 72 = 144 calls, ~$2) would test whether
   Claude's `one_thick` policy and GPT's diffuseness both hold. This is the only route in
   the present data to an asymmetric array.
2. **Re-measure the three FC = 0.667 cells at higher n** before treating them as failures —
   at n = 24 they are one quantisation step below the bar (§4.4). `q_sizerank_tone` and
   `q_numer_arrange`, 2 models × 72 = 288 calls, ~$4.
3. **Do not build more crossed-factor arrays on the current evidence.** Effective support was
   1–3 live objects with a median of 2 (§4.3); crossing factors did not deliver four live
   objects, so the arity increase is not buying what it was meant to buy.

Green assignment, confirmation, and generator changes remain untouched, as instructed.
