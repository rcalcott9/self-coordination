# MASTER DESIGN — Stage 1 (PROVISIONAL)

Lead-owned. Teammates read only. Audit-dependent fields marked **TBD**; everything else is FROZEN
and may not be changed by a teammate.

## 1. Research questions

Program: do independently developed language models converge on the same conventions, and do they
know which partners share them? A convention = a stable choice among several valid alternatives
where there is no objectively correct answer.

**Stage 1 only:** how similar are the underdetermined choice policies of different GPT and Claude
checkpoints, and does that similarity change across model generations?

Program levels 3 (relational policy knowledge) and 4 (strategic use) are OUT OF SCOPE this session.

## 2. Scope and exclusions

IN: policy similarity; policy convergence across checkpoint vintage; two domains (visual Schelling
points, code conventions); descriptive historical comparison.

OUT (hard stop): partner prediction, identity framing, payoff calibration, green assignment,
stag-hunt strategic trials, non-strategic Worker trials.

**Claims that may NOT be made:** that all model policies converge; that temporal patterns are
causal effects of training; that these domains represent deployed-agent behaviour generally; that
resemblance to GPT-5.5 alone proves cross-family convergence; **that cross-family similarity
reflects independent convergence rather than common inheritance from overlapping training corpora
(threat 10 — Stage 1 cannot distinguish these and must state both readings).** Historical checkpoint analysis is
DESCRIPTIVE — available checkpoints are survivorship-biased and may not share identical inference
interfaces.

Required language: "convergence on this fixed battery" not general convergence; "associated with
checkpoint vintage" not caused by training; "policy similarity" not correlated equilibrium;
"descriptive historical pattern" not causal time trend.

## 3. Domains

**Visual** — four-option visual Schelling arrays. Extensive existing stimuli, runners, validation
and policy estimates. Sampling frame TBD (T1).

**Code (EXPLORATORY)** — new four-option underdetermined coding-convention battery. Code
conventions may be too standardised or too easy; that is an EMPIRICAL POSSIBILITY to be reported,
not a problem to engineer around. A code battery is frozen only after its own pilot gate passes.

## 4. Model panel

TBD (T4). Preference: >= 3 GPT and >= 3 Claude checkpoints if they fit the budget and a common
request surface. Older checkpoints are NOT to be excluded merely for complicating a trend;
compatibility strata are to be identified instead. Known constraint from prior work in this tree:
`claude-opus-4-5-20251101` rejects adaptive thinking (HTTP 400), so it cannot share the ADAPTIVE-ON
request surface used by Opus 4.6/4.7/5.

### 4.1 Request surface. FROZEN (D-017).

**Claude: `thinking={"type": "disabled"}`, passed EXPLICITLY on every call, on every checkpoint,
never omitted and never defaulted.** Omission is not equivalent to OFF: it means OFF on Opus
4.6/4.7/4.8 and adaptive-ON on Opus 5, so a defaulted parameter would silently split the panel by
vintage. The runner asserts the parameter is present before dispatch and records
`thinking_blocks_returned` on every row; any row returning a thinking block is a collection failure,
not a datum.

Verified empirically before freezing: the Gate 1 probe (2026-09-09,
`runs/probe_gate1/gate1_probe.json`) put `{"type":"disabled"}` to all seven Claude checkpoints and
all seven accepted it on the first attempt with no thinking block returned. OFF is therefore the
LARGEST COMMON Claude surface; adaptive-ON is not available on the three oldest checkpoints and
cannot serve as the panel surface. The 4.5-era stratum boundary above applies to ON, not to OFF.

**Why OFF, on the merits.** Reasoning traces let a model construct a justification for an
underdetermined choice, and that construction is itself a variance source: it inflates within-model
diffuseness and depresses measured self-match. OFF measures the policy rather than the argument for
it, and it matches the low-effort condition a deployed agent making a fast conventional choice
operates under.

