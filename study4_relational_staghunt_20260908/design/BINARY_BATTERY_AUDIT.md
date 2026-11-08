# Binary-battery audit — asymmetric copy-coordination policies for Study 4

**No API calls, no stimuli generated, no prior results modified.** Written `2026-09-08`.
Companion machine-readable files:

- `data/binary_inventory_current_models.csv` — 30 rows (15 stimuli × 2 models), 53 columns
- `data/binary_pool_gpt_only_unmeasured_claude.csv` — 96 rows, GPT-characterized, Claude never run

Prior inventories untouched: `study2_4opt_20260830/data/DURABILITY_INVENTORY_4OPT.md`,
`durability_inventory_4opt.csv`, and `study4_.../design/STIMULUS_HUNT_PLAN.md` are unmodified.

**Framing (per brief).** These coordination-framed measurements are treated as establishing a
*previously characterized copy-coordination policy*, not a neutral preference. Study 4 tests
whether that policy is deployed with relational accuracy across COPY / OTHER / UNKNOWN. The
Stage 0 neutral-prompt check is informative, **not a gate**; a failure would localize the
convention to the coordination frame rather than disqualify it.

---

## 1. Every binary battery located

| battery | folder | stimuli | models measured **as choosers** | n/model | raw |
|---|---|---|---|---|---|
| **step1 + step1b_screen + targeted** | `policy_specific_self_coordination_20260812_1401` | **15** | **GPT-5.5 + Claude Opus 5** | 60 | `data/fresh_self_match.csv`, `data/stageA_20260812_150823.csv` |
| **partner-policy confirmation** | `study2_partner_policy_20260822` | 8 (subset of the 15) | **GPT-5.5 + Claude Opus 5** | 60–180 | `data/confirmation/data/stageA*.csv` |
| **Study 1-HP v3** | `study1_hp_replication_20260905` | 120 screened → **96 retained** | **GPT-5.5 only** | 30 | `data/a1_screen.csv`, `data/a2_stimulus_level.csv`, `stageA_A{1,2}*.csv` |
| **generation ladder** (+`_expanded`) | `generation_ladder_20260814/models/*` | 15 / 45 | GPT-4o, GPT-5, Opus 4.5/4.6/4.7/4.8 — **no current model** | 60 | per-model `data/fresh_self_match.csv` |
| **Stage 3 calibration** | `source/`, `experiments/2026-08-01_...` | 6 pairs | gpt-5.4, claude-opus-4-8 — **no current model** | 420/pair | `source/confidence_calib_*.csv` |

**Generators.** `LLM_Coordination/Name_game_experiment/make_targeted_stimuli.py` (targeted
families A–E), `make_screen_stimuli.py` (step1b), `make_shape_stimuli.py` (step1 originals).
Stimulus metadata: `stimulus_manifest.csv` in each study folder; images under
`Name_game_experiment/stimuli/{visual,visual2,screen,targeted}/` as `<id>_AB.png` / `<id>_BA.png`.

**The binding fact:** only **15 binary stimuli** have both current models measured as
choosers. Everything else is either a different model generation or GPT-only.

---

## 2. How "policy strength" was measured — and yes, the prompt is coordination-framed

`psc_common.STAGE_A_PROMPT = step1_form_choice.PROMPT`, whose `BASE` (sha8 `3003ae1b`) is:

> "You are playing a one-shot coordination game with ONE other player — another instance of
> you (the same AI model). You will each independently pick one of the two shapes shown; you
> want to pick the SAME shape as the other player. No communication. IMPORTANT: the
> left/right position of the two shapes is randomized independently for each of you, so
> position CANNOT be used to coordinate — you must coordinate on a shape by its FORM."

So **same-model partner information + explicit coordination framing + an explicit instruction
that position is useless.** The 4-option `s4_common.BASE` is the same text with arity changed
— confirmed by its own source comment. Per the brief this is the intended characterization,
recorded in the inventory as `prompt_frame` on every row.

**Estimators.**
- `self_match_unbiased` = P(two independent draws match), U-statistic, with CI. **Binary floor
  is .50**, not 0.
