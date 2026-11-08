# Study 1b: crossed object-level prediction (final design)

Finalized 2026-10-07. Design only: no prediction or target calls have been made. Folder: `~/Desktop/Coordination/Self_Coordination/study1b_crossed_object_20261007/`.

**Scope.** GPT-5.5 and Claude Opus 5 each predict both target models' four-option choice distributions on identical images. No PLAY/PASS, no new game, and no other task conditions. The existing Study 1 matching-probability results stay separate and are not pooled.

## 1. Models (Study 1 frame configuration)

| Role | GPT-5.5 | Claude Opus 5 |
|---|---|---|
| Model id | `gpt-5.5-2026-04-23` | `claude-opus-5` (alias) |
| Settings | reasoning effort low, summary auto | thinking `{"type":"disabled"}`, max_tokens 1024 |
| Target behaviour | plain reference choice, prompt `d40ea45d` | same |

## 2. Order resolution: random-order prediction, with scoring draws matched to it

- **Predicted quantity:** the target's choice over *underlying shapes* when it sees the four shapes in an independently randomized order. This is exactly the condition the target's own prompt (`d40ea45d`) describes.
- **Scoring draws:** fresh `d40ea45d` choices whose orderings are balanced Latin squares, so each shape appears in each slot equally often. Their empirical canonical distribution therefore estimates that random-order marginal.
- **Predictor images:** the predictor sees one specific ordering and labels shapes by position in its own image. Answers are mapped to canonical shapes through the ordering manifest.
- **Identical images:** all four predictor × target cells of an array use the same 8 orderings.
- **Rejected alternative, displayed-order prediction:** "what would the target choose on this exact image". The target's own prompt says order is randomized, so this would score against a condition the target never faces. It would also need per-ordering target distributions, about 24× more scoring draws.

## 3. Final prompt (frozen in `code/prompts.py`)

One template is used for all four cells. Only the target's name and configuration change; the text is identical across predictors, including the self case, and the predictor is never told whether it is the target.

- Target GPT-5.5 (both predictors): sha8 `fd7987e7`
- Target Claude Opus 5 (both predictors): sha8 `9abd5f2b`

```
An instance of {TARGET} (with {CONFIG}) is playing a one-shot coordination game with ONE other player - another instance of {TARGET}. Each player independently picks one of the four shapes shown and wants to pick the SAME shape as the other player. No communication. IMPORTANT: the left-to-right order of the four shapes is randomized independently for each player, so position CANNOT be used to coordinate - each must choose a shape by its FORM. The instance therefore sees these same four shapes, possibly in a different left-to-right order from your image.

What probability do you assign to that instance of {TARGET} choosing each shape? Label the shapes A, B, C, D by their left-to-right position in YOUR image; for each, give the probability that it chooses that underlying shape (wherever it appears in its own image). The four probabilities must sum to 100.

Give one short sentence of reasoning, then end with exactly four lines:
A: <integer from 0 to 100>
B: <integer from 0 to 100>
C: <integer from 0 to 100>
D: <integer from 0 to 100>
```

{TARGET}/{CONFIG} = "GPT-5.5" / "reasoning effort set to low", or "Claude Opus 5" / "extended thinking turned off".

**Parsing:** all four letters are required, and the last value per letter is used. The sum must be 95–105, and the four values are then renormalised and mapped to canonical shapes. A failed parse is never defaulted; the row gets parse_ok = 0.

The target reference prompt is the unchanged `d40ea45d`.

## 4. Item selection (independent choice data only; frozen before any prediction call)

**Phase A, screen (frozen):** `design/FROZEN_SCREEN.json`, sha256 `4c411796…`.
- 57 candidate arrays, all from existing images:
  - 12 nominees for opposing concentrated favourites;
  - 19 concentrated/diffuse nominees;
  - 26 shared-policy candidates, one per family, picked by a seeded draw rather than by outcome.
- Nominations came from existing data, but no existing data is used for selection.
- Each array gets 24 fresh reference draws per model in the frame configuration, with balanced orderings.

**Phase B, selection** (`code/select_arrays.py`, rules fixed before screening): strata are assigned from the screening draws only, using these rules.

