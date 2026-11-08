# DATA DICTIONARY — Stage 1 (PROVISIONAL)

Lead-owned. Common definitions; teammates must use these names and formulas exactly.
Domain-specific field lists marked **TBD** pending T1/T2/T5.

## Identity and provenance (every row of every raw file)
| field | meaning |
|---|---|
| `run_id` | ledger key, matches RUN_LEDGER.csv |
| `domain` | `visual` \| `code` |
| `item_id` | canonical item identifier, unique within domain |
| `mechanism` | the convention type under test; kept SEPARATE from `family` so cosmetic variants are not counted as independent mechanisms |
| `family` | grouping of variants sharing construction |
| `checkpoint_requested` / `checkpoint_returned` | must match on every row; a mismatch stops the run |
| `prompt_hash` | sha256[:8] of the exact prompt text |
| `manifest_hash` | sha256 of the frozen stimulus/item manifest |
| `presentation_id` | permutation index (visual) or option-order seed (code) |
| `canonical_choice` | the model's choice mapped back to canonical option identity |
| `display_position` | the position chosen ON SCREEN, recorded separately and never used to score coordination |
| `parse_ok`, `transport_ok`, `attempt`, `superseded_by_retry` | integrity; all raw attempts preserved |

## Per model x item metrics
| metric | definition |
|---|---|
| `choice_distribution` | counts over canonical options |
| `modal_identity`, `modal_share` | most-chosen option and its share |
| `modal_margin` | modal_share - runner_up_share |
| `within_model_match` | unbiased dyadic self-match, sum_k n_k(n_k-1) / N(N-1) — probability two independent draws agree |
| `effective_support` | 1 / sum_i p_i^2 |
| `position_modal_share` | max share over display positions (chance = .25) |
| `form_consistency` | visual only: 1 - (max - min) of P(choose modal \| modal displayed at position p), over the 4 positions |

## Per model-pair x item metrics
| metric | definition |
|---|---|
| `modal_agreement` | 1 if the two modal identities match |
| `cross_model_match` | sum_i p_A(i) * p_B(i) — expected agreement of one draw each |
| `distribution_distance` | distance between the two full choice distributions (exact statistic TBD, T5) |
| `p_other_modal` | probability model A assigns to B's modal action |

## Convergence analyses (T5 to specify exactly)
Similarity by checkpoint vintage; within-family; cross-family; domain interaction; mechanism
interaction; **determinism-adjusted similarity**; item-level exceptions and reversals;
leave-one-family-out and leave-one-mechanism-out sensitivity.

**Mandatory separation:** any similarity increase must be decomposed into (a) models becoming
individually more deterministic and (b) models becoming more similar to each other. Reporting (a)
as convergence is the primary inferential error this study must avoid.

## Chance floors
Four options: modal share .25; cross-model match .25; within-model match .25.
