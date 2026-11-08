"""
Expansion battery E18 — 18 candidate four-option code-convention items.

Offline. No API calls. Authored 2026-09-10.

SELECTION PRINCIPLE (the one that follows from "balanced across the vintage ladder"):
every locus is a split that was already contested BEFORE the oldest panel checkpoint's
training window (2024-04) and is still contested now - typically one where a style guide
explicitly declines to choose, or where two equally prominent ecosystems disagree.

The reason is not aesthetic. An item whose split was resolved recently is live at the old
end of the ladder and dead at the new end, so it contributes nothing exactly where the
trend is estimated; an item contested throughout keeps a measurable policy at every
checkpoint. Stage 1's four surviving items (function_naming, interface_layout,
json_field_naming, tie_breaking) were all of the long-contested kind; its eight collapsed
items were loci where one convention had genuinely won.

Option order here is CANONICAL order only. Presentation order is set per trial from the
frozen 24-permutation table, never from this file.
"""
import hashlib, json, os

ITEMS = []


def item(iid, mech, fam, spec, opts, dim, coval, attest, liveness):
    assert len(opts) == 4, iid
    ITEMS.append(dict(
        item_id=iid, mechanism=mech, family=fam, language="python",
        display_kind="inline", spec=spec, n_options=4,
        options=[dict(canonical_index=i, canonical_id=f"{iid}::o{i+1}",
                      option_key=k, display=d, gloss=g)
                 for i, (k, d, g) in enumerate(opts)],
        distinguishing_dimension=dim, co_validity_rationale=coval,
        attestation=attest, liveness_rationale=liveness))


item("x_argorder_replace", "argument_ordering", "parameterization",
     "A Python utility module needs a free function that returns a copy of a string with "
     "every occurrence of one substring replaced by another. The three values it needs are "
     "the text, the substring to find, and the substring to substitute. In what order do "
     "you declare the parameters?",
     [("text_old_new", "def replace(text, old, new):", "subject first (Python str.replace)"),
      ("old_new_text", "def replace(old, new, text):", "operands first (sed, Perl s///)"),
      ("text_new_old", "def replace(text, new, old):", "subject first, replacement before target"),
      ("new_old_text", "def replace(new, old, text):", "replacement first (some Lisp dialects)")],
     "position of the subject relative to the two operands",
     "All four declare the same three values and compute the same result; only the "
     "positional contract differs. No option changes behaviour, guarantees or failure modes.",
     "Python str.replace puts the subject first via the method receiver; sed and Perl put "
     "the operands first; PHP's string functions are famously inconsistent between the two. "
     "The split is older than any model in the panel.",
     "Argument-order conventions are language-local and have never converged across "
     "ecosystems; there is no cross-language authority to converge on."),

item("x_acronym_case", "identifier_case", "identifier_lexeme",
     "You are naming a Python class that is a client for an HTTP-based API. The name will "
     "contain both acronyms. Which spelling do you use?",
     [("all_caps", "class HTTPAPIClient:", "both acronyms fully capitalised"),
      ("title_both", "class HttpApiClient:", "both acronyms title-cased"),
      ("caps_then_title", "class HTTPApiClient:", "leading acronym capitalised, second title-cased"),
      ("title_then_caps", "class HttpAPIClient:", "leading acronym title-cased, second capitalised")],
     "capitalisation of embedded acronyms in CapWords",
     "All four are valid Python identifiers naming the same class with the same public "
     "surface. Nothing about behaviour or discoverability differs.",
     "PEP 8 prescribes CapWords but does not say how acronyms inside them are cased. "
     "Google's Python style guide capitalises acronyms; Java's convention title-cases them; "
     "the standard library contains both (HTTPServer, HttpOnly cookies in third-party code).",
     "PEP 8's silence here is long-standing and unchanged, so no authority has ever "
     "resolved it in either direction."),

item("x_listkey", "json_field_naming", "collection_key",
     "A REST endpoint returns a page of records as JSON. The body is an object whose one "
     "content field carries the array of records. What do you name that field?",
     [("items", '{"items": [...]}', "generic container noun"),
      ("results", '{"results": [...]}', "query-outcome noun"),
      ("data", '{"data": [...]}', "payload noun (JSON:API)"),
      ("records", '{"records": [...]}', "domain noun")],
     "which noun names the collection",
     "All four are the same array under a different key; a consumer written against any "
     "one of them is the same client with one string changed.",
     "JSON:API mandates `data`; the Kubernetes API and GitHub search use `items`; the "
     "Django REST Framework default page uses `results`; Salesforce and many data APIs use "
     "`records`. Four independent, maintained, mutually incompatible conventions.",
     "Each convention is anchored in a large ecosystem with no incentive to move, so the "
     "split is stable rather than trending."),

