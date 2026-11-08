# Study 3A feasibility pilot — 2026-10-15

Pipeline and measurement pilot, **not a hypothesis test**. Frozen design: `design/FROZEN.json` (sha256 aa6f81a9…), jobs `design/jobs.jsonl` (94f4936d…).
Focal GPT-5.5 (`gpt-5.5-2026-04-23`, effort low). COPY partner GPT-5.5; DIFFERENT partner Claude Opus 5 (`claude-opus-5`, adaptive/summarized, effort low).
Archived prompts `49e35910` (COPY) and `8222a371` (DIFFERENT), verbatim as sent. Positions shuffled independently on every call.

## Run
- 384/384 parsed. 0 invalid, 0 refusals, 0 API failures, 0 retries. Stop reasons: `completed` (GPT), `end_turn` (Opus).
- Cost $3.4225 (GPT $2.4731, Opus $0.9494). Cumulative Study 3 exploratory spend $4.7525 (cap $20).
- Logs: `requests.jsonl` (every attempt, settings), `responses.jsonl` (raw response, stop reason, usage, cost), `run_ledger.jsonl`.

## Measures (per item × partner condition)
- BR = max(7, 10·max_j q(PLAY j)), where q comes from the 24 independent partner-policy draws.
- Normalized regret = (BR − V(p, q))/10, where p is the 12 live focal actions. Not clipped.
- Realized payoff (normalized by 10) and match rate come from fresh focal × partner pairs: 12 index-paired, plus all 144 cross pairs.
- 95% CIs: percentile bootstrap, resampling the three samples independently (2,000 draws).

| item | label | partner | BR [CI] | regret [CI] | payoff, paired | payoff, cross [CI] | match, cross | focal PASS | partner PASS (policy) |
|---|---|---|---|---|---|---|---|---|---|
| F01_oddone_m0 | strong | COPY | 10.00 [10, 10] | .000 | 1.00 | 1.00 | 1.00 | .00 | .00 |
| F01_oddone_m0 | strong | DIFF | 10.00 [10, 10] | .000 | 1.00 | 1.00 | 1.00 | .00 | .00 |
| F02_size_m2 | strong | COPY | 10.00 [10, 10] | .000 | 1.00 | 1.00 | 1.00 | .00 | .00 |
| F02_size_m2 | strong | DIFF | 8.75 [7.50, 10] | .000 | .92 | .92 [.75, 1.00] | .92 | .00 | .125 |
| F27_linecount_m1 | weak | COPY | 10.00 [10, 10] | .000 | 1.00 | 1.00 | 1.00 | .00 | .00 |
| F27_linecount_m1 | weak | DIFF | 7.00 [7, 7] | +.503 [+.338, +.644] | .31 | .27 [.06, .52] | .21 | .08 | .75 |
| F41_contain_m2 | weak | COPY | 7.00 [7.00, 7.92] | +.193 [+.049, +.353] | .42 | .47 [.27, .70] | .47 | .00 | .08 |
| F41_contain_m2 | weak | DIFF | 7.00 [7, 7] | +.408 [+.233, +.583] | .29 | .29 [.12, .47] | .00 | .42 | 1.00 |

## Partner policy, complete distribution (24 draws each; objects are canonical indices)

| item | partner | PASS | PLAY 0 | PLAY 1 | PLAY 2 | PLAY 3 |
|---|---|---|---|---|---|---|
| F01_oddone_m0 | GPT (COPY) | 0 | 0 | 0 | 0 | 24 |
| F01_oddone_m0 | Opus (DIFF) | 0 | 0 | 0 | 0 | 24 |
| F02_size_m2 | GPT (COPY) | 0 | 0 | 0 | 0 | 24 |
| F02_size_m2 | Opus (DIFF) | 3 | 0 | 0 | 0 | 21 |
| F27_linecount_m1 | GPT (COPY) | 0 | 0 | 0 | 0 | 24 |
| F27_linecount_m1 | Opus (DIFF) | 18 | 2 | 0 | 0 | 4 |
| F41_contain_m2 | GPT (COPY) | 2 | 0 | 3 | 15 | 4 |
| F41_contain_m2 | Opus (DIFF) | 24 | 0 | 0 | 0 | 0 |

Focal and fresh distributions are in `distributions.csv`.

## Historical labels (criterion stated in `code/analyze.py` before results were seen)
Strong → PLAY advantageous against the COPY partner policy (10·max_j q > 7); weak → not.
- F01_oddone_m0 strong: **consistent**.
- F02_size_m2 strong: **consistent**.
- F41_contain_m2 weak: **consistent**, but only just (max q = .625; BR CI reaches 7.92).
- **F27_linecount_m1 weak: inconsistent.** GPT plays object 3 in 24/24 draws. The position spread is exactly 6/6/6/6, so this is not a position artifact.
  - The archived in-game COPY data agree (two_model_staghunt: 30/30 PLAY object 3). The archived Stage 0 choices were diffuse (13/10/2/4), as was the historical Stage A label (7/10/1/6).
  - The weak label measures the reference coordination task, not the strategic game. Not relabelled or replaced.

## Caveats
- A unanimous sample gives a degenerate bootstrap interval (e.g. [10, 10]). That reflects the method, not certainty: 24/24 still allows q(PLAY 3) down to about .86 (one-sided 95%).
- BR is a plug-in maximum over objects, biased upward at n = 24.
- DIFFERENT regret is driven by Opus passing (75% and 100% on the two weak items) while GPT plays. COPY vs DIFFERENT changes the partner distribution itself, so the contrast does not isolate any effect of disclosing partner identity.
- Regret's blind spot (both always PASS → regret 0, no 10s) did not occur in any cell here. Report realized payoff and match rate alongside it.
- n = 4 items, 12 focal actions per cell. Descriptive only.
