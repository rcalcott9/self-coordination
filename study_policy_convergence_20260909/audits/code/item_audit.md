# ITEM AUDIT — code-convention candidate battery `code_conv_candidate_v0.1`

Auditor: T3 (code-redteam). Date 2026-09-09. **No API calls were made.**
Rubric: `rejection_rubric.md` v1.0, sha256 `230ca3d8…`, frozen before `code/design/` existed.
Procedure: `audit_procedure.md` v1.0, sha256 `4c16fe45…`. Machine-readable decisions:
`item_decisions.csv`.

Audited: 36 items, 12 mechanisms x 3, 24 families; `prompts/code_prompt_v1.json`; `code/design/SCHEMA.md`.
`design_notes.md` S4 was read only AFTER all 36 verdicts were fixed, per procedure S0.

---

## 1. Headline

| | count | share |
|---|---|---|
| ACCEPT | 11 | 31% |
| FLAG | 14 | 39% |
| REJECT (List A, invalid) | 11 | 31% |
| **List B (valid-but-universal, RETAINED)** | **1** | **3%** |
| List B watch (C3 or C10 at severity 1) | 12 | 33% |

**Construction-defect rate: 11/36 = 31%.** This implicates the generator, not the domain.
**Domain-fact rate: 1/36 = 3% confirmed, 12/36 = 33% suspected.**

The two rates point in opposite directions, and that is the main result of this audit. The code
domain does **not** look overwhelmingly standardised on this battery — by a priori judgement only
one item (`code_error_003`) is one where every competent model should agree for normative reasons.
What actually threatens the battery is construction defects, and nine of the eleven are repairable
with edits of one line or one option.

**Caveat that cuts against my own headline (S5.1): the battery is systematically biased toward
looking LESS standardised than the domain is.** Eight items split one convention across two
near-synonymous options. Since MASTER_DESIGN S3 makes standardisation the reportable null, a bias
against detecting standardisation is a bias toward the more interesting result, and it must be
corrected or declared before Gate 1.

## 2. One interpretive rule I had to add, stated openly

My rubric's C4 (functional non-equivalence) lists "public API shape" among the things that make
options non-equivalent. Applied literally that would reject most of `return_representation`,
`error_representation`, `serialization` and `interface_layout` — which would be wrong, because API
shape is one of the most important real convention classes. I therefore adjudicated C4 as:

> **C4 fires only when options differ in information carried, guarantees given, or failure modes —
> not when they differ merely in how a caller spells access to the same contract.** The test is
> whether a caller need that the spec states or clearly implies is served by one option and not
> another.

This is an interpretive extension of a blind rubric and the lead should review it, because it is
load-bearing: under the literal reading, 9 further items would be rejected. Under the adopted rule,
`code_return_001` (tuple/dict/namedtuple/dataclass) is valid and `code_return_003`
(mutate/copy/fluent/lazy) is not — the first four spell one contract four ways, the last four are
four different contracts.

## 3. Verdict mapping to D-009

D-009 arrived after the rubric was frozen and maps exactly onto the Class A / Class B split I
derived independently, so no re-scoring was needed. Applied as:

- **verdict** is determined by List-A criteria alone (C1, C2, C4, C5, C6, C7, C8, C9): any at
  severity 2, or three or more at severity 1, → REJECT → **List A, removed**.
- **list = B** is assigned when C3 or C10 reaches severity 2. It is orthogonal to the verdict and
  never removes an item. Repairs to List B items are recorded as non-binding.
- C3/C10 at severity 1 is recorded as **b_watch** — a second tier for the lead, not a verdict.

## 4. What the PROMPT does wrong (not the items)

The prompt is well built — no system prompt, no worked example, explicit position-randomisation
notice, never-default parser, `display_position` kept out of scoring. Five findings, in order of
seriousness.

**4.1 The parser will drop responses non-randomly across checkpoints.** `CHOICE:\s*\[?\s*([A-D])\b`
accepts `CHOICE: A`, `CHOICE: [A]`, `CHOICE: A.` — but fails on `CHOICE: **B**` (markdown bold),
on `` CHOICE: `B` ``, and on lowercase `CHOICE: a` or `choice: A` (no `re.I`). Those are not
exotic outputs; markdown bolding of a final answer is a house habit that varies BY MODEL FAMILY AND
BY VINTAGE. Differential missingness across checkpoints biases exactly the cross-checkpoint
comparison Stage 1 exists to make, and `parse_ok=false` rows are dropped after the n=48 floor is
already committed. Fix: make the marker case-insensitive and let the letter be wrapped in any of
`[ ] * _ \` " '` before the word boundary. Cheap, and it should be decided
before freezing, not after seeing the parse rate.

**4.2 The render rule loses option boundaries on the six multi-line items.** `render_rule` renders
each option as `'<LABEL>.\n<display>'` with no fence and no indent. SCHEMA.md S4 explicitly
requires the opposite ("a fenced block or a consistent indent under each label"). Six items have
multi-line displays (`return_001`, `return_003`, `error_002`, `error_003`, `sentinel_001`,
`fileorg_001`), and `return_001`'s dataclass option contains a blank line, so option D can run
visually into the following instruction. The template also appends the instruction directly after
`{options}` with a leading space and no blank line. Fix: indent every display line by two spaces
under its label, or fence it, and put a blank line before the instruction.

