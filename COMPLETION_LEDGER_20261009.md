# Self-coordination paper: completion ledger v3 (2026-10-10, updated 2026-10-13)

## Active summary update (2026-10-17 ≈20:40Z): PD three-condition pilot COMPLETED, fresh $20 cap
- **Authorisation, verbatim:** "okay run a small pilot based on that. budget = $20. im going to go away, so provide me with a plot of the three conditions by the time i get back" (user, via ChatGPT manager `pd-three-condition-pilot-20usd-01`).
- **Budget:** pilot cap $20, including tests, retries and failures. Cumulative Study 3 ceiling $71.31619 over a prior of $51.31619.
- **Scope:**
  - One-shot PD: CC 8/8, CD 0/10, DC 10/0, DD 3/3.
  - Neutral A/B labels, balanced 32/32 per cell.
  - GPT-5.5 and Opus 5 × {same model, different model, fixed response} × 64 draws = 384 calls.
- **Status: COMPLETED.**
  - **Collection:** 384/384 valid; 0 invalid, refusals, failures or retries.
  - **Spend:** pilot **$1.99287**; **cumulative Study 3 $53.30905**.
- **Finding** (exploratory):
  - **Opus cooperated 64/64 in every condition.** It is at ceiling, so no partner effect is detectable.
  - **GPT-5.5 cooperated 1/64, 0/64 and 6/64** (same, different, fixed). All 7 cooperations were under A = cooperate.
  - Opus gives evidential/correlated-choice reasons, even for the sealed prerecorded response. 24/64 of its different-model reasons misread the game as a Stag Hunt (B = cooperate mapping only).
  - **Opus is exploited in every cross-model dyad:** 0 points vs GPT's 10.
  - Superrationality is not uniquely identified; social preferences, textbook-PD recognition and framing remain alternatives.
- **Evidence:** `study3_pd_three_condition_20261017/results/run/analysis/{REPORT.md, cells.csv, summary.json, fig_pd_three_conditions.png/.pdf}`; frozen `design/FROZEN.json` 86eaeb52…, `jobs.jsonl` 8916615f….
- **Next:** user + ChatGPT review; no further experiments.
- **Reporting corrections to Pilot 3 (PASS = 5), manager-verified; raw results unchanged:**
  1. The matching gains were not entirely from F01: GPT COPY F27 realized matching also rose, from .090909 to .227273.
  2. Diffuse items were mostly PASS, not literally all PASS: one GPT F05 COPY evaluation draw played.

## Active summary update (2026-10-16 ≈17:41Z): PASS = 5 pilot (Pilot 3) AUTHORISED, fresh $20 cap
- **Authorisation, verbatim:** "okay now run pilot if ready" (user, via ChatGPT manager `study3a-pass5-adapted-pilot-execution-20usd-01`).
- **Context, as recorded by the manager:** the user's go-ahead came after the manager explicitly requested a fresh $20 Pilot-3 cap, and the manager accepted it as approval of that allocation. Earlier, the user approved the adaptation itself: "great. run the adapted pilot".
- **Budget:** Pilot-3 cap $20, including tests, retries and failures; cumulative Study 3 ceiling $60.60191 over a prior of $40.60191. No transfer of unused earlier allowances.
- **Scope:** the prepared PASS = 5 candidate, exactly as prepared. 576 calls; no sample or science changes.
- **Status: COMPLETED 2026-10-16 17:52Z.**
  - **Collection:** 576/576 valid; 0 invalid, refusals or failures.
  - **Spend:** pilot $10.7143 of the $20 cap; **cumulative Study 3 $51.3162** of the $60.60191 ceiling.
  - **Finding** (PASS 5 vs PASS 7, exploratory):
    - **10-point match rose in every cell:** GPT copy .31 (.23), GPT vs Opus .25 (.19), Opus copy .25 (.17), Opus vs GPT .25 (.19).
    - The gain came entirely from F01, which moved to PLAY 1.00 and match 1.00 in all cells. F27 is still mostly PASS for Opus, and GPT over-plays it against Opus (regret .333). Diffuse items are all PASS.
    - **Regret:** GPT copy .020, GPT vs Opus .083, Opus 0, 0.
    - Joint shortfall is not comparable across incentives.
    - BR-consistency .99–1.00. EV arithmetic: GPT 1.000; Opus .944–.979 at ≤ 0.01.
    - This is an incentive effect on participation where a shared rule already exists; not privileged knowledge.
  - **Evidence:** `results/run/responses.jsonl`; `results/run/analysis/{REPORT.md, per_item.csv, aggregate.csv, fig_pass5_outcomes.png/.pdf, analyze_used.py}`.
  - **Next:** user + ChatGPT review; no further experiments.
- (Run log, previously "RUNNING" since 2026-10-16 ≈17:43Z.) `study3a_pass5_PROPOSED_20261016/`.
  - Frozen: FROZEN.json sha256 df263507…, jobs.jsonl bc41207f…; prompts b5346bb0 / c12a5ed6. Jobs verified identical to the PASS = 7 pilot apart from the prompt hash.
  - Prices re-verified. Dry run and mock ok.
  - Format check: 8/8 ok, $0.150. Live status in review_loop/pass5_execution_status.json.

## Active summary update (2026-10-16 ≈16:50Z): PASS = 5 adapted pilot PREPARED, BLOCKED on budget
- **Adaptation authorised, verbatim:** "great. run the adapted pilot" (user, via ChatGPT manager `study3a-pass5-adapted-pilot-prep-01`). This approves the incentive change only; no spend is authorised.
- **Prepared offline** (`study3a_pass5_PROPOSED_20261016/`, CANDIDATE, not frozen; $0):
  - PASS 7 → 5 and threshold .70 → .50 by 6 asserted substitutions (prompts b5346bb0 / c12a5ed6);
  - the same 576 jobs;
  - scoring with configurable PASS, joint shortfall and matching (8/8 checks);
  - analysis and figure on mock data;
  - a runner that refuses live dispatch.
- **Blocking:** expected $10.83 (95% $10.76–10.91) exceeds the $9.17 pilot-cap remainder and the $9.40 headroom under $50. It needs an allocation of ≥ ≈ $11.50 and a cumulative ceiling of ≥ ≈ $52.10.
- **Correction:** the PASS = 7 pilot's EV arithmetic is .986 at ≤ 0.01, not "perfect" (note appended to its REPORT).

## Active summary update (2026-10-16 ≈15:45Z): reciprocal-confidence pilot AUTHORISED, pilot cap $20
- **Authorisation, verbatim** (user, relayed by the ChatGPT manager, message `study3a-reciprocal-confidence-pilot-20usd-01`; spec `review_loop/reciprocal_confidence_pilot_APPROVED.json`): "yes and new cap for this experiment: $20".
- **Budget:** $20 is **for this experiment**, in addition to the completed baseline. It includes format checks, retries and failed calls. The cumulative Study 3 ceiling is $50; prior spend recomputed from raw logs is $29.76738.
- **Scope:** a symmetric two-step reciprocal-confidence appendix given truthfully to both players. Items F01_oddone_m0, F27_linecount_m1, F05_orient_m5, F12_mirror_m3 × {GPT-5.5, Opus 5} × {COPY, DIFFERENT}. 24 policy + 12 eval draws per cell; 576 calls. No other arms; all items retained.
- The baseline is used only as an exploratory comparison.
- **Status: COMPLETED 2026-10-16 15:59Z.**
  - **Collection:** 576/576 returned; 574 valid; 2 invalid (Opus F01 DIFFERENT, "PASS with an object", not resampled); 0 refusals, failures or retries.
  - **Spend:** pilot $10.8345 of the $20 cap; **cumulative Study 3 $40.6019** of the $50 ceiling.
  - **Finding** (4 items, exploratory; appendix vs matched baseline):
    - **regret:** GPT copy .045 (.165); GPT vs Opus .009 (.133); Opus copy .011 (.034); Opus vs GPT .036 (.055);
    - **realized 10-point match fell in every cell:** GPT copy .23 (.54), GPT vs Opus .19 (.31), Opus copy .17 (.29), Opus vs GPT .19 (.31). PLAY rates were .21–.31.
    - The appendix made both models more conservative and EV-consistent (BR-consistency ≈ 1.00), but it reduced high-payoff coordination; e.g. F27, where GPT went from 24/24 PLAY to 19/24 PASS.
    - Forecasts underpredict PASS and are projective (own ≈ partner).
    - Inconclusive-to-negative for superrational coordination; no own-policy-knowledge claim.
  - **Evidence:** `results/run/responses.jsonl` (54f60ed1…); `results/run/analysis/{REPORT.md, per_item.csv, aggregate.csv, realized_vs_baseline.csv, fig_reciprocal_regret.png/.pdf, analyze_used.py}`.
  - **Next:** user + ChatGPT review. No further collection; the frozen pilot is complete.
