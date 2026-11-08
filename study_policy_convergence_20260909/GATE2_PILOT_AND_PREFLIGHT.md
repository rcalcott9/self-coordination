# GATE 2 — code pilot result + visual liveness preflight
2026-09-09. Both collections complete. **Spend to date $27.78** of $135 planned / $150 hard.
No further collection until the visual-frame recommendation in §5 is approved.

| run | calls | parse fail | transport fail | checkpoint mismatch | cost |
|---|---|---|---|---|---|
| code pilot (12 items x 9 ckpts x n=48) | 5,184 | **1** | 0 | **0** | $18.96 |
| liveness preflight (24 arrays x 2 ckpts x n=24) | 1,152 | **0** | 0 | **0** | $8.73 |
| Gate 1 availability probe | 17 | 0 | 1 (no vision) | 0 | $0.09 |

**Integrity.** Parse rate 0.9998 overall and reported broken out per checkpoint, never pooled
(Threat 15): 1.0000 on all five Claude checkpoints and on three of four GPT; 0.9983 on
`gpt-4-turbo-2024-04-09` (1 failure in 576). **Zero rows returned a thinking block** — OFF is
verified from the responses, not assumed from the requests. **Zero checkpoint mismatches** in 6,336
calls, so the four undated Claude aliases resolved correctly throughout, not merely at probe time.

One cell is at **n=47** (`code_fnname_001` x `gpt-4-turbo`) because of the single parse failure. It
is flagged, **not topped up**: retrying only the trials that failed to parse would select for
parseable responses, which is Threat 15's mechanism in miniature. 107 of 108 cells are at n=48.

---

## 1. Code pilot — the domain is largely, but not entirely, shared convention

Both codings, side by side, as pre-registered. Neither was chosen after seeing the data
(`coding/convention_groups_v1.json` sha8 `c755c83f`, frozen before the first call).

| item | K_grp | raw med modal | raw med support | collapsed med modal | collapsed med support | cross-family modal agreement |
|---|---|---|---|---|---|---|
| `code_argorder_003` | 3 | 1.000 | 1.00 | 1.000 | 1.00 | **1.00** |
| `code_error_001` | 3 | .958 | 1.09 | .958 | 1.09 | **1.00** |
| `code_fileorg_001` | 4 | 1.000 | 1.00 | 1.000 | 1.00 | **1.00** |
| `code_fnname_001` | 4 | .729 | 1.75 | .729 | 1.75 | .75 |
| `code_iface_003` | 3 | .688 | 1.75 | .688 | 1.75 | **0.00** |
| `code_jsonname_001` | 2 | .604 | 1.92 | .604 | 1.92 | .60 |
| `code_outorder_003` | 4 | 1.000 | 1.00 | 1.000 | 1.00 | **1.00** |
| `code_return_001` | 3 | 1.000 | 1.00 | 1.000 | 1.00 | **1.00** |
| `code_sentinel_001` | 2 | 1.000 | 1.00 | 1.000 | 1.00 | **1.00** |
| `code_serial_001` | 2 | 1.000 | 1.00 | 1.000 | 1.00 | **1.00** |
| `code_tie_001` | 3 | .958 | 1.09 | .958 | 1.09 | .60 |
| `code_varname_002` | 4 | 1.000 | 1.00 | 1.000 | 1.00 | **1.00** |

**Modal agreement across all 36 checkpoint pairs: within-family .922, cross-family .829** — against a
raw chance floor of .25. Identical under both codings.

### 1.1 The pre-registration mattered less than expected, and that is reported, not buried

**The collapsed and raw codings are almost indistinguishable.** Median modal share and median
effective support are equal to three decimals on all 12 items; modal agreement is identical to three
decimals under both. Collapsing moves only the count of fully deterministic cells, and only on three
items (`argorder` 6→7, `sentinel` 7→9, `serial` 8→9).

The reason is that T3's predicted bias needs the mass to be *split* between near-synonyms, and it is
not — the items collapsed onto a single option, so there was nothing for the grouping to re-unite.
The pre-registration was still the right call: it was made when the direction was unknown, and the
result is only reportable *because* the choice was fixed in advance. It does mean the "biased toward
looking less standardised" warning in `GATE1_REPORT §4.2` did **not** materialise on these 12 items.

### 1.2 What the shared conventions are — 8 of 12 items, unanimous across 24 months and both families

