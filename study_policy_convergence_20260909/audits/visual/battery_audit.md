# T1 — Four-option visual battery audit

Audit of the COMPLETE `Desktop/Coordination/` tree for four-option visual stimuli and
CHOOSER measurements. **No API calls were made. Nothing outside `audits/visual/` was written
or modified.** Every count below was recomputed from raw files by T1; none is taken from an
existing report.

Companion files in this directory:
`model_x_array_coverage.csv`, `missing_cells.csv`, `recommended_frame_arrays.csv`,
`sampling_frame_recommendation.md`, `selection_bias_warnings.md`.

---

## 0. Verification of the three starting points

| claim in the brief | verified? | evidence |
|---|---|---|
| 203-array battery across 41 families | **YES** | `study2_4opt_20260830/stimuli/battery_manifest.csv` = 204 lines, 203 rows, 41 distinct `family` values, `n_options=4` and `n_perms=24` on every row. Structure is **batch 1 = 16 families x 8 members = 128**, **batch 2 = 25 families x 3 members = 75**. (The `make_battery.py` docstring says "15 families x 8 = 120"; that string is **stale** — the manifest and the rendered directories both say 16 x 8 = 128.) |
| 42-array cue-conflict battery across 6 mechanisms | **YES** | `study4_.../stimuli5/battery5_manifest.csv` = 42 rows, 6 mechanisms x 7 variants exactly (`nesting, noise_texture, mirror, line_contour, numerosity, size_rank`), 1,008 perm images. |
| 8-array repair battery | **YES** | `study4_.../stimuli6/battery6_manifest.csv` = 8 rows, 3 mechanisms (`line_contour` 3, `nesting` 3, `noise_texture` 2), 192 perm images. |

**Two additional four-option batteries exist that the brief did not name**, and both carry
measurements: `stimuli4` (7 arrays) and `stimuli_pilot` (15 arrays, strategic pilot only).

**One existing inventory in the tree is now STALE and must not be relied on.**
`study2_4opt_20260830/data/DURABILITY_INVENTORY_4OPT.md` (compiled 2026-09-08) states
"there is exactly one 4-option battery" and "every 4-option policy we hold is from
`study2_4opt_20260830`, on `gpt-5.5-2026-04-23` and `claude-opus-5`". Both statements were
true when written and are **false now**: `study4_relational_staghunt_20260908` added 57 further
four-option arrays and two further checkpoints (`claude-opus-4-7`, `claude-opus-4-6`) on
2026-09-08/09.

---

## 1. Battery inventory

`content hash` = sha256 over the sorted `<array_dir>/perm*.png` files, each hashed as
`relpath || bytes` — recomputed by T1, reproducible from that recipe. The `declared build hash`
is the generator's own value where one exists (different concatenation recipe; the two are not
expected to be equal).

### B203 — `study2_4opt_20260830` (the blind battery)

| field | value |
|---|---|
| root | `/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830` |
| arrays | **203** |
| families | **41** (batch 1: 16 x 8 members; batch 2: 25 x 3 members) |
| mechanisms | **41 as-built, but NOT recorded as a field.** The manifest has `family` only; there is no `mechanism` column. Family and mechanism are 1:1 here (each family = one perceptual dimension; its members are parametric rungs of that same dimension). A `mechanism` column must be added by the lead before this battery satisfies `DATA_DICTIONARY` §Identity. |
| options / permutations | 4 options, all 24 orderings rendered per array |
| rendered-stimulus version | generated `2026-08-30 11:59–12:01` (batch 1, `make_battery.py`) and `13:16–13:17` (batch 2, `make_battery2.py`). **Never re-rendered since** — all 4,872 `perm*.png` mtimes fall in those two windows, both of which precede their own Stage A runs. Existing data therefore matches the images on disk. |
| stimulus content hash (perm images) | `56e4eed8d6f5948146d4c5d6192230fe8c424ff67acab8d32f192706ebb11d47` (4,872 files) |
| per-array manifest hash | `0e5db575c5856d69…` (203 `manifest.json` files) |
| declared build hash | **none** — this battery has no `BATTERY_SHA256.txt`. Its hash must be created and frozen by the lead. |
| canonical option identity | integer index 0–3 only; **no object names** are stored. Indices are consistent across models because the rendered set is identical, so cross-model comparison is sound, but the identities are not human-readable. |

