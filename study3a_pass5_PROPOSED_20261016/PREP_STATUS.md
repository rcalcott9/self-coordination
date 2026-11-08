# PASS = 5 adapted pilot — preparation status (2026-10-16). CANDIDATE: not frozen; no calls made.

- **Adaptation authorised:** "great. run the adapted pilot" (user, via ChatGPT manager `study3a-pass5-adapted-pilot-prep-01`).
- **Budget:** unresolved. Experiment spend so far: **$0**.

## Ready (offline-validated)
**Prompts** (`design/prompt_*_CANDIDATE.txt`): COPY `b5346bb0`, DIFFERENT `c12a5ed6`.
- Derived from the completed reciprocal pilot (b308cb54 / 5b087c1d) by exactly 6 asserted substitutions:
  - three game-text "7 points" → "5 points";
  - "PASS earns 7" → "PASS earns 5";
  - threshold "0.70" → "0.50";
  - schema `"PASS": 7` → `"PASS": 5`.
- A diff against the old prompt confirms nothing else changed.

**Jobs** (`design/jobs_CANDIDATE.jsonl`): the same 576 keys, roles (24 policy + 12 eval per cell), permutations and balanced order as the PASS = 7 pilot. Same items, models and settings.

**Scoring** (`code/scoring_pass.py`, PASS configurable; 8/8 checks):
- regret = (max(5, 10·max q) − [5·p_PASS + 10·Σ p_j·q_j])/10, the same-q plug-in, which is ≥ 0;
- joint payoff shortfall = (10 − mean dyadic payoff)/10, where 10 is the ideal coordination ceiling;
- matching rate.

**Analysis and figure** (`code/analyze_pass5.py`):
- Two panels: regret with 95% bootstrap CI, and joint shortfall. PASS = 7 is shown as open circles, PASS = 5 as filled squares.
- EV arithmetic is reported at explicit tolerances (0.01 / 0.1 / 0.5); BR-consistency is exact.
- The PASS = 7 pilot is scored identically from its raw data for the matched comparison. The academic-style figure was rendered on mock data.

**Runner** (`code/run_CANDIDATE.py`): it refuses any live dispatch, allowing only `--mock`/`--dry-run`, until a frozen manifest with a budget exists. The mock produced 576/576 records with 0 mapping errors.

## Cost (from the 576 observed costs of the identical-length PASS = 7 run)
| | value |
|---|---|
| Expected total | **$10.83** (95% range $10.76–10.91) |
| Token-limit hard bound | $68.84 (GPT $0.129, Opus $0.110 per call) |
| Prior cumulative Study 3 spend | $40.60191 |
| Remaining under the previous pilot cap | $9.16547 |
| Headroom under the $50 ceiling | $9.39809 |

## BLOCKING
The expected cost exceeds both headrooms (P ≈ 0). The run would stop at roughly 85% complete, and shrinking the sample or reallocating calls is not permitted.

To complete the frozen 576 calls, the plan needs **an experiment allocation of at least about $11.50** (expected $10.83 plus reservation margin; about $0.75 at concurrency 6, about $0.13 at concurrency 1). It also needs **the cumulative Study 3 ceiling raised to at least about $52.10**.

## Related correction (PASS = 7 pilot)
EV arithmetic consistency is 566/574 (.986) at ≤ 0.01, 573/574 at ≤ 0.1, and 574/574 at ≤ 0.5; all 8 strict-tolerance discrepancies are Opus replies. A note has been appended to that pilot's REPORT.md.
