# Prospective procedural replication across model generations — GPT-5.4 / Claude Opus 4.8

**FROZEN PRE-RUN SPEC.** Frozen 2026-08-14, before any Stage A/B/C call.

**Status: pre-flight COMPLETE (6 paid calls). Main run NOT started — awaiting approval.**

This is **not** an exact replication. Pair identities are re-derived from the older
models' own Stage A behaviour, so throughout it is called a *prospective procedural
replication across model generations* (equivalently, a *policy-relative replication
using the same A→B→C pipeline*). The phrase "exact replication" is not used.

**Scientific target.** Does the same A→B→C procedure recover policy-specific strategic
selectivity in an earlier model generation, even if the particular coordination
conventions have changed?

---

## 1. Design (approved 2026-08-14)

| | |
|---|---|
| Primary | Full A→B→C pipeline re-run on GPT-5.4 and Claude Opus 4.8 |
| Stage A | **Fresh**. The Aug-7 battery is *not* used as ground truth (§4) |
| Pairs | **Re-derived** from the older models' own Stage A. The five 5.5/Opus-5 pairs are **not** frozen in |
| Held constant | Prompts, trial counts, split procedure, Stage B baselines, Stage C payoff grid, primary analysis |
| Secondary | Cross-version transport analysis on the original pairs (§6), reported separately |

---

## 2. Models and settings — RESOLVED AND CONFIRMED BY PRE-FLIGHT

Pre-flight run 2026-08-14, 6 paid calls, `code/preflight_5_4_4_8.py`,
raw results in `replication_5_4_4_8/preflight/preflight_results.json`. **6 of 6 passed.**

| model | requested | **returned** | stage A | stage B | stage C |
|---|---|---|---|---|---|
| GPT | `gpt-5.4` | `gpt-5.4-2026-03-05` | ok | ok | ok |
| Claude | `claude-opus-4-8` | `claude-opus-4-8` | ok | ok | ok |

The OpenAI alias resolves to the pinned build `gpt-5.4-2026-03-05` — the same build
recorded in the Aug-7 battery. All six probes parsed cleanly and none truncated.

**Settings — exactly the Aug-7 Opus-4.8 / GPT-5.4 settings**, recovered from
`step1c_output/targeted_confirmation_calls.csv` and
`calibration_output/calibration_auditor_calls_20260807_183700.csv`, not reconstructed:

```json
gpt-5.4          {"model":"gpt-5.4","reasoning":{"effort":"low","summary":"auto"},
                  "temperature":null,"max_output_tokens":null,"seed":null}

claude-opus-4-8  {"model":"claude-opus-4-8","max_tokens":2000,
                  "thinking":{"type":"adaptive","display":"summarized"},
                  "output_config":{"effort":"low"},"temperature":null,"seed":null}
```

`output_config={"effort":"low"}` — the flagged risk — **is accepted on Opus 4.8.**
Confirmed twice over: 1,020 successful Aug-7 calls used it, and the pre-flight
re-confirmed it live.

**`max_tokens` = 2000, not the Aug-12 value of 4000.** This restores the exact Aug-7
setting. It is a truncation cap, not an estimand, and the pre-flight shows ample
headroom — observed output was 41 / 28 / 60 tokens against the 2000 cap on the Stage A,
B and C prompts respectively, the last being the longest prompt in the series. No probe
returned `stop_reason = "max_tokens"`.

---

## 3. Held constant from the original run

- **Prompts.** Stage A uses `BASE` verbatim; `psc_common` asserts prompt hash `3003ae1b`
  at import and refuses to run otherwise. Stage B auditor / salience and Stage C
  `betting_prompt(safe)` — including the *partner always plays* clause — byte-identical.
- **Stimuli.** Same 15-image battery, same identity coding, verified by
  `build_manifest()` against the confirmed run; fails loudly on any disagreement.
- **Design.** AB/BA counterbalancing. Stage A n=60 per model × stimulus. Stage B n=30
  per cell per arm. Stage C n=30 per model × stimulus × payoff over {3, 5, 7, 9}.
- **Estimators.** Unbiased dyadic match `Σ n_k(n_k−1) / [N(N−1)]`; form consistency with
  the position-fallback diagnostic; the 0.80 clean-rule bar.
- **Split.** `assign_halves()` unchanged — deterministic select/holdout halving.
- **Effort.** `low` on both sides, matching the whole Step 1/1c/2 series.

Changed of necessity: model IDs, `DISPLAY` names, output directory. `psc_common` gains
env-var overrides (`PSC_GPT_ID`, `PSC_CLAUDE_ID`, `PSC_EXP_DIR`) defaulting to current
values, so the original code path is bit-identical when unset.

---

