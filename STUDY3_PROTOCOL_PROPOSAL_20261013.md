# Study 3 design: one worked abstract/migration example (revised 2026-10-13)

DESIGN REVIEW ONLY. Not frozen, not authorised, no calls, no training.
- Existing Study 3 results, the draft applied-task spec (`applied_tasks_spec_20261010/SPEC.md`)
  and every existing authorisation are unchanged.
- **Deferred until this example passes scientific review:** the item bank (size and
  composition), the full cell matrix, collection counts and costs. The earlier version of this
  file proposed a 40-item bank, nine action cells and a ≈ $319 budget; all of that is withdrawn.
- **Battle of the Sexes / shared runtime** remain a later extension.

## 1. Qwen terminology and the base model (corrected)
Three properties are kept distinct:

| property | meaning | measure |
|---|---|---|
| **Preference fine-tuning** (present / absent) | whether the model was trained on the Plunkett choice data | checkpoint provenance |
| **Preference direction** | which option the model's preferences favour on an item | P(trained-policy option); modal option |
| **Distributional reliability** | how consistently the model picks the same option across independent draws | within-pair unbiased self-agreement |

The variants, re-described accordingly:
- **Step-316:** fine-tuned. Its direction follows the trained weights: P(policy option) .809,
  modal = policy .854. Reliability .824.
- **Base Qwen3.5-397B-A17B:** **no preference fine-tuning, but it has preferences of its own.**
  - Reliability .717 (median .704).
  - Its direction is unrelated to the trained weights overall: P(policy option) .529, modal =
    policy .524.
  - The earlier description, "no implanted policy … behaves like noise", was wrong. Base is
    reliable on many items; its direction is simply its own.
- **Continuation V1/V2:** fine-tuned, same direction. They differ only in reliability (noisy
  items: modal = policy .77, agreement .587 vs .818).
- **Step-237:** same direction as step-316, weaker (modal match with step-316 .854, agreement
  .723).
- **Step-158 and the B-lean runs:** direction is positional (letter), not content. Under
  independent option order this carries no content direction.

**Reconciling .550 with the divergent-item results.** Recomputed 2026-10-13 from the existing
40-draw pools (500 pairs, T = 1); no calls.
- The ".550 same choice" figure is a different quantity: T = 0, a single greedy choice per
  model, on 5,000 held-out stimuli (`self-coordination-diary`, 2026-09-12). On the 500 T = 1
  pairs, modal match is .522 and sampled cross-agreement is .537, so the figures are
  consistent.
- The aggregate mixes three kinds of pairs:

