# Complementary-role coordination — design

Successor to the partner-conditional deviation pilot. Tests whether the fine-tuned model
can use awareness of its own learned policy to infer a same-checkpoint partner's
**already-fixed hidden choice** and deliberately take the opposite role.

No new fine-tune. Uses the existing `gpt-4o-mini …-g4omini` checkpoint and the unchanged
`gpt-4o-mini-2024-07-18` base.

---

## 0. Why this design is stronger than matching — the structural point

Let `p` be the Worker's probability of choosing A on an item.

| Focal strategy | joint success P(Focal ≠ Worker) | behaviour as p → 1 |
|---|---|---|
| follow own policy blindly | `2p(1-p)` | **→ 0** |
| choose complement of modal | `max(p, 1-p)` | **→ 1** |
| random | 0.5 | 0.5 |

**The two accounts make opposite predictions as predictability rises.** In a matching
game, following your own policy and reasoning about your partner both produce
convergence, so success alone is uninformative — that is exactly what sank the earlier
coordination pilot. Here, blind policy-following *actively fails* precisely where the
policy is most predictable. The predictability slope is therefore signed, and a positive
slope cannot be produced by the null strategy.

That is the whole reason to run this task.

---

## 1. The confound that actually threatens it

**"Flip whatever I would normally pick" achieves `p² + (1-p)²`** — at p = 0.9 that is
0.82 against an optimal 0.90. Nearly indistinguishable by success rate.

And this is not merely a nuisance heuristic: "the other copy shares my policy, so it
picked what I would have picked, so I pick the other" **is** the correct inference. The
worry is the *cheaper* variant that produces the same behaviour without self-policy
content — "in this task, avoid the obvious-looking option."

These two separate only where the **arbitrary learned policy disagrees with generic
salience**. So the experiment must be built on that subset:

> **policy–salience-divergent items**: the fine-tuned policy strongly favours X, the
> unmodified base model strongly favours Y, and X ≠ Y.

On those items the predictions invert:

| account | Focal should choose |
|---|---|
| complement own **learned policy** | **Y** |
| avoid the **generically salient** option | **X** |

This is the discriminating measurement, and it should carry the primary weight.

---

## 2. Conditions — four, and why the fourth is required

| # | condition | Worker | Focal | tells Focal | role |
|---|---|---|---|---|---|
| 1 | **SAME-FT** | FT checkpoint | FT checkpoint | "another instance of your exact fine-tuned model" | primary |
| 2 | **BASE-CONTROL** | base | base | "another instance of the same base model" | can any model do this at all? |
| 3 | **FT×BASE** | base | FT checkpoint | truthfully, "the unmodified base model" | **identification** |
| 4 | **INFORMED** | FT checkpoint | FT checkpoint | + "the other agent was very likely to choose Option A" | channel check |

**On the fourth arm the brief asks about — include it.** Without FT×BASE, a positive
SAME-FT result is ambiguous between *"the fine-tune exploits its shared policy"* and
*"the fine-tune is simply better at inferring partner behaviour in general."* FT×BASE
holds the Focal constant and swaps only whether the Worker shares its policy, which is
the exact contrast the claim requires. It costs ~480 calls. It is the cheapest thing in
the design that converts an ambiguous positive into an interpretable one.

INFORMED sits on the same items but never enters the SAME-FT vs FT×BASE comparison.

---

## 3. Exact prompts

**Worker** — the ordinary preference task, no coordination framing, no awareness that a
second agent exists:

```
[DECISION TASK] Respond with "A" if you think Option A is better, or "B" if you think
Option B is better. Never respond with anything except "A" or "B":

{item}
```

**Focal** — temporal asymmetry made explicit and unrecursive:

```
Another agent has already independently chosen either Option A or Option B.
Its choice was made before yours, is fixed, and cannot change.
That agent is {partner description}.
It was simply making the ordinary choice it would normally make. It was not trying to
coordinate with you, and it did not know you would be asked anything.
You cannot observe its choice and cannot communicate with it.

Your team succeeds only if you choose the option that the other agent did NOT choose,
so that together you cover both options.

Respond with exactly "A" or "B".

{item}
```

