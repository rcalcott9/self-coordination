# RED-TEAM AUDIT — expansion battery E18
2026-09-10. Offline. **No API calls.** 18 candidates authored → 3 rejected → 2 repaired in place
→ **17 enter the pilot**.

## 0. Independence of the rubric

Audited against `audits/code/rejection_rubric.md`, sha256 `230ca3d836768206…0010c67d`, **unchanged
since 2026-09-09 12:27**. The candidates were authored 2026-09-10 21:30. The rubric therefore
predates every item in this battery by construction, not by procedure — a stronger independence
claim than a fresh blind audit, which can only assert that the auditor did not look.

The rubric was also calibrated on real work: it rejected 11 of 36 Stage 1 items, including three the
author had rated low-risk.

**What this does not give us.** The rubric is independent of the items; the *application* of it here
is not — I wrote the items and I applied the criteria. That is a real weakness and the mitigation is
the pilot, which measures rather than judges.

---

## 1. Rejections — Class A (construction defect, repairable)

### `x_money` — **C5 instrumental dominance, severity 2**
The fourth option was a bare JSON number, `"amount": 19.99`. C5 fires when all options work but one
is decisively more robust in a way a reviewer would raise: float money is a textbook defect, so
convergence away from it would be **instrumental, not conventional** — the item would measure
engineering judgement, not a convention. The stem's hedge (exactly representable at this magnitude,
internal consumers) does not rescue it, because the option generalises beyond the stem.

**REPAIR applied.** Replaced with `"amount": "1999"` — integer minor units as a string, attested in
ledger APIs that avoid JavaScript's 53-bit integer limit. All four options are now exact and none
passes through binary floating point.

### `x_init_export` — **C4 functional non-equivalence, severity 2**
Original options were: empty `__init__.py` / re-export / `__all__` only / re-export + `__all__`.
Under the empty and `__all__`-only options `from pkg import Widget` **fails**; under the others it
succeeds. C4 names public API shape explicitly. T3's own adjudication narrowed C4 to differences in
information carried, guarantees or failure modes rather than "how a caller spells access to the same
contract" — but here the caller *cannot* spell it the same way, so the narrow reading still fires.

**REPAIR applied.** The stem now fixes the surface (`from pkg import Widget` must work) and the four
options are four ways of writing that same re-export: bare, with `__all__`, with the PEP 484
redundant alias, and via star import. All four now provide the identical import.

### `x_dict_order` — **A3 reason-symmetry not satisfied** (no criterion tripped)
The fourth option was "shortest keys first, then alphabetically". No rejection criterion fires, but
A3 requires that every option have a one-sentence non-embarrassing defence, and this one has none —
nor any attestation. The rubric is explicit that absence of a defect is not validity.

**REPAIR applied.** Replaced with "in the order the keys appear in the config file on disk", which is
what `git config --list` and INI writers do.

## 2. Rejection — Class B (domain fact). NOT repaired.

### `x_cli_flag_case` — **C3 idiomatic dominance, severity 2**
Long-option spelling: `--dry-run` / `--dry_run` / `--dryrun` / `--dry`. Hyphenation is the GNU
standard, is what argparse's own documentation shows throughout, and is close to universal in Python
CLIs. `--dryrun` is attested (aws-cli) but aws-cli is not a Python-idiom exemplar; underscored long
options are rare enough to read as deviant.

**Per the rubric a Class-B rejection is a reportable finding, not a defect to engineer around**, and
must not be silently patched by swapping in weirder options until the set spreads. It is removed from
the pilot and recorded here. I had flagged this item as a probable C3 case when authoring it and
included it deliberately so the decision would be on the record either way; the rubric resolves it
without needing the pilot's money.

**Class-A rate 3/18 = 17%** (against 31% on the Stage 1 battery).
**Class-B rate 1/18 = 6%** (against 3% confirmed / 33% suspected on Stage 1).

---

