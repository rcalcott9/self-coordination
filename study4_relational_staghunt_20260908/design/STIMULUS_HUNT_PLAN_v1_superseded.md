# Study 4 (relational stag hunt) — targeted stimulus hunt for divergent-convention arrays

**Status: PLAN ONLY. Nothing generated, nothing sampled, no API calls made.**
Written `2026-09-08`. Nothing under `study2_4opt_20260830/` was modified; the
durability inventory is untouched.

**Scientific target.** Four-object visual arrays on which GPT-5.5 and Claude Opus 5
have *stable, different* modal choices under an **ordinary non-strategic choice prompt**,
so that one array can support both focal directions in a later COPY-vs-OTHER game.

---

## 0. Four findings from the inspection that change the plan

These come before the plan because three of them are blocking.

### 0.1 Every existing measurement used a coordination prompt, not a plain choice prompt

`s4_common.STAGE_A_PROMPT = BASE + CHOICE_FORMAT`, and `BASE` reads:

> "You are playing a one-shot coordination game with ONE other player — another instance
> of you (the same AI model)… you want to pick the SAME shape as the other player… the
> left-to-right order… is randomized independently for each of you, so position CANNOT be
> used to coordinate — you must coordinate on a shape by its FORM."

That is same-model partner information **and** coordination framing — both explicitly
excluded by this brief. `SUMMARY.md` §6.5 calls Stage A the "plain choice frame", but
that is relative to Stage C's payoff grid, not absolute. **There is no non-strategic
choice prompt anywhere in the pipeline.**

Consequence: every number in the durability inventory, including the F10 divergence, was
measured under a prompt this study may not use. The F10 result is evidence that a
divergence *axis* exists; it is **not** evidence that these modal choices survive a
neutral prompt. A prompt-transfer probe is therefore Stage 0 and is a hard gate.

### 0.2 The promotion bar as specified rejects the entire existing battery

Promotion = different modal items **and** both modal probabilities ≥ .90 at n = 24
(i.e. ≥ 22/24).

| F10 member | GPT modal | Claude modal | divergent | passes |
|---|---|---|---|---|
| m0 | .625 | 1.000 | — | no |
| m1 | .542 | .958 | DIV | no |
| m2 | .750 | 1.000 | DIV | no |
| **m3** | **.958** | .875 | DIV | no |
| m4 | .792 | .625 | DIV | no |
| **m5** | **1.000** | .875 | DIV | no |
| m6 | .750 | .875 | DIV | no |
| m7 | 1.000 | .875 | — | no |

**Battery-wide: 0 of 203 stimuli would pass.** At m3/m5/m6 Claude is at 21/24 — *one draw*
short of the bar. At n = 24 the ≥ .90 rule is really "≥ 22/24", and a single draw decides
it. See §3.1 for the borderline band this motivates.

### 0.3 Within F10 the two models' sharpness is anti-correlated

`corr(GPT modal share, Claude modal share)` across the 8 members = **−0.332**. Claude is
sharpest at t = 0, 2 (1.000) where GPT is at .625/.750; GPT is sharpest at t = 5, 7 (1.000)
where Claude is at .875. The ladder compression that sharpens one model blurs the other.

This is the central empirical risk: the parameter that creates divergence may not have a
setting where *both* models are simultaneously sharp. §8 treats it as the thing the pilot
must answer first.

### 0.4 F10's four-object array is effectively a two-object array

Across all 8 members × 2 models × 24 draws (384 draws), the two interior ladder items
received **3 draws total — 0.8%**. Both models choose only between the endpoints.

Battery-wide, 164 of 406 model × stimulus cells put every draw on **one** item and 143 on
**two**; only 44 spread across all four.

This matters scientifically. `SUMMARY.md` §2 argues four options were adopted precisely
because binary self-match has a .50 floor that collides with the selection criteria. An
array whose effective action space is 2 **reinstates that problem** while presenting as
4-option. It is not disqualifying — the object identities are still four and the position
schedule is still over four — but it must be measured and recorded, not assumed away
(§3.4, §4.3).

---

## 1. Audit of existing reusable code and data

### 1.1 Reusable as-is — no changes needed

