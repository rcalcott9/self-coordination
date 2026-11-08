# DESIGN NOTES — code-convention candidate battery

T2 (code-designer), 2026-09-09. Candidate, not frozen. **API calls made: 0.**

Files in this directory:

| file | what it is |
|---|---|
| `code_items.json` | 36 candidate four-option items, machine readable |
| `SCHEMA.md` | schema and the presentation/canonical-identity mapping |
| `design_notes.md` | this file |

`code_items.json` sha256 at time of writing:
`5c77c85e35c9299af0407792721e8e14e7fd4d8dfa62e1247b83df18cfdfb380`

Local verification already run (no model involved): 3456 encode/decode round-trip assertions pass
across all 36 items x 24 permutations x 4 labels; two full permutation cycles put every canonical
option at every display position exactly 12 times, so the n=48 floor gives exact positional balance
rather than expected balance.

---

## 1. What the items are trying to be

Every item is a forced choice among four ways of doing the *same* thing. The intended property is
not "hard" but **underdetermined**: a competent engineer, shown the specification alone, could
write any of the four and no reviewer could call the others wrong. The scientific value depends on
that; an item where one option is objectively right measures competence, not convention, and is
worthless here.

Three design rules I held to:

1. **One free axis per item.** Each item varies on exactly one dimension
   (`distinguishing_dimension`), so a divergence between models is interpretable. The two
   deliberate exceptions are clean 2x2s (`code_varname_003`, `code_jsonname_001`) where both axes
   are independently optional.
2. **The spec must not contain the answer.** Every requirement stated in `spec` is satisfied by
   all four options. I repeatedly cut clauses that leaked a preference — e.g. `code_error_001`'s
   spec deliberately says the caller decides what happens to bad rows, because saying "the job
   should skip bad rows and continue" would have selected the non-raising options.
3. **Scoring by label, never by text.** The model returns a letter; the letter decodes to a
   canonical id. No synonym adjudication, no fuzzy matching, no partial credit. This is why
   phrase-form options (rounding rules, sort orders) are acceptable even though the phrases
   themselves are prose.

---

## 2. Mechanisms covered

All twelve requested mechanisms are covered, three items each, 36 items total.

| mechanism | items | families used |
|---|---|---|
| function_naming | `code_fnname_001..003` | identifier_lexeme, predicate_prefix, conversion_verb |
| variable_naming | `code_varname_001..003` | identifier_lexeme x2, constant_naming |
| json_field_naming | `code_jsonname_001..003` | identifier_case, identifier_lexeme x2 |
| argument_ordering | `code_argorder_001..003` | param_order x2, parameterization |
| return_representation | `code_return_001..003` | container_shape x2, mutation_policy |
| error_representation | `code_error_001..003` | failure_shape, wire_error_shape, absence_handling |
| sentinel_values | `code_sentinel_001..003` | absence_marker x2, unbounded_marker |
| serialization | `code_serial_001..003` | wire_encoding x3 |
| output_ordering | `code_outorder_001..003` | sort_policy x3 |
| file_organization | `code_fileorg_001..003` | layout_tree, helper_placement, test_placement |
| tie_breaking | `code_tie_001..003` | rounding_rule, sort_tiebreak, collation |
| interface_layout | `code_iface_001..003` | cli_surface x2, config_surface |

Language spread (`language` field): 24 Python, 7 JSON, 3 CLI, 2 CSV. This matters for MASTER
DESIGN threat 6 (silent incompatibility) only insofar as a model may be more standardised in one
surface than another; `language` is stored so the lead can stratify.

Three items per mechanism is the minimum that lets Gate-1 tradeoff step (2) — "reduce redundant
items within a mechanism" — drop one per mechanism without losing a mechanism. `tags: ["core"]`
marks the single item per mechanism I would keep if the battery must shrink to 12.

---

## 3. Mechanisms and candidate items I dropped, and why

Dropped because fewer than four genuinely co-valid options exist, or because a tool has already
settled the question so the item would measure formatter defaults rather than model policy:

- **Whitespace, indentation, line length, trailing commas, quote style.** Settled by black /
  prettier / gofmt. Where a choice survives it is binary (`'` vs `"`), not four-way. An item here
  would measure "has the model internalised the dominant formatter", which is a correctness-like
  question, not a convention question.
