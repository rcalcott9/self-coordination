# Policy-specific self-coordination

`2026-08-12` · **built and validated; NOT launched — awaiting approval**

## The question

Do LLMs know when their own policy can successfully coordinate with another
instance of itself, **above and beyond generic/public stimulus salience**?

The confound this design targets: a model may bet on coordination simply because a
stimulus *looks* easy or focal to any observer. The signature that rules that out —

> Two stimuli look similarly coordinable **to an external observer**, but the focal
> model has high self-self coordination on one and low on the other. The focal model
> should be more willing to bet on the former.

## Structure

| stage | what it measures | n | calls |
|---|---|---|---|
| **A** ground truth | fresh self-play coordination on the new model versions | 60 / model × stimulus | 1,800 |
| **B** auditor | `auditor_prediction` — an external **model's** prediction of the focal model's self-coordination reliability | 30 / focal × stimulus | 900 |
| **B** salience | `generic_salience` — how focal the stimulus looks from public structure alone, asked about a *generic* player | 30 / rater × stimulus | 900 |
| **C** betting | focal model chooses ATTEMPT (10 / 0) vs SAFE (guaranteed) | 30 / model × stimulus × payoff | ~2,400 |

Stages A and B run first; the candidate-pair table they produce gates Stage C.

### The two public controls are not the same thing

`auditor_prediction` is **not** a pure public baseline. The auditor is a different
model with its own policy, and it may have learned model-specific information about
GPT or Claude — so it can partly anticipate the focal model's reliability for reasons
unavailable from stimulus structure alone. `generic_salience` names no model at all.

The strongest matched pair therefore differs substantially in **true self-match**
while differing little in **both** public measures.

## Models — resolved, not guessed

Queried from the provider model-list endpoints on 2026-08-12. The project's own
config contained only `gpt-5.4` / `claude-opus-4-8`; the `gpt-5.5` strings found in
the repo were comments and figure titles, not configuration.

| requested | resolved API id | pinned snapshot | settings |
|---|---|---|---|
| GPT-5.5 | `gpt-5.5` | `gpt-5.5-2026-04-23` | Responses API, `reasoning={effort: low, summary: auto}`, no temperature (rejected alongside reasoning), no seed exposed |
| Claude Opus 5 | `claude-opus-5` | — | `thinking={type: adaptive, display: summarized}`, `output_config={effort: low}`, `max_tokens=4000`, no temperature (400 on Opus 5), no seed exposed |

Both the requested name and the provider-returned id are written on **every row**
(`actor_model_id_requested` / `actor_model_id_returned`).

Settings are structurally identical to the Step 1/1c/2 series (`effort: low` on both
sides), so the only thing that changed from the confirmed battery is the model
version. `max_tokens` was raised 2000 → 4000 as truncation headroom — it is a cap,
not an estimand, and thinking tokens count against it on Opus 5.

## Stimulus battery — 15, all verified

Every name, identity coding, image path and classification is checked against
`step1c_output/targeted_confirmation_summary.csv` (the confirmed n=60 sample) at
manifest build time. A mismatch is a hard exit, never a silent substitution.

| category | stimuli | why |
|---|---|---|
| shared control (4) | `proto` `rot` `mirror` `noise` | ceiling, intermediate, structured-ambiguous, floor |
| **clean disparity** (4) | `d_dens_extreme` `s_density` `s_contrast` (GPT>Claude) · `b_spiral_cw` (Claude>GPT) | both models track FORM; one just coordinates more reliably |
| **fallback disparity** (7) | `a_chev_ud` `s_arrow` `s_convexity` `c_open_cplx` (GPT falls back) · `b_tee_ell` `c_contr_subtle` `d_texture` (Claude falls back) | one model tracks form; the other defaults to LEFT/RIGHT |

These two kinds are **never collapsed** — they are separate columns in the manifest,
a separate `pair_kind` in the matched-pair table, and a separate term in the
regression.

⚠️ **A finding worth flagging up front:** two of the four "shared controls" are
themselves fallback stimuli by the project's own criterion. `noise` has Claude
form-consistency **0.13** and `mirror` has GPT form-consistency **0.37** — both far
below the 0.80 clean bar. Their near-0.5 match rates are position defaults wearing a
post-hoc form rationale, not indifference. They are still useful controls, but they
cannot be described as "universally flat" in a write-up.

## Design decisions I made independently

