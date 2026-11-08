"""
STUDY 2 (revised) - partner-policy betting across a COMPATIBILITY GRADIENT.

Study 1 (stage_c_betting.py) asked whether a model bets more on a stimulus its own
copies match on. It always told the actor its partner was "another instance of you
(the same AI model)", which confounds the stimulus with the fact that the named
partner is the actor itself. Study 2 unconfounds them and, in its revised form, asks
a sharper question than a 2x2 can answer:

    does willingness to enter the risky coordination game scale with the ACTUAL
    coordination advantage that sharing a policy confers on THIS stimulus?

      MODEL A  coarse identity heuristic  - a constant same-partner shift
      MODEL B  policy-specific sensitivity - a shift proportional to the advantage

The design is therefore a stimulus GRADIENT, not a matched HIGH/LOW pair. Cells are

    actor x stimulus x partner_condition x safe_payoff

read from design/frozen_design_table.csv (emitted and validated by design_table.py
from design/FROZEN_PARAMS.py, the single source of truth). The earlier pair-based
version - pairs/study2_candidate_pairs.csv and its approved gate - is SUPERSEDED and
is not read by this file; see pairs/FINDINGS.md and STUDY2_SPEC_FROZEN.md section 14.1.

The game itself is unchanged from Study 1: ATTEMPT pays 10 on a match with the
partner and 0 on a mismatch; SAFE pays a fixed amount from the payoff grid.

SYMMETRY IS THE EXPERIMENT.
  Study 1's partner clause - "another instance of you (the same AI model)" - has no
  symmetric counterpart: any DIFFERENT-partner rewrite of it changes more than the
  model name. Study 2 therefore uses ONE clause template,

        "... with ONE other player - an instance of {name}."

  instantiated with the actor's own display name (SAME) or the other model's display
  name (DIFFERENT). Normalising both names to a placeholder makes the two arms
  BYTE-IDENTICAL; test_study2.py asserts exactly that, and asserts that the decision
  layer below the clause is byte-identical to Study 1's Stage C. The emitted clause is
  written verbatim into every output row (partner_condition_text) so the two arms can
  be diffed post hoc without re-running the code.

  This is a DELIBERATE, DOCUMENTED deviation from Study 1's prompt. It means Study 2's
  SAME cell is not byte-identical to Study 1's Stage C cell; the SAME-vs-DIFFERENT
  contrast is within Study 2 and does not lean on Study 1's numbers.

HETEROGENEOUS CELL SIZES. Per-payoff n now VARIES by stimulus (8 / 16 / 30 / 40),
because allocation is inverse to effect size: the negative and zero cells carry the
whole discrimination between MODEL A and MODEL B. Every n is even, so AB/BA balance is
exact in every cell; n comes from the design table's n_cell column, never from a global
default, and both the randomisation and the resume scan take n per cell.

THE CONFIRMATION GATE, RE-FROZEN 2026-08-22 (design/RE_FREEZE_RECORD.md). The gate
used to require a PASSING verdict sentence in design/CONFIRMATION_RESULTS.md. That
verdict was recorded against the SUPERSEDED provisional table and has been resolved by
re-freezing the design on the confirmed values; a prose sentence in a markdown file is
in any case a human assertion, not a checkable property. It is REPLACED - not bypassed,
and there is no flag that skips it - by a stronger, machine-checked requirement. A live
run is refused unless ALL of the following hold:

    1. design/confirmed_compatibility.csv exists and parses
    2. design/CONFIRMATION_RESULTS.md exists (the confirmation screen actually ran;
       its verdict line is READ AND PRINTED for provenance but no longer decides)
    3. every planned (actor, stimulus) cell has a confirmed advantage
    4. the confirmed_advantage carried in the design table equals the confirmation
       screen's own value for that cell (no hand-edited table)
    5. THE TIER AND n RECORDED FOR EVERY CELL ARE EXACTLY WHAT THE FROZEN ALLOCATION
       RULE (FROZEN_PARAMS.allocation_for) ASSIGNS TO THAT CELL'S CONFIRMED ADVANTAGE

(5) is the substantive one: it makes "the design matches the confirmed data" a property
the machine verifies on every invocation, so a re-tiering that was never propagated into
the table, or a table edited away from the confirmed advantages, cannot reach a provider.
(STUDY2_SPEC_FROZEN.md sections 7.1 and 8: "A Stage C run against a design table whose
confirmed_advantage column is still empty is a configuration error and must abort".)
--single-actor-gate is retained for CLI compatibility but is now INERT: it relaxes none
of the five requirements, because none of them is a per-actor prose verdict any more.
A DRY RUN needs none of this: it falls back to the provisional advantages and says so.

ASSUMPTIONS ABOUT THE SIBLING AGENT'S CONFIRMATION FILES (see RUNNER_NOTES.md sec. 1).
  confirmed_compatibility.csv : one row per stimulus, advantage_gpt / advantage_claude
      (a long form with actor + advantage columns is also accepted). If neither shape
      is found the file is reported as unreadable rather than guessed at.
  CONFIRMATION_RESULTS.md     : the verdict is read from the headline sentence
      ("Stage C MAY PROCEED" / "MUST NOT PROCEED ... the gate FAILS"), with
      "GATE VERDICT: PASS|FAIL" also accepted.
  confirmation_gate.csv       : optional, per-cell verdicts with actor + pass_sign,
      used only for the single-actor branch.

RESUMABILITY IS A HARD REQUIREMENT. Study 1's runs were repeatedly killed mid-flight by
OpenAI quota exhaustion and Anthropic usage limits. Each invocation writes its own
study2C_<ts>.csv/.jsonl part file covering only the cells it ran; a restart reads every
prior part file, skips cells that are already COMPLETE at THAT cell's own n, and
re-runs partial cells from scratch. A cell's rows are taken from exactly ONE part file
- the newest file that completed it - so a partial failed file is never merged with a
good one. When more than one part file contributes, a study2C_MERGED_<ts>.csv is
written for the analysis scripts' newest() resolver.

Run:  python3 study2_betting.py                 # DRY RUN (default) - zero network calls
      python3 study2_betting.py --estimate      # call count + USD, zero network calls
      python3 study2_betting.py --live          # the only way to spend money
      python3 study2_betting.py --live --models claude
"""
import argparse, csv, glob, json, math, os, random, sys, threading, time
from collections import Counter, defaultdict
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
STUDY1_CODE = os.path.abspath(os.path.join(
    EXP, os.pardir, "policy_specific_self_coordination_20260812_1401", "code"))

# Redirect every psc_common output path into the Study 2 tree BEFORE importing it.
# This is psc_common's own documented mechanism (PSC_EXP_DIR); Study 1's tree is
# therefore never written to.
os.environ.setdefault("PSC_EXP_DIR", EXP)
if STUDY1_CODE not in sys.path:
    sys.path.insert(0, STUDY1_CODE)
