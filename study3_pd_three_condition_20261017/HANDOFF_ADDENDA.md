# Handoff addenda: PD three-condition pilot (2026-10-17)

Staged here because the worktree guard blocked edits to the shared folders. `finalize.sh` appends each block to its target.

## [LEDGER] Prepend under the title of Self_Coordination/COMPLETION_LEDGER_20261009.md

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

## [PASS5_REPORT] Append to study3a_pass5_PROPOSED_20261016/results/run/analysis/REPORT.md

## Reporting corrections (2026-10-17, manager-verified; raw results and science unchanged)
- "The gain came entirely from F01" is too strong. GPT COPY F27 realized matching also rose, from .090909 (PASS = 7) to .227273 (PASS = 5).
- "Diffuse items all PASS" should read "mostly PASS": one GPT F05 COPY evaluation draw played.

## [DIARY] Insert after the format block of ~/claudine/projects/self-coordination-diary.md

## 2026-10-17 (PD three-condition pilot - AUTHORISED fresh $20, COMPLETED)
- Ran: one-shot PD (8/0/10/3), neutral A/B balanced, GPT-5.5 + Opus 5 x same/different/fixed-response, 384 calls, $1.99; cumulative $53.31.
- Result: Opus 64/64 cooperate in all three conditions (ceiling, evidential "correlated choice" reasons, even for a sealed prerecorded partner; 24/64 different-model reasons misread as Stag Hunt). GPT 1/64, 0/64, 6/64 - all cooperation under A=cooperate. No identifiable partner effect.
- Next: review with ChatGPT; no further experiments. Also logged Pilot-3 reporting corrections (F27 GPT COPY match .09->.23; one F05 eval played).
