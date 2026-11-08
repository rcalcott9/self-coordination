# T4 — Recommended checkpoint panel

No API call was made. Availability marked LIVE is backed by a call already made in this tree within
the last 3 days; everything else is **UNVERIFIED** and re-verification is requested in
`probe_requests.md` (14 calls, < $0.20).

## 1. Recommended panel — 10 checkpoints, 5 GPT + 5 Claude

| # | checkpoint (send this exact string) | family | vintage | stratum | availability |
|---|---|---|---|---|---|
| 1 | `gpt-4o-2024-05-13` | GPT | 2024-05 | G-SAMPLE | UNVERIFIED (last called 2026-08-14) |
| 2 | `gpt-4.1-2025-04-14` | GPT | 2025-04 | G-SAMPLE | UNVERIFIED (probe only, 2026-08-14) |
| 3 | `gpt-5-2025-08-07` | GPT | 2025-08 | G-REASON | UNVERIFIED (last called 2026-08-15) |
| 4 | `gpt-5.2-2025-12-11` | GPT | 2025-12 | G-REASON | UNVERIFIED (probe only, 2026-08-14) |
| 5 | `gpt-5.5-2026-04-23` | GPT | 2026-04 | G-REASON | **LIVE** (2026-09-06) |
| 6 | `claude-opus-4-5-20251101` | Claude | 2025-11 | C-SAMPLE | UNVERIFIED (last called 2026-08-15) |
| 7 | `claude-opus-4-6` | Claude | 2026-02 | C-ADAPTIVE | **LIVE** (2026-09-09) |
| 8 | `claude-opus-4-7` | Claude | 2026-04 | C-ADAPTIVE | **LIVE** (2026-09-09) |
| 9 | `claude-opus-4-8` | Claude | 2026-05 | C-ADAPTIVE | UNVERIFIED (last called 2026-08-16) |
| 10 | `claude-opus-5` | Claude | 2026-07 | C-ADAPTIVE | **LIVE** (2026-09-08) |

Why this set:

- **Meets and exceeds the ≥3 + ≥3 preference** without any budget strain (§3).
- **Every stratum has ≥2 members, and the two frontier strata have ≥3.** G-REASON has 3 points,
  C-ADAPTIVE has 4. A within-stratum vintage trend is therefore estimable *without* crossing a
  surface boundary — which is the only way the trend claim survives the pre-registered limitation in
  `generation_ladder_20260814/ladder_models.py`.
- **One family holds tier constant.** All five Claude checkpoints are Opus. Adding Sonnet 4.5 or
  Haiku 4.5 would give a cheaper, older Claude point but would confound tier with vintage; they are
  listed as extensions, not core.
- **Vintage spacing is roughly even**: GPT 2024-05 / 2025-04 / 2025-08 / 2025-12 / 2026-04; Claude
  2025-11 / 2026-02 / 2026-04 / 2026-05 / 2026-07. The GPT arm reaches further back; the Claude arm
  is denser at the frontier. That is a property of what is callable, not a design choice — it is
  survivorship bias (MASTER_DESIGN §8.7) and must be stated.
- **Pinned ids on the GPT side** so `checkpoint_returned == checkpoint_requested` is a real check
  (see `request_surface_analysis.md` §5). Do **not** send `gpt-5.5` / `gpt-5.4`.

**Nothing here was excluded for complicating a trend.** The two checkpoints excluded from the
*visual* panel are excluded on hard technical grounds only: `gpt-4-0613` has no image input (HTTP
400), and the remaining candidates are extensions rather than exclusions.

## 2. Extensions, in priority order

| ext | checkpoint | domain | why | added cost (18+18 items) |
|---|---|---|---|---|
| E1 | `gpt-4-0613` | **code only** | the only 2023 vintage available anywhere in the panel; text-only is exactly what the code domain needs | +$4.3 |
| E2 | `gpt-5.4-2026-03-05` and/or `gpt-5.1-2025-11-13` | both | densifies G-REASON to 4–5 points, matching C-ADAPTIVE's density | +$13.7 each |
| E3 | `claude-sonnet-4-5-20250929` | both | a second C-SAMPLE member — currently the C-SAMPLE trend rests on a single point | +$5.2 |
| E4 | `gpt-4o-2024-11-20` | both | within-family drift check at fixed generation | +$9.6 |
| E5 | `claude-haiku-4-5-20251001` | both | cheapest point in the panel; tier-confounded | +$1.7 |

E1 and E3 are the two I would actually take: E1 costs almost nothing and buys the widest vintage
span in the study; E3 fixes the one stratum that currently has n=1 members.

## 3. Cost

Assumptions are stated in full in `request_surface_analysis.md` §7. Sizing uses the **higher**
of the two contradictory GPT price assumptions in the tree ($5/$30 per MTok); the lower ($1.25/$10)
is shown as the upside.

Per item across the 10-model panel, at the frozen n=48:

| | per visual item | per code item |
|---|---|---|
| GPT arm (5 models) | $1.68 | $1.67 |
| Claude arm (5 models) | $1.25 | $1.03 |
| **total** | **$2.93** | **$2.72** |

| scenario | visual items | code items | collection | code pilot | retries ~2% | **total** | vs $135 |
|---|---|---|---|---|---|---|---|
| **recommended** | 18 | 18 | $101.7 | $3.5 | $2.0 | **$107.2** | $27.8 headroom |
| conservative | 16 | 16 | $90.4 | $3.5 | $1.8 | **$95.7** | $39.3 headroom |
| stretch | 20 | 20 | $113.0 | $3.5 | $2.3 | **$118.8** | $16.2 headroom |
| recommended, **low GPT price** | 18 | 18 | $59.0 | $2.0 | $1.2 | **$62.2** | $72.8 headroom |
| recommended **+ E1 + E3** | 18 | 18 | $111.2 | $3.5 | $2.2 | **$116.9** | $18.1 headroom |
| 3 GPT + 3 Claude (stated minimum) | 18 | 18 | $65.7 | $3.5 | $1.3 | **$70.5** | $64.5 headroom |