**4.3 The coordination frame is in direct conflict with SCHEMA.md's stated prompt constraint.**
SCHEMA.md S4 says: "Never state or imply that there is a correct answer, a preferred style guide,
or a majority convention. **Never mention coordination, matching, or another model.**" The prompt
mentions all three. Parity with the frozen visual prompt is a real and probably decisive reason to
keep it — but the conflict should be resolved on the record rather than left standing between two
documents, because T2 built and defended 36 items against a constraint the prompt does not honour.

**4.4 The frame changes the measured quantity, and does so asymmetrically between domains.** Told
to match a copy of itself, the rational move is to pick the most publicly salient option — so the
prompt measures coordination salience, not the model's own coding policy, and it systematically
amplifies collapse on exactly the items where a normative or idiomatic attractor exists. That is
tolerable and it is what the visual domain does. The asymmetry is not: each code `spec` ends in a
first-person authorial question ("Which name do you give that function?"), so the rendered code
prompt asks two questions at once — *what do you write* and *what will your copy pick* — where the
visual prompt asks only the second. Models may resolve that tension differently, and differently
BY VINTAGE, which enters the data as policy dissimilarity that is really frame-interpretation
variance. Options: neutralise the spec voice to a descriptive statement, or accept it and
pre-register the interpretation. Either way it belongs in the write-up's construct-validity
section, and "policy" in MASTER_DESIGN S5 should be read as *self-coordination policy*.

**4.5 Free reasoning before the marker is a stronger amplifier in code than in vision.** "Give one
short sentence of reasoning" invites an explicit normative justification a model then follows
("the most standard choice is X, so X"). Verbal justification is far more available for code
conventions than for shape arrays, so the identical format is not an identical treatment across
domains. Worth one line in the domain-interaction analysis; not a defect.

Two smaller notes. The `#` comments carried inside `display` fields (S5.2) are rendered to the
model and in three items they name the convention — that is the `gloss` leaking into the prompt via
the item file, so it is a joint prompt/item defect. And `code_serial_002`'s options are labelled
JSON but `#` is not a JSON comment, a small coherence wrinkle in a wire-format item.

## 5. Battery-level findings

**5.1 Near-synonym option pairs split one convention's mass — the most consequential systematic
defect.** In eight items two of the four options are one convention at two levels of specificity or
spelling:

| item | the split pair | one convention |
|---|---|---|
| `code_varname_001` | `acc` / `accumulator` | role-word naming |
| `code_return_002` | plain dict / `Counter` | mapping return (Counter IS a dict) |
| `code_serial_001` | `…Z` / `…+00:00` | RFC 3339 UTC string |
| `code_serial_002` | base64 / base64url | base64 family |
| `code_tie_003` | casefold / casefold-upper-first | case-insensitive collation |
| `code_fileorg_002` | `utils.py` / `helpers.py` | generic catch-all module |
| `code_fileorg_003` | 3 of 4 options use a top-level `tests/` | top-level test directory |
| `code_outorder_001` | count+alpha / count+first-seen | count-first ordering |

The effect is directional, not noise. Splitting a convention across two options **lowers its
`modal_share`, raises `effective_support`, and lowers `cross_model_match`** — every one of those in
the direction of "this item did not collapse". `code_fileorg_003` is the extreme case: the
dominant Python convention gets three options and its rival gets one. Two remedies, both cheap:
replace one member of each pair with a structurally distinct option, or pre-register a
`convention_group` column and report the grouped distribution beside the four-way one. The second
is preferable because it is auditable and loses no data. **Until one is applied, no non-collapse
result from this battery should be read as evidence that code conventions are underdetermined.**

**5.2 Rendered comments are asymmetric within items.** Six items annotate some options and not
others; in `code_return_002` and `code_serial_002` three of four carry a comment that names the
convention. Where the comment is decorative it is a cue (C7 severity 2). Where it is load-bearing —
`# minor units` is what makes `1234` mean $12.34 — removing it would create a knowledge test
instead, so those items need the annotation equalised across all four options rather than deleted.

**5.3 Option length is confounded with content, and the coordination frame makes it worse.** T2
identified this (design_notes S5) and its mitigation is right: record `len(display)` and line count
per option as covariates and test whether choice share tracks length before reading anything as
convention. I did not fire C7 on length alone where the spread is intrinsic to the mechanism —
lexeme items cannot hold length constant — but I did where an option was structurally rather than
lexically the odd one out (`code_sentinel_001`). Add `display_char_len` and `display_line_count` to
the per-option manifest.

**5.4 Mechanism coverage does not survive the rejections.** Of 12 mechanisms, four drop to a single
surviving item: `argument_ordering` (1), `output_ordering` (1), `return_representation` (1),
`serialization` (1). At one item per mechanism, `mechanism` and `family` are confounded and the
leave-one-mechanism-out sensitivity named in DATA_DICTIONARY S"Convergence analyses" cannot be run.
**This is the strongest argument for repairing rather than deleting**: nine of the eleven rejections
need a one-line or one-option edit, and repairing them restores 3 items per mechanism.

**5.5 Mechanism honesty (B1).** Two labels are doing work they should not. `code_argorder_003` is a
choice of parameterization, not an ordering of a fixed parameter set (T2 says so and tagged the
family for the lead). `code_fileorg_002` is half a naming item. `code_error_003` is absence
handling filed under `error_representation` (T2 says so). None of these is a defect in the item;
all three affect how mechanism-level results may be aggregated.

