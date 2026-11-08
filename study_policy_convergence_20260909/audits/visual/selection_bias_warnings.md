# T1 — selection-bias and inference warnings, visual domain

Ordered by how much damage the error would do to a Stage 1 similarity claim.
Every item was verified against raw files, not inherited from an existing report.

---

## W1 — CRITICAL. Four of the five four-option batteries are selected on a model relationship

| set | arrays | selection criterion (verbatim source) |
|---|---|---|
| FROZEN_22 | 22 | "GPT-5.5 already holds a strong policy (share >= .75, FC >= .80)" — `OLDER_CLAUDE_AUDIT.md` §4 |
| `stimuli4` | 7 | built from binary contrasts pre-labelled Track A (GPT/Claude divergent) or Track B (focal form vs OTHER positional) — `BATTERY4_BUILD.md` §1 |
| `stimuli5` | 42 | mechanisms chosen after re-scanning B203 for arrays "meeting the asymmetry bar"; cue-conflict construction is an explicit divergence-seeking design — `STIMULUS_SEARCH_REPORT.md` §1 |
| `stimuli6` | 8 | built to repair two named GPT-focal failures — `GPT_EXPANSION_REPORT.md` |
| B203 Stage C subset | 29 | HIGH (>= .75 and own−cross >= .15) or LOW (<= .45) |

**Consequence:** a similarity estimate computed on any of these is conditioned on the very
relationship it purports to measure. On FROZEN_22 the conditioning is on GPT strength
specifically, so any GPT-vs-Claude similarity there is guaranteed to be dominated by the
selection.

**These sets are technically indistinguishable from an unconditioned battery.** They use the
same prompt (`d40ea45d`), the same permutation schedule, the same parser and the same estimator,
and their CSVs have the same columns. Nothing in the data will stop them being concatenated.
The only defence is an explicit stratum label carried from the manifest.

---

## W2 — CRITICAL. The only cross-vintage four-option data in existence is on the GPT-strong set

`claude-opus-4-7` (1,056 rows) and `claude-opus-4-6` (1,704 rows) have four-option choice data
**exclusively on FROZEN_22**. There is zero overlap with the blind B203 battery.

Two specific traps follow:

- **Reusing that data to save money would silently import the GPT-strong criterion into the
  vintage trend.** Opus 4.7 agreed with GPT's modal object on 22/22 FROZEN_22 arrays; Opus 4.6
  on 20/22. Reported as "similarity rises with vintage" this would be an artefact of having
  measured older Claudes only where GPT is unanimous.
- **The tree's own documents already show binary counts do not forecast four-option yield.** The
  binary audit predicted 4 asymmetric candidates for Opus 4.7 and got **0**
  (`GPT_FOCAL_OLDER_CLAUDE_RESULT.md`). Do not size or select the panel from binary evidence.

---

## W3 — CRITICAL. A populated model ID does not mean the model chose

Verified in `generation_ladder_20260814/models/opus47_expanded/data/`:
`stageB_salience_20260815_140957.csv` has **1,800 rows with `salience_rating` populated and
`parsed_choice_side` empty**, and **`gpt-5.5-2026-04-23` is one of the two checkpoints in that
file** — inside a folder named for Opus 4.7. GPT is a *rater* there, never a chooser.

Tree-wide rater row counts (binary arity): gpt-5.5 11,345; opus-4-5 6,300; opus-5 5,970;
opus-4-7 4,500; gpt-5 3,150; opus-4-8 1,800; opus-4-6 1,410; gpt-5.4 450; gpt-4o 450.

**At four-option arity the trap does not exist:** no four-option file in the tree has a
`salience_rating` column, `SALIENCE_PROMPT` (`97d216ae`) and the auditor prompts were never run
at arity 4, and `chosen_item` is populated on 100% of rows in every Stage-A-frame file. Every
four-option model ID is a chooser. **Verified per file, not assumed.**

### W3a — two further ID traps in the same tree