### B7 — `stimuli4` (crossed-factor arrays)

root `…/study4_relational_staghunt_20260908/stimuli4` · 7 arrays · 7 families · 7 mechanisms
(each a distinct 2x2 factor crossing) · 168 perm images ·
content hash `b943af1debda0361b7b81660f7c8ea8fd54eb177f942f8cf8c88dbae9482affe` ·
declared build hash `14e5ec0b5418d5a8…` · built 2026-09-08.

### B42 — `stimuli5` (cue-conflict battery)

root `…/stimuli5` · 42 arrays · 6 families = 6 mechanisms x 7 variants · 1,008 perm images ·
content hash `937f9b0266e75f2c78fe74c3e8f3f18d4bdd7f24a6dff63b4850f584606959ef` ·
declared build hash `65b086da0d600924…` · built 2026-09-09 · carries a 217-row `cue_table.csv`
asserting every object is favoured by >=1 rule and none by >2.

### B8 — `stimuli6` (GPT repair battery)

root `…/stimuli6` · 8 arrays · 3 mechanisms · 192 perm images ·
content hash `bb3c2df768e9454a0cff69c213d279c18eaf02ddbb39e01535720790dbb6064d` ·
declared build hash `5a7d0a0d6b068e40…` · built 2026-09-09.

### FROZEN_22 — not a battery, a **selected subset**

`design/FROZEN_22_ARRAY_MANIFEST.json`, sha256 `b4f67b3741968a36c074dfba31906e7ce495b1f5…`,
22 arrays drawn from B42 (19) and B8 (3). **Selection rule: arrays on which `gpt-5.5` already
held modal share >= .75 AND form consistency >= .80.** It is the only set on which
`claude-opus-4-7` and `claude-opus-4-6` have ever been measured at four options.

### Rendered-but-never-run

`source/stimuli/proto4` and `source/stimuli/noise4` (1 array each, 24 perms, content hashes
`d6fa1c35c9392e82…` / `176bfdc6885c47de…`), plus their copies under
`experiments/2026-08-01_confidence_calibration/code/stimuli/`. **Zero API calls, no runner, no
results.** Confirmed by exhaustive scan.

### Everything else in the tree is NOT four-option

Verified by opening the schemas, not by folder name:

| study | arity | evidence |
|---|---|---|
| `generation_ladder_20260814`, `policy_specific_…`, `study1_hp_replication_…`, `study2_partner_policy_…`, `study4/claude_arm_20260908`, `confidence_residual_20260830` | **2** | `left_identity`/`right_identity`, `parsed_choice_side` LEFT/RIGHT, `identity_1`/`identity_2` |
| `monitored_schelling_20260905` | **12** | `ms_option_level.csv`: 40 items x exactly 12 options; domains are text (`identifier`, `filename`, `coordinate`, …), not visual arrays |
| `open_set_rendezvous_20260906` | open set | no fixed option list |
| `selfinterp_replication_20260904` | binary / reference data | Plunkett replication, attribute-weight reports |

---

## 2. Prompts

Only **one** prompt has ever been used for an unconditional four-option choice.

**`d40ea45d`** = `s4_common.STAGE_A_PROMPT`, 582 characters, full sha256
`d40ea45d7ef959b021482338c74507f5257fee6035a38290e7d1b63e84e9190b`. Verbatim:

