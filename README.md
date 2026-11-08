# Self-Coordination

Does an LLM coordinate with copies of itself by consulting a **self-model**
("what would a copy of me pick?"), or just by finding whatever is **salient** in
the stimulus — the thing *any* agent would pick? And does it know when it can
coordinate at all?

Split out of `LLM_Coordination/Name_game_experiment/` on 2026-08-04 as its own
project.

## The three experiments

| launched | experiment | finding |
|---|---|---|
| `2026-07-30` | [selfcoord_identity](experiments/2026-07-30_selfcoord_identity/) | **Partner identity does nothing.** Coordination is set entirely by the stimulus. The `self` framing changes the model's *vocabulary* (37% introspective language vs 0% elsewhere) but not its *procedure* (96%+ salience-hunting in every condition). Even being told the answer outright leaves it squinting at the picture. |
| `2026-08-01` | [confidence_calibration](experiments/2026-08-01_confidence_calibration/) | **Neither model knows when it can coordinate**, and it misses in both directions — underconfident where coordination is perfect, overconfident on pure noise. |
| `2026-08-02` | [partner_specific_coordination](experiments/2026-08-02_partner_specific_coordination/) | The battery contains **model-specific focal points**: `inkblot` is GPT-only (self-advantage +0.47), `rot` is Claude-only (+0.12). |

## Layout

```
experiments/          one self-contained folder per experiment
  <date>_<slug>/
    code/  data/  visualizations/  README.md
source/               the working tree these were built from
  stage_figures/               the three summary figures (one per experiment)
  partner_specific_coordination/   coordination matrix + follow-up design
  stimuli/                     proto4, noise4 stimulus sets
```

`experiments/` folders are self-contained copies; `source/` is where the work
actually happens. All R scripts resolve paths from their own location, so this
project can be moved without breaking.

## Rebuild the figures

```bash
cd source/stage_figures
Rscript fig_stage2_identity.R          # identity vs salience
Rscript fig_stage3_calibration.R       # confidence calibration
Rscript fig_stage4_partner_specific.R  # partner-specific coordination
```

## Open threads

1. **Follow-up allocation pending approval** — `source/partner_specific_coordination/followup_trial_design.csv`
   proposes 5,136 API calls. No runner written yet.
2. **The revealed-confidence measure saturates.** The safe range {3,5,7,9} fails to
   bracket the switch point on most stimuli — 10 of 12 points are censored at a
   boundary. Critically, `inkblot` and `rot` — the two stimuli the whole hypothesis
   rests on — are both pinned, so as specified the measure *cannot* detect a
   partner-identity effect where it matters. Push the safe values higher for those cells.
3. **Three wording decisions block launch** — see `source/partner_specific_coordination/prompt_templates.md`:
   naming symmetry, the `other` phrasing, and whether to name the partner in the
   choice-only elicitation.
4. **The coordination matrix is generic-framing only.** Elicited under "another
   instance of you", not named partners — exploratory, and the named-framing ground
   truth must be recomputed from the follow-up's own choice cells.
5. **`viz_calib.csv` has no derivation script.** The CSV and the plotting code exist,
   but nothing in the tree computes `trueP`/`statedP`/`impliedP` from the raw
   `confidence_calib_*.csv`. The rule was recovered by fitting: `impliedP` is the
   safe/10 threshold where the attempt rate crosses 50%, linearly interpolated,
   clamped to 0.95 above and 0.25 below. Worth writing out properly.
