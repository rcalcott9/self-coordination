# GATE 1 REPORT — Stage 1 policy convergence
**Status: APPROVED 2026-09-09. Collection in progress.** Three lock items recorded before the first
call (D-020..D-024) and folded into the body below: `convention_group` with the collapsed metric
pre-registered as primary (§4.2), the vintage-ladder asymmetry (§6.1), and zero reusable cells as a
cost of the study (§6.2).
Date 2026-09-09. Lead-authored. Every number below was recomputed by the lead from raw files or
from a live probe; nothing is carried over from a teammate's prose without verification, and where
a teammate's prose and its own data disagree, both are reported (§7).

---

## 0. The one-paragraph version

The panel is **live and clean**: 16 of 17 candidate checkpoints answered a real four-option call
today, all 16 returned the checkpoint that was requested, all 16 parsed. `thinking` OFF is accepted
by **all seven** Claude checkpoints, which makes OFF — not the tree's adaptive-ON — the only setting
that spans the panel. That decision (D-017) costs the study all existing four-option data, which
turns out to be a small loss because most of it is selection-conditioned on a model relationship and
could not have been used anyway. Measured per-call cost is **$0.0057 visual / ~$0.0032 code**, which
buys more than the earlier estimates suggested. The recommendation is **9 checkpoints × 41 visual
arrays × n=48, plus a 12-item code pilot**, at **$117.3 base / $134.9 with contingency** — inside the
$135 planned ceiling, with $15 of the $150 hard ceiling untouched. The code battery needed 11 of 36
items removed for construction defects, and the code domain is **not** near-universal agreement a
priori, so the code pilot gate must actually be run rather than assumed away.

---

## 1. Availability probe — run, logged, and it changed two things

Approved by the user and run before this report, as instructed. Script
`runs/probe_gate1/gate1_probe.py`, derived from the frozen `ladder_probe.py`; the original and its
2026-08-14 output are untouched (the latter preserved as
`runs/probe_gate1/ladder_probe_20260814_PRESERVED.json`). One live call per checkpoint on the real
four-option stimulus with the frozen prompt `d40ea45d`. **17 calls, $0.0908**, logged as
`PROBE-G1-01` .. `PROBE-G1-17` in `RUN_LEDGER.csv` with cost metered from `response.usage`.

| | result |
|---|---|
| reachable | **16 of 17** |
| parsed under the frozen parser | **16 of 16** |
| `model_returned == model_requested` | **16 of 16** — zero alias substitution, including the four undated aliases |
| Claude accepting `thinking={"type":"disabled"}` | **7 of 7, first attempt, no fallback needed** |
| thinking blocks returned when OFF was requested | **0 of 7** — off is verified from the response, not assumed from the request |

**The single failure is `gpt-4-0613`, and it is a vision failure, not an availability failure:**
`"Model 'gpt-4-0613' does not support image inputs."` It remains code-eligible. This is exactly the
case D-015(c) predicted the frozen probe would misclassify: the frozen test
`"image" in low and "not supported" in low` does not match `does not support`, so the frozen artifact
records `vision=True` for a vision-less model. The patched test records it correctly. The frozen file
is not edited; the corrected value lives in the lead-owned
`audits/models/checkpoint_panel_verified.csv`.

**Two things this changed.** (1) It resolved the thinking-parameter question in a direction neither
branch of the instruction anticipated — §2. (2) It replaced the inherited `$0.0153/call` cost anchor,
which came from the binary era, with per-checkpoint measurement — §5. The old anchor was **2.7x too
high**; sizing under it would have cut the panel for no reason.

---

## 2. Thinking parameter — decided OFF, and the reason is not the one expected (D-017)

The instruction had two branches: match the tree if the tree is OFF; use OFF if the tree is mixed or
unset. **The tree is neither.** Every chooser runner that has ever produced four-option data uses
`thinking={"type":"adaptive","display":"summarized"}` — verified by opening each file
(`s4_common.py:281`, `psc_common.py:88`, `run_opus47.py:81`, `run_confirm_pair.py:68`). The one
`"thinking": None` in the tree is the else-branch of an env-switched alternative and was never
collected. The tree is consistent, and it is consistently **ON**.

**Decision: OFF.** The deciding fact is availability, not preference. Adaptive-ON is **not available**
on `claude-sonnet-4-5`, `claude-haiku-4-5` or `claude-opus-4-5` — the 2026-08-14 probe shows the two
of those it tested failing the adaptive call and falling back to `temperature=1.0`. Matching the tree
would therefore delete the three oldest Claude checkpoints and leave a "vintage trend" resting on
four points inside a five-month window. The stated reason for matching the tree — comparability with
the existing map — cannot be bought at the price of the comparison the study exists to make. OFF is
accepted by all seven and is the largest common surface.