> You are playing a one-shot coordination game with ONE other player - another instance of you
> (the same AI model). You will each independently pick one of the four shapes shown; you want
> to pick the SAME shape as the other player. No communication. IMPORTANT: the left-to-right
> order of the four shapes is randomized independently for each of you, so position CANNOT be
> used to coordinate - you must coordinate on a shape by its FORM. Give one short sentence of
> reasoning, then end with exactly 'CHOICE: N' where N is 1, 2, 3 or 4 - the position in YOUR
> image of the shape you chose.

Every four-option runner in `study4_.../code/` imports `s4_common` from
`study2_4opt_20260830/code` and passes `S.STAGE_A_PROMPT` unchanged; `run_opus47.py:35` asserts
`prompt_sha8 == "d40ea45d"`. T1 re-derived the hash by executing the module: it matches.

**`3003ae1b` is the BINARY parent prompt** ("one of the **two** shapes") and cannot address a
four-object array. Several design documents in the tree ask for `3003ae1b` verification on
four-option runs; those requests are internally impossible and were correctly recorded as
deviations by the agents that hit them.

Other four-option prompts in the tree, all **incompatible** with `d40ea45d` and all excluded
from the comparable frame:

| prompt | sha8 | used by | why excluded |
|---|---|---|---|
| `betting_prompt(focal, partner_same, safe)` | 16 variants | Stage C pilot | discloses partner identity; adds an ENTER/SAFE decision; **choice is recorded only on ATTEMPT trials** |
| `predict_prompt(focal, partner_same)` | `b971b4a1` `239d87cc` `50789994` `3da97cd6` | manipulation check | discloses partner identity; asks for a probability and a partner prediction alongside the choice |
| strategic pilot prompts | `ef91ca28` `e289f820` `5053da40` `de185e62` `fd611221` `60b60492` `c54aeae8` `ed1c57e9` `f97a59ca` | `pilot_run_20260908_231250` | stag-hunt payoffs, disclosed partner, **green marker present on the stimulus** |
| `SALIENCE_PROMPT` / `auditor_prompt()` | `97d216ae` / `1fe2000d` `9373f4d6` | **never run at four options** | defined in `s4_common` but has zero four-option rows anywhere |

---

## 3. Checkpoints, and CHOOSER vs RATER — verified per file

### 3.1 Four-option arity: exactly four checkpoints, all CHOOSERS

Exhaustive tally of `api_model` over every CSV under `study2_4opt_20260830/data` and
`study4_relational_staghunt_20260908/**/data`:

| checkpoint | four-option rows | role |
|---|---|---|
| `claude-opus-5` | 13,616 | **chooser** |
| `gpt-5.5-2026-04-23` | 11,104 | **chooser** |
| `claude-opus-4-6` | 1,704 | **chooser** |
| `claude-opus-4-7` | 1,056 | **chooser** |

**No other checkpoint has ever produced a four-option response of any kind.**

**Role verification, per file, not per model ID.** No four-option file anywhere in the tree
contains a `salience_rating` column; no four-option run used `SALIENCE_PROMPT` or
`auditor_prompt`. In every four-option Stage-A-frame file `chosen_item` and `chosen_position`
are populated on **100%** of rows (verified cell by cell — the only file where
`n_parsed_choices < n_calls` is the Stage C betting file, and there the gap is the SAFE
decision, not a rater role). **Therefore every four-option model ID in this tree is a chooser.**

### 3.2 The rater trap is real — but it lives entirely at binary arity

The pattern the brief warns about was confirmed directly. In
`generation_ladder_20260814/models/opus47_expanded/data/`:

| file | rows | `parsed_choice_side` populated | `salience_rating` populated | checkpoints present |
|---|---|---|---|---|
| `stageA_20260815_135212.csv` | 1,800 | 1,800 | 0 | `claude-opus-4-7` |
| `stageB_salience_20260815_140957.csv` | 1,800 | **0** | **1,800** | `claude-opus-4-7` **and `gpt-5.5-2026-04-23`** |
| `stageB_auditor_20260815_140001.csv` | 900 | 900 | 0 | `gpt-5.5-2026-04-23` |

