# Analysis history

All times are local, 2026-10-07/08. The original documents are preserved in `docs/history/`.

## Study 1

| When | Event | Status |
|---|---|---|
| 21:14 | Collection and analysis plan finalised (`Study1_frontier_min_collection_plan.md`), with figures specified | Pre-data. **Not hash-frozen** at the time |
| 21:19 | `FROZEN.json` (`18853f3e`): prompts, schedules, models, gates. Old PLAY/PASS files hashed in `LEGACY_MANIFEST.json` | Pre-data |
| 21:19–21:23 | Preflight (8), parse pilot (48), anchor (328) plus drift gate | Gates passed |
| 21:28–21:43 | Main collection (2,296) | |
| ~21:45 | Analysis v1 (`analyze.py`) and `SUMMARY_v1.md` | v1 |
| ~21:46 | S2 CI corrected *before reporting*: arrays now resampled within arm | Logged |
| ~22:00 | Exploratory divergence analysis (`divergence.py`) | **Post hoc** |
| ~22:10 | Four-workstream analysis audit (`ANALYSIS_AUDIT.md`) | See corrections below |
| 22:09 (02:09Z) | Plan and analysis outputs hashed **retrospectively** (`RETRO_HASHES.txt`) | Post-data |
| ~22:15 | `SUMMARY_v2.md`. No numbers changed | v2 |

**Audit corrections in v2.** Results were preserved; only estimators, labels and wording changed.

| v1 | v2 |
|---|---|
| S1 reported with a pooled binomial GLM, on the claim that the GLMM was "unstable" (never tested) | The planned GLMM fits; it is now primary. The GLM is kept as a population-averaged sensitivity analysis |
| "no drift" | "the drift test did not detect drift", with a power table |
| "GPT shows no self-advantage" | "no self-advantage was detected", with the CI's range stated |
| "Opus small self-advantage…" | "borderline (Holm p ≈ .05), not established" |
| P2 permutation p printed as 0 | (k+1)/(N+1): ≤ .001, and .0015 for the GPT auditor |
| Holm family ambiguous | The conclusion is identical under every reading |

## Study 1b

| When (UTC, 2026-10-08) | Event | Status |
|---|---|---|
| 02:20 | `FROZEN_SCREEN` (`4c411796`): 57 candidates. Prompts and selection rules finalised | Pre-data |
| 02:22 | `STUDY1B_FINAL_DESIGN.md` and power hashed in `HASHES.txt` | Pre-data |
| 02:27 | **Amendment 1** frozen and hashed: primary sample S1 + S2; pooled self-minus-cross Brier; S3 and moderation secondary; p denominator = simulated flips | Pre-screening |
| 02:27–02:34 | Screening (2,736 calls) | |
| ~02:35 | Stage handling added to the runner for the existing preflight and pilot gates; selection frozen (`26eb30e6`); `FROZEN_MAIN` (`9e11e56e`) hashes the selection and the amendment | Implementation only |
| 02:36 | Preflight 6/6 and pilot 32/32 | Gates passed |
| 02:37–02:50 | Main collection (2,560) | |
| ~02:55 | Pre-specified analysis (`analyze.py`) | Primary as amended |
| ~02:58 | Projection diagnostic and exact sign-flip p | **Post hoc / exploratory** (scripted later as `projection_diagnostic.py`) |
| ~03:10 | Family-level sensitivity (`family_sensitivity.py`); RESULTS v2 interpretation edits (predictive vs relational; moderation described as descriptive; projection described as "compatible with") | **Post hoc**. The frozen primary is unchanged |
