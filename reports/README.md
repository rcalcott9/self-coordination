# Self-Coordination — reports & figures

Every write-up and plot from the self-coordination thread, collected in one place.
**All files here are copies.** Nothing was moved or deleted; the originals are
still where they were, and each entry below lists its source path.

The research question, across all four stages:

> Does an LLM coordinate with copies of itself by consulting a **self-model**
> ("what would a copy of me pick?"), or just by finding whatever is **salient**
> in the stimulus — the thing *any* agent would pick? And does it know when it
> can coordinate at all?

---

## PDF reports

These are the compiled, written-up reports. Most were sitting in `~/Downloads`
rather than in either project folder — the ones that also exist in the project
tree are byte-identical, so these are the same documents. Renamed by date for
ordering; original filenames given below.

| file | pages | what it is | original |
|---|---|---|---|
| `pdf_reports/2026-07-19_stage1_partner_identity_summary.pdf` | 4 | **Stage 1 read-out.** "Name Game Coordination under Partner-Identity Beliefs" — the 3-condition belief manipulation (self / mixed / human) × 2 models × 10 trials. A pure belief manipulation: all six seats are the same model on the same prompt. | `~/Downloads/name_game_experiment_summary.pdf` |
| `pdf_reports/2026-08-06_step1-1b_model_specific_focal_points.pdf` | 12 | **Steps 1 + 1b.** Model-specific focal points in one-shot visual coordination, five-pair battery + 30-pair screen; the two models dissociate on 8 of 30 pairs. Contains the key methodological finding: a model that can't find a form rule *defaults to a side and justifies it in form language* — so a 50/50 split must never be read as "no preference" without checking position. | `~/Downloads/LLM_coordination_step1_report.pdf` |
| `pdf_reports/2026-08-07_step1c_targeted_stimulus_screen.pdf` | 4 | **Step 1c.** Targeted screen, 3,660 calls, 27 new pairs, 17 confirmed. Only two stimuli survive all five criteria and both run GPT > Claude; the asymmetry is the main result. Documents a winner's-curse correction (`b_spiral_cw` fell 0.303 → 0.176 on fresh trials). | `~/Downloads/targeted_stimulus_screen_summary.pdf` |
| `pdf_reports/2026-08-07_step2_focal_points_and_self_knowledge.pdf` | 8 | **Step 2 — the most recent report.** Two studies, 6,300 API calls, 0 parse failures. Asks *does a model know its own coordination?* and *does the OTHER model know it better?* | `~/Downloads/coordination_studies_report.pdf` |
| `pdf_reports/2026-08-06_LLM_coordination_master_deck_v5.pdf` | 63 | The whole-project deck — lit review (Bardsley focal points, Halpern & Pass translucent players, Kelsey / Chen & Chen on identity), the identity manipulation, and reasoning-trace excerpts. Broader than self-coordination but the self-play and identity sections are central to it. Latest of five versions in Downloads. | `~/Downloads/LLM_coordination (5).pdf` |

---

## The four stages

| stage | date | write-up | finding |
|---|---|---|---|
| 1 | 2026-07-19 | `writeups/stage1_*.md` | Self-play **hacks** almost any option set through shared salience — car makes (5/5, alphabetical / brand prominence), even random 3-letter strings (5/5; Claude alphabetizes noise, GPT takes first-listed). The **roundabout** design (private per-seat rotation + mirror) is unhackable by construction: **0/10 leaks**, and still 0/10 even when the convention is devalued to a 5× incentive to switch. |
| 2 | 2026-07-30 | `writeups/stage2_selfcoord_identity.md` | **Coordination is set by the stimulus.** Identity moves it **+0.046** (95% CI −0.024 to +0.124, p = 0.10) — positive in both runs and on both matched stimuli, but underpowered. The `self` framing changes the model's *vocabulary* (37% introspective language vs 0% elsewhere), not its *procedure* (96%+ salience-hunting in every condition). |
| 3 | 2026-08-01 | `writeups/stage3_confidence_calibration.md` | **Neither model knows when it can coordinate**, and it misses in both directions — underconfident where coordination is perfect, overconfident on pure noise. |
| 4 | 2026-08-02 | `writeups/stage4_partner_specific.md` | The battery contains **model-specific focal points**: `inkblot` is GPT-only (self-advantage +0.47), `rot` is Claude-only (+0.12); `proto`/`nd2` are shared, `mirror`/`noise` universally flat. |

**The core tension this leaves open:** the repeated game (stage 1) says self-framing
drives convention-breaking 10/10; the one-shot probe (stage 2) says identity does
almost nothing. Either the effect lives in the repeated/strategic setting, or the
stage-1 result was salience-hacking.

---

## Figures

Stages 2–4 ship as both PNG and PDF (PDF keeps text vector). Stage 1 is PNG only —
no PDF was ever exported for those.