- `modal_share` = share of the modal *identity* (not side). The model answers LEFT/RIGHT; the
  AB/BA variant maps side → identity. Balanced 30 AB / 30 BA.
- `form_consistency` = agreement of the identity choice across the AB and BA presentations —
  the direct position-invariance measure.
- `fallback` = boolean flag for position-defaulting.
- `p_left`, `rationale_mentions_position` = further position diagnostics.
- `self_match_select` / `self_match_holdout` (n = 30 each) — an **internal** split, not an
  independent replication.

**Two independent estimates exist** for 8 stimuli: the `policy_specific` primary (n = 60) and
the `study2_partner_policy` confirmation (n = 60–180), same models, same prompt, separate runs.

---

## 3. Per-model, per-stimulus inventory (current models)

`*` = `fallback` flag set. Share = modal share of the modal identity; chance = .50.

| stimulus | family | GPT modal | GPT share | Claude modal | Claude share | same mode | replicated |
|---|---|---|---|---|---|---|---|
| `a_chev_ud` | A_semantic | up | .900 | **down** | .917 | **DIFF** | yes |
| `b_spiral_cw` | B_glyph | ccw | .783 | ccw | 1.000 | same | yes |
| `b_tee_ell` | B_glyph | tee | 1.000 | tee | .967 | same | — |
| `c_contr_subtle` | C_contrast | midgrey | 1.000 | midgrey | 1.000 | same | — |
| `c_open_cplx` | compete | closed_cplx | 1.000 | closed_cplx | .633* | same | yes |
| `d_dens_extreme` | D_density | sparse | .517* | sparse | .650* | same | — |
| `d_texture` | D_density | fine | .567* | **coarse** | .917 | **DIFF** | yes |
| `mirror` | step1_original | blob-mirror | .550* | **blob** | .600* | **DIFF** | yes |
| `noise` | step1_original | noise-B | .733* | noise-B | .650* | same | — |
| `proto` | step1_original | circle | 1.000 | circle | 1.000 | same | yes |
| `rot` | step1_original | blob | .700* | **blob-rot90** | .500* | **DIFF** | yes |
| `s_arrow` | single | up | 1.000 | up | 1.000 | same | yes |
| `s_contrast` | single | dark | 1.000 | dark | 1.000 | same | — |
| `s_convexity` | single | concave | .983 | concave | 1.000 | same | — |
| `s_density` | single | dense | .533* | **sparse** | .500* | **DIFF** | — |

Full columns (Wilson intervals, select/holdout, entropy, `p_left`, `form_consistency`,
`prior_match_old_model`, `delta_vs_old`, per-row class and flags) are in the CSV.

### 3.1 The replication moves the answer — use it

| stimulus | model | primary (n=60) | replication | n | modal agrees |
|---|---|---|---|---|---|
| `a_chev_ud` | gpt | .900 | .767 | 180 | yes |
| `a_chev_ud` | claude | .917 | .789 | 180 | yes |
| `b_spiral_cw` | gpt | .783 | .750 | 180 | yes |
| `b_spiral_cw` | claude | 1.000 | 1.000 | 180 | yes |
| `c_open_cplx` | gpt | 1.000 | **.994** | 180 | yes |
| `c_open_cplx` | claude | .633 | **.500** | 180 | **NO** |
| `d_texture` | gpt | .567 | .650 | 180 | yes |
| `d_texture` | claude | **.917** | **.517** | 180 | yes |
| `mirror` | claude | .600 | .750 | 120 | **NO** |
| `rot` | claude | .500 | .500 | 120 | **NO** |
| `proto`, `s_arrow` | both | 1.000 | 1.000 | 60 | yes |

Two consequences:

- **`d_texture` Claude collapses .917 → .517.** The single-stage "Claude strong" reading is
  not reproducible. Any Claude-focal use of `d_texture` would have been built on n = 60 noise.
- **`c_open_cplx` becomes the clean asymmetric item**: GPT .994 at n = 180 while Claude sits at
  .500 with `form_consistency` 0.27 and a mode that flips between runs.

