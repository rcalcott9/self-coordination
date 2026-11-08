# Study 2 (4-option) — frozen design decisions

`2026-08-30`. Records what was decided and *why*, especially where this study
departs from Study 1. Numbers cited here were computed from existing data before
any new API call.

## Why four options and not two

The two-option version of this design is structurally incapable of the test.

Binary self-match is `p² + (1−p)²`, minimised at `p = .5`. **The floor is .50.**
With AB/BA randomisation a position-responding model also sits at exactly .50. So
in a two-option game "low self-match" and "position fallback" are the same event,
and the two selection criteria collide:

- criterion "gap ≥ .30" forces the low member near chance
- criterion "exclude positional fallback" then removes it

Measured on the frozen Study 1 battery (same models, same estimators):

| self-match | n stimuli | of which position-fallback |
|---|---|---|
| ≤ .60 | 11 | **11** |
| ≥ .75 | 17 | **0** |

Perfect separation — no non-fallback low-self-match stimulus exists. The candidate
funnel over 210 pairs confirms it, collapsing at exactly that step:

```
GPT-5.5        high ≥.75: 84 → low ≤.55: 32 → gap ≥.30: 32 → |Δaud| ≤.10: 28 → no fallback: 0
Claude Opus 5  high ≥.75: 90 → low ≤.55: 54 → gap ≥.30: 45 → |Δaud| ≤.10: 36 → no fallback: 0
```

A `low ≤ .45` threshold is additionally unreachable at two options: **0 of 210**
pairs meet it, and the minimum observed low member across all 30 cells is 0.4915
(the bias correction dipping below chance, not signal).

At four options chance is .25, so the three states separate:
position fallback ≈ .25, weak-but-real convention ≈ .35–.55, strong ≥ .75.

## Fallback is a covariate, not an exclusion

**Decision (2026-08-30, user).** At four options a position responder scores .25 —
which *is* chance. It is a genuine floor, not an artefact inflating anything, so it
does not need removing. Position bias is computed per cell, recorded, and reported
as a robustness split; it does **not** veto a stimulus or a pair.

Consequence to report rather than leave implicit: on a positional low member, own-
match and cross-match both sit near .25, so it is a clean zero-advantage floor and
the model-specificity criterion is carried by the high member.

## What is preserved from Study 1

Model ids (`gpt-5.5` → pinned `gpt-5.5-2026-04-23`, `claude-opus-5`), inference
settings (`effort: low` both sides; temperature is rejected with a 400, so it is
never set), the unbiased dyadic match estimator, raw-response-before-parsing,
no-silent-drop, and the shape of the Stage A / auditor / salience prompts. Only the
arity changes: "two shapes" → "four shapes", LEFT/RIGHT → 1–4.

Auditor prompts for the two focal models are byte-identical after name
normalisation (asserted in `test_s4.py`), so an auditor or partner effect can never
be a wording effect.

## Position schedule

Every stimulus renders all 24 orderings. A run of `n` trials uses a schedule in
which **every item appears in every position exactly n/4 times** — constructed, not
sampled, and asserted at build time (`s4_common.position_schedule`). Verified
against live data in the smoke test: exact balance in every cell, zero
manifest round-trip mismatches.

## Battery

16 families × 8 members = **128 stimuli**, four payoff-equivalent options each.
Each family varies one parameter from a strong-focal to a weak-focal setting; which
member lands where is decided by Stage A, not by the generator. Blind and frozen
before any API call — no generate-test-regenerate loop, no stimulus designed
because a named model was observed to prefer a named feature.

Render defect caught at review and fixed before any spend: sparse random-placement
families (`F13_count`) spilled marks across panel gaps, making an option's marks
unattributable. Fixed with a tinted panel ground plus a tighter placement radius.

## Discovery / validation split

- **discovery**, n = 24/model/stimulus — ranks candidates, shortlists.
- **validation**, n = 60/model/stimulus — held out, and the only numbers selection
  is allowed to touch.

Using one sample for both is the winner's curse that halved `a_chev_ud`
(+0.650 → +0.294) on the Aug-22 screen, and it is why the split is enforced by
separate files and separate run modes.

## Cross-model match

Estimated **directly** from the two models' independent Stage A draws
(`Σₖ pₖqₖ`), never inferred from within-model marginals. Note the binary algebraic
pinning `|GC−½| = √((GG−½)(CC−½))` — verified at mean |residual| 0.006 over 15
stimuli — does **not** hold at four options, so own-copy and cross-model are
genuinely separable quantities here. That is a second structural gain from the
arity change.

## Open items carried into Stage C (not yet authorised)

1. **A null is plausible for reasons upstream of stimulus design.** The previous
   Study 2's GPT arm was a null with teeth (slope −0.056, CI [−0.234, +0.118], LOSO
   favouring the no-partner model, g₀ ≈ 0). Trace diagnosis found the partner
   manipulation barely reaches the rationale: 0 of 1,424 trials with policy talk,
   partner mentioned 3.5%/4.5%, attention anti-correlated with where partner
   identity mattered. Recommend a manipulation check before committing to 11,520
   Stage C trials.
2. **Model-specificity should gate the high member, not merely be preferred.** On
   the binary battery, 5 of 8 GPT stimuli with own ≥ .75 had own − cross ≈ 0.000.
   On a shared convention a same-model partner buys nothing, so β₃ = 0 is the
   *correct* behaviour there.
3. **Realized coordination** was called essential in an earlier spec revision and
   is absent from the current one. Recoverable at zero API cost by scoring against
   held-out Stage A choice distributions, since partners are fresh independent draws.
4. **Payoff grid likely censors.** EV(ENTER) = 10 × match: high members 7.5–10, low
   members 2.5–4.5. Against {3,5,7,9} the informative cells are mainly 5 and 7.
   Study 1's safe=3/5 cells were 39 of 40 at exactly 1.000 and bought no
   information and no permutation variance.
5. **Fit on the logit scale.** A constant log-odds shift manufactures a spurious
   risk-difference interaction when baselines vary with the predictor (+0.063 in the
   Aug-22 adversarial simulation); with high members near ceiling and low near
   floor, baselines vary maximally. Report the risk difference as secondary, with
   the baseline-artefact diagnostic.
