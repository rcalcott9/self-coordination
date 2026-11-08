# Study 3A estimand and design memo — 2026-10-16 (PROPOSED alternatives; nothing adopted)

> **Refinement note (2026-10-16):** this memo is kept as proposed. After ChatGPT review (`study3a-design-memo-refinement-01`), option B is relabelled as a mutual (dyadic) naming intervention, the B costs are separated into incremental vs standalone, and a focal-only comparison (C) is added. See `DESIGN_MEMO_addendum_01_20261016.md`.


Request `study3a-estimand-design-memo-01`; $0, no calls.

## 1. What v2 (900 calls) estimates
**Question.** For focal GPT-5.5 on each of 19 items, in two joint conditions:
- **COPY:** actual partner GPT-5.5, described as a copy.
- **DIFFERENT:** actual partner Opus 5, described generically.

How close are GPT's archived actions to the best response to the actual partner's independently measured policy? Measured as normalized regret, realized payoff and matching. Opportunity s is reported per item.

**What it can show:** whether GPT's actions track what each actual partner requires (an association between joint conditions).

**What it cannot identify:**
- **Use of own-policy information:** nothing measures or manipulates it, and strong COPY play is equally consistent with shared salience.
- **The causal effect of disclosure:** partner, partner policy and description all change together, so it is not a framing intervention.
- **Generality** beyond one model, 19 items and Sep/Oct draws.

## 2. Alternatives (user decision; neither adopted)
**(A) v2 as proposed.** All 19 items: new GPT COPY policies, Opus DIFFERENT policies and fresh partners; archived GPT focal actions used for evaluation.
- *Addresses:* decision quality against actual partners, spread of opportunity, partner incompatibility.
- *Leaves open:* own-policy use, the disclosure effect.

**(B) Disclosure comparison with the actual partner fixed at Opus.**
- **Control:** the archived generic DIFFERENT prompt `8222a371`. It is truthful and symmetric for GPT and Opus.
- **Treatment:** new symmetric named disclosure. GPT is told "Claude Opus 5 (Anthropic)"; Opus is told "GPT-5.5 (OpenAI)". Needs new frozen prompt text.
- **Measurements per item:**
  - GPT named focal actions (n_f);
  - Opus named policy (24), since disclosure may also shift the partner;
  - Opus named fresh (12);
  - Opus generic policy and fresh for the control (36; included in A, otherwise extra).
- **Estimand:** the effect of mutual disclosure on GPT's regret with the partner model held fixed. The partner's response to disclosure is reported.
- **Archived generic control:** valid wording, but Sep/Oct draws; non-significant pooling is not equivalence. A concurrent arm (+24 GPT per item) removes the time difference.
- *Addresses:* the disclosure component.
- *Leaves open:* own-policy use; COPY (a truthful "different" description of a copy is impossible).
- *Depends on user decisions:* k (fixed before outcomes), n_f, and archived vs concurrent control.

| plan | GPT | Opus | expected* | hard bound** |
|---|---|---|---|---|
| A, 19 items | 360 | 540 | $7.27 | $101.43 |
| B, k = 4, archived control | 96 | 144 | $1.94 | $27.05 |
| B, k = 8, archived control | 192 | 288 | $3.88 | $54.10 |
| B, k = 19, archived control | 456 | 684 | $9.21 | $128.48 |
| B, k = 4, concurrent control | 192 | 144 | $2.93 | $38.96 |
| B, k = 8, concurrent control | 384 | 288 | $5.86 | $77.92 |
| B, k = 19, concurrent control | 912 | 684 | $13.91 | $185.07 |

\* Recorded pilot means ($0.0103 GPT, $0.0066 Opus); not newly verified prices. Resampling gave $7.57 for A.

\*\* Token-limit maxima: Opus $0.1051; GPT $0.1241 (needs `max_output_tokens` 4000).

- Without A, B needs +36 Opus calls per item.
- Remaining budget: $15.25. **A + B at k = 19 (≈ $16.5) does not fit; A + B at k = 4–8 (≈ $9.2–11.2) does.**
- Only the reserve-at-bound stop rule guarantees the $20 cap.

## 3. Scoring check (`code/scoring.py`, unchanged)
- **Plug-in regret is never negative.** `regret_norm` = (BR(q) − V(p, q))/10 with the **same** q. V is a p-weighted average of the action values EU_q(a), and BR is their maximum, so regret ≥ 0. Verified: minimum 0.0 over 20,000 random (p, q). Bootstrap replicates are also ≥ 0.
- **An independent shortfall can be negative.** BR from the policy sample minus realized payoff against fresh partners can go below zero (constructed case: −0.167).
- **Wording flagged, not edited.** "Not clipped" (docstring, pilot REPORT, v2) and the handover's "don't force negatives to zero" wrongly imply negative plug-in regret; the caution fits only independent shortfalls.
- **Plug-in max bias.** max_j q̂(PLAY j) overestimates the true maximum, most at ties or near s = .7. With true BR 7.00 the mean plug-in BR at n = 24 is 7.37, and regret inherits the bias.
- **Degenerate bootstrap.** Unanimous samples give zero-width intervals (pilot [10, 10]); a bootstrapped maximum is unreliable at ties. The Jeffreys interval for s avoids this.

## 4. Design decision questions
1. **Design decision:** A, B, or A plus a small B? A maps opportunity; B identifies disclosure; neither tests own-policy use.
2. **Design decision (if B):** k and how items are fixed in advance; n_f; archived vs concurrent control.
3. **Design decision:** GPT `max_output_tokens` 4000, so the $20 stop is guaranteed.
4. **Design decision:** primary regret estimator. Plug-in (≥ 0, biased upward) or independent shortfall (can be negative)? Update the wording either way.
5. v2 D1–D7 remain open.
