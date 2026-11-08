# T4 — Request surface analysis and compatibility strata

Written by T4 (model-surface-auditor). Evidence-only: **no API call was made.** Every claim below
is traced to a file in this tree or to the bundled `claude-api` skill reference. Where neither
supports a claim it is marked **UNVERIFIED** and a probe is proposed in `probe_requests.md`.

## 1. Evidence base

| source | what it establishes |
|---|---|
| `policy_specific_self_coordination_20260812_1401/ladder/probe/ladder_probe.json` | one live call per candidate on 2026-08-14: callable / vision / control surface / returned id / parses |
| `policy_specific_self_coordination_20260812_1401/code/ladder_probe.py` | the exact request shapes probed, and the primary/fallback logic |
| `study2_4opt_20260830/code/s4_common.py` | the frozen 4-option request surface actually used (`ask_gpt`, `ask_claude`) |
| `policy_specific_self_coordination_20260812_1401/code/psc_common.py` | the two-surface switch (`PSC_GPT_SURFACE`, `PSC_CLAUDE_SURFACE`) and the settings recorded per row |
| `generation_ladder_20260814/ladder_models.py` | the pre-registered statement that surfaces are NOT identical across the ladder |
| 57 CSV files carrying `actor_model_id_requested` / `..._returned` (≈150k rows) | aliasing and substitution evidence |
| `study4_relational_staghunt_20260908/*/metering.json` | **measured** token counts and dollar cost per 4-option image call, 2026-09-09 |
| `study4_relational_staghunt_20260908/probe_opus4{6,7}/probe_result.json` | availability of Opus 4.6 / 4.7 **today** |
| `monitored_schelling_20260905/data/{focal,monitor}.log` | measured token counts for **text-only** calls (the closest analogue to the code domain) |
| bundled `claude-api` skill (`shared/models.md`, thinking/effort table) | per-checkpoint parameter legality on the Anthropic side |

## 2. The headline finding

**There is no single request surface that spans all candidate checkpoints and means the same thing
on each.** This is stronger than "the surfaces differ": even the apparently neutral choice of
*omitting* the reasoning controls is not neutral.

- Omitting `reasoning` on GPT-5.x does not reproduce the paradigm's `effort: "low"` — it runs the
  provider default. Sending `temperature` instead returns **400** on every GPT-5.x checkpoint
  (`ladder_probe.py` docstring; `psc_common.py` comment; corroborated by every recorded
  `api_settings` value for gpt-5.x carrying `"temperature": null`).
- Omitting `thinking` on Claude means **thinking off** on Opus 4.6/4.7/4.8 but **adaptive thinking
  on** on Opus 5 (`claude-api` skill, Thinking & Effort table). So "omit the parameter" silently
  flips a behavioural variable exactly at the 4.8 → 5 boundary — the newest and most load-bearing
  segment of the vintage trend.

Consequence for Stage 1: strata are mandatory, and the stratum label must be a column in the raw
data, not a footnote in the report. The existing runners already do the right thing —
`psc_common.py` writes the full `api_settings` JSON on every row — and Stage 1 must keep that.

## 3. The strata

### Visual domain (image input required)

| stratum | members | request shape | notes |
|---|---|---|---|
| **G-SAMPLE** | `gpt-4-turbo-2024-04-09`, `gpt-4o-2024-05-13`, `gpt-4o-2024-11-20`, `gpt-4.1-2025-04-14` | Responses API, `temperature=1.0`, no `reasoning` | verified callable + parsing on 2026-08-14 |
| **G-REASON** | `gpt-5-2025-08-07`, `gpt-5.1-2025-11-13`, `gpt-5.2-2025-12-11`, `gpt-5.4-2026-03-05`, `gpt-5.5-2026-04-23` | Responses API, `reasoning={effort:"low", summary:"auto"}`, temperature rejected | verified on all five |
| **C-SAMPLE** | `claude-opus-4-5-20251101`, `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001` | Messages API, `temperature=1.0`, no `thinking`, no `output_config` | adaptive thinking returns **400 "adaptive thinking is not supported on this model"** — confirmed for 4.5 Opus *and* 4.5 Sonnet in `ladder_probe.json`, not assumed |
| **C-ADAPTIVE** | `claude-opus-4-6`, `claude-opus-4-7`, `claude-opus-4-8`, `claude-opus-5` | Messages API, `thinking={type:"adaptive", display:"summarized"}`, `output_config={effort:"low"}`, sampling params rejected | the current production surface |
| — excluded — | `gpt-4-0613` | HTTP 400: model does not support image inputs | see §6 |

### Code domain (text-only)

Identical strata, with one change: **`gpt-4-0613` becomes eligible.** Its only recorded failure is
the vision rejection; the model itself was reachable. That gives the code domain one GPT vintage
point (2023-06) that the visual domain cannot have — an asymmetry the analysis must not paper over
by silently using the same panel in both domains. Report the panels separately or restrict to the
intersection; do not let the code panel's extra point create an apparent domain difference.

