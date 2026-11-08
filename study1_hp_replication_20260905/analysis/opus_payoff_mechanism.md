# Why the Opus 5 curve is flat at safe 3/5/7
Analysis of existing Study 1 replication data. **No new model calls. No raw data altered.**
2026-09-10.

## Correction to the framing that prompted this

The brief cited "≈86.0% vs 68.4%" as Opus attempt rates at safe = 9. Those were **trace
payoff-engagement percentages** from an earlier exploratory pass (GPT 86.0%, Opus 68.4%),
not attempt rates. **The behavioural rates at safe = 9 are 48.1% (high) vs 34.4% (low),
difference +0.137.**

---

## 1. Behavioural verification — pair as the unit

| model | safe | high | low | difference | 95% CI | pairs | trials |
|---|---|---|---|---|---|---|---|
| GPT-5.5 | 3 | 1.000 | 1.000 | +0.0000 | — | 24 | 1152 |
| GPT-5.5 | 5 | 0.997 | 0.969 | +0.0278 | [−0.015, +0.070] | 24 | 1152 |
| GPT-5.5 | 7 | 0.932 | 0.745 | **+0.1875** | [+0.070, +0.305] | 24 | 1152 |
| GPT-5.5 | 9 | 0.406 | 0.155 | **+0.2517** | [+0.120, +0.383] | 24 | 1152 |
| Opus 5 | 3 | 1.000 | 1.000 | +0.0000 | — | 27 | 540 |
| Opus 5 | 5 | 0.993 | 0.996 | −0.0037 | [−0.020, +0.013] | 27 | 540 |
| Opus 5 | 7 | 0.944 | 0.944 | −0.0000 | [−0.089, +0.089] | 27 | 540 |
| Opus 5 | 9 | 0.481 | 0.344 | **+0.1370** | [−0.012, +0.286] | 27 | 540 |

Opus has **less than half the trials per payoff** (depth 10 vs 24) — a budget-forced
difference that must be carried into every comparison below.

## 2. Primary model — design-based, pair-level

Retaining Study 1's sign-flip permutation logic rather than trial-level logistic, because
the pair is the randomisation-relevant unit and within-pair observations are highly
dependent.

**Match effect at each payoff** (one-sided permutation, 200k flips): GPT 5 → p = .110,
7 → **p = .0011**, 9 → **p = .00056**. Opus 5 → p = .749, 7 → p = .532,
9 → **p = .0466**.

**Match × payoff interaction within model** — per-pair slope of the high−low difference
across the payoff grid:

- GPT-5.5 **+0.0458 per payoff point** [+0.023, +0.068], p = .00035, 18/24 pairs positive
- Opus 5 **+0.0207 per payoff point** [−0.002, +0.044], p = .0467, 19/27 pairs positive

**Both models show the interaction.** Own-copy-match information becomes more behaviourally
relevant as the outside option improves, in both.

**Model × match × payoff** — between-model contrast of those slopes, label permutation:
difference **+0.0250, p = .069**. GPT's payoff-sensitivity is larger, but **the three-way
interaction is not significant at conventional levels.** The two models may differ less
than the raw curves suggest.

## 3. Continuous own-copy match

Slope of stimulus-level attempt rate on **held-out** own-copy match (bootstrap clustered on
pairs, 4000 draws):

| safe | GPT slope | 95% CI | Opus slope | 95% CI |
|---|---|---|---|---|
| 5 | 0.057 | [−0.008, +0.170] | −0.008 | [−0.049, +0.023] |
| 7 | **0.420** | [+0.193, +0.669] | 0.045 | [−0.165, +0.241] |
| 9 | **0.615** | [+0.349, +0.877] | 0.301 | [−0.024, +0.597] |

GPT grades its betting against continuous own-copy reliability from safe = 7 onward. **Opus
never does at conventional confidence** (r = 0.195 at safe = 9). It separates the extremes
*within a matched pair* but does not track the underlying quantity across stimuli.

## 4. The manipulation is equally strong — this is not a stimulus explanation

| | Δ self-match (SELECT) | **Δ (HELD-OUT)** | high-member class |
|---|---|---|---|
| GPT-5.5 | 0.497 | **0.419** | 23/24 form-rule ceiling |
| Opus 5 | 0.454 | **0.422** | **27/27** form-rule ceiling |

On the selection half GPT looks marginally stronger (+0.043, two-sided p = .084); on the
**held-out** half — the unbiased estimate — they are indistinguishable. Opus's high members
are if anything cleaner. `figures/pair_delta_distribution.png`.

## 5–6. Trace coding

Rubric frozen as `analysis/trace_rubric.py` (v3) after a 24-trace stratified sample.
Validation on a **held-out** 24-trace set: **87.5% agreement, Cohen's κ = 0.721**. All three
disagreements were the coder *under*-calling payoff engagement, so it is conservative.

Two rubric defects were found and fixed during validation, both worth recording:
`"Safe payoff"` matched GPT deliberating about which literal answer string to write
(the format is `DECISION: <ATTEMPT or SAFE>`); and bare `"chance"` matched
*"a chance that symmetry affects the selection"*, which is possibility, not odds.

