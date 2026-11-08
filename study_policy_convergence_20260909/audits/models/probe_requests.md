# T4 — Probe requests (NOT executed)

**I made no API calls.** Every probe below is a request for lead approval. Each is written so it can
be run verbatim. Total: **14 calls, < $0.20** at the high GPT price assumption. All of them are
technical-compatibility calls on one already-frozen stimulus, not measurements of any estimand, so
none of them consume or contaminate a study cell.

Priority order: P1 → P6 → P2 → P3 → P4. P5 is not an API call at all and should be done first.

---

## P5 (do this first; **not an API call**) — resolve the GPT price

Two working assumptions for `gpt-5.5` contradict each other inside this tree:
`study4_relational_staghunt_20260908/code/run_confirm_pair.py:17` → `$1.25 / $10.00` per MTok;
`monitored_schelling_20260905/code/ms_sample.py:24` → `$5.00 / $30.00`. The project README already
records that GPT pricing was never verified. The gap is worth ~$42 on the Gate 1 total — more than
any panel decision. **No API call can resolve it** (the Responses API returns tokens, not dollars).
Resolve it from the provider's published pricing page or the organisation's billing dashboard, and
record the source and date in `DECISION_LOG.md`. Until then, size at $5/$30.

---

## P1 — availability re-verification sweep (10 calls, ~$0.07)

**Why.** 6 of the 10 recommended checkpoints have not been called since 2026-08-14/16. MASTER_DESIGN
§8.7 names survivorship bias as a threat; the honest response is to re-verify rather than assume.
A retirement discovered during collection would strand a partial panel mid-run.

**Exact call.** Run the existing, unmodified script — it is already written for precisely this:

```
cd Self_Coordination/policy_specific_self_coordination_20260812_1401/code
python3 ladder_probe.py
```

It issues one call per candidate (10 OpenAI + 6 Anthropic = 16; trim `OPENAI`/`ANTHROPIC` to the 10
unverified ids for a 10-call run), on the frozen `proto` AB stimulus with prompt `sha8 3003ae1b`,
and writes `ladder/probe/ladder_probe.json`. **It will overwrite the 2026-08-14 probe file** —
redirect `OUT` or copy the existing file aside first; that file is the primary evidence for this
whole audit.

**One patch required before running** (a real defect, see `request_surface_analysis.md` §6):

```python
# ladder_probe.py, in the except branch — current line is wrong
vision = not ("image" in low and "not supported" in low)
# gpt-4-0613's error is "does not support image inputs": contains "image",
# does NOT contain "not supported", so this records vision=true for the one
# model with no vision. Replace with:
vision = not ("image" in low and ("not support" in low or "not supported" in low))
```

**Decision rule.** Any candidate returning a 404 / model-not-found is replaced by its within-stratum
substitute (`panel_recommendation.md` §5.1), and the substitution is logged in `DECISION_LOG.md` as
survivorship, not as a design choice.

---

## P6 — GPT token usage on a real 4-option image item (1 call, ~$0.01)

**Why.** The only GPT token measurement in the tree
(`replication_5_4_4_8/preflight/gpt_usage_probe.json`, 803 in / 68 out) is from the **binary**
prompt. Every GPT figure in my cost model extrapolates from it. `s4_common.ask_gpt` discards
`r.usage`, so no production run has ever measured the GPT side. This single call removes the second-
largest uncertainty in the Gate 1 budget.

**Exact call.**

```python
import json, sys
sys.path.insert(0, "Self_Coordination/study2_4opt_20260830/code")
import s4_common as S
img = S.b64("<any frozen 4-option array>/perm00.png")
r = S.make_clients()["gpt"].responses.create(
    model="gpt-5.5-2026-04-23",
    reasoning={"effort": "low", "summary": "auto"},
    input=[{"role": "user", "content": [
        {"type": "input_text", "text": S.STAGE_A_PROMPT},
        {"type": "input_image", "image_url": f"data:image/png;base64,{img}"}]}])
print(json.dumps({"model": r.model, "usage": r.usage.model_dump()}, indent=2))
```

**Also fix, whether or not the probe runs:** make `ask_gpt` return `r.usage` alongside
`(text, reasoning, model)`, so `RUN_LEDGER.measured_cost_usd` can be filled for the GPT half.

---

## P2 — is Opus 4.6 a bridge across the C-SAMPLE / C-ADAPTIVE boundary? (1 call, ~$0.005)

