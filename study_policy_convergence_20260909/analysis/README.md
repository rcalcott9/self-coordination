# analysis/ — T5 (analysis-engineer), Stage 1

Owner: T5. Everything here is a proposal for lead review; nothing outside this directory
was created or modified. **No component makes API calls.**

| file | what it is |
|---|---|
| `ANALYSIS_SPEC.md` | the specification: every metric and analysis with exact formulas, plus the determinism/similarity separation argument |
| `synthetic_validation.md` | the ground-truth validation — four known cases and what the statistics returned |
| `convergence_metrics.py` | estimators (pure functions, no I/O) |
| `run_stage1.py` | the pipeline: raw trials -> cells -> pairs -> convergence. `--selftest` asserts the properties the spec claims |
| `synthetic_validation.py` | the synthetic generator and the four ground-truth cases |
| `sources_worked_run.json` | source config for the worked run (existing frozen data, read-only) |
| `out/worked_run/` | worked-run outputs: `SUMMARY.md`, `integrity.json`, `cell_metrics.csv`, `pair_metrics.csv`, `convergence.json` |
| `out/synthetic_validation.json` / `.log` | raw validation output |

## Reproduce

```
python3 run_stage1.py --selftest                 # 7 assertions, exits non-zero on failure
python3 run_stage1.py                            # worked run on existing data (~10 s)
python3 synthetic_validation.py --reps 150 --boot-b 300 --null-reps 25 --null-b 300
```

Requires numpy only. All randomness is seeded (`20260909`).

## The one-paragraph version

Raw `cross_model_match` cannot be read as convergence: on synthetic data where mutual
similarity is *exactly constant* and only determinism rises, it climbs from 0.47 to 0.97
and 100% of simulated studies call it convergence. The analysis therefore (i) splits any
raw-match trend exactly into a determinism channel and an alignment channel via
`log M_AB = .5 log M_AA + .5 log M_BB + log cos_raw`, (ii) reports a tempering-invariant
determinism-adjusted similarity `das`, and (iii) tests its vintage slope against a
**determinism-matched null band** rather than against zero, because at n=48 a collapsed
cell carries no information about its own tail. Validated: correct verdict in all four
ground-truth cases, size 0.00 where the truth is "no change".

**Finding for Gate 1:** the existing 4-option visual battery is already too deterministic
for this question — median effective support 1.18, 52 of 122 cells at `modal_share >= 0.99`,
3 of 137 pairs above the reference threshold. The Stage 1 frame needs a liveness screen.