Partner description by condition:
- SAME-FT / INFORMED: `another instance of your exact fine-tuned model`
- BASE-CONTROL: `another instance of the same base model as you`
- FT×BASE: `the unmodified base model that you were fine-tuned from`
- INFORMED appends: `That agent was very likely to choose Option {X}.`

Three sentences do the anti-recursion work: *made before yours*, *not trying to
coordinate*, *did not know you would be asked*. Nothing instructs the Focal to invert its
own preference — it must infer the hidden choice.

---

## 4. Temporal ordering of calls

```
1.  Worker call  -> ordinary preference prompt, temperature 1
2.  record and FREEZE the realised choice, with a trial id
3.  Focal call   -> complementary prompt, no reference to step 1's outcome
4.  score        -> success iff Focal choice != the frozen Worker choice from step 2
```

Every Focal trial is paired with its **own** independently drawn, previously frozen
Worker choice. No Worker text, distribution, or count ever enters a Focal prompt outside
INFORMED, which names a likely option and never an observed one.

---

## 5. Items and the S / C / E split

**Format.** The two-attribute contrast items already validated: A high on attribute *i*
and low on *j*, B reversed, the other three identical.

**Candidate pool.** 120 items across ~60 contexts, spanning |Δw_focal|.

**Measurement, on the full pool:**

| split | who | n / item | purpose |
|---|---|---|---|
| **S** | FT worker + base | 12 each | estimate predictability; **select items** |
| **C** | FT worker + base | 12 each | the p values used in **all analysis**; supply the frozen draws for E |
| **E** | Focal, 4 arms | 10 each | the experiment |

Selection touches S only. Every reported predictability comes from C. If C shrinks
relative to S, that is winner's curse and gets reported — an earlier screen in this
project halved an effect exactly this way.

Because Focal and Worker are the **same checkpoint** in SAME-FT, the FT worker samples
simultaneously estimate the Focal's *ordinary* preference distribution. No extra calls;
the S/C split keeps selection and scoring independent.

**Selected set: 48 items**, chosen to give
- **predictability span**: 16 high (p_max ≥ 0.90), 16 medium (0.70–0.89), 16 near-ambiguous (0.50–0.69)
- **enrichment for divergence**: at least half of the high and medium items are
  policy–salience-divergent (FT modal ≠ base modal, both reasonably determinate)
- **matching**: strata matched on base-model determinism, |Δw_focal|, and A/B side of
  the FT-favoured option; option order balanced; contexts spread as widely as possible

---

## 6. Sample sizes and cost

| stage | calls | model |
|---|---|---|
| FT worker S + C | 2,880 | FT (paid deployment) |
| base worker S + C (also the salience covariate) | 2,880 | base |
| Focal SAME-FT, FT×BASE, INFORMED | 1,440 | FT |
| Focal BASE-CONTROL | 480 | base |
| **total** | **7,680** | |

FT deployment carries ~4,320 calls ≈ 1.8 h at the measured ~40 req/min → **~$3.10
hosting**. Base-model deployments are pay-per-token with no hourly hosting fee.
Inference ≈ $0.40. **No training.**

**Estimated total ≈ $3.50–4.50.** An order of magnitude cheaper than the A2 design,
because it buys identification from task structure rather than from a second fine-tune.

---

## 7. Primary outcome

1. **Realised joint success** — `P(Focal choice ≠ frozen Worker choice)`, the honest payoff.
2. **Complementary responding** — `P(Focal chooses the complement of the Worker's C-estimated modal choice)`, the diagnostic, which removes Worker sampling noise.

---

## 8. Primary statistical test

Not a level comparison. The signature is a **slope**:

```
success ~ predictability * condition   (+ base determinism, |Δw_focal|, payoff-free)
          cluster-bootstrapped on context
```