| asset | file | why it carries over |
|---|---|---|
| **Two-mode sampler** | `code/run_selfmatch.py` | Already implements exactly the discovery/confirmation split this brief asks for: `--mode discovery` (n = 24) and `--mode validation` (n = 60), **written to separate files and never pooled**. Its docstring already states the winner's-curse rationale. |
| **Position schedule** | `s4_common.position_schedule(n)` | Constructive, not sampled; every item appears in every position exactly n/4 times; asserted at build time; deterministic. Satisfies "randomize display positions while preserving canonical object identity" with no modification. Requires n divisible by 4 — 24 and 60 both qualify. |
| **Item recovery** | per-stimulus `manifest.json` + `run_selfmatch` parse block | Model answers a **position** 1–4; the manifest maps position → item. The estimand is the item. Labels are positional and their object mapping changes every call, so there are **no stable A/B/C/D labels** already. |
| **Choice parser** | `s4_common.parse_choice` | Takes the **last** `CHOICE: N` match; returns 0-based position or `None`. Malformed rows are kept with `parse_ok=False` rather than dropped. |
| **Render loop** | `make_battery*.render()` | 24 permutations per stimulus, numeric position titles, tinted panel ground. The panel-ground comment records a real bug found at review (F13 dot counts unattributable across panel gaps) — keep it. |
| **Drawing primitives** | `make_battery.py` `blob`, `ngon`, `dots`, `grey`, `arc`, `texture`, `_ax` | `blob(seed, spike, scale, rot)` is the exact knob the F10 mechanism turns. |
| **Model config** | `s4_common` `GPT_ID`, `CLAUDE_ID`, effort=low both sides | Must stay pinned — the inventory's model-version caveat applies. |
| **Cell metrics** | `analyze_selfmatch.py` | Produces `self_match`, `modal_item`, `modal_share`, `entropy_bits`, `position_bias`, `item_counts`, `pos_counts`, `cross_match`. Extended, not replaced (§4.3). |

### 1.2 Reusable as evidence, not as stimuli

- `data/cell_metrics_discovery_batch{1,2}.csv` — 406 rows, the prior for which mechanisms
  to target.
- `study2_4opt_20260830/data/durability_inventory_4opt.csv` — read-only input.
- The eight `F10_curvature_m*` stimulus directories — the Stage 0 probe set.

### 1.3 Not reusable

- `STAGE_A_PROMPT` and everything derived from it (§0.1). A new prompt is required.
- `PROMPT_SHA["stage_a"] = d40ea45d` — a new sha must be recorded for the new prompt, and
  the two must never be pooled.
- `auditor_*`, `predict_*`, `SALIENCE_PROMPT` — all coordination-framed; out of scope here.
- The batch-2 `NEAR_EQUIVALENT` set — a recorded annotation, not a filter; carry the
  concept forward but re-derive membership for new families.

---

## 2. Proposed generator changes

New file `code/make_battery3.py`, modelled on `make_battery.py`. **No existing generator
is edited.** Output to a new `stimuli3/` tree with its own manifest.

### 2.1 Mechanism families — grounded in observation, not invented

Only three axes in the battery have any empirical claim to producing divergence. They are
listed with the evidence and with an honest strength rating.

**M1 · curvature/spikiness endpoints (from `F10_curvature`) — STRONG evidence.**
`fam_curvature(t)` builds four blobs with `spike = i·(0.9 − 0.1t)/3`, item 0 smoothest,
item 3 spikiest. GPT takes item 3, Claude item 0, **in the same direction on 6 of 8
members**, with a clean dose-response in t and dead interiors. This is the only
reproducible axis in the battery.

*Parameterization to sweep:* `spike_max` ∈ {0.25, 0.30, 0.35, 0.40, 0.45, 0.50} (m3–m5 sat
at 0.60/0.40); ladder shape ∈ {linear, endpoint-loaded}; interior spacing (to test whether
the interior can be made live at all); base-blob seed (4 draws, to separate the axis from
one particular blob).

**M2 · convexity with a round attractor (from `F09_convexity`) — MODERATE evidence.**
`fam_convexity` = [12-gon, 4-gon, spiky blob, spiky blob]. GPT locks item 1 (the 4-gon) at
**24/24 on 7 of 8 members**; Claude also picks item 1 but leaks consistently to item 0 (the
near-circular 12-gon): 7, 5, 6, 7, 7, 8, 3, 6 of 24. **Zero members diverge**, but Claude
has a persistent second attractor that is exactly the smooth/round pole M1 says it prefers.