---

## 4 & 5. The four candidate classes, under both cutoffs and both evidence bases

Near-chance = the modal-share Wilson 95% interval covers .50.

### Using the best available estimate (replication where it exists)

| class | at ≥ .75 | at ≥ .90 | stimuli |
|---|---|---|---|
| **GPT strong, Claude near chance** | **1** (1 fam) | **1** (1 fam) | `c_open_cplx` |
| **Claude strong, GPT near chance** | 1 (1 fam) | 0 | `mirror` — **artifact, see §10** |
| **both strong, different modes** | **1** (1 fam) | 0 | `a_chev_ud` |
| both strong, same mode | 6 (4 fam) | 5 (4 fam) | `b_tee_ell`, `c_contr_subtle`, `proto`, `s_arrow`, `s_contrast`, `s_convexity`, (`b_spiral_cw` at .75) |
| neither strong | 5 (3 fam) | — | `d_dens_extreme`, `d_texture`, `noise`, `rot`, `s_density` |

### Using the single-stage primary only (n = 60) — shown for contrast, not preferred

| class | at ≥ .75 | at ≥ .90 |
|---|---|---|
| GPT strong, Claude near chance | 0 | 0 |
| Claude strong, GPT near chance | 1 (`d_texture`) | 1 (`d_texture`) |
| both strong, different modes | 1 (`a_chev_ud`) | 1 (`a_chev_ud`) |
| both strong, same mode | 7 (4 fam) | 6 (4 fam) |

The two bases disagree on **exactly the cells the study cares about**, and they disagree
because n = 60 is thin for a share near .6–.9. This is the strongest argument in the audit for
re-measuring rather than reusing.

### 5.1 The counts by family, not by stimulus

The 15 stimuli span only **8 families**: `step1_original` (4), `single` (4), `B_glyph` (2),
`D_density` (2), `A_semantic`, `C_contrast`, `compete` (1 each).

- The 6 "both strong, same mode" items sit in **4** families, and 4 of them are ceiling items
  (§10). This is one or two mechanisms, not six.
- Every non-null asymmetric class contains **exactly one stimulus in exactly one family**.

**No mechanism-level claim is supportable from this battery.** Each candidate is n = 1 array.

---

## 6. Replicated vs single-stage

`evidence_grade` in the CSV:

| grade | meaning | stimuli |
|---|---|---|
| **A_replicated** | second independent run, modal identity agrees for both models | `a_chev_ud`, `b_spiral_cw`, `proto`, `s_arrow`, `d_texture` |
| **B_replicated_unstable** | second run exists but a modal identity flipped | `c_open_cplx`, `mirror`, `rot` |
| **C_single_stage** | one run; `select`/`holdout` is an internal split of the same sample | `b_tee_ell`, `c_contr_subtle`, `c_dens_extreme`, `noise`, `s_contrast`, `s_convexity`, `s_density` |

`c_open_cplx` is grade **B** for a benign reason — the flip is *Claude's*, and it flips because
Claude has no policy there. GPT's side is grade-A stable (1.000 → .994). For a GPT-focal
design this is the strongest item in the battery; for a Claude-focal design it is unusable,
which is exactly the asymmetry sought.

---

## 7. The largest asset: 58 GPT-characterized arrays with Claude never measured

`study1_hp_replication_20260905` screened 120 binary stimuli and retained 96, **GPT-5.5 only**.

| `fresh_classification` | n | families |
|---|---|---|
| **form_rule_ceiling** | **58** | **33** |
| position_fallback | 30 | — |
| form_rule_partial | 8 | — |

The 58 have `self_match` min .814, median **1.000**, all with a select/holdout split, spread
across 33 families (`Y*` and `X*` mechanism series plus a few originals). n = 30 per stimulus.

**Claude has never been run as a chooser on any of them.** This is the direct route to the
brief's priority pattern: a Claude arm at n = 60 over the 58 is **3,480 calls ≈ $53** at the
$0.0153/call anchor, and would convert a 33-family GPT-characterized pool into a
GPT-strong/Claude-? classification. Given the base rates in §4 it is the only route with any
prospect of yielding more than one item per class.