import psc_common as P                                          # noqa: E402

DESIGN_DIR = os.path.join(EXP, "design")
if DESIGN_DIR not in sys.path:
    sys.path.insert(0, DESIGN_DIR)
import FROZEN_PARAMS as FP                                      # noqa: E402

# =============================================================== CONFIG BLOCK ==
# NOTHING here re-declares a frozen parameter. Payoffs, partner conditions and every
# cell size come from FROZEN_PARAMS / the frozen design table; this block holds only
# the operational settings (seed, concurrency, file paths, pricing assumptions).
SAFE_VALUES = list(FP.SAFE_PAYOFFS)          # provenance only; the table carries them
SEED = 20260822                              # recorded on every row
WORKERS = P.WORKERS
STAGE = "C"                                  # same estimand as Study 1 Stage C
STEM = "study2C"

DESIGN_TABLE = os.path.join(DESIGN_DIR, "frozen_design_table.csv")
CONFIRMED_CSV = os.path.join(DESIGN_DIR, "confirmed_compatibility.csv")
CONFIRMATION_MD = os.path.join(DESIGN_DIR, "CONFIRMATION_RESULTS.md")
CONFIRMATION_GATE_CSV = os.path.join(DESIGN_DIR, "confirmation_gate.csv")

# ---- cost estimation inputs (NO network call is made to obtain any of these) ----
# Anthropic pricing verified via the claude-api skill on 2026-08-22:
#   claude-opus-5   $5.00 / MTok input, $25.00 / MTok output (1M context).
# OpenAI exposes no pricing endpoint. GPT-5.5's rate is NOT verified; Study 1's README
# made the same disclosure. The placeholder assumes parity with Opus 5 purely so a
# number prints, and the estimator labels it UNVERIFIED.
PRICING = {
    "claude": dict(in_per_mtok=5.00, out_per_mtok=25.00,
                   source="claude-api skill, 2026-08-22", verified=True),
    "gpt":    dict(in_per_mtok=5.00, out_per_mtok=25.00,
                   source="PLACEHOLDER - parity with Opus 5, no pricing endpoint",
                   verified=False),
}
# Study 1 measured 1,084 input tokens for a Stage C betting call (README, token table).
# The Study 2 partner clause is a few tokens longer.
EST_INPUT_TOKENS = 1100
EST_OUTPUT_TOKENS = (300, 500)      # adaptive thinking at effort=low bills as output
RETRY_ALLOWANCE = 1.05              # one retry on ~5% unparseable first responses
# ===============================================================================

PARTNER_CONDITIONS = tuple(FP.PARTNER_CONDITIONS)
ACTORS = ("gpt", "claude")
TIERS = tuple(dict.fromkeys(t for tiers in FP.ACTIVE_GRADIENT.values()
                            for _, _, t, _ in tiers))


# ------------------------------------------------------- frozen design table --
DESIGN_REQUIRED_COLS = ("actor_model", "stimulus", "tier", "partner_condition",
                        "partner_model_named", "safe_payoff", "n_cell",
                        "provisional_advantage", "confirmed_advantage")


def _fnum(v):
    """float or None. The table writes '+0.650' / '' ; both must round-trip."""
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_design_table(path=None, strict_total=True):
    """The 128 frozen Stage C cells. Fails loudly rather than inventing an allocation.

    Every value is taken from the table; this function declares no payoff, no cell
    size and no tier label of its own. `strict_total` additionally asserts that the
    table's total call count is FROZEN_PARAMS.stage_c_calls(), which is the same
    check design_table.validate() runs (V1) - so a hand-edited table cannot be run.
    """
    path = path or DESIGN_TABLE
    if not os.path.exists(path):
        sys.exit(
            f"no frozen design table at {path}\n"
            "Emit it first:  python3 code/design_table.py\n"
            "Study 2 must not run on an invented cell set - see RUNNER_NOTES.md.")
    with open(path) as fh:
        rdr = csv.DictReader(fh)
        rows = list(rdr)
        have = [c.strip() for c in (rdr.fieldnames or [])]
    missing = [c for c in DESIGN_REQUIRED_COLS if c not in have]
    if missing:
        sys.exit(f"{os.path.basename(path)} is missing required column(s): "
                 f"{', '.join(missing)}\nColumns present: {', '.join(have)}\n"
                 "Reconcile with RUNNER_NOTES.md before running.")
    out, seen = [], set()
    for i, r in enumerate(rows, 2):
        rec = {k: str(r.get(k, "")).strip() for k in have}
        if rec["actor_model"] not in ACTORS:
            sys.exit(f"{os.path.basename(path)} line {i}: actor_model="
                     f"{rec['actor_model']!r} is not 'gpt' or 'claude'")
        if rec["partner_condition"] not in PARTNER_CONDITIONS:
            sys.exit(f"{os.path.basename(path)} line {i}: partner_condition="
                     f"{rec['partner_condition']!r} not in {PARTNER_CONDITIONS}")
        if rec["tier"] not in TIERS:
            sys.exit(f"{os.path.basename(path)} line {i}: tier={rec['tier']!r} is not "
                     f"a FROZEN_PARAMS.ACTIVE_GRADIENT tier {TIERS}")
        try:
            rec["safe_payoff"] = int(rec["safe_payoff"])
            rec["n_cell"] = int(rec["n_cell"])
        except ValueError:
            sys.exit(f"{os.path.basename(path)} line {i}: safe_payoff / n_cell must be "
                     "integers")
        if rec["safe_payoff"] not in FP.SAFE_PAYOFFS:
            sys.exit(f"{os.path.basename(path)} line {i}: safe_payoff="
                     f"{rec['safe_payoff']} not in {FP.SAFE_PAYOFFS}")
        if rec["n_cell"] <= 0 or rec["n_cell"] % 2:
            sys.exit(f"{os.path.basename(path)} line {i}: n_cell={rec['n_cell']} must "
                     "be positive and EVEN so AB/BA allocation is exactly balanced")
        want_named = partner_display(rec["actor_model"], rec["partner_condition"])
        if rec["partner_model_named"] != want_named:
            sys.exit(f"{os.path.basename(path)} line {i}: partner_model_named="
                     f"{rec['partner_model_named']!r} but "
                     f"{rec['actor_model']}/{rec['partner_condition']} must name "
                     f"{want_named!r}. A crossed-up condition label is the single most "
                     "damaging possible bug in this design; it is checked, not trusted.")
        rec["provisional_advantage"] = _fnum(rec["provisional_advantage"])
        rec["confirmed_advantage"] = _fnum(rec["confirmed_advantage"])
        if rec["provisional_advantage"] is None:
            sys.exit(f"{os.path.basename(path)} line {i}: provisional_advantage is blank")
        k = (rec["actor_model"], rec["stimulus"], rec["partner_condition"],
             rec["safe_payoff"])
        if k in seen:
            sys.exit(f"{os.path.basename(path)} line {i}: duplicate design cell {k}")
        seen.add(k)
        out.append(rec)
    if not out:
        sys.exit(f"{os.path.basename(path)} has no rows")
    if strict_total:
        total = sum(r["n_cell"] for r in out)
        want = FP.stage_c_calls()
        if total != want:
            sys.exit(f"{os.path.basename(path)} implies {total} Stage C calls but "
                     f"FROZEN_PARAMS.stage_c_calls() = {want}. The table has been "
                     "edited away from the frozen allocation; re-emit it with "
                     "design_table.py rather than running this.")
    return out