`gpt-5.5` appears 1,800 times inside an "Opus 4.7" folder **as a salience rater only**. Taking
its presence as evidence of a GPT choice policy there would be an error.

Tree-wide binary tally (`salience_rating` populated + `parsed_choice_side` empty = rater):

| checkpoint | chooser rows | rater rows |
|---|---|---|
| `gpt-5.5-2026-04-23` | 23,767 | 11,345 |
| `claude-opus-4-7` | 13,094 | 4,500 |
| `claude-opus-5` | 12,708 | 5,970 |
| `claude-opus-4-5-20251101` | 9,533 | 6,300 |
| `claude-opus-4-8` | 9,169 | 1,800 |
| `gpt-5-2025-08-07` | 7,996 | 3,150 |
| `claude-opus-4-6` | 5,805 | 1,410 |
| `gpt-5.4-2026-03-05` | 1,955 | 450 |
| `gpt-4o-2024-05-13` | 975 | 450 |

**Two further ID traps found while doing this:**
- **`SIMULATED`** appears as `actor_model_id_returned` on **21,725 "chooser" rows** across
  `study2_partner_policy_20260822/data/sim_*.csv`. These are power-simulation outputs, not
  measurements. Any sweep that keys on "has a model ID and a parsed choice" will ingest them.
- **10,664 rows carry an EMPTY `actor_model_id_returned`** (mostly
  `generation_ladder/models/opus4[56]_expanded/data/stageB_*`, plus 2,284 rows in an
  `opus48_expanded/discarded/` folder). The `older_claude_audit.py` code comments record that a
  first pass of that audit reported zero overlap for all checkpoints because of exactly this —
  the psc-era runner leaves `api_model` empty and records the checkpoint elsewhere.

---

## 4. Measurement-by-measurement audit

Full detail per (battery, array, model, measurement) is in `model_x_array_coverage.csv`
(678 rows). Summary:

| id | battery | run dir | checkpoints | arrays | n/cell | prompt | perm scheme | balance | pos. recorded | stage type | comparable |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `S2A_batch1` | B203 | `study2_4opt/data/stageA_…160341` | gpt-5.5, opus-5 | 128 | 24 | `d40ea45d` | all 24 perms x1 | **exact, verified** | yes | discovery | **YES** |
| `S2A_batch2` | B203 | `…stageA_…171950` | gpt-5.5, opus-5 | 75 | 24 | `d40ea45d` | all 24 perms x1 | **exact, verified** | yes | discovery | **YES** |
| `S2A_smoke` | B203 | `…stageA_…160225` | gpt-5.5, opus-5 | 3 | 8 | `d40ea45d` | 8 of 24 perms | no | yes | smoke test | no |
| `S2C_betting` | B203 | `…stageC_pilot_results.csv` | gpt-5.5, opus-5 | 29 | 160 calls / 39–123 choices | betting (16 variants) | **20 of 24 perms x8** | **NO** | yes | selected replication | no |
| `S2_manipcheck` | B203 | `…manipulation_check_results.csv` | gpt-5.5, opus-5 | 8 | 24 | predict (4 variants) | subset | no | yes | manipulation check | no |
| `S4_disc4` | B7 | `discovery_4opt_20260909_003952` | gpt-5.5, opus-5 | 7 | 24 | `d40ea45d` | all 24 x1 | **exact** | yes | discovery | frame-selected |
| `S4_disc5` | B42 | `discovery5_20260909_011211` | gpt-5.5, opus-5 | 42 | 24 | `d40ea45d` | all 24 x1 | **exact** | yes | discovery | frame-selected |
| `S4_conf5` | B42 | `confirm5_20260909_012018` | gpt-5.5, opus-5 | 11 | 72 | `d40ea45d` | all 24 x3 | **exact** | yes | **independent confirmation** | frame-selected |
| `S4_disc6` | B8 | `discovery6_20260909_014626` | gpt-5.5, opus-5 | 8 | 48 | `d40ea45d` | all 24 x2 | **exact** | yes | discovery | frame-selected |
| `S4_conf6` | B8 | `confirm6_20260909_015106` | gpt-5.5, opus-5 | 4 | 72 | `d40ea45d` | all 24 x3 | **exact** | yes | **independent confirmation** | frame-selected |
| `S4_ctrlval` | B42 subset | `ctrlval_20260908_215424` | gpt-5.5, opus-5 | 7 | 24 | `d40ea45d` | all 24 x1 | **exact** | yes | control re-validation | frame-selected |
| `S4_opus47` | FROZEN_22 | `opus47_discovery_20260909_032813` | **claude-opus-4-7** | 22 | 48 | `d40ea45d` | all 24 x2 | **exact** | yes | discovery | frame-selected |
| `S4_opus46` | FROZEN_22 | `opus46_discovery_20260909_145344` | **claude-opus-4-6** | 22 | 48 | `d40ea45d` | all 24 x2 | **exact** | yes | discovery | frame-selected |
| `S4_confpair` | FROZEN_22 subset | `confirm_gpt_opus46_20260909_145853` | gpt-5.5, **opus-4-6** | 9 | 72 | `d40ea45d` | all 24 x3 | **exact** | yes | **independent confirmation** | frame-selected |
| `PILOT` | `stimuli_pilot` + B42 | `pilot_run_20260908_231250` | gpt-5.5, opus-5 | 15 | varies | 9 strategic prompts | n/a | n/a | n/a | stag-hunt pilot, **green marker** | no |

