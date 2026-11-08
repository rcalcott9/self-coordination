# GPT-5.5-focal arm with an older Claude as OTHER — result

Frozen test set `design/FROZEN_22_ARRAY_MANIFEST.json` (sha256 `b4f67b37…`), frozen
before any older-Claude data was collected. Prompt `d40ea45d` unchanged throughout.
No green assigned. No existing data modified.

## VERDICT — target met

**7 confirmed GPT-5.5-focal arrays across 3 mechanisms**, with `claude-opus-4-6` as the
OTHER model. Target was ≥5. **All 9 locked predictions held** (unconstrained confirmation
mode = locked identity, 9/9).

This is the first time the Study 4 GPT direction has had more than a single array.

## The checkpoint ladder — and why 4.6, not 4.7 or 4.5

| checkpoint | surface | discovery result on the frozen 22 |
|---|---|---|
| `claude-opus-4-7` | adaptive thinking, effort low — same as GPT run | **0 asymmetric.** Picked the *same* canonical object as GPT on **22/22** arrays. 17 shared controls. |
| `claude-opus-4-6` | same | **9 asymmetric** across 4 mechanisms, 10 shared controls. Diverged on 2/22 modal objects and was position-sensitive on 7 more. |
| `claude-opus-4-5-20251101` | **incompatible** | `400 — adaptive thinking is not supported on this model`. Excluded on **comparability**, not availability: running it would need a different request surface than GPT and the other Claudes used. Not forced through with a substitute config. |

**The binary audit mispredicted this.** It forecast 4 asymmetric candidates for 4.7 and 7 for
4.6; 4.7 delivered **0**. Binary counts rank checkpoints; they do not forecast four-option
yield. That caveat was recorded in the audit before the spend and is now demonstrated.

## Confirmed arrays (n = 72 per model, 3 full permutation cycles)

`shr`/`FC` are for the **locked** GPT object; `ADV` = GPT COPY − GPT×Opus cross-match.

| array | mechanism | locked GPT object | shr | FC | ADV | Opus shr | Opus FC | subtype |
|---|---|---|---|---|---|---|---|---|
| `m3_mirror_v6` | mirror | `twinTrue` | 1.00 | 1.00 | **+0.792** | 0.35 | 0.44 | diffuse_identity |
| `m4_contour_v4` | line_contour | `closed1_lw6` | 0.97 | 0.94 | **+0.432** | 0.51 | 0.67 | diffuse_identity |
| `m6_sizerank_v0` | size_rank | `equal` | 0.93 | 0.83 | **+0.359** | 0.54 | 0.00 | weak_competing_identity |
| `m6_sizerank_v2` | size_rank | `equal` | 0.97 | 0.94 | **+0.328** | 0.62 | 0.00 | weak_competing_identity |
| `m4_contour_v1` | line_contour | `closed1_lw10` | 0.93 | 0.83 | **+0.306** | 0.60 | 0.50 | weak_competing_identity |
| `m6_sizerank_v6` | size_rank | `equal` | 1.00 | 1.00 | **+0.278** | 0.72 | 0.17 | weak_competing_identity |
| `m6_sizerank_v4` | size_rank | `equal` | 1.00 | 1.00 | **+0.264** | 0.74 | 0.17 | weak_competing_identity |

**Mechanisms:** {'mirror': 1, 'line_contour': 2, 'size_rank': 4}.

### The two failures

| array | shr | FC | ADV | why |
|---|---|---|---|---|
| `m1_nesting_v3` | 0.90 | **0.78** | +0.565 | GPT form consistency below .80 |
| `m3_mirror_v3` | 0.93 | **0.78** | +0.248 | GPT form consistency below .80 |

Both failed on **GPT's own** form consistency (.78, just under the bar), not on the Opus
side and not on advantage — `m1_nesting_v3` held a +0.565 advantage. That is the same
position-sensitivity that sank the earlier repair round, and it is a property of GPT on
those arrays.

## The confound check

The audit flagged the risk that a GPT-focal result is really "GPT treats an older model as
generically unreliable". Two facts argue against a uniform older-model penalty:

1. **Opus 4.6 is sharp on the controls and diffuse on the candidates.** On the 10 retained
   shared-policy arrays it sits at share 1.00 / FC 1.00; on the 9 candidates its FC runs
   0.00–0.58. A model that were simply noisy would be noisy on both.
2. **Opus 4.7 — one generation newer — agreed with GPT on 22/22.** So the effect is not
   monotone "older = worse"; it is checkpoint- and array-specific.

**Caveat, not resolved:** on 7 of the 9 candidates Opus 4.6 picks the *same* object as GPT,
just inconsistently. Identity-level non-transfer there comes from position sensitivity, not
a competing convention. Only `m3_mirror_v6` and `m1_nesting_v3` show a genuinely
different modal object. That is admissible under the agreed subtypes but should be stated
plainly in any write-up.

**Control-arm limitation:** the 10 shared controls span only **2 mechanisms**
(line_contour 6, noise_texture 4), short of the ≥3 the frozen spend gate required. The
Partner × Item Type interaction can be run, but its control arm is mechanism-narrow.

## Cost

| item | calls | cost |
|---|---|---|
| Opus 4.7 probe + discovery | 1,057 | $5.25 |
| Opus 4.6 probe + discovery | 1,057 | $4.73 |
| n=72 confirmation, both models | 1,296 | Claude side **$2.90 measured**; GPT side unmetered |
| | **3,410** | **≈$21–30** |

`s4_common.ask_gpt` does not return usage, so the GPT half of confirmation (648 calls) is
estimated, not measured. Under the $50 ceiling on any reasonable estimate.

## Integrity

Every stage: 100% transport, 100% parsed, 0 checkpoint mismatches, 0 duplicate job keys,
0 position-balance violations. Every canonical identity appeared in every screen position
exactly 12× per cell at discovery and 18× at confirmation.