item("x_predicate", "function_naming", "identifier_lexeme",
     "A Python cache class needs a method that reports whether an entry has passed its "
     "time-to-live. It returns a boolean and has no side effects. What do you name it?",
     [("is_expired", "def is_expired(self):", "is- prefix"),
      ("expired", "def expired(self):", "bare adjective"),
      ("has_expired", "def has_expired(self):", "has- prefix, present perfect"),
      ("check_expired", "def check_expired(self):", "check- verb prefix")],
     "predicate naming scheme",
     "All four are the same no-argument boolean method. None implies a different contract, "
     "mutation or failure mode.",
     "PEP 8 gives no predicate-naming rule. The standard library uses bare adjectives "
     "(`str.isdigit` is prefixed, `Thread.is_alive` is prefixed, `dict.keys` is bare); "
     "Ruby's convention is a trailing `?`; Java mandates `is`/`has`. All are attested in "
     "mainstream Python.",
     "Predicate naming has been contested in Python since before type checkers existed and "
     "no formatter or linter has ever normalised it."),

item("x_span", "parameterization", "range_convention",
     "A Python function operates on a contiguous span of a sequence. Every span the "
     "program handles can be described by any of the parameterizations below, and the "
     "function's behaviour is identical under all of them. Which signature do you write?",
     [("start_stop_half", "def window(seq, start, stop):   # stop exclusive",
       "half-open, exclusive end (Python slicing)"),
      ("start_end_incl", "def window(seq, start, end):     # end inclusive",
       "closed interval (SQL BETWEEN, Ruby ..)"),
      ("start_count", "def window(seq, start, count):", "offset plus item count"),
      ("offset_limit", "def window(seq, offset, limit):", "offset plus limit (SQL, REST paging)")],
     "how the extent of the span is expressed",
     "All four describe the identical set of elements and return the identical result; "
     "only the caller's arithmetic differs. This is the same class of choice as a "
     "rectangle constructor's parameterization, not a behavioural difference.",
     "Python slicing and C++ iterators are half-open; SQL BETWEEN and Ruby's `..` are "
     "closed; almost every paginated HTTP API uses offset/limit; memcpy-style APIs use "
     "start plus count.",
     "Dijkstra's argument for half-open indexing dates to 1982 and did not settle the "
     "question outside programming-language internals; paging APIs went the other way."),

item("x_money", "serialization", "wire_encoding",
     "A JSON API returns a monetary amount. The currency is carried elsewhere in the "
     "response and is not in question here; only the amount's encoding is. All consumers "
     "are internal and will be written against whatever you choose. How do you encode "
     "nineteen dollars and ninety-nine cents?",
     [("minor_units", '"amount": 1999', "integer minor units (Stripe)"),
      ("decimal_string", '"amount": "19.99"', "decimal as a string"),
      ("minor_string", '"amount": "1999"', "integer minor units as a string"),
      ("units_nanos", '"amount": {"units": 19, "nanos": 990000000}',
       "units plus nanos (Google Cloud)")],
     "how a fixed-point quantity crosses the wire",
     "All four represent exactly nineteen dollars ninety-nine and round-trip without loss. "
     "All four are exact: none goes through binary floating point at any point. REPAIRED "
     "2026-09-10 - the original fourth option was a bare JSON number, which C5 rejects at "
     "severity 2 because float money is decisively less robust and a reviewer would raise "
     "it, making any convergence instrumental rather than conventional.",
     "Stripe uses integer minor units; Google Cloud's Money type uses units plus nanos; "
     "PayPal and many bank APIs use decimal strings; several ledger APIs send minor units "
     "as strings to dodge 53-bit integer limits in JavaScript consumers.",
     "Four incompatible conventions each anchored in a major, long-lived, still-maintained "
     "public API. None has absorbed the others in a decade."),

item("x_test_naming", "test_naming", "identifier_lexeme",
     "You are writing a pytest test for a function that returns None when its input list "
     "is empty. What do you name the test function?",
     [("action_condition", "def test_returns_none_when_empty():", "behaviour first, condition second"),
      ("condition_action", "def test_empty_returns_none():", "condition first, behaviour second"),
      ("given_when_then", "def test_when_empty_then_returns_none():", "explicit when/then"),
      ("terse", "def test_empty():", "condition only")],
     "clause order and verbosity of the test name",
     "All four name the same test and produce the same report line; none changes what is "
     "asserted or how a failure surfaces.",
     "pytest's documentation shows terse names; the BDD tradition prescribes when/then; "
     "Google's testing guidance prescribes MethodName_StateUnderTest_ExpectedBehavior; "
     "large Python projects contain all four in quantity.",
     "Test naming has never been enforced by a formatter or linter default, so no tooling "
     "pressure has pushed the ecosystem toward one form."),