The user's scientific rationale is recorded in `MASTER_DESIGN.md §4.1` as given: reasoning traces let
a model construct a justification for an underdetermined choice, and that construction is itself a
variance source. OFF measures the policy rather than the argument for it.

**What it costs, stated plainly: no existing four-option visual measurement is comparable to Stage 1
data, and every visual cell is collected fresh.** This is a smaller loss than it sounds — see §3.

**Operational rule, frozen:** `thinking={"type":"disabled"}` is passed **explicitly on every Claude
call and never defaulted**. Omission is *not* equivalent to OFF — it means OFF on Opus 4.6/4.7/4.8 and
adaptive-ON on Opus 5 — so a defaulted parameter would silently split the panel along the vintage
axis being measured. The runner asserts presence before dispatch and records
`thinking_blocks_returned` per row; a row returning a thinking block is a collection failure, not a
datum.

**Limitation, carried into the report and not solved:** Stage 1 measures the **low-effort policy**. A
thinking-ON condition may produce different distributions and is a follow-up, not a default. No
result may be stated as a property of a model unqualified; it is a property of that model at this
setting, on this fixed battery.

**One side benefit.** MASTER_DESIGN §4 previously carried a stratum boundary at Opus 4.5 because it
rejects adaptive thinking. Under OFF that boundary **disappears** — the Claude panel has a single
uniform request surface across all seven checkpoints. The GPT panel does not and cannot (§6, Threat 13).

---

## 3. Visual sampling frame — `VIS-FRAME-41`, and an explicit selection-inheritance statement

**Recommended frame: 41 arrays, one per family of the 203-array `study2_4opt` battery (B203), the
member chosen by a fixed index rule — the middle rung of the family's parametric ladder,
`index=(n-1)//2` — applied blind to every model result.** File
`audits/visual/recommended_frame_arrays.csv`, frame_id `VIS-FRAME-41`. Extension ladder to 82 is in
the same file; fallback `VIS-FRAME-16` (batch 1 only) if batch 2's conditioning is judged fatal.