Code pilot line: 2 checkpoints × 12 candidate items × 24 draws ≈ 576 calls ≈ $3.5.

**Cost implication of each panel decision, stated singly** (18 visual + 18 code items, high GPT
price):

| decision | Δ cost |
|---|---|
| the recommended 5 + 5 | baseline **$107.2** |
| drop to 3 GPT + 3 Claude (`gpt-5`, `gpt-5.2`, `gpt-5.5`, Opus 4.6/4.7/5) | −$36.7 → $70.5 |
| add E1 (`gpt-4-0613`, code domain only) | +$4.3 |
| add E3 (`claude-sonnet-4-5-20250929`) | +$5.2 |
| add one E2 candidate (`gpt-5.4` or `gpt-5.1`) | +$13.7 |
| add **both** E2 candidates | +$27.5 → $134.7 — at the planned ceiling; take one, not two |
| add E4 (`gpt-4o-2024-11-20`) | +$9.6 |
| add E5 (`claude-haiku-4-5`) | +$1.7 |
| put Opus 4.5 on the `budget_tokens` surface instead of temperature | +$22 to +$27 (min budget is 1024 tokens, all billed as output) |
| add one visual item (all 10 models) | +$2.93 |
| add one code item (all 10 models) | +$2.72 |

Two things follow, and I want to state the first one carefully rather than flatteringly.

**Neither axis is free, and the panel is not the cheaper one per unit.** Cost is
models × items × 48 × price. At 10 models and 36 items, dropping one checkpoint saves $8–14 while
dropping one item saves $2.7–2.9 — one checkpoint is worth 3–5 items. So MASTER_DESIGN §6's
ordering (cut items before checkpoints) is a *scientific* judgement about what the study is for,
not an economy, and it costs more battery than the reverse would cost panel. It happens not to
matter here: **the full recommended design fits with $27.8 of headroom, so no cut is forced at
all.** The ordering only becomes live if the GPT price turns out to be the high figure *and* the
lead wants both E2 candidates.

**The GPT price uncertainty is worth more than any panel decision.** Resolving it moves the total by
~$45 — more than adding four checkpoints, and more than doubling the code battery. It is a
documentation lookup, not an API call (probe P5).

## 4. Reusable existing measurements (Gate-1 tradeoff #1)

Four-option chooser data at the frozen n=48 **already exists** for two panel members:

| checkpoint | existing 4-option coverage | file |
|---|---|---|
| `claude-opus-4-6` | 22 arrays × 48 draws (1056 calls) + 9 arrays × 72 (confirm) | `study4_relational_staghunt_20260908/opus46_discovery_20260909_145344/` |
| `claude-opus-4-7` | 22 arrays × 48 draws (1056 calls) | `study4_relational_staghunt_20260908/opus47_discovery_20260909_032813/` |
| `claude-opus-5`, `gpt-5.5-2026-04-23` | large, spread across `study2_4opt_20260830` and `study4` | multiple |

**Do not bank this.** Those 22 arrays are the Study-4 *frozen selected* set, chosen for a
GPT-focal/Claude-other relationship — precisely the selection-conditioned frame MASTER_DESIGN §8.1
forbids as a sampling frame, and T1 is charged with recommending a broad one. Reuse is legitimate
only for arrays that survive T1's frame independently, at the identical prompt (`sha8 d40ea45d`),
identical surface, and n=48. If, say, 6 arrays overlap, that saves roughly $3 — real but small. The
larger value is that it proves the visual pipeline runs end-to-end for 4.6 and 4.7 at n=48 and
gives the measured cost basis this whole estimate rests on.

Existing data for `gpt-4o-2024-05-13`, `gpt-5-2025-08-07`, `gpt-5.4`, `claude-opus-4-5-20251101`,
`claude-opus-4-8` is **binary (2-option) only** and cannot be reused — MASTER_DESIGN §8.8, "binary
results do not predict four-option results", demonstrated in this tree.

## 5. Conditions on the recommendation

1. **Availability.** 6 of 10 are UNVERIFIED. If a re-verification probe (P1) shows a retirement,
   substitute within stratum — `gpt-5.1-2025-11-13` for `gpt-5.2`, `gpt-4o-2024-11-20` for
   `gpt-4o-2024-05-13`, `claude-sonnet-4-5` for `claude-opus-4-5`. If `claude-opus-4-5` is gone,
   the C-SAMPLE stratum collapses to Sonnet 4.5 alone and the Claude arm becomes
   frontier-only — report that as survivorship bias, do not paper over it.
2. **Set `thinking` explicitly on every Claude call**, including on Opus 5 where it is the default.
   Omitting it makes 4.8 and 5 behaviourally different for a reason unrelated to vintage.
3. **Set `thinking.display` explicitly** — its default changed at 4.7.
4. **Send dated GPT ids.**
5. **Record `api_settings` and the stratum label on every raw row**, as `psc_common.py` already does.
6. **Fix `ask_gpt` to return `r.usage`** before collection, or the GPT half of
   `RUN_LEDGER.measured_cost_usd` cannot be filled in.
7. Token-count T2's actual code items before freezing the code-domain budget; the 450-token input
   figure is my estimate, not a measurement.
