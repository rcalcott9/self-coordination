# Amendment 1: resume after the $150 cap (2026-10-09)

**Scope.** The only change is the budget. The original run stopped at the frozen global cap ($150) with $149.22 spent and 1,337 main jobs outstanding.

The outstanding jobs are:
- Study 1a: the 2 arrays F30_pairratio_m1 (152 jobs, not started) and F40_crossang_m1 (97 jobs, partial).
- Study 1b: the 10 S3 controls (1,088 jobs). For F29_arcdir_m1 and F32_tilt_m1 only predictions are outstanding, because their REF draws were collected in Study 1a.

**Authorised by the PI:** up to $35 of additional spend. The new global cap is $149.22 (spent at stop) + $35 = **$184.22**, including retries.

**Unchanged:** `design/FROZEN.json` (sha256 prefix 933aa87d), every code file and its frozen hash, settings, prompts, schedule, orderings, seeds, checkpoints, parsers, gates and exclusion rules.

**Mechanism.** `code/resume_amend1.py` loads the frozen `code/run.py` unmodified, wraps its `verify()` so the in-memory cap reads $184.22, and calls its `main()`. All hash checks still run. New rows carry `frozen_sha8 = 933aa87d`. Completed jobs are skipped by `job_id`, so no call is duplicated.

**Incomplete-run report preserved.** `RESULTS_incomplete_cap150.md`, plus `analysis/_incomplete_cap150/` (outputs and logs as of the cap stop).
