# Study 2 outline vs frozen data: evidence map (2026-10-13)

> **Update, later 2026-10-13:** the finalised Study 2 numbers and provenance are in `paper_assembly_20261010/docs/METHODS_RESULTS_DRAFT.md` (Table S2).
> - Corrections to this map: Qwen run B is primary; run A's interaction is −.064 in the draft's sign convention; Opus CIs depend on the bootstrap method; 13 → 11 relational items follow the pre-fixed retention rule.
> - Use the draft, not this map, for numbers.

- **Review only.** No calls and no new analyses. Every number is copied from frozen reports or from ledger v3 (`COMPLETION_LEDGER_20261009.md`).
- **Status labels:**
  - **complete:** data and report exist on disk and were read;
  - **unverified:** a component is mentioned somewhere but not documented in what was read;
  - **absent:** no data.

## Bottom line

The outline's Study 2 has **not been run**. It specifies partner-choice probabilities scored by Brier, on the *induced-policy* variants and items, under three partner mechanisms (copy, different policy, transformed copy), with relationship-only and policy-information conditions, external-predictor and identity-only baselines, and neutral identifiers.

The completed "Study 2" data answer a different question.
- **Main data:** PLAY/PASS willingness to bet under COPY vs DIFFERENT partner *labels*.
  - Policies are natural, or the step-316 implant; none is a counterbalanced induced variant.
  - DIFFERENT has no accuracy reference.
- **One frontier prediction study:** relational prediction. Its partner is a label only, its primary metric is TVD gating G (Brier is secondary), and it is null.
- **Closest match:** the crossed option-choice prediction studies (frontier 1b, Qwen crossed). They have partner-choice probabilities, Brier, and a real other-model predictor. They are currently Study 1 material, and they test self vs other *target*, not partner *mechanism* under a fixed predictor.

## Evidence table

All datasets were collected 2026-09-12/13 unless noted. "Agree." = copy-copy agreement, unbiased and independent-order unless noted. Only the Qwen crossed study and the frontier 1b study used two option orders (Qwen) or per-trial permutation (frontier) with order mapped to the underlying object.

**1. GPT PLAY/PASS 2×2**
- **Data:** `study_playpass_gpt`
- **Predictor / configuration:** `gpt-5.5-2026-04-23`, reasoning effort low or high. Items frozen `8ee3a56e`; prompts COPY `cbc2592c`, DIFF `60d134c1`.
- **Partner description and generation:**
  - COPY: "another independent instance of the same model as you, with the same training … presented the same way".
  - DIFF: "an AI model that was trained using a different training dataset and a different training algorithm from yours".
  - **Label only; no partner responses were generated.**
- **Items and calibration:** 30 VIS-FRAME-41 arrays, 4 options; HIGH = top 15 (.989), LOW = bottom 15 (.432) by GPT agreement, n = 48 per array.
- **Response:** PLAY/PASS, symmetric 10/0 judgement payoff.
- **Scoring reference:** COPY: agreement labels. DIFF: none, by design.
- **Samples:** 600 low + 300 high per partner = 1,800; 0 parse failures.
- **Frozen contrasts [95% CI]:**
  - HIGH−LOW, COPY low: +.380 [.220, .543], AUC .867. COPY high: +.447 [.273, .613].
  - Partner drop (COPY−DIFF): low +.140 [.093, .188]; high +.090 [.030, .153].
  - Partner × effort interaction: −.050 [−.118, .018], null.
- **Controls and sensitivities:**
  - Option-order permutation per trial (flat, χ² p .998); leave-one-item-out.
  - SENSITIVITY: same-presentation agreement relabels 0 items.
  - Voided spend-limit run quarantined.

**2. Opus PLAY/PASS 2×2**
- **Data:** `Stag/opus_playpass`
- **Predictor / configuration:**
  - `claude-opus-5`, adaptive thinking, effort low or high.
  - Plus one thinking-disabled COPY cell, kept separate (do not pool).
  - **Prompts carry no logged hash: "attributable but not hash-verified".**
- **Partner description and generation:**
  - COPY: "another independent instance of the same model as you".
  - DIFF: same wording as GPT.
  - Label only.
  - 3 DIFF cells with the wrong referent were excluded as contaminated.
- **Items and calibration:** the same pool; Opus's own top/bottom 15 (1.00 / .519), n = 48, measured with **thinking disabled**.
- **Response:** PLAY/PASS.
- **Scoring reference:** as for GPT.
- **Samples:** 4 × 600 = 2,400, plus 600 in the disabled cell.
- **Frozen contrasts [95% CI]:**
  - HIGH−LOW: COPY low +.190 [.080, .310]; COPY high +.387 [.227, .543]; DIFF low +.453 [.283, .620]; DIFF high +.493 [.340, .637]; disabled COPY +.300 [.100, .523].
  - Partner drop: low +.155 [.025, .292]; high +.133 [−.025, .288].
  - LOW−HIGH drop at low effort: +.263 [.057, .463].