Every one of the nine checkpoints picks the same option, and it is the modal option at .96–1.00:

`rect(x, y, width, height)` · `raise ValueError` · `src/` layout · lexicographic listing ·
`return (lowest, highest)` · `_MISSING = object()` · `"2026-09-09T14:03:27Z"` · `data`

This is the shared-convention finding in its most direct form. **Under a low-effort setting, models
from two independently developed families, spanning 2024-04 to 2026-07, converge on one option out of
four on two thirds of these items, at or near 48/48.**

### 1.3 One item shows complete cross-family divergence, and it replicates across five checkpoints

`code_iface_003` (verbosity CLI surface), **cross-family modal agreement 0.00**:

| | modal option |
|---|---|
| all four GPT checkpoints (2024-04 → 2026-04) | `--verbose` (`store_true`) |
| `claude-opus-4-5` | `--verbose` (`store_true`) |
| `claude-opus-4-6`, `-4-7`, `-4-8`, `opus-5` | **`-v, -vv, -vvv`** (`counting`) |

The divergence survives the collapsed coding (`store_true` and `negatable` group together;
`counting` is a separate group), so it is not an artefact of option splitting. It is also the
cleanest instance of a pattern that shows up in **four** items — `iface`, `tie`, `fnname`,
`jsonname` — where `claude-opus-4-5` sides with GPT and `4-6` onward do not. A change at the Claude
4.5→4.6 boundary, on a panel where every Claude checkpoint shares one request surface and one model
tier. **Descriptive only, on this fixed battery of 12 items** — four items is not a basis for a claim
about the checkpoint.

### 1.4 The decision rule fires, and here is the honest reading of it

The pre-agreed rule was: near-universal agreement on the code pilot ⇒ visual-only, no redesign.
**The pilot meets it** — 8 of 12 items are unanimous and cross-family modal agreement is .829.

But three qualifications belong on the record:

1. **It is not universal.** Four items carry real variation and one diverges completely. Retiring the
   code arm discards a measured cross-family policy difference, which is the rarest thing in the
   study so far.
2. **The code domain has the same identifiability problem as the visual one.** 8 of 12 items sit at
   median effective support 1.00, so the determinism-adjusted statistic cannot be estimated on them.
   Only `fnname`, `iface` and `jsonname` (support 1.75–1.92) are estimable.
3. Expanding to the full 25-item battery was already rejected at Gate 1 for breaching the hard
   ceiling, and nothing here changes that.

**Recommendation: stop the code arm here.** The 12-item pilot at n=48 x 9 checkpoints is a complete,
reportable result in its own right, not a truncated one. Do not expand.

---

## 2. Liveness preflight — the design accident that made it a better experiment

24 arrays x `gpt-5.5-2026-04-23` and `claude-opus-5` x n=24, paired against those checkpoints'
existing n=24 measurements on the same images and the same prompt `d40ea45d`.

**The GPT arm is not an ON→OFF contrast. It is a test–retest control.** `gpt-5.5` is called with
`reasoning={"effort":"low"}` in *both* the tree-era data and this preflight — the thinking change
applies only to Claude. So the GPT deltas measure re-measurement drift at n=24 across nine days with
everything held fixed, which is exactly the noise floor the Claude deltas need to be judged against.
This was not designed; it follows from choosing the only two checkpoints with existing data.

---

## 3. Rule 3 — the two families move in OPPOSITE directions

| | mean Δ support | median Δ | more diffuse | more deterministic | unchanged |
|---|---|---|---|---|---|
| **GPT-5.5** (test–retest control, surface unchanged) | **−0.047** | −0.056 | 7 | 12 | 5 |
| **Claude Opus 5** (ON → OFF) | **+0.093** | +0.148 | 14 | 5 | 5 |

**Correlation of the two deltas: −0.342. Only 7 of 24 arrays moved the same way.**

Read against the control: the noise floor is about ±0.05, and Claude's shift is roughly two to three
times that, in the direction of **more diffuse under OFF**. That is the direction the design's own
rationale predicts — reasoning traces let a model construct a justification, and the justification
locks the choice in; removing them unlocks some of it (`MASTER_DESIGN §4.1`).

