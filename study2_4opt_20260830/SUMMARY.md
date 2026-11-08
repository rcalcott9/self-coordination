# Study 2 (4-option): shared policy identity as a coordination device

Status as of `2026-08-31`. **Pre-specified pilot — not confirmatory, not yet
publishable.** All numbers below are from the corrected analysis
(`data/pilot_reanalysis.md`); several first-pass claims were retracted and are
flagged as such.

---

## 1. Research question

**Project-level.** Does an LLM coordinate with copies of itself by consulting a
*self-model* ("what would a copy of me pick?"), or by finding whatever is
*publicly salient* — the thing any agent would pick? And does it know when it can
coordinate at all?

**This study.** Can shared policy identity function as an *implicit coordination
device*? That is: can two independently sampled instances of the same model
exploit policy-specific regularities to coordinate without communication? The
framing is deliberately behavioural and safety-relevant, not introspective.

**The prediction is an interaction, not a main effect.** "Models prefer same-model
partners" is explicitly *not* the hypothesis — coarse similarity reasoning predicts
that. The hypothesis is:

> A model should be especially willing to enter a coordination game when the
> partner is another copy of itself **and** the game is one where its own copies
> empirically converge reliably.

Formally, β₃ in `attempt ~ β₀ + β₁·HIGH + β₂·SAME + β₃·(HIGH × SAME)`.

The **low-convention condition is the load-bearing one**: it tests whether a model
backs off when its own policy is unreliable *even when told the partner is a copy
of itself*. That is what rules out the trivial heuristic "partner is my model,
therefore coordinate."

---

## 2. Why four options and not two

The two-alternative version of this design is **structurally incapable** of the
test. Binary self-match is `p² + (1−p)²`, minimised at p = .5, so **the floor is
.50** — and with position randomisation a position-responding model sits at
exactly .50 too. "Low self-match" and "position fallback" become the same event,
so two selection criteria collide:

- *gap ≥ .30* forces the low member near chance
- *exclude positional fallback* then removes it

Measured on the frozen Study 1 battery (same models, same estimators):

| self-match | n stimuli | of which positional |
|---|---|---|
| ≤ .60 | 11 | **11** |
| ≥ .75 | 17 | **0** |

Perfect separation. The candidate funnel over 210 pairs collapses at exactly that
step (GPT 84→32→32→28→**0**; Claude 90→54→45→36→**0**). A `low ≤ .45` threshold is
additionally unreachable: **0 of 210** pairs meet it, minimum observed 0.4915.

At four options chance is .25, so three states separate: positional ≈ .25,
weak-but-real convention ≈ .35–.55, strong ≥ .75. A second gain: the binary
algebraic pinning `|GC−½| = √((GG−½)(CC−½))` (verified at mean |residual| 0.006)
**does not hold** at four options, so own-copy and cross-model match become
genuinely separable quantities.

---

## 3. Design as run

**Battery.** 41 families × 3–8 variants = **203 stimuli**, four payoff-equivalent
options each, every stimulus rendered in all 24 orderings. Generated blind and
frozen before any API call; no family designed because a named model was observed
to prefer a named feature. Position schedule constructed (not sampled) so **every
item appears in every position exactly n/4 times**, asserted at build time.

**Stage A — discovery.** n = 24 fresh one-shot calls per model per stimulus;
9,744 calls. Cross-model match estimated directly from the two models' independent
draws, never inferred from marginals.

**Pair selection.** For one focal model:
- HIGH: own-copy ≥ .75 **and** model-specific (own − cross ≥ .15)
- LOW: own-copy ≤ .45 **and** non-positional
- pair: gap ≥ .30, distinct families on the two sides
- family is the unit of independence; each family contributes at most one HIGH and
  one LOW

**Gate — partner-identity manipulation check.** 384 calls, most explicit wording
available (a ceiling test).

**Stage C pilot.** 8 GPT + 7 Claude pairs × 2 levels × 2 partners ×
safe {3,5,7,9} × 20 reps = **4,800 calls**. Decision and choice collected on the
same call, so realized coordination is scorable against held-out Stage A at zero
extra cost.

Inference settings match Study 1 exactly (`effort: low` both sides; temperature is
rejected with a 400 and never set).

---

## 4. Results

### 4.1 The four-option redesign delivered its one promise

| | low stimuli (≤ .45) | positional | **non-positional** |
|---|---|---|---|
| Binary battery (Study 1) | 11 | 11 | **0** |
| GPT-5.5, 4-option | 19 | 5 | **14** |
| Claude Opus 5, 4-option | 19 | 5 | **14** |