1. **Stage A uses the canonical prompt byte-for-byte** (`sha8 3003ae1b`), not the
   spec's paraphrase. Stage A exists to re-measure coordination on *new model
   versions*, so model version must be the only thing that changed; a reworded
   prompt would confound version with prompt and break comparability with the
   confirmed battery. The hash is asserted at import — the run aborts if it drifts.
2. **Salience is model-agnostic and both models rate every stimulus.** It asks about
   "a generic capable AI player", so keying it to a focal model would contradict its
   own construct. Reported per rater *and* pooled.
3. **Auditor and salience are separate calls**, per the spec's default. Prior project
   practice only ever combined a probability with its own most-likely-choice — one
   construct, not two. Combining them would let one answer anchor the other.
4. **The betting prompt embeds `BASE` verbatim**, so the coordination task being bet
   on is exactly the task Stage A measured; only the decision layer is new.
5. **`CHOICE` is collected on ATTEMPT trials** (the spec's stated preference). It
   parses cleanly, and it yields coordination *conditional on attempting* — the thing
   an attempt is actually a bet about.

## Reuse — what is imported rather than rewritten

| from | what |
|---|---|
| `targeted_common.py` | `registry` `paths` `slot_identities` `cell_metrics` `unbiased_match` `plugin_match` `boot_draws` `pct_ci` `load_valid` — the fresh Stage-A numbers are computed by the **same code** that produced the confirmed battery |
| `step1_form_choice.py` | `BASE`, the canonical prompt, `parse_side`, the call shapes, the AB/BA job builder, the retry + `superseded_by_retry` CSV convention |
| `calibration_run.py` | the auditor third-person prompt rewrite, probability parsing with lenient fallback, the stage/rater/focal column layout |
| `confidence_calibration_probe.py` | the arm-3 safe-payoff opt-out design |

Nothing prior is modified and no prior output is overwritten.

## Pre-run validation — all green

`python3 code/test_psc.py` → **60+ checks, all pass** (no API calls, no cost):

- 15 stimuli present, both orientations, classifications match the confirmed data
- AB/BA recoding: LEFT maps to different identities under AB vs BA; an
  always-LEFT responder recodes to exactly 30/30
- parsers: choice / probability / salience / decision, including out-of-range
  values, lowercase markers, bare percentages, and ambiguous both-token strings
- retry + dedup: exactly one `included_in_analysis` row per planned trial, with
  both attempts retained in the raw log
- counterbalancing: exactly 30 AB / 30 BA in every cell, deterministic under seed
- **information symmetry**: the two auditor prompts are identical apart from the
  model name; no prompt leaks empirical rates, priors, or previous outputs
- prompt provenance: Stage A `sha8 == 3003ae1b`

Two real bugs were caught and fixed by these tests: `parse_decision` missed
lowercase `choice:` markers, and manifest booleans compared unequal depending on
whether the manifest was freshly built or round-tripped through CSV.

**Dry run** (`--dry-run`, all four stage runners + both analysis scripts + all four
figures) completes end to end: 60 + 60 + 60 + 160 simulated trials, retry path
exercised, regressions fit, bootstrap and permutation tests run, figures render.
All dry artifacts were then deleted so a real run cannot inherit simulated data.

## Cost and runtime

Input tokens measured exactly via Anthropic's free `count_tokens` endpoint (image
tokens dominate and are constant — every stimulus is 1040×520, well under the
2576px high-res cap; file size is irrelevant):

| call type | Claude input tokens |
|---|---|
| Stage A choice | 925 |
| Stage B auditor | 1,021 |
| Stage B salience | 936 |
| Stage C betting | 1,084 |

At Claude Opus 5's `$5 / $25` per MTok:

| phase | Claude calls | GPT calls | Claude cost |
|---|---|---|---|
| 1 — Stage A + B | 1,800 | 1,800 | **$22 – $31** |
| 2 — Stage C | 1,200 | 1,200 | **$16 – $22** |

(range spans 300–500 output tokens/call; adaptive thinking at `effort: low` bills
against output.)

⚠️ **GPT-5.5 pricing is not verified.** OpenAI exposes no pricing endpoint and I
would be guessing. Call and token volumes are identical to the Claude side, so if
GPT-5.5 is priced comparably the totals roughly double — **plan on $75–110 all-in,
and confirm GPT-5.5's rate before launching.**