- **`SIMULATED` appears as a returned checkpoint on 21,725 rows with parsed choices**, in
  `study2_partner_policy_20260822/data/sim_*.csv`. These are power-simulation outputs. Any
  "model ID + parsed choice = measurement" sweep will ingest them as data.
- **10,664 rows have an EMPTY returned checkpoint**, concentrated in
  `generation_ladder/models/opus4[56]_expanded/data/stageB_*` and a `discarded/` folder
  (2,284 rows). The psc-era runner leaves `api_model` blank and records the checkpoint under
  `actor_model_id_returned`; a first pass of `older_claude_audit.py` reported zero overlap for
  every checkpoint because of exactly this, and the bug is recorded in that file's own notes.

---

## W4 — HIGH. Behavioural collapse makes raw cross-model match uninterpretable

Recomputed from raw, median effective support (`1 / sum p_i^2`, four displayed options):

| set | gpt-5.5 | claude-opus-5 | opus-4-7 | opus-4-6 |
|---|---|---|---|---|
| B203 (203 arrays) | 1.28 | 1.09 | — | — |
| B42 (42 arrays) | 1.39 | **1.00** | — | — |
| FROZEN_22 (22 arrays) | — | — | **1.00** | 1.36 |

Claude Opus 5 is on **one live option** on the median B42 array; `claude-opus-4-7` on the median
FROZEN_22 array. Cells with >= 3 live options: 9/203 (GPT) and 10/203 (Claude) on B203, and
**0/42 on B42 for either model**.

Two independent draws from a one-live-option policy agree with probability 1 regardless of what
the other model does. Any similarity increase along the vintage axis will therefore be
contaminated by Claude becoming more deterministic. This is `MASTER_DESIGN` §5 and
`DATA_DICTIONARY` "Mandatory separation", and it is not a hypothetical risk in this tree — it is
the modal case.

---

## W5 — HIGH. "Four options" does not mean four measured alternatives

Related to W4 but distinct: the *battery* is four-option, the *behaviour* is not. Median
effective support 1.0–1.4 means the chance floors quoted in `DATA_DICTIONARY` (.25) are the
right null for a uniform responder but describe almost nothing that actually happens. Report
`effective_support` per cell in every table; never present a match statistic against the .25
floor without it.

---

## W6 — HIGH. The Stage C replication is not an equivalent-frame replication

`DURABILITY_INVENTORY_4OPT.md` §2 presents Stage C as "a genuine independent re-measurement at
larger n and in a different frame". T1's recomputation shows three separate incompatibilities:

1. **Different prompt.** 16 `betting_prompt` variants; none is `d40ea45d`. Partner identity is
   disclosed and an ENTER/SAFE payoff decision is added.
2. **Permutation balance is broken.** All 30 Stage C cells use **20 of the 24 permutations, 8
   times each** — the only four-option run in the tree whose balance fails. Every other run is
   exactly balanced.
3. **Choice is conditional on ATTEMPT.** Per cell, 160 calls yield 39–123 parsed choices; on
   `F11_noise_m1` Claude yields **1**. The choice sample is selected on the model's own decision
   to play, which is itself driven by its confidence in the array. This is the strongest
   selection effect in the four-option data and it is inside a file that otherwise looks like a
   Stage A file.

Treat the Stage C durability tiers as suggestive, not as certification, and never pool.

---

## W7 — MEDIUM. B203 batch 2 is conditioned on determinism, not on a model relationship

`make_battery2.py` was written after batch-1 Stage A and states that roughly half its 25
families "deliberately present four near-equivalent options … which is where battery 1's
non-positional lows came from", naming `F05_orient`, `F11_noise`, `F12_mirror`, `F16_aspect`.

This is **not** conditioning on GPT-vs-Claude — no named model's preference enters — so batch 2
remains admissible. But it *is* conditioning on the marginal distribution of within-model
convention strength, which is precisely the quantity that must be separated from similarity.
Carry `batch` as a stratum, and report the frame estimate with and without batch 2. If the two
disagree materially, batch 1 alone (`VIS-FRAME-16`) is the defensible answer.

---

## W8 — MEDIUM. An existing inventory in the tree is stale and will mislead

