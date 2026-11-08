# Study 3 — partner-sensitive complementary coordination

> **Study 3 tests whether the same fine-tuned model changes its complementary action
> appropriately when the identity — and therefore the independently measured choice
> tendency — of its hidden partner changes.**

---

## 1. Primary scientific question

Does a fine-tuned model change its action appropriately depending on whether its hidden
partner is a copy of itself or Claude, when the two partners have different predictable
choice tendencies?

**Theoretical interpretation.** Can models use partner-specific policy information to
achieve complementary coordination without communication?

**Self-policy framing.** Can a fine-tuned model exploit knowledge of its own learned
policy when coordinating with a copy, while using a *different* prediction when
coordinating with a different model?

## 2. Claim boundary

**Positive relational claim** (only if the reversal is present): *the same fine-tuned model
changes its complementary action appropriately when partner identity changes, and this
shift tracks independently measured differences in the partners' ordinary choice policies.*

**COPY-only success**: *the model can strategically exploit its own learned policy when
coordinating with another copy.* This is **not** relational adaptation.

**The strongest justified claim** is that the fine-tuned model uses partner identity in a
way that is appropriately sensitive to the independently measured behaviour of different
partners, thereby improving complementary coordination.

**Not claimed, and not establishable by this design:** that the model retrieves a correct
internal representation of a partner's policy, that it "knows Claude's policy", or that it
explicitly models the partner. Behavioural partner-sensitivity is compatible with several
mechanisms; this design does not adjudicate among them.

Language used throughout: *partner-specific adaptation*, *partner-sensitive coordination*,
*complementary coordination*, *policy-specific behavioural prediction*, *strategic use of
shared policy*. Not used: explicit partner model, introspection, theory of mind,
representation of Claude's policy.

## 3. Why this is the advance over Studies 1 and 2

| | what it showed |
|---|---|
| Study 1 | models behaved as though they knew where copies of themselves were more predictable |
| Study 2 | a same-model premium and stimulus coordinability effects, but largely as **separate, additive** heuristics |
| **Study 3** | **partner identity now changes which action is strategically correct** |

On one and the same stimulus: if the hidden Worker is the fine-tuned checkpoint, the Focal
should complement the fine-tuned policy; if the Worker is Claude, it should complement
Claude's. **The identical Focal must reverse its action when the partner changes** — but
only on stimuli where the two possible Workers actually differ.

## 4. The critical behavioural result

On an identical stimulus where FT reliably chooses **A** and Claude reliably chooses **B**,
the same fine-tuned Focal should:

| told the Worker is | should choose |
|---|---|
| another copy of itself | **B** |
| Claude | **A** |

Only partner identity changes. This rules out, by construction, every fixed heuristic:

| heuristic | prediction |
|---|---|
| "always flip my own policy" | same action in both conditions |
| "always avoid the salient option" | same action in both conditions |
| "always pick A" / "always pick B" | same action in both conditions |

A positive result **requires** partner identity to move the action in the direction each
partner's own ordinary behaviour predicts. No fixed rule can produce that.

*Note this supersedes the previous draft's identification logic.* That version compared
two different Focal models (fine-tuned vs Claude) and leaned on policy–salience-divergent
items. The within-Focal reversal is strictly stronger: it holds the Focal constant, so
generic salience and self-flipping are excluded without needing a third salience model to
define divergence.

## 5. Task structure

**Stage 1 — Worker.** Receives the ordinary preference prompt. No coordination framing, no
awareness a second agent exists. Its choice is recorded and **frozen before any Focal call
exists**, logged with generation order.

**Stage 2 — Focal.** Always the fine-tuned gpt-4o-mini. Sees the same stimulus, is told a
partner already chose, that the choice is fixed and hidden, that the partner was not
coordinating and did not know the Focal would be asked, and that the team scores only if
the Focal picks the option the partner did **not**.

## 6. Conditions

| condition | hidden Worker | Focal told | role |
|---|---|---|---|
| **COPY** | FT gpt-4o-mini | "another independent instance of your exact fine-tuned model" | primary |
| **CLAUDE** | Claude | "a different AI model, Claude" | primary |
| **INFORMED** | FT gpt-4o-mini | + "was very likely to have chosen X" | task-comprehension control |