**5.6 What is genuinely good, and should be preserved through any repair.** Nothing here is
selection-conditioned — no model has seen any of this text, so MASTER_DESIGN threat 1 does not
apply to the code domain, and that is a real advantage over the visual battery. The
presentation/decode design is correct and the lead's 3456-assertion round trip confirms it.
`code_tie_002` is a model for stem construction: it names all four tiebreak bases symmetrically, so
every option's key is mentioned and none is differentially cued — precisely what
`code_argorder_001` fails to do. `code_tie_001` defines each rounding rule with a worked example so
no recall is needed, correctly avoiding C9 in an item that could easily have become a knowledge
test.

## 6. Core pilot subset

The 12 `tags:["core"]` items are one per mechanism. **The subset does not survive: 5 ACCEPT,
4 FLAG, 3 REJECT.**

- REJECT: `code_argorder_001` (C6=2), `code_error_002` (C1=2), `code_outorder_002` (C6=2)
- FLAG: `code_fileorg_001`, `code_iface_001`, `code_sentinel_001`, `code_serial_001`
- ACCEPT: `code_fnname_001`, `code_jsonname_002`, `code_return_001`, `code_tie_001`, `code_varname_002`

All three rejected core items are rated `low` collapse risk by T2, and all three carry defects
invisible to a collapse-risk estimate: a stem that enumerates the parameters in one option's order,
an option that fails the spec's own information requirement, and a stem that asserts something
false. This is what an independent pass buys.

**Recommendation: repair, do not recompose.** All three repairs are one-line or one-option and are
specified per item below; `code_outorder_002` and `code_error_002` in particular are trivial. Repair
preserves one-item-per-mechanism coverage, which recomposition cannot fully do.

**Fallback if the lead will not reopen items before the pilot:** swap within mechanism —
`code_argorder_001` → `code_argorder_003` (ACCEPT), `code_error_002` → `code_error_001` (FLAG,
b_watch), `code_outorder_002` → `code_outorder_003` (FLAG). Coverage of all 12 mechanisms is
retained, but the pilot then runs with two FLAG items it need not have.

## 7. Per-item decisions

Severities: 0 absent, 1 arguable, 2 fires with citable evidence. List-A criteria decide the verdict;
C3/C10 decide the list label only. Full fields in `item_decisions.csv`.

### Summary table

| item | mechanism | verdict | list | criteria | b_watch | T2 risk | core |
|---|---|---|---|---|---|---|---|
| `code_argorder_001` | argument_ordering | **REJECT** | A | C6=2 | no | low | yes |
| `code_argorder_002` | argument_ordering | **REJECT** | A | C3=1;C6=2;C10=1 | yes | medium |  |
| `code_argorder_003` | argument_ordering | **ACCEPT** | none | C3=1 | yes | medium |  |
| `code_error_001` | error_representation | **FLAG** | none | C3=1;C4=1;C10=1 | yes | high |  |
| `code_error_002` | error_representation | **REJECT** | A | C1=2 | no | low | yes |
| `code_error_003` | error_representation | **FLAG** | B | C3=2;C6=1;C10=2 | no | medium |  |
| `code_fileorg_001` | file_organization | **FLAG** | none | C6=1 | no | low | yes |
| `code_fileorg_002` | file_organization | **FLAG** | none | C8=1 | no | medium |  |
| `code_fileorg_003` | file_organization | **FLAG** | none | C3=1;C8=1 | yes | low |  |
| `code_fnname_001` | function_naming | **ACCEPT** | none | none | no | low | yes |
| `code_fnname_002` | function_naming | **ACCEPT** | none | C3=1;C10=1 | yes | low |  |
| `code_fnname_003` | function_naming | **ACCEPT** | none | none | no | low |  |
| `code_iface_001` | interface_layout | **FLAG** | none | C7=1 | no | medium | yes |
| `code_iface_002` | interface_layout | **FLAG** | none | C6=1 | no | medium |  |
| `code_iface_003` | interface_layout | **ACCEPT** | none | none | no | low |  |
| `code_jsonname_001` | json_field_naming | **ACCEPT** | none | C3=1 | yes | medium |  |
| `code_jsonname_002` | json_field_naming | **ACCEPT** | none | none | no | low | yes |
| `code_jsonname_003` | json_field_naming | **FLAG** | none | C6=1 | no | low |  |
| `code_outorder_001` | output_ordering | **REJECT** | A | C6=1;C7=1;C8=1 | no | medium |  |
| `code_outorder_002` | output_ordering | **REJECT** | A | C6=2 | no | low | yes |
| `code_outorder_003` | output_ordering | **FLAG** | none | C6=1;C10=1 | yes | medium |  |
| `code_return_001` | return_representation | **ACCEPT** | none | none | no | low | yes |
| `code_return_002` | return_representation | **REJECT** | A | C7=2;C8=1;C10=1 | yes | low |  |
| `code_return_003` | return_representation | **REJECT** | A | C4=2;C6=1 | no | medium |  |
| `code_sentinel_001` | sentinel_values | **FLAG** | none | C7=1 | no | low | yes |
| `code_sentinel_002` | sentinel_values | **FLAG** | none | C5=1;C10=1 | yes | low |  |
| `code_sentinel_003` | sentinel_values | **FLAG** | none | C4=1;C10=1 | yes | low |  |
| `code_serial_001` | serialization | **FLAG** | none | C8=1 | no | low | yes |
| `code_serial_002` | serialization | **REJECT** | A | C7=2;C8=1;C9=1 | no | low |  |
| `code_serial_003` | serialization | **REJECT** | A | C5=2;C7=1 | no | medium |  |
| `code_tie_001` | tie_breaking | **ACCEPT** | none | C10=1 | yes | low | yes |
| `code_tie_002` | tie_breaking | **ACCEPT** | none | none | no | low |  |
| `code_tie_003` | tie_breaking | **REJECT** | A | C1=2;C8=2 | no | medium |  |
| `code_varname_001` | variable_naming | **FLAG** | none | C3=1;C8=1;C10=1 | yes | medium |  |
| `code_varname_002` | variable_naming | **ACCEPT** | none | none | no | low | yes |
| `code_varname_003` | variable_naming | **REJECT** | A | C6=2 | no | low |  |