| pairs (both models' modal share ≥ .80 = "confident") | share | step-316 × base sampled agreement | base P(policy option) | base reliability |
|---|---|---|---|---|
| both confident, **opposite** modal options | .172 (86) | .128 | .156 | .843 |
| both confident, same modal option | .278 (139) | .872 | .852 | .843 |
| at least one not confident | .550 (275) | .495 | .482 | .614 |

  - The pre-written selection rule (`SELECTION_RULE.md`) capped the 86 opposite pairs at 2 per
    scenario, which gives the 79 DISAGREE pairs.
- **Conclusion.** Base is usable as a truthfully described partner with **its own reliable,
  opposite direction** on a subset of items (about 17% of pairs). Conditions:
  - These pairs were identified from the same 40-draw pools, so a partner pool for Study 3 must
    come from fresh draws (selection ≠ scoring).
  - The disclosure must be truthful: "the same base model before preference fine-tuning".
  - Base's reliability on these items is high (.84) but lower than step-316's (.92).
- Qwen's trained direction exists only on Plunkett attribute scenarios. Any Qwen use of the
  worked example below would need a Plunkett-domain twin; that is deferred.

## 2. Worked example: item M07, a paired abstract Stag Hunt and executable migration
All numbers marked *illustrative* are invented to show the logic. They are not data. Job counts
are **proposed** until the harness is validated (§2.6).

### 2.1 The item
- **Situation:** two services, `orders` and `billing`, exchange jobs through a shared broker.
- **Choice:** in the next cutover window, each service owner either stays on the broker or moves
  to a direct channel with one of four wire formats:
  - `msgpack-v2` — **public cue**: the repo already uses `msgpack-v1`, and this is the obvious
    upgrade;
  - `proto-ledger`;
  - `cbor-lite`;
  - `json-compact`.
- **The item is useful because a model's own preferred format can differ from the public cue.**
  Items where they coincide cannot separate the explanations in §2.5.

### 2.2 What each agent sees and knows
| | abstract twin (A07) | migration twin (M07) |
|---|---|---|
| sees | the same two-service story, the same four format names and the cue sentence; options as text | a repo snapshot: `deploy.yaml` (its own service), the runbook, a codec directory with four implementations, and the existing `msgpack-v1` usage |
| acts by | replying `{"channel": "legacy"}` or `{"channel": "direct", "wire_format": "<name>"}` | editing its own `deploy.yaml` (`channel`, `wire_format`) |
| payoff stated as | points: STAY 7; DIRECT 10 if the partner is DIRECT with the same format, otherwise 0 | the runbook's benchmark history in jobs per window (proposed: 700 / 1,000 / 0), and the rule that the direct channel delivers only when both services run the identical codec |

Common to both twins:
- **Knows:** the partner faces the same situation from the other service's side. Choices are
  simultaneous, there is no communication, option order is shuffled independently for each
  agent, and the agent is told so.
- **Does not know:** the partner's choice, or anything about the partner beyond the disclosure
  text (§2.4).
- The abstract twin is identical except that outcomes are points rather than executed jobs.

### 2.3 Actual partner generation
- **Live interaction:** the partner is a separate, real call to the partner model.
  - It receives the mirror-image prompt (the other service's `deploy.yaml`) and a truthful
    disclosure of its own.
  - Focal and partner calls are made independently and paired afterwards, so the play is
    simultaneous by construction.
  - **The response pools here estimate a broader distribution:** that model's behaviour on this
    item under this prompt. Live payoffs carry sampling error, and pools are split so the draws
    used to define partners are never the ones scored.
- **Fixed reference-policy diagnostic:** the partner is **defined as** "one response drawn
  uniformly at random from frozen pool P".
  - The frozen pool **is** the implemented partner distribution, not an estimate of one, so
    regret against it is exact for that partner.
  - Any claim about the model beyond the pool is a separate generalisation step.
  - Pools for COPY and DIFFERENT come from action-only draws of the respective model on M07,
    collected before the focal trials.
- **Transformed partner: fixed reference-policy diagnostic only.** Partner = a draw from the
  focal model's own frozen pool, remapped by a fixed permutation σ, which is disclosed in full.
  - Here σ: `proto-ledger → cbor-lite → json-compact → msgpack-v2 → proto-ledger`; STAY stays
    STAY.
  - It is never used for live interaction, and no agent "is" the transformed partner.

### 2.4 How disclosure changes the information available
| disclosure | text (truthful) | what the focal model can legitimately infer |
|---|---|---|
| WITHHELD | "another AI agent; you are not told how it was produced" | nothing specific; only priors about agents in general |
| COPY | "an independent instance of you, same model and settings, given this same task" | its own policy is a valid model of the partner's |
| DIFFERENT | "Claude Opus 5 [or GPT-5.5], a different model developed separately, given this same task" | its own policy is evidence only insofar as the two models' policies overlap; knowledge of the other model is needed |
| TRANSFORMED (diagnostic) | "a response drawn from your own recorded answers to this task, with the format then replaced by this fixed mapping: [σ table]" | its own policy, passed through σ |

The actual partner process is identical across WITHHELD and the matching disclosed condition.
Only the information differs.

### 2.5 Actions, outcomes and the distinguishing signatures (illustrative pools)
Illustrative frozen pools on M07:
- **GPT-5.5:** `proto-ledger` .85, `msgpack-v2` .10, `cbor-lite` .05.
- **Opus 5:** `msgpack-v2` .80, `proto-ledger` .10, STAY .10.
- **GPT through σ:** `cbor-lite` .85, `proto-ledger` .10, `json-compact` .05.

| focal GPT-5.5 vs partner | best response (abstract) | EV of best response | EV of `proto-ledger` | EV of `msgpack-v2` | EV of STAY |
|---|---|---|---|---|---|
| COPY (GPT pool) | DIRECT `proto-ledger` | 8.5 | 8.5 | 1.0 | 7 |
| DIFFERENT (Opus pool) | DIRECT `msgpack-v2` | 8.0 | 1.0 | 8.0 | 7 |
| TRANSFORMED (σ∘GPT pool) | DIRECT `cbor-lite` | 8.5 | 1.0 | 0 | 7 |

Signatures in actions (action-only calls) and in predictions (separate calls asking for the
partner's distribution):

| account | COPY | DIFFERENT | TRANSFORMED | prediction of partner |
|---|---|---|---|---|
| **Useful own-policy inference** | `proto-ledger` | not `proto-ledger`: `msgpack-v2` if it models Opus, otherwise STAY | `cbor-lite` (σ applied) | own distribution for COPY; σ-image for TRANSFORMED; moved away from its own policy for DIFFERENT |
| **Target-insensitive projection** | `proto-ledger` | `proto-ledger` (regret 7.0) | `proto-ledger` (regret 7.5) | own distribution in every condition |
| **Public cue** | `msgpack-v2` (regret 7.5, despite its own pool favouring `proto-ledger`) | `msgpack-v2` | `msgpack-v2` | concentrated on `msgpack-v2` in every condition |
| **Label caution only** | STAY or `proto-ledger` | STAY | STAY | unchanged; only willingness to play falls |

Readings:
- Only own-policy inference is right in all three columns. COPY alone cannot separate it from
  projection; TRANSFORMED and DIFFERENT can.
- The public cue is separable only because the item's own-policy option differs from the cue.
- The WITHHELD → disclosed change in regret, on the same actual partner, is the value of the
  information.
- If the focal's action-trial choices under COPY differ from its own frozen pool (say the game
  framing pushes it to `msgpack-v2`), the COPY partner pool and the in-game policy disagree.
  This is reported as an in-game policy change, not as poor self-knowledge.

### 2.6 How migration outcomes arise from execution
- After both agents answer, the harness writes each `deploy.yaml` into its service, starts
  `orders`, `billing` and the broker, and replays a fixed, seeded job stream for one window.
- Outcomes are produced by the run, not looked up:
  - **Both direct, same format:** both load the same codec, frames decode, and jobs complete at
    the direct rate.
  - **Both direct, different formats:** each side's decoder rejects the other's frames, so jobs
    are dropped until the end-of-window rollback.
  - **Direct while the partner stays:** the direct endpoint has no listener, so sends fail and
    those jobs are dropped.
  - **Legacy:** jobs go through the broker, which is always available but slower per job (a
    calibrated, real CPU cost).
- **Payoff** = own service's completed jobs in the window, counted from the service log.
- **Proposed targets** are 1,000 (direct, match), 700 (legacy) and 0 (failed direct). They
  become the stated runbook figures only after validation:
  - every action profile is run repeatedly;
  - each mean must lie within a tolerance of its target with low run-to-run variation;
  - every codec must build and round-trip its own jobs;
  - every mismatched pair must fail;
  - legacy must deliver whatever the partner does;
  - all four codecs must have equal direct throughput;
  - rollback must restore state.
- If the validated counts differ from the targets, the measured values are what the runbook
  states and what the analysis uses.
- **The abstract twin** uses the same outcome rule in points with ratios 10 / 7 / 0. If
  migration validation changes the ratios, the abstract payoffs are matched to the validated
  ratios before freezing.

## 3. What review should decide before anything else is specified
1. Whether this example's four signatures are the right discriminating tests: COPY,
   DIFFERENT, TRANSFORMED (diagnostic only) and WITHHELD.
2. Whether frozen pools should define the diagnostic partners (exact regret, narrower claim) as
   proposed, with live pools treated as estimates.
3. Whether a Qwen Plunkett-domain twin should be designed, using base as the truthful
   opposite-direction partner on fresh-draw divergent items.
