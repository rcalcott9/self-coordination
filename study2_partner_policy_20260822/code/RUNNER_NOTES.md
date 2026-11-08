# study2_betting.py — what it reads, what it refuses, what is still unreconciled

Re-pointed 2026-08-22 from the SUPERSEDED pair-based design onto the frozen stimulus
GRADIENT (STUDY2_SPEC_FROZEN.md §14.1). Everything below is either an assumption the
runner makes about a sibling agent's output or a rule the analysis depends on. If a
line is wrong the fix is a one-line change here, not a redesign.

## 0. What changed, and what deliberately did not

| kept, unchanged | re-pointed |
|---|---|
| one partner-clause template with a single name substitution, so the two arms are byte-identical after normalising the name, and the decision layer is byte-identical to Study 1's Stage C | cells now come from `design/frozen_design_table.csv`, not `pairs/study2_candidate_pairs.csv` |
| exact AB/BA balance per cell, `build_jobs` byte-identical to `psc_common.build_jobs` at uniform n | per-cell n is read from the table and **varies** (8 / 16 / 30 / 40); nothing global remains |
| resume by part file: a cell is complete only inside ONE file, two partials never merge | completion is judged at **that cell's own n** |
| `--estimate`, `--dry-run` as default, `--live` as the only way to spend money | the approved-pairs gate is replaced by the **confirmation gate** |
| output schema as a strict superset of Study 1's Stage C `psc_common.COLS` | `pair_id` / `stimulus_level` are gone; `tier`, `compatibility_advantage`, `advantage_source`, `provisional_advantage`, `confirmed_advantage` are added |

Removed with the pair design: `load_pairs`, `resolve_columns`, `PAIR_ALIASES`,
`load_power_config` and the `design/*.json` override, `N_PER_CELL`, `--n`,
`--safe-values`, `--n-per-payoff`. The allocation is frozen; a flag that could change
it would be a way to break the freeze.

## 1. The design table — `design/frozen_design_table.csv`

Emitted and validated by `code/design_table.py` from `design/FROZEN_PARAMS.py`. The
runner **re-validates on load** rather than trusting the file:

| check | behaviour on failure |
|---|---|
| file exists | abort, pointing at `design_table.py` |
| required columns present (`actor_model`, `stimulus`, `tier`, `partner_condition`, `partner_model_named`, `safe_payoff`, `n_cell`, `provisional_advantage`, `confirmed_advantage`) | abort, listing what is missing |
| `actor_model ∈ {gpt, claude}`, `partner_condition ∈ FROZEN_PARAMS.PARTNER_CONDITIONS`, `tier ∈ GRADIENT` tiers, `safe_payoff ∈ SAFE_PAYOFFS` | abort |
| `n_cell` positive and **even** | abort — AB/BA could not be exact |
| `partner_model_named` equals `DISPLAY[actor if same else OTHER[actor]]` | abort — a crossed-up condition label is the single most damaging possible bug here, so it is checked on every row, not trusted |
| no duplicate `(actor, stimulus, partner, payoff)` | abort |
| total calls == `FROZEN_PARAMS.stage_c_calls()` (2,976) | abort unless `--design` points somewhere else (`strict_total` is off for an explicit override, so tests and staged sub-tables still work) |

Cell key is `actor | stimulus | partner_condition | safe_payoff` — four fields, no pair
component. Old part files from the superseded design cannot collide with it, and the
scan is restricted to the cells the current invocation plans anyway.

## 2. The confirmation gate — the replacement for `approved == True`

A **live** run is refused unless all three hold:

1. `design/confirmed_compatibility.csv` exists and parses;
2. `design/CONFIRMATION_RESULTS.md` records a **passing** verdict;
3. every planned `(actor, stimulus)` has a confirmed advantage — an empty
   `confirmed_advantage` is a configuration error, never a silent fallback to the
   provisional value (§8 of the spec).

A **dry run** needs none of this: it prints the gate state, falls back to the
provisional advantage wherever a confirmed one is missing, and records which it used in
`advantage_source`.

