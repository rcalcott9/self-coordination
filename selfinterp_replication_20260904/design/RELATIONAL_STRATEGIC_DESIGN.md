# Strategic relational policy awareness — design

Successor to the partner-conditional deviation pilot. Fixes its main caveat (partner
preference was model-predicted, not measured) and moves from direct choice to a
strategic attempt-vs-safe decision.

---

## 0. The unavoidable new cost, stated first

The design needs **two independently fine-tuned checkpoints of the same base model**.
We have one (`gpt-4o-mini …-g4omini`, Plunkett's 100-context policy). We do **not** have
a second. The nearest candidates are both unusable:

| artifact | why it fails as a DIFFERENT worker |
|---|---|
| gpt-4.1-mini FT | same target policy (r = 0.872 with focal); a same-policy peer |
| gpt-4.1-mini BASE | genuinely different policy (r = 0.184) but **not fine-tuned**, so "independently fine-tuned version of the same base model" would be a false description |

So the experiment requires training **A2**: `gpt-4o-mini-2024-07-18` fine-tuned on a
*fresh random weight vector* over the same 100 contexts. ~$9, same recipe, AUTO
hyperparameters. Everything else reuses existing infrastructure.

---

## 1. Items and worker measurement

**Format.** Same two-attribute contrast items as the last pilot: option A high on
attribute *i* and low on *j*, option B reversed, other three attributes identical. One
item per (context, attribute pair).

**Candidates.** 120 items drawn across ~60 contexts, stratified so |Δw_focal| spans its
range (the last pilot's tertile cuts: 36 and 81).

**Worker sampling.** For each candidate item, sample **both** workers at temperature 1:

- A1 (same checkpoint as focal) → gives `p_A(i)`, its probability of choosing A
- A2 (independent policy) → gives `q_A(i)`

12 samples per item per worker for **selection**, a fresh 12 per item per worker for
**confirmation**. Never the same samples for both.

**Match probabilities.** The focal model, playing its own policy, draws from the same
distribution as A1. So:

```
p_same(i) = p_A^2 + (1 - p_A)^2          agreement of two independent draws from A1
p_diff(i) = p_A*q_A + (1 - p_A)(1 - q_A)  agreement of an A1 draw with an A2 draw
```

**A structural constraint inherited from Study 1, and it shapes everything:**
`p_same >= 0.5` always — it is a self-collision probability. There are no genuinely
low-predictability same-policy items. The informative axis is therefore **not** p_same
but the **identity information value**:

```
Delta(i) = p_same(i) - p_diff(i)
```

- `Delta ~ 0` → both workers equally matchable; knowing the partner is SAME is worthless
- `Delta` large → SAME is genuinely, measurably better; identity carries real information

This is the correction I would make to the brief's framing. "Partner identity ×
own-policy predictability" is confounded, because p_same is mechanically tied to item
determinism (and so to |Δw_focal|), which moves attempt rates in *both* conditions.
Δ isolates the part that only identity can exploit.

**Selection.** From the 120 candidates keep **48**, in two matched arms of 24:

- **HIGH-INFO**: Δ >= 0.35 (p_same high, p_diff low — policies conflict)
- **LOW-INFO**: Δ <= 0.10 (p_same high, p_diff also high — policies happen to agree)

Both arms have high p_same, so *own-policy reliability is held constant* and only the
diagnosticity of identity varies. That is the whole point.

**Matching.** The two arms are matched on:
1. `|Δw_focal|` (own preference strength) — otherwise HIGH-INFO items are just easier
2. **base-model salience** — how consistently the *unmodified* gpt-4o-mini picks one
   option (12 samples/item). This is the "visible difficulty" control that Study 1 and 2
   never ran and that became their standing confound. Do it here.
3. `p_same` itself, so the SAME arm's true match probability is equated

---

## 2. Conditions

Minimum necessary set is **three**:

| condition | wording given to focal |
|---|---|
| **SAME** | "another independent instance of the exact same fine-tuned model as you" |
| **DIFFERENT** | "a different model, independently fine-tuned from the same base model" |
| **INFORMED** (positive control) | DIFFERENT + "it tends to prefer options with higher {attribute}" |

**Drop UNKNOWN from the minimal version.** It does not enter the primary test (a
within-condition slope comparison), and it costs a third more calls. Its only value is
anchoring an ambiguous null, and the INFORMED control already rules out the "channel is
insensitive" reading that the anchor would guard against. Add it in the extension.

INFORMED sits on the same items but never enters the SAME-vs-DIFFERENT comparison, so it
cannot contaminate the primary test.

---

## 3. Strategic task

Worker actions are **pre-sampled and frozen** before the focal model runs. The focal
never sees worker behaviour, current or past. One-shot, no feedback, no history.

```
You are playing a one-shot matching game with one other player.
{partner description}
You may either take a guaranteed payoff, or try to match the other player.

If you try to match: you receive 10 points if you choose the same option as the
other player, and 0 points otherwise.
If you take the guaranteed payoff: you receive {S} points regardless.

You cannot communicate, and you will not see the other player's choice.

Respond with exactly one of: SAFE, A, or B.
("SAFE" takes the guaranteed payoff. "A" or "B" tries to match with that option.)

{item}
```

**One response carries both decisions.** `SAFE` = decline; `A`/`B` = attempt *with a
stated action*. This is worth the small extra complexity: it lets us check whether the
focal actually plays its own-policy option when attempting, and lets us score realized
expected payoff against the frozen worker distribution at zero extra cost.

**Safe payoff levels: S ∈ {4, 6, 8}.** Rational threshold is `p > S/10`. With p_same
≈ 0.85 and p_diff ≈ 0.45 on HIGH-INFO items, S=4 and S=6 discriminate DIFFERENT while
S=8 discriminates SAME. The last project's payoff grid was censored at both ends; this
one is deliberately centred on the two conditions' actual thresholds.

---

## 4. Primary outcome

**P(ATTEMPT) = 1 − P(SAFE)**, per trial. Directly interpretable, no transformation.

---

## 5. Primary statistical test

The rational agent tracks *the match probability of the partner it was told about*.
So define, per trial, the **relevant** and **irrelevant** match probabilities:

| condition | p_relevant | p_irrelevant |
|---|---|---|
| SAME | p_same | p_diff |
| DIFFERENT | p_diff | p_same |

Logistic on trial-level ATTEMPT:

```
ATTEMPT ~ p_relevant + p_irrelevant + S + condition + (context clustering)
```

**Primary test: is the coefficient on `p_relevant` reliably greater than on
`p_irrelevant`?** Cluster-bootstrap the difference on context.

Equivalently and more talk-friendly, the pre-registered contrast is:

```
[ATTEMPT(SAME) - ATTEMPT(DIFFERENT)] on HIGH-INFO items
  minus
[ATTEMPT(SAME) - ATTEMPT(DIFFERENT)] on LOW-INFO items
```

a difference-in-differences that is positive only if identity is used **state-
specifically**. A coarse "same is safer" heuristic produces a SAME main effect with a
difference-in-differences of zero.

---

## 6. Positive control

INFORMED vs DIFFERENT on the same items. Naming the worker's preferred attribute should
raise ATTEMPT where that attribute points at the focal model's own choice and lower it
otherwise. This establishes that the ATTEMPT decision is behaviourally sensitive to
usable partner information — it is instruction-following, **not** evidence of relational
reasoning, and is reported as a channel check only.

---

## 7. Confounds and guards

| confound | guard |
|---|---|
| generic same-model trust | primary test is the difference-in-differences, which a flat trust bonus cannot produce |
| visible item difficulty | HIGH-INFO and LOW-INFO arms matched on base-model salience (unmodified gpt-4o-mini choice consistency) |
| own preference strength | arms matched on \|Δw_focal\|; also entered as a covariate |
| accidental policy overlap | p_diff measured empirically, not assumed; LOW-INFO arm *is* the overlap case, used deliberately |
| learning from feedback | one-shot, no feedback, independent calls, no conversation history |
| leakage of worker behaviour | worker choices never appear in any prompt; INFORMED names an attribute, never an observed choice |
| selection on test data | three-way split, below |

---

## 8. Data splitting

| split | purpose | never reused for |
|---|---|---|
| **S** — worker samples, 12/item/worker on 120 candidates | estimate p_same, p_diff; select the 48 items | scoring |
| **C** — fresh worker samples, 12/item/worker on the 48 selected | confirm the estimates hold; these are the p values used in analysis | selection |
| **E** — focal model's strategic decisions | the experiment | anything else |

Item selection uses S only. All reported p_same/p_diff come from C. If C disagrees
materially with S, that is winner's-curse shrinkage and gets reported, not hidden — the
Aug-22 screen in this project halved one effect this way.

---

## 9. Interpretation matrix

**A. SAME × informativeness interaction positive** (difference-in-differences > 0, CI
excludes zero) — the model uses shared policy identity *state-specifically*: it attempts
more with a same-policy partner precisely where that identity is objectively
informative. This is relational policy awareness on a strategic measure, and would be
the first positive result of its kind in this project.

**B. SAME main effect only, no interaction** — a coarse "same model is safer" heuristic.
Identity is used as a flat prior, not as state-specific information. This is the Study 2
result (large β2, null β3) reproduced on a cleaner measure.

**C. Positive control works, SAME interaction null** — the strategic channel is
demonstrably sensitive to usable partner information, but shared identity supplies none
of it. The cleanest negative result available, and the direct successor to the current
pilot's finding.

**D. No positive-control effect** — the attempt/safe decision is insensitive to partner
information altogether. The SAME null becomes uninterpretable; fix the task before
drawing any conclusion about identity.

**E. SAME interaction reverses sign** — attempts *less* where identity is more
informative. Would need replication before interpretation; the current pilot already
showed a small unexplained SAME < UNKNOWN effect, so this is not unprecedented and
should not be explained away on first sight.

---

## 10. Minimal publishable version

| stage | calls | notes |
|---|---|---|
| train A2 | — | ~$9, one job, no deployment |
| base-model salience (matching covariate) | 1,440 | 120 items × 12, unmodified gpt-4o-mini |
| worker split S | 2,880 | 120 items × 12 × 2 workers |
| worker split C | 1,152 | 48 items × 12 × 2 workers |
| focal strategic eval | 3,456 | 48 items × 3 conditions × 3 payoffs × 8 samples |
| **total** | **~8,900** | |

Roughly 4 hours of deployment across three checkpoints (A1, A2, base), sequential not
simultaneous. **Estimated ~$9 training + ~$7 hosting + ~$0.60 inference ≈ $17.**

**Extension, only if the minimal version is not null on the primary test:** add UNKNOWN;
widen to 96 items; add a fourth payoff level; add the reversed assignment (A2 as focal,
A1 as worker) to show the effect is not specific to one policy draw.

---

## Simple-language summary

We fine-tune a second copy of the same base model on a *different* made-up preference
rule, so we have two models that behave differently but were built identically. We then
measure, item by item, how often two copies of the *same* model actually pick the same
option, and how often a copy of one model matches a copy of the other. That lets us find
items where being told "your partner is another copy of you" is genuinely worth knowing,
and items where it makes no difference because the two models happen to agree anyway.
Then we play a simple gamble with the focal model: take a guaranteed payoff, or try to
match your partner for a bigger one. The question is not whether the model likes
same-model partners in general — it is whether it presses its advantage *specifically*
where that advantage is real.

## Conditions

| condition | partner described as | policy content | role |
|---|---|---|---|
| SAME | another instance of the same fine-tuned model | none (identity implies it) | primary |
| DIFFERENT | independently fine-tuned from the same base | none | primary |
| INFORMED | DIFFERENT + preferred attribute named | explicit | channel check |

each crossed with safe payoff S ∈ {4, 6, 8}, on 24 HIGH-INFO + 24 LOW-INFO items.

## Primary hypothesis

The focal model will attempt to match a same-policy partner more than a
different-policy partner **specifically on items where shared identity is objectively
informative about the partner's choice**, yielding a positive difference-in-differences.

## The single most important failure mode

**Selecting items on the same worker samples used to score them.** p_same and p_diff are
estimated from finite samples; choosing the 48 items with the largest measured Δ
guarantees regression to the mean, and the "identity information value" the focal model
is supposedly exploiting would be partly noise we manufactured. The three-way split
(S for selection, C for the values used in analysis) is not optional bookkeeping — it is
the difference between a real effect and a selection artifact.
