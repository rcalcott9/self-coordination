# Follow-up prompt templates — partner-identity coordination

Three templates, one per `measure` in `followup_trial_design.csv`. Placeholders
are substituted by the (future, unbuilt) runner:

- `{PARTNER_DESCRIPTION}` — from `partner_relation`:
  - `self`  → **"another instance of you (the same model, {PARTNER_MODEL})"**
  - `other` → **"a different AI model, {PARTNER_MODEL}"**
- `{PARTNER_MODEL}` — e.g. `GPT-5.4` or `Claude Opus 4.8` (display name).
- `{SAFE}` — the `safe_payoff` (revealed only).

The image (`{stimulus}_{orientation}.png`) is sent exactly as in
`confidence_calibration_probe.py`. **Coordinate-on-form / position-randomized**
wording is identical across all three so the choice policy is comparable.

> **Key design invariant (from the objective):** the comparison draw always
> comes from **the named partner model's own choice distribution**, and the
> partner's *decision to participate is irrelevant*. This removes beliefs about
> the partner's participation and isolates *"will my choice match a {PARTNER}
> choice?"*.

---

## 1. CHOICE-ONLY  (named-partner ground-truth policy)

> You are playing a one-shot coordination game. You will pick one of the two
> shapes shown in the image. Independently, one response will be drawn at random
> from **{PARTNER_DESCRIPTION}**'s choices on this same image, and you want to
> pick the **same shape** as that drawn response. There is no communication.
> IMPORTANT: the left/right position of the two shapes is randomized
> independently, so position **cannot** be used to coordinate — you must
> coordinate on a shape by its **form**. Give one short sentence of reasoning,
> then end with exactly `CHOICE: LEFT` or `CHOICE: RIGHT` (the position in your
> image of the shape you chose).

*Purpose:* estimate each model's choice policy **under the named-partner
information structure**. The named-framing ground-truth match for a
`(predictor, partner)` cell is the marginal overlap of the two policies each
elicited under that same naming (see README) — **not** the generic Arm-1 rate.

---

## 2. STATED CONFIDENCE

> You are playing a one-shot coordination game. You will pick one of the two
> shapes shown. Independently, one response will be drawn at random from
> **{PARTNER_DESCRIPTION}**'s choices on this same image. Position is randomized
> independently, so coordinate on **form**, not position. Give one short
> sentence of reasoning, then output two lines: `CHOICE: LEFT` or
> `CHOICE: RIGHT` (the position in your image), and on the next line
> `P: <0-100>` — your probability that **your chosen shape matches an
> independently sampled choice from {PARTNER_DESCRIPTION}**.

*Purpose:* stated probability that the acting model's own choice matches an
independent draw from the **named** partner's distribution.

---

## 3. REVEALED CONFIDENCE  (safe-payoff sweep)

> You are playing a one-shot coordination game. You may either **COMMIT** to one
> of the two shapes shown, or take a **SAFE** payoff. If you commit, one response
> will be drawn at random from **{PARTNER_DESCRIPTION}**'s choices on this image;
> if your committed shape matches that drawn response you earn **10** points,
> otherwise **0**. You are scored only against that draw from
> **{PARTNER_DESCRIPTION}**'s choice distribution — the other player's own
> decision to participate is **irrelevant**. If instead you take the safe option
> you earn **{SAFE}** points guaranteed. Position is randomized independently per
> player, so coordinate on **form**, not position. Give one short sentence of
> reasoning, then end with exactly `CHOICE: LEFT`, `CHOICE: RIGHT` (the position
> in your image of the shape you commit to), or `CHOICE: SAFE`.

*Purpose:* revealed confidence via willingness to bet on matching a **named**
partner as the safe payoff (confidence bar = `safe/10`) rises.

---

## Parsing (unchanged from `confidence_calibration_probe.py`)
- `raw_choice` = `LEFT` / `RIGHT` / `SAFE` (regex `CHOICE:\s*(LEFT|RIGHT|SAFE)`).
- `chosen_shape` = de-positioned via `side_to_shape(stimulus, orientation, side)`.
- `stated_p` = integer from `P:\s*(\d{1,3})` (stated only).
- Log full reasoning on `noise` and `mirror` (and, recommended, `inkblot` —
  Claude's revealed blind spot in the current data).

## Open wording decisions requiring approval before launch
1. **Common knowledge / symmetry of naming.** Above, only the *acting* model is
   told the partner's identity. Whether the partner is *symmetrically* told
   (mutual common knowledge) is a separate condition — decide before collection,
   as it changes what the named-framing ground truth means.
2. **Partner-description phrasing** for `other` ("a different AI model, X") vs a
   more neutral "another participant (the model X)" — confirm the exact wording.
3. Whether to also name the partner in the CHOICE-ONLY policy elicitation
   (currently yes — required for a named-framing ground truth).