*Parameterization:* raise the roundness of item 0 (12-gon → 24-gon → true circle) and lower
the distinctiveness of the 4-gon (rotate off-axis, soften corners) to try to tip Claude's
leak into a mode while GPT stays on the polygon.

**M3 · corner radius with a crossover (from `F20_corner`) — WEAK evidence, 3 members only.**
`F20_corner(t)` renders four rounded squares, radius ladder item 0 sharpest → item 3
roundest. GPT picks item 3 on all three members (.609/.609/.656 modal .75/.75/.79); Claude
picks item 0 at t = 0 (**24/24**) then flips to item 3 at t = 1, 2. So a crossover exists
between t = 0 and t = 1 and the grid has only three points across it.

*Parameterization:* dense radius sweep across the crossover — `r_max` ∈ {0.45, 0.50, 0.55,
0.60, 0.65, 0.70} with `r_min` ∈ {0.02, 0.06}, plus stroke-weight and fill variants.

**Explicitly not carried forward as Tier-1 sources:** `F03_symmetry` (7/8 members agree on
item 0), `F28_dotarrange`, `F41_contain` (agreement families; their one divergent member has
both models weak), `F11_noise` and `F12_mirror` (divergence is real but both models are
usually near chance — Tier-2 material, §3.3).

### 2.2 Substrate variation — and an honest note on what "family" then means

To reach the brief's 6–8 distinct families, each mechanism is realized on multiple
rendering substrates: filled polygon, outline-only, dot-cloud boundary, and textured fill.
That yields up to 12 nominal families from 3 mechanisms.

**These are not 6–8 independent mechanisms and must not be reported as such.** The schema
therefore carries `mechanism` **and** `family` as separate columns (§4.1), and the analysis
plan must cluster on `mechanism` for any claim about generality. Substrate variation tests
whether an axis survives re-rendering — worth knowing — but it is a robustness check, not
independent evidence.

### 2.3 Build-time assertions (new)

Added to `render()` in `make_battery3.py`, all hard failures:

1. **No duplicate objects.** The four drawn objects must be pairwise distinct — assert
   pairwise `sha256` of each object's own rendered panel differs. Guards against a
   parameter sweep collapsing two ladder rungs onto the same shape.
2. **No degenerate perms.** All 24 permutation PNGs pairwise distinct.
3. **Ink balance.** Per-object foreground pixel fraction within a stated band (propose
   [0.5×, 2.0×] of the array mean) so no object wins on sheer size. Recorded per object
   even when it passes.
4. **No panel-edge contact.** Every object's bounding box strictly inside its panel — the
   `dots()` comment records why this bit before.
5. **Determinism.** Re-running the generator reproduces byte-identical PNGs (fixed seeds,
   no RNG outside seeded generators).
6. **Arity.** Exactly four objects, exactly 24 perms, for every array.

### 2.4 The new prompt

Non-strategic, no partner, no payoff, no coordination, no green outline, no mention of
other agents. Position is **not** discussed — the old prompt's position sentence exists to
license coordination-on-form and would be leading here; position dependence is handled by
the schedule and measured as a diagnostic (§7).

```
Look at the four shapes in the image. Pick one.
Give one short sentence of reasoning, then end with exactly 'CHOICE: N'
where N is 1, 2, 3 or 4 - the position in the image of the shape you picked.
```

Recorded as `PROMPT_SHA["plain_choice"]`. Frozen before Stage 0 and never edited; a change
means a new sha and a new, separately stored sample.

**Open risk to check in Stage 0:** removing the position sentence may raise position
dependence. It is measured per cell and is a Tier-1 criterion (§3.2), not an afterthought.

---

## 3. Exact candidate-selection rules

Let n₂₄ = discovery draws, n₆₀ = confirmation draws. For a model × array cell define
`p_modal` = modal item share, `p_runner` = second-place share, `WLo` = Wilson 95% lower
bound on `p_modal`.

### 3.1 Discovery → promotion (n = 24 per model per array)

**Primary gate (as specified).** Promote iff:
- `modal_item[gpt] ≠ modal_item[claude]`, **and**
- `p_modal[gpt] ≥ .90` **and** `p_modal[claude] ≥ .90` (≥ 22/24), **and**
- parse rate ≥ .95 in both cells.

