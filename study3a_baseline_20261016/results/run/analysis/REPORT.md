# Study 3A baseline — regret against measured partners (2026-10-16)

- **Authorisation, verbatim** (user, via ChatGPT manager `study3a-baseline-execution-30usd-01`): "run exactly this experiment. i want a resulting plot that shows regret for each model, relative to an optimal (low regret) benchmark" and "your budget is $30" (read as the cumulative Study 3 cap).
- **Frozen design:** `design/FROZEN.json` (sha256 206095b9…).
- **Game:** PASS = 7 always; PLAY j = 10 only if the partner PLAYs j, else 0. Object positions shuffled independently on every call.
- **Sample:** 19 items × focal {GPT-5.5, Claude Opus 5} × {COPY = same-model partner; DIFFERENT = the actual other model}. Per (item, model, prompt) cell: 24 policy and 12 evaluation draws, roles disjoint.
- **Settings:** GPT `gpt-5.5-2026-04-23`, effort low, `max_output_tokens` 4000. Opus `claude-opus-5`, adaptive thinking (summarized), effort low, `max_tokens` 4000.
- **Prompts:** archived baseline prompts 49e35910 / 8222a371. No intervention.

## Run
- **2,592 / 2,592 new calls collected, all valid.** 0 invalid, 0 refusals, 0 API failures, 0 retries.
- **Reuse:** 144 historical draws (2026-10-15 Opus DIFFERENT on F01, F02_m2, F27, F41_m2; exact model, settings, prompt and stimuli; original roles kept). No GPT draw and no September draw was reused.
- **Collection path:**
  1. 8-call format check;
  2. main run at concurrency 6, which the budget rule stopped at 2,551 records;
  3. the remaining 41 frozen jobs resumed at concurrency 1 under the same rule.
- **Cost:** $25.0149 this run; **cumulative Study 3 spend $29.7674** of the $30 cap. Prices verified 2026-10-16.

## Primary result (figure `fig_baseline_regret.{png,pdf}`; equal item weights; all 19 items in every cell)
Regret = [max(7, 10·max_j q(PLAY j)) − (7·p(PASS) + 10·Σ_j p(PLAY j)·q(PLAY j))]/10. Here p is the focal model's evaluation draws and q is the actual partner's separate policy draws, including the partner's PASS rate. **0 = best response to the measured partner.**

| focal | partner | mean regret [95% CI] | items at 0 | focal PASS | expected payoff/10 | realized payoff/10 | realized match |
|---|---|---|---|---|---|---|---|
| GPT-5.5 | copy | **.123** [.099, .156] | 7/19 | .14 | .72 | .72 | .62 |
| GPT-5.5 | Opus 5 | **.201** [.174, .232] | 7/19 | .49 | .52 | .53 | .19 |
| Opus 5 | copy | **.042** [.027, .063] | 9/19 | .78 | .67 | .66 | .12 |
| Opus 5 | GPT-5.5 | **.032** [.021, .053] | 11/19 | .77 | .73 | .73 | .19 |

- **CI method:** percentile bootstrap that resamples policy and evaluation draws independently within items, with the items fixed.
- **Jeffreys Dirichlet(½) credible intervals** (labelled sensitivity) are higher: GPT .160–.227 / .226–.289; Opus .098–.155 / .082–.138. The prior puts mass on unobserved actions, which raises regret at n = 12/24. They are not intervals for the plug-in estimate.
- Per-item values, full action distributions and companion measures are in `per_item.csv`; aggregates are in `aggregate.csv`.

**Figure caption.** Normalized full-action best-response regret for each focal model, against an independent same-model partner (copy, circles) and against the actual other model (different, squares). Open markers are single items, 19 per group. Filled markers are equal-item means with 95% percentile bootstrap intervals; policy and evaluation draws are resampled independently within items, with the items fixed. The dashed line at 0 is a best response to the **measured** partner policy. Lower is better.

**Data provenance and coverage.**
- 2,592 new actions (2026-10-16) plus 144 historical Opus DIFFERENT actions (2026-10-15 pilot; exact model, settings, prompt and stimuli; F01, F02_m2, F27, F41_m2).
- Full coverage: every item × model × condition has 12 evaluation and 24 policy draws.

**Uncertainty caveat.**
- Zero regret means a best response to the measured q. It does not establish optimality against the population policy.
- The bootstrap cannot represent uncertainty in unanimous cells, and the plug-in maximum biases regret upward.
- The Jeffreys Dirichlet(½) sensitivity gives noticeably higher intervals (above) because of prior mass on unobserved actions at n = 12/24. The aggregate levels are therefore prior- and small-sample-sensitive. The model ordering (Opus lower than GPT) holds under both.

## Interpretation (baseline only)
- **Opus 5 plays close to a best response to its measured partners**, with low regret in both conditions. It does so mainly by passing (PASS ≈ .78). That is often the best response, because its partners often pass too. Opus's regret is concentrated where GPT reliably PLAYs one object but Opus passes (F27 .22, F10 .17, F09 .12).
- **GPT-5.5 has moderate regret, and more against Opus than against a copy.**
  - **Against Opus:** GPT keeps playing its preferred object while Opus mostly passes (F27 .53, F10 .53, F36 .50, F18 .45, F07/F09/F41_m2 ≈ .41).
  - **Against a copy:** its regret comes from items where its own policy is diffuse yet it still PLAYs (F05_m5 .34, F12_m3 .32, F12_m4 .30).
  - On strong items where its copy plays reliably, GPT has zero regret and the highest matching (.62).
- **Overall: a positive baseline for Opus** (near best response, with a safe-action profile and low matching). **A negative one for GPT**, which over-participates relative to its measured partners.
- This baseline does **not** test or show use of own-policy knowledge. COPY vs DIFFERENT changes the actual partner, its policy and its description together.
- The F27 pattern found earlier holds: Study 1 labelled it weak, yet GPT plays it 24/24 against a copy.

## Limitations
- Plug-in BR uses a maximum, so regret is biased upward at small n.
- Unanimous cells give zero-width bootstrap intervals, and 24/24 does not mean population certainty.
- Twelve evaluation draws per cell.
- Equal item weights over a fixed, non-random item set, so the results do not generalise beyond these 19 items.
- The October-15 Opus draws on 4 items are about one day older than the rest.
- The historical Study 3 benchmark B = max(7, 10ĉ) is preserved separately and not used here.