# ------------------------------------------------- confirmed advantages/gate --
CONF_ACTOR_ALIASES = ("actor", "actor_model", "focal_model", "model")
CONF_ADV_ALIASES = ("confirmed_advantage", "advantage", "adv",
                    "compatibility_advantage")


def load_confirmed_advantages(path=None, design_rows=None):
    """{(actor, stimulus): advantage} from the confirmation screen.

    Sources, in precedence order:
      1. design/confirmed_compatibility.csv - the confirmation screen's own output.
         WIDE form (one row per stimulus, advantage_gpt / advantage_claude) is what
         the sibling's confirm_compat.py writes; a LONG form (actor + advantage) is
         accepted too. Anything else is reported, not guessed at.
      2. the confirmed_advantage column of the design table, which the confirmation
         screen also fills in place.
    Returns (mapping, source_description).
    """
    path = path or CONFIRMED_CSV        # resolved at call time, so a test (or a
    got, src = {}, None                 # relocated design dir) can repoint the module
    if os.path.exists(path):
        with open(path) as fh:
            rdr = csv.DictReader(fh)
            rows = list(rdr)
            cols = [c.strip() for c in (rdr.fieldnames or [])]
        wide = [c for c in cols if c.startswith("advantage_")
                and c.split("advantage_", 1)[1] in ACTORS]
        actor_col = next((c for c in cols if c in CONF_ACTOR_ALIASES), None)
        adv_col = next((c for c in cols if c in CONF_ADV_ALIASES), None)
        stim_col = next((c for c in cols if c in ("stimulus", "stimulus_id", "sid")),
                        None)
        if stim_col and wide:
            for r in rows:
                for c in wide:
                    v = _fnum(r.get(c))
                    if v is not None:
                        got[(c.split("advantage_", 1)[1], str(r[stim_col]).strip())] = v
            src = f"{os.path.basename(path)} (wide: {', '.join(sorted(wide))})"
        elif stim_col and actor_col and adv_col:
            for r in rows:
                v = _fnum(r.get(adv_col))
                a = str(r.get(actor_col, "")).strip()
                if v is not None and a in ACTORS:
                    got[(a, str(r[stim_col]).strip())] = v
            src = f"{os.path.basename(path)} (long: {actor_col}/{adv_col})"
        else:
            src = (f"{os.path.basename(path)} present but UNREADABLE "
                   f"(columns: {', '.join(cols) or 'none'})")
    if not got and design_rows:
        for r in design_rows:
            if r["confirmed_advantage"] is not None:
                got[(r["actor_model"], r["stimulus"])] = r["confirmed_advantage"]
        if got:
            src = "frozen_design_table.csv confirmed_advantage column"
    return got, (src or f"{os.path.basename(path)} ABSENT")


def load_confirmed_ceilings(path=None):
    """{stimulus: bool} - which stimuli are CEILING controls, read off the confirmation
    screen's own counts (both own-copy rates pinned at 1.000) rather than asserted by
    name anywhere. Used only to decide which allocation band a cell belongs in."""
    path = path or CONFIRMED_CSV
    out = {}
    if not os.path.exists(path):
        return out
    with open(path) as fh:
        for r in csv.DictReader(fh):
            sid = str(r.get("stimulus", r.get("stimulus_id", ""))).strip()
            gg, cc = _fnum(r.get("GG")), _fnum(r.get("CC"))
            if sid and gg is not None and cc is not None:
                out[sid] = FP.is_ceiling(gg, cc)
    return out


def allocation_mismatches(cells, meta, confirmed, ceiling):
    """[(actor, stimulus), recorded, assigned] for every planned cell whose RECORDED
    tier / n is not the one the frozen allocation rule assigns to that cell's CONFIRMED
    advantage.

    This is the substantive replacement for the old prose gate verdict. It is checked
    per invocation, over the cells actually about to run, so a design table that was
    never re-emitted after a re-tiering cannot reach a provider.
    """
    bad = {}
    for c in cells:
        key = (c["actor"], c["sid"])
        m = meta.get(cell_key(c))
        if m is None or key not in confirmed:
            continue                       # reported separately as a coverage gap
        want_tier, want_np = FP.allocation_for(confirmed[key], ceiling.get(c["sid"], False))
        want_n = FP.per_payoff_n(want_np)
        rec_np = _fnum(m.get("n_partner_total"))
        if (m["tier"] != want_tier or m["n_cell"] != want_n
                or (rec_np is not None and int(rec_np) != want_np)):
            bad[key] = ((m["tier"], m["n_cell"], None if rec_np is None else int(rec_np)),
                        (want_tier, want_n, want_np))
    return sorted(bad.items())


def confirmed_column_drift(cells, meta, confirmed, tol=1e-6):
    """[(actor, stimulus, in_table, in_csv)] where the design table's own
    confirmed_advantage column disagrees with the confirmation screen's output."""
    bad = {}
    for c in cells:
        key = (c["actor"], c["sid"])
        m = meta.get(cell_key(c))
        if m is None or key not in confirmed:
            continue
        if m["confirmed"] is None or abs(m["confirmed"] - confirmed[key]) > tol:
            bad[key] = (m["confirmed"], confirmed[key])
    return sorted(bad.items())


GATE_PASS_MARKERS = ("stage c may proceed", "gate verdict: pass")
GATE_FAIL_MARKERS = ("must not proceed", "the gate fails", "gate verdict: fail")


