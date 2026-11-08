#!/usr/bin/env bash
# One-command reproduction of every reported Study 1 / Study 1b number and figure from packaged data.
# No API calls. Usage:  ./reproduce.sh [python]   (default python: python3 with numpy scipy pandas statsmodels matplotlib)
# Needs R with lme4 for the GLMM audit. Runtime ~15-25 min (bootstraps, power simulations).
set -euo pipefail
PKG="$(cd "$(dirname "$0")" && pwd)"; PY="${1:-python3}"
export S1PKG="$PKG" HOME="$PKG/home" PYTHONPATH="$PKG/repro" MPLBACKEND=Agg PYTHONHASHSEED=0
S1="$HOME/Desktop/Coordination/Self_Coordination/study1_frontier_min_20261007"
S1B="$HOME/Desktop/Coordination/Self_Coordination/study1b_crossed_object_20261007"
LOG="$PKG/reproduction_log.txt"; : > "$LOG"
run() { echo "== $*" | tee -a "$LOG"; "$@" >> "$LOG" 2>&1 || { echo "FAILED: $*" | tee -a "$LOG"; exit 1; }; }
mkdir -p "$S1/analysis/out" "$S1B/analysis/out" "$PKG/reproduced/scratch"
# ---- Study 1 (frontier minimal) ----
run "$PY" "$S1/code/analyze.py"
run "$PY" "$S1/code/anchor_check.py"
run "$PY" "$S1/code/divergence.py"
run "$PY" "$S1/analysis/audit/A_bootstrap/audit_A.py"
run "$PY" "$S1/analysis/audit/B_ordering_multiplicity/check_B.py"
run "$PY" "$S1/analysis/audit/C_glm/make_trials.py"
( cd "$S1/analysis/audit/C_glm" && Rscript glmm.R > glmm_output.txt 2>&1 && Rscript glmm_opus_adj.R > glmm_opus_adj_output.txt 2>&1 ) \
  && echo "== Rscript glmm.R / glmm_opus_adj.R" | tee -a "$LOG" || { echo "FAILED: R GLMM" | tee -a "$LOG"; exit 1; }
run "$PY" "$S1/analysis/audit/D_drift/drift_audit.py"
# ---- Study 1b (crossed object-level prediction) ----
run "$PY" "$S1B/code/analyze.py"
run "$PY" "$S1B/code/family_sensitivity.py"
run "$PY" "$S1B/code/projection_diagnostic.py"
( cd "$PKG/reproduced/scratch" && "$PY" "$S1B/design/final/power_final.py" >> "$LOG" 2>&1 ) && echo "== power_final.py" | tee -a "$LOG"
# ---- compare with reported outputs ----
"$PY" "$PKG/repro/compare.py" | tee -a "$LOG"
