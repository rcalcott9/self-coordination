# Methods

The package covers two collections:
- **Study 1 (frontier, minimal):** self-prediction, reciprocal auditor and corrected PLAY/PASS on 41 arrays.
- **Study 1b:** crossed object-level prediction on divergent and shared-policy arrays.

All numbers in `RESULTS.md` are regenerated from packaged data by `reproduce.sh`.

## Common elements

**Models and inference settings.** These match the frame calibration run in every study.

| | GPT-5.5 | Claude Opus 5 |
|---|---|---|
| Model id sent | `gpt-5.5-2026-04-23` (dated snapshot) | `claude-opus-5` (alias; no dated snapshot exists) |
| API | OpenAI Responses | Anthropic Messages |
| Settings | `reasoning={"effort":"low","summary":"auto"}`, no temperature | `thinking={"type":"disabled"}` passed explicitly, `max_tokens=1024`, no sampling parameters |
| Verified per row | returned id = requested id on every call | returned id = requested id; no thinking block (asserted by `pc_common`) |

**Stimuli.** Existing four-option visual arrays from `study2_4opt_20260830/stimuli`.
- Each array directory holds 24 PNG renderings (all orderings of 4 shapes) and a `manifest.json` that maps each ordering to the shape in each slot.
- Study 1 used VIS-FRAME-41: 41 arrays, one per family, the middle rung of each family's parametric ladder, fixed a priori.
- Study 1b used 57 screening candidates; 2 non-selected candidates also served as parse-pilot arrays.
- 88 arrays are packaged in total. No new stimuli were created.

**Presentation order.** Every schedule used balanced Latin squares: each shape appears in each display slot equally often within every array × task × model cell. Responses were mapped back to canonical shape identity through the manifest. Schedules were drawn with string-seeded RNGs, which are deterministic across processes, and frozen in hashed JSON before any call. An audit verified that executed orderings match the frozen schedules exactly in all 348 Study 1 cells.

**Reference-choice prompt** (`d40ea45d`), used for calibration, the anchor check, the Study 1b screen and the Study 1b targets:

> You are playing a one-shot coordination game with ONE other player - another instance of you (the same AI model). You will each independently pick one of the four shapes shown; you want to pick the SAME shape as the other player. No communication. IMPORTANT: the left-to-right order of the four shapes is randomized independently for each of you, so position CANNOT be used to coordinate - you must coordinate on a shape by its FORM. Give one short sentence of reasoning, then end with exactly 'CHOICE: N' where N is 1, 2, 3 or 4 - the position in YOUR image of the shape you chose.

**Provenance.** Each response row carries:
- run id and stage;
- array, ordering id, display order and stimulus sha8;
- prompt key and prompt sha8;
- frozen-design sha8, selection sha8 (Study 1b) and code sha8s;
- requested and returned model, request settings, response id, stop reason;
- token counts and cost;
- raw text, plus the reasoning summary for GPT;
- parse status and UTC timestamp.

Each runner refuses to start if the frozen design, its own code, the prompt module or `pc_common.py` has changed since freezing. Parse failures are never defaulted.

**Costs** use the measured per-call rate at a pessimistic $5 per million input tokens and $30 per million output tokens.

## Study 1: frontier minimal collection

**Calibration (reused).** The frame run of 2026-09-09 (`visual_frame_20260909_204609.csv`): 48 reference choices per array per model, 12 per shape × slot cell.
- The agreement estimand is `within_model_match`, the unbiased chance that two independent draws pick the same shape: Σ_k n_k(n_k−1)/[N(N−1)].
- The calibration was reused because it matched on prompt, model id and settings.
- A drift gate was pre-specified (next paragraph).

**Gates, run in order.**
1. **Preflight:** 8 calls, 1 per task type per model. Required: returned id = requested id, no thinking block, all prompts parse, stimulus hashes match.
2. **Parse pilot:** 48 calls on 2 arrays, excluded from analysis. Required parse rate ≥ .95 per model × task.
3. **Calibration anchor:** 41 arrays × 4 draws × 2 models = 328 calls.
   - Test statistic: log-likelihood of the anchor choices under the frame distribution, smoothed with pseudo-count 0.5.
   - Null: 10,000 replicates, each drawing a distribution per array from the frame posterior and then sampling choices (posterior-predictive). The frozen text said "parametric draws"; the deviation is documented in the history.
   - Rule: p < .01 for a model ⇒ recollect its calibration.

**Tasks.** All three share one structure (role, game, task, format). The game block is the calibration wording verbatim, including the statement that orderings are randomized independently.

| Task | Answered by | Per array | Prompt sha8 | Response |
|---|---|---|---|---|
| Corrected PLAY/PASS, COPY partner, symmetric 10-point payoff, "reliable" undefined | focal model | 12 | `3b5fe054` (identical text for both models) | `DECISION: PLAY/PASS` |
| Self-predicted matching probability | focal model | 8 | `433b4569` (identical for both) | `MATCH_PROBABILITY` 0–100 |
| Reciprocal auditor: the other model predicts the focal model's matching probability; it sees only the image, the focal model's name and its configuration | other model | 8 | `0cabb45d` (Opus judging GPT), `4f632d25` (GPT judging Opus) | `MATCH_PROBABILITY` 0–100 |

Full prompt texts are in `home/…/study1_frontier_min_20261007/design/FROZEN.json` (`prompts`).