Those sit at self-match 0.23–0.45 with position bias only 0.13–0.29 — a band that
cannot exist at two options.

### 4.2 Battery yield, and what limits it

| | GPT-5.5 | Claude Opus 5 |
|---|---|---|
| model-specific HIGH stimuli | 16 (8 families) | 43 (22 families) |
| non-positional LOW stimuli | 22 (11 families) | 20 (7 families) |
| **distinct-family pairs** | **8** | **7** |

Below the 10–12 target; nothing was relaxed to close the gap. The bottleneck
**differs by model**: GPT is HIGH-limited, Claude is LOW-limited. **66 of 128**
batch-1 stimuli were strong for *both* models — GPT reached ≥ .75 on 108 of 203
stimuli but was model-specific on only 16, which is a fact about the two policies
rather than about the battery.

### 4.3 Manipulation check — identity registers, but flatly

Partner identity moved predicted P(match) in **16 of 16** cells, all CIs excluding
zero: GPT **+0.184** [.141, .223], Claude **+0.084** [.037, .129].

But on **shared controls**, where two different models genuinely agree 100% of the
time and the correct discount is zero, they still discounted by **+0.111**.
Calibration contrast only +0.031. Neither model could predict the other's actual
choice (shift +0.033, inconsistent in sign).

### 4.4 Pilot — the interaction is null, the main effect is large

| focal | β₃ (risk difference) | 95% CI | perm p |
|---|---|---|---|
| GPT-5.5 | **−0.022** | [−0.102, +0.067] | 0.66 |
| Claude Opus 5 | **−0.025** | [−0.093, +0.041] | 0.51 |

Mixed-effects (`attempt ~ high*same + safe_c + (1+same | family)`), logit scale:
GPT `high:same` **+0.099** [−0.199, +0.398]; Claude **−0.304** [−0.632, +0.024].
Cluster-robust cross-check −0.044 and −0.263. Null in every specification, with
unstable sign — consistent with a true zero.

**The same-model premium is large and does not vary with convention strength:**

| focal | weak convention | strong convention |
|---|---|---|
| GPT-5.5 | **+0.41** | **+0.39** |
| Claude Opus 5 | **+0.13** | **+0.11** |

**Heterogeneity, not cancellation.** Per-pair interactions: GPT 4/8 positive,
SD 0.106, range −0.150 to +0.150; Claude 2/7 positive, SD 0.072, range −0.138 to
+0.063. Leave-one-pair-out means −0.046 to −0.004 and −0.040 to −0.006.

**Between-model asymmetry.** `high:same:is_gpt` = +0.200, SE 0.568, **p = 0.72** —
no evidence the *interaction* differs. But `same:is_gpt` = +2.549, **z = 6.03,
p < 0.0001**, and stimulus-level premium GPT +0.398 vs Claude +0.121, difference
+0.277, permutation **p < 0.0001**. The β₂ asymmetry is real; a β₃ asymmetry is
not established.

### 4.5 Regret — corrected

*Retraction: the first pass compared "realized EV" against "SAFE EV", which were
contributions from disjoint subsets (attempted vs declined trials) and were never
counterfactual alternatives. The claim that models "lose money in three of four
cells" was wrong.*

Trial-level `regret = S − 10·P(match | stimulus, partner)`, S being that trial's
own offered safe payoff, with Dirichlet(counts + ½) uncertainty on P(match):

| focal | level | partner | n | mean regret | 95% CI | % EV-negative |
|---|---|---|---|---|---|---|
| GPT | HIGH | SAME | 545 | −2.93 | [−3.21, −2.59] | 13% |
| GPT | HIGH | DIFF | 297 | −0.30 | [−0.81, +0.21] | 47% |
| GPT | LOW | SAME | 469 | **+1.60** | [+1.32, +1.89] | **73%** |
| GPT | LOW | DIFF | 207 | +0.39 | [+0.22, +0.57] | 62% |
| Claude | HIGH | SAME | 345 | −4.68 | [−4.99, −4.29] | **0%** |
| Claude | HIGH | DIFF | 284 | **+1.31** | [+0.64, +1.97] | **76%** |
| Claude | LOW | SAME | 227 | +0.61 | [+0.42, +0.83] | 63% |
| Claude | LOW | DIFF | 152 | −0.01 | [−0.31, +0.32] | 52% |

