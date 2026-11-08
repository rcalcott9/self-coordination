# TEAM TASKS — proposed. NOT YET SPAWNED. Awaiting lead/user approval.

Isolation model: **strictly non-overlapping directories** (git worktrees unusable — see
DECISION_LOG D-003). Every teammate works inside ONE directory and may not write outside it.

Universal prohibitions (all teammates):
- MUST NOT modify frozen data or overwrite existing results anywhere under `Self_Coordination/`.
- MUST NOT edit another teammate's directory.
- MUST NOT edit the lead-owned control files: MASTER_DESIGN.md, DATA_DICTIONARY.md,
  RUN_LEDGER.csv, DECISION_LOG.md, FROZEN_HASHES.json, TEAM_TASKS.md, STATUS.md (read-only).
- MUST NOT change shared schemas, prompts, or thresholds.
- MUST NOT make API calls (T1,T2,T3,T5 = none; T4 = none without explicit lead approval).
- MUST NOT spawn further teammates.
- MUST submit a plan for lead approval before any material edit.

| # | name | task | directory (write) | may read | API | depends on | done when |
|---|---|---|---|---|---|---|---|
| T1 | visual-auditor | audit every 4-option battery + chooser measurement | `audits/visual/` | whole tree, read-only | none | — | coverage table, battery audit, sampling-frame recommendation, missing-cell list, selection-bias warnings |
| T2 | code-designer | design 30-40 four-option code-convention items | `code/design/` | own dir + MASTER_DESIGN | none | — | items + schema, each option functionally valid, canonical-identity scorable |
| T3 | code-redteam | independent rejection rubric, then audit T2 | `audits/code/` | T2 dir READ-ONLY | none | rubric first; audit after T2 | rubric + item-level accept/flag/reject with repairs |
| T4 | model-surface-auditor | largest defensible callable checkpoint panel + common request surface | `audits/models/` | whole tree, read-only | none w/o approval | — | per-checkpoint table, compatibility strata, cost estimates |
| T5 | analysis-engineer | Stage 1 analysis spec + implementation on synthetic/existing data | `analysis/` | read existing runs | none | — | spec + code + synthetic validation; separates determinism from similarity |

Notes:
- T3 must not edit T2's files; it writes a separate audit. T3 may begin its rubric immediately.
- T5 must not use new API data.
- T1's sampling frame must NOT be selected on GPT-strong / shared / divergent / previously
  successful arrays. Broad frame required.