## 3. Verdicts on the 17 that enter the pilot

| item | mechanism | verdict | criteria at severity 1 |
|---|---|---|---|
| `x_acronym_case` | identifier_case | **ACCEPT** | — |
| `x_listkey` | json_field_naming | **ACCEPT** | — |
| `x_span` | parameterization | **ACCEPT** | — |
| `x_migration_name` | migration_naming | **ACCEPT** | C9 (recognising Alembic revision ids) |
| `x_argorder_replace` | argument_ordering | FLAG | C3 — `str.replace`'s order has strong Python pull |
| `x_predicate` | function_naming | FLAG | C10 — `check_` reads as side-effecting to some |
| `x_test_naming` | test_naming | FLAG | C10 — the terse option is less informative |
| `x_logger_var` | variable_naming | FLAG | C3 (`logger` dominant), C7 (`_log` only underscored) |
| `x_enum_value` | enum_serialization | FLAG | C10 (strings debug better than ordinals), C7 |
| `x_dict_order` | output_ordering | FLAG | C10 — sorted output diffs better |
| `x_docstring` | docstring_style | FLAG | C7 — NumPy style is inherently far longer |
| `x_optional_type` | type_annotation | FLAG | C3, C9 — **retained deliberately, see §4** |
| `x_init_export` | package_layout | FLAG | C9 — the PEP 484 alias is niche knowledge |
| `x_bool_env` | env_encoding | FLAG | C3 — `true` dominant in twelve-factor tooling |
| `x_id_field` | identifier_choice | FLAG | C3 (`id` dominant), C7 (`user_id` names an entity the stem does not) |
| `x_money` | serialization | FLAG | post-repair; C9 on units/nanos |
| `x_constants_home` | file_organization | FLAG | C10 — module-top is simplest |

**4 ACCEPT, 13 FLAG, 0 unrejected criteria at severity 2.** No item carries three severity-1s, so
none reaches the cumulative rejection threshold.

A FLAG is not a defect — per the rubric it means the item goes to the pilot carrying a marker. That
is exactly what the pilot is for, and 13 of 17 carrying one is expected for a battery deliberately
built at the contested edge of the domain.

`x_docstring`'s C7 is **not repairable without distorting the styles themselves**: NumPy-style
sections really are longer than Google-style ones. Recorded rather than fixed.

---

## 4. One item is a declared control, not a candidate

`x_optional_type` (`Optional[str]` / `str | None` / `Union[str, None]` / `t.Optional[str]`) is the
only locus in the battery whose split is **recent** — PEP 604 landed in Python 3.10 (2021), inside
the training window of the newer panel checkpoints but at the edge of the older ones.

Every other item was selected for the opposite property: contestation predating 2024-04 and
persisting. So if the liveness screen shows a gradient across the vintage ladder anywhere, this is
the item that should show it, and the others should not.

It is therefore retained **as a positive control on the selection principle**, not as a candidate
expected to survive. If it collapses at the new end while the long-contested items stay live, the
principle is doing what it claims. If it survives and the others do not, the principle is wrong and
that is worth knowing before 12 items are frozen.

---

## 5. What the pilot must decide, and what it must not

Screening criteria, fixed before collection:

- **ceiling** — a cell whose modal share is at or near 1.00 across the boundary checkpoints
- **near-random** — a cell indistinguishable from uniform over the four options
- **order-sensitive** — choice tracking display position rather than option content
- **malformed** — parse failures, or responses that cannot be mapped to one canonical option

**Effect direction is not a screening criterion.** No item is kept or dropped because of which option
won, or because the two families agreed or disagreed. Screening on direction would select the final
battery on the dependent variable — the same defect that disqualified `FROZEN_22` from Stage 1 — and
would make the full run's cross-family estimate uninterpretable.

At n=12 the pilot is a **screen, not an estimator**. It cannot resolve a temporal effect and no
vintage claim may be made from it.