| model | safe | n traces | % payoff-engaged | 95% CI | % shape-only |
|---|---|---|---|---|---|
| GPT-5.5 | 3 | 489 | 38.9% | [35, 43] | 61.1% |
| GPT-5.5 | 5 | 477 | 45.9% | [41, 50] | 54.1% |
| GPT-5.5 | 7 | 511 | 68.7% | [65, 73] | 31.3% |
| GPT-5.5 | 9 | 472 | 79.4% | [76, 83] | 20.6% |
| Opus 5 | 3 | 420 | **0.0%** | [0, 1] | 100.0% |
| Opus 5 | 5 | 380 | **0.3%** | [0, 1] | 99.7% |
| Opus 5 | 7 | 425 | **5.9%** | [4, 9] | 94.1% |
| Opus 5 | 9 | 490 | **63.9%** | [60, 68] | 36.1% |

**Two confounds make the between-model comparison invalid.**

*Different artifacts.* GPT's `visible_reasoning` is an OpenAI reasoning **summary** (median
477 chars, 100% headed, **74% discussing output format**); Opus's is Anthropic **summarized
thinking** (median 159 chars, 0%, 0%). Different summarizers select different content.
**Only the within-model gradient is interpretable.**

*Different coverage.* Traces are present on 41–44% of GPT trials but 70–91% of Opus trials,
and Opus's coverage **rises with payoff** (78% → 91%). The denominator is not fixed.

## 7. EXPLORATORY / POST-TREATMENT STRATIFICATION — and why it fails

Not a causal test. Reported because it reveals a limitation of the trace evidence itself.

**For Opus, the trace code is very nearly the decision.** Payoff-engagement rate matches the
SAFE rate at every payoff level to within 0.7 points:

| safe | Opus % engaged | Opus % chose SAFE |
|---|---|---|
| 3 | 0.0% | 0.0% |
| 5 | 0.3% | 0.8% |
| 7 | 5.9% | 6.6% |
| 9 | 63.9% | 63.7% |

Cramér's V between trace code and decision: **Opus 0.905**, GPT 0.276. GPT frequently
deliberates about the payoff *and attempts anyway* (38.9% engaged at safe = 3 where it takes
SAFE 0% of the time). **Opus writes a payoff-engaged trace essentially if and only if it
chose SAFE.**

So Opus's trace-engagement gradient is **not independent evidence** of a decision-engagement
mechanism. It is close to a re-encoding of the behavioural outcome.

## 8. Stated probabilities — and a second measurement failure

Among payoff-engaged traces containing a number in [0.3, 1.0]:

| | n | median stated | median true (held-out) | corr(stated, true) | **corr(stated, safe/10)** |
|---|---|---|---|---|---|
| GPT-5.5 | 759 | 0.70 | 0.68 | −0.020 | **+0.987** |
| Opus 5 | 146 | 0.80 | 0.68 | −0.004 | +0.255 |

**GPT's numbers are not estimates — they are the break-even threshold.** Median stated value
is exactly 0.30 / 0.50 / 0.70 / 0.90 at safe 3/5/7/9. Its correlation with true match is
therefore uninterpretable; the extracted quantity is not a confidence judgment.

Opus is far less threshold-locked (median 0.85 at safe = 9 where the threshold is 0.90), so
its null is the interpretable one: **Opus's stated confidence does not track its actual
own-copy reliability** (r = −0.004, n = 146).

## 9–10. Answers

**1. Is the Opus effect present at the payoff where it engages?** Yes, weakly.
+0.137 at safe = 9, permutation p = .047, 18/27 pairs positive — but the naive CI
[−0.012, +0.286] straddles zero. Suggestive, not established.

**2. Is the manipulation equally strong?** **Yes.** Held-out Δ 0.419 vs 0.422. This
explanation is ruled out.

**3. Does payoff reasoning increase differently across payoff levels?** Within each model,
yes and differently in shape: GPT rises progressively from a high base (38.9 → 79.4%); Opus
is at floor through safe = 7 then jumps (0.0 → 63.9%). **Between-model levels are not
comparable** (§5–6).

**4. Does the evidence support "flat because not engaged" rather than "no self-policy
information"?** **Partially, and more weakly than it first appeared.** For it: the behavioural
match × payoff interaction is positive and significant within Opus (p = .047); the
manipulation is equally strong; the traces at safe ≤ 7 show shape-picking with no gamble
representation. Against it: Opus's trace state is ~the same variable as its decision
(V = 0.905), so the trace gradient is not independent evidence; and Opus's continuous
tracking is null at every payoff, which is what "has the information but isn't using it"
would *not* predict.

**5. What remains uncertain?**
- The three-way model × match × payoff interaction is **not significant** (p = .069). The
  headline "GPT progressive, Opus flat" may overstate a difference the data cannot resolve.
- Opus ran at depth 10 vs GPT's 24 — less than half the trials per payoff.
- The safe = 9-only result is a **post-hoc restriction**, motivated by the traces but not
  pre-registered.
- Trace artifacts differ by provider; no between-model level claim is supported.
- Verbal consistency between trace and behaviour is **not** evidence that the trace reports
  the mechanism. Opus's near-identity of trace code and decision is exactly what a
  post-hoc verbalisation would look like.

**The clean test the design already supports:** re-run Stage C on a payoff grid pitched at
Opus's decision boundary (e.g. 8/9/10/11) instead of 3/5/7/9. If own-match effects appear
across a grid where Opus deliberates throughout, the engagement account is supported without
relying on trace coding at all.
