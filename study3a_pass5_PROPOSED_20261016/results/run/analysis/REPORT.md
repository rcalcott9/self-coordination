# Study 3A Pilot 3: PASS = 5 reciprocal-confidence pilot — 2026-10-16 (real results)

- **Authorisation, verbatim:** "great. run the adapted pilot" and "okay now run pilot if ready" (user, via ChatGPT manager `study3a-pass5-adapted-pilot-execution-20usd-01`). The manager records the latter as approving its requested fresh $20 cap.
- **Frozen design:** FROZEN.json sha256 df263507…; jobs bc41207f…; prompts COPY b5346bb0, DIFFERENT c12a5ed6.
- **Game:** PASS 5; PLAY j 10 iff the partner PLAYs j, else 0; threshold 0.50.
- **Prompt:** the same symmetric two-step appendix as the PASS = 7 pilot, with exactly 6 incentive substitutions. Every player in a condition got the same prompt.
- **Sample:** the same 576 jobs, permutations and settings: 4 items × {GPT-5.5, Opus 5} × {COPY, DIFFERENT}, 24 policy + 12 eval per cell.

## Run
- **576/576 valid.** 0 invalid, 0 refusals, 0 API failures, 0 retries. The 8-call format check is included.
- **Cost:** pilot $10.7143 (cap $20); **cumulative Study 3 spend $51.3162** (ceiling $60.60191). Prices verified at launch.

## Results (4 items, equal weights; same-q regret uses fresh PASS = 5 partner policies; PASS = 7 is the exploratory matched pilot)
| focal | partner | regret [95% CI] (PASS 7) | 10-point match (PASS 7) | joint shortfall (PASS 7)* | focal payoff/10 | PLAY |
|---|---|---|---|---|---|---|
| GPT-5.5 | copy | .020 [.000, .054] (.045) | **.31** (.23) | .391 (.288) | .609 | .40 |
| GPT-5.5 | Opus 5 | **.083** [.052, .115] (.009) | **.25** (.19) | .417 (.263) | .542 | .42 |
| Opus 5 | copy | .000 [.000, .000] (.011) | **.25** (.17) | .375 (.275) | .625 | .25 |
| Opus 5 | GPT-5.5 | .000 [.000, .000] (.036) | **.25** (.19) | .417 (.263) | .625 | .25 |

\* Joint shortfall = (10 − mean dyadic payoff)/10, where 10 is the ideal coordination ceiling (not guaranteed attainable without a shared rule). **It is not comparable across incentive levels**: universal PASS gives .30 at PASS = 7 but .50 at PASS = 5. Use the 10-point match rate to compare the two pilots.

**Figure:** `fig_pass5_outcomes.{png,pdf}`. Three panels: regret (95% bootstrap CI that resamples policy and evaluation draws independently within items), joint shortfall, and 10-point match rate. PASS = 7 pilot: open circles; PASS = 5: filled squares.

**Per item** (`per_item.csv`):
- **F01, the clear odd-one-out:** under PASS = 5, every cell has PLAY = 1.00 (Opus as partner .96), match 1.00 and regret 0. Under PASS = 7, 4–46% passed.
- **F27, an ambiguous rule** (most vs fewest lines):
  - Opus passes in nearly every draw;
  - GPT's COPY play splits 50/50 (match .23);
  - GPT keeps playing against a passing Opus (PLAY .67 vs Opus partner PLAY .04), which gives regret .333, the source of GPT's DIFFERENT regret.
- **F05, F12 (diffuse):** all PASS under both incentives.

**Forecasts and consistency:**
- **Partner-forecast error:** mean TVD .27–.38.
- **BR-consistency:** decisions are best responses to the model's own stated partner forecast in .99–1.00 of cases.
- **EV arithmetic:** GPT 1.000 at every tolerance. Opus .944/.979 (COPY/DIFF) at ≤ 0.01, .979/1.000 at ≤ 0.1, .993/1.000 at ≤ 0.5.

**Explanations:**
- 189 of 213 Opus PASS replies and 278 of 288 GPT replies cite the 0.50 threshold.
- **F27, Opus:** names the split between "most (5) and fewest (2) lines" as the reason no object exceeds 50%.
- **F01, both models:** the only stated risk is the partner passing.

## Interpretation (incentive effect, exploratory; not privileged policy knowledge)
- Lowering PASS from 7 to 5, with the threshold moving from .70 to .50, **raised 10-point coordination in every cell** (+.06 to +.08). This came entirely from the clear focal item F01, which moved to full participation and perfect matching.
- **It did not unlock items whose rule is ambiguous (F27) or diffuse (F05, F12).** On F27, GPT now over-participates against a passing Opus.
- The models respond to the stated payoff threshold in a way that is internally consistent with their own forecasts. Their forecasts about partners remain inaccurate (TVD ≈ .3).
- The change is an incentive effect on participation where a shared salient rule already exists. It is **not** evidence of privileged own-policy knowledge.
- The comparison with the PASS = 7 pilot changes both the incentives and the partners' policies, so it is exploratory.

## Limitations
- 4 items; 12 evaluation draws per cell; unanimous cells give zero-width bootstrap intervals; plug-in regret is biased upward.
- Joint shortfall is incentive-dependent (see note).
- The forecasts and the threshold reminder are bundled in one prompt.
- Same-day comparison; no new act-only arm.

## Reporting corrections (2026-10-17, manager-verified; raw results and science unchanged)
- "The gain came entirely from F01" is too strong. GPT COPY F27 realized matching also rose, from .090909 (PASS = 7) to .227273 (PASS = 5).
- "Diffuse items all PASS" should read "mostly PASS": one GPT F05 COPY evaluation draw played.
