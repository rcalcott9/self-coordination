# Minimal frontier Study 1 collection: design, counts, cost, analysis plan

Status: design and costing only. Nothing has been built, frozen or run, and no API calls have been made. Per-call costs below are measured from existing logs at the project's pessimistic rate ($5 per million input tokens, $30 per million output; `pc_common.cost`).

## Scope

- **Models:** GPT-5.5 and Opus 5.
- **Arrays:** all 41 existing VIS-FRAME-41 arrays, using the existing stimuli. No new stimuli, lotteries, salience ratings or robustness sweeps.
- **Three new tasks per model:**
  - corrected PLAY/PASS (COPY only);
  - self-predicted matching probability, collected in a separate call;
  - blinded reciprocal auditor predictions (GPT predicts Opus copies; Opus predicts GPT copies).
- **Calibration:** reuse the existing frame data (48 draws per array, same prompt `d40ea45d`, same settings, fully balanced orderings). It is recollected only if the drift check fails.
- **Old PLAY/PASS:** kept untouched in its current folders. The new study goes in its own folder and records sha256 hashes of the old files.

## Checkpoint and settings (from records; live verification is the preflight step)

| | GPT-5.5 | Opus 5 |
|---|---|---|
| Model id sent | `gpt-5.5-2026-04-23` (dated snapshot, not the alias) | `claude-opus-5` (alias only; no snapshot exists) |
| Settings | reasoning effort low, summary auto, no temperature | thinking `{"type":"disabled"}` passed explicitly, max_tokens 1024, no sampling params |
| Matches calibration? | yes | yes (frame used the same settings) |
| Last on record | 2026-09-16 | 2026-09-16 |
| Live check | preflight: returned id must equal requested; settings accepted | preflight: returned id equal; no thinking block in reply |
| Drift risk | low (dated snapshot) | weights behind the alias are invisible, so the anchor check below is needed |

## One common prompt structure (frozen and hashed)

Each prompt has four parts:
1. `[ROLE]` (one line naming whose choice is at stake);
2. `[GAME]`, a block identical in every task, taken from the calibration wording, including "the left-to-right order of the four shapes is randomized independently for each of you, so position CANNOT be used to coordinate";
3. `[TASK]`;
4. `[FORMAT]`.

- **PLAY/PASS:** the existing symmetric 10-point payoff; "reliable" is left undefined, as in the old prompt. The only change is the independent-randomization statement, and GPT and Opus now share identical wording. Output: `DECISION: PLAY|PASS`.
- **Self-prediction:** "What probability, 0–100, that you and the other instance pick the same underlying shape?" Output: `MATCH_PROBABILITY: <int>`. No choice is collected in the same call.
- **Auditor:** the `[GAME]` block in the third person about the named focal model and its configuration (for example, "Claude Opus 5, extended thinking off"). Target: the probability that two independent instances pick the same underlying shape. Output: `MATCH_PROBABILITY: <int>`. The auditor sees no focal answers, labels or statistics.

**Provenance logged per row:** run id, stage, task, array, ordering id and object order, stimulus sha8, prompt sha8, frozen-package sha8, `pc_common` sha8, request settings JSON, requested and returned model, response id, token usage, cost, raw text, reasoning summary (GPT), parse status and UTC timestamp.

## Counts

Orderings come from balanced Latin squares (each object in each slot equally often), generated with a fixed seed. The frame runner's per-process `hash()` seed is not reused.

| Stage | Per model | Both models | Purpose |
|---|---|---|---|
| Preflight | 4 (1 per task type) | 8 | liveness, returned id, settings, parse |
| Parse pilot | 24 (2 arrays × 4 orderings × 3 tasks) | 48 | parse rate ≥ .95 gate; excluded from analysis |
| Calibration anchor | 164 (41 × 4, one Latin square) | 328 | drift check against the frame data |
| Corrected PLAY/PASS | 492 (41 × 12) | 984 | |
| Self-prediction | 328 (41 × 8) | 656 | |
| Auditor (as auditor of the other model) | 328 (41 × 8) | 656 | |
| **Total** | **1,340** | **2,680** | |

## Cost

Measured per call (pessimistic rate):
- GPT reference choice $0.0082 (frame, 652 in / 164 out tokens); GPT PLAY/PASS $0.0114 (713 / 262).
- Opus reference choice $0.0056 (788 / 55); Opus PLAY/PASS with thinking disabled $0.0063 (870 / 65).
- Self-prediction and auditor calls are costed at the PLAY/PASS rate (similar input length, short output).