## 8. LIST A — INVALID, removed (11)

### `code_argorder_001` — argument_ordering / param_order · **core**
Severities: C6=2  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** C6 MASKED-STEM HIT (prediction: "(source, destination, amount), matching stem order"). The distinguishing dimension IS positional order, and the stem enumerates the parameters in one specific order: "the source account, the destination account, and the amount" - which is option src_dst_amt verbatim. Lexical-overlap metrics cannot see this (ov=[3,3,3,3]); only the masked-stem pass caught it.

**Repair.** Delete the enumeration; let the signatures supply the parameter names: "A Python ledger module needs a function that moves money from one account to another. Which signature do you write?" Mechanism/family unchanged. Alternative: randomise stem enumeration order per presentation and record it as a covariate (prompt_hash already varies per presentation_id).

### `code_argorder_002` — argument_ordering / param_order
Severities: C3=1;C6=2;C10=1  ·  b_watch: yes  ·  T2 self-rated: medium

**Evidence.** Same defect as argorder_001 and worse: the stem order "the value, the lower bound, and the upper bound" cues clamp(value, low, high), which is ALSO the numpy.clip attractor - the leak points at the already-dominant option, so the two effects are confounded and inseparable. T2 worried about the wrong thing here (plausibility of v_hi_lo, not the stem).

**Repair.** Delete the enumeration as in argorder_001. Separately, T2 is right that v_hi_lo is the weakest option; after the stem fix, consider replacing it, which changes family to a grouped-interval form and makes it a new item.

### `code_error_002` — error_representation / wire_error_shape · **core**
Severities: C1=2  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** C1: the spec REQUIRES both "a machine-readable reason and a human-readable sentence". Option flat_error is {"error": "email is not a valid address"} - it carries NO machine-readable code and so fails the item own stated contract. T2 co_validity_rationale concedes this in a parenthetical ("or, for the flat form, the sentence the spec asks for"), which is an admission that one option under-delivers. A reviewer would open a defect: the client cannot branch on the error. Core-tagged and rated low risk by T2.

**Repair.** Replace flat_error with the OAuth2 / RFC 6749 envelope, which is a real fourth convention carrying both fields: {"error": "invalid_email", "error_description": "email is not a valid address"}. Restores co-validity, keeps four distinct real envelopes, mechanism/family unchanged. Re-check: does not trip C7 (comparable length, no comment) or C8 (distinct from the nested and sibling forms).

### `code_outorder_001` — output_ordering / sort_policy
Severities: C6=1;C7=1;C8=1  ·  b_watch: no  ·  T2 self-rated: medium

**Evidence.** Cumulative rule: three List-A criteria at severity 1, none individually decisive. C6: "how many times it occurred" primes a frequency-ranked reading (T2 own concern, which I confirm). C8: count_alpha and count_firstseen are ONE convention (count-first) split across two options while alpha and firstseen each stand alone - a 2-vs-1-vs-1 split that structurally depresses the count-first share. C7: options 1-2 carry a primary key plus a tiebreak clause; options 3-4 carry only a primary, so the set is not parallel in form (14 vs 93 chars).

**Repair.** Adopt T2 own C6 repair (describe the output as a word list with an occurrence column) AND collapse the count pair: keep one count-first option, add a fourth single-key order. If no fourth natural order exists, pre-register convention_group={count_alpha,count_firstseen} and report grouped. Rejected rather than flagged because three independent weaknesses compound; any two of the three repairs makes it a FLAG.

### `code_outorder_002` — output_ordering / sort_policy · **core**
Severities: C6=2  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** C6 MASKED-STEM HIT (prediction: "alphabetical is primed"). The stem says the fields are "listed here alphabetically" - naming the exact ordering principle that is option alpha, immediately before asking for a column order. Worse, the claim is FALSE: the stem lists email, id, created_at, name, whose alphabetisation is created_at, email, id, name. Verified computationally. So the item both leaks one option and asserts something untrue, and a model that notices the error has no defined behaviour. Core-tagged, rated low risk by T2.

**Repair.** Delete "listed here alphabetically" and reorder the field list so it matches none of the four options, e.g. "Each record has exactly the fields email, name, created_at, and id; the source objects carry no intrinsic field order." Verified: email,name,created_at,id is not any of the four option orders. One-line edit, no label impact.

### `code_return_002` — return_representation / container_shape
Severities: C7=2;C8=1;C10=1  ·  b_watch: yes  ·  T2 self-rated: low

