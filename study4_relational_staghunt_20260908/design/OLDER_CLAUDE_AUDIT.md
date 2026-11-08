# Older-Claude audit — can an older checkpoint supply the OTHER model for a GPT-5.5-focal arm?

Audit only. **No API calls, no new stimuli, no existing data modified.**
Deliverable CSVs: `design/older_claude_overlap.csv`,
`design/older_claude_gpt_focal_candidates.csv`, `design/older_claude_shared_controls.csv`.
Code: `code/older_claude_audit.py` — both models re-estimated from raw through
`targeted_common`, the same path as every Study 4 number. Checkpoints are never pooled
(asserted in code: each source file must contain exactly one checkpoint).

## VERDICT

**Targeted measurement warranted.** Existing data are insufficient — not marginal, *absent*:
**no older Claude checkpoint has ever been run on a four-option array.** The comparison is
not confounded in principle and the checkpoints are usable; the data simply do not exist at
the required arity.

---

## Phase 1 — existing-data audit

### 1.1 The decisive fact

Scanning every results file in the tree and partitioning by arity:

| arity | models present |
|---|---|
| **4-option** | `gpt-5.5-2026-04-23`, `claude-opus-5` — **and nothing else** |
| binary | gpt-5.5, claude-opus-5, claude-opus-4-5-20251101, claude-opus-4-6, claude-opus-4-7, claude-opus-4-8, gpt-5.4, gpt-5, gpt-4o |

All older-Claude data is **binary**. Overlap with GPT-5.5 at four options is **zero**.

A second trap, checked and confirmed: in the `generation_ladder` files where GPT-5.5 and an
older Claude appear together, **GPT-5.5 is only a Stage-B salience rater** (populated
`salience_rating`, empty `parsed_choice_side`). It is never a chooser there, so those
files provide no comparable choice data.

### 1.2 Per-checkpoint overlap (binary only)

Every older checkpoint overlaps GPT-5.5 on exactly the same 15-array step1 battery.

| checkpoint | avail. for new calls | battery | overlapping arrays | arity | prompt | framing | n/cell | position scheme | parser | raw |
|---|---|---|---|---|---|---|---|---|---|---|
| `claude-opus-4-5-20251101` | unverified* | step1 (15) | 15 | 2 | `3003ae1b` | same-model coordination | 60 | AB/BA, n/2 each | `parse_side` LEFT/RIGHT | yes |
| `claude-opus-4-6` | unverified* | step1 (15) | 15 | 2 | `3003ae1b` | same-model coordination | 60 | AB/BA, n/2 each | same | yes |
| `claude-opus-4-7` | unverified* | step1 (15) | 15 | 2 | `3003ae1b` | same-model coordination | 60 | AB/BA, n/2 each | same | yes |
| `claude-opus-4-8` | unverified* | step1 (15) | 15 | 2 | `3003ae1b` | same-model coordination | 60 | AB/BA, n/2 each | same | yes |

*Availability cannot be established without an API call, which this audit forbids. What is
on record: each ID was called successfully in Aug 2026 with 0 transport failures. **Live
availability must be probed before committing to a checkpoint.**

Comparability holds on every axis the brief requires — identical rendered images, identical
prompt hash on both sides (verified, not assumed), identical AB/BA balancing, identical
parser, and both sides re-estimated through the same code. GPT-5.5's side comes from
`policy_specific` (n = 60), not from the ladder.

---

## Phase 2 — candidate inventory (BINARY; supporting evidence only)

These cannot serve a four-object Study 4 arm. They are reported because they are the only
evidence available for *choosing* a checkpoint.

| checkpoint | GPT-focal asymmetric | families | shared controls | Claude policy subtypes |
|---|---|---|---|---|
| `claude-opus-4-5` | **9** | 6 | **0** | position 2, weak-competing 2, diffuse 3, strong-competing 2 |
| `claude-opus-4-6` | **7** | 5 | 1 | diffuse 3, position 2, weak 1, strong 1 |
| `claude-opus-4-7` | **4** | 4 | **4** | diffuse 3, position 1 |
| `claude-opus-4-8` | 1 | 1 | **7** | position 1 |

**The gradient is monotone and it is the whole story.** As the checkpoint approaches Opus 5,
asymmetric arrays fall 9 → 7 → 4 → 1 and shared controls rise 0 → 1 → 4 → 7. Recency trades
directly against divergence from GPT-5.5.

**No checkpoint meets the Phase-3 requirement, at any arity.** The requirement is ≥6
asymmetric **and** ≥6 controls from the *same* checkpoint. On a 15-array battery those two
counts are near-complementary, so the requirement is arithmetically unreachable here: 4.5
gives 9+0, 4.8 gives 1+7, and the best balance (4.7) gives 4+4 = 8 of 15.

