# Frontier Study 1 package (Study 1 and Study 1b)

GPT-5.5 (`gpt-5.5-2026-04-23`, reasoning effort low) and Claude Opus 5 (`claude-opus-5`, thinking disabled). Collected 2026-10-07/08. Packaged 2026-10-08 with no new API calls.

## Contents

| Path | What it contains |
|---|---|
| `docs/METHODS.md`, `docs/RESULTS.md`, `docs/LIMITATIONS.md` | Manuscript sections. Each analysis is labelled pre-specified, audit-corrected or post hoc |
| `docs/ANALYSIS_HISTORY.md` | Timeline of plans, freezes, data, analyses, audit corrections and amendments |
| `docs/SUPPLEMENT.md` and `docs/supplement/*.csv` | Supplementary tables S1–S9 (integrity and cost, all prompts, per-array tables, drift audit, screening and selection, families, Study 1b contrasts) |
| `docs/history/` | Original documents as written: plan, SUMMARY v1/v2, divergence note, analysis audit, retrospective hashes, Study 1b design, Amendment 1, hashes, RESULTS v1/v2 |
| `docs/REPRODUCTION_REPORT.txt` | Output of the last verification run |
| `home/Desktop/…` | Self-contained mirror of the original project layout (below) |
| `reported/` | The outputs as originally reported; `reproduce.sh` compares against these |
| `repro/` | Reproduction sandbox (`sitecustomize.py`), comparison script (`compare.py`), supplement builder |
| `reproduce.sh` | One-command reproduction |
| `MANIFEST.sha256` | sha256 of every file in the package |

The mirror under `home/Desktop/Coordination/Self_Coordination/` contains:
- `study1_frontier_min_20261007/`:
  - `design/`: `FROZEN.json` with prompts, schedules and gates, plus `LEGACY_MANIFEST.json`;
  - `runs/`: all raw responses (preflight, pilot, anchor, main) with full provenance;
  - `code/`: runner, prompts, freeze, analyse, anchor check, divergence;
  - `analysis/audit/`: audit scripts A–D, the GLMM R scripts, and `trials.csv`.
- `study1b_crossed_object_20261007/`:
  - `design/`: `FROZEN_SCREEN.json`, `SELECTION.json`, `FROZEN_MAIN.json`, `final/` (design, amendment, power, hashes), `inventory/`;
  - `runs/`: screen, preflight, pilot, main;
  - `code/`.
- `study_policy_convergence_20260909/`: the reused frame calibration responses (`visual_frame_20260909_204609.csv`), `pc_common.py`, the VIS-FRAME-41 list, and frame cell metrics.
- `study2_4opt_20260830/`: stimuli for the **88 arrays used** (24 orderings each, with manifests), the battery manifest, and `s4_common.py`, the source of the reference prompt.
- `study_playpass_gpt/` and `../Superrationality/Stag/opus_playpass/`: the old PLAY/PASS data, preserved unchanged and listed in `LEGACY_MANIFEST.json`.

API keys and `.env` files are **not** included. Collection code is packaged for provenance; re-collecting would need your own keys and would not reproduce outputs exactly, because the models sample stochastically.

## Reproduce

```
./reproduce.sh /path/to/python      # python with numpy, scipy, pandas, statsmodels, matplotlib; R with lme4
```

**What it does:**
- Runs every analysis and figure script on the packaged data, in about 8 minutes.
- Sets `HOME` to the package mirror and `PYTHONHASHSEED=0`.
- Loads a sandbox that remaps the absolute paths recorded in the frozen JSON files into the package. An audit hook makes any file read outside the package an error.
- Ends with `repro/compare.py`, which checks numbers (relative tolerance 1e-9), CSV cells, PNG pixels and R output lines against `reported/`.

**Verified 2026-10-08** with Python 3.12.7 (Anaconda; numpy, scipy 1.13.1, statsmodels 0.14.2, matplotlib 3.9.2, pandas 2.2.2) and R 4.4 with lme4 1.1.35.5. **20 of 22 reported outputs reproduced exactly**: every Study 1 table, figure and audit output; every Study 1b figure, item table, family analysis, projection diagnostic and power table; and every primary and secondary number in Study 1b.

## Concrete missing assets and reproduction failures

1. **`reported/study1/audit/B_ordering_multiplicity/multiplicity.json`: no generating script.** The audit agent computed the Holm-by-family table inline; `check_B.py` writes only `B_checks.json`. The values (Opus P1 Holm ≈ .05 under every family definition) are documented in `docs/history/ANALYSIS_AUDIT.md` but cannot be regenerated from packaged code.
2. **`reported/study1/audit/C_glm/glm_boot_output.txt`: no generating script.** The S1 GLM uncertainty diagnostics (Pearson dispersion, quasi-binomial Wald, array-only bootstrap) were computed inline. The GLMM outputs (`glmm.R`, `glmm_opus_adj.R`) do reproduce exactly.
3. **Study 1b sensitivity: the hierarchical-bootstrap CI is not exactly reproducible.**
   - Cause: `study1b…/code/analyze.py` iterates over `set(xs)`, whose order depends on Python's hash seed, so random draws are consumed in a different order on each unseeded run.
   - Values seen: reported [.111, .421] (RESULTS v1/v2); last analysis run, packaged in `reported/`, [.118, .412]; reproduction with `PYTHONHASHSEED=0` [.117, .416], which is deterministic across repeated runs.
   - Every other Study 1b number is unaffected, including the frozen primary, the exact p-values, the family analysis and the log-score and mixed-model sensitivities. The conclusion is unchanged. No code was changed.
4. **Study 1b design-phase candidate inventory** (`design/inventory/inventory.py`) is packaged with its outputs, but its inputs are not: the 203-array stage-A battery data and `model_x_array_coverage.csv`. It informed the frozen thresholds and nominations only; no reported result depends on it.
5. **`trials.csv` order.** The audit built it inline. The packaged `make_trials.py` rebuilds it with identical rows in a different order; `reproduce.sh` runs the GLMMs on the packaged original so that parametric-bootstrap draws match exactly.