- (Run log, previously "RUNNING" since 2026-10-16 ≈15:49Z.) `study3a_reciprocal_confidence_20261016/`.
  - Frozen: FROZEN.json sha256 936dd19b…, jobs.jsonl e4a66b67…; prompts COPY b308cb54, DIFFERENT 5b087c1d.
  - Offline checks: parser 8/8; dry run; mock 576 records with 0 mapping errors; pilot-cap stop test held at a $1 test cap; analysis and figure on mock data.
  - Format check: 8/8 ok, $0.154. Projected ≈ $11.1. Live status in review_loop/reciprocal_confidence_status.json.

## Active summary update (2026-10-16): Study 3A BASELINE authorised, $30 cumulative cap
- **Authorisation, verbatim** (user, relayed by the ChatGPT manager in message `study3a-baseline-execution-30usd-01`):
  - "no we first want to test baseline performance on the stag hunt with the relevant stimuli (test in stag hunt to avoid the thing we found previously that weak policies in study 1 are strong here)"
  - "yes. this is good. run exactly this experiment. i want a resulting plot that shows regret for each model, relative to an optimal (low regret) benchmark"
  - "your budget is $30"
- **Cap:** $30 is read conservatively as the **total cumulative Study 3 cap**, replacing $20. Prior spend was recomputed from raw logs at $4.75248, leaving $25.2475.
- **Scope:** 19 retained items × focal {GPT-5.5, Claude Opus 5} × {COPY = same-model partner, DIFFERENT = the actual other model}. 24 independent policy + 12 evaluation draws per cell, archived baseline prompts, no intervention.
- **Settings:** GPT `max_output_tokens` 4000; Opus `max_tokens` 4000. Token-limit reservation before every dispatch.
- **Prices verified at launch, 2026-10-16:** GPT-5.5 $5/$30; Opus 5 $5/$25 per MTok.
- **Superseded, never executed:** the policy-knowledge preparation (`study3a_policy_knowledge_PROPOSED_20261016`). The $20 cap is no longer current.
- **Status: COMPLETED 2026-10-16 04:03Z.**
  - **Collection:** 2,592/2,592 new calls valid (0 invalid, refusals, failures or retries) plus 144 reused. The budget rule stopped the concurrency-6 run at 2,551; the remaining 41 frozen jobs were resumed at concurrency 1 under the same rule.
  - **Spend:** run $25.0149; **cumulative Study 3 $29.7674 of the $30 cap**.
  - **Finding** (mean normalized regret, equal item weights, 19/19 items):
    - GPT COPY .123 [.099, .156]; GPT vs Opus .201 [.174, .232];
    - Opus COPY .042 [.027, .063]; Opus vs GPT .032 [.021, .053].
    - Opus plays near a best response, mostly by passing (PASS ≈ .78). GPT over-participates: against a passing Opus, and on its own diffuse items.
    - No evidence about own-policy knowledge use (baseline only).
  - **Evidence:** `results/run/responses.jsonl` (sha256 3b62c800…); `results/run/analysis/{REPORT.md, per_item.csv, aggregate.csv, fig_baseline_regret.png/.pdf, analyze_used.py}`.
  - **Next:** user + ChatGPT review. Remaining headroom is $0.23; no further collection is possible without a new cap.
- (Run log, previously "RUNNING" since 2026-10-16 ≈03:29Z.) `study3a_baseline_20261016/`.
  - Frozen: FROZEN.json sha256 206095b9…, jobs.jsonl c46bd5d8… (2,592 new jobs), reuse.jsonl b8df0d62… (144 Oct-15 Opus DIFFERENT draws on the 4 pilot items, exact match, roles kept).
  - Offline checks passed: dry run; mock with mapping 0 errors and no duplicates; cap stop-rule test held under a test cap; analysis and figure on mock data.
  - Format check: 8/8 ok, $0.081.
  - Expected ≈ $22.17 new; live status in review_loop/baseline_execution_status.json.

## Active summary update (2026-10-15)
- **Running:** nothing. **Spent 2026-10-15:** $3.4225 (Study 3A feasibility pilot, 384 calls; see B). Cumulative Study 3 exploratory spend $4.7525 (cap $20).
- **Completed (local):** GREEN 5-/7-point reconciliation (D1–D8 still open); [exploratory] joint Opus GLMM; Study 3A comparator verification and item inventory (see B). Details in A ("Most consequential unsupported claim") and B.
- **Pending decisions:** D1–D8; whether to relabel Study 3A, since the poster shows the GREEN game; adding payoff/matching outcomes; 3A → 3C sequencing. None adopted. Collection is not authorised.

## Active summary (as of 2026-10-13 15:20 EDT)
- **Running:** nothing (process list checked). **Spent 2026-10-13:** $0; no research calls.
- **Completed 2026-10-13 (existing data):**
  - Study 2 freeze (figure + tables);
  - two new labelled sensitivities (Study 2 logit interaction; Study 3 benchmark bias);
  - methods/results draft: `paper_assembly_20261010/docs/METHODS_RESULTS_DRAFT.md`.
  - [exploratory] Study 1b projection diagnostic, all three datasets: `paper_assembly_20261010/code/study1_projection_diagnostic.py` → `tables/study1_projection_{items,summary}.csv`.
    - On divergent items, predictors' forecasts for the two targets differ by only 4–15% of the measured target difference (TVD .02–.10 vs .55–.69; exact p = .002 each).
    - Every forecast of the other model sits closer to the predictor's own choices (Brier gap +.22 to +.78, p ≤ .047).
    - Reproduces the existing low-reasoning values (.067/.048, .275/.264).
  - Study 1 figure package: `study1_figure_package_20261013/` (+ zip in `~/Downloads`); PNG/JSON regenerate byte-identical, PDF differs only in CreationDate.
- **Frozen, not started:** reasoning-on follow-up (recorded conditional $68 approval; see C).
- **Proposed, not authorised:** applied tasks T1/T2/T2-A (spec draft, ≈ $84, cap $118).
- **Next:** decide Opus's Study 1 wording (see "Most consequential unsupported claim" below), then write the discussion; approve or edit the applied-task spec.

- **Supersedes:** v2 (`COMPLETION_LEDGER_20261009_v2_SUPERSEDED.md`) and v1 (`…_v1_SUPERSEDED.md`). Corrections are listed at the end.
- **Provenance:** every row was checked against run files.
- **No calls launched.** No research process is running (process list checked 2026-10-10).

## A. Paper from existing data (Studies 1–3): ASSEMBLED

All zero-cost assembly tasks are done. Outputs are in `paper_assembly_20261010/`: README with captions, figures, tables, errata, `MANIFEST.sha256`.

### Study 1

| | provenance (exact) | status |
|---|---|---|
| **1a low** | `study1_frontier_min_20261007`, FROZEN `18853f3e`. Prompts CALIB `d40ea45d`, PLAYPASS `3b5fe054`, SELFPRED `433b4569` all state independent order. 2,680 calls, $23.60. | complete |
| **1b low** | `study1b_crossed_object_20261007`, FROZEN_SCREEN `4c411796`. 5,334 calls, $39.34. | complete |
| **1a + 1b high** | `study1_highreason_20261009`, FROZEN `933aa87d` + Amendment 1. 8,324 calls, $171.40. | complete |
| **Qwen observational** | `plunkett_qwen/results/study1_final_20261009` | complete |
| **Qwen continuation** | V1 `40e61320…/qcp_V1_step157`, V2 `88bcef52…/qcp_V2_step157`, ≈ $40.10 | complete |
| **Qwen crossed option-choice prediction** | `~/Desktop/Superrationality/Stag/qwen_crossed_prediction_20261009`.<br>- **Reconciled 2026-10-13.** The conflicting reports are a timeline:<br>&nbsp;&nbsp;- Authorised by the user at 2026-10-09 18:58:41 UTC ("Run only the proposed 20-item … crossed-prediction study, authorized under a $3 total cap"; session `861b9087`).<br>&nbsp;&nbsp;- Raw calls timestamped 19:03–19:04 UTC.<br>&nbsp;&nbsp;- v1's "DROP" was written at 19:01 UTC, before the run; v2's "proposed, not run" missed it.<br>&nbsp;&nbsp;- `~/Downloads/Qwen_Study1_final_20261009.md` ("no cross-model predictions exist") predates the run.<br>&nbsp;&nbsp;- The study **ran and is complete**; the v3 row stands.<br>- Re-verified 2026-10-13: FROZEN and all three code hashes match; 256 result lines = 256 jobs.<br>- +.575 (pooled) and +.594 (target step-316, plotted in Fig. 1f) are different frozen contrasts from one analysis, not a conflict.<br>- FROZEN `2da6c591` verified (sha256 matches `FROZEN.sha256`).<br>- Raw `results/{pilot,ref,pred}/calls.jsonl`: 16 + 80 + 160 = 256 calls, which equals the 256 frozen jobs.<br>- 1,920 scoring choices, 635/640 predictions, 0 failures.<br>- `analysis/results.json`; figure-ready tables already merged into `study1_figure_data_20261009` (`crossed_prediction_cells_all.csv`, `self_advantage_by_column.csv`).<br>- Cost $2.28 conservative ($0.51 if prefill is billed once), within a $3 cap. | **complete** |

