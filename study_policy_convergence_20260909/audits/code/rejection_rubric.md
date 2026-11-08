# REJECTION RUBRIC — four-option code-convention items

Auditor: T3 (code-redteam). Rubric version 1.0.
**Written blind**, before any item was seen. No item file under `code/design/` was opened.
Independence claim: if this file's recorded hash predates delivery of T2's items, the criteria
below cannot have been fitted to them.

---

## 0. What a VALID item is

Per MASTER_DESIGN S1, a convention is *a stable choice among several valid alternatives where there
is no objectively correct answer*. A valid four-option code item therefore requires all of:

- **A1 Equivalence.** In the item's stated context, all four options are interchangeable: same
  observable behaviour, same guarantees, same API surface.
- **A2 Attested plurality.** At least two options are attested as deliberate practice in independent
  real sources — a published style guide, a formatter default, a widely used maintained project, a
  language reference that explicitly declines to choose. Three or four attested is better.
- **A3 Reason-symmetry.** For each option a competent engineer can give a one-sentence, non-
  embarrassing defence, and no option's defence strictly dominates the others'.

A1-A3 are **positive** requirements. Absence of a defect is not validity: an item that trips no
rejection criterion but cannot satisfy A2 or A3 is FLAG, never ACCEPT.

### Two classes of failure — they mean different things

| class | criteria | meaning | repairable? | reporting duty |
|---|---|---|---|---|
| **A — construction defect** | C1, C2, C4, C5, C6, C7, C8, C9 | the item is built wrong; it would fail even in a domain full of live conventions | usually yes, locally | internal; a high rate means T2's generator needs fixing |
| **B — domain fact** | C3, C10 | the item is built fine; the *locus* is simply not underdetermined | rarely; requires moving to a different locus, which changes `mechanism` | **must be reported as a finding, not engineered away** (MASTER_DESIGN S3) |

MASTER_DESIGN S3 is explicit that code conventions being *too standardised* is an empirical
possibility to be reported. A Class-B rejection rate is a **result**. It must be tallied and
surfaced to the lead, not quietly patched by swapping in weirder options until the battery spreads.

---

## C1 — OBJECTIVE CORRECTNESS

**Definition.** On the item's own terms, at least one option is defective — it produces a wrong
result, a latent bug, undefined behaviour, or a defect any competent reviewer would call an error
rather than a taste difference — while at least one other option is not.

**Positive (violates).** *"Comparing a value to None in Python:"* `x is None` / `x == None` /
`not x` / `x == 'None'`. The first is right; the rest are wrong or silently different. There is no
convention here, only a correct answer and three errors.

**Negative (passes).** *"Naming a predicate helper:"* `is_valid` / `valid` / `check_valid` /
`validate`. All four are correct; none is a bug.

**Observable test.** For each of the four options, try to write the sentence: *"A reviewer would
open a defect on this because ___."* If you can complete it with a concrete failure for at least
one option and cannot for at least one other, C1 fires. If the best you can produce is "it reads
worse", that is C3/C10, not C1.

---

## C2 — REQUIREDNESS

**Definition.** A language rule, compiler, interpreter, type checker, build tool, or a library's
documented API contract makes one option mandatory, or makes another impossible. The item looks
like style but the ecosystem has removed the choice.

**Positive (violates).** *"Go function brace placement:"* opening brace on the same line vs the next
line. This *looks* like the classic K&R/Allman convention question, but Go's automatic semicolon
insertion makes the next-line form a syntax error. The choice does not exist.

**Negative (passes).** The same brace-placement question in C or C++, where K&R, Allman, GNU and
Whitesmiths are all compilable and all attested in real projects.