- **Import ordering and grouping.** isort and PEP 8 fix the group order and alphabetise within
  groups. What remains free (one import per line vs combined) is binary.
- **Type-annotation spelling.** `List[int]` vs `list[int]` is decided by the target Python
  version; `Optional[X]` vs `X | None` is binary and also version-gated. Not underdetermined,
  just versioned.
- **Docstring format** (Google / NumPy / reStructuredText / Epytext). This *is* a genuine
  four-way convention and would have made a good item. I left it out only because it is outside
  the twelve requested mechanisms and I preferred exact balance across those twelve.
  **Recommendation: if the lead wants the battery larger, this is the first mechanism to add** —
  four named, documented, mutually exclusive, tool-supported styles, scorable by label.
- **HTTP status-code selection** (200 vs 201 vs 202 vs 204 for a create endpoint). Rejected:
  RFC 9110 constrains these enough that a reviewer can call some choices wrong, so it is partly a
  correctness item.
- **Concurrency primitive** (threads vs asyncio vs multiprocessing vs a queue). Rejected: the
  choice has real performance consequences, so it is not free.
- **Logging level for a given event.** Rejected: partly determined by operational semantics; a
  reviewer can argue an event "is" a warning.
- **Commit-message and branch-naming conventions.** Genuinely four-way and genuinely
  underdetermined, but not code, and out of the stated mechanism list.
- **Identifier abbreviation policy as its own mechanism** (`cfg` vs `config` vs `conf` vs
  `settings`). Cut as too close to a synonym set; the abbreviation axis survives only as one
  option pair inside `code_varname_001`, where I have flagged it.

---

## 4. Items I consider most at risk — my own list, ordered

I am flagging these before T3 writes anything. `self_rated_collapse_risk` in the JSON carries the
same judgement per item (1 high, 13 medium, 22 low).

**Tier 1 — I expect T3 to challenge these, and I would not defend them hard.**

1. **`code_error_001` (failure shape: raise / None / (value, error) / Result).** The one item I
   rated `high`. Raising is so dominant in Python specifically that models may treat it as the
   correct answer rather than a house style; the Go and Rust shapes read as imports from another
   language. I kept it because failure shape is among the most consequential real conventions and
   because a hard collapse here is a *reportable* result under MASTER_DESIGN S3, not a failure.
   Repair if wanted: restate the spec in language-neutral pseudocode so no language's default
   applies. Note also that if this item collapses it will drag `error_representation` as a
   mechanism, which matters for the leave-one-mechanism-out sensitivity T5 is specifying.
2. **`code_fileorg_002` (helper placement: utils.py / helpers.py / common/dates.py /
   dates.py).** Two of the four differ only in lexeme (`utils` vs `helpers`), so the item is half
   a file-organization question and half a naming question — it partly duplicates the
   `function_naming` mechanism. Weakest of the three file-organization items.
3. **`code_varname_001` (total / running_total / acc / accumulator).** `acc` and `accumulator`
   are the closest thing in the battery to a synonym pair; they differ only on the abbreviation
   axis. Scoring is unambiguous because the model picks a label, but a reviewer may fairly call
   the pair too fine-grained to count as distinct conventions.
4. **`code_argorder_002` (clamp orderings).** Three of the four orderings map to real conventions
   (numpy.clip; the `low <= value <= high` mnemonic; interval-first for partial application). The
   fourth, `(value, high, low)`, is defensible but noticeably rarer. If T3 rejects it the repair
   is to substitute a grouped-interval signature, which changes the family.

**Tier 2 — real doubts, but I would argue for keeping them.**

5. **`code_outorder_003` (directory listing order).** The `os.scandir` option is what a great many
   real scripts print, but it is not stable across filesystems, so a reviewer can argue it is not
   co-valid with three deterministic orders.
6. **`code_iface_001` (CLI surface, including the stdout-filter option).** The spec says the tool
   "produces one output" precisely to avoid requiring the tool to open a destination file. Whether
   that wording holds is exactly the kind of thing an outside auditor should test.
7. **`code_jsonname_001` (created_at / createdAt / created_time / createdTime).** In real work the
   surrounding API's existing keys settle the case convention; the spec deliberately supplies no
   siblings and names no host language. If models silently assume a host language they will
   collapse onto snake or camel. Informative either way, but more context-sensitive than the rest.