**Verified by the lead from the raw stimulus directory, not from prose:** 203 array directories,
41 families, structured as batch 1 = 16 families x 8 members + batch 2 = 25 families x 3 members.
(`make_battery.py`'s docstring saying "15 x 8 = 120" is stale.) The frame file contains 41 rows
under `VIS-FRAME-41`, 41 distinct arrays, 41 distinct families — one array per family, no family
twice. This is the maximal application of the tradeoff order's step 2, "reduce redundant items within
a mechanism": all within-family redundancy is removed before anything else is touched.

### Selection inheritance — stated explicitly, per source

This is the constraint that decides which existing stimuli may be used at all, and it is stated per
source rather than in aggregate:

| source | conditioned on | admissible for similarity? |
|---|---|---|
| **B203 batch 1** (16 families x 8) | **nothing** — render timestamps precede its first API call | **YES** |
| **B203 batch 2** (25 families x 3) | aggregate weak-convention yield; **no model relationship** | **YES, with `batch` as a stratum** |
| `stimuli4`, `stimuli5`, `stimuli6` | a model relationship | **NO** |
| `FROZEN_22` | literally "GPT-5.5 share >= .75 and FC >= .80" | **NO — sharpest case** |
| Stage C set, `stimuli_pilot` | a model relationship | **NO** |

`FROZEN_22` matters most because it is the **only** set on which Opus 4.6/4.7 have four-option data.
Reusing that data would import GPT-strength directly into the vintage trend. Combined with D-017,
this is why **no existing visual cell enters Stage 1** — and why little is forgone: the reuse the
budget was hoping for was largely inadmissible on selection grounds before the thinking decision
touched it.

### A correction to a tree document, verified from raw

`DISCOVERY4_REPORT.md` states that no four-option positional policy exists. That was inferred from 14
cells. On the 406-cell B203 battery there are **three cells at `position_modal_share` >= .75**, which
the lead recomputed independently from the raw choice rows:

| array | checkpoint | pos_modal_share | raw position distribution |
|---|---|---|---|
| `F05_orient_m2` | gpt-5.5 | **.750** | {pos3: 6, pos4: 18} |
| `F11_noise_m2` | claude-opus-5 | **.792** | {pos2: 19, pos3: 2, pos1: 1, pos4: 2} |
| `F11_noise_m5` | gpt-5.5 | **.917** | {pos4: 22, pos3: 2} |

All three recompute to T1's figures exactly. The claim "position policies do not survive the move
from 2 to 4 options" is **over-general and must not be repeated** — it holds for the arrays it was
measured on, not for the battery. `position_modal_share` stays a mandatory reported column, and any
array reaching .75 is analysed as position-policy rather than form-policy. `DURABILITY_INVENTORY_4OPT.md`
is separately stale ("exactly one 4-option battery", "only gpt-5.5 and opus-5") and should not be
cited.

---

## 4. Code battery — two rejection lists, as instructed

T3 audited all 36 items against a rubric it wrote and froze **before** `code/design/` contained
anything (blind authorship is structurally guaranteed, and the rubric hashes recompute exactly).
Verdicts: **11 ACCEPT / 14 FLAG / 11 REJECT**.

### List A — INVALID. Removed. 11 items.

`code_argorder_001`, `code_argorder_002`, `code_error_002`, `code_outorder_001`, `code_outorder_002`,
`code_return_002`, `code_return_003`, `code_serial_002`, `code_serial_003`, `code_tie_003`,
`code_varname_003`.

These fail construction, not interest. **Construction-defect rate 11/36 = 31%, which implicates the
generator.** Three the lead re-verified directly against `code_items.json`, all of which T2 had rated
**low** risk:

- **`code_outorder_002`** — the stem says the fields `email, id, created_at, name` are "listed here
  alphabetically". They are not; alphabetical is `created_at, email, id, name` — **which is option B**.
  The stem both asserts a falsehood and, to any model that notices the falsehood, points at one option.
- **`code_tie_003`** — option B's rule ("leaving names that differ only in case in their input order")
  is contradicted by its own worked example `(Apple, apple, apricot, Banana)`; input order puts
  `apple` first. The example is also identical to option C's. Two options demonstrate identical
  behaviour as rendered.
- **`code_error_002`** — the stem requires *both* a machine-readable reason and a human sentence;
  option A `{"error": "email is not a valid address"}` carries only the sentence. It does not satisfy
  the stem.

Nine of the eleven need a one-line or one-option edit. Repair is preferred to deletion (§4.3).

### List B — VALID BUT UNIVERSAL. Retained and labelled. 1 confirmed + 12 watch.

**This is not a defect.** Per the instruction, near-universal agreement is a *measurable subset*, not
a reason to remove an item. Confirmed: **`code_error_003`**. Watch list (C3/C10 at severity 1, i.e.
suspected-universal on an unsourced judgement): 12 further items, listed in
`audits/code/item_decisions.csv` under `b_watch`.

`convention_universality` becomes a **pre-registered item-level covariate**, not a filter. An item on
List B that collapses to one option across every checkpoint is a *result* — the reportable null of
§3 of MASTER_DESIGN — and is reported as such.

### 4.1 The finding that matters most about the code domain

**Domain-fact rate is 1/36 confirmed (3%), 33% suspected; construction-defect rate is 31%.** The two
rates point opposite ways, and that is the finding: **the code domain does not look overwhelmingly
standardised.** What threatens the code battery is construction quality, not the domain being trivial.

This bears directly on one of the two decisions stated in advance — "if the code pilot shows
near-universal agreement, go visual-only and do not redesign". The a-priori audit does **not**
support assuming that outcome. The pilot gate has to actually be run.

### 4.2 The bias that must be pre-registered before any code collection

Eight items split one convention across two near-synonymous options (`acc`/`accumulator`,
dict/`Counter`, `Z`/`+00:00`, base64/base64url; `code_fileorg_003` gives the dominant convention
three options and its rival one). Splitting **lowers `modal_share`, raises `effective_support`, and
lowers `cross_model_match`** — every one of them toward "did not collapse", which is the more
interesting result. **LOCKED (D-020a).** `coding/convention_groups_v1.json`, sha8 `c755c83f`, frozen **before** the first
code call. The pre-registration is not just the column — it is which metric is primary:

- **PRIMARY: the collapsed coding.** Every metric in `ANALYSIS_SPEC.md` is computed on counts summed
  within `convention_group`. `K` becomes the number of groups for that item and the chance floor is
  recomputed as `1/K_group` — it is **not** .25 for a collapsed item.
- **SECONDARY: the raw four-option coding**, `K = 4`, chance .25.
- **Both are reported for every item and every headline number, side by side, regardless of which is
  more interesting.** Where they disagree in direction, the disagreement *is* the result and the item
  is named. It is not resolved in favour of either.

7 of 12 core items collapse; 5 do not. Not collapsing is a positive decision with a recorded reason —
wrongly grouping genuinely different conventions creates the opposite bias to the one being
corrected — so the rule is narrow: same rule differently rendered (an abbreviation, an alternative
packing of the same information, or a designator variant). `code_serial_001` groups `Z` with
`+00:00`; `code_tie_001` groups half-up with half-away-from-zero, which are indistinguishable on the
positive values the spec describes; `code_fnname_001` and `code_varname_002` are **not** grouped,
because the item *is* the choice of lexeme. `code_sentinel_001` is flagged `aggressive` (4 options to
2 groups) and must always be read beside its raw coding.

### 4.3 Code core pilot — 12 items, no repair round needed

T3 found the original 12-item core does not survive (3 rejections). It does not need repairing,
because a surviving item exists in every mechanism. Recommended core, one per mechanism, all drawn
from ACCEPT or FLAG:

| mechanism | item | verdict |
|---|---|---|
| argument_ordering | `code_argorder_003` | ACCEPT |
| error_representation | `code_error_001` | FLAG |
| file_organization | `code_fileorg_001` | FLAG |
| function_naming | `code_fnname_001` | ACCEPT |
| interface_layout | `code_iface_003` | ACCEPT |
| json_field_naming | `code_jsonname_001` | ACCEPT |
| output_ordering | `code_outorder_003` | FLAG |
| return_representation | `code_return_001` | ACCEPT |
| sentinel_values | `code_sentinel_001` | FLAG |
| serialization | `code_serial_001` | FLAG |
| tie_breaking | `code_tie_001` | ACCEPT |
| variable_naming | `code_varname_002` | ACCEPT |

7 ACCEPT + 5 FLAG, 12 mechanisms, 12 families. **Note the confound this does not fix:** after List A
removals, four mechanisms (`argument_ordering`, `output_ordering`, `return_representation`,
`serialization`) have only **one** surviving item each, so mechanism is confounded with family there
and leave-one-mechanism-out is impossible. Repairing List A is the only fix, and it is recommended as
a post-approval task for T2 (T2 owns `code/design/`; the lead does not edit it).

### 4.4 Four prompt defects that must be fixed before any code call

1. **The parser will drop responses non-randomly across checkpoints.** `CHOICE:\s*\[?\s*([A-D])\b`
   fails on `CHOICE: **B**`, on backticked letters, and on lowercase (no `re.I`). Markdown-bolding a
   final answer is a house habit that varies by family and vintage — **differential missingness biases
   exactly the cross-checkpoint comparison**, and the drops land after n=48 is committed. Fix the
   regex and add a hard per-cell parse-rate floor.
2. **The render rule loses option boundaries** on the six multi-line items (`'<LABEL>.\n<display>'`
   with no fence or indent), against `SCHEMA.md §4`.
3. **The coordination frame contradicts `SCHEMA.md §4`** ("never mention coordination, matching, or
   another model"). Recommendation: **keep the frame** — parity with the visual domain is what makes
   the two domains comparable at all — and amend SCHEMA.md on the record rather than leave a silent
   contradiction.
4. **The frame changes the measured quantity asymmetrically between domains.** Each code `spec` ends
   in a first-person question ("Which name do you give?"), so the code prompt asks two questions —
   what do you write, *and* what will your copy pick — where the visual prompt asks only the second.
   "Policy" in MASTER_DESIGN §5 must be read as **self-coordination policy**, and the asymmetry
   recorded as a domain-comparison limitation.

---

## 5. Checkpoint panel — verified, and now cheaper than assumed

`audits/models/checkpoint_panel_verified.csv` (lead-owned; T4's `checkpoint_panel.csv` left
byte-unchanged). 17 candidates, 16 LIVE, availability evidence dated today.

**Measured cost per call, at the $5.00/$30.00 per-Mtok rate fixed by D-016** (the pessimistic
assumption, used for both providers as the single primary number — not a claim about GPT's real price):

| domain | measured | range across checkpoints |
|---|---|---|
| visual (image + 4-option prompt) | **$0.00567 mean/call** | $0.0043 (gpt-4o) – $0.0098 (haiku-4-5) |
| code (text only, ~230 in / ~70 out) | **~$0.00324 est/call** | input from rendered items; output from probe |

The code figure is an estimate (input tokens approximated at chars/4 from the rendered prompts); the
visual figure is **measured**. Both are logged with their basis.

### Alias resolution — what the probe established, and what it did not (D-021)

Four Claude checkpoints are requested by **undated alias** (`claude-opus-4-6`, `-4-7`, `-4-8`,
`claude-opus-5`) rather than by a pinned snapshot, so the provider could in principle serve a
different build than the alias names. The Gate 1 probe put one live call to each and
`model_returned == model_requested` in every case, including all four aliases; **no substitution was
observed.**

That establishes the aliases **resolved correctly on 2026-09-09**. It does not establish that they
are pinned. The limitation is therefore kept but weakened to exactly that: `checkpoint_returned` is
recorded and compared on **every collected row**, so a mid-run substitution would be caught rather
than assumed absent. The five GPT-side checkpoints are pinned snapshots and are not exposed to this.

### Strata

- **GPT: two request-surface strata, and the boundary is unfixable.** `gpt-5`+ take
  `reasoning={"effort":"low"}`; `gpt-4*` have no reasoning parameter and take `temperature=1.0`.
  The boundary falls at 2025-08, in the *middle* of the vintage range. **Threat 13.**
- **Claude: one stratum.** Under OFF, all seven share a request surface (§2).
- **Claude tier is a second axis.** `sonnet-4-5` and `haiku-4-5` are not Opus. Mixing them into a
  vintage ladder confounds vintage with model tier, so the recommended Claude panel is **Opus-only**
  and the two non-Opus checkpoints are held back as a *tier* contrast, not a vintage point.

---

## 6. Sizing — arithmetic at n=48 against $135 planned / $150 hard

n = 48 per new model x item cell. **Fixed floor, never lowered.** Calls = checkpoints x items x 48.

### Recommended plan

| tranche | cells | calls | base cost |
|---|---|---|---|
| **A — visual** | 9 ckpts x 41 arrays | 17,712 | **$100.5** |
| **B — code pilot** | 9 ckpts x 12 core items | 5,184 | **$16.8** |
| | **total** | **22,896** | **$117.3** |
| | + 15% contingency (retries, output-length variance, parse re-runs) | | **$134.9** |

**$134.9 against the $135 planned ceiling. $15.1 of the $150 hard ceiling is untouched and is the
only reserve.** The 15% figure is defensible because the probe measured real token counts on the real
prompt and stimulus, and a permutation-balanced run has a deterministic call count — the residual
variance is output length and retries, not design.

### Recommended panel — 9 checkpoints, 4 GPT + 5 Claude

| GPT | vintage | surface | | Claude (Opus tier only) | vintage | surface |
|---|---|---|---|---|---|---|
| `gpt-4-turbo-2024-04-09` | 2024-04 | temperature | | `claude-opus-4-5-20251101` | 2025-11 | thinking OFF |
| `gpt-4.1-2025-04-14` | 2025-04 | temperature | | `claude-opus-4-6` | 2026-02 | thinking OFF |
| `gpt-5-2025-08-07` | 2025-08 | reasoning low | | `claude-opus-4-7` | 2026-04 | thinking OFF |
| `gpt-5.5-2026-04-23` | 2026-04 | reasoning low | | `claude-opus-4-8` | 2026-05 | thinking OFF |
| | | | | `claude-opus-5` | 2026-07 | thinking OFF |

Exceeds the >=3 GPT / >=3 Claude preference. **Two GPT checkpoints sit either side of the 2025-08
surface boundary**, which is the minimum needed to examine a trend *within* surface as well as across
it — the only available mitigation for Threat 13.

### 6.1 The vintage ladder is asymmetric, and this bounds the headline claim (D-020b)

**The GPT ladder spans 24 months (2024-04 to 2026-04). The Opus-tier Claude ladder spans 8
(2025-11 to 2026-07).** That is not a design choice — it is the whole vision-capable Opus history.

**Stated plainly: the vintage analysis is a GPT analysis with a short Claude window attached.** A
null Claude trend over 8 months carries much less weight than a null GPT trend over 24. The two are
never presented side by side as comparable evidence, and no summary sentence may combine them into a
single statement about "models". Any Claude-side null is stated together with the window it was
measured over.

`claude-sonnet-4-5` and `claude-haiku-4-5` are deliberately not used to lengthen the Claude ladder —
they are a different tier, and adding them would confound vintage with tier.

### 6.2 Zero reusable cells is a cost of the study (D-020c)

### Alternatives, if the recommendation is declined

| option | ckpts | vis arrays | code items | base | +15% | note |
|---|---|---|---|---|---|---|
| **Recommended** | 9 | 41 | 12 | $117.3 | **$134.9** | at planned ceiling |
| Visual-only, stage code later | 9 | 41 | 0 | $100.5 | $115.6 | keeps $19 reserve; code becomes a second gate |
| Full code battery | 9 | 41 | 25 | $135.5 | $155.8 | **breaches the hard ceiling. Rejected.** |
| Wider panel, narrower visual | 10 | 34 | 12 | $111.1 | $127.7 | adds `gpt-5.4`; drops 7 mechanisms |
| Cheaper fallback | 8 | 41 | 12 | $104.3 | $119.9 | drops one Claude vintage point |

**If the recommendation goes over at collection time,** the order fixed by D-010 applies and is
applied in this order: (1) reuse valid existing measurements — **already exhausted, the answer is
zero**; (2) cut redundant items within a mechanism — **already exhausted, the frame is one array per
family**; (3) cut the battery, retaining both domains; then (4) cut the panel. **n=48 is never cut.**
The user's standing instruction that a sizing overrun is met by cutting the panel before n is
consistent with this and binds at step 4.

**Every Stage 1 cell is new. Existing reusable cells: zero.** Two independent reasons, either
sufficient: the thinking-surface change (D-017) and selection conditioning (§3). The existing n=24
gpt-5.5 and opus-5 measurements on B203 batch 1 are **not pooled** and are retained as a free
external stability check — a same-stimulus, same-prompt, different-surface comparison that costs
nothing and directly measures how much the thinking setting moves a policy.

This is recorded as a **cost**, not a neutral fact. `FROZEN_22` was selected on "GPT-5.5 share >= .75
and FC >= .80" and was never admissible for estimating similarity — and it is the only set carrying
four-option data for Opus 4.6/4.7. The budget therefore buys a smaller battery and a shorter panel
than it would have if any existing measurement had been reusable. **The code pilot gate is not
compressed to make room for anything downstream.**

---

## 7. Where a teammate's report and its own data disagree

Reported because the instruction was to verify claims against raw files rather than accept prose.

- **T1's four-option row counts.** T1's prose gives `claude-opus-5` = 13,616 rows. T1's own coverage
  CSV gives 10,136 for the same checkpoint, and the lead's independent count from raw is **9,944**.
  The prose figure appears to fold in
  `study4_relational_staghunt_20260908/claude_arm_20260908/data/stageA_CLAUDE58_20260908_172722.csv`
  — 3,480 rows, and a **binary** file (`parsed_choice_side`, no `chosen_item`): 10,136 + 3,480 =
  13,616 exactly. A residual 192-row gap on each of the two large checkpoints is consistent with
  `n_calls` counting planned rather than returned calls in the Stage C betting cells, where T1 itself
  reports choices conditional on ATTEMPT. **Verified counts to use: gpt-5.5 10,912; opus-5 9,944;
  opus-4-6 1,704; opus-4-7 1,056.** The 4-6 and 4-7 figures match T1 exactly.
  This does not affect sizing — every cell is new regardless — but it must not be quoted as-is.
- **Confirmed against raw, no discrepancy:** 203 arrays / 41 families; four checkpoints only have ever
  produced a four-option response; **no four-option file has a `salience_rating` column** (so all
  four-option data is chooser data, and the rater trap is confined to binary arity); the three
  `position_modal_share` >= .75 cells and their exact values.
- **Confirmed against raw:** T3's three headline item defects (§4), read directly from
  `code_items.json`.

---

## 8. What is required before the first collection call

1. **User approval of the panel, frame and budget in §6.**
2. Fix the code parser regex and the multi-line render rule (§4.4 items 1–2).
3. Add and pre-register the `convention_group` column (§4.2).
4. Amend `SCHEMA.md §4` on the record to permit the coordination frame (§4.4 item 3).
5. Capture `r.usage` in the GPT runner. `s4_common.ask_gpt` discards it, so GPT spend is currently
   unmeasurable and `measured_cost_usd` would stay empty for half the study, leaving the ceiling
   enforced on estimates alone (D-016).
6. Assert `thinking={"type":"disabled"}` present on every Claude call and record
   `thinking_blocks_returned` per row (D-017).
7. T5's analysis specification and null-band calibration — **outstanding, still running.** It
   constrains analysis, not sizing, and does not block this gate.

Collection runs **sequentially in one chat with conservative concurrency**, not in parallel subagents.

**STOP. No collection call until the panel, frame and budget above are approved.**