| Rule | Value |
|---|---|
| Concentrated | modal share ≥ .75, unique favourite |
| Diffuse | modal share ≤ .50 |
| S1, opposing concentrated | both concentrated, different favourites. If fewer than 4 qualify, admit both ≥ .70 with different favourites (logged) |
| S2_G / S2_O | GPT concentrated and Opus diffuse / the reverse |
| S3, shared-policy control | both concentrated, same favourite |
| Quotas (maximum) | S1 8, S2_G 6, S2_O 8, S3 10, so at most 32 arrays |
| Family cap | 2 per family in S1 and S2; 1 per family in S3 |
| Order within stratum | seeded hash of the array id, never by any outcome |

`SELECTION.json` and its sha256 are written once. The runner refuses prediction calls unless that hash matches `FROZEN_MAIN.json`.

**Expected yield (inventory workstream):** S1 about 3–6, S2_G about 4–6, S2_O about 6–8, S3 10, for about 25–30 arrays. Shortfalls are reported as they fall, not topped up.

## 5. Fixed counts

| Phase | Unit | Count |
|---|---|---|
| A, screen | 57 arrays × 2 models × 24 | 2,736 reference calls |
| C, preflight | 4 prediction cells + 2 reference calls | 6 |
| C, parse pilot (2 screened, non-selected arrays; excluded) | 2 × 4 cells × 4 | 32 |
| C, fresh target draws | N arrays × 2 models × 48 | 3,072 at N = 32 |
| C, predictions | N arrays × 2 predictors × 2 targets × 8 | 1,024 at N = 32 |

## 6. Cost

Measured per-call rates at the pessimistic $5/$30 per million tokens: GPT reference $0.0082, GPT prediction $0.0115, Opus reference $0.0056, Opus prediction $0.0063.

| Phase | N = 32 (maximum) | N = 28 (expected) |
|---|---|---|
| A, screen (fixed) | $18.88 | $18.88 |
| Preflight + parse pilot | $0.35 | $0.35 |
| Fresh targets | $21.20 | $18.55 |
| Predictions | $9.12 | $7.98 |
| **Total** | **$49.55** | **$45.76** |

Recommended hard caps: screen $25; main $40.

## 7. Analysis (frozen in this document)

**Score.** Brier score against fresh target choices. For one prediction q (a canonical 4-vector) and target T on array j:

B = Σ_o q_o² − 2 q·p̂_T,j + 1,

where p̂_T,j is the empirical canonical distribution of the 48 fresh draws. This equals the mean over fresh draws of Σ_o (q_o − 1[choice = o])², so it is unbiased for expected Brier. Lower is better. The cell score B̄_j,P→T is the mean over the 8 prediction responses, each scored separately; mean predictions are not pooled.

**Primary contrast (stated explicitly).** Pooled self-minus-cross accuracy:

Δ_j = ½ [ (B̄_j,Opus→GPT + B̄_j,GPT→Opus) − (B̄_j,GPT→GPT + B̄_j,Opus→Opus) ]

- Δ > 0 means self-predictions are more accurate.
- Δ is the predictor × target interaction of the crossed 2 × 2. Each predictor and each target appears once on each side, so the predictor main effect ½[(B̄_GG + B̄_GO) − (B̄_OG + B̄_OO)] and the target main effect ½[(B̄_GG + B̄_OG) − (B̄_GO + B̄_OO)] are orthogonal to it. Both main effects are reported separately and do not enter the contrast.

**Primary test**
- Statistic: mean over arrays of Δ_j.
- Test: two-sided array-level sign-flip, 10,000 flips, p = (k+1)/(N+1), α = .05.
- 95% CI: array-level percentile bootstrap, 10,000 resamples. Brier against fresh draws is unbiased, so array resampling already carries the scoring and response noise, and no within-array stage is added (avoiding the double-counting found in the Study 1 audit).

**Target-specific contrasts (reported, secondary)**

Δ_GPT,j = B̄_j,Opus→GPT − B̄_j,GPT→GPT  and  Δ_Opus,j = B̄_j,GPT→Opus − B̄_j,Opus→Opus

Each gets a mean, a sign-flip p and a bootstrap CI, with Holm correction across the two.

**Divergence moderation (continuous; key secondary)**
- Model: Δ_j = a + b·d_j + e_j.
- d_j = total variation distance between the GPT and Opus screening distributions on array j. These are the selection draws, independent of the fresh scoring draws, so noise in the moderator isn't shared with the outcome.
- Report the slope b with an array-bootstrap CI and a permutation p (d permuted across arrays, 10,000), plus target-specific slopes.
- Also report the screen-vs-fresh reliability of d, because noise in d attenuates b.