**Why this is the highest-value methodological probe.** The Claude stratum boundary at 4.5 → 4.6 is
currently an *uncontrolled* confound with vintage. Opus 4.6 is the only Claude checkpoint documented
to accept **both** surfaces: adaptive thinking (verified live in `ladder_probe.json`) and ordinary
sampling parameters (`claude-api` skill, Thinking & Effort table — "Opus 4.6 / Sonnet 4.6 ...
Sampling: Allowed"). Never exercised in this tree. If it holds, Stage 1 can run **one** checkpoint
under **both** surfaces on the same items and *measure* how far the surface alone moves the policy —
converting the stratum boundary from an untestable caveat into a reported quantity. If it fails,
that is equally worth knowing and the caveat stands as pre-registered.

**Exact call.**

```python
import anthropic
r = anthropic.Anthropic().messages.create(
    model="claude-opus-4-6", max_tokens=2000, temperature=1.0,
    messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": IMG_B64}},
        {"type": "text", "text": STAGE_A_PROMPT}]}])
print(r.model, r.stop_reason, r.usage, "".join(b.text for b in r.content if b.type == "text"))
```

Success = HTTP 200 with a parseable `CHOICE: N`. Failure = 400. Either result is reportable.

---

## P3 — is Opus 4.5 reachable on an effort-controlled surface? (1 call, ~$0.03)

**Why.** The mirror image of P2, from the older side. The `claude-api` reference states `effort`
works on Opus 4.5 (`low`/`medium`/`high` only), and pre-4.6 thinking uses
`{type:"enabled", budget_tokens:N}`. If both hold, Opus 4.5 can be run at `effort: "low"` — closer
to the C-ADAPTIVE surface than the temperature-only fallback the generation ladder used.

**Two cautions the lead should weigh before approving.** (a) Minimum `budget_tokens` is 1024, all
billed as output, so this surface costs **~6× per call** ($0.031 vs $0.0055) — roughly +$22–27 on
the Stage 1 total for one checkpoint. (b) It would make new Opus 4.5 data non-comparable with the
existing `generation_ladder/models/opus45` rows, which were collected on the temperature surface.
My recommendation is to run the probe for the record but **keep Opus 4.5 on the temperature
surface** for collection, on both cost and continuity grounds.

**Exact call.**

```python
r = anthropic.Anthropic().messages.create(
    model="claude-opus-4-5-20251101", max_tokens=3000,
    thinking={"type": "enabled", "budget_tokens": 1024},
    output_config={"effort": "low"},
    messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": IMG_B64}},
        {"type": "text", "text": STAGE_A_PROMPT}]}])
```

Run once with both `thinking` and `output_config`; if it 400s, retry once with `output_config` only
to separate which parameter was rejected. Budget 2 calls.

---

## P4 — does a `gpt-5.3` checkpoint exist? (1 call, ~$0.01; low priority)

**Why.** `ladder_probe.py`'s candidate list jumps 5.2 → 5.4. If a 5.3 exists it is a free extra
vintage point inside G-REASON, and its absence from the list may be an oversight rather than a fact.
A models-list call would settle it, but the lead has forbidden even a model-list call without
approval, so this is submitted as a request like the others.

**Exact call** — the minimal form is the list endpoint, which is cheaper and more informative than a
generation:

```bash
curl -s https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY" \
  | python3 -c "import json,sys;print(sorted(m['id'] for m in json.load(sys.stdin)['data'] if m['id'].startswith('gpt-')))"
```

This also re-verifies P1's OpenAI half in one request and would let P1 drop to its 2 Anthropic
candidates. If the lead prefers a single approval, **approve this list call plus P1's Anthropic
half** and the sweep shrinks from 10 calls to 3.

---

## Summary for the lead

| probe | calls | cost | blocks Gate 1 sizing? |
|---|---|---|---|
| P5 GPT price (documentation lookup, no call) | 0 | $0 | **yes — ±$42 on the total** |
| P1 availability sweep | 10 (or 2, with P4) | ~$0.07 | yes — 6 of 10 panel members are UNVERIFIED |
| P6 GPT 4-option token usage | 1 | ~$0.01 | yes — every GPT cost figure is extrapolated |
| P2 Opus 4.6 sampling-surface bridge | 1 | ~$0.005 | no — but it is the only way to *measure* the stratum confound |
| P3 Opus 4.5 effort surface | 2 | ~$0.06 | no |
| P4 OpenAI model list | 1 | ~$0 | no |
| **total** | **≤ 15** | **< $0.20** | |

None of these is a substantive research call, none touches a study cell, and none writes to a data
directory. All spend is inside the $15 contingency reserve and does not draw on the $135 planned
allocation. **Awaiting lead approval; nothing has been executed.**