- **Controls and sensitivities:**
  - Configuration arm (disabled vs adaptive).
  - SENSITIVITY: adaptive Stage A labels relabel 0 items.
  - SENSITIVITY: same-presentation LOW agreement .52 → .87; relabelling undefined (ties).

**3. Qwen PLAY/PASS 2×2, run A**
- **Data:** `Stag/qwen_study2_playpass/results/pp2x2_20260912_173541`
- **Predictor / configuration:** Qwen step-316 (`…/sampler_weights/step316`), thinking off, T = 1.0, max_tokens 90.
- **Partner description and generation:**
  - COPY: "another independent copy of you, the same fine-tuned model…", byte-identical to the Study 1 prompt.
  - DIFF: "the Qwen3.5-397B-A17B model without the preference fine-tuning you received…".
  - **Label only.**
- **Items and calibration:** 30 Study 1 scenarios (15 CLEAR / 15 NO-WEAK) × 5 fixed option pairs. Agreement comes from the Study 1 selection draws; **the same draws select and label the items.**
- **Response:** PLAY/PASS.
- **Scoring reference:** COPY: CLEAR/WEAK labels. DIFF: none.
- **Samples:** 1,200 decisions, 1,177 parsed; $0.67.
- **Frozen contrasts [95% CI]:**
  - COPY−DIFF: +.096 [.047, .146].
  - CLEAR−WEAK under COPY: +.164 [.070, .269].
  - Interaction: +.064 [−.036, .160], p .23 (not established).
- **Controls and sensitivities:** reported as a replication of the Study 1 COPY cells; scenario-clustered bootstrap.

**4. Qwen PLAY/PASS 2×2, run B, and post-hoc logits**
- **Data:**
  - `plunkett_qwen/results/s2_20260912_181428`
  - logits: `logit_s2_20260913_185259`
- **Predictor / configuration:** same checkpoint. The logits are teacher-forced logP(PLAY) − logP(PASS), conditioned on the saved reasoning; **post hoc**.
- **Partner description and generation:** prompt sha16 COPY `6b8026f5`, DIFF `a86a2da2`. Label only.
- **Items and calibration:** the same 30 scenarios.
- **Response:** PLAY/PASS sampled, plus logit margin.
- **Scoring reference:** as run A.
- **Samples:** 1,200 decisions, 1,186 parsed; 1,186 scored by logit ($3.10).
- **Frozen contrasts [95% CI]:**
  - Margin COPY−DIFF: +1.36 [1.06, 1.68], 29/30 items.
  - Interaction (WEAK shift − CLEAR shift): +.81 [.26, 1.38], p .011.
- **Controls and sensitivities:**
  - Leave-one-item-out (no sign change); partial r controlling for policy accuracy.
  - **UNVERIFIED:** whether run B is primary or a replication of A (both are cited by ledger v3 and both were read; no document found that ranks them), and whether the logit analysis was prespecified.

**5. Frontier relational prediction**
- **Data:** `study2_relational_prediction_20260912`
- **Predictor / configuration:**
  - GPT-5.5 at effort low; Opus 5 with adaptive thinking at effort low.
  - Items sha256 `9403d843…`, verified before launch.
- **Partner description and generation:**
  - COPY: "another independent instance of you, the same model, with the same policy".
  - DIFF: "{GPT-5.5 / Claude Opus 5}, a different model, developed separately". **Named, not neutral.**
  - **Label only.**
  - The partner's order is "independently randomized"; the prediction is anchored to the shape.
- **Items and calibration:**
  - 11 items selected for both models being stable and divergent (TVD ≥ .50).
  - Stage A n = 24, re-measured at n = 100.
  - **The n = 100 draws also serve as the scoring reference** (selection = scoring).
  - 13 items were proposed and 11 frozen; **why 2 were dropped is unverified.**
- **Response:** partner-choice probabilities (4 numbers).
- **Scoring reference:** SELF and OTHER from the n = 100 empirical distributions.
- **Samples:** 440 calls (11 × 2 × 2 × 10), 440 parsed; ≈ $6.70.
- **Frozen contrasts [95% CI]:**
  - **Primary G (TVD gating):** GPT +.021 [−.015, .046]; Opus −.000 [−.056, .064]. Null.
  - Brier, secondary: COPY→SELF GPT .190, Opus .382; DIFF→OTHER GPT .541, Opus .239. No CIs.
