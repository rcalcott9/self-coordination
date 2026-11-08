# Self-coordination paper: completion ledger (2026-10-09)

**State at writing:** no research jobs running (checked by process list). Nothing launched by this ledger.

**Bottom line:**
- No study needs new collection to support its claim.
- All remaining work is analysis and assembly.
- Every prepared-but-unrun collection is either dropped or held behind an explicit claim-dependent gate.

## Study 1 — CLOSE (own-coordinability knowledge)

| | |
|---|---|
| **Claim** | Reliability judgements (PLAY/PASS, symmetric scoring) track a model's own copy agreement. Models are not better than an auditor at predicting their own match rate. Their apparent self-advantage on option choice (1b) is compatible with projection. In Qwen, training a scenario toward 70/30 targets causally lowers PLAY on it, by a small amount and on top of a larger generic drop. |
| **Evidence, frontier** | **1a/1b low reasoning:** `study1_frontier_min_20261007` ($23.60) and `study1b_crossed_object_20261007` ($39.34), packaged in `Study1_frontier_package_20261008` (20/22 outputs reproduce).<br>**1a/1b high reasoning:** `study1_highreason_20261009` ($171.40). Opus P1 −.055 (auditor better); 1b +.235, p .002. |
| **Evidence, Qwen** | **Observational:** `plunkett_qwen/results/study1_final_20261009` (d′ .49, AUC .78).<br>**Causal:** `Stag/qwen_continuation_pilot_20261009` ($40.10). Agreement contrast D .231 [.215, .248]; PLAY β +.063 [.034, .093]; global PLAY drop −.14; selectivity .055 [.018, .092]. |
| **Indispensable collection** | **None.** |
| **Indispensable analysis** | **(a) Estimand.** The 1a PLAY/PASS prompt (`3b5fe054`) describes a same-presentation game, but y is independent-order agreement. Report same-presentation agreement as co-primary, computed from existing REF draws (48 over 24 orderings = 2 per ordering). The VIS-FRAME audit shows a large gap: low-reasoning LOW arm GPT .63 vs .43, Opus .87 vs .52.<br>**(b) Asset-audit fixes:** r = .07 is actually −.073; the Opus headline mixes configs; 20 coded traces are missing; prereg hashes changed after the freeze; the step-316 lr label is wrong.<br>**(c) Repackage** with the high-reasoning run and the continuation pilot, run with `PYTHONHASHSEED=0`. |
| **Final figure** | 2×3 (GPT \| Opus \| Qwen).<br>**Top row:** P(PLAY) vs own agreement, low and high reasoning; Qwen shows the observational Study 1 points.<br>**Bottom row:** 1b self-advantage for GPT and Opus. For Qwen, the continuation-pilot within-item clean−noisy PLAY contrast, with the generic drop marked. **This replaces the empty Qwen crossed-prediction panel and the α panel.** Data: `study1_figure_data_20261009` + `qwen_continuation_pilot_20261009/analysis/`. |
| **Stopping rule** | Closed when the figure and repackaged outputs regenerate from frozen data and the audit flags are resolved. No further Study 1 calls. |

## Study 2 — FREEZE (partner identity)

| | |
|---|---|
| **Claim** | Copy vs different-model framing shifts the reliability judgement without integrating with own-policy reliability. Explicit relational prediction is null: neither model conditions its partner prediction on identity. |
| **Evidence** | **Qwen:** `qwen_study2_playpass` v1/v2 (partner +.155 [.103, .206]; interaction −.059 [−.157, .044]) + logits ($3.06).<br>**Frontier PLAY/PASS 2×2:** `study_playpass_gpt`, `Stag/opus_playpass` (data file rows "1-2").<br>**Relational prediction:** `study2_relational_prediction_20260912` ($6.70; G GPT +.021, Opus −.000). |
| **Indispensable collection** | **None.** |
| **Indispensable analysis** | **(a) Opus label sensitivity.** The Opus 2×2 is thinking-adaptive, but its HIGH/LOW labels came from thinking-disabled runs (r .779 between configs). Recompute the labels from adaptive Stage A data, which already exist (`rational_agent_collection/audit/opus_thinking_check.csv`).<br>**(b) Freeze.** Hash the inputs, write RESULTS, build the figure. |
| **Final figure** | Per model, P(PLAY) by policy class × partner (interaction plot), plus a forest plot of relational G. |
| **Stopping rule** | Frozen after (a) and (b). No new calls. |

## Study 3 — bounded battery (converting reliability into payoff: PLAY/PASS Stag Hunt)