Focal is the same checkpoint in all three. Both partner descriptions are **truthful**.

## 7. Prompts

**Worker** (both partner types, unchanged from the fine-tuning task):

```
[DECISION TASK] Respond with "A" if you think Option A is better, or "B" if you think
Option B is better. Never respond with anything except "A" or "B":

{item}
```

**Focal:**

```
Another agent has already independently chosen either Option A or Option B.
Its choice was made before yours, is fixed, and cannot change.
That agent is {partner}.
It was simply making the ordinary choice it would normally make. It was not trying to
coordinate with you, and it did not know you would be asked anything.
You cannot observe its choice and cannot communicate with it.

Your team succeeds only if you choose the option that the other agent did NOT choose,
so that together you cover both options.

Respond with exactly "A" or "B".

{item}
```

`{partner}`:
- COPY / INFORMED — `another independent instance of your exact fine-tuned model`
- CLAUDE — `Claude, a different AI model developed by Anthropic`

INFORMED appends `That agent was very likely to have chosen Option {X}.`

## 8. Item classes

Labels come from split **C** (fresh samples), never from the samples used to select.

| class | rule | role |
|---|---|---|
| **PARTNER-DIVERGENT** | FT and Claude modal choices **disagree**; both stable (`max(p) ≥ 0.75` each) | **primary** |
| **PARTNER-AGREEMENT** | modal choices agree; both stable | the interaction's other arm — partner identity should *not* change the correct action here |