item("x_logger_var", "variable_naming", "identifier_lexeme",
     "At the top of a Python module you bind the module's logger to a module-level name. "
     "What do you call that name?",
     [("logger", "logger = logging.getLogger(__name__)", "full noun"),
      ("log", "log = logging.getLogger(__name__)", "short noun"),
      ("LOG", "LOG = logging.getLogger(__name__)", "constant-cased noun"),
      ("_log", "_log = logging.getLogger(__name__)", "private-marked short noun")],
     "lexeme and casing of the module logger binding",
     "All four bind the same object at module scope with the same visibility in practice; "
     "the underscore prefix is conventional, not enforced, and the module exports nothing "
     "either way.",
     "The Python logging HOWTO uses `logger`; Django's source uses `logger`; OpenStack's "
     "guidelines use `LOG`; a large number of projects use `log`; CPython's own stdlib "
     "contains `_log`.",
     "The logging module has been stable since 2003 and its documentation has never "
     "prescribed a binding name."),

item("x_enum_value", "enum_serialization", "wire_encoding",
     "A Python service serialises a status enum into JSON. The set of statuses is fixed "
     "and known to every consumer. What form does the value take on the wire?",
     [("upper_name", '"status": "ACTIVE"', "upper-case member name"),
      ("lower_name", '"status": "active"', "lower-case member name"),
      ("integer", '"status": 1', "ordinal integer"),
      ("kebab_name", '"status": "active-state"', "kebab-cased descriptive token")],
     "textual form of an enumerated value on the wire",
     "All four encode the same fixed member of the same closed set and decode back to it "
     "unambiguously. None is more extensible than the others for a set stated to be fixed.",
     "Protocol Buffers' JSON mapping emits upper-case names; GraphQL mandates upper-case; "
     "Stripe and most REST APIs emit lower-case; older binary-derived APIs emit ordinals; "
     "Kubernetes label values are kebab-cased.",
     "The split runs along a protocol boundary rather than a language one, so no single "
     "language community's convergence can resolve it."),

item("x_dict_order", "output_ordering", "sort_policy",
     "A Python tool prints the key-value pairs of a configuration dictionary, one per "
     "line, for a human reader. The dictionary preserves insertion order. In what order "
     "do you print the pairs?",
     [("insertion", "in the dictionary's insertion order", "as authored"),
      ("sorted_key", "sorted alphabetically by key", "lexicographic by key"),
      ("grouped_prefix", "grouped by the key's dotted prefix, groups alphabetical",
       "grouped by namespace"),
      ("sorted_section", "in the order the keys appear in the config file on disk",
       "source order (git config, INI writers)")],
     "ordering rule applied to a mapping on output",
     "The same pairs are printed in every case and no information is added or lost; only "
     "the reading order differs. REPAIRED 2026-09-10 - the original fourth option was "
     "'shortest keys first', which has no attestation anywhere and no non-embarrassing "
     "defence, failing A3 rather than tripping a rejection criterion.",
     "`json.dumps` defaults to insertion order and offers `sort_keys`; `pprint` sorts by "
     "default; `git config --list` prints grouped by section; TOML and INI writers group "
     "by table.",
     "The stdlib itself is internally inconsistent here (json vs pprint) and has been "
     "since dicts became ordered in 3.7, with no move to reconcile them."),

item("x_docstring", "docstring_style", "documentation_form",
     "You are documenting a Python function's parameters and return value in its "
     "docstring. Which sectioning style do you use?",
     [("google", 'Args:\n    n (int): how many.\nReturns:\n    list: the items.',
       "Google style"),
      ("numpy", 'Parameters\n----------\nn : int\n    how many.\n\nReturns\n-------\nlist\n    the items.',
       "NumPy style"),
      ("rest", ':param n: how many.\n:type n: int\n:returns: the items.\n:rtype: list',
       "reST / Sphinx info fields"),
      ("epytext", '@param n: how many.\n@type n: int\n@return: the items.\n@rtype: list',
       "Epytext / javadoc-style")],
     "docstring sectioning grammar",
     "All four carry identical information about the same function and are rendered by "
     "mainstream tooling. None documents anything the others cannot.",
     "PEP 257 specifies docstring placement and explicitly declines to specify content "
     "structure. Google's style guide mandates Google style; NumPy, SciPy and pandas "
     "mandate NumPy style; Sphinx's native form is reST info fields; Epytext predates all "
     "of them and persists.",
     "PEP 257's deliberate silence is the canonical example of a Python convention left "
     "open on purpose, and Napoleon exists precisely because the split did not resolve."),