**What this costs, stated plainly.** Every four-option measurement already in this tree was collected
adaptive-ON. **No existing visual cell is comparable to Stage 1 data**, and every visual cell is
collected fresh. (T1's audit independently recommends fresh collection, so little is forgone.)

**GPT: no uniform surface exists and none can be manufactured.** `gpt-5*` take
`reasoning={"effort":"low"}`; `gpt-4*` have no reasoning parameter and take `temperature=1.0`.
Recorded per row in `control_surface` and carried as Threat 13.

**LIMITATION, NOT SOLVED.** The setting is a constraint on the trend claim. Stage 1 measures the
**low-effort policy**. A thinking-ON condition may produce different distributions and is a
FOLLOW-UP, not a default. No Stage 1 result may be stated as a property of a model unqualified; it
is a property of that model AT THIS SETTING, on this fixed battery.

### 4.2 The vintage ladder is asymmetric. FROZEN (D-020b).

The GPT ladder spans **24 months** (2024-04 to 2026-04). The Opus-tier Claude ladder spans **8**
(2025-11 to 2026-07). This is not a design choice - it is the whole vision-capable Opus history.

**The vintage analysis is therefore a GPT analysis with a short Claude window attached, and is
reported that way.** A null Claude trend over 8 months carries much less weight than a null GPT trend
over 24. The two are NEVER presented side by side as comparable evidence, and no summary sentence may
combine them into a single statement about "models". Any Claude-side null is stated together with the
window it was measured over.

`claude-sonnet-4-5` and `claude-haiku-4-5` are deliberately NOT used to lengthen the Claude ladder:
they are a different model tier, and adding them would confound vintage with tier. They are available
as a tier contrast, which is a different question.

### 4.3 Zero reusable cells is a COST of this study. FROZEN (D-020c).

Every Stage 1 cell is new. Two independent reasons, either sufficient: the request-surface change
(§4.1, D-017), and selection conditioning (`FROZEN_22` was selected on "GPT-5.5 share >= .75 and
FC >= .80" and was never admissible for estimating similarity; it is also the only set carrying
four-option data for Opus 4.6/4.7).

This is recorded as a cost, not a neutral fact. It means the budget buys a smaller battery and a
shorter panel than it would have if any existing measurement had been reusable, and it means the
code pilot gate is **not compressed to make room for anything downstream**. The existing n=24
gpt-5.5 and opus-5 cells on B203 are retained *unpooled* as a free external check on how much the
thinking setting moves a policy - that is their only role.

### 4.4 Alias resolution - what the probe established, and what it did not (D-021)

Four Claude checkpoints are requested by undated alias (`claude-opus-4-6`, `-4-7`, `-4-8`,
`claude-opus-5`) rather than by a pinned snapshot, so the provider could in principle serve a
different build than the alias names. The Gate 1 probe of 2026-09-09 put one live call to each and
`model_returned == model_requested` in every case, including all four aliases; no substitution was
observed. **That establishes the aliases resolved correctly on that date, not that they are pinned.**
`checkpoint_returned` is recorded and compared on every collected row, so a mid-run substitution
would be caught rather than assumed absent.

## 5. Sampling units and definitions

- **Unit of measurement:** one model x item cell.
- **n = 48 per NEW model x item cell. FROZEN FLOOR.** Never silently lowered. 48 = 2 complete
  cycles of all 24 permutations for visual items, giving every canonical option every screen
  position exactly 12 times.
- **Policy:** a model's choice distribution over canonical options for an item.
- **Policy similarity (pairwise, per item):** agreement between two models' choice distributions —
  modal agreement, expected cross-model match, distributional distance, and probability assigned to
  the other model's modal action.
- **Convergence:** similarity that increases with checkpoint vintage. Must be distinguished from
  models individually becoming MORE DETERMINISTIC, which raises expected match without any
  increase in mutual similarity. Determinism-adjusted similarity is mandatory, not optional.

## 6. Budget and gates

| constraint | value |
|---|---|
| planned spend ceiling | **$135** |
| total Stage 1 hard ceiling | **$150** |
| contingency reserve | $15 (the difference; not allocatable at Gate 1) |
| n per new cell | **48, floor** |

Gate order and tradeoff preference if the design does not fit — **in this order, sample size never
reduced**: (1) reuse valid existing measurements; (2) reduce redundant items within a mechanism;
(3) reduce total battery size while retaining BOTH domains; (4) reduce the checkpoint panel LAST.

**Sequential gates**
1. **Gate 1 (team synthesis)** — lead reconciles all five reports against raw files, proposes
   visual frame, code pilot battery, checkpoint panel, schemas, sample sizes, required new cells,
   cost. **User approval required before any substantive API call.**
2. **Code-domain pilot gate** — small independent pilot. Passes only with: >1 behaviourally live
   option on a meaningful fraction of items; within-model stability on some items; across-model or
   across-checkpoint variation; no domination by correctness or universal style; reliable parsing.
   Standardisation or universal instability are REPORTABLE OUTCOMES, not failures to fix.
3. **Collection** — only after Gate 1 approval and pilot pass; all manifests, prompts, schemas and
   the checkpoint panel frozen and hashed first. **Collection runs SEQUENTIALLY in one chat with
   conservative concurrency (D-011), not as parallel per-checkpoint workers.** Wall-clock is
   therefore additive across checkpoints and must be sized on the slowest per-call checkpoint.
   Per-checkpoint integrity requirements are unchanged: identical frozen artifacts, returned
   checkpoint verified on every response, stop on any manifest/prompt/parser/checkpoint mismatch.

## 7. Approval requirements

- No substantive API call before user approval of Gate 1.
- Teammates make NO API calls (T4 may request a minimal availability probe; lead approval required).
- Teammates submit a plan for lead approval before material edits.
- Only the lead edits the seven control documents.

## 8. Known threats to inference

1. **Selection-conditioned batteries.** Most existing four-option arrays were selected for a model
   relationship (GPT-strong, shared, divergent, previously confirmed). A frame built from these
   cannot estimate similarity. T1 must recommend a BROAD frame.
2. **Determinism vs similarity.** See S5.
3. **Behavioural collapse.** Four displayed options frequently reduce to one or two live choices;
   effective support must be measured per cell, never assumed.
4. **Position sensitivity.** Must be measured explicitly, not inferred.
5. **Estimator coarseness.** At n=24 form consistency is quantised to 1/6 and cannot certify
   position invariance for a selected item; this motivated the n=48 floor.
6. **Silent incompatibility.** Multiple prompt generations, model generations, salience ratings and
   chooser responses coexist in this tree. A populated model ID does NOT mean the model acted as a
   chooser. Never combine incompatible prompts, checkpoints, stimulus versions or estimators.
7. **Survivorship bias** in which historical checkpoints remain callable.
8. **Binary results do not predict four-option results** — demonstrated in this tree, not assumed.
9. **Training-frequency attractors (raised by T3; NO item-level fix exists).** An option that is
   arbitrary for a human author may nonetheless be strongly attractored for an LLM by corpus
   frequency. Such an item passes every construction criterion in the T3 rubric and still yields
   convergence that is an artefact of shared corpus statistics rather than convention formation.
   This is the largest hole in the code-domain design and cannot be closed by better items.
10. **Common-cause confound (raised by T3; STUDY-LEVEL, not item-level).** No item, however clean,
   separates convergence from shared training data. GPT and Claude train on overlapping public
   corpora, so similarity between families has at least two explanations — independent convergence
   on the same convention, and common inheritance from the same sources. Stage 1 CANNOT distinguish
   them. Every cross-family claim must be stated as compatible with both.
11. **Post-hoc undecidability of collapse (T3).** Neither the item audit nor the pilot can tell an
   item that collapses because one option is RIGHT from one that collapses because it is
   CONVENTIONAL. This is why the rubric had to be written a priori: the pilot can retire bad items
   but can never certify good ones.
12. **Rubric knowledge cutoff (T3).** C3/C10 judgements rest on the auditor's recall of what an
   ecosystem has standardised, not a corpus measurement, and cannot be refreshed without network
   access. Unsourced C3/C10 calls are capped at severity 1 and carry a named-source field.
13. **The GPT control surface changes across the vintage ladder (D-019).** Pre-`gpt-5` checkpoints
   have no reasoning parameter and are called at `temperature=1.0`; `gpt-5`+ are called at
   `reasoning={"effort":"low"}`. The boundary (2025-08) falls in the MIDDLE of the vintage range, so
   any GPT trend straddling it is confounded with control surface. Unfixable by parameter choice.
   Mitigation is analytic only: `control_surface` is a recorded column, and the trend is examined
   WITHIN surface as well as across it. The Claude panel is not affected - OFF is uniform across all
   seven checkpoints.
14. **Thinking-OFF bounds every Stage 1 claim (D-017).** See section 4.1. Results describe the
   low-effort policy, not the model.
15. **Differential parse missingness reads as a cross-family policy difference (D-023, caught before
   collection, not after).** Response formatting is a *house habit*: markdown-bolding a final answer,
   backticking a letter, lower-casing a marker are conventions that vary by model family and by
   vintage. A parser that is even slightly narrow therefore drops responses at a rate that **varies
   with the very grouping variable the study compares**, and the drops land after the n floor is
   committed, so the surviving cells are quietly non-random within model but not across models. The
   failure is invisible in aggregate parse rate and would present as a genuine difference in policy
   between GPT and Claude, or between vintages of one family - the exact effect the study is looking
   for. Mitigations, all mandatory: the parser accepts every formatting variant it can without
   guessing and NEVER defaults; a **per-cell** parse-rate floor of 0.95 is enforced and a cell below
   it is flagged in `integrity.json` and excluded from headline estimates rather than carried; and
   parse rate is reported **broken out by model family and vintage**, never as a single pooled
   number, because a pooled rate is exactly what hides this.
16. **Behavioural collapse is an identifiability limit on the primary statistic, and is ALSO a
   result.** Once a cell puts all its mass on one option, no estimator can recover the order of the
   tail, and the determinism-adjusted statistic is driven toward its ceiling whatever the truth
   (T5 measured the drift: estimate 0.925 -> 0.994 as support falls 2.00 -> 1.02 with truth fixed at
   0.932). More data does not fix it. Two consequences are carried, not resolved: the primary
   statistic is reported only on cells that clear the liveness threshold, with an explicit
   `identifiable` flag; and the **prevalence of collapse is itself reported as a substantive
   finding** on the full unscreened frame, because a model placing one option 48/48 under a
   low-effort setting IS the shared-convention result in its most direct form.