**Results (frozen):**
- **Qwen crossed:** pooled self advantage on divergent items +.575 [.377, .761], exact p .004, 9/10.
- **Controls are not zero:** +.072 [.048, .100]. Step-316 predicts the base model poorly even on shared items. Self-projection is not excluded.

**Done (no calls):**
- **Figure 1 (2×3):** `paper_assembly_20261010/figures/fig_study1_2x3.{pdf,png}`. The Qwen bottom-right panel is now **filled with the crossed study**: target-specific +.594 divergent, −.029 control. The continuation result is plotted as its own series in panel c and is not used as choice self-advantage.
- **Audit flags:** all six are resolved in `docs/ERRATA_STUDY1_AUDIT_FLAGS.md`.
  - r = −.073;
  - Opus configurations separated;
  - the 20 uncoded traces are one failed coder batch (unique ids 2420–2439);
  - an amendment wording for the re-frozen prereg hashes;
  - lr 2.78e-5;
  - "scenario-level" AUC label.
  - Frozen files were not edited.
- **Repackage:** a provenance manifest covering the high-reasoning run, the Qwen crossed study and the figure export. The low package is unchanged.

### Study 2: FROZEN 2026-10-13

| | provenance | status |
|---|---|---|
| Frontier PLAY/PASS 2×2 | `study_playpass_gpt`, `Stag/opus_playpass` (adaptive 2×2 + `parallel_disabled_191726`) | complete |
| Qwen PLAY/PASS partner + logits | primary run B `plunkett_qwen/results/s2_20260912_181428`: the PI-approved symmetric wording (launch instruction 2026-09-12 22:13 UTC, session `b5db4a80`), partner +.155 [.103, .206]. Logits `logit_s2_20260913_185259` are post hoc and exploratory (requested 2026-09-13 after the results). Run A `qwen_study2_playpass/pp2x2_20260912_173541` is an earlier run with different partner wording (session `1e2df94d`), partner +.096 [.047, .146]. It is reported separately, never pooled, and is not a failed replication. | complete |
| Relational prediction | `study2_relational_prediction_20260912` | complete |

**SENSITIVITY checks done** (`code/study2_sensitivity.py`). Frozen contrasts are unchanged.
- **(a) Same-presentation agreement:**
  - GPT: LOW arm .43 → .63; 0 items relabelled; contrasts unchanged.
  - Opus: LOW arm .52 → .87; relabelling is undefined (18 ties at the boundary); ρ falls from .59–.78 to .46–.62.
  - Wording consequence: Opus HIGH/LOW separates perfect from high same-presentation agreement.
- **(b) Opus adaptive Stage A labels:** 0 of 30 items relabelled, so the contrasts are identical.

**Freeze done 2026-10-13** (`code/study2_freeze.py`, `figures/fig_study2`, `tables/study2_*`):
- Reproduces the frozen contrasts (asserted in the script).
- Partner shift: GPT +.140, Opus adaptive-low +.155, Qwen +.155.
- **Opus interaction (frozen, `REPORT_2x2.txt` Q2):** +.263 [.057, .463], unpaired item bootstrap. [sensitivity] The paired re-analysis gives [.147, .390]. HIGH is at ceiling (.967/.943). The 10-13 note that it was "never reported" was wrong.
- **[sensitivity] logit GLMM interaction** (`code/study2_logit_interaction.R`), not established in any model:
  - Opus +1.11, Wald [−0.44, 2.66];
  - GPT +0.19;
  - Qwen +0.18.
- **Wording:** "integration with own reliability not established", not "absent".

### Study 3

| | provenance | status |
|---|---|---|
| GPT-5.5 / Opus 5 | `two_model_staghunt_20260916`: $10.14 + $10.54 | complete |
| Fable 5.1 | `fable_staghunt_20261008`, $8.17 | complete |
| Qwen thinking off / on | `qwen_staghunt_pilot_20260916` $0.11; `qwen_staghunt_thinking_20261008` $7.70 | complete |

**Done:**
- Battery table: `tables/study3_battery_table.csv`.
- Figure 3: V̂ vs B.
- **SENSITIVITY, Qwen same-order B:**
  - thinking off: V̂ − B −1.78 → −1.85 [−2.27, −1.40], 10/10 items below B;
  - thinking on: −0.30 → −0.34 [−1.31, 0.65].
  - The conclusions are unchanged.
- **[sensitivity, 2026-10-13] Benchmark bias** (`code/study3_benchmark_bias.py`): B = max(7, 10ĉ) is biased upward by +0.02 to +0.15. Bias-corrected and cross-fitted B leave every frozen-primary conclusion unchanged.
  - Cross-fitted: Opus −1.05 [−2.13, −0.16], Fable −1.88, Qwen off −1.52.
  - GPT-low −0.08 [−0.88, 0.82]; it was never significant.

### Most consequential unsupported claim (2026-10-13)
- **The claim at risk:** "Opus 5's reliability judgements reflect knowledge of its *own* coordinability" (Fig. 1 is titled "own-coordinability knowledge").
- **Opus:** PLAY/PASS tracks its agreement, but not beyond the auditor's public prediction A, in either setting:
  - low: 3.81, Wald [−1.54, 9.15];
  - high: 3.29, Wald [−1.10, 7.68];
  - at high reasoning the auditor predicts Opus better than Opus does (P1 −.055, Holm .010).
- **GPT:** passes in both settings (3.73 [2.17, 5.48]; 2.49 [0.17, 4.91]).
- **Collinearity is not the obstacle:** r(y, A) is about .55–.59, with 22–25 of 41 arrays where |y − A| > .2. Opus's PLAY simply barely tracks the residual (r .12–.19).
- **Existing-data analysis that could resolve it** (none run):
  1. A joint Opus GLMM over both settings (82 array-settings, setting as a fixed effect, arrays as a random effect) for `play ~ y + A`. This is exploratory because it combines configurations.
  2. A pre-stated equivalence bound on the adjusted y slope, to turn "not established" into "absent".
- If (1) still includes 0, word Opus as "tracks publicly predictable agreement".
- **2026-10-15 (1) run: joint Opus GLMM (completed, [exploratory]; local, no calls, $0).** `paper_assembly_20261010/code/study1_opus_joint_glmm.R` (sha256 91c52c73…) → `tables/study1_opus_joint_glmm.{csv,txt}` (csv sha256 2957c6b2…).
  - Inputs (read-only): low `study1_frontier_min_20261007/analysis/audit/C_glm/trials.csv` (sha256 155e25e4…); high `study1_highreason_20261009/analysis/out_1a/glmm_trials.csv` (9eaae216…). 984 judgements = 41 arrays × 12 × 2 settings; same 41 arrays in both.
  - Specification, fixed before fitting: `play ~ y + A + effort + (1|array) + (1|array:effort)`, logit. y and A are setting-specific; effort is ±0.5; y and A are standardised on the pooled rows and reported on the original scale. Repeated items are handled by the array intercept (across settings) and the array × setting intercept (within the 12 judgements).
  - Reproduction: the per-setting fits give 3.807 / 3.291, matching the frozen values.
  - **Focal y slope 3.47.** Wald [0.28, 6.65], p .033; parametric bootstrap [0.18, 6.93] (1,000/1,000); array-cluster bootstrap [0.10, 7.82] (1,000/1,000), P(≤ 0) .020. A slope 21.8 [12.0, 31.5]. RE SD: array 1.84, cell 1.23.
  - **By effort:** y × effort +0.77, Wald [−4.37, 5.91], LRT p .77; implied slopes low 3.44, high 4.21. No evidence the association differs by effort; the test is weakly informative.
  - Sensitivity, array-only RE (ignores cell clustering, so anti-conservative): 3.58 [1.40, 5.77].
  - Not available: profile CIs (profiling found a deviance 0.0003 lower, a near-flat optimum) and the allFit optimizer check (call-evaluation error). Neither fix changes the model.
  - **No equivalence bound was chosen or tested.** Item (2) stays not run.
  - Frozen paper untouched. The proposed wording edit is in the 10-15 session reply; it is not applied to `METHODS_RESULTS_DRAFT.md`.

## B. Planned paper: NOT complete. Specifications now drafted

