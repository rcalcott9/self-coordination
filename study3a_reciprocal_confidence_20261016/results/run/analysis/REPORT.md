# Study 3A reciprocal-confidence pilot — 2026-10-16

- **Authorisation, verbatim** (user, via ChatGPT manager `study3a-reciprocal-confidence-pilot-20usd-01`): "yes and new cap for this experiment: $20".
- **Approved spec:** `review_loop/reciprocal_confidence_pilot_APPROVED.json`. Frozen design: `design/FROZEN.json` (sha256 936dd19b…); prompts COPY `b308cb54`, DIFFERENT `5b087c1d`.
- **Prompt:** the baseline game text, then the approved two-step appendix verbatim, then a response schema. **Every player received the same prompt for its condition**, so the appendix statement "both players receive this additional instruction" is true.
- **Settings:** as in the baseline. GPT-5.5 `gpt-5.5-2026-04-23`, effort low, `max_output_tokens` 4000. Opus 5 adaptive thinking, effort low, `max_tokens` 4000.
- **Sample:** 4 items × {GPT-5.5, Opus 5} × {COPY, DIFFERENT}. Per cell: 24 policy and 12 evaluation draws, all new and all under the appendix. The baseline is used only as an exploratory matched-item comparison, never as a partner benchmark.

## Run
- **576/576 calls returned.** 574 valid; 2 invalid; 0 refusals; 0 API failures; 0 retries.
- **The 2 invalid replies** are both Opus F01 DIFFERENT, one eval and one policy draw. Each reported PASS with an object. They were rejected by the frozen parser and not resampled. That leaves n_eval = 11 for Opus F01 DIFFERENT, and n_policy = 23 for the Opus partner sample GPT faces on F01.
- **Cost:** pilot $10.8345 (cap $20); **cumulative Study 3 spend $40.6019** (ceiling $50). The format check (8 calls, $0.154) is included and counted in the sample.

## Results (4 items, equal weights; exploratory; `per_item.csv`, `aggregate.csv`, `realized_vs_baseline.csv`)
| focal | partner | regret, appendix [95% CI] | regret, baseline (same items) | realized payoff/10 appendix (baseline) | realized 10-point match appendix (baseline) | focal PLAY |
|---|---|---|---|---|---|---|
| GPT-5.5 | copy | .045 [.013, .084] | .165 | .712 (.673) | .23 (.54) | .31 |
| GPT-5.5 | Opus 5 | .009 [.000, .022] | .133 | .744 (.662) | .19 (.31) | .21 |
| Opus 5 | copy | .011 [.000, .027] | .034 | .725 (.740) | .17 (.29) | .21 |
| Opus 5 | GPT-5.5 | .036 [.000, .081] | .055 | .730 (.779) | .19 (.31) | .23 |

**Regret** is same-q plug-in regret, ≥ 0, against the measured policies of partners who also received the appendix. Zero means a best response to that measured partner.

**Figure:** `fig_reciprocal_regret.{png,pdf}`. It shows baseline (open circles) vs appendix (open squares) per item, joined by lines. Filled markers are means; the appendix means carry 95% bootstrap intervals that resample policy and evaluation draws independently within items.

**What changed.**
- **Both models shifted heavily toward PASS.** PLAY rates fell to .21–.31, and on the two diffuse items (F05_m5, F12_m3) every draw passed.
- **Regret fell in all four cells,** mainly because passing is the best response to a partner who now also passes.
- **High-payoff coordination fell in every cell.** The clearest case is F27:
  - in the baseline, GPT played object 3 24/24 with its copy and matched perfectly;
  - under the appendix, GPT's policy is 19/24 PASS, so most of that coordination gain is gone.
  - F01 (an obvious odd-one-out) stayed mostly PLAY.
- **Net payoff:** GPT's realized payoff rose (.67 → .71 with a copy; .66 → .74 with Opus) because it stopped losing on unreciprocated plays. Opus's fell slightly (.74 → .73; .78 → .73).

**Forecasts** (eval-draw forecasts scored against independent policy draws).
- **Accuracy:** mean TVD for own forecasts was GPT .14–.17 and Opus .29–.34; for partner forecasts, .18–.34.
- **Systematic bias:** forecasts put too little weight on PASS where every draw actually passed. For example, Opus forecast PASS ≈ .46–.50 on F27, yet measured PASS was 1.00.
- **Own vs partner forecasts are nearly identical** within a model and condition. They look like projection, not a distinct model of the partner.
- **EV consistency is near perfect:** stated expected points equal 10 × the stated partner probability, and decisions are best responses to the model's own stated forecasts (BR-consistency .99–1.00).
- **Threshold anchoring:** many explanations cite a partner probability "just under 0.70". The appendix states this threshold explicitly, and it may anchor the forecasts.

## Interpretation (exploratory; no confirmatory or privileged-access claim)
- **What the appendix did:** it made both models more conservative and internally consistent, with decisions following their own stated forecasts. It lowered measured regret, but it also reduced high-payoff coordination.
- **Regret alone would overstate the benefit.** If everyone passes, regret is zero but no 10s are earned.
- **The improvement is not evidence of better own-policy knowledge.** Forecasts are endogenous to the same prompt, are miscalibrated (they underpredict PASS), and are largely projective. The intervention also changed the partners' policies, so the regret comparison with the baseline is between different games of play.
- **Overall: an inconclusive-to-negative result for the "superrational coordination" aim.** The appendix improves safety, not coordination.

## Limitations
- 4 items; 12 evaluation draws per cell; plug-in regret biased upward; zero-width bootstrap intervals in unanimous cells.
- The baseline comparison is exploratory and taken a day apart (models unchanged).
- Two invalid Opus replies reduce one cell's n.
- Expected-match and realized-match measures differ by construction; the realized measures are compared like for like in `realized_vs_baseline.csv`.

## Correction (2026-10-16, after manager review; results unchanged)
"Stated expected points equal 10 × the stated partner probability" held only at tolerance ±0.5, which `analyze_used.py` used.

| tolerance | consistent records (all 574 valid replies with expected points) |
|---|---|
| ≤ 0.01 | 566/574 (.986) |
| ≤ 0.05 | 567/574 (.988) |
| ≤ 0.1 | 573/574 (.998) |
| ≤ 0.5 | 574/574 (1.000) |

- All 8 strict-tolerance discrepancies are Opus replies. Most are rounding or transposition at the 0.1 scale (e.g. 0.7 vs 0.6); one is 7.4 vs 7.18 (F01 DIFFERENT policy rep 35).
- The manager independently found 4 discrepancies at its strict tolerance; the counts may differ because of the record set or the tolerance used.
- BR-consistency is unaffected.