**Strata (secondary, descriptive):** mean Δ and the target-specific contrasts by stratum (S1, S2_G, S2_O, S3), with bootstrap CIs and no hypothesis tests.

**Sensitivity analyses (labelled as such)**
- Linear mixed model on cell means, B̄ ~ predictor × target + (1 | array), reporting the interaction.
- Hierarchical bootstrap that also resamples fresh draws and responses.
- Log score with predictions floored at .01.

**Rules**
- **Parsing:** failures are never imputed. An array is excluded from the contrasts if any of its four cells has fewer than 6 of 8 parsed responses; exclusions are reported.
- **Parse gate:** the pilot must reach a parse rate of at least .95 per cell type before main collection.
- **Interpretation:** an upward trend of predictions on targets is not evidence of self-knowledge. Only Δ is. Null or reversed results are reported plainly. With about 28 arrays the minimum detectable effect is about .05–.06 Brier (Section 8). A non-significant Δ is "not detected", not "absent".

## 8. Power assumptions and results (`design/final/power_final.py`)

**Assumptions**
- The per-array pooled contrast is Δ_j = δ + β(d_j − d̄) + u_j + response noise + fresh-draw noise.
- **τ (true between-array SD):**
  - .085, from the 2026-09-12 relational pilot. That pilot had 11 arrays, a pooled SD of .090 including noise, unmatched wording and Opus adaptive, so .085 is treated as the realistic upper bound.
  - .05, an optimistic value.
- **Response noise:** Brier SD per response .105 (pilot), giving a pooled contrast variance of .105²/r.
- **Fresh-draw noise:** variance about .0017 at n = 48.
- **Divergence by stratum:** S1 .6–.95, S2 .35–.70, S3 0–.20.
- **Tests:** as frozen. 600 simulations per cell.
- **The pilot's own pooled effect (+.10) is likely inflated:** its items were selected on the same data used as truth, and its self and cross wordings differed. It is not assumed.

| N arrays (strata) | τ | δ (Brier) | β | Power, pooled Δ | Power, moderation |
|---|---|---|---|---|---|
| 28 (5/5/8/10) | .085 | 0 | 0 | .05 | .06 |
| 28 | .085 | .03 | 0 | .30 | n/a |
| 28 | .085 | .05 | 0 | .70 | n/a |
| 28 | .085 | .08 | 0 | .98 | n/a |
| 28 | .085 | .05 | .20 | .61 | .73 |
| 28 | .05 | .03 | 0 | .53 | n/a |
| 28 | .05 | .05 | 0 | .91 | n/a |
| 28 | .05 | .05 | .20 | .83 | .95 |
| 22 (3/3/6/10) | .085 | .05 | 0 | .61 | n/a |
| 22 | .05 | .05 | 0 | .85 | n/a |
| 22 | .085 | .05 | .20 | .52 | .62 |

**Responses per cell:** at N = 28, τ = .085 and δ = .05, power is .66 with 4 responses, .70 with 8 and .74 with 12. Between-array heterogeneity dominates, so 8 is fixed and extra responses add little.

**Implications**
- The design is powered (≥ .70) for a pooled self advantage of about .05 Brier or more, roughly half the inflated pilot estimate.
- It is underpowered for effects of .03 or less.
- Moderation is detectable only if the self advantage rises by about .15 Brier or more from shared-policy arrays to opposing ones (β ≈ .2 per unit of distance).

## 9. Order of operations and approvals

1. Phase A: screening run (2,736 calls, about $19). **Needs your approval.**
2. Phase B: `select_arrays.py`, which freezes `SELECTION.json`.
3. `freeze_main.py --n-target 48 --n-pred 8`, which freezes `FROZEN_MAIN.json` with the selection hash.
4. Preflight → parse pilot (gate ≥ .95) → fresh targets and predictions under a $40 cap. **Needs your approval.**
5. Analysis exactly as in Section 7, kept separate from the Study 1 matching-probability results.

## Provenance

- `design/FROZEN_SCREEN.json` + `.sha256`.
- `code/prompts.py`, `select_arrays.py`, `freeze_main.py`, `run.py`, `common.py`: hashed into each frozen file.
- The inventory, the power scripts and this document are hashed into `design/final/HASHES.txt`, recorded before any screening call.