| planned component | status |
|---|---|
| Simultaneous Battle of the Sexes | **ABSENT** (no data). Specified as **T2-A abstract BoS** (points), item-matched to T2. |
| Executable applied task 1 | **ABSENT** (no data). Specified as **T1, coordinated service migration** (Stag Hunt; measured throughput 1,000 / 700 / 0 jobs). |
| Executable applied task 2 | **ABSENT** (no data). Specified as **T2, simultaneous shared-runtime selection** (BoS; measured throughput 1,000 / 600 / 0 jobs). |

Spec: `applied_tasks_spec_20261010/SPEC.md` (draft, not frozen).
- **2026-10-13 design (review only, not authorised):** `STUDY3_PROTOCOL_PROPOSAL_20261013.md` is now one worked abstract/migration example (M07). The item bank, cell matrix, counts and costs are deferred until scientific review; the earlier ≈ $319 budget is withdrawn. T2/T2-A stay an extension. Existing results and authorisations are unchanged.
- **2026-10-14 item M07 implemented (completed; local only):** `study3_item_M07_20261013/`.
  - Authorization, verbatim: "This authorizes local implementation and software checks only: no model API calls, training, or resumed experiments." (user, 2026-10-14 ≈02:40 UTC, session `80332460`).
  - All 25 joint actions were executed over real localhost TCP (3 reps × 2 services). Result: KEEP 700; matching MIGRATE 1,000; any other combination 0. No discrepancy and no silent corruption.
  - Prompts are drafted. The pilot (≈ 354 calls, ≈ $5, cap $8) is **proposed, not authorised**. $0 spent.
- **2026-10-14 M07 basic simultaneous Stag Hunt, SELF condition (prepared; local only):** `study3_item_M07_20261013/basic_stag_hunt/`.
  - Request: prepare prompts and pairing/scoring; "No model calls or training"; "Keep collection unstarted" (user, 2026-10-14 ≈03:30 UTC, session `80332460`).
  - Draft action and prediction prompts; seeded per-call option order; live partners from fresh SELF action responses (not reference pools); pairing/scoring self-test passed on synthetic data.
  - Pilot 128 calls, ≈ $1.3 (cap $2) is **proposed, not authorised**; with the fixed-partner pilot 482 calls ≈ $6.3 (cap $10). $0 spent.
  - 2026-10-14 ≈04:00 UTC revision (local only; "do not make API calls, train, or start either pilot"): prediction prompt now asks for order-averaged probabilities; per-option selection rate by position; prediction scoring fixed (TVD; mean multiclass Brier; mean log loss with ε = .01 clip-then-renormalize; implied best response with ties kept). Self-test passed. Status unchanged: prepared, not run; pilots not authorised; budgets unchanged.
  - 2026-10-14 scoring spec accepted (user; "Local documentation/prompt edits only; no API calls or training"). Removed "in the order listed above" from the prediction output line; stated pilot prediction metrics are descriptive (target = 40 actions per model). Status unchanged: prepared, not run; pilots not authorised; scope and budgets unchanged.
  - 2026-10-14 milestone closed (review): SELF preparation accepted by user as ready for the proposed pilot; no further prep edits. Evidence: self-test passes; 120 regenerated prompts carry the corrected wording (`basic_stag_hunt/`; sha256 prefixes: action_selfplay f3289159, prediction_selfplay 1ef17834, options_block5 975413b7, selfplay.py 49eb3c60). Cost $0. Next: once authorised, run the 8-call format check first (≈ $0.10), inspect outputs and parsing, then proceed within approved scope. SELF pilot ≈ $1.30, cap $2 proposed; combined cap $10 proposed. Both pilots NOT authorised.
  - **2026-10-14 format check (completed, execution).** Authorization, verbatim: "run" (user, 2026-10-14 ≈04:00 UTC, session `80332460`). Read narrowly as the recorded next action only: the 8-call format check, then stop and inspect. The SELF pilot and the fixed-partner pilot remain **not authorised**.
    - Finding: GPT-5.5 4/4 parsed (actions json-b64 ×2; predictions put json-b64 at 70% / 60%, one an exact KEEP|json-b64 tie). Opus 5 0/4 parsed: three empty replies with 0 output tokens, one prediction cut off after 3 lines (56 tokens). stop_reason was not logged, so the cause is not identified.
    - Evidence: `basic_stag_hunt/results/format_check_20261014_000026/responses.jsonl`; runner `code/run_format_check.py` (env /opt/anaconda3 python; openai 2.35.1, anthropic 0.84.0).
    - Cost: $0.045 logged (8 calls).
    - Next: diagnose the Opus empty outputs (runner now logs stop_reason); any re-check needs new authorization. Pilot not started.
  - **2026-10-14 Opus format-failure diagnosis (completed, review; local artifacts only, "No API calls, retries, training, or pilots").**
    - Finding: all 4 Opus requests were accepted (Message returned, model claude-opus-5); visible text empty ×3 and cut mid-line ×1; reported output_tokens 0/0/0/56 vs max_tokens 4000. stop_reason, block types and raw responses were not retained, so absent generation is not established. M07 is the project's first text-only Opus request on this surface (all earlier ones sent an image); prior successful Opus runs show no empty text.
    - Leading hypothesis: stop_reason = "refusal" (unconfirmed).
    - Logging fixed: runner now keeps stop reason, full usage, block types/lengths, response id, raw response, and error body/status; verified offline.
    - Cost: $0 (recorded spend stays $0.045).
    - Next (proposed, NOT authorised): re-send the 4 identical Opus requests with full logging; expected ≈ $0.02, hard cap $0.50. Both pilots NOT authorised.
  - **2026-10-14 Opus diagnostic (completed, execution).** Authorization, verbatim: "Run the approved M07 Opus diagnostic: up to 4 calls, sequentially, $0.50 hard cap for this diagnostic." (user, 2026-10-14, session `80332460`).
    - Finding: the first re-sent request (fc_action|0; prompt sha256 497c534c… verified against a fresh render) returned stop_reason "refusal", stop_details category "cyber" ("triggered restrictions on violative cyber content"), content [] and output_tokens 0. Stopped per the rule; 3 calls not sent. This is the repeat's stop reason, not proof of the original calls' cause.
    - Evidence: `basic_stag_hunt/results/opus_diagnostic_20261014_001153/` (diagnostic.jsonl with raw response; message id msg_011Cg1UkzbQupBeBypuhqiwd).
    - Cost: $0.00197 (1 call). Cumulative M07 API spend $0.04687.
    - Next: design decision on the Opus prompt content (needs review; no prompt changes made). Both pilots NOT authorised.
- **2026-10-14 item SHAPES prepared (completed, local only; "no API calls or training").** `study3_item_SHAPES_20261014/`.
  - Finding: a new abstract Stag Hunt item with labels CIRCLE/SQUARE/TRIANGLE/STAR. Protocol descriptions and the JSON sentence are removed. KEEP, payoffs, randomization, pairing and scoring are unchanged, and the templates are byte-identical to M07's. Offline validation passed: no protocol/JSON vocabulary; identical stimulus across models apart from model name. Not tested against the refusal.
  - **Not poolable with M07:** removing protocol semantics and the explicit JSON cue changes the stimulus.
  - Evidence: README.md; code/selfplay.py sha 527341f9…; manifest_PROPOSED.jsonl sha 30cd5890…. M07 is unchanged (27 files hash-identical).
  - Cost: $0. Cumulative Study 3 M07/SHAPES API spend $0.04687.
  - Next: review of the rendered prompts; any format check or pilot needs authorization. Both pilots NOT authorised.