**Assumed formats (written against the sibling's `code/confirm_compat.py`).**

- `confirmed_compatibility.csv` — WIDE: one row per `stimulus` with `advantage_gpt` /
  `advantage_claude` (this is what the sibling writes). A LONG form (`actor` +
  `confirmed_advantage`/`advantage`) is also accepted. Anything else is reported as
  UNREADABLE and the gate stays shut — the format is never guessed at.
- `CONFIRMATION_RESULTS.md` — the verdict is read from the headline, case-insensitively:
  PASS on `"Stage C MAY PROCEED"` or `"GATE VERDICT: PASS"`, FAIL on
  `"MUST NOT PROCEED"` / `"the gate FAILS"` / `"GATE VERDICT: FAIL"`. A report with no
  recognised verdict line is `unknown`, which does **not** open the gate.
- `confirmation_gate.csv` — optional; per-cell rows with `actor` and `pass_sign`, ANDed
  within actor. Used only for the §7.1 single-actor branch.
- Fallback source for the values: the design table's own `confirmed_advantage` column,
  which `confirm_compat.fill_design_table()` also writes.

**Section 7.1 single-actor branch.** `--single-actor-gate` **with** `--models` proceeds
live for an actor whose own critical cells passed even though the overall verdict is a
failure. It is refused without `--models`, and refused for an actor whose own cells
failed. Nothing else may proceed after a failed gate.

**State as of 2026-08-22 17:2x** (recorded because it decides whether Stage C may run at
all): the sibling's confirmation screen has landed and its verdict is **FAIL** —
`claude`/`mirror` moved to |adv| = 0.114, off the zero floor, and the claude critical
order does not hold; `gpt` passes on its own. So the runner currently refuses `--live`
outright, and `--live --models gpt --single-actor-gate` is the only branch it would
accept. Whether to take that branch is a design decision for the spec owner, not a
runner setting; §7.1's own table says a `G4` failure is a STOP-and-re-freeze.

## 3. Output schema and the conflict with `study2_schema.py`

Columns are `psc_common.COLS` verbatim and in order, then:

`tier`, `compatibility_advantage`, `advantage_source`, `provisional_advantage`,
`confirmed_advantage`, `partner_condition`, `partner_model_named`, `partner_model_id`,
`partner_condition_text`, `n_per_cell`, `cell_key`, `study`.

`compatibility_advantage` is the confirmed value where available and the provisional one
otherwise; `advantage_source` is `"confirmed"` or `"provisional"` on every row, so the
analysis never has to infer which it got. Both underlying values are also carried.

### UNRECONCILED with the sibling analysis agent (recorded, not silently resolved)

1. `study2_schema.COLS` still lists **`pair_id` and `stimulus_level`** from the
   superseded pair design. The runner no longer emits them — §14.1 says to replace them
   with `tier` and `confirmed_advantage`, which is what happened. The schema's own text
   marks both as REQUIRED-OR-DERIVED, so an analysis that derives rather than demands
   them is unaffected; an analysis that hard-requires them will fail at load. **The
   schema half of §14.1 is still to be done by the analysis agent**, and
   `test_study2.py` §4 reports this as a NOTE rather than a failing check.
2. The runner emits **`advantage_source`**, which `study2_schema` does not declare.
   `DOSE_COLS` (`compatibility_advantage`, `tier`) are emitted as declared.
3. `study2_schema.ADVANTAGE_TOL` says the analysis re-derives the analysed advantage
   from the confirmation counts and only compares the runner's column against it. That
   is the right precedence and the runner does not contest it: its column is provenance.

## 4. Resume semantics (the rule the analysis depends on)

- Each invocation writes its own `data/study2C_<ts>.csv` / `.jsonl` **part file** holding
  only the cells it ran.
- A cell counts **complete** only if **one single part file** holds ≥ **that cell's own
  n** rows with `included_in_analysis=True`. Counts are never summed across files — two
  half-finished runs of a cell do not add up, because each run has its own AB/BA prefix.
- A **partial** cell is re-run from scratch and its rows are excluded from the merge. The
  runner prints every partial cell with its row count and that cell's target.
- When more than one part file contributes, `study2C_MERGED_<ts>.csv` is written with one
  source file per cell.
- `--min-valid-frac 0.95` relaxes the bar **per cell** — 38/40 completes an n=40 cell,
  8/8 is still required of an n=8 cell. Default is 1.0, strict.
- `_DRY` and `MERGED` files are never counted as progress, and the scan is restricted to
  the cells this invocation plans.
- Verified end to end 2026-08-22 on an isolated `PSC_EXP_DIR`: with one cell short by
  three valid rows, a re-run reported `7 cell(s) already complete, 1 partial` and
  re-ran that cell in full (8 trials, not the 3 missing ones).

## 5. Flags

`--live` (the only way to spend money), `--dry-run` (explicit no-op; already the
default), `--estimate`, `--design`, `--models`, `--stimuli` (staged running; resume
covers the rest), `--workers`, `--no-resume`, `--min-valid-frac`, `--single-actor-gate`,
`--print-all-prompts`, and `--dry-n` — a dry-run-only even cap on per-cell n for fast
smoke tests, **refused with `--live`**, which always runs the frozen allocation.

## 6. Cost estimate assumptions (`--estimate`)

- **Claude Opus 5: $5.00 / $25.00 per MTok** — model id `claude-opus-5`, verified against
  the `claude-api` skill on 2026-08-22, not recalled.
- **GPT-5.5: NOT VERIFIED.** OpenAI exposes no pricing endpoint; Study 1's README made the
  same disclosure. The estimator uses parity with Opus 5 purely so a number prints and
  labels the row `[UNVERIFIED PRICE]`. **Confirm the OpenAI rate before `--live`.**
- 1,100 input tokens/call (Study 1 measured 1,084 for a Stage C betting call), 300–500
  output tokens, ×1.05 retry allowance. Zero network calls; `count_tokens` is not called.
- At the frozen allocation: 2,976 planned trials → 3,124 estimated calls, **$40.61–$56.23**
  total (1,562 calls and $20.31–$28.12 per actor).

## 7. Safety rails

- `--dry-run` is the default; `--live` is the only way to spend money, and passing both is
  refused.
- A missing or edited design table, a crossed-up partner label, an odd or duplicated cell,
  a missing confirmation file, an unreadable confirmation format, an unrecognised verdict,
  a cell with no confirmed advantage, `--single-actor-gate` without `--models`, and
  `--dry-n` with `--live` each abort with a message rather than a guess.
