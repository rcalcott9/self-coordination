# Self-coordination paper: completion ledger v2 (2026-10-09)

- **Supersedes:** `COMPLETION_LEDGER_20261009_v1_SUPERSEDED.md`. Corrections to v1 are listed at the end.
- **Provenance:** every row was checked against run files (frozen JSON, run manifests, response files).
- **No calls launched.** No research process is running (process list checked).

## A. Can the paper be assembled from existing data? YES, for Studies 1–3 as scoped below

### Study 1: own-coordinability knowledge (frontier 1a/1b + Qwen)

| | provenance (exact) | status |
|---|---|---|
| **1a low** | `study1_frontier_min_20261007`, FROZEN `18853f3e`. Prompts verified in FROZEN.json: CALIB `d40ea45d`, PLAYPASS `3b5fe054`, SELFPRED `433b4569`. **All three state "the left-to-right order … is randomized independently for each of you".** Calibration reused from `visual_frame_20260909_204609.csv` (sha aa5e91d9…; estimand "within_model_match (independent-order dyadic match)", 48/array). 2,680 calls, $23.60. | complete |
| **1b low** | `study1b_crossed_object_20261007`, FROZEN_SCREEN `4c411796`. 5,334 calls, $39.34. | complete |
| **1a + 1b high** | `study1_highreason_20261009`, FROZEN `933aa87d` + Amendment 1 (budget only). Same `d40ea45d`/`3b5fe054`/`433b4569` texts; auditor/prediction clause names the high configuration. 8,324 calls, $171.40. | complete (authorised resume finished, 0 fails) |
| **Qwen observational** | Original step-316 (`2d50363f…/step316`). Study 1 run `plunkett_qwen/results/s1_20260911_132831`; truth `predict_20260911_123902`; final `results/study1_final_20261009`. | complete |
| **Qwen intervention** | Replica `12f8e1b3…/weights/state316` → V1 `40e61320…/qcp_V1_step157`, V2 `88bcef52…/qcp_V2_step157`. Spend: training 2 × $14.2811, calibration 3 × $1.1344, PLAY/PASS $7.948, plus unlogged ≈ $0.19 (restore check + 2 crashed one-step launches) → **≈ $40.10**. | complete (both authorised phases finished) |

**Matching quantity: no change.** The corrected 1a prompts specify independent order, so the frozen independent-order primary is the correct estimand. v1's proposal to make same-presentation agreement co-primary was wrong and is withdrawn.

**Essential analysis (no calls):**
- Resolve the asset-audit flags: r = .07 is actually −.073; the Opus headline mixes configs; 20 coded traces are missing; prereg hashes changed after the freeze; the step-316 lr label is wrong.
- Repackage with the high-reasoning run.

**Figure (2×3):**
- **Top row:** P(PLAY) vs own agreement. GPT and Opus at low and high reasoning; Qwen observational.
- **Bottom row:** option-choice self-advantage (1b) for GPT and Opus.
- **Qwen bottom-right: ABSENT.** There are no Qwen crossed option-choice predictions. The training effect (continuation PLAY contrast, recovery r) is **not** choice self-advantage and must not fill this panel. Show the continuation result as its own labelled panel ("Qwen: PLAY/PASS after training-induced reliability change"), in Study 1 or the supplement.

### Study 2: partner identity

| | provenance | status |
|---|---|---|
| Frontier PLAY/PASS COPY/DIFFERENT 2×2 | `study_playpass_gpt` (`playpass_full_20260912_191607`), `Stag/opus_playpass` (`parallel_disabled_191726` + adaptive 2×2) | complete |
| Qwen PLAY/PASS partner | `qwen_study2_playpass` v1 `pp2x2_20260912_173541`, v2 `plunkett_qwen/results/s2_20260912_181428`, logits `logit_s2_20260913_185259` ($3.06) | complete |
| Relational prediction | `study2_relational_prediction_20260912` (440 calls, ≈ $6.70; null) | complete |

**Verified prompt issue (legacy runs only):**
- The legacy frontier PLAY/PASS prompt (`study_playpass_gpt/code/run_playpass.py`) says the copy/other model "sees the EXACT SAME stimulus … presented the same way".
- Its HIGH/LOW labels, however, come from independent-order agreement.

**Essential analysis (no calls), labelled sensitivity:**
- **(a)** Same-presentation agreement for the legacy items, computed from the existing 48-draw frame calibration (2 draws per ordering). The audit's LOW-arm values were GPT .63 vs .43 and Opus .87 vs .52.
- **(b)** Opus HIGH/LOW labels recomputed from adaptive Stage A data (`rational_agent_collection/audit/opus_thinking_check.csv`).
- Frozen primaries are unchanged.

### Study 3: PLAY/PASS Stag Hunt battery