- **2026-10-14 SHAPES SELF run (stopped at format check; execution).** Authorization, verbatim: "User authorises running SHAPES SELF now. Hard cap: $2 total for this run, including format checks." (user, 2026-10-14, session `80332460`).
  - Runner: `study3_item_SHAPES_20261014/code/run_shapes.py`, with M07's full logging. Sequential, max_retries=0. Added GPT max_output_tokens=4000 so each call has a finite maximum cost for the budget rule.
  - Finding: 6 of 7 format-check calls passed. No refusals; all stop reasons were normal.
    - Actions: GPT STAR ×2; Opus KEEP ×2.
    - Predictions: GPT KEEP 80%; Opus KEEP 72%.
    - Call 7 (GPT prediction 1) failed parsing: it echoed the display suffix ("CIRCLE (label): 4%", KEEP 92%).
    - Stopped per the rule. Call 8 was not sent, and the pilot did not start.
  - Evidence: `results/run_20261014_002715/` (format_check_responses.jsonl with raw responses; run_log.json).
  - Cost: $0.08126 this run. Cumulative $0.12814.
  - Next: decide whether the parser should accept the "(label)" suffix (no prompt change) before any rerun; needs user decision. Fixed-partner pilot NOT authorised.
  - **Parser amendment (2026-10-14, before pilot collection; user-directed).** The prediction parser accepts an optional trailing "(label)" on the four label names only, for both models. All other rules are unchanged; no prompt change. The original failure record is preserved; the corrected parse of the 7 saved replies (7/7 valid) is in `format_check_amended_parse.jsonl`. selfplay.py sha 7181cba7….
    - Resume instruction: send only the outstanding Opus format-check prediction, then the pilot if it passes. Same $2 run cap ($0.08126 spent, $1.91874 remaining). GPT 4,000-token cap retained.
    - Cap change, verbatim (user, 2026-10-14 ≈12:20 EDT, mid-run): "dont worry about the $2 cap - go under $20". The SHAPES SELF run cap is now $20; scope is unchanged (format check + 40 actions + 20 predictions per model). The fixed-partner pilot remains unauthorised.
    - Concurrency: the user asked "send 4-6 calls at once" while the API was taking 80–160 s per call. By then latency had recovered and 96 of 120 pilot calls were done, so the sequential process was left to finish rather than killed mid-call. The concurrent resume mode (`--resume-concurrent`) was written but not used.
  - **2026-10-14 SHAPES SELF pilot (completed, execution).**
    - Finding:
      - Opus 5 chose KEEP 40/40, so all 20 pairs were both-KEEP (7.00).
      - GPT-5.5 chose STAR .525, CIRCLE .325, KEEP .15. Primary pairs 11 coordinated / 4 miscoordinated / 4 mixed / 1 both-KEEP, mean 6.55. All-pairs expected 4.74 [4.48, 5.73].
      - Predictions implied KEEP 20/20 for both models. GPT's mean predicted KEEP was .727 vs .15 actual; Opus .613 vs 1.00.
      - TVD/Brier/log loss (descriptive): GPT .655 / 1.235 / 2.404; Opus .388 / .208 / .503.
      - 0 invalid, 0 refusals.
    - Evidence: `study3_item_SHAPES_20261014/results/run_20261014_002715/` (pilot_responses.jsonl, scored/summary.json, scored/pairs.csv, resume_log.json).
    - Cost: pilot $1.19368; SHAPES run total $1.28312; cumulative Study 3 M07/SHAPES API spend $1.32999 (cap $20).
    - Next: user review of the pilot. Fixed-partner pilot NOT authorised.
  - **2026-10-14 SHAPES pilot reasoning review + interpretation correction (completed, review; "Local analysis only; no new API calls").**
    - Finding: interpretation corrected. Both models' forecasts miss observed frequencies (TVD GPT .655, Opus .388). Opus actions agree with its prediction-implied best response (KEEP 40/40 vs 20/20); GPT actions mostly do not (34/40 labels vs implied KEEP 20/20). Prediction and action are separate calls/roles, not one instance contradicting itself.
    - GPT summaries (single coder, overlapping, not reliability-tested; 23/40 action and 13/20 prediction calls had a non-empty summary): copy symmetry 16/23 vs 3/13; shape salience 19/23 vs 7/13; option order 12/23 vs 10/13; safety/EV 15/23 vs 8/13. Descriptive only; no motives inferred.
    - Bootstrap verified: percentile bootstrap, 2,000 replicates, resampling the 40 responses and recomputing the U-statistic; reproduces [4.48, 5.73]. Caveat: copy-to-copy pairs in replicates inflate it (boot mean 4.868 vs 4.742). Copy-excluded diagnostic [4.35, 5.60] is NOT adopted; user decision.
    - Evidence: `study3_item_SHAPES_20261014/results/run_20261014_002715/analysis_reasoning_20261014/` (REPORT.md, code_reasoning.py, gpt_reasoning_coded.json, counts.json).
    - Cost: $0. Cumulative stays $1.32999.
    - Next: user decides on the CI correction. Fixed-partner pilot NOT authorised.
    - CI decision (user, 2026-10-14): "Preserve SHAPES, its original bootstrap interval and all raw records; do not adopt copy-excluded resampling." The recorded interval [4.48, 5.73] stands.
- **2026-10-14 GREEN core preparation (completed, review/preparation; "Local preparation only; no model calls").** `study3_green_core_20261014/`.
  - Finding:
    - The archived GREEN-match game (study4 pilot, 10 same unmarked / 5 both GREEN / 0 otherwise) is set up as the proposed core.
    - 14 candidates are frozen (FROZEN_CANDIDATES.json sha256 0f653474…) before any new outcome. Old labels are historical strata only.
    - The m3_mirror_v6 renderer, mapping and GREEN assignment are restored pixel-identically; the archived PNGs are used by hash.
    - Prompts: archived ones are reused verbatim (sha8 asserted) and one new WITHHELD clause is added, giving 4 actual-partner × disclosure cells with symmetric information. Predictions are separate calls. A POLICY/LIVE split is proposed.
    - Flags: every historical label comes from copy-framed Stage A (no GREEN); no GPT COPY or prediction measurements exist in the GREEN game; pilot rows lack stop reason, reasoning and raw responses.
    - Migration needs KEEP removed and a match-only marked format (500 jobs) to match the payoff table exactly.
  - Evidence: DESIGN_PREP.md, FROZEN_CANDIDATES.json, code/green_core_prompts.py, code/freeze_candidates.py, prompts/PROMPTS_RENDERED.md.
  - Cost: $0. Cumulative stays $1.32999.
  - Next: user decisions D1–D8 in DESIGN_PREP.md (GREEN payoff 5 vs 7 first). No collection authorised. Fixed-partner pilot NOT authorised.
- **2026-10-15 GREEN core: D1–D8 record + 5-point / 7-point reconciliation (completed, review; "Local reconciliation and analysis only; no model calls or new spending").** Prospective GREEN benchmark only; nothing here touches the frozen paper.
  - **Resolutions recorded from the user's 2026-10-15 message:**
    - The 14 frozen candidates stay unchanged (FROZEN_CANDIDATES.json sha256 0f653474… re-verified against its .sha256).
    - Collection remains **unauthorised**. Fixed-partner pilot NOT authorised.
    - D1–D8: the message makes no explicit choice on any of the eight, so all eight stay **unresolved**. The original proposals in DESIGN_PREP.md are preserved unedited.
  - **Claude recommendations, 2026-10-15 (proposed, not adopted):** D1 5; D2 keep archived wording; D3 approve; D4 all 14 as core, m3_mirror_v6 as worked example; D5 keep archived per-model order and disclose; D6 approve, seed fixed before collection; D7 M07 full logging + GPT max_output_tokens 4000 (disclosed settings change); D8 after D1. **The D1 recommendation predates the reconciliation below and should be re-read in its light.**
  - **Reconciliation: two GREEN games, shared stimuli.**
    - *5-point:* `study4_relational_staghunt_20260908/pilot_run_20260908_231250` (`code/pilot_prompts.py`: green 5 / same unmarked 10 / mismatch 0). Claude focal; GPT only as partner (OTHER/UNKNOWN). Partner wording "same / different underlying policy".
    - *7-point:* `~/Desktop/Superrationality/Stag/gpt_staghunt`, GPT-5.5 (`gpt-5.5-2026-04-23`, effort low) only, framing-only partner (no live pairing), "trained using a different training dataset and … algorithm" wording, CHOICE-slot answer. Runs: `results/gate_game_context` (7 arrays × COPY/DIFFERENT × 24, 336 calls) and `results/confirmatory_20260911_161319` (FROZEN_CONFIRMATORY.json; 4 arrays × 2 × 72, 576 calls, $5.93). Its m3_mirror_v6 result: P(TARGET) COPY 1.000 / DIFFERENT .681; GREEN 0/72 vs 23/72.
    - *Overlap with the 14:* m3_mirror_v6 (gate + confirmatory) and m4_contour_v4 (gate only; failed the gate). Their `data/stimuli_green/` PNGs are byte-identical to the frozen `perm_png_sha256` (24/24 each, in order; verified 2026-10-15), with the same GREEN object (sym2; continuous1_lw9). The confirmatory combined image hash matches its spec. The other 12 candidates appear in no Stag result file found (design docs only).
    - *Correction to the 10-14 flag* "No GPT COPY action … exist in the GREEN game": true **for the 5-point game only**. In the 7-point game GPT COPY actions exist for m3_mirror_v6 (24 gate + 72 confirmatory) and m4_contour_v4 (24 gate). No GPT predictions and no WITHHELD cell were found in either game.
    - *Payoff context for D1:* every other GREEN spec inspected uses 7 (gpt_staghunt confirmatory/state-specific, opus_staghunt statespec (FROZEN_OPUS_STATESPEC, _v3, _v4), staghunt_high_effort GPT/Opus, rational_agent_collection). The 5-point study4 pilot is the only 5-point game found. So D1 = 5 restores the pilot; D1 = 7 matches the later GPT/Opus GREEN runs. Neither is poolable with the other.
    - *Not poolable regardless of D1:* partner wording, answer format and partner structure (framing-only vs paired) all differ between the two games.
    - *Selection note:* the 7-point m3_mirror_v6 outcomes were reported 2026-09-11 and re-read 2026-10-15, after the 10-14 freeze; nothing was relabelled or dropped. 5-point pilot responses were still not opened.
  - **Scope of absence claims** (hold only for the files inspected): study4 `code/pilot_prompts.py` and `pilot_run_20260908_231250` metadata; `Stag/gpt_staghunt/{design,results,data/stimuli_green,src}`; every `FROZEN*.json` under `Stag/`; a grep of `Stag/` for the 14 array ids. `Stag/trace_prereg/*.csv` mentions m3_mirror_v6 but its cell contents were **not** inspected.
  - Evidence: this entry; hashes above. Cost $0. Cumulative Study 3 M07/SHAPES API spend stays $1.32999.
  - Next: user decides D1 (now with the 7-point context), then D2–D8. Collection still not authorised.
