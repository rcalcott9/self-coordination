# E18 PILOT GATE — the design premise failed
2026-09-10. **Expansion spend $2.66 of $50.** No full-run call made.

## Collection

816 calls, 17 items × 4 boundary checkpoints × n=12, in 182 s at 4.5 calls/s.
**Zero parse failures. Zero transport failures. Zero retries. Zero checkpoint mismatches.**
Counterbalancing exact: every option at every label 3× in every cell, asserted before dispatch.

The per-endpoint pool scheduler worked. Stage 1's comparable stage lost 59 calls to connection
errors caused by 30 workers converging on one endpoint; capping concurrency at 4 per endpoint with
one independent pool each produced none.

## The screen

Thresholds and the selection rule were frozen to disk (`screen_rule.json`, sha8 `a97f7afc`) after
the run and **before any result was inspected**. Applied mechanically:

| outcome | n | items |
|---|---|---|
| **ceiling** (median modal share ≥ .95) | **12** | argorder_replace, bool_env, constants_home, dict_order, docstring, id_field, init_export, logger_var, migration_name, optional_type, predicate, span |
| near-random | 0 | — |
| order-sensitive | 0 | — |
| malformed | 0 | — |
| **survive** | **5** | acronym_case, enum_value, listkey, money, test_naming |

## The premise failed, and the number that says so

**Zero of 17 items are live at all four boundary checkpoints.** Three are live at 3 of 4; six at 2
of 4. The frozen max-min selection rule — keep the items that stay live at their *worst* checkpoint —
therefore has no item to reward: every candidate's minimum effective support is exactly 1.000.

The rule still returns an answer, because only 5 items survived the exclusions and 5 < 12, so all 5
are selected. **The frozen procedure yields 5 items, not the 10–12 targeted.** Under the stated
priority order that is the correct outcome: reduce item count rather than weaken the per-cell design.

## Why it failed — it is the checkpoints, not the items

| checkpoint | vintage | fully deterministic | median support |
|---|---|---|---|
| `gpt-4-turbo-2024-04-09` | 2024-04 | **5 / 17 (29%)** | **1.18** |
| `claude-opus-4-5-20251101` | 2025-11 | 13 / 17 (76%) | 1.000 |
| `gpt-5.5-2026-04-23` | 2026-04 | 14 / 17 (82%) | 1.000 |
| `claude-opus-5` | 2026-07 | 14 / 17 (82%) | 1.000 |

Only the 2024-04 checkpoint retains meaningful diffuseness. On loci selected specifically for
long-standing, documented, unresolved contestation, the three checkpoints from 2025-11 onward are
deterministic on roughly four fifths of them.

**This sharpens Stage 1's determinism result rather than repeating it.** Stage 1 showed determinism
rising with vintage. E18 shows the rise had largely *completed* by late 2025: the gap between
2025-11 and 2026-07 is small (76% → 82%), while the gap between 2024-04 and 2025-11 is enormous
(29% → 76%). The panel's usable diffuseness is concentrated in one checkpoint at one end.

## The control failed its prediction, informatively

`x_optional_type` was declared in the audit as a positive control on the selection principle — the
one locus whose split is *recent* (PEP 604, 2021), predicted to collapse at the new end and survive
at the old end.

**It collapsed at all four, unanimously.** All 12 trials at every checkpoint chose `str | None`,
including `gpt-4-turbo-2024-04-09`.

So the premise behind the whole battery — that contestation predating 2024-04 predicts liveness
across the ladder — is not supported. The 2024-04 model had already resolved a 2021 split, and the
loci that stayed live are not the ones age predicted. Long-standing contestation among *humans*
does not imply contestation in a *model's* policy.

## Recommendation

Do not spend the remaining $47.34 the same way. Three options:

1. **Run the 5 survivors at n=48 × 9 checkpoints — $8.18, ~10 min.** Cheap and the frozen procedure
   supports it. But each survivor already collapses at 1–2 of 4 boundary checkpoints, so much of the
   grid will be dead cells, and 5 items is thin for anything item-clustered.
2. **Stop the code expansion and report E18 as a null-result battery.** The finding — 12 of 17
   deliberately contested code loci at ceiling, zero live across the ladder — is a substantive result
   about the domain, and Class-B rejections are reportable evidence per the rubric. Costs $0 more.
3. **Redirect the budget to the visual domain**, where Stage 1 measured 33% of cells at support ≥ 1.5
   and the older checkpoints stay diffuse. $47 buys roughly 10 visual items at n=48 × 9.

**I recommend 1 + 2 together**: run the 5 survivors ($8.18) because it completes the frozen
procedure honestly and produces a usable if small battery, and report the ceiling rate as the
headline finding either way. That leaves ~$39 of the cap unspent and available.

I do **not** recommend relaxing the screen to reach 12 items. Loosening a frozen threshold after
seeing which items it excluded is the defect this whole procedure exists to prevent.