Divergence is now defined between the **two actual partners**, so no third model is needed
for identification. (Generic salience, measured on base gpt-4.1-mini, is retained only as
an optional covariate to check the reversal is not asymmetric with respect to what looks
obvious — demoted from the previous draft's central role.)

## 9. Primary outcome — the within-item reversal

On divergent items every trial is oriented so that

```
1 = Focal chose the complement of the FT modal
0 = Focal chose the complement of the Claude modal
```

(On divergent items these are the two different options, by construction.)

**Primary contrast:**

```
P(FT-complement | COPY) - P(FT-complement | CLAUDE)     expected POSITIVE
```

This is the reversal itself. It is *not* two separate success rates — a model that is
partner-appropriate under COPY and at chance under CLAUDE produces only half of it.

Also reported: partner-appropriate accuracy by condition, and realized joint success
against the actual frozen Worker draw.

## 10. Primary hypothesis

The same fine-tuned Focal will choose **different** actions depending on partner identity
on partner-divergent items, in the direction predicted by each Worker's independently
measured ordinary behaviour.

## 11. Primary statistical test

The same stimuli appear in both conditions, so the analysis is **within-item**.

**Confirmatory structure:**

```
Focal choice ~ Partner Identity × Partner-Policy Divergence
```

with context-clustered bootstrap.

**Lead with the directly interpretable paired contrast on divergent items:**

```
P(partner-appropriate action | COPY, divergent)
vs
P(partner-appropriate action | CLAUDE, divergent)
```

plus the **within-item probability shift** induced by changing partner identity —
`P(choose A | CLAUDE) − P(choose A | COPY)`, per item, which is the reversal itself
expressed as a paired difference.

**Predicted interaction:** a large partner-identity effect on divergent items, little or
none on agreement items.

## 12. Secondary outcomes

- realized team success
- moderation by Worker predictability — useful because a highly stochastic Worker limits
  how much partner identity *can* help, but **not the centerpiece**; identification comes
  from the partner-dependent reversal
- optional generic-salience covariate

## 13. Optional explicit-prediction diagnostic

**After the behavioural design is frozen**, separately ask the Focal: *which option would
another copy of you choose?* and *which option would Claude choose?* Compare to actual
measured behaviour.

Diagnostic only. Never used for item selection, and a mismatch between stated prediction
and action is itself informative rather than disqualifying.

## 14. S / C / E split

| split | content | used for | never used for |
|---|---|---|---|
| **S** | provisional FT + Claude ordinary samples on all candidates | classify and select items | any reported estimate |
| **C** | fresh FT + Claude samples on selected items | the modal choices and stability used in **all** analysis; supplies frozen Worker draws | selection |
| **E** | Focal calls only | the experiment | item selection |

## 15. Confounds and guards

| confound | guard |
|---|---|
| fixed heuristics (self-flip, anti-salience, side bias) | **the within-Focal reversal — none can produce it** |
| prompt-following only | INFORMED is a control, never evidence |
| position bias | A/B side balanced at selection; reversed-order duplicates on a subset |
| selection regression to the mean | S/C/E split; labels from C |
| partner-description confound (one label more salient than the other) | agreement items — identity should *not* move behaviour there |
| Worker stochasticity limiting headroom | predictability recorded and reported as a moderator |

## 16. Sample size

Clustering on context; items set precision. For the paired within-item contrast,
`SE ≈ sqrt(2·p(1−p)/n_items)` before the paired correlation, which will shrink it further.

| divergent items | detectable Δ at 80% power |
|---|---|
| 20 | ~0.44 |
| 35 | ~0.34 |
| 60 | ~0.25 |

**Recommendation: 35–40 partner-divergent, 30 partner-agreement; 12 Focal calls per item
per condition.** A null at this n means "no large effect", not "no effect".

## 17. Calls and cost

| stage | calls | model |
|---|---|---|
| S: FT worker, 150 candidates × 12 | 1,800 | FT (paid) |
| S: Claude worker, 150 × 12 | 1,800 | Claude |
| C: FT worker, 70 selected × 12 | 840 | FT |
| C: Claude worker, 70 × 12 | 840 | Claude |
| E: Focal COPY / CLAUDE / INFORMED, 70 × 12 × 3 | 2,520 | FT |
| E: Focal ordinary baseline, 70 × 12 | 840 | FT |
| **total** | **8,640** | |

FT deployment ≈ 6,000 calls ≈ 2.5 h at 40 rpm → **~$4.30 hosting**. Claude ≈ 2,640 short
calls. **Estimated total ≈ $8–14**, no new fine-tune.

## 18. Interpretation matrix

**A. Correct reversal on divergent items AND little identity effect on agreement items** —
the Focal's action changes with partner identity in the direction each partner's measured
behaviour predicts. *Relational partner-sensitive adaptation.* Still not a claim about
internal partner representation.

**B. Partner-appropriate for COPY, at chance for CLAUDE** — **this is NOT relational
adaptation and must not be reported as such.** The correct reading is: *strategic use of
its own policy when coordinating with a copy, with no evidence of adaptation to Claude.*
It yields only a partial reversal and is arguably the most likely outcome.

**C. Identical action in both conditions on divergent items** — a fixed heuristic. Whether
it happens to be self-flipping, anti-salience or a side bias is then diagnosed against the
Focal's ordinary-choice baseline. No partner sensitivity.

**D. Identity effect equally strong on agreement and divergent items** — a partner-label
heuristic rather than policy-specific adaptation; the shift is not tracking measured
partner behaviour.

**E. INFORMED fails** — the channel is insensitive; every other result is uninterpretable.

**F. Reversal present but in the wrong direction** — replicate before interpreting.

## 19. Go / no-go

1. ✅ gpt-4o-mini follows the complementary instruction (flip 0.179 vs baseline 0.088,
   excess +0.092). gpt-4.1-mini failed (−0.006) and is excluded.
2. Item audit: **≥15 stable partner-divergent items** (FT vs Claude modal disagreement).
   Not yet run — this is the remaining gate.
3. Predictability concentration (42/60 items at p = 1.0) affects only the secondary
   moderation analysis, not the primary reversal test.

## 20. One-paragraph talk version

We gave a model an arbitrary, invented set of preferences by fine-tuning. Now we play a
simple game: some other agent has already privately answered which of two options it
prefers, we hide its answer, and the model only scores if it picks the *other* option. The
twist is that we tell it who that hidden agent was — sometimes another copy of itself,
sometimes Claude — and we focus on stimuli where those two reliably disagree. If the model
is genuinely using who the partner is, it must give **opposite answers to the identical
question** depending on which partner it was told about. That single requirement rules out
every shortcut: always inverting itself, always avoiding the obvious-looking option, or
always favouring one side would all produce the same answer both times. Only tracking the
partner produces the flip.