**Borderline band (a proposed deviation, flagged not hidden).** §0.2 shows this bar rejects
every existing stimulus, with Claude one draw short at three F10 members. Also promote,
tagged `promotion_band = "borderline"`, iff modes differ and:
- one model ≥ .90, and the other in **[.79, .90)** (i.e. 19–21 of 24).

Rationale: at n = 24 the .90 rule is a single-draw threshold, and resolving exactly that
uncertainty is what the n ≥ 60 confirmation stage is *for*. Borderline candidates are
confirmed under identical rules and are **not** given easier Tier-1 criteria. The band is
recorded so any later analysis can drop them and re-derive the primary-only result.

Borderline capacity is capped at **40%** of the confirmation budget so it cannot crowd out
primary candidates.

### 3.2 Tier 1 — clean divergent arrays (confirmation, n ≥ 60, fresh sample)

All of:

1. **Different confirmed modes** — `modal_item[gpt] ≠ modal_item[claude]`, both computed
   from confirmation draws only.
2. **Both strong** — `p_modal ≥ .75` for each model.
3. **Adequate modal margin** — for each model, `p_modal − p_runner ≥ .25` **and**
   `WLo ≥ .60`. The margin requirement is what stops a .76/.24 split counting as a
   convention.
4. **No material position dependence** — for each model, over the 4 display positions:
   `max_position_share ≤ .40`, and χ²(3) on position counts **not** significant at α = .01.
5. **Clean cells** — parse rate ≥ .95, no cell rebuilt more than once.

### 3.3 Tier 2 / Tier 3

- **Tier 2 — asymmetric.** One model confirmed strong (Tier-1 conditions 2–5 met) and the
  other diffuse: `p_modal < .50` **or** Wilson 95% upper bound `< .75`. The existing
  battery already supplies replicated instances (`F11_noise_m0`, `F12_mirror_m3`,
  `F27_linecount_m1`), but under the *old* prompt — they must be re-measured under the new
  prompt to count.
- **Tier 3 — shared convention.** Both models confirmed strong (conditions 2–5) on the
  **same** modal object. Useful as a stag-hunt control condition.

### 3.4 Recorded covariates, never exclusions

Following the project's existing treatment of `position_bias`:

- `n_items_live` — items receiving ≥ 5% of pooled draws. **`n_items_live ≤ 2` flags an
  effectively-binary array** (§0.4). Recorded on every array; reported in any write-up;
  does not exclude.
- `interior_share` — draws going to non-extreme ladder rungs.
- `ink_fraction` per object, `mechanism`, `substrate`, `family`, `param_vector`.

### 3.5 The non-independence flag

One Tier-1 array yields **two** focal-model conditions (GPT-focal and Claude-focal). These
are **not two independent stimuli**. The schema carries:

- `array_id` — the physical array
- `pairing_id` = `{array_id}::{focal_model}` — the analysis unit
- `independent_unit` = `array_id`

Any later model must cluster on `array_id` (or on `mechanism` for generality claims).
Target counts below are stated in **arrays**, never in pairings.

---

## 4. Output schemas

Four files, all new, none overwriting anything.

### 4.1 `stimuli3/battery3_manifest.csv` — one row per array

```
array_id, family, mechanism, substrate, member, param_vector_json,
n_options, n_perms, dir, object_roles_json, ink_fraction_json,
build_sha256, generator_version, created_utc
```

`object_roles_json` names each canonical item (e.g. `{"0":"spike_0.00","3":"spike_0.40"}`)
so a modal item is interpretable without re-reading the generator.

### 4.2 `data/stage{0,1,2}_<mode>_<ts>.csv` — one row per call

Superset of the existing `run_selfmatch` output, plus prompt provenance:

```
stage, mode, prompt_id, prompt_sha, array_id, model, api_model,
trial, perm_id, chosen_position, chosen_item,
ok, parse_ok, error, finish_reason, secs, ts, raw, reasoning
```

`mode ∈ {discovery, confirmation}`. **Discovery and confirmation rows never share a file**,
enforced by filename and asserted by the analyzer.

### 4.3 `data/cell_metrics_<stage>.csv` — one row per array × model

```
stage, mode, array_id, family, mechanism, substrate, model, n,
self_match, ci_lo, ci_hi, modal_item, modal_share, runnerup_item, runnerup_share,
modal_margin, wilson_lo, wilson_hi, entropy_bits, item_counts_json,
pos_counts_json, max_position_share, position_chi2, position_p, position_bias,
n_items_live, interior_share, parse_rate, n_malformed
```