- **2026-10-15 Study 3A comparator verification + item inventory (completed, review; "Local verification only; no model calls or spending").** Active task stays Study 3A, the guaranteed-PASS Stag Hunt.
  - Project map: the request refers to a "supplied outline", but no outline came with it. Nothing has been adopted as the project map; the existing ledger structure is unchanged.
  - **Pending scientific decisions (recorded, NOT adopted; protocol unchanged; collection not expanded):**
    1. Add payoff and matching outcomes to Study 3A reporting (proposed).
    2. Sequence 3A → 3C first (proposed).
  - **Finding 1, poster vs game.** The final poster (`~/Downloads/LLM_self_coordination_poster-2.pptx`, Sep 16 15:44) benchmarks the **GREEN Hi–Lo game**, not the PASS game: "Vref = max{V(p₀), 7}; V(p) = 10 Σₐ≠g p(a)² + 7p(g)²". Its 7 requires both players to choose green. No on-disk code implementing Vref was found (searched Superrationality, Coordination, Downloads). The guaranteed-PASS game is the paper's Study 3; it has no poster panel.
  - **Finding 2, implemented PASS-game comparator** (`Stag/two_model_staghunt_20260916/src/analyze.py`; reused by Fable/Qwen; asserted in `paper_assembly_20261010/code/study3_benchmark_bias.py`):
    - c0 = ĉ = Σ nₐ(nₐ−1)/(N(N−1)) (l. 56–58), the unbiased estimate of Σp₀(a)² from 20 fresh Stage 0 draws. The Stage 0 prompt `d40ea45d` is copy-framed pure coordination with no PASS and no green, and the order is randomised.
    - B = max(7, 10ĉ) (l. 124). **Partner participation is not included**: B assumes both PLAY or both PASS. **The comparator cannot choose an object**: only PLAY vs PASS, with the object fixed at the Stage 0 distribution.
    - V̂ = 7S/N + 10 Σ mₐ(mₐ−1)/(N(N−1)) (l. 40–43). It includes partner PASS; PLAY against a PASSer pays 0 (prompt `49e35910`).
  - **Finding 3, discrepancy with a full-action best response** [diagnostic; plug-in max, biased upward; scratch only, not written to project]. BRgame = max(7, 10·maxₐ mₐ/N) against the actual in-game COPY partner. Mean B / V̂ / BRgame: GPT low 8.12 / 7.85 / 8.70; Opus low 8.20 / 7.08 / 7.50; Fable 8.94 / 6.90 / 7.30; Qwen off 7.86 / 6.08 / 7.60. Against the real abstaining partner, Opus, Fable and Qwen's shortfall shrinks (V̂ − BRgame −0.42 / −0.40 / −1.52 vs V̂ − B −1.12 / −2.04 / −1.78). GPT's widens (−0.85 vs −0.27).
  - **Finding 4, reusable items:** 10 items per model in `two_model_staghunt_20260916` (Stage 0 30, COPY 30, DIFFERENT 20 at low effort; high effort COPY only, n = 10). Fable on the Opus items (20/20/20); Qwen 10 items × 2 orientations; `gpt_staghunt_pilot_20260916` 10 other arrays without fresh Stage 0. Stimuli are a subset of the Study 1a set. Study 1 overlap is 4 frontier arrays (GPT F18, F27; Opus F30, F37). The Opus configuration differs (Study 1a thinking disabled vs Stag adaptive-low). GPT/Opus share only F01_m0 and F36_m0.
  - **Finding 5, missing in-game measurements** (scope: `results/*/responses.jsonl` + `design/` of those runs; Study 1/2 CSVs filtered to these arrays): no partner predictions (object or PLAY rate) in any 3A run; object policy is seen only after PLAY (Opus 0 PLAY on 4/10 COPY items, verified; Fable 5/10); no high-effort DIFFERENT; no real DIFFERENT partner, so no DIFFERENT payoff; no WITHHELD; no same-order arm; no Stage 0 under DIFFERENT framing.
  - **Finding 6, completed vs proposed:** Study 1/2 results are completed or frozen as listed in A. The mechanisms linking them to 3A are **proposed, with no direct test**: reliability judgement → participation (4 overlapping arrays, Opus configuration differs); self-projection → choices (Study 3 has no predictions); Study 2 partner sensitivity → in-game COPY−DIFF (descriptive only); policy transfer (assumed in B).
  - Evidence: agent scratch at `/private/tmp/claude-501/-Users-calypsocalcott-Desktop-Coordination-Self-Coordination/fa80d8b5-9f90-4a27-8730-6dbf8ded0dc7/scratchpad/{comparator,inventory}/`. Cost $0.
  - Next: user decides whether "Study 3A = poster's guaranteed-PASS game" should be re-labelled (the poster shows the GREEN game) and whether to adopt pending decisions 1–2.
- **2026-10-15 Study 3A feasibility pilot (completed, execution).** `study3a_feasibility_20261015/`. Pipeline and measurement pilot, not a hypothesis test.
  - Authorization, verbatim:
    - "This prompt authorizes at most $3 of new spend, including retries, and never overrides the recorded $20 cumulative cap." (user, 2026-10-15)
    - "we can go up to $50 if needed" (user, 2026-10-15, mid-run).
    - Applied narrowly: scope unchanged (one pilot, ≤ 384 calls, no prediction calls, no larger run); run hard cap $10; cumulative Study 3 cap $20 still respected.
  - Preflight passed:
    - Prices verified current (GPT-5.5 $5/$30; Opus 5 $5/$25).
    - Under the original $3 cap the run was stopped before calls: expected $3.66, max $7.17. It proceeds only under the $50 message.
    - Scoring checks 18/18 (`code/test_scoring.py`), including agreement with the historical `pair_payoff`/`v_hat` and the documented discrepancy (historical B = 10 vs full-action BR = 7 against an always-PASS partner).
    - Dry run and offline mock passed.
  - Frozen: `design/FROZEN.json` (sha256 aa6f81a9…), `design/jobs.jsonl` (94f4936d…).
    - Focal GPT-5.5 (gpt-5.5-2026-04-23, effort low, summary auto, no output cap). COPY partner GPT-5.5; DIFFERENT partner Claude Opus 5 (claude-opus-5, adaptive summarized, effort low, max_tokens 4000).
    - Archived prompts 49e35910 / 8222a371, verbatim as sent.
    - Items by recorded GPT Stage A labels only: strong F01_oddone_m0, F02_size_m2; weak F27_linecount_m1, F41_contain_m2.
    - Per item × condition: 24 policy + 12 focal + 12 fresh = 384 calls. Permutations shuffled independently.
  - New scoring (`code/scoring.py`) is separate from the historical calculation, which is not modified.
  - **Finding:**
    - 384/384 parsed; 0 invalid, refusals, API failures or retries.
    - Strong items F01 and F02 coordinate perfectly in COPY (BR 10, regret 0, match 1.00).
    - **Weak label fails for F27:** GPT plays object 3 in 24/24 draws (position spread 6/6/6/6; archived in-game COPY also 30/30), while Stage 0/Stage A were diffuse. The label measures the reference task, not the game. Not relabelled.
    - F41 weak is consistent: COPY regret +.193 [+.049, +.353], cross payoff .47, match .47.
    - DIFFERENT (Opus partner): Opus passes 18/24 on F27 and 24/24 on F41, so BR = PASS. GPT mostly plays, giving regret +.503 [+.338, +.644] and +.408 [+.233, +.583].
  - Evidence: `results/pilot/{requests,responses,run_ledger}.jsonl`; `results/pilot/analysis/{REPORT.md,cells.csv,distributions.csv,summary.json}`.
  - Cost: $3.4225 (GPT $2.4731, Opus $0.9494). Cumulative Study 3 exploratory spend $4.7525 (cap $20).
  - Next: user review. No larger run. Design decision pending: item selection for any follow-up must use in-game policy measurements, not reference-task labels.