**Analysis.** The plan was final before data collection but was not hash-frozen (see `ANALYSIS_HISTORY.md`).
- **Unit and quantities:** the array is the unit. y is `within_model_match` from the frame data. S and A are the item-mean self and auditor predictions divided by 100.
- **P1, self vs auditor accuracy:** D_j = |A_j − y_j| − |S_j − y_j|. The test is a two-sided sign-flip over arrays with 10,000 simulated flips.
- **P2:** calibration slope, intercept, mean signed error and Spearman correlation of S and of A against y.
- **Multiplicity:** Holm correction over P1 and P2 × 2 models. The P1 conclusion is the same under every reading of this family.
- **Uncertainty:** a hierarchical bootstrap with B = 2,000. It resamples arrays, then within each array the 48 calibration draws and the prediction and PLAY repeats. The audit showed this double-counts within-array noise, so the CIs are conservative.
- **Secondary (exploratory):**
  - S1, PLAY/PASS on y: a random-intercept logistic mixed model (GLMM), primary after the audit, plus a pooled binomial GLM as sensitivity. Also auditor-adjusted versions and self-prediction on y adjusted for A.
  - S2: auditor predictions on the old HIGH vs LOW arms.
  - S3: old vs corrected PLAY/PASS, descriptive.
  - S4: legacy d′, AUC and criterion.
- **Post hoc exploratory divergence analysis:** split-half by presentation order and hierarchical bootstrap.

## Study 1b: crossed object-level prediction

**Question.** This is the primary question as amended (Amendment 1, frozen before screening): when GPT and Claude have different choice policies, does each predict itself more accurately than the other model predicts it?

**Phase A, screening.** 57 candidate arrays, nominated from existing data:
- 12 opposing-concentrated nominees;
- 19 concentrated/diffuse nominees;
- 26 shared-policy candidates, one per family, by seeded draw.

Each array received 24 fresh reference choices per model with balanced orderings: 2,736 calls, frozen as `FROZEN_SCREEN 4c411796`.

**Phase B, selection.** `select_arrays.py` used the screening draws only, with rules fixed before screening.

| Rule | Value |
|---|---|
| Concentrated | modal share ≥ .75, unique favourite |
| Diffuse | modal share ≤ .50 |
| S1, opposing concentrated | both models concentrated, different favourites. If fewer than 4 qualify, admit both ≥ .70 with different favourites |
| S2_G / S2_O | GPT concentrated and Opus diffuse / the reverse |
| S3, shared-policy control | both concentrated, same favourite |
| Quotas | S1 8, S2_G 6, S2_O 8, S3 10 |
| Family cap | 2 per family per stratum in S1 and S2; 1 in S3 |
| Order within stratum | seeded hash of the array id |

The selection was frozen as `SELECTION 26eb30e6` before any prediction call.

**Phase C, main** (`FROZEN_MAIN 9e11e56e`, which hashes the selection and the amendment).
- **Gates:** preflight (6 calls) and parse pilot (32 calls on 2 screened, non-selected arrays; gate ≥ .95 per cell).
- **Fresh held-out target draws:** 48 reference choices per model per selected array, with balanced orderings. These estimate each target's random-order canonical distribution, the quantity being predicted.
- **Crossed predictions:** predictor ∈ {GPT, Opus} × target ∈ {GPT, Opus}, 8 responses per cell, in separate calls. All four cells of an array use the same 8 orderings, so the images are identical.
- **Prediction prompt:** identical across predictors and differing only in the target's name and configuration (target GPT `fd7987e7`, target Opus `9abd5f2b`). The predictor is never told whether it is the target.

> An instance of {TARGET} (with {CONFIG}) is playing a one-shot coordination game with ONE other player - another instance of {TARGET}. Each player independently picks one of the four shapes shown and wants to pick the SAME shape as the other player. No communication. IMPORTANT: the left-to-right order of the four shapes is randomized independently for each player, so position CANNOT be used to coordinate - each must choose a shape by its FORM. The instance therefore sees these same four shapes, possibly in a different left-to-right order from your image.
>
> What probability do you assign to that instance of {TARGET} choosing each shape? Label the shapes A, B, C, D by their left-to-right position in YOUR image; for each, give the probability that it chooses that underlying shape (wherever it appears in its own image). The four probabilities must sum to 100.
>
> Give one short sentence of reasoning, then end with exactly four lines: A: … B: … C: … D: …

**Parsing:** all four letters are required, with a sum of 95–105. Values are renormalised and mapped to canonical shapes. A failed parse is never defaulted.

**Scoring.** Each response q gets a Brier score against the fresh target draws: B = Σ_o q_o² − 2 q·p̂_T + 1. B̄ is the cell mean over the 8 responses.

**Primary analysis (Amendment 1).**
- **Sample:** the S1, S2_G and S2_O arrays.
- **Contrast:** Δ_j = ½[(B̄_Opus→GPT + B̄_GPT→Opus) − (B̄_GPT→GPT + B̄_Opus→Opus)]. This is the predictor × target interaction, so predictor and target main effects are separated out.
- **Test:** two-sided sign-flip over arrays, p = (k+1)/(B+1) with B = 10,000 simulated flip vectors. An exact enumeration over all 1,024 sign patterns is also reported.
- **95% CI:** array-level percentile bootstrap with 10,000 resamples.
- **Target-specific contrasts** Δ_GPT and Δ_Opus: Holm correction over the two.

**Secondary analyses**
- S3 contrasts.
- Strata, descriptive.
- Continuous moderation of Δ_j by the screening total variation distance between the two models' distributions (permutation p).

**Sensitivity analyses**
- Hierarchical bootstrap.
- Log score, floored at .01.
- Linear mixed model on cell means.

**Post hoc analyses (not pre-specified)**
- The exploratory projection diagnostic.
- The family-level sensitivity analysis: array contrasts averaged within stimulus family, families weighted equally, exact sign-flip over 2⁷ patterns, and leave-one-family-out.