`study2_4opt_20260830/data/DURABILITY_INVENTORY_4OPT.md` (2026-09-08) asserts "there is exactly
one 4-option battery" and "every 4-option policy we hold is from `study2_4opt_20260830`, on
`gpt-5.5-2026-04-23` and `claude-opus-5`". Both were true at the time and are now false: 57
further four-option arrays and two further checkpoints were added on 2026-09-08/09. Its §5
"available pool" and §4a divergence table are computed on B203 only and must be re-derived
before use.

---

## W9 — MEDIUM. n = 24 discovery screens have already let position-sensitive arrays through

At n = 24 with all 24 permutations, form consistency rests on 6 trials per slot and is quantised
to 1/6 — T1 confirms the observed FC values across the tree are exactly
{0.33, 0.50, 0.67, 0.83, 1.00}. `GPT_POSITION_DIAGNOSIS.md` and `GPT_EXPANSION_REPORT.md` record
that this is *why* `m4_contour_v1` and `m1_nesting_v3` passed a discovery screen and then failed
at n = 72 on form consistency alone (.72 and .56). The n = 48 floor in `MASTER_DESIGN` is
directly supported by this; it should not be relaxed for any checkpoint.

---

## W10 — MEDIUM. One published four-option generalisation is too strong

`DISCOVERY4_REPORT.md` §4.1: "at four options neither model runs a stable positional policy",
derived from 14 cells on the 7-array `stimuli4` battery (max `pos_modal_share` .458). On the
406-cell B203 battery T1 finds **3 cells at `position_modal_share` >= .75**, maximum **.917**.
Rare, but not zero. Position sensitivity must be measured per cell in Stage 1, not assumed away
by citing that sentence.

---

## W11 — LOW/MEDIUM. Provenance gaps that block `FROZEN_HASHES.json`

- **B203 has no frozen battery hash.** `stimuli4/5/6` each ship a `BATTERY*_SHA256.txt`; B203
  ships none. T1's independently computed content hash of its 4,872 perm images is
  `56e4eed8d6f5948146d4c5d6192230fe8c424ff67acab8d32f192706ebb11d47` (sorted `perm*.png`, each
  hashed as `relpath || bytes`).
- **B203 has no `mechanism` field.** `DATA_DICTIONARY` requires `mechanism` kept separate from
  `family`; the B203 manifest has `family` only. Here they are 1:1, but the column must be added
  explicitly rather than inferred at analysis time.
- **`make_battery.py`'s docstring disagrees with its own output** (15x8=120 vs the actual
  16x8=128). Trust the manifest.
- **GPT spend has never been measured.** `s4_common.ask_gpt` discards `r.usage`. The
  `$0.0153/call` figure quoted throughout study4 comes from the *strategic pilot*, whose prompts
  are far longer than `d40ea45d`; measured `d40ea45d` Claude anchors are `$0.005025` and
  `$0.004475` per call. Do not size the visual domain on `$0.0153`.
- **`older_claude_audit.py` imports `targeted_common` from
  `LLM_Coordination/Name_game_experiment/`**, outside the `Self_Coordination` root. It exists,
  but the four-option analysis path has a live dependency on a directory this study does not own
  and does not hash.

---

## W12 — LOW. Survivorship, and what "the same checkpoint" means

- Only 4 of the 17 checkpoints in T4's panel have ever produced a four-option response. The
  vintage ladder is being reconstructed from checkpoints that happen to still be served; this is
  survivorship bias and Stage 1's language must stay descriptive.
- Claude aliases (`claude-opus-4-6/-4-7/-4-8/-5`) return the alias itself, so
  `checkpoint_returned == checkpoint_requested` is near-vacuous on the Claude side
  (`DECISION_LOG` D-015(b)). GPT returns a dated snapshot and is therefore auditable.
- Existing B203 data is 2026-08-30. Pooling a 2026-09 top-up onto it assumes no serving-stack
  drift over 9 days on the two most load-bearing checkpoints. If the lead pools, test the two
  blocks for homogeneity per array and keep the block indicator; do not merge silently.