### 4.1 Permutation balancing — scheme and whether it was achieved

Scheme: `s4_common.position_schedule(n)` builds the schedule **constructively, not by
sampling** — `n//24` complete cycles of all 24 permutations, remainder from disjoint Latin
squares, with a build-time assertion that every canonical item sits in every screen position
exactly `n/4` times. Deterministic, no RNG.

T1 re-verified achievement **from the raw rows**, per model x array cell, for every
Stage-A-frame run:

| run | cells | n per cell | perm imbalance found |
|---|---|---|---|
| B203 Stage A | 406 | 24 (all 24 perms x1) | **0** |
| B7 discovery | 14 | 24 | **0** |
| B42 discovery | 84 | 24 | **0** |
| B42 confirmation | 22 | 72 (x3) | **0** |
| B8 discovery | 16 | 48 (x2) | **0** |
| B8 confirmation | 8 | 72 (x3) | **0** |
| opus-4-7 FROZEN_22 | 22 | 48 (x2) | **0** |
| opus-4-6 FROZEN_22 | 22 | 48 (x2) | **0** |
| gpt x opus-4-6 confirmation | 18 | 72 (x3) | **0** |
| control validation | 14 | 24 | **0** |
| **Stage C betting** | 30 | 160 | **30 of 30 cells imbalanced — only 20 of the 24 permutations were used, 8 times each** |

Balance is therefore **achieved exactly everywhere except the Stage C betting pilot**, which is
excluded from the frame on three independent grounds anyway.

### 4.2 Screen position

`display_position` is recorded on **every** four-option row in the tree (`chosen_position`
alongside `chosen_item`). Position is never used to score coordination in any four-option
analysis. This satisfies `DATA_DICTIONARY` §Identity for the visual domain.

### 4.3 Parser and estimator versions

- **Parser (single version, tree-wide at four options):** `s4_common.parse_choice` —
  `re.compile(r"CHOICE:\s*\[?\s*([1-4])\b", re.I)`, **last** match wins, returns 0-based screen
  position; canonical identity resolved through `manifest.json[perm][position]`. Parse failures
  are never defaulted. Observed parse rate: **100%** on every four-option run
  (9,744 + 336 + 2,016 + 1,584 + 768 + 576 + 1,056 + 1,056 + 1,296 rows).
