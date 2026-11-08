# Addendum 01 to the Study 3A design memo — 2026-10-16 (PROPOSED; nothing adopted)

Responds to ChatGPT review `study3a-design-memo-refinement-01`. $0, no calls.

## 1. Relabelling option B
B changes **both** players' descriptions: mutual generic vs mutual named. It therefore estimates the **total dyadic disclosure intervention**, which includes Opus's possible response. It does not estimate the effect of information supplied to GPT alone.

Its contrast is generic "another AI … trained on different data" vs named "Claude Opus 5". So it tests **naming, i.e. model-specific disclosure**, not disclosing vs withholding partner identity in general.

## 2. For comparison only: C, focal-only disclosure vs withholding
- **Design:** the actual partner (Opus 5) and **its prompt** are held fixed. Only GPT's information varies:
  - arm 1: GPT is truthfully told the partner's identity;
  - arm 2: partner information is withheld from GPT.
- **Constraint:** both archived prompts state that "both of you receive … the same description", which would be false here. C therefore needs a **new fixed partner prompt and two new focal prompts** (wording not drafted or frozen).
- **Partner policy:** one Opus sample serves both focal arms, because model, settings, prompt and condition are identical. No existing cell matches the new partner prompt, so **nothing is reused**.
- **What C does not identify:** own-policy use. C identifies the value to GPT of external partner information.

## 3. Conditional arithmetic
Expected = pilot mean per call ($0.0103 GPT, $0.0066 Opus); bound = token-limit maximum. Estimates, not verified prices; a capped run may stop incomplete.

| option | per item | 4 items | 8 items | 19 items |
|---|---|---|---|---|
| A (v2, standalone) | – | – | – | 900 calls, $7.27 / bound $101.43 |
| B incremental to A, archived control | GPT 24 + Opus 36 | $1.94 | $3.88 | $9.21 |
| B standalone, archived control | GPT 24 + Opus 72 (36 on a pilot item) | $2.89* | $5.78* | $13.72* |
| B standalone, concurrent control | GPT 48 + Opus 72 | $3.88* | $7.75* | $18.42* |
| C (standalone = add-on) | GPT 2×24 focal + Opus 24 policy + 12 fresh | $2.93 | $5.86 | $13.91 |

\* Assumes no pilot items are among the chosen items. Each pilot item reduces B by 36 Opus calls (≈ $0.24).

- C per item: 84 calls, $0.73 expected, $9.74 bound.
- C's Opus draws are new policy and fresh-partner measurements; its GPT draws are focal only. Nothing is shared with A.
- Remaining budget is $15.25. A + C fits at 4 items ($10.20) or 8 items ($13.13) on expected cost, not on hard bounds.

## 4. Own-policy use
Establishing own-policy use, rather than a benefit of partner information, would need evidence that GPT's decisions track its own (manipulated or independently measured) policy beyond what an external auditor or partner information predicts, with partner information held constant.

## 5. Open Design decisions
- A, B (dyadic naming), C (focal-only), or a small combination.
- Item count, items fixed in advance, n_f.
- Concurrent vs archived controls.
- GPT `max_output_tokens`.
- Primary regret estimator.
- v2 D1–D7.