| | provenance | status |
|---|---|---|
| GPT-5.5 / Opus 5, 10 arrays each | `two_model_staghunt_20260916`: pilot $10.139; extensions $10.54 (low COPY to 30/cell; high-reasoning COPY pilot 10/cell). Game prompt `49e35910` states independent order, so B uses independent-order c (correct as frozen). | complete |
| Fable 5.1 on the Opus arrays | `fable_staghunt_20261008`, $8.165 | complete |
| Qwen step-316 thinking off | `qwen_staghunt_pilot_20260916`, $0.105 (+ $0.007 calibration) | complete |
| Qwen step-316 thinking on | `qwen_staghunt_thinking_20261008`, $7.698 | complete |

**Essential analysis (no calls):**
- The Qwen game prompt implies the same presentation ("the same two options"). Add same-order Stage 0 agreement as a labelled sensitivity next to the frozen pooled B; the existing data have 10 draws per order.
- Report the high-reasoning frontier arm as an exploratory pilot.

## B. Is the planned paper complete? NO

Searched: all project folders, `~/Downloads` documents, project context, and Claude Code logs.

| planned component | evidence on disk | status |
|---|---|---|
| **Simultaneous Battle of the Sexes** | **None.**<br>- No design, runner, prompt or response file.<br>- The only hits are model reasoning texts that mention the game, plus Akata et al.'s third-party **repeated** PD/BoS human dataset (`LLM_Coordination/data/repeatedgames`), which is not our collection.<br>- No spec for the planned study was found. | **ABSENT** |
| **Executable applied task 1** | **None executable.**<br>Nearest existing text-only pilot: `open_set_rendezvous_20260906` (online rendezvous; 1,080 responses).<br>- The frozen verdict is **NO-GO**.<br>- A post-hoc Amendment 01 passes criterion (d).<br>Whether this is the planned task is unconfirmed. | **ABSENT** as executable; pilot only |
| **Executable applied task 2** | **None executable.**<br>Nearest: `monitored_schelling_20260905`, Phase 1 screening only.<br>- Its design states the strategic monitored condition is **not implemented**.<br>Whether this is the planned task is unconfirmed. | **ABSENT** as executable; screening only |

These three components cannot be costed: no specification exists on disk. Cost and design need the spec.

## C. Status of previously authorised and prepared jobs

| job | authorisation | status |
|---|---|---|
| Study 1 high-reasoning 1a/1b (+ Amendment 1 +$35) | authorised | **complete**: 8,324/8,324 calls, $171.40 |
| Qwen continuation training + calibration (cap $40) | authorised | **complete**: $32.15 incl. unlogged ≈ $0.19 |
| Continuation PLAY/PASS (hard cap $16) | authorised | **complete**: 14,400 decisions, $7.948 |
| Qwen untrained screen, thinking on (cap $10) | authorised 2026-10-08 | **INCOMPLETE**: 360/600 draws, $4.69. Stopped by Tinker HTTP 402. Process killed before writing failure rows, so 24 cells are resumable (≈ $3). Not cancelled by you; v1's "DROP" was only a recommendation. |
| Reasoning-on follow-up (`reasoning_followup/`; caps $40 + $28) | **prepared only** (asked to prepare and return costs) | not run, $0 |
| Qwen crossed-prediction proposal (≈ $0.60, cap $3) | proposed | not run |
| rational_agent Wave 1 / Wave 2 (≈ $20 / ≈ $30) | prepared 2026-09-15, never approved | not run |
| `policy_specific_self_coordination_20260812_1401` | "built and validated; NOT launched — awaiting approval" | not run |

## D. Essential remaining work and cost

| # | work | needed for | cost |
|---|---|---|---|
| 1 | Study 1 audit-flag fixes + repackage (high reasoning included) | A | $0 |
| 2 | Study 1 figure, with the Qwen choice-self-advantage panel marked absent and the continuation result in its own labelled panel | A | $0 |
| 3 | Study 2 sensitivities: legacy same-presentation agreement; Opus adaptive labels | A | $0 |
| 4 | Study 3 Qwen same-order B sensitivity; battery table + V̂-vs-B figure | A | $0 |
| 5 | **Supply the specs** for simultaneous BoS and the two executable applied tasks | B | — |
| 6 | Design + collection for those three components | B | not costable until (5) |

- **Existing-data paper (A):** $0 remaining.
- **Planned paper (B):** blocked on missing specifications. Nothing is launched or proposed here beyond identifying the gap.

## Corrections to v1

1. **Withdrawn:** "1a PLAY/PASS describes same-presentation; make it co-primary." The corrected prompts state independent order. The same-presentation wording belongs only to the **legacy** PLAY/PASS runs (Study 2 data); it is now handled as a sensitivity there.
2. **Withdrawn:** filling the Qwen bottom-row (choice self-advantage) panel with the continuation training effect. The panel is now marked absent.
3. **Corrected:** the untrained screen is authorised and incomplete (resumable), not "dropped". The reasoning-on follow-up is prepared-only, not authorised.
4. **Added:** Battle of the Sexes and executable applied tasks are absent. Existing-data assembly is now separated from planned-paper completeness.
5. **Corrected:** exact costs from manifests (continuation ≈ $40.10 = $39.913 logged + ≈ $0.19 unlogged).