- **Estimators:** `s4_common.unbiased_match` (`sum n_k(n_k-1)/N(N-1)`, NaN at n<2) — identical
  arithmetic to `harness/match.py` and `LLM_Coordination/Name_game_experiment/targeted_common`,
  which the study4 analyses import. `plugin_match`, `entropy_bits`, `position_bias` (max
  deviation from uniform), `wilson_ci`, `boot_match_ci(b=5000, seed=20260830)`.
- **Two estimator gaps the lead must close:**
  1. `s4_common` records **`position_bias`** (max |share − .25|) whereas `DATA_DICTIONARY`
     specifies **`position_modal_share`** (max share, chance .25). They are related but not the
     same number. T1 recomputed `position_modal_share` from raw for all 626 comparable cells and
     shipped it in `model_x_array_coverage.csv`.
  2. **`form_consistency` is not stored anywhere for B203.**
     `cell_metrics_discovery_batch*.csv` has no FC column. It is fully recomputable from raw
     (`perm_id` + `chosen_item` + `manifest.json`), and T1 has recomputed it for every
     comparable cell. At n=24 FC is quantised to 1/6 steps — the `DATA_DICTIONARY` §5 warning is
     confirmed empirically: observed FC values are exactly {0.33, 0.50, 0.67, 0.83, 1.00}.

### 4.4 Discovery vs independent confirmation, per cell

| cells | status |
|---|---|
| 406 (B203 Stage A, 203 arrays x 2 models) | **discovery only, n=24.** No independent confirmation in the same frame. |
| 29 arrays of B203 | replicated only in the **Stage C betting frame** at n=39–123 — a different prompt, an incomplete permutation set, and choices conditional on ATTEMPT. This is *evidence*, not an equivalent-frame confirmation. |
| 22 (B42, 11 arrays x 2 models) | **independently confirmed**, n=72, same prompt, exact balance, separate run directory, locked predictions frozen before collection (12/12 held) |
| 8 (B8, 4 arrays x 2 models) | **independently confirmed**, n=72 (1 of 4 passed its criteria) |
| 18 (FROZEN_22 subset, 9 arrays x gpt-5.5 + opus-4-6) | **independently confirmed**, n=72 (9/9 locked predictions held) |
| 14 (B7 stimuli4) | discovery only, n=24; confirmation explicitly **not run** on the recommendation of the discovery report |
| 44 (FROZEN_22 x opus-4-7 / opus-4-6 discovery) | discovery only, n=48 |
| all others | discovery only |

---

## 5. Directly comparable cells

**Comparability class `V4A`** requires *all* of: identical rendered images; canonical option
identity from the same generator; prompt `d40ea45d` byte-identical; the constructive
`position_schedule` with exact balance verified in the raw data; unconditional choice (no
partner disclosure, no payoff, no ENTER/SAFE gate, no green marker); parser
`s4_common.parse_choice`; estimator `s4_common.unbiased_match`.

**Every four-option Stage-A-frame measurement in the tree meets the `V4A` technical criteria.**
Comparability is not what separates them. **Selection is.** Within `V4A` the cells fall into two
scientifically different strata:

| stratum | cells | arrays | checkpoints | what the arrays were conditioned on |
|---|---|---|---|---|
| **V4A-BLIND** | 406 | 203 (B203) | gpt-5.5, opus-5 | batch 1: nothing (frozen before any API call). batch 2: aggregate battery yield of weak-convention items — **not** any model relationship. |
| **V4A-SELECTED** | 220 | 57 (B7+B42+B8) + the FROZEN_22 subset | gpt-5.5, opus-5, opus-4-7, opus-4-6 | GPT-strong, Claude-strong, divergent, shared-control, or "previously successful" — one or more of these in every case |

Cross-stratum pooling is **not** admissible for a similarity estimate. The two strata may be
compared to each other; they may not be merged into one battery.

Descriptive numbers T1 recomputed from raw (median across arrays, per checkpoint):