**Evidence.** C7: three of four options carry a rendered comment that NAMES the convention ("# plain dict", "# collections.Counter", "# list of 2-tuples") and the fourth carries none. This puts the gloss into the display field, which SCHEMA.md S2.1 forbids for exactly this reason ("a gloss would name the convention and bias the choice"). C8: Counter IS a dict subclass, so two options are one convention at two levels of specificity. C10: a mapping is normatively favoured over a list of pairs for a lookup-shaped result.

**Repair.** Remove all four comments (the code is self-describing) AND replace counter with a genuinely distinct container, e.g. return a list of Counter-free (word,n) pairs is already present - use collections.OrderedDict or a frozen mapping instead. Re-check: removing comments does not create C9 here because dict/Counter/pairs/records are visually distinguishable without a gloss.

### `code_return_003` — return_representation / mutation_policy
Severities: C4=2;C6=1  ·  b_watch: no  ·  T2 self-rated: medium

**Evidence.** C4 is this rubric own worked example (list.sort vs sorted), written blind before the battery was seen. records.sort() mutates the caller list; sorted() does not; the generator form does nothing until iterated and cannot be re-iterated. A caller holding a second reference observes different program states. These are four contracts, not four spellings of one. mutation_policy cannot be a pure convention mechanism. C6=1: T2 is right that "arranges them" tilts toward in-place, but that is the lesser problem.

**Repair.** Fix mutation by fiat in the spec ("the caller list must not be modified") and vary only the return convention among options that share one contract. That reduces family mutation_policy to a return_convention item; mechanism return_representation is unchanged, but the lead should treat it as near-new. Note the residual: list vs iterator remains a laziness difference and cannot both be kept.

### `code_serial_002` — serialization / wire_encoding
Severities: C7=2;C8=1;C9=1  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** C7=2: three of four options carry rendered comments naming the convention ("# standard base64", "# base64url, unpadded", "# lowercase hex"); the fourth has none. Same gloss-in-display defect as return_002, and here the comments are doing real work - without them, telling base64 from base64url requires recalling that base64url substitutes -/_ for +/, which is C9 (knowledge, not convention). So the item is either cued (with comments) or a recall test (without them). C8=1: base64/base64url are one convention with an alphabet variant.

**Repair.** Drop base64url entirely and drop all comments; replace with a distinct, self-evident fourth encoding such as prefixed hex "sha256:deadbeef..." (the OCI/Docker digest convention). This clears C7, C8 and C9 together. Mechanism/family unchanged.

### `code_serial_003` — serialization / wire_encoding
Severities: C5=2;C7=1  ·  b_watch: no  ·  T2 self-rated: medium

**Evidence.** C5=2, mechanism and scale both named as the rubric requires. Mechanism: IEEE-754 binary64 cannot exactly represent 12.34 (it parses to 12.3399999999999998578...), and mainstream JSON parsers default to binary64, so cent-level error accumulates across a ledger. Scale: the spec says PAYMENTS SERVICE - precisely the context where every major money API (Stripe minor units, PayPal decimal string, Google units/nanos) deliberately avoids the float, and where a reviewer would open a defect. Three options are deliberate money encodings and the fourth is the known anti-pattern; that is instrumental dominance, not a convention. T2 saw the objection and under-weighted it as applying only "at other magnitudes".

**Repair.** Replace number with a fourth float-free money convention, e.g. {"amount": {"value": 1234, "scale": 2}} (value+scale, used in ISO 20022-style ledgers). Keeps four real encodings, removes the dominated option, mechanism/family unchanged. Also drop the "# minor units" comment (C7) and make the minor-units option self-evident by keying it "amount_minor".

### `code_tie_003` — tie_breaking / collation
Severities: C1=2;C8=2  ·  b_watch: no  ·  T2 self-rated: medium

**Evidence.** Verified computationally. For the spec own example input (apple, Banana, apricot, Apple), the casefold rule (case-insensitive, ties left in input order) yields apple, Apple, apricot, Banana - but the option displays "(Apple, apple, apricot, Banana)". The worked example CONTRADICTS the rule it illustrates (C1: an option rendered text is incorrect). Worse, that wrong example is byte-identical to casefold_upper example, so AS RENDERED the two options demonstrate identical behaviour and a respondent reading the examples cannot distinguish them (C8=2). T2 flagged the pair as fine-grained but did not catch the error.

**Repair.** Fix the casefold example to "(apple, Apple, apricot, Banana)". One-token edit and the C1 defect clears. C8 then falls to severity 1 (the pair is still fine-grained but genuinely distinct), making the item a FLAG; also consider annotating the locale option with a worked example so all four are parallel in form.

### `code_varname_003` — variable_naming / constant_naming
Severities: C6=2  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** C6 MASKED-STEM HIT (prediction written before options seen: "an option containing DEFAULT and possibly SECONDS"). The item varies exactly two optional annotations (role prefix, unit suffix) and the stem asserts BOTH as salient facts: "the number of seconds to wait" and "used when the caller does not supply one". Stating an optional annotation makes including it conversationally responsive. Cues DEFAULT_TIMEOUT_SECONDS.

**Repair.** Split into two one-axis items, each stating both facts identically so the mention cannot discriminate: item A varies DEFAULT_ prefix with _SECONDS held on in all four; item B varies _SECONDS with DEFAULT_ held on. Mechanism variable_naming and family constant_naming unchanged; battery item count +1. A 2x2 whose two axes must both be asserted in the stem is intrinsically leaky and cannot be repaired in place.