| Stage | GPT | Opus | Total |
|---|---|---|---|
| Preflight + pilot | $0.32 | $0.18 | $0.50 |
| Anchor | $1.34 | $0.92 | $2.26 |
| PLAY/PASS | $5.61 | $3.10 | $8.71 |
| Self-prediction | $3.74 | $2.07 | $5.81 |
| Auditor | $3.74 | $2.07 | $5.81 |
| **Planned total** | **$14.75** | **$8.34** | **$23.09** |
| Recommended hard cap (+25% for retries and longer outputs) | $18.50 | $10.50 | **$29.00** |

**Conditional:**
- If the anchor check fails for a model, recollect its full calibration (41 × 48 = 1,968 calls): GPT +$16.1, Opus +$11.0. The worst case with both failing is about $50 in total.
- Raising PLAY/PASS from 12 to 20 per array (to match the old 600-call density) adds 328 calls per model: +$3.74 GPT, +$2.07 Opus.

The old PLAY/PASS data costs nothing extra; it is reused as-is.

## Gates (in order; each stops the run on failure)

1. **Preflight:** returned id must equal requested, no thinking block for Opus, all 3 new prompts parse.
2. **Pilot:** parse rate must be at least .95 per model × task, with no default values for failed parses.
3. **Anchor drift check:** compute the log-likelihood of the 164 anchor choices under the frame distribution (smoothed with a pseudo-count of 0.5). The null distribution comes from 10,000 simulated anchor samples drawn from the frame. If p < .01, frame calibration is not reused for that model: recollect 48 draws per array, and only then run the main tasks.
4. **Main collection:** run the three tasks interleaved across models and arrays, under a hard budget cap.

## Analysis plan

**Basics**
- **Unit of analysis:** the array. GPT and Claude (Opus 5) are analysed separately.
- **Actual matching probability (y):** `within_model_match` from the existing frame data, 48 draws per array. This is the independent-order quantity, and it is now the correct target for every task, because every new prompt states that orderings are shuffled independently.
- **Prediction terms:** self-prediction S is the item mean of the focal model's MATCH_PROBABILITY / 100; auditor prediction A is the item mean of the other model's MATCH_PROBABILITY / 100 about the focal model.
- **Uncertainty: a single hierarchical bootstrap** (2,000 resamples) is used throughout, so that pairing is preserved:
  1. resample the 41 arrays with replacement, keeping each array's y, S, A and PLAY data together;
  2. within each resampled array, resample the 48 calibration draws (recompute y), the self-prediction reps (recompute S), the auditor reps (recompute A) and the PLAY/PASS reps.

  Calibration uncertainty therefore enters every statistic and figure.
- **Parse failures:** never imputed. They are reported per model × task.

**Interpretation rule.** An upward trend of predictions on actual matching is not, by itself, evidence of privileged self-knowledge, because an outside auditor can produce the same trend from externally legible features of the display. The key comparison is self vs auditor accuracy on the same arrays. A null or reversed self-advantage is reported plainly, with the same prominence as a positive one.

**Primary**
1. **P1, self vs auditor accuracy (key test).**
   - Per array: D_i = |A_i − y_i| − |S_i − y_i|, where D > 0 means a self-prediction advantage.
   - Report mean D with its 95% bootstrap interval, and the number of arrays with D > 0, D = 0 and D < 0.
   - Two-sided array-level sign-flip permutation test (10,000 permutations).
   - The same absolute error is used throughout; no alternative loss sweep.
2. **P2, calibration of each predictor.** Separately for S and A against y:
   - calibration slope and intercept from the regression of prediction on y;
   - mean signed error (over- or underconfidence);
   - Spearman correlation.

   P2 describes the predictors. It is not evidence of self-knowledge without P1.

Holm correction applies across P1 and P2 × 2 models.

**Secondary**

3. **S1, corrected PLAY/PASS.**
   - Item-level P(PLAY) on y across all 41 arrays: mixed logistic model PLAY ~ y + (1 | array); report the slope, Spearman correlation and AUC.
   - Auditor-adjusted association: PLAY ~ y + A + (1 | array); report the partial coefficient for y with its bootstrap CI.
   - Self-prediction beyond the auditor: S ~ y + A, coefficient for y.

   These are labelled exploratory. Auditor predictability is a proxy for externally legible information, not a measure of salience.