| file | what it shows | copied from |
|---|---|---|
| `figures/stage1_hackability_plot.png` | hackability across option sets, both models | `LLM_Coordination/Name_game_experiment/figures/` |
| `figures/stage1_hackability_gpt.png` | same, GPT alone | ″ |
| `figures/stage1_hackability_claude.png` | same, Claude alone | ″ |
| `figures/stage1_hackable_stimuli_gallery.png` | the option sets that got hacked | ″ |
| `figures/stage1_hack_and_solution.png` | the hack and the roundabout fix, side by side | ″ |
| `figures/stage2_identity_vs_salience.{png,pdf}` | identity × stimulus; **panel C** is the direct contrast (bootstrap CI + one-sided permutation test) | `source/stage_figures/` |
| `figures/stage3_confidence_calibration_summary.{png,pdf}` | the one-panel stage summary | `source/stage_figures/` |
| `figures/stage3_confidence_calibration_detail.{png,pdf}` | the fuller original calibration analysis | `source/confidence_calibration.*` |
| `figures/stage3_stimulus_gallery_4opt.png` | the proto4 / noise4 stimulus battery | `source/stimuli/gallery_4opt.png` |
| `figures/stage4_partner_specific_summary.{png,pdf}` | the one-panel stage summary | `source/stage_figures/` |
| `figures/stage4_coordination_matrix.{png,pdf}` | 4-panel GG / CC / GC match matrix + self-advantage | `source/partner_specific_coordination/` |
| `figures/step1_stimulus_battery_30pairs.pdf` | the 30-pair screening battery | `~/Downloads/stimulus_battery_30pairs.pdf` |
| `figures/step1b_screen_findings.pdf` | dissociation CIs + the form-vs-side diagnostic | `~/Downloads/step1b_screen_findings.pdf` |
| `figures/step2_calibration_self_vs_auditor.pdf` | predicted vs actual coordination, self against auditor | `LLM_Coordination/…/calibration_output/` |

## Write-ups

| file | copied from |
|---|---|
| `writeups/00_project_overview.md` | `Self_Coordination/README.md` |
| `writeups/stage1_hack_car_makes.md` | `LLM_Coordination/…/experiments/2026-07-19_hack_car_makes/README.md` |
| `writeups/stage1_hack_random_strings.md` | `…/2026-07-19_hack_random_strings/README.md` |
| `writeups/stage1_roundabout_solution.md` | `…/2026-07-19_roundabout_solution/README.md` |
| `writeups/stage1_roundabout_devalued.md` | `…/2026-07-19_roundabout_devalued/README.md` |
| `writeups/stage2_selfcoord_identity.md` | `Self_Coordination/experiments/2026-07-30_selfcoord_identity/README.md` |
| `writeups/stage3_confidence_calibration.md` | `…/2026-08-01_confidence_calibration/README.md` |
| `writeups/stage4_partner_specific.md` | `…/2026-08-02_partner_specific_coordination/README.md` |
| `writeups/stage4_partner_specific_methods.md` | `source/partner_specific_coordination/README.md` — the detailed methods (match-from-marginals derivation, bootstrap scheme, generic-framing caveat) |
| `writeups/stage4_prompt_templates.md` | `source/partner_specific_coordination/prompt_templates.md` |

---

## Notes on scope and caveats

- **The stage table above stops at Aug 2; the PDF reports run to Aug 7.** The
  Step 1 / 1b / 1c / 2 reports are a later study line — stimulus screening for
  model-specific focal points, then a self-knowledge study — that isn't reflected
  in the stage-numbered write-ups or the project README. The Step 2 report is the
  current frontier of the work.
- **Stage 1 lives in a different project folder.** It predates the Aug-4 split and
  still sits in `~/Desktop/Coordination/LLM_Coordination/Name_game_experiment/`.
  It is included here because it is the first stage of this thread; the four
  experiments chosen are the ones scoped to self-coordination in the Claudine tab
  (the two hacks + the two roundabout runs). Delete `stage1_*` if you want this
  folder to cover only the post-split project.
- **The write-ups' internal links don't resolve from here.** Each one refers to its
  own `code/` and `data/` subfolders, which stayed in the original experiment
  folder. Use the source paths in the tables above to get back to them.
- **Data and code were not copied** — only reports and plots, as asked. Result
  tables that arguably straddle the line (`coordination_matrix.csv`,
  `followup_trial_design.csv`, `bootstrap_draws.csv`) stayed in
  `source/partner_specific_coordination/`.
- **Stage 2's pooled n = 48 rests on an unverified assumption** — the CSVs don't
  store the prompt, so it is not confirmed that the `self`/`neutral` opener wording
  was identical across runs `150646` and `154134`. Settle this before the pooled
  estimate goes in a manuscript.
- **Stage 3 is heavily censored** — the safe grid {3,5,7,9} doesn't bracket the
  switch point; 10 of 12 revealed-confidence points are censored.
- **Stage 4's matrix is generic-framing only** — the choices were elicited under
  "another instance of you", not a named GPT-vs-Claude partner. It is an
  exploratory first matrix; see the methods write-up.