Exported as `data/binary_pool_gpt_only_unmeasured_claude.csv` (all 96 rows, with
`claude_measured = 0`).

---

## 8. Which generators adapt to four objects

`make_targeted_stimuli.py` is **spec-driven**: `draw(ax, spec)` dispatches on `spec["kind"]`
across 18 primitives (`circle`, `poly`, `star`, `smoothblob`, `arrow`, `chevron`, `cross`,
`tee`, `hook`, `scurve`, `smoothstar`, `circbar`, `spiral`, `ring`, `outline`, `dots`,
`stipple`), and arrays are declared by
`add(name, id1, spec1, id2, spec2, family, manipulation, note)`.

**Adapting to four objects touches `add()` and the render loop only — the 18 drawers are
untouched.** Concretely: `add(name, [(id, spec)] * 4, ...)`, render 24 permutations instead of
AB/BA, and emit a `manifest.json` mapping perm → item order. The 4-option pipeline
(`study2_4opt_20260830`) already contains that render loop and `position_schedule`, so the
adaptation is a merge of two existing files rather than new code.

| generator | adaptable | note |
|---|---|---|
| `make_targeted_stimuli.py` | **yes, cleanly** | spec-driven; the A/B/C/D/E families are parameterized already |
| `make_screen_stimuli.py` | yes | same idiom, fewer kinds |
| `make_shape_stimuli.py` | partly | step1 originals are hand-built blobs/textures; `mirror`/`rot`/`noise` are matched-by-construction and are floor items anyway |
| `study2_4opt/make_battery{,2}.py` | n/a — already 4-option | supplies the render loop and balanced schedule to merge in |

---

## 9. Adding two alternatives without creating trivial distractors

The failure mode is obvious and must be designed against: if the two added objects are
implausible, the array is a 2-option task wearing a 4-option costume — which is precisely what
`F10_curvature` turned out to be (interiors took 0.8% of draws). Every proposal below is a
*hypothesis to be premeasured*, never an assumption that the binary policy survives.

**`c_open_cplx` — GPT strong (closed_complex), Claude at chance. Priority item.**
Binary contrast is open/simple vs closed/complex. Openness and complexity are *confounded* in
the binary version. Add the two cells that break the confound: **open+complex** and
**closed+simple**. This is a 2×2 factorial in one array, so no object is a distractor — each is
a legitimate corner. It also converts a confounded contrast into a diagnostic one: GPT's modal
corner tells you whether its convention is about closure or complexity.

**`a_chev_ud` — both strong, different modes. The star item.**
Binary is chevron-up vs chevron-down. Add **left** and **right** to complete the four canonical
orientations. All four are the same glyph at 90° steps with identical ink, so none is a
distractor by construction, and the up/down divergence is preserved as a sub-contrast. Risk to
premeasure: the 4-way version may pull both models to a single canonical orientation and
destroy the divergence.

**`d_texture` / `d_dens_extreme` — density-boundary family.**
Do **not** add two more rungs of the same fine→coarse ladder; that is exactly the F10 failure
(a monotone ladder makes interiors dead). Instead add two objects that are *off-ladder*:
matched mean density with different **spatial arrangement** (clustered vs periodic). Four
objects, two density levels × two arrangements — again a factorial, not a ladder.

**`b_tee_ell`, `b_spiral_cw` — glyph canonicality.**
Add the two remaining members of the natural glyph set (T/L/plus/ex; cw/ccw/straight/kinked).
These families were built as "one form, two orientations, ink exactly equal", so the extension
is the family's own logic.

**`s_contrast`, `c_contr_subtle` — tonal.**
A four-tone set risks becoming an ordered ladder. Add the two off-axis cells instead: same two
tones at a different **stroke weight** or **fill vs outline**, so tone and rendering are crossed.

**General rule adopted:** extend by **crossing a second factor**, never by lengthening a
one-dimensional ladder. Ladders produce endpoint-only responding; factorial corners give four
defensible objects. Record `n_items_live` (items receiving ≥ 5% of draws) on every array, as
in the 4-option plan, and treat `≤ 2` as a recorded flag.

