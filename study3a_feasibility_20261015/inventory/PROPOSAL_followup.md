# Study 3A follow-up — PROPOSED (2026-10-15) — SUPERSEDED by PROPOSAL_followup_v2.md

Not authorised and not launched. Study 3A only.

## 1. Inventory of existing in-game actions
Source files: `inventory_cells.csv` (152 source cells) and `inventory_pooled.csv` (101 item × model × effort × condition cells), built by `build_inventory.py`.

- **Included:** only rows whose prompt is an archived 3A game prompt, COPY `49e35910` or DIFFERENT `8222a371`. 1,000 reference-task (Stage 0) rows were excluded by prompt hash. Every action is PASS or PLAY with a canonical object 0–3. All 152 cells' images match the canonical `study2_4opt_20260830/stimuli` PNGs.
- **Runs:**
  - `two_model_staghunt_20260916`: GPT-5.5 and Opus 5, low effort, COPY + DIFFERENT. Also a COPY-only high-effort pilot.
  - `gpt_staghunt_pilot_20260916`: GPT-5.5, low effort.
  - `fable_staghunt_20261008`: Fable 5.1 on the Opus items.
  - `study3a_feasibility_20261015`: GPT-5.5 and Opus 5.
- **GPT configuration:** identical across runs. Requested `gpt-5.5`, returned `gpt-5.5-2026-04-23`, effort low, summary auto, no output cap, text before image.
- **Opus configuration:** `claude-opus-5` (no dated id), adaptive thinking (summarized), effort low, max_tokens 4000.
- **Excluded:** Qwen (two-option text scenarios, not the visual items), every GREEN-game run, SHAPES and M07.

## 2. Candidate items and selection rule (fixed before any new outcome)
- **Candidates:** all 19 items with existing low-effort GPT-5.5 in-game COPY actions. No item is selected, dropped or replaced on outcomes.
- **Historical labels** (two_model bins; gpt_staghunt_pilot CLEAR/WEAK) are carried only as a provenance column. They are never used as current strength labels.
- **Current policy strength** is computed from the partner-policy sample only, never from evaluation draws:
  - s = max_j q_COPY(PLAY j);
  - PLAY-advantage indicator 10·s > 7.
- **Every one of the 19 items is reported** in a single table. Columns:
  - item and historical label (with its source);
  - n policy / focal / fresh per condition, plus invalid, refusal and failure counts;
  - the full COPY and DIFFERENT partner distributions (PASS, PLAY0–3);
  - BR, normalized regret [CI], normalized payoff [CI], match rate, focal PASS rate;
  - status.

## 3. Smallest follow-up (focal GPT-5.5; partners as in the pilot)
| sample | source | new calls |
|---|---|---|
| Evaluation, focal COPY | archived GPT COPY draws (19–78 per item) | 0 |
| Evaluation, focal DIFFERENT | archived GPT DIFFERENT draws (19–39 per item) | 0 |
| COPY realized payoff | U-statistic over distinct pairs of the evaluation draws (same distribution) | 0 |
| **DIFFERENT partner policy (Opus)** | new, 24 per item on 13 items; archived on F05_orient_m1 and F36_split_m0 (n = 20) | **312** |
| **DIFFERENT fresh partners (Opus)** | new, 12 per item on 15 items | **180** |
| COPY partner policy, option (i) | seeded split of archived GPT COPY draws into policy and evaluation halves | 0 |
| COPY partner policy, option (ii) | new GPT COPY policy draws, 24 per item on 15 items | 360 |

The 4 pilot items (F01, F02_m2, F27, F41_m2) are already complete and need no new calls.

- **Core (Opus only): 492 calls**, about $3.24 at the pilot's mean per-call cost ($5.12 at the maximum observed per call).
- **Core + option (ii): 852 calls**, about $6.95 ($13.79 at the maximum).
- Cumulative Study 3 spend is $4.75 now, so even the maximum stays under the recorded $20 cap.
- Same archived prompts, settings and stimuli; positions shuffled independently; no prediction calls.

## 4. Remaining scientific decisions
1. COPY policy separation: option (i) (no calls; about 10 policy draws on the 19–20-draw items) or option (ii) (+360 calls; n = 24 policy on every item). **Recommend (ii).**
2. Pooling across time: archived September draws (GPT is a pinned snapshot; Opus is an undated alias) with new October Opus draws. Accept, or recollect the 2 archived Opus policy cells (+48 calls)?
3. Strength summary: is s from the policy sample, with the 10·s > 7 indicator, the right descriptive? It is not a selection rule.
4. Uncertainty for unanimous cells: the bootstrap is degenerate there. A Dirichlet/Jeffreys posterior interval for q, and therefore for BR, is proposed.
5. Primary outcome: normalized regret is approved in direction only; the normalization and companion measures are not frozen.
6. Scope: GPT-focal only. An Opus-focal arm would need GPT DIFFERENT partner draws on the Opus items and is out of scope here.
7. DIFFERENT wording: keep the archived generic, truthful "another AI model that was trained on different data", or name the partner?
8. Cap: which applies to this follow-up, the recorded $20 cumulative cap or "up to $50"?