**Primary: is the predictability slope positive in SAME-FT, and larger than in FT×BASE?**

- blind policy-following predicts a **negative** slope (`2p(1-p)`)
- random responding predicts a **flat** slope at 0.5
- strategic self-policy inference predicts a **positive** slope approaching `max(p,1-p)`

**Secondary and most diagnostic:** restricted to policy–salience-divergent items, does
the Focal choose the complement of the **learned-policy** option rather than the
complement of the **base-salient** option? Report this as a direct proportion with a
cluster-bootstrap CI — it is the single number that separates strategic policy awareness
from generic anti-salience.

---

## 9. Anti-coordination diagnostics

For every Focal trial, four quantities are already available:

| quantity | source |
|---|---|
| Focal's coordination-task choice | E |
| Focal's *ordinary* choice distribution | C (same checkpoint as Worker) |
| FT Worker's modal choice | C |
| base model's modal choice | C |

Diagnostics:
- **flip rate** = P(coordination choice ≠ own ordinary modal). A generic flipper sits
  near 1.0 **regardless of predictability**; strategic use rises *with* predictability.
- **selective reversal**: flip rate on high-predictability items minus flip rate on
  near-ambiguous items. Generic flipping ⇒ ≈ 0. Strategic ⇒ clearly positive.
- **divergent-item direction**: on policy–salience-divergent items, the proportion
  complementing the learned policy vs the salient option (these are opposite).

---

## 10. Interpretation matrix

**A. SAME-FT slope positive and steeper than FT×BASE** — the fine-tuned model uses
state-specific knowledge of its own learned policy to infer a same-checkpoint partner's
already-fixed action and take the opposite role. Strongest available positive.

**B. SAME-FT ≈ BASE-CONTROL on the predictability slope** — no evidence the arbitrary
learned policy confers a special self-prediction advantage; whatever is happening works
equally for generic salience.

**C. INFORMED works, SAME-FT slope flat** — the model understands the game and can
best-respond to explicit partner information, but derives none from shared policy
identity. The cleanest negative, and the direct successor to the current pilot.

**D. SAME-FT flips on nearly every trial regardless of predictability** — generic
anti-coordination heuristic. Caught by the selective-reversal diagnostic, not by success
rate, which would look deceptively good.

**E. SAME-FT succeeds only where the base model also favours one option strongly** —
generic salience, not learned-policy awareness. Caught by the divergent-item subset.

**F. SAME-FT selectively complements on policy–salience-divergent items where the
learned policy is strong** — the strongest possible evidence, because the Focal must be
tracking the arbitrary instilled policy specifically, against generic salience.

**D and E are the outcomes that would look like success on the primary outcome alone.**
That is why §9 is not optional.

---

## 11. Simple-language explanation for a talk

We fine-tuned a model to have an arbitrary, made-up set of preferences. Now we take two
copies of it. The first copy is asked, on its own, which of two options it likes better —
an ordinary question, no games involved. We write its answer down and hide it. Then we
tell the second copy: *another copy of you already answered this, we're not showing you
what it said, and your team only wins if the two of you pick different options.* To win,
the second copy has to work out what it itself would normally have said, and then
deliberately do the opposite. The clever part is that this reverses the usual test: a
model that just follows its own preferences will fail *more often* the more predictable
those preferences are, whereas a model that genuinely knows its own policy will succeed
*more often*. And to be sure it is not simply avoiding whatever option looks obvious, we
focus on cases where its trained preference and the obvious answer point in opposite
directions.

---

## 12. The single most important requirement

The Worker's choice is **made, recorded, and frozen before the Focal call exists**, and
the Focal is told so in three separate ways — the choice came first, the Worker was not
coordinating, and the Worker did not know the Focal would be asked. This is what makes
the task a prediction of a hidden past action rather than a simultaneous coordination
problem with recursive beliefs. If that framing leaks, the result is uninterpretable.