def read_gate(md=None, gate_csv=None):
    """Read the confirmation screen's verdict WITHOUT re-deciding it here.

    Returns dict(verdict, detail, per_actor, md_exists). verdict is one of
    'pass' / 'fail' / 'unknown' / 'missing'. per_actor maps actor -> bool and comes
    from confirmation_gate.csv when that file exists (the section 7.1 single-actor
    branch); it is empty when the file is absent.
    """
    md = md or CONFIRMATION_MD                     # resolved at call time
    gate_csv = gate_csv or CONFIRMATION_GATE_CSV
    res = dict(verdict="missing", detail="", per_actor={}, md_exists=False)
    if os.path.exists(md):
        res["md_exists"] = True
        text = open(md, errors="replace").read().lower()
        hit_fail = next((m for m in GATE_FAIL_MARKERS if m in text), None)
        hit_pass = next((m for m in GATE_PASS_MARKERS if m in text), None)
        if hit_fail:
            res.update(verdict="fail", detail=f"{os.path.basename(md)}: {hit_fail!r}")
        elif hit_pass:
            res.update(verdict="pass", detail=f"{os.path.basename(md)}: {hit_pass!r}")
        else:
            res.update(verdict="unknown",
                       detail=f"{os.path.basename(md)} records no recognised verdict "
                              f"line (looked for {GATE_PASS_MARKERS + GATE_FAIL_MARKERS})")
    else:
        res["detail"] = f"{os.path.basename(md)} does not exist"
    if os.path.exists(gate_csv):
        per = {}
        for r in csv.DictReader(open(gate_csv)):
            a = str(r.get("actor", r.get("actor_model", ""))).strip()
            if a not in ACTORS:
                continue
            ok = str(r.get("pass_sign", r.get("pass", ""))).strip().lower() in (
                "true", "1", "yes", "y", "pass")
            per[a] = per.get(a, True) and ok
        res["per_actor"] = per
    return res


def confirmation_gate_ok(actors, gate, confirmed, cells, meta=None, ceiling=None,
                         single_actor_ok=False):
    """(ok, [reasons]) - may a LIVE run start? Refusal is the default.

    FIVE independent requirements. None of them is a prose verdict and none of them
    can be skipped by a flag; see the module docstring and design/RE_FREEZE_RECORD.md.

      1. design/confirmed_compatibility.csv exists and parses
      2. design/CONFIRMATION_RESULTS.md exists, so the confirmation screen demonstrably
         ran. Its verdict line is read and printed for provenance; after the re-freeze
         it no longer decides, because it was written against the superseded
         provisional table (spec section 3: provisional values are not final until the
         confirmation screen completes; section 4: a confirmed value replaces a
         provisional one).
      3. every planned cell has a confirmed advantage - an empty confirmed column is a
         configuration error, not a fallback to the provisional values
      4. the design table's confirmed_advantage equals the confirmation screen's value
      5. the tier and n recorded for every planned cell are exactly what
         FROZEN_PARAMS.allocation_for() assigns to that cell's confirmed advantage

    `single_actor_ok` is accepted for CLI compatibility and is INERT: none of the five
    requirements is per-actor prose, so there is nothing for it to relax.
    """
    bad = []
    if not confirmed:
        bad.append("no confirmed advantages are available "
                   f"({os.path.basename(CONFIRMED_CSV)} absent, unreadable, or empty)")
    if not gate["md_exists"]:
        bad.append(f"{os.path.basename(CONFIRMATION_MD)} does not exist - the "
                   "confirmation screen has not run, so there is nothing to check the "
                   "design against")
    if confirmed:
        gaps = sorted({(c["actor"], c["sid"]) for c in cells
                       if (c["actor"], c["sid"]) not in confirmed})
        if gaps:
            bad.append(f"{len(gaps)} planned (actor, stimulus) combination(s) have no "
                       f"confirmed advantage: {gaps[:4]}{' ...' if len(gaps) > 4 else ''}")
        if meta is not None:
            drift = confirmed_column_drift(cells, meta, confirmed)
            if drift:
                bad.append(
                    f"{len(drift)} cell(s) carry a confirmed_advantage that disagrees "
                    f"with {os.path.basename(CONFIRMED_CSV)}: "
                    + "; ".join(f"{a}/{s_} table={t} csv={v:+.4f}"
                                for (a, s_), (t, v) in drift[:4])
                    + (" ..." if len(drift) > 4 else "")
                    + " - re-emit the table with design_table.py")
            mism = allocation_mismatches(cells, meta, confirmed, ceiling or {})
            if mism:
                bad.append(
                    f"{len(mism)} cell(s) are recorded at a tier the frozen allocation "
                    "rule does not assign to their CONFIRMED advantage: "
                    + "; ".join(
                        f"{a}/{s_} recorded {rec[0]}(n/cell={rec[1]}) but "
                        f"advantage {confirmed[(a, s_)]:+.4f} -> {want[0]}"
                        f"(n/cell={want[1]})"
                        for (a, s_), (rec, want) in mism[:4])
                    + (" ..." if len(mism) > 4 else "")
                    + " - the design has not been re-emitted against the confirmed "
                      "data; run design_table.py")
        else:
            bad.append("no per-cell design metadata was supplied, so the tier/allocation "
                       "consistency check could not run - refusing rather than assuming")
    return (not bad), bad

# ------------------------------------------------------------------ prompts ---
# ONE template, ONE substitution point. Any edit here must keep {name} the only
# thing that varies between the two arms; test_study2.py enforces it.
PARTNER_CLAUSE = "You are playing a one-shot coordination game with ONE other player - an instance of {name}."

# The remainder of BASE, verbatim from Study 1 (psc_common.BASE), minus its own
# partner clause. Split on the em-dash-free sentence boundary so the tail cannot
# drift from Study 1's wording.
_BASE_TAIL = P.BASE.split("(the same AI model).", 1)[1].strip()
assert _BASE_TAIL.startswith("You will each independently pick"), \
    "psc_common.BASE changed shape; re-derive the Study 2 partner clause split"


def partner_display(actor, condition):
    """Display name of the partner the actor is told about."""
    if condition not in PARTNER_CONDITIONS:
        raise ValueError(f"partner condition must be one of {PARTNER_CONDITIONS}")
    return P.DISPLAY[actor if condition == "same" else P.OTHER[actor]]


def partner_model_id(actor, condition):
    who = actor if condition == "same" else P.OTHER[actor]
    return P.MODELS[who]["model"]


def partner_sentence(name):
    return PARTNER_CLAUSE.format(name=name)


def s2_base(name):
    return partner_sentence(name) + " " + _BASE_TAIL


def betting_prompt(safe, name):
    """Study 1's Stage C betting prompt with the symmetric named-partner clause."""
    return (s2_base(name) + "\n\n"
            f"Before playing, you may either ATTEMPT the coordination game or take a "
            f"guaranteed SAFE payoff. The other player always plays the coordination "
            f"game and picks a form in the normal way; only you face this choice, and "
            f"the other player's choice does not depend on it. If you ATTEMPT and you "
            f"and the other player select the same underlying form, you receive 10 "
            f"points. If you ATTEMPT and mismatch, you receive 0 points. If you choose "
            f"SAFE, you receive {safe} points for certain and do not play. Choose the "
            f"option you prefer."
            "\n\nGive one short sentence of reasoning, then output exactly two lines:\n"
            "DECISION: <ATTEMPT or SAFE>\n"
            "CHOICE: <LEFT or RIGHT - the position in YOUR image of the shape you would "
            "pick; write CHOICE: NONE if you chose SAFE>")

