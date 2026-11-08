# Study 3A follow-up v2 — PROPOSED (2026-10-15). Supersedes PROPOSAL_followup.md (kept unchanged).

Not authorised and not launched. Study 3A only; focal GPT-5.5. Evidence files: `verify_pooling.py` → `pooling_checks.{csv,txt}`.

## 1. Pooling evidence
**GPT settings and input are identical across all four GPT sources** (two_model main and low_ext, gpt_staghunt_pilot, 10-15 pilot).
- **Request shape:** one user message with input_text (prompt) then input_image (base64 PNG data URL). `reasoning={"effort":"low","summary":"auto"}`. No max_output_tokens, temperature, instructions or image-detail field.
- **Billed input tokens** are exactly 818 (COPY) and 813 (DIFFERENT) on every call: 740 game calls at low effort, plus high effort.
- **Returned model:** `gpt-5.5-2026-04-23` on every call.
- **The only difference:** the requested string. The archived runs used the alias `gpt-5.5`; the pilot used the pinned id. Both resolved to the same snapshot.
- **Unobservable:** client SDK versions in September.

**GPT in-game actions agree on every overlapping item × condition**, comparing all cells observed in two or more sources with no selection.
- 10 run-level and 15 sub-run/role comparisons; permutation p ≥ .17 in every one.
- Max pairwise TVD: .235 on F11_noise_m0 COPY across runs; .317 on F41_m2 COPY across five small groups.
- Power is limited: 9 of the 25 comparisons are unanimous in every group.
- Conclusion: pooling archived GPT draws with new ones is supported, with the caveat about power.

**Opus September vs October: pooling is not established.**
- Inputs are identical (1,015 input tokens on every DIFFERENT call in both months) and the returned name is `claude-opus-5`. But the alias is undated, so identical weights can't be verified.
- The only behavioural overlap is F01 DIFFERENT: 20/20 vs 36/36, both unanimous, so it can't reveal drift.
- **Recommendation:** recollect the 2 archived Opus policy cells (F05_orient_m1, F36_split_m0): 48 actions, ≈ $0.32. Keep the September draws as a reported comparison.

## 2. Revised design (all 19 retained items; no outcome-based selection)
| sample | items | per item | calls |
|---|---|---|---|
| GPT COPY partner policy (new, independent of evaluation) | 15 (the 4 pilot items already have 24) | 24 | 360 |
| Opus DIFFERENT partner policy (new) | 13 + 2 recollected | 24 | 360 |
| Opus DIFFERENT fresh partners (new) | 15 | 12 | 180 |
| **Total** | | | **900** (Opus 540, GPT 360) |

- **Evaluation** uses existing archived focal GPT draws: COPY 19–78 per item, DIFFERENT 19–39 per item.
- **COPY realized payoff** is computed over distinct pairs within the evaluation draws, which come from the same distribution.
- **Positions** are shuffled independently: each of the 24 permutations exactly once in every policy cell, and a seeded sample for fresh cells.
- **Prompts** are the archived `49e35910` / `8222a371`. No prediction calls.

## 3. Reported for every item (all 19 rows, none dropped)
- Historical label (provenance only) and its source.
- n sent, ok, invalid, refused and failed, per sample.
- **s = max_j q_COPY(PLAY j)**, continuous, from the policy sample. Reported with a Jeffreys Dirichlet(½) posterior 95% interval and **P(s > 0.7)**, the point where PLAY beats PASS (`scoring.strength`; checks pass).
  - Examples: 24/24 → s 1.00 [.80, .99], P = .999. 17/24 → .71 [.47, .83], P = .35. Pilot F41 COPY → .63 [.40, .76], P = .11.
- Full partner distributions (PASS, PLAY0–3) for COPY and DIFFERENT.
- BR; normalized regret (BR − V)/10 with CI, not clipped; realized payoff/10; match rate; focal PASS rate; partner PASS rate.

## 4. Cost and the hard cumulative stop rule
**Expected cost** (resampling 1,384 observed game-call costs): total $7.57 mean, $7.69 at the 95th percentile, $7.80 at the 99.9th.
- These figures assume future calls behave like past ones. The largest observed call ($0.0241 GPT, $0.0104 Opus) is **not** a ceiling.

**Hard per-call bounds** (from token limits, not from observation):
- Opus: max_tokens 4000 bounds output, which includes thinking. Bound = 1,022 × $5/M + 4,000 × $25/M = **$0.1051**.
- GPT: the archived settings have **no output cap**, so no finite per-call bound exists beyond the model's own output limit. A guaranteed stop rule needs a GPT `max_output_tokens`.
  - Proposed value: 4,000. The largest observed output is 667 tokens across 740 low-effort calls.
  - Bound = 818 × $5/M + 4,000 × $30/M = **$0.1241**.
  - This is a settings change from the archived runs (decision D2). A truncated reply would be logged as incomplete or invalid, never resampled.

**Stop rule (hard cumulative $20):**
1. At launch, recompute prior cumulative spend from the ledger and every Study 3 run log. Currently $4.7525. Remaining R = $20 − prior.
2. Before dispatching any call, reserve that call's **hard bound** (not its expected cost). Dispatch only if run actual spend + all outstanding reservations + this bound ≤ R.
3. On completion, release the reservation and add the actual cost from returned usage at the verified price. If usage is missing (error after possible billing), keep the full bound as spent.
4. Retries are new calls with their own reservation. Stop on 3 refusals, 5 consecutive failures, or any non-retryable 4xx.
5. Re-verify prices on the launch day; abort if any price is higher than the bounds assume.

Under this rule, spend cannot exceed $20 whatever the concurrency, given the token bounds. With 4 calls in flight, about $0.50 is reserved at a time, so an early stop is expected only if spend runs about twice the estimate. Without a GPT output cap the rule can't be guaranteed.

## 5. Unresolved decisions
1. **Opus pooling:** recollect the 48 actions (recommended, included in the 900), or pool the September draws.
2. **GPT output cap:** add `max_output_tokens` = 4000 so the $20 stop is guaranteed (recommended), or keep the archived uncapped setting and accept a stop rule that can't be guaranteed.
3. **The 0.7 threshold:** s and P(s > 0.7) are descriptive only. Confirm they are never used to select or relabel items.
4. **Regret normalization and companion measures:** approved in direction only; not frozen.
5. **Evaluation from archived GPT draws** (Sep/Oct) vs new focal draws. Supported by the GPT pooling evidence.
6. **DIFFERENT wording:** keep the generic archived description.
7. **Cap:** this plan uses the hard $20 cumulative cap; "up to $50" is not applied.