4. **S2, old HIGH vs LOW sets.** Difference in A between the old HIGH and LOW items, with bootstrap CI and the item-level table. Exploratory.
5. **S3, old vs corrected PLAY/PASS.**
   - On the 30 old items: item-level change in P(PLAY), with the old data also re-scored against same-order agreement.
   - Descriptive only, labelled as a wording change.
   - Kept in its own table and figure, never overlaid on the corrected-data figures and never pooled.
6. **S4, legacy metrics on the corrected data.** d′, AUC and criterion on the old HIGH/LOW split, for comparability only. The Opus HIGH tie-break is reported as undocumented.

## Outcome figures

Every figure uses the academic house style (`plt.style.use("academic")`):
- Arial 9 pt, no in-axes titles, thin black axes with top and right spines removed, ticks outward, no gridlines.
- Thin capped error bars, not translucent bands.
- 5.5 × 3.2 in at 300 dpi, exported as both PDF and PNG.
- Series are distinguished by marker and linetype as well as colour, so every figure survives greyscale printing.
- n, the method and the CI definition go in the caption.

**Figure 1 (primary): calibration.**
- **Layout:** two panels, GPT (left) and Claude (right), with shared axes running 0–1.
- **Axes:** x = actual matching probability y; y = mean predicted matching probability.
- **Points:** two series per array. Self-prediction S is a filled circle in a dark tone; auditor prediction A is an open square in a mid tone. A thin light-grey segment connects S and A for the same array, so the pairing is visible.
- **Reference line:** y = x as a thin solid black line, labelled "accurate" in the caption.
- **Uncertainty:**
  - per-point 95% bootstrap intervals as thin, light, capped bars, horizontal for calibration uncertainty in y and vertical for prediction uncertainty, drawn underneath the markers;
  - one fitted calibration line per series (S solid, A dashed), with its 95% bootstrap band shown as thin dotted bound lines rather than a filled band.
- **Caption:** n arrays, reps per array, the bootstrap definition, and each series' calibration slope and intercept.

**Figure 2 (primary): paired error.**
- **Layout:** two panels, GPT and Claude.
- **Points:** one per array, D_i = |A_i − y_i| − |S_i − y_i|, with arrays ordered by D on the x-axis (rank) and D on the y-axis.
- **Uncertainty:** each point carries a thin capped 95% interval from the hierarchical bootstrap (calibration, self and auditor resampling).
- **Reference marks:**
  - a thin horizontal line at 0;
  - the mean paired difference as a dashed horizontal line;
  - its 95% interval (array-resampled with pairing preserved, calibration uncertainty included) as a thick-capped interval at the right margin.
- **Axis label:** "Self-prediction advantage (positive = self closer to actual)". A mean below zero is shown and captioned as an auditor advantage, not hidden or rescaled.

**Figure 3 (secondary): PLAY/PASS.**
- **Layout:** two panels, GPT and Claude.
- **Axes:** x = actual matching probability y; y = proportion choosing PLAY.
- **Points:** all 41 arrays, each with a thin capped Wilson 95% interval over the 12 reps.
- **Colour:** points are coloured by auditor-predicted matching probability A, using a perceptually uniform sequential map whose luminance increases monotonically (cividis), with a colourbar. Colour here shows a covariate; it does not carry a series.
- **Fit:** the fitted relationship is the marginal curve from PLAY ~ y + (1 | array), drawn as a solid line with dotted 95% bootstrap bounds.
- **Caption:** states that colour is descriptive only. The auditor-adjusted association (S1) is reported separately in a table, because colouring by A is not statistical control.
- **Separation:** old PLAY/PASS data does not appear in this figure. Old vs corrected (S3) gets its own descriptive figure and table.

## Decisions frozen unless you object

- PLAY/PASS is COPY only (DIFFERENT belongs to Study 2).
- "Reliable" stays undefined, which keeps the construct comparable with the old runs; the analysis is graded rather than threshold-based.
- The key test is self vs auditor accuracy (P1). PLAY/PASS is secondary.
- The auditor is told the focal configuration, and runs in its own frame configuration.
- 12 PLAY/PASS calls per array, 8 per array for self-prediction and the auditor.
- The anchor is run for both models, even though GPT is on a dated snapshot.

## To check before running

- No Python environment found yet has `dotenv`, `openai`, `anthropic` and `numpy` together. Confirm which interpreter the frame run used.
- Preflight is the only live verification of model ids and settings. The records stop on 2026-09-16.
