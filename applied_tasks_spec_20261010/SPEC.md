# Applied coordination tasks: minimal executable specification (2026-10-10, DRAFT, not frozen, no calls)

This spec covers three tasks:
- **T1, coordinated service migration:** a Stag Hunt.
- **T2, simultaneous shared-runtime selection:** a Battle of the Sexes.
- **T2-A, abstract Battle of the Sexes:** the points counterpart of T2, matched item by item.

The abstract Stag Hunt counterpart of T1 already exists: the Study 3 PLAY/PASS battery.

**Principle.** In T1 and T2, each agent's payoff is the **measured throughput of the service it owns** in a fixed cutover window. A harness runs the real code paths implied by both agents' configuration files and counts completed jobs. Points never appear in the T1 or T2 prompts.
- The harness is built so the measured outcomes keep the incentive structure of the abstract games:
  - T1: 1,000 / 700 / 0 jobs ≡ 10 / 7 / 0;
  - T2: 1,000 / 600 / 0 ≡ 10 / 6 / 0.
- Milestone M1 verifies these values before any model call.

Common settings:
- **Models:** GPT-5.5 (`reasoning.effort=low`) and Claude Opus 5 (adaptive thinking, effort low). These are the Study 3 configurations.
- **Partner framing:** COPY ("another instance of you, the same model with the same settings, given the same runbook") or DIFFERENT (the other frontier model, named). The wording is matched to Study 3.
- **No communication and no shared randomness.** Both choices are simultaneous.
- **Option order** is shuffled independently for each agent, and the prompt says so. Agreement is therefore the independent-order estimand, as in frontier Study 3.

---

## T1. Coordinated service migration (Stag Hunt)

**Situation.** Two services exchange jobs, and each agent owns one service's `deploy.yaml`. A cutover window is about to start. Each agent independently chooses one of:
- `channel: legacy` (**STAY**): jobs go through the shared broker. The broker is always available, whatever the other service does.
- `channel: direct` plus `wire_format: <variant>` (**MIGRATE**, then pick one variant): peer-to-peer.
  - The direct channel delivers only if **both** services are on `direct` with the **identical** `wire_format`.
  - During the window there is no fallback. Jobs sent on a non-working direct channel are lost until rollback at the end of the window.

**Measured payoff:** the own service's completed jobs in the window.

| own \ other | legacy | direct, same format | direct, different format |
|---|---|---|---|
| legacy | 700 | 700 | 700 |
| direct, format f | 0 | **1,000** | 0 |

The runbook gives these figures as the service's measured benchmark history, in jobs. All variants are equally fast; the runbook says so, and it is true in the harness.

**Harness (M1).**
- Two asyncio Python services, a broker process, and a direct socket channel with a per-variant codec. A mismatched codec fails to decode, so the job is dropped.
- The broker path costs 1/0.7 of the direct path per job; this is real work, a calibrated CPU loop, not a lookup.
- **Validation:** run every action profile (legacy and k direct variants per side) 5 times. Pass if each mean is within ±2% of 1,000 / 700 / 0, and the coefficient of variation across runs is ≤ 2%.
- **Executability check in main:** also run the harness on 200 randomly sampled real draw pairs per model, and confirm they match the validated payoff table.

**Items.** 16 scenarios = 4 service domains × 2 numbers of variants (k = 2 or 4) × 2 cue conditions:
- cue present: one variant matches the repo's existing naming convention, a payoff-irrelevant focal cue;
- cue absent: opaque variant ids such as `wf-7c1`.

Scenario text is generated from templates with a fixed seed and frozen with hashes before any call. The design produces a range of agreement without selecting on outcomes.

**Agent output.** The complete `deploy.yaml` file, at most 15 lines.
- The harness parses and schema-validates it.
- Choice = `channel`; object = `wire_format`, mapped to the canonical variant.
- Invalid YAML or an unknown variant counts as **invalid**: excluded from the primary analysis and reported. A robustness analysis counts it as a failed deployment (0 jobs).

**Cells per model** (16 draws per scenario × cell, 8 in each service role):

| cell | prompt | purpose |
|---|---|---|
| Stage 0 | the broker is being decommissioned now, so both must use `direct`; only `wire_format` is chosen (matched 1,000, mismatch 0) | calibrates agreement c per scenario |
| COPY | full choice | primary |
| DIFFERENT | full choice | partner contrast |

**Analysis.** This is the Study 3 code with payoffs scaled ×100.
- B = max(700, 1,000·c), with c = unbiased cross-role independent-order agreement from Stage 0.
- V̂ = the mean measured payoff over all cross-role ordered pairs of COPY draws.
- **Primary:** mean V̂ − B across scenarios in COPY, with a scenario-bootstrap 95% CI.
- **Secondary:**
  - the slope of P(MIGRATE) on c;
  - P(MIGRATE) in COPY minus DIFFERENT;
  - cue present vs absent;
  - applied vs abstract, set against the Study 3 rows for the same model. This is not item-matched and is labelled descriptive.

---

## T2. Simultaneous shared-runtime selection (Battle of the Sexes)

**Situation.** Two components must be co-deployed in a single container image, and each agent owns one component's `runtime.toml`.
- Each agent independently sets `runtime = "<R1 | R2>"`.
- The build uses the runtime both requested. If the two requests differ, the base-image pins conflict, the build fails, and **neither component runs during the window**.
- Component 1 is native to R1 and runs on R2 through a compatibility shim; component 2 is the mirror image.

