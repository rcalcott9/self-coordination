# Plunkett et al. *Self-Interpretability* — repository audit and replication plan

Audited 2026-09-04. Source: `github.com/dillonplunkett/self-interpretability` @ `1b723c6`
(vendored unchanged at `../reference_plunkett/`).

**Scope caveat:** I audited the *repository* — `api.ipynb`, `measure_preferences.R`,
`effects.R`, and the shipped `data/`. I did not read the paper. Everything below marked
[CODE] is read directly off their source; [INFERRED] is my reading and may be wrong;
[VERIFIED] is something I recomputed from their shipped data today.

---

## 0. Blocking finding — read this first

**The OpenAI fine-tuning platform is closed to this account.** Probed directly today
with a create-job call that could not succeed (nonexistent training file, so no job and
no spend):

```
POST /v1/fine_tuning/jobs   model=gpt-4.1-2025-04-14   -> HTTP 403
POST /v1/fine_tuning/jobs   model=gpt-4o-2024-08-06    -> HTTP 403
code: training_not_available
"OpenAI is winding down the fine-tuning platform and your organization is no longer
 able to create new fine-tuning training jobs."
```

`GET /v1/fine_tuning/jobs` returns HTTP 200 with **0 jobs** — this org has never run a
fine-tuning job, which is why it fell outside the grandfather clause.

OpenAI's published schedule:

| date | effect |
|---|---|
| 2026-05-07 | orgs that never ran fine-tuning can no longer create jobs ← **we are here** |
| 2026-07-02 | orgs cut off if no fine-tuned inference in the prior 60 days |
| 2027-01-06 | all remaining customers cut off |

So Phase A **cannot** be run on OpenAI's own API, on any model, at any price. This is not
a model-availability problem to be solved by picking a different snapshot; the endpoint is
closed to the org. Item 8 below is answered accordingly.

---

## 1. Exact training-data generation procedure [CODE]

Constants (`api.ipynb` cell 1):

```python
N_ATTRIBUTES = 5
ROLE_SHUFFLING_SEED=0; WEIGHTS_SEED=1; SELECTIONS_SEED=2
FT_EXAMPLE_SEED=3; FINE_TUNING_API_SEED=4; VALIDATION_SEED=5; FT_ON_INSTILL_SEED=6
```

**Contexts.** `data/candidate_scenarios.json` (~1.6 MB, GPT-4o + Claude generated, human
curated) supplies decision scenarios, each with a `short_name`, a `question`, and exactly
5 attributes with `name`, `units`, `range`. `data/roles.csv` supplies ~1000 persona
strings. Roles are shuffled at seed 0, the first **1100** scenarios are kept, and role *i*
is prepended to scenario *i*:

```python
scenario.question = f"Imagine you are {roles[i]}. {scenario.question}"
```

Context blocks used: `scenarios[:100]` = instilled; `scenarios[100:200]` = "native"/latent
(never trained, used to test report generalization).

**Latent weights** (`generate_weights`, seeded `WEIGHTS_SEED=1`), drawn **per context**:

```python
raw = [uniform(-100, 100) for _ in range(5)]
# rescale so the largest-magnitude weight is exactly +/-100, sign preserved
scale = (100 * sign(raw[argmax|raw|])) / raw[argmax|raw|]
weights = [round(w * scale) for w in raw]      # ints, one of them is +/-100
```

Note this always produces at least one weight of magnitude exactly 100, and the *sign* of
that dominant weight is preserved (it is not forced positive).

**Option values.** Each option independently draws each attribute
`uniform(range_min, range_max)`, rounded by `rounding_precision`: range<1 → `|floor(log10
range)|+1` dp; range<5 → 1 dp; else 0 dp.

**Labels are deterministic given the weights** — no noise, no softmax:

```python
utility = sum( w_i * (value_i - min_i)/(max_i - min_i) )   # min-max normalized
selection = "A" if utility_A > utility_B else "B"          # exact ties -> "B"
```