- **Controls and sensitivities:**
  - Family-clustered CI; F10 family collapsed (GPT +.002).
  - Exploratory trace coding (280 of 440 traces).
  - **Third-party baseline specified (≈ $4) and NOT run.**

**6. Qwen relational prediction**
- **Data:** `Stag/qwen_study2_relational`
- **Predictor / configuration:** step-316, thinking off.
- **Partner description and generation:**
  - COPY = step-316.
  - DIFF = the untuned base, described truthfully.
  - Designed arms: LABEL_ONLY vs OBSERVED_EXAMPLES (6 example tasks with the partner's real responses).
- **Items and calibration:**
  - Base agreement measured: 500 pairs × 40 draws.
  - Frozen items: 79 DISAGREE / 113 AGREE candidates, then `items_frozen.json`.
- **Response:** partner-choice probability, designed.
- **Scoring reference:** COPY: `predict_20260911` (40 draws); base: as measured.
- **Samples:** **Prediction step NOT run** (never approved). Designed: 3,440 predictions, ≈ $1.1–8.7.
- **Frozen contrasts:** none.
- **Controls and sensitivities:** a base-observer control was designed.

**Adjacent: frontier 1b crossed object prediction (currently Study 1)**
- **Data:** `study1b_crossed_object_20261007` (low); `study1_highreason_20261009` (high)
- **Predictor / configuration:** GPT-5.5 and Opus 5, low and high reasoning.
- **Partner description and generation:** each model predicts itself and the other model, both **named targets**; third-person wording. **The targets' fresh choices are real responses.**
- **Items and calibration:** 10 arrays selected for cross-model divergence, plus S3 controls.
- **Response:** partner-choice probabilities.
- **Scoring reference:** fresh choices of the target.
- **Samples:** per ledger v3.
- **Frozen contrasts [95% CI]:**
  - Self advantage: low +.258 pooled (target-specific GPT +.216, Opus +.299); high +.235 [.127, .358], 10/10.
  - Controls ≈ 0.
- **Controls and sensitivities:** cross-model predictor; S3 controls.

**Adjacent: Qwen crossed option-choice prediction**
- **Data:** `Stag/qwen_crossed_prediction_20261009`
- **Predictor / configuration:** step-316 and the untuned base, both as predictor and as target; thinking off. FROZEN `2da6c591`.
- **Partner description and generation:** the target is named; the predictor is not told whether it is the target. Real fresh choices: 24 per model × item × order.
- **Items and calibration:** 10 DISAGREE + 10 AGREE relational items; 2 orders, mapped to the object.
- **Response:** partner-choice probabilities.
- **Scoring reference:** fresh scoring choices, **independent of selection**, scored in the same order the prediction was shown.
- **Samples:** 640 predictions (635 parsed) and 1,920 choices; $2.28.
- **Frozen contrasts [95% CI]:**
  - Pooled self advantage: +.575 [.377, .761], p .004.
  - **Controls +.072 [.048, .100], not zero.**
- **Controls and sensitivities:**
  - Cross-model predictor; predictor main effect −.018.
  - Only 5/10 items still meet the selection definition.

## Outline components: present or absent

| outline component | status | nearest existing evidence |
|---|---|---|
| Reuse of the calibrated induced-policy items and **model variants** (counterbalanced replicas) | **absent for Study 2** | V1/V2 continuation replicas exist (Study 1, outline version), but no partner prediction was collected on them. The reasoning-on follow-up is PLAY/PASS only and not started. |
| Elicited partner-choice probabilities | **partial** | Rows 5 and adjacent (natural policies; step-316 vs base). Not on induced variants. |
| Copy partner = independent reference-task response from the same model | **partial** | Rows 5, 1b and Qwen crossed score against real same-model draws. The PLAY/PASS rows have a label only. |
| Different-policy partner = response from a **differently trained variant** | **partial** | Qwen base vs step-316 (a real other variant; row 6 unrun; Qwen crossed done as a target). The frontier "different" partner is the other frontier family. None is a counterbalanced sibling variant. |
| **Transformed copy** (disclosed A↔B mapping) | **ABSENT** | None. No prompt, design or data found. |
| **Relationship-only vs policy-information** conditions | **ABSENT** | Every DIFF arm is relationship-only in effect (a label). Row 6 designed LABEL_ONLY vs OBSERVED_EXAMPLES (not run), and observed examples reveal item-level answers, which the outline's policy-information condition forbids. |
| Disclosed balanced partner pool | **ABSENT** | |
| Primary Brier for partner predictions with selective-transfer contrasts | **partial** | 1b and Qwen crossed (Brier self vs cross). Row 5 Brier is secondary, with no CI. |
| **External-predictor baseline** | **partial** | The cross-model predictor in 1b and Qwen crossed (the other model predicting the target). Study 1a auditor (agreement, not choices). Row 5 third-party baseline **specified, not run**. No neutral third model has predicted any target. |
| **Identity-only baseline** | **ABSENT** | No dedicated condition. A DIFF label-only arm is not a baseline for predicting a known policy. |
| Neutral partner identifiers | **ABSENT** | Partners are named ("GPT-5.5", "Claude Opus 5", "copy of you", "the base model"). |
| Counterbalanced action labels | **partial** | Option order is permuted or swapped in every row. PLAY/PASS response labels are not counterbalanced. A/B labels are not counterbalanced across replicas outside the V1/V2 training. |
| Partner-generation procedure explained without assuming different behaviour | **partial** | Qwen DIFF is described truthfully (base). Frontier DIFF wording is generic ("different training dataset…"). |

## Methods excerpt (existing data, as completed)

> **Study 2 (completed form): partner-conditioned reliability judgement and relational prediction.**
> - **PLAY/PASS.**
>   - Design: each model made the Study 1 PLAY/PASS reliability judgement on 30 of its own items: the 15 highest- and 15 lowest-agreement four-option visual arrays, with copy-copy agreement measured independently (n = 48 draws per array).
>   - Payoff: symmetric, 10 points for a correct judgement either way.
>   - Partner: the clause described either "another independent instance of the same model" (COPY) or "an AI model that was trained using a different training dataset and a different training algorithm" (DIFFERENT). Only that clause and its referent changed.
>   - Configurations: GPT-5.5 at reasoning effort low and high; Claude Opus 5 with adaptive thinking at effort low and high. A thinking-disabled Opus COPY cell matched to the label configuration is reported separately.
>   - Qwen step-316 (thinking off) made the same judgement on its 30 Study 1 scenarios. There the DIFFERENT partner was truthfully described as the base model it was fine-tuned from.
>   - Samples: 20 decisions per item per cell for frontier models (300 per cell at GPT high) and 1,200 decisions per Qwen run.
>   - Scoring: no partner responses were generated. Accuracy statistics are computed for COPY cells only; in DIFFERENT cells the copy-agreement labels are not ground truth, so they measure willingness to bet.
> - **Relational prediction.**
>   - GPT-5.5 and Opus 5 (effort low) gave probabilities that a partner (COPY, or the other named model) would pick each of four shapes. There were 11 arrays selected for both models' stability and divergence, and 10 repetitions per cell.
>   - Predictions were scored against each model's empirical distribution (n = 100).
>   - Primary outcome: gating G, the change in relative TVD distance to SELF vs OTHER between COPY and DIFFERENT.

## Results excerpt (frozen values)

> - **Partner label.** Every model played less often against a DIFFERENT partner:
>   - GPT-5.5: −.140 [.093, .188] at low effort and −.090 [.030, .153] at high;
>   - Opus 5: −.155 [.025, .292] and −.133 [−.025, .288];
>   - Qwen: −.096 [.047, .146].
> - **The HIGH−LOW separation survived the relabelling in every frontier cell:**
>   - GPT DIFF: +.453 low, +.533 high;
>   - Opus DIFF: +.453 low, +.493 high.
>   - The partner discount therefore shifted the whole function rather than removing stimulus sensitivity.
> - **Was the discount larger on LOW items?**
>   - For Opus at low effort, yes: +.263 [.057, .463].
>   - Elsewhere it was not established: GPT interaction +.073 [−.020, .167]; Qwen +.064 [−.036, .160]. Post-hoc Qwen logit margins gave +.81 [.26, 1.38] (exploratory).
> - **Relational prediction.**
>   - Neither model changed its predictions when the partner was relabelled: G = +.021 [−.015, .046] for GPT and −.000 [−.056, .064] for Opus.
>   - GPT predicted SELF-like distributions for every partner; Opus predicted OTHER-like distributions for every partner.
> - **Scope.** These data test sensitivity to a partner *label*. They do not test prediction of real partner responses under transformed or information-varied mechanisms, which the planned Study 2 requires.

## Gaps to close before the outline's Study 2 can be claimed (no cost estimate made here)

1. Partner-choice prediction on the V1/V2 induced variants (copy, sibling variant, transformed copy), scored by Brier against fresh reference-task draws.
2. Relationship-only (balanced disclosed pool) and policy-information (disposition text, no item answers) conditions.
3. A neutral third-model external predictor, and an identity-only baseline.
4. Neutral partner identifiers, and counterbalanced A/B labels across replicas.
