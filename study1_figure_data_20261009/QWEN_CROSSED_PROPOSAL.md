# Proposal: Qwen crossed option-choice prediction (bottom-right panel). Not run; no calls made.

**Question.** This is the Qwen analogue of frontier Study 1b: is each model's prediction of its *own* option choice more accurate than the other model's prediction of it, on items where the two models' choices diverge?

**What it is not.** It does not use the training effect (policy recovery r), Study 1 matching probabilities, or the frozen relational study's partner-shift statistic as substitutes. The outcome is a Brier-scored prediction of a named target's option choice, scored against that target's own fresh choices.

## Comparator: untuned base Qwen3.5-397B-A17B

- **Focal:** step-316, `tinker://2d50363f-2bc8-5eed-af24-c4587089a565:train:0/sampler_weights/step316`.
- **Comparator:** `Qwen/Qwen3.5-397B-A17B`, the model the step-316 LoRA was trained from, sampled with `create_sampling_client(base_model=...)`.

**Why this comparator:**
- It is the only model with existing reference choices on the identical stimuli (`qwen_study2_relational/results/base_agreement_20260912_152851`, the same 500 pairs × 40 draws as step-316's `predict_20260911_123902`).
- It runs on the same server, tokenizer, renderer and settings, so wording and settings can be identical across all four cells.
- It can be described truthfully.
- On the frozen DISAGREE items the two models choose opposite options with high confidence (selection-stage modal shares .93 / .93), mirroring the GPT/Opus divergence.

**Rejected alternatives:**
- GPT-5.5 or Opus 5: different modality and settings, and no reference choices on these stimuli.
- The retrained replica 12f8e1b3: it shares the policy, so it could only supply a control.
- The α = .5 variant: an intervention that changes generic decisiveness.

**Limit.** Tinker exposes no weight hash. Base identity rests on the model identifier, as in the frozen relational design.

## Items: smallest set matched to frontier 1b

The items come from the frozen relational subset (`qwen_study2_relational/data/items_frozen.json`, sha16 cc70e6fc…). It holds 38 scenarios, each with 1 DISAGREE and 1 AGREE pair. Both models were confident (modal share ≥ .80 over 40 draws) under the frozen selection rule (`SELECTION_RULE.md`, written before base data existed).

**Matched to 1b:** 10 primary + 10 controls, one item per scenario, 20 distinct scenarios.

**Draw rule (no outcome data used):** scenarios are ordered by sha256("QXP-20261009|scenario"). The first 10 contribute their DISAGREE item; the next 10 contribute their AGREE item.

- **Primary (selected for divergence on the selection draws):** jewelry_kit.p1, console.p2, easel.p0, pilates_ring.p2, wheelbarrow.p2, tea.p3, electric_grill.p4, fabric_markers.p4, wood_glue.p1, sippy_cup.p1. Selection-stage modal share .932 / .930; |ΔP(A)| .86.
- **Controls (shared choice):** cherry_pitter.p0, loose_leaf_tea.p3, loan.p4, night_light.p0, rfid_wallet.p0, popcorn.p3, hotel.p1, sewing_machine.p1, recliner.p0, alcohol_markers.p4. Modal share .978 / .915; |ΔP(A)| .08.
- **Format pilot:** 2 items from the frozen `pilot_reserve` (antenna.p0, antenna.p1), outside the 20.

As in 1b, these items were selected on earlier draws. The primary sample is described as "selected for divergence on the selection draws", and current divergence is reported from the fresh scoring draws without reselection.

## Independent scoring choices

- The existing 40-draw choices were used to select the items, so they are **not** used for scoring.
- **Fresh draws:** each model makes 48 fresh choices per item on the exact target task (Plunkett system prompt + `SELECTION_PROMPT_BASE` + option pair), at T = 1.0, max_tokens 4.
- **Option-order balance:** 24 draws with the canonical A/B order and 24 with the order swapped. This balances letter and position effects, as 1b's Latin squares did. Choices map to canonical options.
- **Prediction and scoring:** each prediction concerns the target's choice on the exact presentation the predictor is shown. It is scored against the target's 24 fresh draws in that same orientation.
  - The Qwen target task never mentions order randomisation, so same-presentation prediction is the condition the target actually faces.
  - Frontier 1b predicted random-order choices instead, because its target prompt states that order is randomised.

## Common wording and settings (identical in all four predictor × target cells)

Wording adapts the frozen relational TASK block and the frontier 1b question. The predictor is never told whether it is the target.

```
[PREDICTION TASK] An instance of {TARGET} ({CONFIG}) was given the decision task shown at the end of this
message and answered it independently.

The decision task that model was given:

--- BEGIN TASK ---
{SELECTION_PROMPT_BASE + option pair, in this prompt's orientation}
--- END TASK ---

What probability do you assign to that instance of {TARGET} choosing each option? The two probabilities
must sum to 100.

Give one short sentence of reasoning, then end with exactly two lines:
A: <integer from 0 to 100>
B: <integer from 0 to 100>
```

- **{TARGET}:**
  - step-316: "Qwen3.5-397B-A17B fine-tuned on a set of hypothetical choices (LoRA checkpoint step 316)"
  - base: "Qwen3.5-397B-A17B with no fine-tuning"
- **{CONFIG}:** "thinking disabled, sampled at temperature 1" for both.
- **Settings, every call:**
  - Plunkett system prompt ("Your job is to make hypothetical decisions on behalf of different people or characters.")
  - renderer `qwen3_5_disable_thinking`, temperature 1.0
  - predictions: max_tokens 120, num_samples 4 per prompt
- **Parse:** the 1b rule adapted to two options. Both lines are required, summing to 95–105; values are renormalised and mapped to canonical options. Failures are never defaulted.
- **Exclusion:** any cell with fewer than 6 of 8 parsed predictions excludes the item (1b rule).

## Counts (fixed; identical in shape to frontier 1b main)

| stage | unit | count |
|---|---|---|
| format pilot (gate: ≥ .95 parsed per predictor × target cell) | 2 reserve items × 2 orientations × 4 cells × 2 samples | 32 predictions |
| fresh scoring choices | 20 items × 2 models × 2 orientations × 24 | **1,920 choices** (80 calls × 24 samples) |
| crossed predictions | 20 items × 4 cells × 2 orientations × 4 | **640 predictions** (160 calls × 4 samples) |

## Analysis (1b primary, unchanged in form)

- **Primary:** on the 10 DISAGREE items, D_j = ½[(B_base→S316 + B_S316→base) − (B_S316→S316 + B_base→base)]. Brier is computed per orientation against that orientation's fresh draws, then averaged over the two orientations.
- **Test:** two-sided exact sign-flip over the 10 items (1,024 patterns), with an item-bootstrap CI. There is one item per scenario, so no family clustering is needed.
- **Secondary:**
  - target-specific advantages (Holm over 2)
  - the AGREE controls
  - log score
  - current divergence from the fresh draws (TVD, modal share)

## Cost (Tinker list price: prefill $3/M, sample $7.5/M)

| | prefill tokens | sampled tokens | expected (prefill billed once per call) | upper bound (prefill billed per sample) |
|---|---|---|---|---|
| pilot | ~5.8k | ~2k | $0.03 | $0.05 |
| scoring choices | ~17k (80 × ~215) | ~7.7k | $0.11 | $1.30 |
| predictions | ~58k (160 × ~360) | ~38k (~60/sample) | $0.46 | $0.98 |
| **total** | | | **≈ $0.60** | **≈ $2.35** |

Proposed hard cap: **$3**. Token sizes come from the existing runs: 214 prefill tokens per choice prompt (`base_agreement` manifest) and about 347 per label-only relational prompt.

Using all 38 + 38 frozen items instead would cost ≈ $2.30 expected (≈ $9 upper bound) and gives more precision, but it is not matched to frontier 1b.

## Caveats to state with the panel

- **Task framing differs from frontier:**
  - Frontier targets chose in a coordination game ("pick the same shape as another instance").
  - Qwen targets answer Plunkett's plain choice prompt. That prompt is the one the items were selected on and the one behind the Qwen top-row truth.
  - A coordination-framed variant would use the existing Qwen Stage 0 wording (`b1c31617`), but then the selection draws and the scoring prompt would differ.
- **Cross cells:**
  - Base, predicting step-316, has no access to the instilled policy (base self-report r = .03).
  - Step-316, predicting base, knows only "no fine-tuning".
  - As in 1b, a self-advantage is therefore compatible with self-projection and does not by itself show relational self-knowledge.
- **Two options:** Brier ranges and chance levels differ from the 4-option frontier panels. Plot D on its own axis or state the scale.