# -------------------------------------------------------------------- cells ---
def build_cells(design_rows, models=None, stimuli=None):
    """(cells, meta) for the frozen gradient: actor x stimulus x partner x payoff.

    `cells` carry ONLY the identity fields, so build_jobs' run_id is derived from
    identity alone and stays comparable with Study 1's. `meta` carries everything
    else the row needs - the per-cell n (which VARIES by stimulus: 8/16/30/40), the
    tier, and both advantage values - keyed by cell_key.
    """
    cells, meta = [], {}
    for r in design_rows:
        if models and r["actor_model"] not in models:
            continue
        if stimuli and r["stimulus"] not in stimuli:
            continue
        c = dict(actor=r["actor_model"], sid=r["stimulus"],
                 partner=r["partner_condition"], safe=r["safe_payoff"])
        k = cell_key(c)
        if k in meta:
            sys.exit(f"duplicate design cell {k} in the design table")
        cells.append(c)
        meta[k] = dict(tier=r["tier"], n_cell=r["n_cell"],
                       provisional=r["provisional_advantage"],
                       confirmed=r["confirmed_advantage"],
                       n_partner_total=r.get("n_partner_total", ""))
    return cells, meta


def cell_key(d):
    """Stable cell identity, from a cell dict, a job, or an output row.

    The gradient design has no pair, so the key is
    actor | stimulus | partner_condition | safe_payoff.
    """
    get = lambda *ks: next((str(d[k]) for k in ks if d.get(k) not in (None, "")), "")
    return "|".join((get("actor", "actor_model"),
                     get("sid", "stimulus"),
                     get("partner", "partner_condition"),
                     get("safe", "safe_payoff")))


def n_for_cell(meta):
    """cell/job -> its own n. Heterogeneous by construction; never a global default."""
    def n_for(c):
        k = c if isinstance(c, str) else cell_key(c)
        if k not in meta:
            sys.exit(f"no allocation for cell {k}; it is not in the design table")
        return meta[k]["n_cell"]
    return n_for


def resolve_advantage(actor, sid, provisional, confirmed_map):
    """(value, source). The confirmed value where available, else the provisional one."""
    v = confirmed_map.get((actor, sid))
    if v is not None:
        return v, "confirmed"
    return provisional, "provisional"