## 4. Stage A ground truth — fresh, per approval

The Aug-7 battery is **not** used as primary ground truth. It contributed to stimulus
discovery and selection, so reusing it would weaken the independence of the replication
and partially undo the winner's-curse protection that sample splitting exists to provide.
Aug-7 data is used **descriptively only**, as historical comparison.

---

## 5. FROZEN PAIR-SELECTION RULE

Frozen before any Stage A call. Fully deterministic: given Stage A+B outputs it returns
one pair set with no further judgement. Implemented in
`code/select_pairs_replication.py`; manual approval may only **reject** (§5.5).

Thresholds are anchored to values realised by the original nine candidates, so the rule
would have admitted the original design — they are not tuned to this generation's data,
which does not yet exist.

### 5.1 Eligibility gates (ALL must hold)

| # | gate | threshold | rationale |
|---|---|---|---|
| E1 | select-half true self-match gap | `d_true_select ≥ 0.25` | original minimum was 0.287 |
| E2 | held-out sign agreement | `holdout_sign_agrees == True` | **required**; all 9 originals passed |
| E3 | held-out true self-match gap | `d_true_holdout ≥ 0.20` | original minimum was 0.405 |
| E4 | held-out generic-salience gap | `\|d_salience_holdout\| ≤ 0.10` | original max was 0.083 |
| E5 | held-out auditor-prediction gap | `\|d_auditor_holdout\| ≤ 0.10` | original max was 0.089 |
| E6 | select-half public z-gaps | `\|z_salience\| ≤ 0.85` **and** `\|z_auditor\| ≤ 0.85` | original maximum was 0.82 — see correction below |
| E7 | data sufficiency | ≥ 25 valid trials per member per half | guards degenerate splits |
| E8 | diagnostics defined | `pair_diagnostic` not undefined/NaN | no silent NaN propagation |

**E6 correction, 2026-08-14, made before any Stage A result was inspected.** E6 was
first written at 0.35 (`SMALL_PUBLIC_Z`, the constant behind the descriptive
`pair_diagnostic` label). Replaying the frozen rule against the original
`matched_pairs.csv` showed 0.35 rejects **3 of the 5 pairs the original study actually
approved** (auditor z up to 0.82), leaving only 3 eligible — it would have run a
*stricter* design than the one being replicated, contradicting "as close as possible to
the original". E6 is now anchored the way E1–E5 are: to the maximum realised by the
original approved set. Verified: **5 of 5 original approved pairs pass at 0.85**, and
the rule selects 5 pairs, 4 of them the original approved ones. The substantive
public-matching constraint remains E4/E5, which cap the *holdout* gaps at 0.10 in
probability units.

Both members must belong to the **same focal model**. Direction is fixed by the
select half: HIGH is the member with the larger select-half self-match. The holdout
never redefines direction — it only validates it (E2/E3).

### 5.2 Ranking (select half only)

`matching_score_public = z_true_select − |z_salience_select| − |z_auditor_select|`,
descending. Already implemented as `score_pub`. The holdout is a **gate, never a
ranking input** — otherwise the split's protection is spent.

### 5.3 Selection

1. Greedy descending within each model.
2. **Stimulus reuse:** a stimulus may appear **at most once per model**. Reuse *across*
   models is allowed (as in the original, where `s_convexity` and `d_dens_extreme`
   served both).
3. **Allocation:** target 3 GPT + 2 Claude = 5, matching the original. If a model yields
   fewer eligible pairs, backfill from the other model up to 5 total.
4. **Contrast representation:** if ≥1 eligible pair is a *both-form-rule* contrast (both
   members `form_consistency ≥ 0.80`), the highest-ranked such pair is force-included for
   that model, displacing that model's lowest-ranked selected pair. Capped at **one
   forced inclusion per model**, so representation cannot dominate the set. If no such
   pair is eligible, this is recorded as "no both-form contrast available" — not worked
   around.

### 5.4 Tie-breaking (deterministic, in order)

(a) larger `d_true_holdout` → (b) smaller `|d_salience_holdout|` →
(c) smaller `|d_auditor_holdout|` → (d) alphabetical `pair_id`.

### 5.5 Manual approval

May **reject** a scientifically pathological pair (e.g. a degenerate stimulus, an
identity-coding anomaly). May **not** add, reorder, or re-rank. Every rejection is
recorded with a written reason in `rejected_pairs.csv`. Approval happens **before any
Stage C call exists** — pairs are never chosen or revised by inspecting Stage C.

### 5.6 If fewer than 5 pairs qualify

| eligible | action |
|---|---|
| ≥ 5 | proceed as specified |
| 3–4 | **proceed** with those pairs; Stage C shrinks to n=30 × 2 × 4 × k calls; reduced power reported prominently |
| < 3 | **STOP.** Do not run Stage C. Report that the older generation does not support the design |
| 0 for one model | run the single-model replication and flag it explicitly |