| | |
|---|---|
| **Claim** | Playing with copies, models do not reliably reach the policy-transfer benchmark B. Opus over-passes and GPT over-plays. Partner framing barely changes behaviour. Reasoning-on Qwen plays at ceiling. |
| **Battery (closed)** | **GPT-5.5 / Opus 5**, 10 arrays each, low reasoning COPY 30/cell + DIFFERENT 20/cell, plus high-reasoning COPY pilot 10/cell: `two_model_staghunt_20260916` ($10.14 + $10.54).<br>**Fable 5.1** on the Opus arrays: `fable_staghunt_20261008` ($8.17).<br>**Qwen step-316:** thinking-off `qwen_staghunt_pilot_20260916` ($0.11) and thinking-on `qwen_staghunt_thinking_20261008` ($7.70). |
| **Indispensable collection** | **None.** |
| **Indispensable analysis** | **(a) Benchmark estimand per prompt.** Frontier game prompts state that order is randomised independently, so B uses independent-order c (correct as is). The Qwen game prompt implies the same presentation, so recompute Qwen B with same-order agreement from existing Stage 0 data (10 draws per order).<br>**(b) Report the high-reasoning frontier arm as an exploratory pilot (10/cell, COPY only).** Not as a claim. |
| **Final figure** | V̂(COPY) vs B per array, one panel per model (GPT, Opus, Fable, Qwen off/on), with the PASS = 7 line. Inset: P(PLAY) COPY vs DIFFERENT. |
| **Stopping rule** | The battery is closed. Extending it requires a claim in the draft that the existing rows cannot support. |

## Prepared or proposed work: disposition

| item | cost | disposition | reason |
|---|---|---|---|
| Qwen reasoning-on follow-up (`qwen_continuation_pilot_20261009/reasoning_followup/`) | exp. $31–53, cap $68 | **DROP (keep files)** | Thinking-on is off step-316's training distribution. No claim needs it. |
| Qwen crossed-prediction panel (`study1_figure_data_20261009/QWEN_CROSSED_PROPOSAL.md`) | ≈ $0.60 | **DROP** | Fills a panel for symmetry. The continuation contrast takes that slot. |
| Proposal A matched-lottery / shared-eval pilot | ≈ 2k calls | **DROP** | The symmetric judgement has no risk confound to control. Self, auditor and PLAY/PASS now exist on one set (VIS-FRAME-41, both settings). |
| Qwen untrained screen, remaining 12 items | ≈ $3 | **DROP** | Fed only the reasoning-on weak arm. Report the 18/30 interim as is. |
| rational_agent Wave 1 (≈ $20) / Wave 2 core (≈ $30) | ≈ $50 | **DROP** | Built for the green-object Stag Hunt, which is not the reported paradigm. |
| `qwen_study2_relational` prediction step | small | **DROP** | Frontier relational null already answers Study 2. |
| Study 3 high-reasoning completion (DIFFERENT, 30/cell) | not costed | **DROP** unless the draft claims a reasoning effect in Study 3 | Symmetry with Study 1 only. |
| Name-game M=15/N=12 rerun | ≈ $58 | **Out of scope** | Different paper (Name Game). |

## Duplicates and reusable calibration

- **Reusable calibration:**
  - The VIS-FRAME-41 low-reasoning frame calibration is reused by 1a low. Labelled; do not re-collect.
  - High reasoning has its own fresh REF. 6 arrays share REF between 1a and 1b high (same prompt and settings), so it is reusable in both.
  - The continuation-pilot calibration (600 items × 2 orders × 20 draws × 3 checkpoints) is the only Qwen calibration with balanced orders. Reuse it for any Qwen Study 1 figure value.
- **Do not pool:**
  - Qwen original 316 (Study 1/2/3) vs replica 12f8e1b3 (α, continuation).
  - Opus thinking-disabled labels vs adaptive 2×2.
  - Low vs high Stage 0 in Study 3.
  - Opus 4.8 vs Opus 5.
- **Superseded:**
  - The α-scaling "intervention" rows in the Study 1 figure data: generic, superseded by the continuation pilot. Keep in the supplement.
  - The green-object Stag Hunt exports (`_green_version_not_used/`).
  - `RESULTS_incomplete_cap150.md`. Kept for provenance only.
  - The continuation pilot's percentile and "basic" CIs. Corrected CIs are canonical.

## Spend on record (studies above)

Study 1: $23.60 + $39.34 + $171.40 + $40.10 = **$274.44** (plus the earlier Qwen Study 1).
Study 2: $6.70 + $3.06 = **≈ $9.76** (plus the earlier 2×2 runs).
Study 3: $10.14 + $10.54 + $8.17 + $0.11 + $7.70 = **$36.66**.
Untrained screen (dropped line): $4.69.
**Remaining committed spend: $0.**

## Execution queue (no API calls)

1. **Study 1 estimand:** compute same-presentation agreement for 1a (low and high) from existing REF orderings, refit P1/P2/GLMM on it, and report as co-primary.
2. **Study 1 audit fixes:** sign, config separation, missing traces, hashes, lr label. Then repackage with high-reasoning + continuation and run `reproduce.sh`.
3. **Study 1 figure:** regenerate the 2×3 with the Qwen bottom panel = continuation contrast.
4. **Study 2:** Opus label sensitivity from adaptive Stage A → freeze RESULTS + hashes → figure.
5. **Study 3:** recompute Qwen B with same-order agreement; build the battery table and V̂-vs-B figure; label the high-reasoning frontier arm as a pilot.
6. **Gate (your call, not a task):** new collection only if the final draft states a claim with no evidence row above.