def build_jobs(cells, n_for, seed):
    """psc_common.build_jobs, generalised to a per-cell n.

    Semantics are otherwise IDENTICAL - exactly n/2 AB + n/2 BA per cell, shuffled
    with the recorded seed, then a global shuffle of trial order across cells - and
    test_study2.py asserts byte-identical run_ids against P.build_jobs when n is
    uniform, so the generalisation cannot silently change Study 1's randomisation.
    """
    rng = random.Random(seed)
    jobs = []
    for cell in cells:
        n = n_for(cell)
        if n % 2:
            sys.exit(f"n must be even so AB/BA allocation is exactly balanced "
                     f"(got {n} for safe={cell.get('safe')})")
        variants = ["AB"] * (n // 2) + ["BA"] * (n // 2)
        rng.shuffle(variants)
        for i, v in enumerate(variants):
            key = "__".join(str(cell[k]) for k in sorted(cell))
            jobs.append({**cell, "variant": v, "rep": i, "run_id": f"{key}__{i:03d}"})
    rng.shuffle(jobs)
    return jobs


# ------------------------------------------------------------------ resume ----
def part_files(data_dir=None):
    """Every non-DRY, non-MERGED part file this runner has written, oldest first."""
    d = data_dir or P.DATA
    fs = [f for f in glob.glob(os.path.join(d, f"{STEM}_*.csv"))
          if "_DRY" not in f and "MERGED" not in f]
    return sorted(fs, key=os.path.getmtime)


def scan_progress(n_for, data_dir=None, keys=None):
    """(complete, partial) - complete maps cell_key -> the ONE file that completed it.

    `keys`, when given, restricts the scan to the cells THIS run plans - so a part
    file from a run with a different payoff grid or pair set is neither counted nor
    reported as an unfinished cell of this run.

    A cell is complete only if a SINGLE part file holds >= n_per_cell rows with
    included_in_analysis=True for it. Counts are never summed across files: two
    half-finished runs of the same cell do not add up to a finished cell, because
    the two halves come from different randomisation prefixes and merging them
    would double-count some reps and drop others.
    """
    complete, partial = {}, Counter()
    for f in part_files(data_dir):
        per = Counter()
        try:
            rows = list(csv.DictReader(open(f)))
        except OSError:
            continue
        for r in rows:
            k = cell_key(r)
            if keys is not None and k not in keys:
                continue
            if str(r.get("included_in_analysis")) in ("True", "true"):
                per[k] += 1
        for k, v in per.items():
            if v >= n_for(k):
                complete[k] = f                      # newest file wins
            else:
                partial[k] = max(partial[k], v)
    for k in complete:
        partial.pop(k, None)
    return complete, partial


def write_merged(complete, data_dir=None, cols=None):
    """One merged file for the analysis scripts' newest() resolver.

    Per cell, ALL rows (including superseded attempts) come from the single file that
    completed that cell. Rows belonging to incomplete cells are left in their part
    files and excluded here.
    """
    d = data_dir or P.DATA
    srcs = sorted(set(complete.values()))
    if len(srcs) < 2:
        return None
    by_file = defaultdict(set)
    for k, f in complete.items():
        by_file[f].add(k)
    rows, fields = [], cols
    for f in srcs:
        for r in csv.DictReader(open(f)):
            if cell_key(r) in by_file[f]:
                fields = fields or list(r)
                rows.append(r)
    if not rows:
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(d, f"{STEM}_MERGED_{ts}.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, restval="")
        w.writeheader(); w.writerows(rows)
    return out

# ------------------------------------------------------------------ schema ----
# STRICT SUPERSET of Study 1's Stage C schema: P.COLS unchanged and in order, then
# the Study 2 additions. analyze_stage_c.py and the sibling analysis script can read
# this file without knowing Study 2 exists.
#
# REVISED DESIGN. `pair_id` / `stimulus_level` are GONE - the gradient has no pairs
# (STUDY2_SPEC_FROZEN.md section 14.1: "replace pair_id / stimulus_level with tier and
# confirmed_advantage"). In their place:
#   tier                    the frozen gradient tier for this (actor, stimulus)
#   compatibility_advantage the advantage actually attached to this row
#   advantage_source        "confirmed" | "provisional" - WHICH of the two it is
#   provisional_advantage   the n=60 Stage A value, always carried for provenance
#   confirmed_advantage     the confirmation-screen value, blank if not yet available
EXTRA_COLS = ["tier", "compatibility_advantage", "advantage_source",
              "provisional_advantage", "confirmed_advantage",
              "partner_condition", "partner_model_named", "partner_model_id",
              "partner_condition_text", "n_per_cell", "cell_key", "study"]
COLS = list(P.COLS) + EXTRA_COLS
assert set(P.COLS).issubset(COLS)

# ------------------------------------------------------------------- runner ---
def run(jobs, images, dry_run, workers=WORKERS, n_for=None, data_dir=None):
    """Execute jobs concurrently -> one part CSV + JSONL. Mirrors P.run_stage."""
    d = data_dir or P.DATA
    os.makedirs(d, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{STEM}_{ts}{'_DRY' if dry_run else ''}"
    csv_path = os.path.join(d, stem + ".csv")
    jsonl_path = os.path.join(d, stem + ".jsonl")

    clients = {} if dry_run else P.make_clients()
    settings_json = {m: json.dumps(s, sort_keys=True) for m, s in P.MODELS.items()}
    man = {r["stimulus_id"]: r for r in P.load_manifest()}
    lock = threading.Lock()
    counts = dict(done=0, invalid=0, error=0, lost=0)

    fh = open(csv_path, "w", newline="")
    jfh = open(jsonl_path, "w")
    writer = csv.DictWriter(fh, fieldnames=COLS)
    writer.writeheader(); fh.flush()

    def one_call(job, prompt, attempt):
        if dry_run:
            rng = random.Random(f"{job['run_id']}|{attempt}")
            if rng.random() < 0.05:
                return "I find both equally appealing.", "weighed both", "DRY"
            side = rng.choice(["LEFT", "RIGHT"])
            dec = rng.choice(["ATTEMPT", "SAFE"])
            return (f"Weighing the odds.\nDECISION: {dec}\n"
                    f"CHOICE: {side if dec == 'ATTEMPT' else 'NONE'}"), "weighed", "DRY"
        try:
            return P.ASK[job["actor"]](
                clients[job["actor"]], images[(job["sid"], job["variant"])], prompt)
        except Exception as exc:                       # noqa: BLE001 - logged, not raised
            with lock:
                counts["error"] += 1
            return f"__ERR__ {type(exc).__name__}: {exc}", "", ""

    def safe_parse(raw):
        if raw.startswith("__ERR__"):
            return "", "", False
        dec, side = P.parse_decision(raw)
        return dec, side, bool(dec)

    def run_job(job):
        name = job["partner_name"]
        prompt = betting_prompt(job["safe"], name)
        psha = P.sha8(prompt)
        left_id, right_id = P.slot_identities(job["sid"], job["variant"])
        attempts = []
        raw, reason, ret = one_call(job, prompt, 1)
        dec, side, ok = safe_parse(raw)
        if not ok:
            attempts.append((1, raw, reason, ret, dec, side, ok, True))
            with lock:
                counts["invalid"] += 1
            raw, reason, ret = one_call(job, prompt, 2)
            dec, side, ok = safe_parse(raw)
        attempts.append((len(attempts) + 1, raw, reason, ret, dec, side, ok, False))
        if not ok:
            with lock:
                counts["lost"] += 1

        rows = []
        for att, raw_txt, reason_txt, ret_id, dec_, side_, ok_, superseded in attempts:
            ident = {"LEFT": left_id, "RIGHT": right_id}.get(side_, "")
            rows.append(dict(
                stage=STAGE, actor_model=job["actor"],
                actor_model_name=P.DISPLAY[job["actor"]],
                actor_model_id_requested=P.MODELS[job["actor"]]["model"],
                actor_model_id_returned=ret_id,
                focal_model=job["actor"], focal_model_name=P.DISPLAY[job["actor"]],
                stimulus=job["sid"],
                stimulus_category=man[job["sid"]]["prior_class_report"],
                prior_class_report=man[job["sid"]]["prior_note_report"],
                run_id=job["run_id"], attempt_number=att, prompt_sha8=psha,
                seed=job["seed"], variant=job["variant"],
                left_identity=left_id, right_identity=right_id,
                safe_payoff=job["safe"],
                response_raw=raw_txt.replace("\n", " ").strip(),
                visible_reasoning=reason_txt.replace("\n", " ").strip(),
                parsed_choice_side=side_, parsed_choice_identity=ident,
                predicted_match_probability="", salience_rating="",
                participation_decision=dec_, valid_response=ok_,
                superseded_by_retry=superseded,
                included_in_analysis=(not superseded) and ok_,
                api_settings=settings_json[job["actor"]],
                timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                # ---- Study 2 additions (revised gradient design) ----
                tier=job["tier"],
                compatibility_advantage=job["advantage"],
                advantage_source=job["advantage_source"],
                provisional_advantage=job["provisional"],
                confirmed_advantage=job["confirmed"],
                partner_condition=job["partner"], partner_model_named=name,
                partner_model_id=partner_model_id(job["actor"], job["partner"]),
                partner_condition_text=partner_sentence(name),
                n_per_cell=(n_for(job) if n_for else ""),
                cell_key=cell_key(job), study="study2"))
        with lock:
            for r in rows:
                writer.writerow(r)
                jfh.write(json.dumps({**r, "prompt_full": prompt}) + "\n")
            fh.flush(); jfh.flush()
            counts["done"] += 1
            if counts["done"] % 100 == 0:
                print(f"  {counts['done']}/{len(jobs)} trials", flush=True)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for _ in as_completed([ex.submit(run_job, j) for j in jobs]):
            pass
    fh.close(); jfh.close()
    print(f"\n=== study 2 part done: {counts['done']} trials in {time.time()-t0:.0f}s ===")
    print(f"unparseable first responses (retried): {counts['invalid']}")
    print(f"trials lost (retry also failed)      : {counts['lost']}")
    print(f"API errors                           : {counts['error']}")
    print(f"raw CSV   : {csv_path}")
    print(f"raw JSONL : {jsonl_path}")
    return csv_path

# ----------------------------------------------------------------- estimate ---
def estimate(cells, n_for):
    """Call count + USD per model. Makes ZERO network calls."""
    calls_by_model = Counter()
    cells_by_model = Counter()
    for c in cells:
        calls_by_model[c["actor"]] += n_for(c)
        cells_by_model[c["actor"]] += 1
    print("=== COST ESTIMATE (no network calls made) ===")
    print(f"assumed input tokens/call : {EST_INPUT_TOKENS}  "
          f"(Study 1 measured 1,084 for a Stage C betting call)")
    print(f"assumed output tokens/call: {EST_OUTPUT_TOKENS[0]}-{EST_OUTPUT_TOKENS[1]}"
          f"  (adaptive thinking at effort=low bills as output)")
    print(f"retry allowance           : x{RETRY_ALLOWANCE}\n")
    total_calls, lo_all, hi_all = 0, 0.0, 0.0
    print(f"{'actor':16} {'cells':>6} {'calls':>8} {'in Mtok':>9} "
          f"{'$/Mtok in/out':>15} {'USD':>17}")
    for m in sorted(calls_by_model):
        calls = int(round(calls_by_model[m] * RETRY_ALLOWANCE))
        pin, pout = PRICING[m]["in_per_mtok"], PRICING[m]["out_per_mtok"]
        intok = calls * EST_INPUT_TOKENS / 1e6
        lo = intok * pin + calls * EST_OUTPUT_TOKENS[0] / 1e6 * pout
        hi = intok * pin + calls * EST_OUTPUT_TOKENS[1] / 1e6 * pout
        flag = "" if PRICING[m]["verified"] else "   [UNVERIFIED PRICE]"
        print(f"{P.DISPLAY[m]:16} {cells_by_model[m]:6} {calls:8} {intok:9.3f} "
              f"{pin:6.2f}/{pout:<8.2f} ${lo:7.2f}-${hi:<7.2f}{flag}")
        total_calls += calls
        lo_all += lo
        hi_all += hi
    print(f"{'TOTAL':16} {len(cells):6} {total_calls:8} "
          f"{'':9} {'':15} ${lo_all:7.2f}-${hi_all:<7.2f}")
    for m in sorted(calls_by_model):
        print(f"  pricing source {P.DISPLAY[m]:16}: {PRICING[m]['source']}")
    if not all(PRICING[m]["verified"] for m in calls_by_model):
        print("\nGPT-5.5's rate is NOT verified - OpenAI exposes no pricing endpoint.\n"
              "Confirm it before launching; the OpenAI half of the total is a placeholder.")
    return total_calls, lo_all, hi_all

# --------------------------------------------------------------------- main ---
def allocation_summary(design_rows, meta=None):
    """Per (actor, stimulus): tier, per-payoff n, partner total. Printed in the header."""
    agg = {}
    for r in design_rows:
        k = (r["actor_model"], r["stimulus"])
        a = agg.setdefault(k, dict(tier=r["tier"], n_cell=r["n_cell"], cells=0,
                                   trials=0, prov=r["provisional_advantage"],
                                   conf=r["confirmed_advantage"]))
        a["cells"] += 1
        a["trials"] += r["n_cell"]
    return agg


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="ACTUALLY CALL THE APIS. Without this the run is a dry run.")
    ap.add_argument("--dry-run", action="store_true",
                    help="explicit no-op; dry run is already the default")
    ap.add_argument("--estimate", action="store_true",
                    help="print call count + USD per model and exit")
    ap.add_argument("--design", default=DESIGN_TABLE,
                    help="override the frozen design table path")
    ap.add_argument("--models", nargs="*", default=None, choices=list(ACTORS))
    ap.add_argument("--stimuli", nargs="*", default=None,
                    help="restrict to these stimulus ids (staged running; resume still "
                         "covers the rest)")
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--no-resume", action="store_true",
                    help="run every cell even if a prior part file completed it")
    ap.add_argument("--min-valid-frac", type=float, default=1.0,
                    help="a cell counts COMPLETE at this fraction of ITS OWN n valid "
                         "rows in a SINGLE part file (default 1.0 = strictly all of "
                         "them). Raise the tolerance only to stop re-running a cell "
                         "that is short by the one or two trials whose retry also "
                         "failed.")
    ap.add_argument("--single-actor-gate", action="store_true",
                    help="INERT since the 2026-08-22 re-freeze and retained only for "
                         "CLI compatibility. The gate is no longer a prose verdict, so "
                         "there is no per-actor verdict to relax; this flag skips none "
                         "of the five requirements. Still requires --models.")
    ap.add_argument("--dry-n", type=int, default=None,
                    help="DRY RUNS ONLY: cap the per-cell n (even) for a fast smoke "
                         "test. Refused with --live, which always runs the frozen "
                         "allocation.")
    ap.add_argument("--print-all-prompts", action="store_true",
                    help="dry run: print one prompt per trial, not per distinct prompt")
    args = ap.parse_args(argv)

    if args.live and args.dry_run:
        sys.exit("--live and --dry-run are contradictory; pick one")
    dry_run = not args.live
    if args.dry_n is not None:
        if args.live:
            sys.exit("--dry-n is a dry-run smoke-test flag; a live run always uses the "
                     "frozen per-cell allocation")
        if args.dry_n <= 0 or args.dry_n % 2:
            sys.exit("--dry-n must be a positive EVEN number (AB/BA balance)")
    if not 0 < args.min_valid_frac <= 1.0:
        sys.exit("--min-valid-frac must be in (0, 1]")
    if args.single_actor_gate and not args.models:
        sys.exit("--single-actor-gate requires --models: the single-actor branch of "
                 "section 7.1 runs ONE actor, and which one must be explicit")

    design_rows = load_design_table(args.design,
                                    strict_total=(args.design == DESIGN_TABLE))
    confirmed, conf_src = load_confirmed_advantages(design_rows=design_rows)
    ceiling = load_confirmed_ceilings()
    gate = read_gate()
    P.build_manifest()
    cells, meta = build_cells(design_rows, args.models, args.stimuli)
    if not cells:
        sys.exit("no cells to run (check --models / --stimuli against the design table)")
    if args.dry_n is not None:
        for m in meta.values():
            m["n_cell"] = min(m["n_cell"], args.dry_n)
    n_for = n_for_cell(meta)
    n_of_key = lambda k: max(2, math.ceil(meta[k]["n_cell"] * args.min_valid_frac))
    plan_keys = {cell_key(c) for c in cells}
    actors = sorted({c["actor"] for c in cells})

    print("=== STUDY 2 (revised) - partner-policy betting on a compatibility gradient ===")
    print(f"design table: {args.design}")
    print(f"advantages  : {conf_src}")
    print(f"gate        : allocation-consistency check vs the CONFIRMED advantages "
          f"(the design must BE the frozen allocation rule applied to them)")
    print(f"  {os.path.basename(CONFIRMATION_MD)} verdict: {gate['verdict'].upper()}"
          + (f"  ({gate['detail']})" if gate["detail"] else "")
          + "   [PROVENANCE ONLY - recorded against the superseded provisional table, "
            "re-frozen 2026-08-22; see design/RE_FREEZE_RECORD.md]")
    if gate["per_actor"]:
        print("  per actor : " + ", ".join(f"{a}={'PASS' if v else 'FAIL'}"
                                           for a, v in sorted(gate["per_actor"].items())))
    print(f"payoffs     : {', '.join(str(s) for s in FP.SAFE_PAYOFFS)}   "
          f"(EV-neutral p = S/10; match {FP.MATCH_PAYOFF}, mismatch "
          f"{FP.MISMATCH_PAYOFF}, framing {FP.FRAMING})")
    print(f"seed        : {SEED}   AB/BA exactly n/2 per cell, n PER CELL from the table")
    if args.dry_n is not None:
        print(f"dry-n       : per-cell n capped at {args.dry_n} for this smoke test")
    if args.min_valid_frac < 1.0:
        print(f"resume bar  : a cell counts complete at {args.min_valid_frac:.0%} of "
              "its own n valid rows in ONE part file")
    print(f"actors      : {P.DISPLAY['gpt']} ({P.GPT_ID}), "
          f"{P.DISPLAY['claude']} ({P.CLAUDE_ID})")
    for actor in actors:
        for cond in PARTNER_CONDITIONS:
            print(f"  {P.DISPLAY[actor]:16} partner={cond:9} -> "
                  f"{partner_display(actor, cond)} "
                  f"({partner_model_id(actor, cond)})")

    print("\ngradient    : per-payoff n VARIES by stimulus (allocation is inverse to "
          "effect size)")
    print(f"  {'actor':<8}{'stimulus':<14}{'tier':<11}{'n/cell':>7}{'cells':>7}"
          f"{'trials':>8}   {'provisional':>11} {'confirmed':>10}  source")
    planned_by_stim = Counter()
    for c in cells:
        planned_by_stim[(c["actor"], c["sid"])] += n_for(c)
    for (actor, sid), trials in sorted(planned_by_stim.items()):
        ks = [k for k in plan_keys if k.startswith(f"{actor}|{sid}|")]
        m0 = meta[ks[0]]
        adv, src = resolve_advantage(actor, sid, m0["provisional"], confirmed)
        conf_txt = "" if m0["confirmed"] is None else f"{m0['confirmed']:+.3f}"
        if (actor, sid) in confirmed:
            conf_txt = f"{confirmed[(actor, sid)]:+.3f}"
        print(f"  {actor:<8}{sid:<14}{m0['tier']:<11}{m0['n_cell']:>7}{len(ks):>7}"
              f"{trials:>8}   {m0['provisional']:>+11.3f} {conf_txt:>10}  {src}")

    planned = sum(n_for(c) for c in cells)
    sizes = sorted({meta[k]["n_cell"] for k in plan_keys})
    print(f"\ncells       : {len(cells)}   per-payoff cell sizes: {sizes}   "
          f"planned trials: {planned}")
    # Identical hashes across (actor=claude, same) and (actor=gpt, different) are
    # CORRECT and are the symmetry made visible: the prompt is fixed by the NAME.
    for a in actors:
        for cond in PARTNER_CONDITIONS:
            hs = " ".join(f"S{v}={P.sha8(betting_prompt(v, partner_display(a, cond)))}"
                          for v in FP.SAFE_PAYOFFS)
            print(f"  sha8 {P.DISPLAY[a]:16} {cond:9} {hs}")

    if args.estimate:
        print()
        estimate(cells, n_for)
        return 0

    # ---- the confirmation gate REPLACES the superseded approved-pairs gate --------
    ok, why = confirmation_gate_ok(actors, gate, confirmed, cells, meta, ceiling,
                                   args.single_actor_gate)
    if not ok:
        if args.live:
            sys.exit("\nREFUSING TO RUN LIVE - the confirmation gate is not satisfied:\n"
                     + "\n".join(f"  - {w}" for w in why)
                     + "\n\nStage C may not start until design/confirmed_compatibility.csv "
                       "and design/CONFIRMATION_RESULTS.md exist AND every planned cell "
                       "carries the confirmation screen's advantage at the tier the "
                       "frozen allocation rule assigns to it (STUDY2_SPEC_FROZEN.md "
                       "sections 7.1 and 8; design/RE_FREEZE_RECORD.md). There is no "
                       "flag that skips this.")
        print("\nconfirmation gate NOT satisfied - NO LIVE RUN IS POSSIBLE. The dry run "
              "continues;\neach row carries the best advantage available and "
              "advantage_source records which\n(PROVISIONAL wherever the confirmation "
              "screen has not supplied a value):")
        for w in why:
            print(f"  - {w}")
    else:
        print(f"\nconfirmation gate satisfied: all {len(cells)} planned cell(s) carry "
              "the confirmation screen's own advantage,\n  at exactly the tier and n "
              "FROZEN_PARAMS.allocation_for() assigns to it.")

    # ---- full factorial randomisation, built over ALL cells so that a resumed run
    # ---- gets exactly the AB/BA sequence the unresumed run would have got.
    all_jobs = build_jobs(cells, n_for, SEED)
    for j in all_jobs:
        m = meta[cell_key(j)]
        adv, src = resolve_advantage(j["actor"], j["sid"], m["provisional"], confirmed)
        j["seed"] = SEED
        j["partner_name"] = partner_display(j["actor"], j["partner"])
        j["tier"] = m["tier"]
        j["advantage"] = f"{adv:+.3f}"
        j["advantage_source"] = src
        j["provisional"] = f"{m['provisional']:+.3f}"
        j["confirmed"] = ("" if confirmed.get((j["actor"], j["sid"])) is None
                          else f"{confirmed[(j['actor'], j['sid'])]:+.3f}")

    complete, partial = (({}, Counter()) if args.no_resume
                         else scan_progress(n_of_key, keys=plan_keys))
    if complete or partial:
        print(f"\nresume      : {len(complete)} cell(s) already complete, "
              f"{len(partial)} partial cell(s) will be re-run from scratch")
        for k, v in sorted(partial.items()):
            print(f"  PARTIAL {k}  ({v}/{n_of_key(k)} valid rows - discarded, not merged)")
    jobs = [j for j in all_jobs if cell_key(j) not in complete]
    print(f"to run      : {len(jobs)} trials"
          f"{'   [DRY RUN - zero network calls]' if dry_run else '   [LIVE]'}\n",
          flush=True)

    if dry_run:
        seen = set()
        for j in jobs:
            key = (j["actor"], j["partner"], j["safe"])
            if not args.print_all_prompts and key in seen:
                continue
            seen.add(key)
            pr = betting_prompt(j["safe"], j["partner_name"])
            print("-" * 78)
            print(f"actor={P.DISPLAY[j['actor']]}  partner={j['partner']} "
                  f"({j['partner_name']})  safe={j['safe']}  sha8={P.sha8(pr)}")
            print("-" * 78)
            print(pr)
            print()
        print(f"[{len(seen)} distinct prompt(s) printed; "
              f"{len(jobs)} trials will be written to the _DRY file]\n", flush=True)

    if not jobs:
        print("nothing to run - every cell is already complete.")
    else:
        sids = sorted({j["sid"] for j in jobs})
        run(jobs, P.load_images(sids), dry_run, args.workers, n_for)

    if not dry_run:
        complete2, partial2 = scan_progress(n_of_key, keys=plan_keys)
        m = write_merged(complete2)
        print(f"\ncomplete cells: {len(complete2)}/{len(cells)}"
              f"   still partial: {len(partial2)}")
        if m:
            print(f"merged file  : {m}   (one source file per cell; partial cells "
                  "excluded)")
        if len(complete2) < len(cells):
            print("RUN INCOMPLETE - re-run the same command to resume.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