---

## 6. Primary vs secondary — kept separate

**PRIMARY (confirmatory).** Re-derived pairs only. Does each model attempt more on its
own higher-reliability stimuli?

**SECONDARY (cross-version transport, descriptive).** The original five 5.5/Opus-5 pairs
under 5.4/4.8: do the old pair gaps persist, collapse, or reverse; do the older models'
strategic preferences follow the old labels or their own current policy? Runs only if
approved as Option C (+1,200 calls); **never pooled into the primary claim**, and
reported in a separate section with its own table.

---

## 7. PRIMARY REPLICATION STATISTIC — pre-specified

Replication success is **not** "4/5 pair p-values < .05". Single aggregate statistic:

> **δ̂ = the coefficient on `is_high` in the joint payoff-response model**
> `logit P(attempt) = α_model + β_model · safe_payoff + δ · is_high`
> fitted by IRLS over all Stage C trials from all approved pairs pooled, with a
> **cluster bootstrap resampling whole stimuli** (5,000 draws) for the 95% CI.

**Replication is declared if δ̂ > 0 and its 95% cluster-bootstrap CI excludes 0.**

Accompanying confirmatory test, same permutation logic as the original: statistic =
mean over approved pairs of `(p_attempt_high − p_attempt_low)`, permuting the
high/low label **within (pair × payoff) strata**, one-sided (H₁: δ > 0), on **raw
counts** — never rounded rates (the bug caught and fixed on 2026-08-12).

*One deliberate deviation, flagged for approval:* permutations raised **2,000 → 20,000**.
The count is a resolution parameter, not an estimand; at 2,000 the smallest reportable
p is ~0.0005 and three of the original pairs sat exactly on that floor. Say the word and
it stays at 2,000.

**Reported descriptively alongside (never as the success criterion):** sign of the
effect in each pair; number of pairs with a positive high−low contrast; payoff
monotonicity across SAFE ∈ {3,5,7,9}; held-out survival of Stage A gaps; held-out
salience and auditor differences.

**Interpretive test (§8 of the approval).** If the older models show *different*
high/low stimuli, those gaps survive held-out validation, salience/auditor stay matched,
and Stage C selectivity follows the older model's **own** reliability map — the writeup
will emphasise that the behavioural effect tracks the current policy rather than fixed
stimulus properties. This is a pre-registered interpretation, not a post-hoc reading.

---

## 8. Stopping and failure conditions

| condition | action |
|---|---|
| Pre-flight setting rejected | STOP. Report raw provider error. No substitution | ✅ passed |
| `model_id_returned` ≠ requested | STOP mid-stage |
| Parse-failure rate > 2% in any stage | STOP and report |
| Any Stage A cell < 55 valid trials after retries | STOP and report |
| < 3 eligible pairs | STOP before Stage C (§5.6) |
| Write attempted outside `replication_5_4_4_8/` | assert-fail |
| Stage B salience/auditor arm fails entirely | STOP — E4/E5 become unevaluable |

---

## 9. Call budget

| stage | arithmetic | calls |
|---|---|---|
| A ground truth | 15 × 2 × 60 | 1,800 |
| B auditor | 15 × 2 × 30 | 900 |
| B salience | 15 × 2 × 30 | 900 |
| C betting | 5 pairs × 2 × 4 payoffs × 30 | 1,200 |
| **TOTAL (primary)** | | **4,800** |
| pre-flight (already spent) | | 6 |
| optional Option-C transport run | | +1,200 |

Retries historically add ~0.1% (1 extra call in 4,800). Wall clock ≈ **66 min** at 8
workers, from the Aug-12 timings.

**Cost is not verified.** Neither prior run logged token usage and I have no confirmed
`gpt-5.4` price. Pre-flight Claude usage was ~925–1,127 input / 28–60 output tokens per
call; at that scale 4,800 calls is order tens of dollars, not hundreds — an estimate,
not a quote. The replication runners will log `usage` so the real figure is recorded.

---

## 10. Archive layout

Everything under `replication_5_4_4_8/`. **No file in the original 5.5/Opus-5 project is
written to or overwritten.**

```
replication_5_4_4_8/
  REPLICATION_5.4_4.8_SPEC.md      frozen copy of this spec (hash recorded)
  preflight/preflight_results.json  resolved IDs + settings + raw probe results  [done]
  data/                             raw Stage A / B / C outputs (csv + jsonl)
  splits/                           select / holdout assignment per cell
  pairs/candidate_pairs.csv         every candidate with all gate values
  pairs/rejected_pairs.csv          rejected candidates + written reason
  pairs/approved_pairs.csv          final approved set
  analysis/primary/                 δ̂, CI, permutation test, descriptives
  analysis/transport/               cross-version secondary (if Option C approved)
  run_logs/
```