- **2026-10-15 Study 3A in-game inventory + follow-up proposal (completed review; follow-up PROPOSED, not authorised; "Local work only; no model calls or spending").** `study3a_feasibility_20261015/inventory/` (`build_inventory.py`, `inventory_{cells,pooled}.csv`, `followup_plan.py`, `followup_items.csv`, `PROPOSAL_followup.md`).
  - Finding: 152 in-game source cells across 4 runs, all on archived game prompts 49e35910/8222a371. Images match the canonical stimuli 152/152. Reference-task rows were excluded by prompt hash. There are 19 GPT-5.5 low-effort candidate items. Opus DIFFERENT draws exist on only 6 of them (F01, F02_m2, F27, F41_m2, F05_orient_m1, F36).
  - Proposed: all 19 items, with no outcome-based selection; historical labels kept as provenance only. Core = 492 new Opus calls (≈ $3.24; $5.12 at the maximum per-call cost). Option (ii) adds 360 GPT COPY policy calls (total ≈ $6.95; $13.79 at the maximum). Decisions 1–8 are listed in the proposal.
  - Cost $0.
- **2026-10-15 Study 3A pooling checks + plan v2 (completed review; plan PROPOSED, not authorised; "Local checks only; no model calls or spending").** `inventory/verify_pooling.py` → `pooling_checks.{csv,txt}`; `inventory/PROPOSAL_followup_v2.md` supersedes v1 (v1 header marked only).
  - **GPT pooling supported.** Identical request shape (text then image; reasoning low/auto; no output cap). Billed input tokens 818/813 on every call; returned `gpt-5.5-2026-04-23` on every call; only the requested string differs (alias vs pinned). All 25 overlapping item × condition comparisons have permutation p ≥ .17; max TVD .32. Power is limited (9/25 unanimous).
  - **Opus pooling not established.** Inputs are identical (1,015 tokens) under the undated alias, but the only behavioural overlap (F01 DIFFERENT) is unanimous. Recollect F05_orient_m1 + F36_split_m0: 48 actions, ≈ $0.32.
  - **Plan v2:** 900 calls (GPT COPY policy 360; Opus DIFFERENT policy 360; Opus fresh 180). Expected $7.57 (p99.9 $7.80, resampled).
    - Hard stop rule: reserve each call at its token-limit bound (Opus $0.1051; GPT $0.1241, which needs `max_output_tokens` 4000 — a settings change, decision D2) against R = $20 − recomputed prior cumulative ($4.7525).
    - s reported continuously with a Jeffreys posterior and P(s > .7) (`scoring.strength`; test_scoring 23/23).
    - Pilot analysis regenerated identically by a seeded re-run.
  - Cost $0. Next: user decisions D1–D7 in v2 §5. Collection not authorised.
- **2026-10-16 Study 3A read-only design diagnostic (completed, review).** Authorisation, verbatim: "okay. send CC to do the read-only diagnostic" (user, relayed by the ChatGPT research manager, message `study3a-readonly-design-diagnostic-01`). `study3a_feasibility_20261015/inventory/diagnostic_20261016/` (REPORT.md, diagnostic_items.csv, diagnostic.py, validation.json).
  - Finding: s ranges .16–1.00 across the 19 items. 9 have P(s > .7) ≥ .95, 4 sit near .7 and 6 are clearly below. Only 4 s values come from independent policy samples; 15 are exploratory reuse of evaluation draws.
  - Low s combines GPT passing (.37–.63) with object dispersion.
  - Opus DIFFERENT is measured on only 6 items. Three have September draws, but only 2 are September-only (F05_orient_m1, F36_split_m0); F01 also has independent October data. *(Corrected 2026-10-16 after ChatGPT review; previously "3 of them September-only". Results unchanged.)* Where measured, incompatibility is Opus passing (.75–1.00), not a different object. Strong COPY + incompatible: F27 (independent) and F36 (archived).
  - Validation: 1,469 rows; 0 mapping errors; 0 invalid/refused/failed; counts match inventory_pooled.
  - Cost: $0 experiment spend; agent inference unknown (not free). Cumulative $4.7525 of $20.
  - Next: the user and ChatGPT decide the design. No collection authorised. Completion report in review_loop/completions/.
- **2026-10-16 Study 3A estimand and design memo (completed review; both alternatives PROPOSED, neither adopted).** ChatGPT manager message `study3a-estimand-design-memo-01`, under the user's request for manager/Claude iteration within the $20 cap. `inventory/diagnostic_20261016/DESIGN_MEMO_estimand_20261016.md`.
  - **Finding:** v2 estimates descriptive decision quality against actual partners under the joint COPY/DIFFERENT conditions. It cannot identify own-policy use or a disclosure effect, because partner, policy and description change together.
  - **Alternatives:**
    - (A) v2: 900 calls, ≈ $7.27 expected.
    - (B) Named vs archived generic disclosure with the partner fixed at Opus: ≈ $1.94–13.91 by k and control type.
    - A + B at k = 19 exceeds the $15.25 remaining.
  - **Scoring:** plug-in regret_norm ≥ 0 by construction (min 0.0 over 20,000 random pairs); an independent shortfall can be negative. The "not clipped" wording is flagged, not edited. Plug-in max bias example 7.00 → 7.37 at n = 24.
  - Cost $0. Next: user Design decisions (memo §4).
  - **Addendum 01 (2026-10-16, after ChatGPT review `study3a-design-memo-refinement-01`; PROPOSED).** `DESIGN_MEMO_addendum_01_20261016.md`; the memo now carries a refinement note.
    - B relabelled: a mutual (dyadic) naming intervention, not focal-only information and not disclosure vs withholding in general.
    - Added for comparison only, C: focal-only truthful disclosure vs withholding, with Opus and its prompt fixed. Needs a new fixed partner prompt and two new focal prompts (not drafted). One shared Opus policy; nothing reused. Per item 84 calls, $0.73 expected, $9.74 bound.
    - B costs separated into incremental vs standalone.
    - Own-policy use is not identified by A, B or C.
    - Cost $0.
- **2026-10-16 Study 3A policy-knowledge pilot preparation (completed preparation; pilot PROPOSED, not frozen, not authorised).** `study3a_policy_knowledge_PROPOSED_20261016/`.
  - Authorisation, verbatim (user, relayed by ChatGPT manager message `study3a-policy-knowledge-pilot-prep-01`):
    - "okay. im going to leave you to sort this out. i want you to get to the point where you and claude code can run a pilot fo the stag hunt with in-game stimuli policies (weak v strong). can you do that?"
    - "wait. we dont just want to test partner identity framing; we also want to test real use of policy knowledge".
    - $0 spend authorised for this step.
  - Identity-only proposals (v2, memo B and C) superseded as the sole target.
  - **Proposed core (focal GPT-5.5; PASS 7 / match 10):** independent GPT COPY and Opus DIFFERENT policy draws; spontaneous forecasts F_COPY and F_DIFF; Opus auditor AU_COPY; act-only E0 vs forecast-then-act E1.
    - (i) access: self-forecast vs independent own policy, beyond uniform, other items and the auditor;
    - (ii) target: projection index;
    - (iii) use: Δ same-q regret E1 − E0 plus BR-consistency.
  - 4 candidate items for review: F27 and F14 strong-PLAY; F05_m5 and F12_m3 diffuse. Screening rule fixed in advance; all items retained.
  - 504 calls; expected ≈ $6.73 (range $4.59–8.87); hard bound $60.44; proposed cap $8.
  - Offline self-test 23/23. Historical scoring, raw results and frozen files untouched.
  - Cost $0. Next: user + ChatGPT Design decisions 1–9 in PROPOSAL_PROPOSED.md §7.
- **Milestones:**
  - M1: harnesses + payoff validation, $0;
  - M2: items, prompts, freeze, re-cost, $0;
  - M3: format pilot, 112 calls, ≈ $2;
  - M4: main collection;
  - M5: analysis.
- **Collection:** 4,720 calls, **≈ $84 expected, hard cap $118**. The COPY-only minimum is 2,560 calls plus the pilot, ≈ $48 (cap $68).
- **Not authorised.** No calls made.

## C. Previously authorised and prepared jobs