---

## Phase 3 — recommended checkpoint

**`claude-opus-4-7`**, with `claude-opus-4-6` as fallback.

Rationale, in the brief's own order of preference — *the closest capable checkpoint that
meets the stimulus requirement*:

- **4.8** is closest to Opus 5 but shows almost no divergence (1 of 15 binary arrays). It
  would very likely yield too few asymmetric four-option arrays to support an arm.
- **4.5 / 4.6** diverge most, but they are furthest from Opus 5, and 4.5 produced **zero**
  shared controls — which makes the required Partner × Item Type interaction untestable.
- **4.7** is the only checkpoint with a usable balance in *both* directions (4 asymmetric,
  4 controls, 4 families), and it is one generation from Opus 5. Parse reliability is clean
  (900/900 rows, 0 failures).

Choosing 4.7 deliberately does **not** maximise the number of differences — 4.5 would. The
interaction test needs both arms, so balance beats magnitude.

### 3.1 The "GPT treats an older model as generically unreliable" confound

**It does not apply to the measurement proposed in Phase 4, and it does apply to the game.**

At *measurement* time the confound is structurally absent: the four-option coordination
prompt says "another instance of you", so neither model is ever told about the other, and
neither is asked to predict the other. COPY-minus-OTHER is a derived statistic comparing
GPT's self-match to a GPT × Claude cross-match computed from two independent marginals. GPT
has no opportunity to treat the partner as anything.

At *game* time, partner identity is disclosed, and the confound is live. The required
protection is exactly as the brief states — a **Partner × Item Type interaction**:
COPY-minus-OTHER must be large on asymmetric arrays and substantially smaller on
shared-policy arrays. A uniform older-Claude penalty across both item types would be
generic distrust, not relational policy accuracy. **This is the reason the arm needs ≥6
shared controls and not just asymmetric arrays**, and it is why 4.5 is rejected despite
having the most asymmetry.

---

## Phase 4 — proposed minimal measurement (not run)

GPT-5.5 already holds a strong policy (share ≥ .75, FC ≥ .80) on **22 of the 50 four-option
arrays**, spanning all 6 mechanisms — line_contour 9, noise_texture 4, size_rank 4,
nesting 2, mirror 2, numerosity 1. Those 22 are the natural test set: the GPT side is
already established, so only the older Claude needs measuring.

| stage | what | calls | est. cost |
|---|---|---|---|
| 1 | `claude-opus-4-7` discovery on the 22 GPT-strong arrays, **all 24 permutations × 2 cycles (n = 48)** | 22 × 1 × 48 = **1,056** | ~$16 |
| 2 | joint confirmation, n = 72, on promoted candidates + retained controls (assume ~10 arrays, both models) | 10 × 2 × 72 = **1,440** | ~$22 |
| | **total** | **≈ 2,500** | **≈ $38** |

Discovery at n = 48 rather than 24 is deliberate: the Study 4 diagnosis established that FC
at 6 trials/slot is too noisy to screen on, and it is what let position-sensitive arrays
through before.

**Does current GPT need remeasurement?** Partly. Eight arrays already carry independent
n = 72 GPT data from the Study 4 confirmation runs and need nothing further. The other 14
rest on n = 24/48 discovery only, which is adequate to *select* but not to *certify* a
GPT-focal array. Hence Stage 2 confirms **both** models on whatever promotes — that is the
$22 line, and it is not optional if the arm is to be confirmatory.

**Before committing:** probe that `claude-opus-4-7` is still served (one API call). If it
is retired, fall back to `claude-opus-4-6` (7 asymmetric / 1 control at binary) and accept
that the control arm will have to come mostly from the four-option measurement itself.

---

## Deviations and limits

- **Availability unverified** for all four checkpoints — the audit forbids API calls.
- **Binary evidence is not a substitute.** Every count in Phase 2 is from 2-option arrays.
  Study 4 policies did not transfer from binary to four-option before (5 of 7 focal policies
  degraded), so these counts should be read as *checkpoint ranking*, not as a yield forecast.
- **The 15-array overlap is small**, and the asymmetric/control split within it is
  near-complementary, so no existing battery can satisfy ≥6 + ≥6 regardless of checkpoint.
- A first pass of this audit reported zero overlap for all checkpoints. That was a loader
  bug — the psc-era runner leaves `api_model` empty and records the checkpoint in
  `actor_model_id_returned`. Fixed, and the code now asserts the checkpoint read from the
  rows matches the folder it came from.