### What the boundaries cost in comparability

| boundary | what is confounded with vintage |
|---|---|
| G-SAMPLE → G-REASON (2025-04 → 2025-08) | presence of a reasoning stage at all, plus loss of temperature control. Any discontinuity here **cannot** be attributed to training-era convergence. Pre-registered as such in `generation_ladder_20260814/ladder_models.py` §"PRE-REGISTERED LIMITATION". |
| C-SAMPLE → C-ADAPTIVE (2025-11 → 2026-02) | same, on the Claude side |
| within C-ADAPTIVE, 4.8 → 5 | **only if `thinking` is omitted.** Setting `thinking` explicitly on every call removes this. Stage 1 must set it explicitly. Also: `thinking.display` default changed from `"summarized"` (4.6) to `"omitted"` (4.7/4.8/5), so reasoning-trace availability differs by vintage unless `display` is set explicitly too — the existing runners already set it. |
| within C-ADAPTIVE, 4.6 → 4.7 | `budget_tokens` is accepted (deprecated) on 4.6 and rejected with 400 on 4.7+. Irrelevant if `budget_tokens` is never sent — and it never is in this tree. |

## 4. The largest common request surface

Everything that is genuinely common across all fourteen visual-domain candidates:

- Messages/Responses, **one user turn**, no system prompt, no assistant prefill.
- Content: one image block (base64 PNG) + one text block, image first — the order used in both
  `s4_common.ask_claude` and `ask_gpt`.
- Byte-identical prompt across checkpoints (`sha8 d40ea45d` for the 4-option Stage A prompt;
  asserted at import in `run_opus47.py`).
- Free-text response, **regex-parsed** `CHOICE: N`. No structured outputs anywhere in this tree
  (`grep` for `output_config.*format` / `response_format` / `json_schema`: zero hits). Keep it that
  way — structured-output support is uneven across the older checkpoints and adopting it would
  itself become a stratum boundary.
- A max-output cap large enough not to truncate (2000–4000 tokens in existing runs; no truncation
  observed).
- Parse failures recorded, never defaulted (`s4_common` returns `None`; the "J bug" note).

Everything that controls reasoning depth is **outside** the common surface. That is the whole
finding.

## 5. Aliasing and checkpoint-substitution risk

Across ~150k rows carrying both fields, `actor_model_id_returned` was never a *different model*
from what was requested. But the two families behave differently and the difference matters:

| requested | returned | rows | reading |
|---|---|---|---|
| `gpt-5.5` | `gpt-5.5-2026-04-23` | 37,027 | alias → dated snapshot. Substitution would be **visible**. |
| `gpt-5.4` | `gpt-5.4-2026-03-05` | 2,520 | same |
| `gpt-5-2025-08-07`, `gpt-4o-2024-05-13` | identical | 12,672 | pinned; self-certifying |
| `claude-opus-4-5-20251101` | identical | 15,836 | pinned dated id; self-certifying |
| `claude-opus-4-6 / -4-7 / -4-8 / -5` | **the alias itself** | 56,460 | see below |

**Asymmetry the DATA_DICTIONARY rule does not currently capture.** The rule
"`checkpoint_requested` / `checkpoint_returned` must match on every row" is a strong integrity
check on the GPT side *only if the dated id is sent* — and a **structurally weak** one on Claude
4.6+, because Anthropic publishes no dated snapshot id for those checkpoints (`shared/models.md`
Full ID column is empty for Opus 4.6/4.7/4.8/5). The response echoes the alias, so a weights change
behind the alias would satisfy the equality check and be invisible. Recommendations:

1. **Always send the dated GPT id**, never the alias — this is a free upgrade to the integrity
   check and costs nothing. (Existing runs sent the alias; that is why the "mismatches" above are
   benign rather than absent.)
2. Record the collection date per checkpoint in `RUN_LEDGER.csv` and state in the report that
   Claude 4.6+ identity is certified **to the alias, on that date**, not to a weights snapshot.
3. Do not treat `returned == requested` on Claude as evidence against substitution. It is not.

## 6. Two defects found in the existing tooling

- **`ladder_probe.py` vision detection is wrong.** On failure it sets
  `vision = not ("image" in low and "not supported" in low)`. The gpt-4-0613 error text is *"does
  not support image inputs"*, which contains `"image"` but not `"not supported"` — so the record
  reads `"vision": true` for the one model in the whole probe that demonstrably has no vision.
  Anyone reading `ladder_probe.json` at face value would put gpt-4-0613 in the visual panel.