Runtime at 8 workers: roughly **60 min** for phase 1, **40 min** for phase 2.

## How to run

```bash
cd code
python3 test_psc.py                              # 60+ checks, free
python3 stage_a_ground_truth.py --dry-run        # pipeline check, free

# --- phase 1 (paid) ---
python3 stage_a_ground_truth.py --n 60
python3 stage_b_perception.py --arm both --n 30
python3 analyze_stage_ab.py                      # -> matched_pairs.csv, then STOPS

# --- review matched_pairs.csv, set approved=True on the pairs you accept ---

# --- phase 2 (paid) ---
python3 stage_c_betting.py --n 30
python3 analyze_stage_c.py
python3 figures.py
```

`stage_c_betting.py` **refuses to run** unless `matched_pairs.csv` has rows marked
`approved=True` — verified by test.

## Candidate pairs — described and ranked, never selected

`analyze_stage_ab.py` enumerates every within-model stimulus pair and describes it.
It selects nothing: every row is written `approved=False`, and `approved` is the only
field Stage C, the Stage C analysis, and the figures read.

**Primary scale — standardized difference** `z_true`, `z_salience`, `z_auditor`
(difference ÷ battery SD, within focal model). Scale-free and comparable across the
three measures, so these drive both scores and the diagnostic.

**Reliability diagnostics only** — `t_true`, `t_salience`, `t_auditor`
(difference ÷ SE, SEs recovered *approximately* from bootstrap percentile intervals
and combined in quadrature). Descriptive. **No |t| cutoff — 1.96 or any other — is
used anywhere to decide whether two stimuli are matched.**

```
matching_score        = z_true − |z_salience|
matching_score_public = z_true − |z_salience| − |z_auditor|
```

Both are ranking aids only. `matching_score_public` is the stricter one, since a pair
matched on `generic_salience` but not on `auditor_prediction` is only partly matched.

**`pair_diagnostic`** — a qualitative label from two configurable descriptive
thresholds printed prominently at run time (`LARGE_TRUE_Z = 0.75`,
`SMALL_PUBLIC_Z = 0.35`). These are heuristics for surfacing candidates, not
inferential criteria:

| label | meaning |
|---|---|
| `ideal` | large true self-coordination difference with little difference in either public measure |
| `auditor_informed` | generic salience is matched, but an external model can partly anticipate the focal model's reliability difference |
| `salience_mismatch` | the stimuli differ visibly in apparent coordinability, so the pair does not cleanly isolate policy-specific knowledge |
| `non_diagnostic` | the true gap is below `LARGE_TRUE_Z` — too little self-coordination difference to test |

**Repeated stimuli are reported, not suppressed.** `stimulus_high_use_count` /
`stimulus_low_use_count` record how often each stimulus appears among the top-ranked
candidates, and the console warns when one stimulus takes more than 2 of the top 8 for
a focal model. Pairs are **not** de-duplicated automatically — pair independence and
diversity are decided manually at approval time.

## Payoff grid

Default `{3, 5, 7, 9}`. `analyze_stage_ab.py` computes the EV-neutral payoff span
(`10 × p`) for the selected pairs and prints an explicit recommendation with
rationale if that grid brackets the range poorly. Overriding it requires
`--safe-values`, which prints a warning naming the approval requirement.

## Interpretation discipline

A positive `true_self_match` coefficient surviving controls for auditor prediction
and generic salience supports:

> "Models exhibit **policy-specific knowledge** about when self-coordination is
> likely to succeed, beyond generic public focality."

It does **not** by itself support "introspection" — a learned self-model produces the
same signature. The stronger claim ("models *use* policy-specific self-knowledge to
selectively enter coordination games with copies") needs the matched-pair result:
selective betting **within** pairs matched on public coordinability. Generic self
preference, public salience, model stereotypes, and positional fallback are each
tested and reported separately, never folded into the headline.

## Layout

```
code/    psc_common.py  stage_a_ground_truth.py  stage_b_perception.py
         stage_c_betting.py  analyze_stage_ab.py  analyze_stage_c.py
         figures.py  test_psc.py  stimuli/ (frozen copies of all 30 images)
data/    raw CSV + JSONL per stage, derived tables
visualizations/   fig1 matching · fig2 primary · fig3 summary · figS1 supplementary
stimulus_manifest.csv    frozen, used by every stage
matched_pairs.csv        produced by analyze_stage_ab.py; gates Stage C
```