8. **`code_return_003` (in-place vs new list vs fluent vs generator).** Spec neutrality is
   delicate: "arranges them" can be read as licensing mutation. Repair: "produces the records in
   score order, highest first."
9. **`code_outorder_001` (word-count listing order).** "how many times it occurred" may prime a
   ranked reading and pull models toward the two count-first options. Repair: describe the output
   as a word list with an occurrence column.
10. **`code_serial_003` (money encoding).** The units/nanos object is real (gRPC
    `google.type.Money`) but far rarer than the other three, and the bare JSON number invites a
    float-precision objection that is a correctness argument at other magnitudes even if not at
    $12.34.
11. **`code_tie_003` (collation).** Two options differ only in what happens to strings that
    differ solely in case — possibly too fine — and the locale option may read as over-engineering
    for a tag list.
12. **`code_argorder_003` (rectangle parameterization).** Sits on the boundary between argument
    ordering and interface layout; it is a choice of parameterization, not a permutation of one
    fixed parameter set. Tagged `family: parameterization` so the lead can reclassify it without
    editing the item.
13. **`code_error_003` (missing-key idiom).** Classified under `error_representation` as absence
    handling, but it is arguably a control-flow-style mechanism of its own. Also the shortest
    option (`dict.get`) may attract choices for terseness rather than for convention — a general
    length-artefact worry, see S5.
14. **`code_iface_002` (where a deployment knob lives).** "set once per deployment" was chosen to
    keep all four surfaces live, but it leans slightly away from a per-invocation flag.

---

## 5. Cross-cutting artefacts the lead and T5 should know about

- **Option length is not balanced within every item.** Where options are code blocks
  (`code_return_001`, `code_return_003`, `code_sentinel_001`, `code_error_003`) the four differ in
  line count, and length is a known position-independent salience cue. This cannot be equalised
  without padding the shorter options into unnatural code. Mitigation: option length is a fixed
  per-option property, so it is a candidate covariate — I recommend T5 record
  `len(display)` and line count per option and check whether choice share tracks length across
  items before reading any result as convention.
- **Position sensitivity is measurable but the battery cannot remove it.** The 24-permutation
  cycle guarantees exact positional balance; it does not guarantee that a model is
  position-insensitive. That is measured, per MASTER_DESIGN threat 4, not assumed.
- **Alphabetical-label artefact.** Several items have an option that is alphabetically first among
  the option *contents* as well as sometimes first by label. Because labels are permuted, a
  content-alphabetical preference would show up as a canonical-option preference and be
  indistinguishable from a convention. Not fixable within a four-option forced choice; worth
  naming in the write-up.
- **The battery is exploratory by construction.** MASTER_DESIGN S3 says code conventions may be
  too standardised, and that this is an empirical possibility to report rather than engineer
  around. I have not tuned any item to manufacture spread. Items 1-4 above are the ones I expect
  to collapse; if far more than that collapse, the honest reading is that the code domain is
  standardised, not that the battery is broken.
- **Nothing here is selection-conditioned.** Unlike the visual batteries (MASTER_DESIGN threat 1),
  no item was chosen because of any observed model behaviour — no model has seen any of this text.
  The battery is therefore a genuinely broad frame for the code domain.

---

## 6. Suggested pilot subset

If the code-domain pilot gate (MASTER_DESIGN S6.2) needs a subset rather than all 36, I suggest
the twelve items tagged `core` — one per mechanism, all rated `low` collapse risk except
`code_error_001` and `code_iface_001`:

`code_fnname_001`, `code_varname_002`, `code_jsonname_002`, `code_argorder_001`,
`code_return_001`, `code_error_002`, `code_sentinel_001`, `code_serial_001`,
`code_outorder_002`, `code_fileorg_001`, `code_tie_001`, `code_iface_001`.

That subset preserves one item per mechanism, so the pilot can report per-mechanism liveness, and
it is the smallest set consistent with the gate's requirement of ">1 behaviourally live option on
a meaningful fraction of items". Whether to pilot the high-risk items *deliberately* — to learn
early whether failure shape collapses — is a lead decision; there is a case for including
`code_error_001` in the pilot precisely because it is the item most likely to fail.