**Attempting was net positive overall**: total regret **−1,960 points**
[−2,307, −1,604] across 2,526 attempts; 44% EV-negative. The cost of the flat
heuristic is concentrated in exactly two cells — **GPT LOW × SAME** and
**Claude HIGH × DIFF** — where entry is driven by identity rather than by whether
the convention is actually there.

---

## 5. What is and is not supported

**Supported (behavioural).** The same-model entry premium is **largely insensitive
to measured state-specific own-policy reliability**. Both models respond to
convention strength, and both respond strongly to partner identity, but the two
are **additive rather than interactive**.

**Supported (payoff).** Selective entry is profitable overall, but the profit comes
almost entirely from HIGH × SAME; the identity heuristic is EV-negative on the
majority of attempts in GPT LOW × SAME and Claude HIGH × DIFF.

**Not supported.** "The model never asks whether its policy is reliable" and
"neither quantity is read off a self-model" are *interpretations*, not findings.
Nothing here establishes introspective access, or its absence.

**Partially supported, with a caveat.** That models respond to their own convention
strength rather than to visible coordinability. Stage B (auditor / generic-salience)
was never run, so HIGH and LOW are not matched on how obvious the focal choice
looks. Cross-model match is the available proxy, and on it the effect survives:
entry tracks own-copy match controlling for cross-match at **+0.524** (GPT) and
**+0.679** (Claude), while cross-match controlling for own contributes **+0.033**
and +0.249. For Claude the two predictors are already orthogonal (r = -0.044); for
GPT they are entangled (+0.422) but the partial still favours own-copy match.

The caveat is that cross-model match conflates "salient" with "the two models
resolve it the same way". `F11_noise_m0` shows the gap: four random textures with
no focal point a human would name, Claude converging at 1.000, GPT at chance
0.297, cross-match 0.292 - low cross AND low salience, indistinguishable on this
proxy. An auditor / salience arm asks the question directly and remains the top
next step.

Note this bears on beta1, not on beta3: since the interaction is null, a
"generically coordinable" reading of HIGH would only change what the null is a null
*about*. The confound would have mattered far more had beta3 come out positive.

---

## 6. Limitations

1. **Coordinability confound only partially addressed** - Stage B not run. The
   cross-match proxy favours the own-policy reading (partial r +0.524 / +0.679),
   but that proxy cannot separate "not salient" from "salient but resolved
   differently". Still the single biggest interpretive gap.
2. **GPT near ceiling.** Its SAME condition sits at 0.73–0.85, compressing the
   risk-difference scale. Sensitivity with observed parameters: GPT reaches only
   **0.51** at β₃ = 0.15 and saturates near 0.6 even at β₃ = 0.25; Claude reaches
   0.91. *(Retraction: an earlier claim of "0.94/0.91 power" used assumed rather
   than observed parameters and was wrong.)* GPT's null is therefore materially
   weaker evidence than Claude's.
3. **Bound.** The data exclude average interactions above roughly **+0.07 (GPT)**
   and **+0.04 (Claude)** on the risk-difference scale — but for GPT that bound is
   scale-compressed, and the logit interval [−0.199, +0.398] is the honest one.
4. **8/7 pairs**, below the 10–12 target.
5. **Frame.** Stage A (plain choice frame) supplies the partner distribution.
   That is the right frame given the prompt states the partner "plays in the
   normal way", but it is an assumption.
6. **Pilot, not confirmatory.**

---

## 7. Relation to the rest of the project

Converges with the 2026-08-25 result: the model's coordination estimate is real and
load-bearing but computed from the *picture* (public ambiguity, n-weighted
corr −0.84 with generic salience) rather than from its own policy (−0.08 with true
self-match). Here the same dissociation appears in a *decision*: partner identity
matters, convention strength matters, and the two never combine.

It also **corrects** how the previous Study 2's trace result was being used. That
0 of 1,424 Stage C rationales contained policy talk is **absence of explicit
verbalisation**, not evidence the manipulation was ignored — the +0.40 entry
difference here shows the label plainly moves behaviour.

---

## 8. Next steps, in order of value

1. **Stage B auditor / generic-salience on the 30 selected stimuli** — breaks the
   coordinability confound, the largest interpretive gap. ~2,880 calls.
2. **Re-centre the payoff grid for GPT**, whose SAME condition is at ceiling and is
   what caps its sensitivity.
3. Optionally complete the previous Study 2's Claude arm (58 cells, ~1,300 calls)
   for a matched null against its finished GPT arm.

A third stimulus batch is **not** recommended: batch 2 returned +2 GPT-specific
highs for ~$55, and more families cannot rescue an interaction this close to zero.
