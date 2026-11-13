# Self-Coordination

Do language models know when they can coordinate with a copy of themselves, and do
they use that knowledge?

Two copies of the same model face a coordination problem: pick the same option and
both win. The questions this project asks:

1. **Own-coordinability knowledge (Study 1).** Can a model tell which items it would
   match a copy of itself on, better than an outside model predicting it?
2. **Partner description (Study 2).** Does it bet less on coordination when told its
   partner is a *different* model, and is that adjustment item-specific?
3. **Converting reliability into payoff (Study 3).** In a Stag Hunt where joint play pays
   off only if both match, do copies reach the payoff a perfect self-model would earn?

Models: GPT-5.5, Claude Opus 5, Fable 5.1 and fine-tuned Qwen checkpoints (trained on
the Plunkett et al. choice data). All raw responses, frozen designs and analysis code
are included.

**Start here:** [`paper_assembly_20261010/docs/METHODS_RESULTS_DRAFT.md`](paper_assembly_20261010/docs/METHODS_RESULTS_DRAFT.md)
— the methods and results draft, with every number labelled by provenance
(frozen / planned / sensitivity / exploratory). Figures are in
[`paper_assembly_20261010/figures/`](paper_assembly_20261010/figures/).

## Main findings (draft, not peer reviewed)

| study | finding |
|---|---|
| **1** | Reliability judgements track the model's own copy–copy agreement in all three models. For GPT-5.5 this holds after controlling for an outside auditor's prediction; for Opus 5 it does not, and at high reasoning the auditor predicts Opus better than Opus predicts itself. Forecasts about the *other* model sit close to the predictor's own choices (projection). |
| **2** | Describing the partner as a different model lowers PLAY in every model and configuration (e.g. GPT-5.5 low, low-reliability items: .45 → .27). Neither assay shows that models apply their own policy selectively to partners who share it. |
| **3** | Copies fall short of the self-model benchmark for Opus, Fable and Qwen (thinking off), but not reliably for GPT. They lose in different ways: GPT by mismatching, Opus by abstaining. Later Stag Hunt and Prisoner's Dilemma pilots (Oct 2026) are exploratory. |
| early | Partner *identity* framing changes vocabulary, not procedure: coordination is driven by stimulus salience. Models are poorly calibrated about when they can coordinate. Some focal points are model-specific. |

Limitations are listed at the end of the draft.

## Repository map

Folders are named `<study>_<date started>`. Each is self-contained: design (frozen
prompts and hashes), code, raw responses and analysis.

**Paper and reports**
- `paper_assembly_20261010/` — methods/results draft, final figures and tables, errata. No API calls; rebuilt from data on disk.
- `Study1_frontier_package_20261008/` — reproducible Study 1/1b package. `reproduce.sh` regenerates the reported outputs; `home/` is the frozen mirror of the original folders it runs against.
- `study1_figure_package_20261013/`, `study1_figure_data_20261009/`, `study2_figure_data_20261013/` — figure inputs.
- `reports/` — earlier write-ups, decks and PDF reports.
- `COMPLETION_LEDGER_20261009.md` — dated log of every run: authorisation, budget, spend and result.

**Study 1: own-coordinability knowledge**
- `study1_frontier_min_20261007/`, `study1b_crossed_object_20261007/` — frontier models, low reasoning (primary).
- `study1_highreason_20261009/` — high-reasoning replication.
- `study1_hp_replication_20260905/` — earlier single-model GPT-5.5 confirmatory replication.
- `study_policy_convergence_20260909/` — frame calibration (agreement estimates for the 41 VIS-FRAME arrays).

**Study 2: partner description**
- `study_playpass_gpt/`, `study2_4opt_20260830/`, `study2_partner_policy_20260822/` — PLAY/PASS under COPY vs DIFFERENT partner.
- `study2_relational_prediction_20260912/` — relational prediction (null).
- `STUDY2_OUTLINE_EVIDENCE_MAP_20261013.md` — what the completed data can and cannot answer.

**Study 3: Stag Hunt and payoff**
- The primary Study 3 runs (two-model, Fable and Qwen Stag Hunt pilots) live outside this repository; their per-item results are in `paper_assembly_20261010/tables/study3_*`.
- `study4_relational_staghunt_20260908/` — stimulus discovery: building and screening the four-object arrays used as coordination items.
- `study3a_feasibility_20261015/`, `study3a_baseline_20261016/`, `study3a_reciprocal_confidence_20261016/`, `study3a_pass5_PROPOSED_20261016/` (run despite the name), `study3_pd_three_condition_20261017/` — exploratory pilots.
- `study3_item_M07_20261013/`, `study3_item_SHAPES_20261014/`, `study3_green_core_20261014/`, `STUDY3_PROTOCOL_PROPOSAL_20261013.md`, `applied_tasks_spec_20261010/` — design work for the next Study 3 items.

**Earlier and supporting work**
- `experiments/` — the first three experiments (Jul–Aug 2026), each with code, data and figures; `source/` is the working tree they were built from.
- `policy_specific_self_coordination_20260812_1401/`, `generation_ladder_20260814/`, `confidence_residual_20260830/`, `study3_partner_purchase_20260823/`, `monitored_schelling_20260905/`, `open_set_rendezvous_20260906/`, `selfinterp_replication_20260904/` — fine-tuning, calibration and replication work that fed the main studies.

## The first three experiments (Jul–Aug 2026)

| launched | experiment | finding |
|---|---|---|
| `2026-07-30` | [selfcoord_identity](experiments/2026-07-30_selfcoord_identity/) | **Partner identity does nothing.** Coordination is set by the stimulus. The `self` framing changes the model's *vocabulary* (37% introspective language vs 0% elsewhere) but not its *procedure* (96%+ salience-hunting in every condition). |
| `2026-08-01` | [confidence_calibration](experiments/2026-08-01_confidence_calibration/) | **Neither model knows when it can coordinate.** It is underconfident where coordination is perfect and overconfident on pure noise. |
| `2026-08-02` | [partner_specific_coordination](experiments/2026-08-02_partner_specific_coordination/) | The battery contains **model-specific focal points**: `inkblot` is GPT-only (self-advantage +0.47), `rot` is Claude-only (+0.12). |

Rebuild their figures:

```bash
cd source/stage_figures
Rscript fig_stage2_identity.R
Rscript fig_stage3_calibration.R
Rscript fig_stage4_partner_specific.R
```

## Notes

- Files over 50 MB (two posterior-predictive arrays) and the third-party
  `reference_plunkett` clone are not included.
- Many scripts use absolute paths from the original machine; the Study 1 package's
  `reproduce.sh` is the sandboxed, path-independent route.
- Status: work in progress. Numbers may change before publication.