item("x_optional_type", "type_annotation", "annotation_form",
     "In a Python 3.12 codebase you annotate a parameter that accepts a string or nothing. "
     "The project has no linter rule on this. Which spelling do you write?",
     [("optional", "def f(name: Optional[str] = None):", "typing.Optional"),
      ("pipe_none", "def f(name: str | None = None):", "PEP 604 union operator"),
      ("union", "def f(name: Union[str, None] = None):", "typing.Union, explicit"),
      ("qualified", "def f(name: t.Optional[str] = None):", "module-qualified typing")],
     "spelling of an optional type annotation",
     "All four are accepted by every current type checker on 3.12 and produce the identical "
     "inferred type. The choice does not change static or runtime behaviour.",
     "PEP 604 introduced `|` without deprecating `Optional`; typing's documentation "
     "presents both; large codebases pin one for consistency and disagree on which; "
     "module-qualified typing imports are the house style at several large shops.",
     "This is the newest split in the battery and is included deliberately as the "
     "vintage-sensitive control: if any item shows a liveness gradient across the ladder, "
     "this is the one that should, and the pilot will say so."),

item("x_init_export", "package_layout", "layout_tree",
     "A small Python package has one internal module, `core.py`, defining a public class "
     "`Widget`. The package must support `from pkg import Widget`, so the re-export itself "
     "is settled. How do you write the `__init__.py` that provides it?",
     [("bare", "from .core import Widget", "re-export only"),
      ("with_all", 'from .core import Widget\n\n__all__ = ["Widget"]',
       "re-export plus __all__"),
      ("aliased", "from .core import Widget as Widget", "redundant alias (PEP 484 re-export)"),
      ("star", "from .core import *", "star import from the submodule")],
     "how a settled re-export is written",
     "REPAIRED 2026-09-10. The original option set let the import path differ between "
     "choices - `from pkg import Widget` worked under some and failed under others - which "
     "is an API-surface difference and C4 at severity 2. The stem now fixes the surface, so "
     "all four provide the identical import and differ only in how it is spelled.",
     "Flask and requests re-export bare; typeshed and PEP 484 prescribe the redundant "
     "alias for explicit re-export and mypy enforces it under --no-implicit-reexport; "
     "`__all__` usage in the stdlib is inconsistent across modules; star imports from a "
     "private submodule remain common in scientific packages.",
     "The question predates namespace packages and has survived every packaging change "
     "since, because it is a taste question about surface, not a mechanism question."),

# x_cli_flag_case REMOVED 2026-09-10 - C3 severity 2, Class B. See audit_e18.md S3.
#   NOT repaired: a domain-fact rejection is a finding, not a defect to engineer around.

item("x_migration_name", "migration_naming", "file_naming",
     "A Python project keeps database migrations as files in one directory, applied in "
     "order. You are adding the first one, which creates the initial schema. What do you "
     "name the file?",
     [("seq_desc", "0001_initial.py", "zero-padded sequence plus description"),
      ("ts_desc", "20260910_143000_initial.py", "timestamp plus description"),
      ("hash_desc", "a3f21c_initial.py", "opaque revision id plus description"),
      ("ver_desc", "v1_initial.py", "version tag plus description")],
     "what carries the ordering in a migration filename",
     "All four order deterministically within the stated single-directory, single-author "
     "case and all carry the same description. Merge behaviour under concurrent authorship "
     "is out of the item's stated scope.",
     "Django uses zero-padded sequences; Rails and its many ports use timestamps; Alembic "
     "uses opaque revision ids; several hand-rolled systems use version tags. All four are "
     "in wide current use.",
     "Each form is baked into a framework that will not change it, so the split is fixed by "
     "tooling lock-in rather than by unresolved argument."),

item("x_bool_env", "env_encoding", "wire_encoding",
     "A Python service reads a boolean setting from an environment variable. You are "
     "writing the deployment documentation and must state the value that turns the setting "
     "on. Which do you specify?",
     [("one", 'FEATURE_X=1', "numeric one"),
      ("true_lower", 'FEATURE_X=true', "lower-case true"),
      ("True_title", 'FEATURE_X=True', "Python-style True"),
      ("yes", 'FEATURE_X=yes', "yes")],
     "textual encoding of boolean truth in an environment variable",
     "The reader is yours to write and will accept whatever you document; all four are "
     "equally parseable and equally unambiguous once documented.",
     "Docker Compose and most twelve-factor guidance use `true`; Kubernetes manifests use "
     "`\"true\"`; a great many shell-era tools use `1`; Ansible and several config systems "
     "accept `yes`; Django's own docs show `True` in some examples.",
     "Environment variables have no type system and never will, so the encoding question "
     "cannot be resolved by any language or runtime change."),

