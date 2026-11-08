# Study 1b: Amendment 1 (frozen before screening)

Date: 2026-10-07. This amends `STUDY1B_FINAL_DESIGN.md`; that document's sha256, `e51b691a…`, is in `HASHES.txt`. The following are unchanged:
- prompts (`fd7987e7`, `9abd5f2b`, reference `d40ea45d`);
- selection rules and quotas;
- scoring draws (48 per model per array, balanced);
- response counts (8 per cell);
- the existing gates (preflight, parse rate ≥ .95, budget caps of $25 for screening and $40 for main).

## Changes

1. **Primary question.** When GPT-5.5 and Claude Opus 5 have different choice policies, does each predict itself more accurately than the other model predicts it?
2. **Primary sample.** The selected divergent arrays only: S1, S2_G and S2_O.
3. **Primary outcome.** The existing crossed contrast: the pooled self-minus-cross Brier advantage, averaged over primary-sample arrays.

   Δ_j = ½[(B̄_j,Opus→GPT + B̄_j,GPT→Opus) − (B̄_j,GPT→GPT + B̄_j,Opus→Opus)], with Δ > 0 meaning self is more accurate.

   - Test: two-sided sign-flip across arrays, α = .05.
   - 95% CI: array-level percentile bootstrap.
4. **Target-specific advantages** (Δ_GPT, Δ_Opus) on the primary sample are reported separately, with Holm correction across the two.
5. **Secondary analyses:**
   - shared-policy S3 arrays (Δ and target-specific advantages, descriptive);
   - continuous divergence moderation across all selected arrays (Δ_j on screening total variation distance);
   - stratum breakdowns.
6. **Power.** It will be recomputed for the actual primary sample size after selection, using the frozen assumptions (τ = .085 and .05, 8 responses per cell, 48 scoring draws). Any shortfall is reported as a limitation. No calls are added and collection is not delayed.
7. **Sign-flip p-values.** p = (k + 1)/(B + 1), where B = 10,000 is the number of **simulated sign-flip vectors** (not the number of arrays) and k is the number with |mean| ≥ the observed |mean|. A check of the Study 1 code (`analyze.py`) confirms it also divides by the number of simulated flips (k/B, B = 10,000).
8. **Implementation notes**, not design changes, to be added after screening and before the main freeze:
   - `run.py` and `freeze_main.py` gain stage handling for the existing preflight (6 calls) and parse-pilot (32 calls) gates.
   - The pilot uses 2 screened, non-selected arrays chosen by a seeded hash.
   - The `primary_test` text in `FROZEN_MAIN` is updated to this amendment.
   - These files are hashed into `FROZEN_MAIN`.
   - The screening run uses the code as hashed in `FROZEN_SCREEN`.