| job | authorisation | status |
|---|---|---|
| Study 1 high-reasoning (+ Amendment 1) | authorised | complete, $171.40 |
| Qwen continuation training + calibration | authorised | complete, ≈ $32.15 |
| Continuation PLAY/PASS | authorised (cap $16) | complete, $7.95 |
| **Qwen crossed option-choice prediction** | authorised 2026-10-09 ($3 total cap) | **complete**, $2.28 conservative |
| **Reasoning-on follow-up** (`qwen_continuation_pilot_20261009/reasoning_followup/`) | **conditional approval of $68** = calibration cap $40 + PLAY/PASS cap $28. The PLAY/PASS phase runs only if the frozen retention criterion returns RETAINED; `run_rfu.py` asserts this.<br>Recorded from the user's 2026-10-10 16:04:48 UTC instruction ("Correct reasoning-follow-up authorization to the existing conditional $68 approval"; session `80332460`).<br>Re-searched 2026-10-13: the only earlier request (2026-10-09 18:39 UTC) asked to *prepare* it and return costs. No separate approval message exists in local session logs. Authorisation is preserved as recorded, not widened. | **NOT STARTED** (re-verified 2026-10-13).<br>- No `results/` directory, no run manifest, no process.<br>- No file under `Stag/` modified since 2026-10-10.<br>- All six frozen hashes intact.<br>- $0 spent. |
| Qwen untrained screen, thinking on (cap $10) | authorised 2026-10-08 | incomplete: 360/600 draws, $4.69, stopped by Tinker HTTP 402; 24 cells resumable (≈ $3) |
| rational_agent Waves 1–2; `policy_specific_self_coordination_20260812_1401` | never approved | not run |

## D. Essential remaining work and cost

| # | work | cost |
|---|---|---|
| 1 | Write the paper text from `paper_assembly_20261010`. **Methods/results drafted 2026-10-13** (`docs/METHODS_RESULTS_DRAFT.md`). Remaining: introduction and discussion, plus the Opus wording decision above. | $0 |
| 2 | (optional, already approved) reasoning-on follow-up | ≤ $40, plus ≤ $28 only if RETAINED |
| 3 | **Approve or edit** the applied-task spec, then build M1–M2 | $0 |
| 4 | M3 pilot + M4 collection for T1, T2 and T2-A | ≈ $84 (cap $118), or COPY-only ≈ $48 (cap $68) |

## Corrections made 2026-10-13 (to v3)

1. The Qwen crossed-study location is `~/Desktop/Superrationality/Stag/…`. "`Stag/`" in this ledger means that folder.
2. The Study 2 Qwen primary is named explicitly (`s2_20260912_181428`). The `pp2x2_…173541` run (run A) is a separate earlier run with different partner wording, reported separately, not superseded (freeze-script comment corrected 2026-10-13).
3. ~~The Opus Study 2 probability-scale interaction (+.263) was previously unreported.~~ **Wrong:** it is in the frozen `REPORT_2x2.txt` (Q2) as +.263 [.057, .463], unpaired bootstrap. The draft now reports the frozen CI first, then the paired and logit sensitivities.
4. **Study 2 methods/results finalised 2026-10-13** (`docs/METHODS_RESULTS_DRAFT.md`, Table S2): per-cell collected/parsed counts, exact partner clauses, configurations verified from output tokens (the stored Opus settings files are stale), CI method per report, relational 13 → 11 items by the pre-fixed retention rule (F26_bumploc_m0, F40_crossang_m2), and the Qwen interaction sign converted. Unresolved facts are listed in the draft's limitations.
5. **Study 2 reporting corrections 2026-10-13** (no calls):
   - Labels: frozen and prespecified are now distinct. Only the Qwen run B contrasts and the relational G/Brier/TVD analyses are prespecified; the GPT/Opus contrasts are frozen only.
   - Opus requested settings: traced to the launch commands in session `54ea082e` plus the runner code. Tokens corroborate; there is no server-side confirmation.
   - Opus frozen and paired CIs are reported together.
   - The relational README temperature is corrected (none sent; the plan said 1.0).
   - The planned log score, per-item CIs and leave-one-item-out check are disclosed as not run.
6. **Study 2 finalised 2026-10-13** (no calls):
   - PLAY/PASS prompts verified per model. The response is called a reliability judgment, not betting. The scoring criterion ("your preferences/way of choosing really is reliable here") does not mention the partner.
   - Labels: frozen = original report, unmodified. Planning labels follow evidence: [planned: plan file], [planned: PI instruction], [not planned in advance].
   - Relational plan written 19:14:22 UTC, before collection (19:17:48). Retention rule stated by the PI at 19:17:03, before re-measurement.
   - Bootstrap explanation corrected: the unpaired bootstrap omits the positive covariance.
   - Planned log score, per-item CIs and LOIO were completed (`study2_relational_prediction_20260912/addendum_20261013/`, spec sha `8504bb62`). The GPT G null depends on F36_split_m2: without it, +.037 [.025, .048].
5. Run A's "superseded" label is softened to "separate earlier run": no document supersedes it; it simply used different wording.

## Corrections to v2

1. **Qwen crossed prediction:** v2 said "proposed, not run" and marked the Qwen choice panel ABSENT. Both were wrong. The study ran on 2026-10-09 under a $3 authorisation, at `Stag/qwen_crossed_prediction_20261009`; its frozen manifest, raw responses, results and figure exports all verify. v2's search missed it.
2. **Reasoning-on follow-up:** v2 said "prepared only, not authorised". It has a conditional $68 approval ($40 + $28, the second conditional on retention). It has not started.
3. **Zero-cost tasks:** listed as pending in v2; now done.
4. **Applied tasks:** v2 said "cannot be costed, no spec". A spec and costs now exist.

## 2026-10-19 — Visual BoS continuation (visual-bos-copy-policy-01) — COMPLETED (execution)
- **Authorisation (verbatim):** "Add $15 — total cap $25" (amendment visual-bos-budget25-resume-01; original FROZEN cap $10 preserved).
- **Finding:** all 512 frozen jobs attempted; 473 valid, 23 invalid (all GPT max_output_tokens, mostly F05/F11), 16 prior connection failures (not retried).
- **Evidence:** `~/.codex/.chatgpt-projects/g-p-6aa069d23ae08191a861f83470dbc913/review_loop/visual_bos/` (claude_execution_receipt.json, completion.json, plots); prior 208-row prefix hash unchanged.
- **Cost:** known API $18.731845 + $3.24384 unresolved reserves = $21.975685 of $25.
- **Next:** manager review; no further calls scheduled.

## 2026-10-20 — Private Convention (private-convention-bos-play5-01) — COMPLETED (execution)
- **Authorisation (verbatim):** "pick up again my laptop crashed $20" (fresh $20 cap; no transfers).
- **Finding:** both candidate sets qualified on fresh validation; COPY partners PLAY near-universally and earn above the guaranteed 5; DIFFERENT partners earn below 5 (exploratory, independent-draw pairing, 4 draws per role/partition cell).
- **Evidence:** `~/.codex/.chatgpt-projects/g-p-6aa069d23ae08191a861f83470dbc913/review_loop/private_convention_participation/` (FROZEN.json, responses.jsonl, qualification.json, analysis/, completion.json, claude_execution_receipt.json).
- **Cost:** $9.81413 metered (all exact), $0 unresolved; cap $20.
- **Next:** manager review.

## 2026-10-20 — Policy Payoff Check (participation-regret-five-model-smoke-01) — COMPLETED (execution)
- **Authorisation:** user's fresh $75 cap and "yes" to the proposed small pilot (relayed by manager; `APPROVED.json`). No transfers.
- **Scope:** GPT-5.5, GPT-6 Sol, Opus 5, Fable 5.1, original Qwen step316 (visual task, thinking-on); F10 curvature + F06 density; Stag Hunt + BoS (2 roles × 2 maps); COPY/DIFFERENT; B 800 forced + C 1200 voluntary at safe 3/6/9.
- **Collection:** 2000/2000 attempted, 1703 valid, 0 API failures. All 297 invalid are Qwen hitting the frozen 8192-token limit mid-thinking (BoS forced 114/128).
- **Finding (exploratory):** normalized participation regret is low for frontier models (≈.006–.11 all-games). GPT-5.5 COPY is ≈0. GPT-6 Sol COPY Stag Hunt is .18: it plays at b=6/9 while its benchmark V≈4.5. PLAY falls with b in every arm and is higher under COPY than DIFFERENT. Qwen BoS is not estimable.
- **Deviation:** the runner's concurrency limit of 8 was defined but not applied. Dispatch was bounded only by the $75 reservation rule (peak ≈440 in flight); the cap held and there were no failures.
- **Evidence:** `~/.codex/.chatgpt-projects/g-p-6aa069d23ae08191a861f83470dbc913/review_loop/participation_regret_smoke/` (FROZEN.json, responses.jsonl, analysis/, completion.json, claude_execution_receipt.json, latest_execution_handoff.json).
- **Cost:** $38.72 metered + $22.09 Qwen token-count estimate = $60.81 of $75; $0 unresolved.
- **Next:** manager review.