### 4.4 `data/tier_assignments.csv` — one row per pairing

```
array_id, pairing_id, focal_model, other_model, independent_unit,
focal_modal_item, focal_modal_share, focal_wilson_lo, focal_margin,
other_modal_item, other_modal_share, other_wilson_lo,
modes_differ, tier, promotion_band, n_items_live_flag,
position_ok, discovery_only_estimate, confirmation_estimate, notes
```

`discovery_only_estimate` and `confirmation_estimate` are separate columns so pooling is
structurally impossible; the analyzer asserts that all tier decisions read the
confirmation column.

---

## 5. Cost and call counts

Anchor: batch 2 was 3,600 calls for ≈ $55 → **≈ $0.0153/call** at `effort=low` both sides
with one ~40 KB image per call. Costs below use $0.016 for headroom.

| stage | what | arrays | models | n | calls | cost |
|---|---|---|---|---|---|---|
| **0** | prompt-transfer probe: existing `F10_curvature_m{2,3,5,6}` + 2 agreement controls, **both** prompts | 6 | 2 | 24 | **576** | **$9** |
| **1** | discovery on new battery: 3 mechanisms × 4 substrates × 8 members | 96 | 2 | 24 | **4,608** | **$74** |
| **2** | confirmation on promoted candidates (budget 24 arrays; ≤ 40% borderline) | 24 | 2 | 60 | **2,880** | **$46** |
| **2b** | contingency: re-run of malformed/rebuilt cells, ~5% | — | — | — | ~370 | $6 |
| | **total** | | | | **≈ 8,430** | **≈ $135** |

Stage 0 is 7% of the budget and gates the other 93%. If Stage 1 discovery yield is far
below projection, Stage 2 spends less, not more — the confirmation budget is a cap.

For reference, this is roughly 2.5× the cost of batch 2, which `SUMMARY.md` §8 judged poor
value at +2 GPT-specific highs. The difference is that this hunt is targeted at an observed
mechanism rather than adding random families — which is precisely the bet §8 says to test.

---

## 6. Stopping rules

Written before any data, in the project's usual terms: **thresholds are not relaxed to
close a gap.**

- **G0 — prompt-transfer gate (hard).** If under the new plain prompt the F10 probe arrays
  do not show `modal_item[gpt] ≠ modal_item[claude]` on **≥ 2 of the 4** F10 members, with
  each model's `p_modal ≥ .60`, **stop.** The mechanism is a coordination-framing artifact
  and the whole generation plan is void. Redesign before spending Stage 1.
- **G1 — discovery yield floor.** If Stage 1 promotes **< 8** arrays (primary + borderline),
  stop and report. Do not lower the promotion bar, do not add substrates, do not re-run
  discovery hoping for different draws.
- **G2 — confirmation floor.** If confirmation yields **< 6 Tier-1 arrays**, report the
  shortfall and hand the go/no-go for the stag hunt back to the user. Do not re-screen
  Tier-1 failures at larger n to rescue them (that is the winner's curse the two-mode
  design exists to prevent).
- **G3 — anti-correlation kill.** If across Stage 1 the within-mechanism correlation
  between the two models' modal shares is **≤ −0.5**, record that the mechanism cannot
  sharpen both models at once and stop sweeping it further, whatever the raw yield.
- **G4 — budget.** Hard stop at **$180** across all stages.
- **G5 — no threshold edits after seeing data.** Any change to §3 after Stage 1 opens
  requires a dated amendment document stating that the criterion failed and why the change
  is a measurement argument, on the model of `AMENDMENT_01_criterion_d.md`. Both verdicts
  are then reported, always.

---

## 7. Position dependence and malformed output

### 7.1 Position

- **Design.** `position_schedule(n)` puts every item in every position exactly n/4 times,
  constructively. n = 24 and n = 60 are both divisible by 4. One schedule per
  (array, model, stage) cell.
- **Per-cell diagnostics.** `max_position_share`, χ²(3) on `pos_counts`, and the existing
  `position_bias`. Tier-1 requires `max_position_share ≤ .40` and χ² p ≥ .01 (§3.2).