## 9. FLAG — not usable as-is, lead adjudication (14)

### `code_error_001` — error_representation / failure_shape
Severities: C3=1;C4=1;C10=1  ·  b_watch: yes  ·  T2 self-rated: high

**Evidence.** SURVIVES, contra T2 own top worry. C3 two-source test FAILS to fire at 2: the Python stdlib itself ships both conventions (int() raises; re.match/str.find return a failure value), so raising is dominant but not exclusive. C10 does not fire at 2 either: "in Python you raise" is a GROUP FACT, not a general quality argument, and a team mandating Result objects in a hot batch loop is different, not wrong. C4=1 only because an uncaught exception propagates where an ignored None silently skips - an observable difference in the do-nothing caller case.

**Repair.** No repair needed for validity. If the lead wants the collapse risk reduced, T2 language-neutral-pseudocode restatement would work but would break parity with the rest of the battery, which is Python-voiced. Recommend keeping as-is and labelling.

### `code_error_003` — error_representation / absence_handling · **LIST B (retained, labelled)**
Severities: C3=2;C6=1;C10=2  ·  b_watch: no  ·  T2 self-rated: medium

**Evidence.** LIST B - the battery only confirmed universal item. C3=2: for supplying a default for ONE missing key, config.get(k, default) is what every reputable Python source does; try/except KeyError for a single default is genuinely rare and defaults-merging is a pattern for several settings, which the spec explicitly makes it not ("One setting is optional"). C10=2: the counterfactual community that mandates try/except for a single-key default is slightly WRONG, not merely different - verbose with no benefit. T2 equivalence claim is otherwise correct: all four agree on every input including an explicitly-null value. C6=1: the merge option local variable is named settings, echoing the stem "reads settings from a dict".

**Repair.** Non-binding per D-009. C6 repair is cheap and worth doing even for a retained item: rename the merge local from settings to conf, or drop "settings" from the stem. Does not affect the List B label.

### `code_fileorg_001` — file_organization / layout_tree · **core**
Severities: C6=1  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** C6=1: the stem says "one MODULE of code plus its tests", which describes option flat_root (a single tool.py); the other three create packages (tool/__init__.py). The stem vocabulary matches one option class.

**Repair.** Replace "one module of code" with "a single small body of code" or "one unit of code". One-line edit, no label impact.

### `code_fileorg_002` — file_organization / helper_placement
Severities: C8=1  ·  b_watch: no  ·  T2 self-rated: medium

**Evidence.** C8=1, confirming T2 own Tier-1 concern: utils.py and helpers.py are one convention (generic catch-all module) differing only in lexeme, so the item is half a naming item and partly duplicates the function_naming mechanism. Battery consequence: file_organization is not cleanly measuring placement.

**Repair.** Replace helpers.py with a structurally distinct placement, e.g. the helper defined in report/__init__.py, or a private report/_dates.py. Restores four distinct placements and removes the lexeme axis. Mechanism/family unchanged.

### `code_fileorg_003` — file_organization / test_placement
Severities: C3=1;C8=1  ·  b_watch: yes  ·  T2 self-rated: low

**Evidence.** C8=1: three of four options put tests in a top-level tests/ dir (test_ prefix, _test suffix, unit/ tier) and only one is adjacent, so the dominant convention is split three ways while its rival gets one option - this will make tests/ look far weaker than it is. The item also varies two axes (placement, naming) without crossing them. C3=1: tests/test_*.py is dominant in Python though *_test.py is genuinely used.

**Repair.** Cross the axes into a clean 2x2: {tests/, pkg/} x {test_ prefix, _test suffix}. Unlike varname_003, this 2x2 is safe because neither axis has to be asserted in the stem. Mechanism/family unchanged.

### `code_iface_001` — interface_layout / cli_surface · **core**
Severities: C7=1  ·  b_watch: no  ·  T2 self-rated: medium

**Evidence.** C7=1: only the filter option carries a rendered comment ("# result goes to stdout"), marking it out. The comment is load-bearing (the option is opaque without it), so severity 1 not 2. On T2 own question: the wording "produces one output" DOES hold - stdout is one output and the spec never says the tool must open the destination - so C4 does not fire.

**Repair.** Give all four options a parallel one-clause annotation, or move the stdout fact into the option text itself ("conv INPUT > OUTPUT"). Mechanism/family unchanged.

### `code_iface_002` — interface_layout / config_surface
Severities: C6=1  ·  b_watch: no  ·  T2 self-rated: medium

**Evidence.** C6=1, confirming T2 own concern and slightly strengthening it: "they set it once per deployment" is close to a definition of a deployment-level surface, which argues against a per-invocation --retries flag and against a library constructor argument for CLI users. Two of the four options are partly excluded by the spec own stipulation, so this shades from a cue into an equivalence (A1) concern.

**Repair.** Adopt T2 repair: cut the clause. Suggested stem ending: "Operators need to be able to set how many times a failed network call is retried. Where do you put that knob?" One-line edit, no label impact.

### `code_jsonname_003` — json_field_naming / identifier_lexeme
Severities: C6=1  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** C6 token-overlap: the stem contains the word "total" verbatim ("match the query in total"), which is exactly option 1 and a substring of option 3. Partly offset because "how many" cues count/num_results, so the cues do not point one way; hence severity 1 not 2.

