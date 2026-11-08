# RESUME — how to finish Stage 1 after a restart

Everything below is safe to run more than once. The runners are resume-safe on
`(array_id/item_id, checkpoint, trial)` and flush every row to disk as it is collected, so a
kill, a sleep or a crash loses nothing and never double-charges. Rows that failed in flight are
**not** marked done and are retried automatically.

---

## 1. Finish the visual frame collection

```
cd ~/Desktop/Coordination/Self_Coordination/study_policy_convergence_20260909
nohup python3 -u runners/run_visual.py --set frame --workers 30 --cap CAP >> runs/visual_frame/frame.log 2>&1 &
```

**Set `CAP` to the hard-ceiling remainder, not the original figure.** The budget guard counts from
zero on each invocation, so it needs what is left, not what was planned. To compute it:

```
python3 - <<'PY'
import csv
t=sum(float(r['measured_cost_usd'] or 0) for r in csv.DictReader(open('RUN_LEDGER.csv')))
import glob
for f in glob.glob('runs/visual_frame/visual_frame_*.csv'):
    t+=sum(float(r['cost_usd'] or 0) for r in csv.DictReader(open(f,newline='')) if r['transport_ok']=='1')
print('spent total $%.2f | remaining to $150 hard: $%.2f'%(t,150-t))
PY
```

Watch it with `tail -f runs/visual_frame/frame.log`. It prints every 200 calls.

**Expect a handful of `tx_fail` rows** if the machine slept mid-run: sleeping drops the in-flight
connections and the backoff gives up after five tries. Those are retried by the resume above. They
are not a collection fault and must not be read as one.

## 2. Build the analysis view and run the pipeline

```
python3 runners/to_pipeline.py --set frame
python3 analysis/run_stage1.py --sources analysis_input/sources_frame.json --out analysis/out/stage1_frame
```

`analysis_input/` is a regenerable view; the raw CSVs under `runs/` are the record. Read
`analysis/out/stage1_frame/SUMMARY.md` and `integrity.json` first — the integrity gates are the
thing to check before any number is quoted.

## 3. Report the two declared strata (D-027) — do not collapse them into one

- **Stratum L**, both models at effective support >= 1.5 under OFF: carries the primary
  determinism-adjusted statistic with the `identifiable` flag.
- **Stratum F**, the full unscreened 41 arrays: carries **prevalence of collapse**, modal agreement
  and the shared-convention result.

Stratum L is conditioned on a **generator property** through within-model marginals only — never on
a between-model relationship. That is weaker than the conditioning that disqualified `FROZEN_22`,
but it is not absent, and it is disclosed on every Stratum L result.

---

## State at the last checkpoint before the restart

| | |
|---|---|
| Gate 1 availability probe | complete, 17 calls, $0.09 |
| Code pilot gate | **complete**, 5,184 calls, $18.96 — code arm closed (D-025) |
| Liveness preflight | **complete**, 1,152 calls, $8.73 |
| Visual frame | **in progress**, ~7,200 of 17,712 calls, ~$45.80 |
| Spend | ~$73.6 of $150 hard |
| Integrity so far | 1 parse failure in ~13,500 calls; **zero** checkpoint mismatches; **zero** thinking blocks returned |

Reports to read for context, in order: `GATE1_REPORT.md`, `GATE2_PILOT_AND_PREFLIGHT.md`,
`DECISION_LOG.md` (D-001..D-030), `MASTER_DESIGN.md` (§4.1 request surface, §4.2 ladder asymmetry,
threats 1–16).

## What must NOT happen next

Stage 1 stops at policy similarity and policy convergence. Do not begin partner prediction, identity
framing, payoff calibration, green assignment, stag-hunt strategic trials, or non-strategic Worker
trials.