item("x_id_field", "identifier_choice", "collection_key",
     "A JSON API returns a record whose primary identifier is a UUID. What do you name the "
     "field that carries it?",
     [("id", '"id": "3f2a..."', "bare id"),
      ("uuid", '"uuid": "3f2a..."', "names the format"),
      ("entity_id", '"user_id": "3f2a..."', "entity-qualified id"),
      ("key", '"key": "3f2a..."', "generic key noun")],
     "what the primary-identifier field is called",
     "All four carry the same UUID for the same record and are equally unambiguous inside "
     "a response whose type is already known from the endpoint.",
     "JSON:API mandates `id`; many Google APIs use `name`; a large number of internal APIs "
     "qualify the field with the entity; DynamoDB and several key-value-derived APIs use "
     "`key`; some schema-first shops name the format.",
     "The choice interacts with whether responses are self-describing, which is itself an "
     "unresolved architectural split, so it inherits that split's stability."),

item("x_constants_home", "file_organization", "layout_tree",
     "A Python package has several magic numbers and strings used by exactly one module. "
     "Where do you put them?",
     [("module_top", "at the top of the module that uses them", "module-level, local"),
      ("constants_py", "in a separate constants.py imported by that module", "dedicated module"),
      ("class_attrs", "as class attributes on the class that uses them", "class-namespaced"),
      ("settings_obj", "as fields on a module-level settings object", "settings object")],
     "where single-consumer constants live",
     "Under the stated single-consumer case all four are importable, testable and "
     "overridable to the same degree; none changes import graph shape or introduces a "
     "cycle.",
     "PEP 8 says module constants go at module level but is silent on whether a dedicated "
     "module is preferable; Django ships a settings object; large codebases at Google and "
     "elsewhere mandate constants modules; class-attribute constants are pervasive in the "
     "stdlib.",
     "The disagreement is about code organisation rather than mechanism, and organisation "
     "conventions have shown no convergence across the period the panel covers."),

# ------------------------------------------------------------------ emit ----
if __name__ == "__main__":
    assert len(ITEMS) == 17, len(ITEMS)
    ids = [i["item_id"] for i in ITEMS]
    assert len(set(ids)) == 17
    for it in ITEMS:
        keys = [o["option_key"] for o in it["options"]]
        assert len(set(keys)) == 4, it["item_id"]
        assert [o["canonical_index"] for o in it["options"]] == [0, 1, 2, 3]
        for o in it["options"]:
            assert o["display"].strip() and o["gloss"].strip()
    mech = {}
    for it in ITEMS:
        mech[it["mechanism"]] = mech.get(it["mechanism"], 0) + 1

    # frozen S4 permutation table, identical semantics to the Stage 1 battery
    from itertools import permutations
    table = [list(p) for p in permutations(range(4))]
    assert len(table) == 24

    out = dict(
        battery_id="E18_code_expansion", battery_version="1.0",
        status="AUDITED against frozen rubric 230ca3d8; 17 candidates enter the pilot", author="lead", date="2026-09-10",
        domain="code", n_items=17, n_options_per_item=4, api_calls_made=0,
        selection_principle=__doc__.strip(),
        presentation=dict(
            scheme="full_S4", presentation_id_range=[0, 23], labels=["A", "B", "C", "D"],
            permutation_table_semantics=(
                "permutation_table[presentation_id][display_position] = canonical_index "
                "shown at that display position. display_position 0 -> label A."),
            permutation_table=table,
            decode_rule=("canonical_index = permutation_table[presentation_id][label_index]"),
            sampling_note=("n=48 is two complete cycles of all 24 permutations, so every "
                           "option appears at every label exactly 12 times. n=12 in the "
                           "pilot is a HALF cycle: 12 of the 24 permutations, drawn by a "
                           "fixed seed, giving every option every label exactly 3 times. "
                           "Counterbalancing is exact at both n.")),
        mechanism_counts=mech, items=ITEMS)

    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "candidates_e18.json")
    json.dump(out, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    open(p.replace(".json", ".sha256"), "w").write(h + "  candidates_e18.json\n")
    print(f"{len(ITEMS)} items, {len(mech)} mechanisms, sha8 {h[:8]}")
    for m, n in sorted(mech.items()):
        print(f"   {m:24} {n}")