**Repair.** Rewrite the stem clause as "an integer giving the number of records matching the query across all pages" - removes the verbatim "total" while preserving meaning. One-line edit, no label impact.

### `code_outorder_003` — output_ordering / sort_policy
Severities: C6=1;C10=1  ·  b_watch: yes  ·  T2 self-rated: medium

**Evidence.** C6=1: the stem raises the very distinction exactly one option acts on ("The directory holds both files and subdirectories" -> dirs_first), the same Gricean pattern as varname_003 in weaker form. C10=1: os_order is dominated by a general quality argument (reproducibility across machines) rather than by a group fact - T2 anticipated this and is right to have flagged it.

**Repair.** C6: deleting the subdirectories clause removes the cue but leaves dirs_first unmotivated - a genuine trade-off; recommend keeping the clause and recording the cue rather than a blind edit. C10: os_order is retainable as a labelled non-convention, or replace with "by file size, largest first".

### `code_sentinel_001` — sentinel_values / absence_marker · **core**
Severities: C7=1  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** C7: option ellipsis renders as one 17-char line (def f(x=...)) against 43/71/76-char two-part blocks, because a builtin needs no definition line. Structurally, not merely lexically, the odd one out - and under a coordination frame a visually distinctive option is a salience magnet independent of its convention.

**Repair.** Give the Ellipsis option the same two-part shape as the others by naming it, which is itself a real idiom: "_MISSING = ...\n\ndef f(x=_MISSING): ..." Equalises structure without changing the convention. Mechanism/family unchanged.

### `code_sentinel_002` — sentinel_values / absence_marker
Severities: C5=1;C10=1  ·  b_watch: yes  ·  T2 self-rated: low

**Evidence.** C5/C10=1: the spec stipulates unknown consumers ("consumed by other teams tools"), and the empty field is the least-assumption encoding for an unknown consumer - a general robustness argument, which is a C10-shaped reason rather than a house style. Offset because NA is the R-world standard and pandas reads all four as missing, so the advantage is real but not decisive; hence 1, not 2.

**Repair.** Optional: name the consumer to neutralise the robustness argument (e.g. "consumed by a downstream pandas job"), which converts the reason back into a convention. Changes nothing structural.

### `code_sentinel_003` — sentinel_values / unbounded_marker
Severities: C4=1;C10=1  ·  b_watch: yes  ·  T2 self-rated: low

**Evidence.** C4/C10=1: limit=0 is a legitimate finite cap in many APIs (return zero rows), so using it for unbounded destroys an expressible behaviour that the other three preserve. Note the internal inconsistency with sentinel_001, which teaches that a meaningful value cannot double as a sentinel; here 0 arguably IS meaningful. math.inf is also type-inconsistent with an int limit.

**Repair.** One-clause spec edit closes it: add "callers never ask for zero rows" so 0 carries no other meaning. Preserves all four options and the mechanism. Alternative: replace zero with limit="all", a real string sentinel.

### `code_serial_001` — serialization / wire_encoding · **core**
Severities: C8=1  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** C8=1: iso_z and iso_offset are two spellings of ONE convention (RFC 3339 UTC); they split that convention mass against the two epoch forms, which are themselves a near-pair (s vs ms). As rendered the item is closer to a 2x2 of {ISO, epoch} x {two spellings} than to four conventions.

**Repair.** Pre-register convention_group = {iso_z,iso_offset} and {epoch_s,epoch_ms} and report the grouped 2-way distribution alongside the 4-way; or replace iso_offset with a genuinely different encoding (e.g. "2026-09-09 14:03:27Z" space-separated, or an RFC 1123 date string). Grouping is the cheaper fix and loses nothing.

### `code_varname_001` — variable_naming / identifier_lexeme
Severities: C3=1;C8=1;C10=1  ·  b_watch: yes  ·  T2 self-rated: medium

**Evidence.** C8: acc/accumulator are the SAME convention (role word) at two abbreviation levels; scoring is unambiguous but the two options split one convention mass, deflating its share and inflating effective_support. Design is not the clean 2x2 claimed: total/running_total differ on a temporal-qualifier axis, not abbreviation.

**Repair.** Either replace accumulator with a different convention (e.g. subtotal), or pre-register a convention_group column grouping {acc,accumulator} and report the grouped 3-way distribution alongside the 4-way. Mechanism/family unchanged.


## 10. ACCEPT (11)

### `code_argorder_003` — argument_ordering / parameterization
Severities: C3=1  ·  b_watch: yes  ·  T2 self-rated: medium

**Evidence.** Spec explicitly stipulates co-validity ("can be described by any of the parameterizations below") without enumerating parameters in order - this is the correct construction that argorder_001/002 lack. All four are the primary rect interface of a major toolkit (CSS/SDL, Win32/PIL, detection stacks, Cocoa). C4 does NOT fire under the adjudication rule in S2: differing arity/API text with an identical contract is convention, not functional difference.

### `code_fnname_001` — function_naming / identifier_lexeme · **core**
Severities: none  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** Two-source test passes: dedupe/unique/distinct/remove_duplicates each attested (Go+modern Py; numpy/pandas .unique; SQL/LINQ; spelled verb phrase). Spec fixes behaviour so name is free.

### `code_fnname_002` — function_naming / predicate_prefix
Severities: C3=1;C10=1  ·  b_watch: yes  ·  T2 self-rated: low