---

## 11. Deviations from the original, in full

1. Model IDs and display names — the point of the exercise.
2. Pair identities re-derived (approved; §1). Hence "procedural replication", not "exact".
3. `max_tokens` 4000 → **2000**, restoring the exact Aug-7 setting (§2).
4. Permutations 2,000 → 20,000, flagged for approval (§7).
5. Output directory (§10).

Nothing else changes.

---

## 12. FROZEN SECONDARY ANALYSES (added 2026-08-14, BEFORE Stage C launched)

These are pre-specified. None may replace the primary statistic in §7.

### 12.A Leave-one-pair-out robustness
Recompute the **pooled** high-vs-low Stage C effect five times, omitting one selected
pair each time. Report direction and magnitude of δ̂ per fold. This is a **sensitivity
analysis, not five hypothesis tests** — no per-fold p-values are interpreted as tests.

### 12.B `proto`-excluded sensitivity
Repeat the pooled effect after excluding Pair 1 (`gpt: proto > s_arrow`). Labelled a
**pre-specified sensitivity analysis motivated by `proto` being the shared-easy
ceiling-control stimulus.** It does not replace the primary analysis. Pre-launch check
confirmed `proto` was genuinely eligible under the frozen rule (no exclusion clause in
the spec, no category filter in the selector, present in 28/210 original candidates, and
`gpt__proto__vs__d_texture` passes the frozen gates on the original data), so Pair 1 is
retained in the primary.

### 12.C Cross-generation transport analysis — FULLY SEPARATE
Compares the original 5.5/Opus-5 reliability map with the fresh 5.4/4.8 map. Reports:
per-stimulus and per-pair gap changes; sign reversals; overlap in selected pairs;
rank correlation of stimulus-level self-match; form-rule/fallback status changes.

**Constraints.** It must not redefine HIGH/LOW for the primary. It must not be pooled
into the replication claim. **Zero selected-pair overlap is DESCRIPTIVE, not a formal
test of version instability** — the statistical evidence for instability comes from the
measured Stage A cross-version changes and sign reversals, not from set overlap.

---

## 13. INTERPRETATION TO PRESERVE

The replication target is **not** "the same visual pairs reproduce." It is: *the same
prospective A→B→C procedure recovers strategic selectivity relative to the current
model's own policy.*

If Stage C is positive, the strongest supportable claim is:

> Across model generations, the particular coordination conventions changed, but
> strategic behaviour continued to track the conventions implemented by the model's own
> current policy.

---

## 14. SELECTOR BUG RECORD (both fixed BEFORE Stage C; neither changed any threshold)

Two **implementation** defects prevented the already-frozen rule from executing. Neither
altered a threshold, a gate, a ranking function, or any scientific criterion.

| # | defect | effect | fix |
|---|---|---|---|
| 1 | `delta_true_select` is derived by `analyze_stage_ab`, not stored as a column | E1 read `nan` for **all 210** candidates → 0 eligible, which would have masqueraded as a genuine "STOP, design unsupported" result | derive it in the loader as `true_self_match_high_select − true_self_match_low_select` |
| 2 | console print used obsolete column names (`d_true_select` etc.) | `KeyError` after selection had already succeeded; cosmetic, no effect on selection | use the `delta_*` names |

A third, earlier defect was caught during pre-run validation: the selector initially read
`stage_c_candidates.csv`, a 17-column view carrying no `z_*`, which silently NaN'd E6.
Fixed to read the full `matched_pairs.csv`. Also caught pre-run: E6 was mis-anchored at
0.35 and is now 0.85 (§5.1 correction).

Frozen script: `code/select_pairs_replication.py`, sha256 recorded in
`replication_5_4_4_8/selector_sha256.txt`.

---

## 15. PAIR-SPECIFIC PROVENANCE NOTES

- **Pair 1 (`gpt: proto > s_arrow`)** — conceptually unusual: HIGH is the shared-easy
  ceiling-control stimulus. Verified pre-run eligible under the frozen rule and retained;
  the frozen exclusion sensitivity (§12.B) covers it.
- **Pair 4 (`gpt: s_contrast > b_spiral_cw`)** — a **both-form-rule** contrast
  (form consistency 1.00 / 1.00). Especially informative: a positive effect here cannot
  be reduced to detecting position fallback, since neither member is a fallback stimulus.
- **Claude both-form representation** — no eligible Claude both-form-rule pair existed
  under the frozen rule. Documented as a limitation; selection was **not** altered to
  manufacture one.