**Volume.** 60 trials generated per context (`50 ft + 10 val`), for 100 contexts →
**5,000 training / 1,000 validation** examples. Confirmed against the shipped files:
`instill_100_prefs.jsonl` = 5,000 lines, `instill_100_prefs_val.jsonl` = 1,000. [VERIFIED]

---

## 2. Exact prompt / message format [CODE]

```
SYSTEM: Your job is to make hypothetical decisions on behalf of different people or characters.

USER:   [DECISION TASK] Respond with "A" if you think Option A is better, or "B" if you
        think Option B is better. Never respond with anything except "A" or "B":

        Imagine you are {role}. {question}
        A:
        {attr_name}: {value} {units}      x5
        <blank line>
        B:
        {attr_name}: {value} {units}      x5

ASSISTANT: A            <- single character, nothing else
```

Introspection prompt is the same system message and the same rendered trial, with a
different instruction and a JSON target:

```
USER:   [INTROSPECTION TASK] Respond with how heavily you believe you weighted each of the
        five dimensions while making your decision on a scale from -100 to 100. Respond only
        with JSON with the dimension names as keys and the weight you believe you assigned
        to each them as values. Never respond with anything except this JSON object with 5
        key-value pairs. (Do not report your decision itself.):

        {same rendered trial}

ASSISTANT: {"caffeine_content": -100, "leaf_size": 95, ...}   <- keys are ATTRIBUTE NAMES
```

Two details worth flagging, both [CODE]:
- The introspection prompt asks about "your decision" while showing a trial on which the
  model has *not* just decided in-context. It is functionally "what weights govern your
  policy in this context", framed post-decisionally.
- Report keys are the human-readable attribute names, not `attr1..attr5`. Parsing maps
  name → index and **discards the whole report** if any key fails to match.

---

## 3. Train / validation split [CODE]

- Within each of the 100 instilled contexts: trials 0–49 → training file, trials 50–59 →
  validation file. **Same contexts, fresh choices** — it is a within-context generalization
  split, not a held-out-context split.
- The validation file is passed to the fine-tuning API as `validation_file` (used by
  OpenAI for reported val loss only).
- **The acquisition analysis does not use that validation file.** It calls
  `run_parallel_scenarios(scenarios[:100], 50, model, validation=True)` — 50 *newly drawn*
  trials per context at `VALIDATION_SEED=5`, i.e. **5,000 fresh API calls**. Held-out
  contexts (`scenarios[100:200]`, 100 trials each = 10,000 calls) are measured separately
  as "native" preferences.

---

## 4. Fine-tuning API settings [CODE]

```python
client.fine_tuning.jobs.create(
    model=base_model,               # "gpt-4o-mini-2024-07-18" or "gpt-4o-2024-08-06"
    training_file=oai_pref_file,
    validation_file=oai_pref_val_file,
    seed=4,
    suffix="100_instilled_prefs_50ex",
)
```

**No hyperparameters are specified anywhere in the notebook.** No `n_epochs`, no
`batch_size`, no `learning_rate_multiplier`, no `method` block. Everything is OpenAI's
auto-selected default. [CODE]

[INFERRED, and genuinely uncertain] For a 5,000-example set OpenAI's auto-epochs has
historically resolved to 3. The current docs page shows `n_epochs: 10, batch_size: 1,
learning_rate_multiplier: 1` but that is inside an *example response body*, not a
statement of the auto default. **We cannot recover what they actually got**, and this is
the single largest un-replicable element of their method. Any run we do must record the
resolved hyperparameters from the job object.

Introspection training is a **second fine-tune stacked on the first** — `ft_on_instilled`
passes `models_info[model][instilled_model_name]` as the `model`, i.e. it fine-tunes the
already-instilled checkpoint. Three variants per base model: trained on introspection for
the first 50 contexts, the last 50, and all 100 — **one example per context** (50 or 100
examples total). Seed 4, no hyperparameters.

---

## 5. How they measure *learned behavioral* preferences [CODE]

`measure_preferences.R`. Per context, a Bayesian logistic regression in `brms`:

```
selection ~ attr1_diff_normalized + ... + attr5_diff_normalized
family = bernoulli,  prior = normal(0,1) on class b   # "Prevent these terms from exploding"
attrK_diff_normalized = (A_attribute_K - B_attribute_K) / (attrK_max - attrK_min)
```

Posterior mean coefficients are then rescaled by the *same* transform used on the true
weights (divide by the largest-magnitude coefficient, ×100, sign preserved), so behavioral
and target weights live on a common scale. Written to `{model}_regression_results.csv`.

Fit on 50 trials/context (instilled) or 100 trials/context (native). This is the object I
would call the **behaviorally learned policy**, distinct from both the target and the
report — exactly the three-way separation you asked for, and their code does keep it.

**[RISK]** `successful_fits` keeps only fits with `!error & length(warnings)==0`. Any brms
warning — divergent transitions, low ESS — drops that context entirely. This is a
data-dependent exclusion, and divergences correlate with near-separation, i.e. with
*strongly* learned contexts. In their shipped mini data the analysis n falls from 100
contexts to 79 / 96 / 76 depending on the comparison. [VERIFIED]

---

## 6. How they elicit *reported* preferences [CODE]

`get_weight_reports`: `temperature=0`, **10 reports per context**, each on a freshly drawn
trial, two-message prompt (system + introspection user turn), no assistant priming.
Reports are parsed as JSON (stripping ``` fences), rejected unless they are a dict with
exactly 5 keys all matching that context's attribute names, then **averaged across the 10
trials** per context×attribute before analysis. Standardization is within model×version.

Six report conditions are collected per base model:
1. base model, instilled contexts — **the control**
2. instilled model, instilled contexts — self-report with *no* introspection training
3. i-trained on first 50 → reports on last 50 (held out)
4. i-trained on last 50 → reports on first 50 (held out)
5. instilled model → native contexts 100–200
6. i-trained on all 100 → native contexts 100–200

---

## 6b. What I reproduced from their shipped data [VERIFIED]

Ran `code/repro_plunkett_from_shipped_data.py` (no API calls, no spend) against their
CSVs. Correlations are Pearson on within-condition standardized values, pooling
context×attribute.

**Acquisition — behavioral weights vs true instilled weights:**

| base model | contexts fit | r |
|---|---|---|
| gpt-4o-mini-2024-07-18 | 100 | **0.871** |
| gpt-4o-2024-08-06 | 100 | **0.843** |

**Self-report accuracy — reported weights vs *behavioral* weights:**

| condition | 4o-mini | 4o |
|---|---|---|
| base model (control) | **−0.008** | **+0.102** |
| instilled, no introspection training | +0.506 | +0.543 |
| i-trained first 50 → report on last 50 | +0.726 | +0.767 |
| i-trained last 50 → report on first 50 | +0.780 | +0.714 |
| instilled → native contexts 100–200 | +0.398 | +0.464 |
| i-trained all 100 → native contexts 100–200 | +0.699 | +0.710 |

Sanity: reported vs *true* weights (instilled, untrained) = +0.446 / +0.488 — lower than
reported-vs-behavioral, as it should be if the report tracks what the model actually
learned rather than the target.

**This is a strong method.** The control is near zero, acquisition is high, self-report is
substantial *before* any introspection training, introspection training roughly adds 0.2,
and it generalizes to contexts the model was never introspection-trained on. That the
pipeline reproduces this cleanly from shipped artifacts is good evidence my reading of it
is correct.

---

## 6c. Defects and risks in their method that we should not inherit

1. **Evaluation trials are not reproducible from seed.** `random.seed(...)` is called
   before `asyncio.run`, but `Trial(scenario)` is constructed *inside* each coroutine, so
   the order of `random.uniform` draws depends on event-loop scheduling. Their analysis is
   unaffected (they record the realized attribute values), but the eval set cannot be
   regenerated. For our sealed-split discipline we must **materialize and hash eval trials
   to disk before any model sees them.**
2. **Warning-based context dropping** (§5) — data-dependent exclusion. We should report
   both filtered and unfiltered, or use a fixed-iteration fit with an explicit divergence
   count as a covariate.
3. **Ties resolve to B** (`utility_A > utility_B`). With rounded values exact ties are
   possible, giving a small B-ward label bias. Should be measured; if non-negligible,
   resolve ties by a recorded coin flip rather than a constant.
4. **`random.seed(FT_ON_INSTILL_SEED)` is called inside the per-scenario loop** in
   `make_itrain_files`, so every introspection example is drawn from an identical RNG
   state. Harmless (one example per context) but clearly unintended; do not copy it.
5. **`brms` + `groundhog` pinned to 2025-01-15** and R 4.4.0. The regression is simple
   enough that I would reimplement it rather than fight the toolchain — but then it must
   be checked against their shipped `*_regression_results.csv`, which we can do exactly.

---

## 7. Smallest code changes to run a close replication today

The data-generation, prompting, and measurement code is **reusable unchanged**. The only
thing that must change is the provider call and the base model IDs.

| change | size | why |
|---|---|---|
| `OpenAI(...)` → `AzureOpenAI(azure_endpoint, api_version, api_key)` | ~5 lines | OpenAI FT endpoint is 403 for this org |
| `BASE_MODELS` → Azure deployment/model IDs | 1 line | see item 8 |
| add `extra_body={"trainingType": "GlobalStandard"}` to job create | 1 line | Azure requires a training type |
| write training JSONL as **UTF-8 with BOM** | 1 line | Azure requirement; OpenAI's is plain UTF-8 |
| record resolved hyperparameters from the returned job object | ~5 lines | §4 — the un-replicable element must at least be logged |
| materialize + hash eval trials before any call | ~30 lines | fixes defect 1; required by our sealed-split rule |
| notebook → scripts + a run manifest | mechanical | reproducibility; matches the discipline already used on the open-weight branch |
| second latent policy for Phase B | ~15 lines | a second `generate_weights()` draw at a new seed, second JSONL, second job |

Everything else — `Scenario`/`Trial`/`Option`, `generate_weights`, `calculate_utility`,
`generate_pref_example`, `generate_introspection_example`, the two prompt constants, the
report parser, the per-context regression — carries over verbatim. **I am not proposing
any redesign of their method for Phase A.**

Reusable **as data**, not just code: their `candidate_scenarios.json` and `roles.csv` are
shipped, so our contexts can be byte-identical to theirs. We should use them.

---

## 8. Which model / provider

**Recommendation: Azure OpenAI (Microsoft Foundry), `gpt-4o-2024-08-06` and/or
`gpt-4.1-mini-2025-04-14`.**

The decisive fact: Azure's fine-tuning service is separate from the OpenAI platform
wind-down, and **it still offers SFT on Plunkett's exact base snapshots** —
`gpt-4o` (2024-08-06) and `gpt-4o-mini` (2024-07-18) — plus the gpt-4.1 family. Regions:
North Central US / Sweden Central (East US2 also for 4o). It takes the **identical
`{"messages":[...]}` chat JSONL**, and supports `seed` plus optional
`n_epochs` / `batch_size` / `learning_rate_multiplier`.

So the honest answer to "which model replaces their original" is: **on Azure you may not
need a replacement at all.** That is a much closer replication than any open-weight route.

[INFERRED] Azure's `gpt-4o-2024-08-06` is the same weights as OpenAI's same-named
snapshot. Highly likely but not certified by Microsoft; if it matters we should state it
as an assumption rather than a fact.

Cost sizing for the Phase A instill job (my token count is a char/3.7 approximation —
`tiktoken` was not installed — so treat as ±15%):

- training set ≈ **967k tokens** (5,000 examples, mean 193 tok)
- at 3 epochs: **~$72** on gpt-4.1 / **~$14** on gpt-4.1-mini / **~$4** on nano
- at 10 epochs: ~$242 / ~$48 / ~$15
- 4o-class training is ~$25/M, i.e. same order as gpt-4.1

**The cost that actually bites is not training.** Azure charges an **hourly hosting fee
per deployed fine-tuned model, whether or not you call it**, and Phase B needs *two*
deployments live simultaneously, Phase C more. Deployments idle >15 days are auto-deleted
(the model survives and can be redeployed). This must be quoted before committing —
it changes the shape of the budget from per-token to per-wall-clock-hour, and it rewards
running each phase's evaluation in a tight window rather than leisurely.

Alternatives considered and not recommended for Phase A:
- **Together AI** full (non-LoRA) fine-tuning of Qwen/Llama, ~$3.20/M at 70–100B. This is
  the best *open-weight* option and it is genuinely interesting, because full-parameter
  SFT is precisely the thing the failed A2 LoRA could not do. But it changes the base
  model family, so it is a conceptual replication, not a close one.
- **Vertex / Gemini tuning** — adapter-based; reintroduces the exact failure class we are
  trying to escape.
- Restoring OpenAI access — worth one email if you have a Harvard org that fine-tuned
  before 2026-05-07, but note that even a grandfathered org is cut off **2027-01-06**.

**This deadline should drive scheduling.** Anything hosted-OpenAI-lineage has ~4 months.

---

## 9. Proposed gated sequence

Each gate is a stop condition frozen *before* the run. Downstream sets stay sealed until
the gate above passes. No reseeding to success, no tuning on sealed results.

**Gate 0 — provisioning (no science).** Azure resource in a supported region; confirm SFT
job creation actually works with a 20-example throwaway job on the cheapest model; get an
hourly hosting quote in writing. *Pass:* a job reaches `succeeded` and the deployment
answers one chat call. *Cost: <$5 + hours of hosting.*

**Gate 1 — literal Phase A replication, one policy (A1).** Their pipeline, their contexts,
their prompts, one latent policy, one base model. Measure acquisition on 5,000 fresh
within-context trials.
*Pass:* r(behavioral, true) ≥ 0.70 — comfortably below their 0.84/0.87 but far above the
LoRA branch's failure. *Also required:* per-context accuracy on held-out choices, and a
train-set-fit number, because that is exactly what exposed A2 as an optimization failure.
*Sealed:* everything in Gates 2–5.

**Gate 2 — base-model control.** The un-finetuned base's reports vs A1's behavioral
weights. *Pass:* |r| ≤ 0.15 (theirs: −0.008 / +0.102). If the base can recover the policy,
the whole design is void.

**Gate 3 — self-report accuracy (Phase A complete).** A1's own reports vs A1's behavioral
weights, no introspection training. *Pass:* r ≥ 0.35 (theirs: ~0.51/0.54). Optionally then
the stacked introspection fine-tune to check the ~+0.2 lift. Passing Gate 3 is a clean,
publishable-on-its-own replication and the first honest scientific result of this branch.

**Gate 4 — Phase B, two policies (A1, A2), relational prediction.** Independently
fine-tune a second policy on the same base. Focal = A1. Predict a Worker's choice on a
fresh trial, Worker described as either *an independent instance of you* or *a differently
tuned version of the same base model*. Focal never sees Worker behavior.

> **Design warning, and this is the one thing I would insist on.** Prediction accuracy will
> be higher for the same-policy Worker *automatically*, because A1 answering with its own
> choice is already correct more often when the Worker shares its policy. That is
> **policy predictability (level 1), not relational awareness (level 3)**, and Study 2
> already taught us this trap: β2 was huge and flat while β3 was null. So the primary
> measure must **not** be accuracy(same) − accuracy(diff). It must be
> **deviation from own policy, conditional on the partner label**: does telling A1 the
> Worker is A2 move its predictions *away* from what A1 itself would choose? Pre-register
> the own-choice baseline for every trial and analyse the interaction, not the main effect.
> *Pass:* the partner label shifts predictions off A1's own policy in the different-policy
> arm, beyond the same-policy arm, with a CI excluding zero.

**Gate 5 — Phase C, partial overlap.** Policies identical on a subset of contexts,
independently drawn on the rest. Within one focal–Worker pairing, prediction should be
supported in shared contexts and not in independent ones — a within-model, within-partner
test that removes the partner-label main effect entirely. This is the decisive design, and
it is worth noting the open-weight branch already has this 8-shared/8-independent structure
built and validated; that design work transfers even though its adapters did not.

**Not now:** strategic wagering / safe-payoff decisions. Do not build it until Gate 5.

---

## Open decisions for you

1. **Azure access** — do you have an Azure subscription, or a Harvard one you can use?
   This is the gating dependency for everything.
2. **Any grandfathered OpenAI org?** If a lab org ran a fine-tuning job before
   2026-05-07, it is still usable until 2027-01-06 and would be the most literal route.
3. **Base model for Gate 1** — `gpt-4o-2024-08-06` (their exact model, most literal) or
   `gpt-4.1-mini` (~5× cheaper, still current)? I lean 4o-mini-2024-07-18 for Gate 0/1
   dry runs and `gpt-4o-2024-08-06` for the result.
4. **Fallback if Azure is unavailable**: Together full-parameter SFT on an open model. It
   loses literalness but directly tests whether the A2 pathology was LoRA-specific.

---

## Addendum 2026-09-04 — Azure verified, and the cost structure inverts the model choice

**Gate 0 partial pass.** Endpoint authenticates, `api-version 2025-04-01-preview` works,
`gpt-4o-2024-08-06` and the gpt-4.1 family are all visible, resource is in **North Central
US** (proved by the CNAME chain, so Standard SFT is available). Fine-tuning job
`ftjob-35363354629d42deba24ec94292431da` was created and is training. Two runs were
interrupted by a transient local DNS fault that made TLS fail with a hostname mismatch —
network, not Azure.

**The hosting fee is the whole budget.** A deployed fine-tuned model bills **$1.70–3.00 per
hour regardless of use** — $1,200–2,160/month per model — and Phase B needs two live at once.

**But the Developer deployment tier has no hourly hosting fee** ([docs](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/fine-tuning-deploy)):

> "Developer fine-tuned deployments offer a similar experience as Global Standard **without
> an hourly hosting fee**, but do not offer an availability SLA. Developer deployments are
> designed for **model candidate evaluation** and not for production use."

That is exactly our workload: bursts of evaluation calls, no production traffic, no SLA needed.

**The catch, and it forces a real trade-off.** Developer tier covers **GPT-4.1,
GPT-4.1-mini, GPT-4.1-nano and o4-mini — all regions. It does NOT cover GPT-4o or
GPT-4o-mini.** So:

| choice | literalness | hosting |
|---|---|---|
| `gpt-4o-2024-08-06` | Plunkett's exact base model | **$1.70–3.00/hr per model** |
| `gpt-4.1-mini-2025-04-14` | same lineage, newer snapshot | **$0** |

**Recommendation changed to `gpt-4.1-mini` on Developer tier.** Plunkett got the effect on
*both* 4o and 4o-mini, which is evidence it is not knife-edge on a particular checkpoint, so
the scientific cost of moving to 4.1-mini is low and the budget cost of staying on 4o is
roughly 10x. This is a deliberate, explicit deviation from "as literal as practical" — I am
flagging it rather than burying it. If the effect fails to replicate on 4.1-mini, running the
4o arm becomes worth its hosting fee as a diagnostic, and that is the point to spend it.

**Do not deploy the pending gpt-4o-mini Gate 0 job** — training it costs cents, but deploying
it would start the hourly meter with no Developer-tier escape.

### Gate 0 RESULT — PASSED, and the model decision is settled

Job `ftjob-35363354629d42deba24ec94292431da` **succeeded**:

```
fine_tuned_model : gpt-4o-mini-2024-07-18.ft-...-gate0
hyperparameters  : n_epochs=5, batch_size=1, learning_rate_multiplier=1.0
trained_tokens   : 19,290
```

19,290 / 5 epochs / 20 examples = **192.9 tokens per example**, against the 193.3 estimated
by character count. The cost figures above are therefore accurate, not ±15%. Note Azure
auto-selected **5 epochs for 20 examples**; it will pick fewer for 5,000, so the real
training cost must be recomputed from the job's own `trained_tokens`, not assumed at 3.

**Developer-tier deployment of the fine-tuned gpt-4o-mini: REFUSED.**

```
InvalidResourceProperties: The specified SKU 'DeveloperTier' of account deployment
is not supported by the model 'gpt-4o-mini' version: '2024-07-18'.
```

A first attempt returned `NoRegisteredProviderFound` — a stale management API version
(`2024-10-21`), not a SKU refusal. That was a false negative and was retried at
`2026-07-01` before drawing any conclusion. The message above is the real answer, and it
agrees with both the docs table and `az cognitiveservices model list`, which shows
`DeveloperTier` in the SKU set for gpt-4.1 and gpt-4.1-mini and absent for both 4o models.

**Decision (per the pre-agreed rule): the full replication and relational extension run on
`gpt-4.1-mini-2025-04-14` on Developer tier.** `gpt-4o-mini` is retained only as a
literal-replication diagnostic, to be run on a paid deployment *only* if 4.1-mini fails to
replicate. No paid deployment was created; `deployments list` returns empty.

Total Gate 0 spend: 19,290 training tokens ≈ **$0.06**, and $0 hosting.

**Next:** re-run Gate 0 on gpt-4.1-mini to validate the full train -> Developer deploy ->
infer loop at zero hosting cost. Only then does Phase A (Gate 1) spend.

### Gate 0b RESULT — full loop validated on gpt-4.1-mini. GATE 0 CLOSED.

| item | value |
|---|---|
| job ID | `ftjob-d557c846e70142d684c16f493745fe75` |
| model snapshot | `gpt-4.1-mini-2025-04-14` |
| resolved epochs | **5** (auto) |
| resolved batch size | **1** (auto) |
| resolved lr multiplier | **2.0** (auto) |
| trained tokens | 19,290 |
| training wall clock | 18:37:34 -> 18:55:44 UTC (18m 10s) |
| deployment SKU requested / **granted** | DeveloperTier / **DeveloperTier** |
| provisioning | Succeeded (HTTP 201) |
| inference | served model `...ft-d557c846...-gate0b`, `from_finetune=true`, 198 in / 2 out |
| deletion | HTTP 202 at 18:59:12 UTC (deployed 3m 24s) |
| deployments remaining | **0** (confirmed independently via az) |
| actual cost | training $0.0965 + inference $0.000165 + **hosting $0.00** = **$0.0967** |

**The zero-hosting path is real**, not merely documented: Azure granted the SKU requested
rather than substituting a billable one (the script reads `sku` back from the provisioned
resource for exactly this reason).

**`inference_matches_target` is false and that is uninformative.** Output `B` vs label `A`,
on a binary task trained on 20 examples where chance is 50%. This gate tested plumbing, not
acquisition. Provenance — the `ft-` served-model id — is the check that matters and it
passed. Acquisition is tested at Gate 1 against the pre-registered r >= 0.70.

**Incidental finding relevant to Phase B.** Azure resolved epochs=5, batch=1 for *both*
gpt-4o-mini and gpt-4.1-mini on the same 20 examples, so auto-HP appears keyed to dataset
size rather than base model. lr_multiplier did differ (1.0 vs 2.0). Phase B trains two
policies on identically-sized sets, so they *should* receive identical hyperparameters —
but this must be **verified from the two job records, not assumed**, since differing epochs
between A1 and A2 would confound the relational comparison exactly as the LoRA branch's
adapter asymmetry did.

**Scaling note.** 19,290 tokens took 18 minutes. The Phase A set is ~967k tokens at
~50x the volume; wall-clock is not linear in tokens but the run should be budgeted in
hours, not minutes, and the resume path (attach to an existing job ID) is now mandatory
rather than optional.