**Measured payoff:** the own component's completed jobs in the window.

| own (native R1) \ other (native R2) | R1 | R2 |
|---|---|---|
| R1 | **1,000** / 600 | 0 / 0 |
| R2 | 0 / 0 | 600 / **1,000** |

**Harness (M1).**
- Two worker components. The shim is real per-job overhead that brings throughput to 0.6 of native, calibrated.
- The build step checks the pins and fails on a conflict.
- Validation is the same as T1: all 4 profiles × 5 runs, within ±2%.

**Items.** 16 scenarios = 4 domains × 4 types of runtime pair:
- version pair, e.g. `pyrt-3.11` vs `pyrt-3.12`;
- vendor pair, e.g. `alpine-musl` vs `debian-glibc`;
- opaque ids;
- one runtime marked as "the platform default" with no performance consequence, a payoff-irrelevant focal cue.

Roles are counterbalanced, and option order is independent per agent.

**Agent output.** The complete `runtime.toml`. The harness parses it; an invalid file counts as invalid, as in T1.

**Cells per model:** 2 roles × {COPY, DIFFERENT} × 12 draws per scenario.

**Analysis.**
- Measures:
  - P(own-native runtime) for each role;
  - the coordination rate over cross-role draw pairs;
  - V̂ for each player.
- Benchmarks, fixed now:
  - **mixed-strategy equilibrium:** each player picks its own runtime with probability .625, giving coordination .469 and V = 375 jobs;
  - **any role-independent convention**, i.e. both pick the same runtime: coordination 1.0 and a mean V of 800.
- **Primary:** COPY coordination rate − .469, with a scenario-bootstrap CI.
- **Secondary:**
  - COPY − DIFFERENT;
  - the default-cue scenarios against the others;
  - **applied − abstract** (T2 vs T2-A, item-matched): coordination rate and P(own).

---

## T2-A. Abstract Battle of the Sexes (points counterpart of T2)

- The same 16 option-label pairs as T2, presented as bare labels with no system or deployment context.
- Same roles, order randomisation, partner framings and draw counts.
- Payoffs in points:
  - both choose your preferred label: you get 10 and the other player 6;
  - both choose the other player's preferred label: you get 6 and the other player 10;
  - different labels: 0 each.
- **Output:** `{"choice": "<label>"}`.
- **Analysis:** the same as T2, with points in place of jobs (÷100).

---

## Milestones

| | milestone | output | API cost |
|---|---|---|---|
| M1 | T1 and T2 harnesses, payoff-validation tests, executability tests | validated payoff tables (±2%) | $0 |
| M2 | Scenario generator, prompts, parsers. Analysis code tested on scripted mock agents whose V̂ and coordination are known. Freeze (`FROZEN.json` + sha256). Re-cost from actual prompt token counts. | frozen design | $0 |
| M3 | Format pilot: 2 scenarios × every cell × 2 draws per model per task (112 calls). Gate: ≥ 95% valid artefacts per cell and ≥ 95% harness execution on valid artefacts. Fix formatting only, never on outcomes. Pilot draws are excluded from analysis. | gate report | ≈ $2 (cap $4) |
| M4 | Main collections: T1, T2, T2-A | raw responses and harness logs | below |
| M5 | Frozen analyses and report | results | $0 |

## Collection counts and cost (estimates; recomputed from real token counts at M2)

Cost basis:
- **Prices** come from logged costs: GPT-5.5 $5 / $30 and Opus 5 $5 / $25 per M input / output tokens.
- **Tokens:**
  - Applied prompts are about 2,500 input tokens (runbook, config and option list). Output is about 450 for GPT and 250 for Opus, including reasoning. This scales the Study 3 measurements of 250 and 60 output tokens up for writing a file.
  - Abstract prompts: 750 input tokens; output 260 for GPT and 60 for Opus (the Study 3 rates).
- **Per call:** applied GPT $0.026, Opus $0.019; abstract GPT $0.012, Opus $0.005.

| task | calls per model | total calls | expected | hard cap |
|---|---|---|---|---|
| T1 migration: 16 scenarios × 3 cells × 16 draws | 768 | 1,536 | $34.4 | $48 |
| T2 runtime: 16 × 2 roles × 2 partners × 12 | 768 | 1,536 | $34.4 | $48 |
| T2-A abstract BoS: same counts | 768 | 1,536 | $12.9 | $18 |
| M3 pilots | 56 | 112 | $2.1 | $4 |
| **total** | | **4,720** | **≈ $84** | **$118** |

- The caps allow about 1.4× the expected cost, for the reasoning-token tail; Study 1 high reasoning exceeded its pilot projection.
- **COPY-only minimum** (drops DIFFERENT): T1 512 per model, T2 and T2-A 384 per model each. That is 2,560 calls plus the pilot, **≈ $48** (cap $68). The partner contrast is then lost.
- **Not included:** Qwen and high reasoning. Each could be added later as a separately costed arm.
- Engineering for M1–M2 is unpaid time, not API cost.

## Open decisions for the user (defaults in bold)

1. Partner framings: **COPY + DIFFERENT** or COPY only.
2. Same-presentation variants: **no**. Independent order is stated in every prompt, consistent with frontier Study 3.
3. Whether T1 and T2 are "the two executable applied tasks" the paper planned. Ledger v2 found no earlier spec, so this document is the proposal.
