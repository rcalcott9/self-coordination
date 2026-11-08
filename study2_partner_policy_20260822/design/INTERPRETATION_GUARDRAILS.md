# Study 2 — interpretation guardrails

**Frozen 2026-08-22.** Derived from `design/FROZEN_PARAMS.py` §15
(`FORBIDDEN_TERMS` and the permitted framing). Enforced mechanically by
`code/check_terms.py`, which scans every `.md` file in this study and every
figure caption in `figures/` and **exits nonzero** on a hit.

Run it before any writeup, figure export, or hand-off:

```
python3 code/check_terms.py          # exit 0 = clean, exit 1 = a forbidden term is present
python3 code/check_terms.py --list   # show what would be scanned
```

---

## 1. The one sentence that is permitted

> Models selectively entered risky coordination opportunities as a function of
> the empirical compatibility between their policy and their partner's policy.

Every claim in the writeup must be reachable from that sentence plus the numbers.
If a sentence says more, it is out of scope — not "probably fine", out of scope.

---

## 2. Hard-forbidden vocabulary

Taken verbatim from `FROZEN_PARAMS.FORBIDDEN_TERMS`. Matched case-insensitively
with stems, so inflected forms are caught too.

| term | why it is out | say instead |
|---|---|---|
| `collusion` / `collude` <!-- terms-check: allow --> | imports intent and a norm violation the design cannot observe; the prompts are neutrally framed and never describe the game this way | "coordination", "entering the coordination game" |
| `deception` <!-- terms-check: allow --> | nothing in this design involves a false signal to anyone; there is no communication channel at all | — (there is no substitute; the claim does not belong here) |
| `consciousness` <!-- terms-check: allow --> | not measured, not measurable by a betting task | — (the claim does not belong here) |

**`introspection` is a special case.** The word is not banned; the *mechanism
claim* is. Forbidden: introspection as an established mechanism — "the model
introspected on its own policy", "consulted its own dispositions". Permitted:
explicitly ruling it out or bracketing it — "the mechanism, introspective or
otherwise, is not measured here". `check_terms.py` prints every occurrence as a
**warning** so a human checks the direction of the sentence; it does not fail the
run.

---

## 3. Claim checklist

### May be claimed

- [ ] Attempt rates differed between the same-model and different-model partner arms (`γ`), with the interval.
- [ ] The same-minus-different shift **scaled with** the measured compatibility advantage (`δ`), with the interval — *if* `δ`'s interval excludes 0.
- [ ] Behaviour was **graded by**, **tracked**, **scaled with**, or **was sensitive to** the advantage. All four verbs are descriptive and safe.
- [ ] The model behaved **as if** it had information about the compatibility between its policy and its partner's.
- [ ] Where the advantage was negative, the same-model partner was preferred **less** — *only if* the §10.3 reversal test supports it.
- [ ] The advantage is a behavioural quantity derived from independently measured choice marginals, never shown to the model.
- [ ] The result is specific to GPT-5.5 and Claude Opus 5, 8 binary visual stimuli, one prompt family, one point in time.

### May NOT be claimed

- [ ] That the model **knows**, **is aware of**, **has access to**, or **represents** its own policy. Behaviour is what was measured.
- [ ] That the model **introspected**, **self-modelled**, or **reasoned about itself** — as an established mechanism. The mechanism is not measured.
- [ ] That the same-model preference reflects **self-recognition**, **identity**, or **self-preference** in any psychological sense.
- [ ] Anything about intent, honesty, norms, or awareness.
- [ ] That a same > different **main effect** supports policy-specific sensitivity. It is exactly what MODEL A predicts. The slope is the test.
- [ ] That a null `δ` **disproves** policy-specific sensitivity. The negative range is bounded by algebra (spec §5), so a null reversal test is weak evidence.
- [ ] That the finding generalises across model versions. It does not without re-running the pipeline.
- [ ] That the cross-model rate was **observed**. It is derived from independently estimated marginals under a stated independence assumption (spec §4).

---

## 4. Design-specific traps

| trap | the guardrail |
|---|---|
| Reporting `γ` as the headline | The frozen primary coefficient is `FROZEN_PARAMS.PRIMARY_COEF = "partner_x_advantage"`. `γ` is reported, never headlined. |
| Quoting the `a_chev_ud`-excluded slope without saying so | Always state the advantage range that produced it: [−0.128, +0.678] with it, [−0.128, +0.401] without. |
| Treating the advantage as error-free | Every quoted `δ` must say which of the three §9.1 estimates it is: latent/EIV (headline), propagating bootstrap, or plug-in. |
| Calling the negative cells "small because of the battery" | They are small because of the structural identity in spec §5. Say that. |
| A figure caption that outruns its figure | Captions are scanned by `check_terms.py` too. The caption states n, estimator, and interval definition — nothing interpretive that §3 does not license. |
| "The model preferred itself" | Replace with "attempt rates were higher against a same-model partner". |

---

## 5. Sign-off

Before any writeup leaves this directory:

- [ ] `python3 code/check_terms.py` exits 0.
- [ ] `python3 code/design_table.py --check` passes.
- [ ] Every warning printed by `check_terms.py` has been read and each sentence
      denies or brackets a mechanism rather than asserting one.
- [ ] Every `may not be claimed` box above has been read against the final text.