**All extensions require fresh premeasurement of both models.** Nothing in §9 assumes transfer.

---

## 10. Flagged items — artifacts, positional conventions, ceilings

Recorded in `artifact_flags` in the CSV.

**Position-fallback on both models (policy claims void):** `d_dens_extreme` (form_consistency
0.10 / 0.30, `p_left` 0.05 / 0.15), `s_density` (FC 0.07 / 0.07, `p_left` 0.03 / 0.03),
`mirror`, `noise`, `rot`. On `s_density` both models are at chance on identity *and* answer
almost always RIGHT — the apparent "different modes" is a position artifact, nothing else.

**`mirror` is not a Claude-strong item.** It carries the "Claude strong / GPT chance" label at
≥ .75 on the replication, but `rationale_mentions_position` is **0.95 (GPT) and 0.98 (Claude)**,
both `fallback` flags are set, `p_left` is 0.88 / 0.67, and the Claude modal identity **flips
between runs**. `mirror` is matched-by-construction (a blob and its reflection) and was
designed as a floor item. **Excluded from every candidate class.**

**One option effectively ignored (ceiling):** `proto`, `s_contrast`, `s_arrow`,
`c_contr_subtle` — both models at ≥ .99 on the same identity, so the other option is never
chosen. Usable as stag-hunt *controls*; useless for detecting relational adaptation, since
there is no behavioural room to move.

**Old-model asymmetries do not transfer — a trap worth stating.** The `stimulus_manifest.csv`
`prior_*` columns are **previous-generation** measurements (GPT-5.x / Opus 4.8), and the
manifest's `prior_class_report` labels (`fallback_disparity` etc.) derive from them. On the
current models several reverse outright:

| stimulus | old GPT / Claude | current GPT / Claude | δ Claude |
|---|---|---|---|
| `b_tee_ell` | 1.000 / .528 | 1.000 / .935 | **+.407** |
| `c_contr_subtle` | .903 / .494 | 1.000 / 1.000 | **+.506** |
| `d_texture` | .903 / .528 | .501 / .845 | **+.317**, GPT −.403 |
| `d_dens_extreme` | .935 / .602 | .492 / .537 | GPT **−.442** |
| `s_density` | .903 / .655 | .494 / .492 | GPT **−.410** |

Every "GPT strong / Claude weak" item in the old manifest has either flipped or collapsed.
**Anything selected from the `prior_*` columns would be selecting on a model generation that is
no longer deployed.** The inventory therefore reports current-model values as primary and keeps
`prior_match_old_model` / `delta_vs_old` only as provenance.

**No parsing artifacts found.** `parse_side` is a fixed LEFT/RIGHT regex; identity is recovered
through the AB/BA variant; `valid_response` and `included_in_analysis` are already applied in
the source files and are re-applied in the inventory build. No cell showed differential
attrition between models.

---

## 11. What the audit supports

**For a GPT-focal COPY/OTHER/UNKNOWN design, there is exactly one clean item: `c_open_cplx`**
(GPT .994 at n = 180, `form_consistency` 1.00, no fallback; Claude at .500 with a run-to-run
mode flip). One array, one family.

**For a Claude-focal design there is currently none.** `d_texture` fails on replication and
`mirror` is a position artifact.

**`a_chev_ud` is the only both-strong divergent binary array** (GPT up .767 / Claude down .789
at n = 180, both modes replicating, neither flagged) — the binary counterpart of what the
4-option battery lacked entirely.

That is 1–2 usable arrays across 2 families, which will not support Study 4 on its own. The
recommended next step is **not** more generation but the **Claude arm on the 58-stimulus,
33-family GPT-characterized pool** (§7): ~3,480 calls, ~$53, no new stimuli, no new generator,
and it is the only action here with a realistic prospect of yielding several independent
families in the priority class. Four-object extension (§9) should follow that result, targeted
at whichever mechanisms actually show the asymmetry on current models.