- **GPT spend is unmeasurable with the current runner.** `s4_common.ask_gpt` returns
  `(text, reasoning, model)` and discards `r.usage`; `run_confirm_pair.py` says so explicitly in its
  own output ("gpt usage not exposed by ask_gpt") and meters only the Claude half. The single GPT
  token measurement in the tree is `replication_5_4_4_8/preflight/gpt_usage_probe.json` (803 in /
  68 out, 44 reasoning) — from the **binary** Stage A prompt, not the 4-option one. Returning
  `r.usage` from `ask_gpt` is a one-line change and is required if `RUN_LEDGER.measured_cost_usd`
  is to mean anything for the GPT half of Stage 1.

## 7. Cost model and per-call assumptions

**Stated assumptions, all of them.**

*Token counts.*

| call type | input | output | source |
|---|---|---|---|
| Claude, visual (4-option image, prompt `d40ea45d`, effort low + adaptive) | **794** / **737** | **42** / **32** | MEASURED — `opus47_discovery` 1044 calls, `opus46_discovery` 1056 calls |
| GPT, visual | ~803 (binary prompt) | 68, of which 44 reasoning | MEASURED once, **on the binary prompt**; the 4-option figure is UNMEASURED |
| GPT, text-only, 12 options, effort low | 201 | **256** | MEASURED — `monitored_schelling` focal, 2000 calls |
| Claude, text-only, 12 options, thinking implicit | 399 | 307 | MEASURED — `monitored_schelling` monitor, 2000 calls |

I therefore use **800 in / 45 out** for a Claude visual call, **800 in / 120 out** for a GPT visual
call, **450 in / 80 out** for a Claude code call and **450 in / 200 out** for a GPT code call. The
code-domain input figure (450) is an *estimate*: no code battery exists yet, and it assumes the
frozen instruction block (~130 tokens, as in `s4_common.BASE + CHOICE_FORMAT`) plus four short code
options. T2's actual items should be token-counted before Gate 1 sizing is finalised.

*Prices.*

- Claude Opus 4.6/4.7/4.8/5: **$5 / $25 per MTok — VERIFIED**, in the strongest available sense: the
  measured `metering.json` figures reproduce exactly (794 × 5e-6 + 42.2 × 25e-6 = $0.005025 =
  the recorded `per_call_usd`). Consistent with the `claude-api` skill's pricing table.
- Claude Opus 4.5: assumed same Opus-tier $5 / $25. **UNVERIFIED for that checkpoint.**
- Claude Sonnet 4.5 $3 / $15, Haiku 4.5 $1 / $5: **UNVERIFIED / partly inferred** (the skill table
  prices Sonnet 4.6 and Haiku 4.5; Sonnet 4.5 is not priced there).
- **GPT: NOT VERIFIED, and the tree contradicts itself.** Two different working assumptions for the
  *same* model (`gpt-5.5`) exist three days apart:
  `study4_relational_staghunt_20260908/code/run_confirm_pair.py:17` → `$1.25 / $10.00`;
  `monitored_schelling_20260905/code/ms_sample.py:24` → `$5.00 / $30.00`.
  The project README already flags this: *"GPT-5.5 pricing is not verified. OpenAI exposes no
  pricing endpoint and I would be guessing."* **I size the panel at the higher figure** and report
  the lower as the upside. This 3–4× spread is the largest single uncertainty in the Gate 1 budget
  and it cannot be resolved by an API call — only by reading the provider's pricing page or the
  org's billing dashboard.

*Resulting per-call estimates* (central; the CSV carries them per checkpoint):

| | visual call | code call |
|---|---|---|
| Claude Opus 4.6/4.7/4.8/5 | **$0.0051** | $0.0043 |
| Claude Opus 4.5, temperature surface | $0.0055 | $0.0045 |
| Claude Opus 4.5, `budget_tokens=1024` surface | **up to $0.031** | up to $0.031 |
| GPT-5.x @ $5/$30 (used for sizing) | **$0.0076** | $0.0083 |
| GPT-5.x @ $1.25/$10 (upside) | $0.0022 | $0.0026 |
| GPT-4o / 4.1 / 4-turbo @ $5/$30 (upper bound) | $0.0061 | $0.0050 |

At n=48 a cell costs **$0.25–$0.40**. Note the Opus 4.5 row: the minimum legal `budget_tokens` is
1024, so putting Opus 4.5 on a thinking surface can bill ~6× the adaptive-at-effort-low cost. That
is a genuine reason to keep 4.5 on the sampling surface — a cost reason, on top of the
comparability reason that the existing 4.5 data was collected that way.

## 8. What this means for the tradeoff order

MASTER_DESIGN §6 puts "reduce the checkpoint panel" **last**. The cost arithmetic does **not**
independently support that: cost is models × items × 48 × price, and at a ten-model, thirty-six-item
design one checkpoint costs $8–14 while one item costs $2.7–2.9, so a checkpoint is worth 3–5 items.
Cutting items first is therefore a scientific judgement about what Stage 1 is for, not the cheaper
move. I flag this only so the ordering is applied with open eyes; it does not bind here, because the
full recommended design fits inside $135 with headroom and **nothing in the budget forces the panel
below ten checkpoints.**