**Evidence.** is_ prefix likely dominant for a bool-returning METHOD; has_/bare-adjective attested (hasattr; Django is_authenticated; requests .ok) so split is real but thin. check_ conventionally implies validate-and-raise, so its defence is weakest.

### `code_fnname_003` — function_naming / conversion_verb
Severities: none  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** Four-way attested split: to_dict (pandas), as_dict (configobj/ORMs), asdict (dataclasses/attrs), serialize (DRF/marshmallow return dicts). Spec fixes return type so all four denote one operation.

### `code_iface_003` — interface_layout / cli_surface
Severities: none  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** All four are directly supported by argparse and click and each is the surface of well-known tools. The banned-lexicon grep hits "should" in the stem, but it is deontic ("the tool should let a user...") and describes the requirement, not the options, so C6 does not fire.

### `code_jsonname_001` — json_field_naming / identifier_case
Severities: C3=1  ·  b_watch: yes  ·  T2 self-rated: medium

**Evidence.** Clean 2x2 (case x lexeme), neither axis asserted by the stem, no host language named. C3=1 only because models may impute a host language; T2 is right that such a collapse is itself informative.

### `code_jsonname_002` — json_field_naming / identifier_lexeme · **core**
Severities: none  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** items/results/data/records each the house choice of a major API (GitHub, DRF, JSON:API, various). Shape fixed by the spec so only lexeme varies.

### `code_return_001` — return_representation / container_shape · **core**
Severities: none  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** Same values, same guarantees, spec fixes the contract ("the caller reads both") and names none of iteration/attribute access/JSON-serializability/immutability. Access spelling differs; contract does not. Model item for the C4 adjudication rule.

### `code_tie_001` — tie_breaking / rounding_rule · **core**
Severities: C10=1  ·  b_watch: yes  ·  T2 self-rated: low

**Evidence.** Strong item. All four halfway rules are named, standardised and deterministic, each display defines its rule with a worked example so no recall is needed (C9 correctly avoided), and the spec names no accounting standard or jurisdiction. C10=1 only because half_even is the least biased rule and the bias argument is general rather than communal. NOTE for the lead: co_validity_rationale mis-states the decimal module (Python ROUND_HALF_UP rounds ties AWAY FROM ZERO, matching option half_away, not option half_up; there is no built-in ties-toward-positive-infinity mode). The rationale is metadata and never rendered, so the item itself is unaffected.

**Repair.** None required. Correct the co_validity_rationale text for the record.

### `code_tie_002` — tie_breaking / sort_tiebreak
Severities: none  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** Model item for stem construction: it names ALL FOUR tiebreak bases symmetrically ("a name, a numeric id, and the time their score was submitted, and they arrive in an input list"), so every option key is mentioned and none is differentially cued. This is the correct way to do what argorder_001 does wrongly. All four deterministic and attested.

### `code_varname_002` — variable_naming / identifier_lexeme · **core**
Severities: none  ·  b_watch: no  ·  T2 self-rated: low

**Evidence.** data/payload/body/parsed all standard for a decoded HTTP body; none shadowed. Mild semantic pull toward body/data from the unavoidable HTTP framing, not differential enough to fire C6.


---

## 11. What this audit could not check

Carried forward from `audit_procedure.md` S6, with the two additions this battery surfaced.

1. **Training-frequency attractors.** An option can be arbitrary for humans yet strongly
   attractored for language models by corpus frequency. Such an item passes all ten criteria and
   still produces convergence that is a shared-corpus artefact rather than a convention. No reading
   test detects it. This is the largest hole and it bears directly on the Stage 1 estimate.
2. **Common-cause confound.** Even a flawless item cannot separate convergence from shared training
   data. Study-level; untouchable from here.
3. **My knowledge cutoff.** Every C3 and C10 severity rests on my recall of what real communities
   do, not on a corpus measurement, and cannot be refreshed without network access. Each such call
   names its sources in the evidence field precisely so the lead can overrule it by naming a source
   I missed. An unsourced C3/C10 call was capped at severity 1 throughout.
4. **Single auditor, no reliability statistic.** I recommend a second independent pass on Pass 4
   (C3, C9, C10) only — 36 items, cheap, and it is where disagreement will concentrate. My
   confirmed List B count of 1 is the number I would least trust another auditor to reproduce.
5. **Elicitation artefacts** — answer-format effects, refusal behaviour, self-consistency pressure —
   live in the runner, not the items. S4.1 is the one instance I could catch by reading.
6. **Post-hoc undecidability.** Neither this audit nor the pilot can distinguish an item that
   collapses because it is right from one that collapses because it is conventional. The pilot gate
   can retire items; it cannot certify them.
7. **NEW — the C4 adjudication rule is mine, not the frozen rubric's.** S2 above. Nine additional
   items turn on it. If the lead reads C4 literally, `return_representation`,
   `error_representation`, `serialization` and much of `interface_layout` collapse as mechanisms and
   the code domain loses most of its API-shape content. I judged that reading wrong, but the
   judgement is contestable and it is the single point where this audit could be most consequentially
   mistaken.
8. **NEW — I cannot estimate how much the vote-splitting bias (S5.1) moves any statistic.** I can
   show the direction (toward apparent non-collapse) and name the eight items, but the magnitude
   depends on the true distributions, which cannot be known without collection. The lead should
   treat S5.1 as a threat to be removed by construction, not as one to be bounded by argument.