- **Why it is stricter here than in Study 2.** There, position bias was a recorded
  covariate because a position responder scores .25 — chance — so it was a floor rather
  than an artifact. Here the estimand is the *identity of the modal object*, and a position
  responder can manufacture a spurious modal item. Hence promotion to an exclusion
  criterion for Tier 1 only.
- **New risk.** The plain prompt drops the old prompt's "position CANNOT be used"
  sentence. Stage 0 reports position diagnostics for both prompts on the same arrays, which
  measures the cost of that removal directly.

### 7.2 Malformed output

- Parser unchanged (`parse_choice`, last `CHOICE: N`).
- Malformed rows are **kept** with `parse_ok=False`, never silently dropped — this is what
  the Gate-1 backfill incident in Thread C established as necessary (thin cells attenuate
  estimates in a direction that flatters the hypothesis).
- Per-cell `parse_rate ≥ .95` or the cell is rebuilt **once**, with both attempts retained
  and the rebuild flagged. A cell rebuilt more than once fails Tier-1 condition 5.
- `finish_reason` recorded on every call to distinguish truncation from refusal-shaped
  output — Thread C's Gate 2A showed a `max_tokens` deviation can only be ruled out by
  measurement.
- Attrition audit before any tier assignment: if malformed calls concentrate in one
  mechanism or one model, report it, because the mechanism (token exhaustion on
  low-focality items) biases `p_modal` upward exactly where the hypothesis wants it.

---

## 8. Feasibility recommendation

**The brief's target — 12–16 Tier-1 arrays spanning 6–8 distinct families — is not
supported by the evidence. I recommend proceeding, but on a reduced and staged target.**

Why:

1. **Base rate.** 2 of 203 existing arrays have both models strong (≥ .75) and divergent —
   ≈ 1%. Both are `F10_curvature`, and Claude is at 0.772 in both.
2. **The bar is stricter than anything observed.** 0 of 203 arrays meet the n = 24
   promotion rule (§0.2).
3. **Only one mechanism has strong evidence.** M1 (F10) diverges on 6/8 members in a
   consistent direction. M2 is a zero-divergence near-miss. M3 has three members and a
   crossover glimpsed between two of them. There is no honest route to 6–8 *independent*
   mechanisms; substrate variation inflates the family count without adding mechanisms
   (§2.2).
4. **Anti-correlation.** Within F10, `corr(p_modal[gpt], p_modal[claude]) = −0.332`. The
   setting that sharpens one blurs the other, so "both ≥ .90" may have no interior solution
   on this axis.
5. **Prompt transfer is unverified.** All of the above was measured under coordination
   framing (§0.1), which this study excludes.
6. **Structural competition.** Battery-wide, when both models hold a strong convention they
   agree on the object **90 of 92 times (97.8%)**; among the 63 arrays where both exceed
   .90, divergence is **zero**. Strong conventions in these models are overwhelmingly
   *shared*. The hunt is looking for a rare configuration, not an under-sampled one.

**Realistic target: 4–10 Tier-1 arrays across 2–3 mechanisms.** I would treat 6 arrays from
2 mechanisms as a success worth building the stag hunt on, and 12–16 across 6–8 mechanisms
as not achievable from this starting point.

**Recommended sequencing.** Run Stage 0 first and treat G0 as a genuine stop. It costs $9,
resolves the blocking unknown (§0.1), and simultaneously measures whether the anti-correlation
(§0.3) and the dead-interior problem (§0.4) persist under the new prompt. Nothing in Stage 1
is worth funding until Stage 0 returns.

**If G0 fails,** the fallback is not more stimulus generation. It is a design change: either
accept Tier-2 arrays (one model has a convention, the other is diffuse — the battery already
has replicated instances) as the basis for an asymmetric stag hunt, or run the stag hunt
under the coordination-framed prompt the divergence was actually measured under, and drop
the non-strategic requirement. Both are real options; the second changes what the study can
claim about "ordinary" choice and should be decided deliberately, not by drift.

---

## 9. What this document does not do

No stimuli generated, no API calls, no files under `study2_4opt_20260830/` modified, no
change to `durability_inventory_4opt.csv` or `DURABILITY_INVENTORY_4OPT.md`. Nothing here
is frozen yet — freezing (design + generator + prompt + analyzer hashes) happens before
Stage 0, on the pattern of `data/osr_frozen_hashes.txt`.