**What this does and does not threaten.** It does *not* create a differential inside Stage 1: every
checkpoint is collected at one fixed surface, so no within-study comparison straddles a surface
change. It sharpens two things already on the record. First, it puts a measured magnitude on
Threat 13 — "low-effort policy" is not the same intervention for the two families, because for Claude
OFF removes reasoning while for `gpt-5*` reasoning effort stays low and for `gpt-4*` there is no
reasoning parameter at all. Second, it confirms D-017's conclusion empirically: tree-era Claude
numbers are **not** comparable to Stage 1 Claude numbers, and the size of the incomparability is now
known rather than assumed.

The effect is not uniform across the range — it is concentrated in the middle
(`mid` stratum: Claude +0.22; `high` +0.06; `low` −0.00). Collapsed cells do not move.

---

## 4. Rule 1 — the OFF support distribution, as a substantive output

On these 24 arrays, median OFF support is **1.80** (GPT) and **1.93** (Claude), with 8% of cells
fully deterministic. **These figures are not the battery-wide prevalence** and must not be quoted as
such: the 24 arrays were deliberately enriched, two thirds drawn from the mid and high ON strata.
Battery-wide prevalence comes from the unscreened frame, which is why §5 does not screen it down.

**The decisive result is about the collapsed end. OFF does not rescue a collapsed cell.**
Of the 8 cells at ON support < 1.10, **7 stayed collapsed** (median OFF support 1.09) and one rose to
1.56. Collapse under ON predicts collapse under OFF.

That settles the question the preflight was bought to answer: **the identifiability problem in
`VIS-FRAME-41` is real and the surface change does not fix it.** 30 of the frame's 41 arrays sit in
the low ON stratum.

---

## 5. Recommendation on the visual frame

**Do not screen the frame down.** Collect all 41 arrays and report two declared strata from the one
collection:

- **Stratum L — liveness-screened.** Arrays where both models clear effective support 1.5 under OFF.
  Carries the primary determinism-adjusted statistic, with T5's `identifiable` flag. 14 of the 24
  preflight arrays qualify; the frame's own membership is determined from the frame's own data.
- **Stratum F — the full unscreened frame.** Carries **prevalence of collapse**, modal agreement and
  the shared-convention result, which need no diffuseness and are the safety-relevant output.

**Disclosure, stated and not left implicit:** Stratum L is conditioned on a **generator property** —
how graded a manipulation is — measured through two checkpoints' *within-model* marginals. It does
**not** condition on any between-model relationship: not agreement, not cross-model match, not modal
coincidence. **That is a weaker form of selection than the one that disqualified `FROZEN_22`**, whose
rule was literally "GPT-5.5 share ≥ .75 and FC ≥ .80" — a rule on the dependent variable itself.
Weaker is not absent. Every Stratum L result is reported as conditioned on a generator property, and
never as a property of the battery.

### 5.1 Cost — the projection changed and the number needs a decision

The Gate 1 sizing used $0.00567/call from a single probe call on an easy stimulus. Measured over
1,152 real calls it is **$0.00758 blended**, because reply length scales with how ambiguous the array
is (GPT-5.5 emits 278 output tokens on `high` arrays against 156 on `low`; Claude 73 against 55).

Re-projecting properly — per-array by ON stratum, per-checkpoint by its measured output-token ratio,
and at the real 4-GPT/5-Claude panel mix rather than the preflight's 1:1:

| plan | visual cost | total incl. $27.78 spent | |
|---|---|---|---|
| **41 arrays x 9 ckpts x n=48** | **$109.0** | **$136.8** | **$1.8 over planned, $13.2 under hard** |
| 41 arrays x 8 ckpts | $93.2 | $120.9 | fits planned |
| 41 arrays x 7 ckpts | $82.3 | $110.0 | fits planned |
| 34 arrays x 9 ckpts | $90.3 | $118.1 | fits planned |

(The naive blended rate would have said $134.3; the enriched preflight overstates the frame, which is
mostly `low` arrays.)

**Recommendation: run the full 41 x 9 as approved and accept the $1.8 planned overrun**, with the
budget guard set at the $122.2 hard-ceiling remainder. The overrun is smaller than the projection's
own error, the alternatives all cut science to save an amount inside that error, and the tradeoff
order says cut items before panel — but here neither cut is worth making. If it does overrun, the
guard stops the run cleanly and resumes after a decision, as it did on the preflight.

**Requires approval before the visual tranche starts.**