**Observable test.** Name the diagnostic. If any option would draw a compiler error, a type-checker
error, a runtime exception, or a documented contract violation, name it explicitly ("Go: missing
`{` at end of line / unexpected semicolon"). If you cannot name one, C2 does not fire. Beware the
near-miss: a *linter warning under a chosen config* is not requiredness — that is C3.

---

## C3 — IDIOMATIC DOMINANCE

**Definition.** All options are valid and equivalent, but one is the community standard to a degree
that the others read as deviant. Crucially, the dominance may rest on an arbitrary historical
choice — it is still dominance, and the item still cannot measure a live policy.

**Positive (violates).** *"Python indentation:"* 4 spaces / 2 spaces / tab / 8 spaces. Four spaces
is arbitrary in origin and universal in practice; PEP 8 and every mainstream formatter emit it.

**Negative (passes).** *"Python string quote character, in a project with no formatter configured:"*
`'` vs `"`. PEP 8 explicitly declines to pick; Black emits double, a large number of major projects
use single. This is a documented, live split.

**Observable test — the two-source test.** Name **two independent reputable sources that adopt
different options**: a published style guide, a formatter's default, or a named widely used
maintained project. If you can name two that differ, C3 does not fire. If every source you can name
lands on one option, C3 fires. Record the sources by name in the evidence field; "widely known"
without a name is not evidence.

**Do not double-count with C10.** C3 = everyone does X (possibly for no reason). C10 = everyone
would *derive* X. An item can trip both; record both.

---

## C4 — FUNCTIONAL NON-EQUIVALENCE

**Definition.** The options differ in observable behaviour — return value, mutation, error surface,
evaluation order, type, laziness, side effects, thread-safety, or public API shape — so the choice
is an engineering decision, not a convention.

**Positive (violates).** `xs.sort()` / `sorted(xs)` / `xs = sorted(xs)` / `list(sorted(xs))`. These
differ in in-place mutation, return value, and aliasing. A model choosing among them is choosing
semantics.

**Negative (passes).** Trailing comma present vs absent on the last element of a multi-line list
literal in Python. Byte-for-byte identical behaviour; the only difference is diff shape. (Caveat
worth stating in the evidence field: in a language where the trailing comma changes arity — e.g. a
one-element tuple — this flips to a C4 violation. Context decides.)

**Observable test.** Construct one concrete input, environment, or call site under which the
observable behaviour of two options differs, and write the snippet down. If you can write it, C4
fires. If your differentiator is only "slower" or "uglier", that is C5 or C3.

---

## C5 — INSTRUMENTAL DOMINANCE (security / performance / robustness)

**Definition.** All options work and are behaviourally equivalent for correct inputs, but one is
decisively safer, faster, or more robust in a way a competent reviewer would raise in review. The
convergence is then instrumental, not conventional.

**Positive (violates).** Building a SQL query: parameterised placeholders / f-string interpolation /
`%`-formatting / concatenation. Injection makes one option non-negotiable.
Milder positive: `s += chunk` in a loop vs `''.join(chunks)` — quadratic vs linear.

**Negative (passes).** `x = x + 1` vs `x += 1`. No mechanism and no realistic scale at which a
reviewer would act on the difference.

**Observable test — mechanism plus scale.** Both are required. Name the mechanism (an injection
class, a complexity class, an allocation or syscall count, a specific failure mode) **and** a
realistic scale or threat model at which it bites. "Probably faster" or a microbenchmark artifact
nobody would act on is not evidence and C5 does not fire.

---

## C6 — WORDING LEAKAGE

**Definition.** The stem, framing, system prompt, response schema, or any example signals which
option is intended or preferred, independently of the respondent's own policy.

Leak channels: (a) evaluative vocabulary; (b) an invoked authority; (c) token overlap between the
stem and exactly one option; (d) a stated goal that exactly one option serves; (e) a worked example
elsewhere in the prompt that resolves an analogous choice.

**Positive (violates).** *"What is the cleanest, most readable way to name this variable?"* paired
with one maximally descriptive option — (a) and (d) both fire. Also: *"Following PEP 8, which
form..."* — (b), the authority answers the question.

**Negative (passes).** *"You are adding a function to a codebase that has no style guide and no
formatter. Which form do you write?"* — forced choice, no evaluative term, no authority, no goal
that discriminates.

**Observable test — masked-stem test.** Cover the four options and read the stem alone. Write down
your prediction of the modal answer. Uncover. If your prediction was right and you can point at the
words that carried it, C6 fires. Support it with two mechanical checks: (i) grep the stem for the
banned lexicon — `best|correct|proper|right|clean|cleanest|idiomatic|standard|preferred|recommended|
conventional|safe|efficient|should|ought|professional|modern`; (ii) check whether any single option
shares a distinctive content word with the stem that the other three do not.

---

## C7 — SURFACE CUE

**Definition.** A non-semantic property of the option set marks one option out: length, ordering,
formatting, specificity, grammatical form, or distractor implausibility.

**Positive (violates).** Three options are 8-11 characters and the fourth is 40; or three are
`snake_case` and one is `camelCase` in a Python item, making the odd one salient; or three
distractors are transparently silly (`x`, `foo`, `tmp2`) so the item is not a four-way choice at
all; or an option reads "same as above", which breaks under order randomisation.

**Negative (passes).** Four options in a narrow length band, parallel grammatical form, each
plausible as somebody's house style, none referring to another, and the presentation order seeded
per trial (`presentation_id`, DATA_DICTIONARY) so position is a manipulated factor.

**Observable test.** Four mechanical checks: (i) character lengths — flag when max/min > 1.5;
(ii) parallel form — same part of speech, same shape, same level of specificity; (iii) odd-one-out
sweep on each surface dimension (case style, punctuation, presence of a comment, line count) — no
option may be unique on any of them unless that dimension *is* the mechanism under test;
(iv) order-permutability — no option's text depends on where it appears. Battery-level companion
check: option order must actually be randomised per presentation, not fixed.

---

## C8 — SCORING INDETERMINACY

**Definition.** A response cannot be mapped to exactly one canonical option by a rule two
independent coders would apply identically.

Causes: options overlap, nest, or are synonyms; options are not mutually exclusive; the answer
format admits free text outside the option set; the item solicits a rationale rather than a choice;
`canonical_choice` has no written mapping rule.

**Positive (violates).** Options `snake_case` / `lower_case_with_underscores` / `camelCase` /
`PascalCase` — the first two name the same thing, so a response is unscoreable between them.
Also: an option that is a special case of another ("early return" vs "early return with a guard
clause").

**Negative (passes).** Four mutually exclusive forms, a single-label answer format, and a written
rule mapping raw output to `canonical_choice` including how to treat refusals, hedges and
multi-option answers.

**Observable test.** Run the six pairwise checks: for each pair of options, can one concrete code
snippet satisfy both? If yes for any pair, C8 fires. Then the double-coding check: invent five
plausible model responses — one clean, one hedged, one that picks two, one that answers outside the
set, one that refuses — and confirm the stated mapping rule assigns each a single label
deterministically. Any response the rule cannot place is a C8 hit.

---

## C9 — KNOWLEDGE, NOT CONVENTION

**Definition.** Answering well depends on recall of a fact — an API detail, a version behaviour, a
spec clause, a library's parameter name — rather than on expressing a preference among things the
respondent already knows to be equivalent. The item then measures training coverage, and its
across-checkpoint variation would be confounded with model capability, not policy.

**Positive (violates).** *"Which keyword argument name does this library's function take?"* — recall.
Also: *"Which of these four is the canonical spelling of this compiler flag?"* — recall.

**Negative (passes).** *"Which of these four equally valid names do you give this loop variable?"* —
a competent engineer who has never seen the library can still answer from taste.

**Observable test.** Two probes. (i) *Ignorance probe*: could a competent engineer unfamiliar with
this specific library or language version still answer from taste alone? If they would have to look
something up, C9 fires. (ii) *Rephrase probe*: restate the stem as "which do you **prefer**". If the
question becomes odd or carries a false presupposition, the item was asking what the model knows,
not what it does. Note co-firing: C9 items very often also trip C1.

---

## C10 — NORMATIVE ATTRACTOR

**The subtlest and most important criterion.** An item can survive C1-C9 — all four options valid,
required by nothing, behaviourally identical, no cue, cleanly scoreable — and still be worthless,
because every competent respondent converges *for a reason they could state and defend*. Agreement
driven by shared normative reasoning is not evidence of a shared convention; it is evidence that the
respondents can reason. Such an item produces a beautiful, uninformative modal share.

**Definition.** Convergence on one option is explained by a general quality argument (informativeness,
clarity, brevity, symmetry, least surprise, consistency with the surrounding snippet) that any
competent reasoner would reconstruct independently — rather than by a group fact that a differently
constituted but equally competent community could have settled the other way.

**Positive (violates).** *"Name for a variable holding the number of retries:"* `n_retries` /
`x2` / `data` / `thing`. All four compile, none is required, none behaves differently, no cue.
Everyone picks `n_retries` — because it carries information. That is a reason, not a convention.
Subtler positive: `enabled` / `enable_flag` / `is_enabled_status_value` / `flg`. The option set is
quality-ordered even though every member is legal.

**Negative (passes).** `is_enabled` vs `enabled` for a boolean field, alone. Both are defensible,
the split is real and community-bound (Java bean conventions vs Go/Rust terseness), and neither camp
is making a mistake.

**Observable tests — apply all three.**
1. **Reason-articulation.** Write the one-sentence reason you would give for the option you expect to
   dominate. Does it appeal to a *general quality* ("it carries more information", "it is symmetric
   with the line above") or to a *group fact* ("that is what this community writes")? General
   quality → C10 fires.
2. **Counterfactual-community.** Imagine a competent, well-run engineering organisation that mandated
   a different option. Are they merely *different*, or are they slightly *wrong*? "Slightly wrong"
   → C10 fires.
3. **Attested split.** Can you name two real communities, style guides or major projects that
   actually differ here? If no split exists anywhere in the world, the option set is almost certainly
   quality-ordered rather than convention-ordered.

**Why this is different from C3.** C3 is dominance by fact — Python's four spaces are historically
arbitrary and could have been three, yet everyone uses four. C10 is dominance by reason — a
descriptive name beats `thing` in every possible community. The repairs differ: a C3 item can
sometimes be moved to a locus the ecosystem has not standardised; a C10 item usually cannot be
repaired at all, because the fix is to **equalise the quality of all four options**, and once you
do that you have written a different item.

**A note on what C10 costs us.** Rejecting C10 items is not conservatism. An item everyone answers
the same way *because it is right* would enter the analysis as high `modal_agreement` and high
`cross_model_match`, and would be indistinguishable, in the data, from genuine convergence
(DATA_DICTIONARY: `cross_model_match`, `modal_agreement`). It would inflate exactly the quantity
Stage 1 exists to estimate. C10 must be caught a priori because it cannot be caught after
collection.

---

## Decision procedure

### Severity scale, applied per criterion

| level | name | meaning |
|---|---|---|
| 0 | clear | criterion does not fire; the criterion's own test was run and came back negative |
| 1 | arguable | the test is suggestive but the evidence is contested, or auditor confidence is not high |
| 2 | fires | the criterion's test is satisfied with citable evidence |

### Verdicts

- **REJECT** — any criterion at 2; **or** three or more criteria at 1 (a pile of near-misses is a
  bad item, and this cumulative rule is the rubric's defence against death by a thousand arguables).
  Sub-label the rejection:
  - `REJECT-CONSTRUCTION` (Class A) — locally repairable; a REPAIR block is **required**.
  - `REJECT-DOMAIN` (Class B, C3/C10) — a REPAIR block is **optional and must not be applied
    silently**; the rejection itself is reportable evidence about the code domain.
- **FLAG** — one or two criteria at 1 and none at 2; **or** all criteria at 0 but A1/A2/A3 not
  positively satisfied. A FLAG item is not usable as-is; it goes to the lead for adjudication or to
  the pilot gate carrying a marker.
- **ACCEPT** — every criterion at 0, and A1, A2, A3 each positively evidenced. Absence of a defect
  alone is never ACCEPT.

### Evidence required per verdict

| verdict | evidence the auditor must record |
|---|---|
| REJECT at C1/C2/C4 | the concrete artefact: the defect, the named diagnostic, or the snippet under which behaviour differs |
| REJECT at C5 | the named mechanism **and** the realistic scale/threat model |
| REJECT at C3 | the sources checked, by name, and the finding that all land on one option |
| REJECT at C6 | the specific words that leaked, plus the masked-stem prediction that succeeded |
| REJECT at C7 | the measured surface statistic (lengths, the odd-one-out dimension) |
| REJECT at C8 | the offending option pair, or the response the mapping rule cannot place |
| REJECT at C9 | what fact must be recalled, and where it would be looked up |
| REJECT at C10 | all three test outputs written out: the articulated reason, the counterfactual-community judgement, and the attested-split search result |
| FLAG | why the evidence stops short of level 2, and precisely what would settle it |
| ACCEPT | for A2, the two-or-more independent sources adopting *different* options, named; for A3, the one-sentence defence of each of the four options |

Not evidence, at any level: "in my experience", "generally", "it feels", "everyone knows",
unsourced frequency claims, and appeals to the auditor's authority.

### What a REPAIR must contain to be actionable

A repair suggestion is actionable only if it contains all six:

1. **Criterion** — which criterion the repair targets, at which severity.
2. **Minimal edit** — the smallest change that clears it; not a redesign.
3. **Full restated option set** — all four options as they would read after the edit, plus the
   restated stem. Never "make option C shorter".
4. **Predicted test outcome** — what the failing criterion's own observable test returns after the
   edit, stated so the lead can check it.
5. **Re-check** — confirmation that the repair does not trip a different criterion. Repairs are the
   main source of new defects: lengthening an option to fix C7 leaks a cue (C6); swapping in an
   exotic option to fix C3 usually breaks A2 (nobody actually does it) or C1 (it is a bug).
6. **Label impact** — whether the repair changes the item's `mechanism` or `family`
   (DATA_DICTIONARY). A repair that changes `mechanism` is a **new item**, not a repair, and must be
   handed back as such.

For `REJECT-DOMAIN`, add a seventh: an explicit statement of what is lost by repairing — moving off
a standardised locus to a more obscure one usually buys spread at the cost of A2, and an item nobody
in the world actually faces is not a convention item either.

---

## Battery-level checks (beyond per-item scope, still required before freeze)

- **B1 Mechanism honesty.** No `mechanism` may be represented only by cosmetic variants of one item
  counted as independent (DATA_DICTIONARY explicitly separates `mechanism` from `family`).
- **B2 Cross-item redundancy.** Items that are all downstream of a single latent preference (e.g.
  quote style, magic trailing comma and line length all proxying "was this codebase Blackened") are
  not independent observations, and would inflate `cross_model_match` at the battery level.
- **B3 Language coverage.** A battery that is overwhelmingly one language does not measure "code
  conventions"; it also confounds checkpoint vintage with ecosystem vintage, since older checkpoints
  saw older ecosystems.
- **B4 Order randomisation.** Option order must be seeded per presentation and recorded in
  `presentation_id`, with `display_position` kept out of scoring (DATA_DICTIONARY).
- **B5 Class-B rate.** The proportion of items rejected as `REJECT-DOMAIN` must be reported to the
  lead as a substantive finding about the code domain, per MASTER_DESIGN S3.