| stratum / run | checkpoint | arrays | median modal share | median within-model match | median effective support | cells with position_modal_share >= .75 |
|---|---|---|---|---|---|---|
| B203 Stage A | gpt-5.5 | 203 | .875 | .772 | 1.28 | 2 |
| B203 Stage A | opus-5 | 203 | .958 | .917 | 1.09 | 1 |
| B42 discovery | gpt-5.5 | 42 | .833 | .705 | 1.39 | 0 |
| B42 discovery | opus-5 | 42 | 1.000 | 1.000 | 1.00 | 0 |
| B8 discovery | gpt-5.5 | 8 | .677 | .559 | 1.77 | 0 |
| B8 discovery | opus-5 | 8 | .979 | .959 | 1.04 | 0 |
| FROZEN_22 | opus-4-7 | 22 | 1.000 | 1.000 | 1.00 | 0 |
| FROZEN_22 | opus-4-6 | 22 | .844 | .728 | 1.36 | 0 |

Two facts here matter for Stage 1 and are **new**:

1. **Behavioural collapse is severe and asymmetric.** Median effective support is 1.0–1.4 of 4
   displayed options. Opus-5 is at effective support 1.00 on more than half of B42. A
   determinism-adjusted similarity statistic (`DATA_DICTIONARY` "Mandatory separation") is not
   optional here — the raw cross-model match will be dominated by how deterministic Opus is.
2. **A four-slot positional policy is rare but NOT absent.** `DISCOVERY4_REPORT.md` §4.1
   concludes "at four options neither model runs a stable positional policy" from 14 cells on
   B7. On the 406-cell B203 battery T1 finds **3 cells at `position_modal_share` >= .75**
   (max .917). The claim is right as a generalisation and wrong as an absolute; the frame must
   still measure position sensitivity per cell rather than assume it away.

Cross-model modal agreement and expected cross-match, recomputed from raw:

| set | arrays | modal agreement (gpt-5.5 vs opus-5) | mean expected cross-match |
|---|---|---|---|
| B203 (blind) | 203 | **.764** | **.698** |
| B42 (cue-conflict, built to induce asymmetry) | 42 | **.762** | **.701** |
| B8 (repair) | 8 | .625 | .643 |

The cue-conflict battery, designed specifically to manufacture GPT/Claude divergence, produced
**the same** aggregate agreement as the blind battery. That is a useful negative result — but it
does **not** license using B42 as an unconditioned frame, because its arrays were still
generated under a divergence-seeking hypothesis and its *within*-array structure was chosen to
make one model spread out.

---

## 6. Deviations and defects recorded

1. `model_x_array_coverage.csv` is keyed on **(battery, array, model, measurement)**, not
   (battery, array, model). A single array x model has up to three distinct measurements with
   different prompts and different permutation coverage; collapsing them would hide exactly the
   prompt-incompatibility and conditional-choice distinctions this audit exists to surface.
2. `make_battery.py`'s docstring ("15 families x 8 members = 120 stimuli") disagrees with its
   own output (16 x 8 = 128). The manifest and the rendered directories are authoritative.
3. `DURABILITY_INVENTORY_4OPT.md` is stale (see §0) and its §5 "available pool" should not be
   carried into Stage 1 without re-derivation.
4. B203 has **no frozen battery hash** and **no `mechanism` field**. Both must be created before
   `FROZEN_HASHES.json` can be populated.
5. `s4_common.ask_gpt` discards `r.usage`, so **GPT four-option spend has never been measured**
   in this tree — only estimated. Measured Claude anchors that do exist:
   `$0.005025/call` (opus-4-7 discovery, 1,044 calls) and `$0.004475/call` (opus-4-6 discovery,
   1,056 calls). The `$0.0153/call` anchor quoted in several study4 documents comes from the
   strategic pilot, whose prompts are much longer; it **overstates** the cost of a `d40ea45d`
   call by roughly 3x on the Claude side.
6. `older_claude_audit.py` imports `targeted_common` from
   `LLM_Coordination/Name_game_experiment/` — outside `Self_Coordination/`. It exists, but the
   four-option pipeline has a live dependency on a directory the study root does not own.
