"""
Study 2 (revised) pre-run validation. Everything here runs with NO API calls and no cost.

  1  partner wording symmetry   the SAME and DIFFERENT prompts differ ONLY in the
                                model name; the emitted clause is recorded verbatim;
                                the decision layer is byte-identical to Study 1
  2  design table + randomisation  cells come from design/frozen_design_table.csv;
                                exact AB/BA balance in every cell at HETEROGENEOUS
                                per-cell n (8/16/30/40); deterministic under the seed
  3  confirmation gate          replaces the superseded approved-pairs gate: a live run
                                is refused unless confirmed_compatibility.csv exists AND
                                CONFIRMATION_RESULTS.md records a passing verdict
  4  output schema              strict superset of Study 1's Stage C columns, plus
                                tier / compatibility_advantage / advantage_source
  5  resume                     completed cells are skipped at THEIR OWN n; a partial
                                file is never merged with a good one
  6  dry run                    zero network calls, a _DRY file, one analysed row/trial
  7  config block               payoffs and every cell size come from FROZEN_PARAMS and
                                the frozen table, not from literals here
  8  information symmetry       no arm leaks information the other arm lacks

Run:  python3 test_study2.py
"""
import csv, io, contextlib, os, shutil, sys, tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import study2_betting as S
import psc_common as P
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "design"))
import FROZEN_PARAMS as FP

FAIL = []
NOTES = []


def check(cond, label, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {label}"
          + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAIL.append(label)


def note(text):
    """A documented divergence, not a failure. Collected and reprinted at the end."""
    print(f"  NOTE  {text}")
    NOTES.append(text)


def exits(fn, *a, **kw):
    """(did it sys.exit?, the message). sys.exit(msg) carries msg on the exception,
    so the message is read off SystemExit rather than off stderr."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            fn(*a, **kw)
    except SystemExit as e:
        msg = "" if e.code in (0, None) or isinstance(e.code, int) else str(e.code)
        return True, buf.getvalue() + msg
    return False, buf.getvalue()

# ============================================================ 1. symmetry =====
print("=== 1. partner wording symmetry ===")
GN, CN = P.DISPLAY["gpt"], P.DISPLAY["claude"]
norm = lambda s: s.replace(GN, "<M>").replace(CN, "<M>")

for actor in ("gpt", "claude"):
    same = S.betting_prompt(5, S.partner_display(actor, "same"))
    diff = S.betting_prompt(5, S.partner_display(actor, "different"))
    check(norm(same) == norm(diff),
          f"{P.DISPLAY[actor]}: SAME and DIFFERENT prompts are identical apart from "
          f"the model name")
    check(same != diff, f"{P.DISPLAY[actor]}: the two arms are not the same string")
    # exactly one substitution point: normalising must remove exactly one occurrence
    check(same.count(S.partner_display(actor, "same")) == 1,
          f"{P.DISPLAY[actor]}: SAME prompt names a model exactly once",
          str(same.count(S.partner_display(actor, "same"))))
    check(diff.count(S.partner_display(actor, "different")) == 1,
          f"{P.DISPLAY[actor]}: DIFFERENT prompt names a model exactly once")
    check(S.partner_display(actor, "different") not in same
          and S.partner_display(actor, "same") not in diff,
          f"{P.DISPLAY[actor]}: neither arm mentions the other arm's model")

# The prompt is a function of the NAME only, so the two arms cross exactly:
# what GPT sees under DIFFERENT is byte-identical to what Claude sees under SAME.
check(S.betting_prompt(5, S.partner_display("gpt", "different"))
      == S.betting_prompt(5, S.partner_display("claude", "same")),
      "gpt/DIFFERENT and claude/SAME are byte-identical (prompt depends on name only)")
check(S.betting_prompt(5, S.partner_display("claude", "different"))
      == S.betting_prompt(5, S.partner_display("gpt", "same")),
      "claude/DIFFERENT and gpt/SAME are byte-identical")

# named partners are correct and symmetric
check(S.partner_display("gpt", "same") == GN
      and S.partner_display("gpt", "different") == CN
      and S.partner_display("claude", "same") == CN
      and S.partner_display("claude", "different") == GN,
      "partner_display maps {actor, condition} -> the right model name")
check(S.partner_model_id("gpt", "same") == P.GPT_ID
      and S.partner_model_id("gpt", "different") == P.CLAUDE_ID
      and S.partner_model_id("claude", "same") == P.CLAUDE_ID
      and S.partner_model_id("claude", "different") == P.GPT_ID,
      "partner_model_id reads the model ids from psc_common (no new hardcoded ids)")
try:
    S.partner_display("gpt", "self")
    check(False, "an unknown partner condition is rejected")
except ValueError:
    check(True, "an unknown partner condition is rejected")

# the rest of the prompt is Study 1 verbatim
for v in (3, 5, 7, 9):
    pr = S.betting_prompt(v, GN)
    check(f"receive {v} points for certain" in pr, f"betting prompt states safe payoff {v}")
check("you receive 10 points" in S.betting_prompt(5, GN),
      "ATTEMPT still pays 10 on a match")
check(S._BASE_TAIL in S.betting_prompt(5, GN),
      "the non-partner part of BASE is Study 1 verbatim")
check("position CANNOT be used to coordinate" in S.betting_prompt(5, GN),
      "position-randomisation warning survives the rewrite")
tail1 = P.betting_prompt(5).split("Before playing,", 1)[1]
tail2 = S.betting_prompt(5, GN).split("Before playing,", 1)[1]
check(tail1 == tail2, "the decision layer is byte-identical to Study 1's Stage C")
check("another instance of you" not in S.betting_prompt(5, GN),
      "Study 1's asymmetric self-reference is gone (it has no symmetric counterpart)")
check(len({P.sha8(S.betting_prompt(v, GN)) for v in (3, 5, 7, 9)}) == 4,
      "each safe payoff yields a distinct prompt hash")
check(P.sha8(S.betting_prompt(5, GN)) != P.sha8(S.betting_prompt(5, CN)),
      "the two partner arms have different prompt hashes")
check(S.partner_sentence(GN) in S.betting_prompt(5, GN),
      "partner_condition_text (the recorded clause) appears verbatim in the prompt")

# ============================================ 2. design table + randomisation =
print("\n=== 2. frozen design table + randomisation ===")
tmp = tempfile.mkdtemp(prefix="study2_test_")
DCOLS = ["actor_model", "stimulus", "tier", "partner_condition", "partner_model_named",
         "safe_payoff", "match_payoff", "mismatch_payoff", "framing", "n_cell",
         "n_cell_ab", "n_cell_ba", "n_partner_total", "advantage_def",
         "provisional_advantage", "confirmed_advantage", "confirm_n", "gate_critical",
         "sensitivity_exclude"]


def design_row(actor, stim, tier, partner, safe, n_cell, prov=+0.100, conf=""):
    return dict(actor_model=actor, stimulus=stim, tier=tier, partner_condition=partner,
                partner_model_named=S.partner_display(actor, partner), safe_payoff=safe,
                match_payoff=FP.MATCH_PAYOFF, mismatch_payoff=FP.MISMATCH_PAYOFF,
                framing=FP.FRAMING, n_cell=n_cell, n_cell_ab=n_cell // 2,
                n_cell_ba=n_cell // 2, n_partner_total=n_cell * 4,
                advantage_def=FP.ADVANTAGE_DEF, provisional_advantage=f"{prov:+.3f}",
                confirmed_advantage=conf, confirm_n=180, gate_critical=True,
                sensitivity_exclude=False)


def write_design(name, rows, fields=DCOLS):
    p = os.path.join(tmp, name)
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, restval="")
        w.writeheader(); w.writerows(rows)
    return p


# a small synthetic gradient with DELIBERATELY HETEROGENEOUS per-cell n
SYNTH = []
for actor, stim, tier, n in (("gpt", "a_chev_ud", "large", 8),
                             ("gpt", "b_spiral_cw", "negative", 40),
                             ("claude", "proto", "zero_ceil", 16),
                             ("claude", "rot", "zero_floor", 30)):
    for partner in FP.PARTNER_CONDITIONS:
        for safe in FP.SAFE_PAYOFFS:
            SYNTH.append(design_row(actor, stim, tier, partner, safe, n))
synth_path = write_design("synth_design.csv", SYNTH)

rows = S.load_design_table(synth_path, strict_total=False)
cells, meta = S.build_cells(rows)
check(len(cells) == 4 * 2 * 4, "4 (actor x stimulus) x 2 partners x 4 payoffs = 32 cells",
      str(len(cells)))
check(len({S.cell_key(c) for c in cells}) == len(cells), "every cell key is unique")
check({meta[k]["n_cell"] for k in meta} == {8, 40, 16, 30},
      "per-cell n is heterogeneous and comes from the table", str(sorted(
          {meta[k]["n_cell"] for k in meta})))
per = Counter((c["actor"], c["sid"], c["partner"]) for c in cells)
check(set(per.values()) == {4}, "every (actor, stimulus, partner) spans the payoff grid",
      str(per))

n_for = S.n_for_cell(meta)
jobs = S.build_jobs(cells, n_for, S.SEED)
bal = Counter((S.cell_key(j), j["variant"]) for j in jobs)
check(all(v == meta[k]["n_cell"] // 2 for (k, _), v in bal.items()),
      "exact AB/BA balance in EVERY cell at heterogeneous n", str(sorted(set(bal.values()))))
check(len(bal) == 2 * len(cells), "every cell has both variants present")
check(len(jobs) == sum(meta[S.cell_key(c)]["n_cell"] for c in cells),
      "job count == sum of the per-cell n (not cells x a global n)", str(len(jobs)))
check(len({v for (k, v) in bal}) == 2 and len({meta[k]["n_cell"] for (k, _) in bal}) == 4,
      "the balance check really did span four different cell sizes")
jobs2 = S.build_jobs(cells, n_for, S.SEED)
check([j["run_id"] for j in jobs] == [j["run_id"] for j in jobs2],
      "job construction is deterministic under the recorded seed")
check([j["run_id"] for j in S.build_jobs(cells, n_for, S.SEED + 1)]
      != [j["run_id"] for j in jobs], "a different seed gives a different trial order")
check(len({j["run_id"] for j in jobs}) == len(jobs), "run_ids are unique")
check(any(jobs[i]["actor"] != jobs[i + 1]["actor"] for i in range(30)),
      "trial order is shuffled ACROSS cells, not blocked by cell")

# the generalisation to a per-cell n must not change Study 1's randomisation
p_cells = [{k: c[k] for k in ("actor", "sid", "safe")} for c in cells]
check([j["run_id"] for j in S.build_jobs(p_cells, lambda c: 30, S.SEED)]
      == [j["run_id"] for j in P.build_jobs(p_cells, 30, S.SEED)],
      "build_jobs is byte-identical to psc_common.build_jobs at uniform n")
ok, _ = exits(S.build_jobs, cells, lambda c: 7, S.SEED)
check(ok, "an odd n is rejected")

# ---- the REAL frozen table -----------------------------------------------------
real = S.load_design_table()
rcells, rmeta = S.build_cells(real)
check(len(real) == 128, "the frozen design table holds 128 cells", str(len(real)))
check(len(rcells) == 128, "every table row becomes exactly one cell", str(len(rcells)))
check(sum(m["n_cell"] for m in rmeta.values()) == FP.stage_c_calls(),
      f"planned trials == FROZEN_PARAMS.stage_c_calls() == {FP.stage_c_calls()}",
      str(sum(m["n_cell"] for m in rmeta.values())))
check(sorted({m["n_cell"] for m in rmeta.values()}) == [8, 16, 30, 40],
      "per-payoff cell sizes are the frozen {8, 16, 30, 40}",
      str(sorted({m["n_cell"] for m in rmeta.values()})))
check(all(m["n_cell"] % 2 == 0 for m in rmeta.values()),
      "every frozen cell size is even, so AB/BA is exact everywhere")
rjobs = S.build_jobs(rcells, S.n_for_cell(rmeta), S.SEED)
check(len(rjobs) == FP.stage_c_calls(),
      f"the real design produces {FP.stage_c_calls():,} trials", str(len(rjobs)))
rbal = Counter((S.cell_key(j), j["variant"]) for j in rjobs)
check(all(v == rmeta[k]["n_cell"] // 2 for (k, _), v in rbal.items()),
      "AB/BA is exactly n/2 in all 128 real cells")
check(len(rbal) == 256, "all 128 cells carry both variants", str(len(rbal)))
tiers = {(r["actor_model"], r["stimulus"]): r["tier"] for r in real}
check(all(tiers[(a, s)] == t for a, tl in FP.ACTIVE_GRADIENT.items()
          for s, _p, t, _n in tl for (a2, s2) in [(a, s)] if (a2, s2) in tiers),
      "tier labels in the table match FROZEN_PARAMS.ACTIVE_GRADIENT")
check(all(int(r["n_cell"]) == FP.per_payoff_n(n)
          for r in real for a, tl in FP.ACTIVE_GRADIENT.items() for s, _p, _t, n in tl
          if r["actor_model"] == a and r["stimulus"] == s),
      "every n_cell equals FROZEN_PARAMS.per_payoff_n(N_PARTNER)")
check(FP.ACTIVE_GRADIENT is FP.CONFIRMED_GRADIENT,
      "ACTIVE_GRADIENT is the CONFIRMED table, not the superseded provisional one")
check(all(r["confirmed_advantage"] is not None for r in real),
      "every frozen row carries a CONFIRMED advantage (re-freeze, 2026-08-22)",
      str(sum(r["confirmed_advantage"] is None for r in real)))
check(all(r.get("advantage_source") == "confirmed" for r in real),
      "every frozen row records advantage_source=confirmed")
_ceil = S.load_confirmed_ceilings()
_conf, _ = S.load_confirmed_advantages()
check(bool(_conf) and not S.allocation_mismatches(rcells, rmeta, _conf, _ceil),
      "every frozen cell sits at the tier/n the allocation rule assigns to its "
      "CONFIRMED advantage",
      str(S.allocation_mismatches(rcells, rmeta, _conf, _ceil)[:3]))
check(not S.confirmed_column_drift(rcells, rmeta, _conf),
      "the table's confirmed_advantage column equals confirmed_compatibility.csv",
      str(S.confirmed_column_drift(rcells, rmeta, _conf)[:3]))

# ---- the loader refuses malformed tables ---------------------------------------
ok, out = exits(S.load_design_table, os.path.join(tmp, "nope.csv"))
check(ok and "no frozen design table" in out,
      "a missing design table refuses to run (does not invent cells)")
bad = write_design("bad.csv", [dict(whatever="x")], fields=["whatever"])
ok, out = exits(S.load_design_table, bad)
check(ok and "missing required column" in out,
      "an unrecognised schema refuses to run rather than guessing")
odd = write_design("odd.csv", [design_row("gpt", "proto", "zero_ceil", "same", 3, 7)])
ok, out = exits(S.load_design_table, odd, False)
check(ok and "EVEN" in out, "an odd n_cell is refused (AB/BA could not be exact)")
crossed = [design_row("gpt", "proto", "zero_ceil", "same", 3, 8)]
crossed[0]["partner_model_named"] = P.DISPLAY["claude"]
xp = write_design("crossed.csv", crossed)
ok, out = exits(S.load_design_table, xp, False)
check(ok and "crossed-up condition label" in out,
      "a crossed-up partner_model_named is caught at load time, not trusted")
dup = write_design("dup.csv", [design_row("gpt", "proto", "zero_ceil", "same", 3, 8)] * 2)
ok, out = exits(S.load_design_table, dup, False)
check(ok and "duplicate design cell" in out, "a duplicated design cell is refused")
badtier = [design_row("gpt", "proto", "zero_ceil", "same", 3, 8)]
badtier[0]["tier"] = "enormous"
ok, out = exits(S.load_design_table, write_design("bt.csv", badtier), False)
check(ok and "tier" in out,
      "a tier outside FROZEN_PARAMS.ACTIVE_GRADIENT is refused")
ok, out = exits(S.load_design_table, synth_path, True)
check(ok and "frozen allocation" in out,
      "a table whose total != FROZEN_PARAMS.stage_c_calls() is refused under strict_total")

# ====================================================== 3. confirmation gate ==
# This REPLACES the superseded approved-pairs gate. Every path below works on files
# in a temp directory, and the live-refusal check additionally stubs S.run, so no
# branch of this section can reach a provider even if the sibling agent's real
# confirmation files land while the test is running.
print("\n=== 3. confirmation gate (replaces the approved-pairs gate) ===")
GDIR = os.path.join(tmp, "design")
os.makedirs(GDIR, exist_ok=True)
MD = os.path.join(GDIR, "CONFIRMATION_RESULTS.md")
CONF = os.path.join(GDIR, "confirmed_compatibility.csv")
GCSV = os.path.join(GDIR, "confirmation_gate.csv")

g = S.read_gate(md=os.path.join(GDIR, "absent.md"), gate_csv=os.path.join(GDIR, "a.csv"))
check(g["verdict"] == "missing", "a missing CONFIRMATION_RESULTS.md is 'missing'",
      g["verdict"])
open(MD, "w").write("# results\n\n**Stage C MAY PROCEED as frozen.**\n")
check(S.read_gate(md=MD, gate_csv=GCSV)["verdict"] == "pass",
      "the sibling's PASS headline is read as a passing verdict")
open(MD, "w").write("# results\n\n**Stage C MUST NOT PROCEED as frozen - the gate "
                    "FAILS.**\n")
check(S.read_gate(md=MD, gate_csv=GCSV)["verdict"] == "fail",
      "the sibling's FAIL headline is read as a failing verdict")
open(MD, "w").write("# results\n\nGATE VERDICT: PASS -- sign and order replicate\n")
check(S.read_gate(md=MD, gate_csv=GCSV)["verdict"] == "pass",
      "the console-style 'GATE VERDICT: PASS' line is also accepted")
open(MD, "w").write("# results\n\nnothing decidable here\n")
check(S.read_gate(md=MD, gate_csv=GCSV)["verdict"] == "unknown",
      "a report with no recognised verdict line is 'unknown', never assumed to pass")

# per-actor verdicts, for the section 7.1 single-actor branch
with open(GCSV, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["actor", "stimulus", "tier", "pass_sign", "note"])
    w.writeheader()
    w.writerows([dict(actor="gpt", stimulus="a_chev_ud", tier="large", pass_sign="True",
                      note=""),
                 dict(actor="gpt", stimulus="b_spiral_cw", tier="negative",
                      pass_sign="True", note=""),
                 dict(actor="claude", stimulus="a_chev_ud", tier="large",
                      pass_sign="True", note=""),
                 dict(actor="claude", stimulus="c_open_cplx", tier="negative",
                      pass_sign="False", note="sign flipped")])
per = S.read_gate(md=MD, gate_csv=GCSV)["per_actor"]
check(per == {"gpt": True, "claude": False},
      "per-actor verdicts are ANDed over that actor's cells", str(per))

# confirmed advantages: wide, long, unreadable, and the design-table fallback
with open(CONF, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["stimulus", "GG", "CC", "GC", "advantage_gpt",
                                       "advantage_claude"])
    w.writeheader()
    w.writerow(dict(stimulus="a_chev_ud", GG=".9", CC=".9", GC=".3",
                    advantage_gpt="0.612", advantage_claude="0.655"))
    w.writerow(dict(stimulus="b_spiral_cw", GG=".4", CC=".7", GC=".5",
                    advantage_gpt="-0.140", advantage_claude="0.204"))
m, src = S.load_confirmed_advantages(CONF)
check(m.get(("gpt", "a_chev_ud")) == 0.612 and m.get(("claude", "b_spiral_cw")) == 0.204,
      "the sibling's WIDE confirmed_compatibility.csv is read", str(sorted(m)[:2]))
check("wide" in src, "the source of the confirmed values is reported", src)
LONG = os.path.join(GDIR, "long.csv")
with open(LONG, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["actor", "stimulus", "confirmed_advantage"])
    w.writeheader()
    w.writerow(dict(actor="gpt", stimulus="rot", confirmed_advantage="0.041"))
m2, src2 = S.load_confirmed_advantages(LONG)
check(m2 == {("gpt", "rot"): 0.041}, "a LONG (actor, stimulus, advantage) form is "
      "accepted too", str(m2))
JUNK = os.path.join(GDIR, "junk.csv")
open(JUNK, "w").write("a,b\n1,2\n")
m3, src3 = S.load_confirmed_advantages(JUNK)
check(m3 == {} and "UNREADABLE" in src3,
      "an unrecognised confirmation format is reported, never guessed at", src3)
fallback_rows = [dict(actor_model="gpt", stimulus="proto",
                      confirmed_advantage=0.005, provisional_advantage=0.0)]
m4, src4 = S.load_confirmed_advantages(os.path.join(GDIR, "absent.csv"),
                                       design_rows=fallback_rows)
check(m4 == {("gpt", "proto"): 0.005} and "design_table" in src4.replace(" ", "_"),
      "the design table's own confirmed_advantage column is the documented fallback",
      f"{m4} / {src4}")

# the gate decision itself -- RE-FROZEN 2026-08-22 (design/RE_FREEZE_RECORD.md).
# The prose verdict in CONFIRMATION_RESULTS.md no longer decides; five machine-checked
# requirements do, and NO flag skips any of them.
gcells = [dict(actor="gpt", sid="a_chev_ud", partner="same", safe=3),
          dict(actor="gpt", sid="b_spiral_cw", partner="same", safe=3)]
conf_ok = {("gpt", "a_chev_ud"): 0.6, ("gpt", "b_spiral_cw"): -0.14}
gceil = {"a_chev_ud": False, "b_spiral_cw": False}


def gmeta(conf, tiers=None):
    """meta for gcells, tiered by the frozen rule unless a tier is forced."""
    out = {}
    for c in gcells:
        t, npart = FP.allocation_for(conf[(c["actor"], c["sid"])], False)
        if tiers and c["sid"] in tiers:
            t, npart = tiers[c["sid"]]
        out[S.cell_key(c)] = dict(tier=t, n_cell=FP.per_payoff_n(npart),
                                  provisional=0.0,
                                  confirmed=conf[(c["actor"], c["sid"])],
                                  n_partner_total=npart)
    return out


PASS = dict(verdict="pass", detail="", per_actor={}, md_exists=True)
FAILG = dict(verdict="fail", detail="gate FAILS", per_actor={"gpt": True},
             md_exists=True)
MISS = dict(verdict="missing", detail="absent", per_actor={}, md_exists=False)

ok, why = S.confirmation_gate_ok(["gpt"], PASS, conf_ok, gcells, gmeta(conf_ok), gceil)
check(ok, "a design consistent with the confirmed advantages opens the gate", str(why))
ok, why = S.confirmation_gate_ok(["gpt"], MISS, conf_ok, gcells, gmeta(conf_ok), gceil)
check(not ok and any("does not exist" in w for w in why),
      "a missing CONFIRMATION_RESULTS.md keeps the gate shut - the confirmation "
      "screen must demonstrably have run", str(why))
ok, why = S.confirmation_gate_ok(["gpt"], PASS, {}, gcells, {}, gceil)
check(not ok and any("no confirmed advantages" in w for w in why),
      "no confirmed_compatibility.csv keeps it shut", str(why))
ok, why = S.confirmation_gate_ok(["gpt"], PASS, {("gpt", "a_chev_ud"): 0.6}, gcells,
                                 gmeta(conf_ok), gceil)
check(not ok and any("no confirmed advantage" in w for w in why),
      "a cell with no confirmed advantage keeps the gate shut (empty column is a "
      "configuration error, not a fallback)", str(why))

# --- the substantive replacement for the prose verdict -----------------------
ok, why = S.confirmation_gate_ok(["gpt"], PASS, conf_ok, gcells,
                                 gmeta(conf_ok, {"b_spiral_cw": ("small", 120)}), gceil)
check(not ok and any("allocation rule does not assign" in w for w in why),
      "a cell recorded at a tier the allocation rule does not assign to its CONFIRMED "
      "advantage is REFUSED", str(why))
stale = gmeta(conf_ok)
stale[S.cell_key(gcells[0])]["confirmed"] = 0.65      # table edited away from the CSV
ok, why = S.confirmation_gate_ok(["gpt"], PASS, conf_ok, gcells, stale, gceil)
check(not ok and any("disagrees with" in w for w in why),
      "a design table whose confirmed_advantage disagrees with the confirmation "
      "screen is REFUSED", str(why))
ok, why = S.confirmation_gate_ok(["gpt"], PASS, conf_ok, gcells, None, gceil)
check(not ok and any("could not run" in w for w in why),
      "with no per-cell metadata the consistency check cannot run, so the gate "
      "refuses rather than assuming", str(why))
# ceiling status changes which band a zero-advantage cell belongs in, and is read
# off the confirmation counts rather than asserted by name
check(FP.allocation_for(0.0, True) == ("zero_ceil", 64)
      and FP.allocation_for(0.0, False) == ("zero_floor", 120),
      "a zero advantage lands in the ceiling or the floor band by its own-copy rate")
check(FP.is_ceiling(1.0, 1.0) and not FP.is_ceiling(1.0, 0.5),
      "is_ceiling requires BOTH own-copy rates pinned at 1.000")
check(FP.allocation_for(0.25) == ("medium", 64) and FP.allocation_for(0.2501)[0] == "large",
      "the recorded boundary convention holds: |adv| <= 0.25 is medium")

# --- the prose verdict is now advisory, and there is NO bypass flag ----------
ok, why = S.confirmation_gate_ok(["gpt"], FAILG, conf_ok, gcells, gmeta(conf_ok), gceil)
check(ok, "the superseded FAIL verdict no longer blocks a design that IS consistent "
      "with the confirmed data (re-freeze; the verdict is provenance only)", str(why))
bad_meta = gmeta(conf_ok, {"b_spiral_cw": ("small", 120)})
ok_flag, why_flag = S.confirmation_gate_ok(["gpt"], PASS, conf_ok, gcells, bad_meta,
                                           gceil, single_actor_ok=True)
check(not ok_flag,
      "--single-actor-gate is INERT: it does not open the gate on an inconsistent "
      "design", str(why_flag))
ok_flag2, _ = S.confirmation_gate_ok(["gpt"], MISS, conf_ok, gcells, gmeta(conf_ok),
                                     gceil, single_actor_ok=True)
check(not ok_flag2, "--single-actor-gate does not substitute for a missing "
      "confirmation report either")

# ---- and the whole thing end to end: --live is refused, with S.run stubbed so the
# ---- test cannot reach a provider under any circumstances --------------------
_real_run, _real_conf, _real_md, _real_gcsv = (S.run, S.CONFIRMED_CSV,
                                               S.CONFIRMATION_MD,
                                               S.CONFIRMATION_GATE_CSV)


def _forbidden(*a, **kw):
    raise AssertionError("study2_betting.run() was reached during a test")


S.run = _forbidden
S.CONFIRMED_CSV = os.path.join(tmp, "no_confirmed.csv")
S.CONFIRMATION_MD = os.path.join(tmp, "no_report.md")
S.CONFIRMATION_GATE_CSV = os.path.join(tmp, "no_gate.csv")
try:
    ok, out = exits(S.main, ["--live"])
    check(ok and "REFUSING TO RUN LIVE" in out,
          "main --live is refused while the confirmation screen has not reported",
          out[-200:])
    check("confirmed_compatibility.csv" in out and "CONFIRMATION_RESULTS.md" in out,
          "the refusal names both files the gate requires")
    ok, out = exits(S.main, ["--live", "--single-actor-gate"])
    check(ok and "requires --models" in out,
          "--single-actor-gate without --models is refused")
    ok, out = exits(S.main, ["--live", "--dry-n", "4"])
    check(ok and "frozen per-cell allocation" in out,
          "--dry-n cannot be combined with --live")
    ok, out = exits(S.main, ["--live", "--dry-run"])
    check(ok, "--live together with --dry-run is refused")
    # a DRY run, by contrast, proceeds on the provisional values and says so
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            S.main(["--models", "gpt", "--stimuli", "proto", "--dry-n", "2"])
        except AssertionError:
            pass                      # S.run is stubbed; the header is what matters
    o = buf.getvalue()
    check("confirmation gate NOT satisfied" in o and "PROVISIONAL" in o,
          "a dry run continues on the provisional advantages and says so")
finally:
    S.run, S.CONFIRMED_CSV = _real_run, _real_conf
    S.CONFIRMATION_MD, S.CONFIRMATION_GATE_CSV = _real_md, _real_gcsv

# the sibling's real confirmation files, if they have landed, must parse
if os.path.exists(S.CONFIRMED_CSV):
    m, src = S.load_confirmed_advantages()
    check(bool(m), "the sibling's real confirmed_compatibility.csv parses", src)
    real_gate = S.read_gate()
    check(real_gate["verdict"] in ("pass", "fail"),
          "the sibling's real CONFIRMATION_RESULTS.md records a decidable verdict",
          real_gate["detail"])
else:
    print("  (skip) the sibling's confirmation files do not exist yet - the gate is "
          "shut, which is the correct state")

# ======================================================== 4. output schema ====
print("\n=== 4. output schema ===")
check(set(P.COLS).issubset(set(S.COLS)),
      "Study 2 columns are a strict SUPERSET of Study 1's Stage C schema",
      str(sorted(set(P.COLS) - set(S.COLS))))
check(S.COLS[:len(P.COLS)] == list(P.COLS),
      "Study 1's columns keep their original order and position")
for extra in ("partner_condition", "partner_model_named", "tier",
              "compatibility_advantage", "advantage_source"):
    check(extra in S.COLS, f"required new column {extra} is present")
check("partner_condition_text" in S.COLS,
      "the partner wording is emitted verbatim into every row")
check("provisional_advantage" in S.COLS and "confirmed_advantage" in S.COLS,
      "both advantage values are carried for provenance, not just the resolved one")
check("pair_id" not in S.COLS and "stimulus_level" not in S.COLS,
      "the superseded pair columns are gone (spec section 14.1)")
check(len(S.COLS) == len(set(S.COLS)), "no duplicated column names")

# --- integration with the sibling analysis agent's frozen schema ---
try:
    import study2_schema as SCH
except ImportError:
    SCH = None
    print("  (skip) study2_schema.py (sibling analysis) not present yet")
if SCH is not None:
    check(set(SCH.REQUIRED).issubset(set(S.COLS)),
          "every REQUIRED analysis column is emitted",
          str(sorted(set(SCH.REQUIRED) - set(S.COLS))))
    check(list(SCH.PSC_COLS) == list(P.COLS),
          "the sibling's copy of Study 1's columns matches psc_common.COLS")
    check(tuple(SCH.PARTNERS) == S.PARTNER_CONDITIONS,
          "partner_condition values agree with the analysis", str(SCH.PARTNERS))
    check(SCH.DISPLAY == {k: P.DISPLAY[k] for k in SCH.DISPLAY},
          "display names agree with psc_common", str(SCH.DISPLAY))
    check(SCH.SAFE_VALUES_DEFAULT == S.SAFE_VALUES,
          "the default payoff grid agrees with the analysis")
    msg = SCH.assert_matches_psc_common()
    check("verified identical" in msg, "sibling schema self-check passes", msg)
    dose = set(getattr(SCH, "DOSE_COLS", []))
    check(dose.issubset(set(S.COLS)),
          "the runner emits the analysis' dose-response columns "
          "(compatibility_advantage, tier)", str(sorted(dose - set(S.COLS))))
    # KNOWN, DOCUMENTED divergences - recorded here and in RUNNER_NOTES.md rather
    # than silently reconciled in either direction.
    gone = [c for c in SCH.COLS if c not in S.COLS]
    if gone:
        note(f"study2_schema.COLS still lists {gone} from the superseded pair design; "
             "the runner no longer emits them (spec 14.1). Recorded in RUNNER_NOTES.md.")
    if "advantage_source" not in set(SCH.COLS) | dose:
        note("the runner emits advantage_source (confirmed vs provisional), which "
             "study2_schema does not yet declare. Recorded in RUNNER_NOTES.md.")


# ============================================================== 5. resume =====
print("\n=== 5. resume at heterogeneous cell sizes ===")
DATA = os.path.join(tmp, "data")
os.makedirs(DATA, exist_ok=True)
N_OF = {"gpt|a_chev_ud|same|3": 8, "gpt|b_spiral_cw|same|3": 40,
        "gpt|b_spiral_cw|different|3": 40, "claude|rot|same|9": 30}
n_of = lambda k: N_OF[k]


def fake_rows(key, n, included=True):
    a, sid, part, safe = key.split("|")
    return [dict.fromkeys(S.COLS, "") | dict(
        actor_model=a, stimulus=sid, partner_condition=part, safe_payoff=safe,
        run_id=f"{key}__{i:03d}", valid_response="True",
        included_in_analysis="True" if included else "False", cell_key=key)
        for i in range(n)]


def write_part(name, rows):
    p = os.path.join(DATA, name)
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=S.COLS, restval="")
        w.writeheader(); w.writerows(rows)
    os.utime(p, None)
    return p


K_SMALL = "gpt|a_chev_ud|same|3"        # n = 8
K_BIG = "gpt|b_spiral_cw|same|3"        # n = 40
K_PART = "gpt|b_spiral_cw|different|3"  # n = 40

# 8 rows completes the SMALL cell and must NOT complete the BIG one
f1 = write_part("study2C_20260822_100000.csv",
                fake_rows(K_SMALL, 8) + fake_rows(K_BIG, 8) + fake_rows(K_PART, 11))
comp, part = S.scan_progress(n_of, DATA)
check(list(comp) == [K_SMALL], "8 rows completes an n=8 cell", str(list(comp)))
check(part.get(K_BIG) == 8,
      "the same 8 rows leave an n=40 cell PARTIAL - completion is per-cell, not global",
      str(dict(part)))
check(part.get(K_PART) == 11, "a second partial cell is tracked separately")

# two half-finished files must NOT add up to a finished cell
import time as _t
_t.sleep(0.01)
f2 = write_part("study2C_20260822_110000.csv", fake_rows(K_PART, 29))
comp, part = S.scan_progress(n_of, DATA)
check(K_PART not in comp,
      "11 rows in one file + 29 in another do NOT count as a complete cell of 40",
      str(list(comp)))
check(part[K_PART] == 29, "the partial count is per-file, never summed", str(dict(part)))

# invalid rows never count toward completion
_t.sleep(0.01)
K_INVALID = "claude|rot|same|9"
write_part("study2C_20260822_120000.csv", fake_rows(K_INVALID, 30, included=False))
comp, part = S.scan_progress(n_of, DATA)
check(K_INVALID not in comp, "rows with included_in_analysis=False do not complete a cell")

# a later file that DOES complete the partial cell supersedes the earlier partial
_t.sleep(0.01)
f4 = write_part("study2C_20260822_130000.csv", fake_rows(K_PART, 40))
comp, part = S.scan_progress(n_of, DATA)
check(comp.get(K_PART) == f4, "the newest file that completed a cell owns that cell")
check(K_PART not in part, "a completed cell is no longer reported as partial")

merged = S.write_merged(comp, DATA, S.COLS)
check(merged is not None and "MERGED" in os.path.basename(merged),
      "a merged file is written when more than one part file contributes")
mrows = list(csv.DictReader(open(merged)))
mcount = Counter(r["cell_key"] for r in mrows)
check(mcount[K_PART] == 40,
      "the merged file takes the completed cell from ONE file only (40 rows, not 80)",
      str(mcount[K_PART]))
check(mcount[K_SMALL] == 8, "the n=8 cell is carried over intact at ITS size",
      str(mcount[K_SMALL]))
check(K_INVALID not in mcount,
      "rows from a cell that no single file completed are NOT merged in")
check(set(csv.DictReader(open(merged)).fieldnames) == set(S.COLS),
      "the merged file keeps the full schema")

# _DRY files are never treated as real progress
_t.sleep(0.01)
write_part("study2C_20260822_140000_DRY.csv", fake_rows("gpt|b_spiral_cw|same|3", 40))
comp2, _ = S.scan_progress(n_of, DATA)
check(comp2.get(K_BIG) is None, "a _DRY file is never counted as progress")
check(all("_DRY" not in f and "MERGED" not in f for f in S.part_files(DATA)),
      "part_files() excludes _DRY and MERGED files")

# a part file from a run with a different cell set is ignored entirely
comp3, part3 = S.scan_progress(n_of, DATA, keys={K_SMALL})
check(set(comp3) == {K_SMALL} and not part3,
      "scan restricted to THIS run's cells ignores foreign part-file cells",
      f"{list(comp3)} / {dict(part3)}")

# --min-valid-frac relaxes the bar per cell, not globally
n_frac = lambda k: max(2, -(-N_OF[k] * 95 // 100))
write_part("study2C_20260822_150000.csv", fake_rows(K_BIG, 38))
comp4, part4 = S.scan_progress(n_frac, DATA)
check(K_BIG in comp4, "38/40 valid rows completes an n=40 cell at --min-valid-frac 0.95",
      str(list(comp4)))
check(S.scan_progress(n_of, DATA)[0].get(K_BIG) is None,
      "the same 38 rows do NOT complete it at the default strict bar")

# resume actually removes the completed cells from the job list, at the right size
rjobs_all = S.build_jobs(cells, S.n_for_cell(meta), S.SEED)
k0 = S.cell_key(cells[0])
remaining = [j for j in rjobs_all if S.cell_key(j) != k0]
check(len(remaining) == len(rjobs_all) - meta[k0]["n_cell"],
      "a completed cell drops exactly ITS OWN n jobs", str(meta[k0]["n_cell"]))
by_id = {j["run_id"]: j["variant"] for j in rjobs_all}
check(all(by_id[j["run_id"]] == j["variant"] for j in remaining),
      "resuming does not change the AB/BA assignment of the remaining trials")


# ============================================================= 6. dry run =====
print("\n=== 6. dry run ===")
# --no-resume is REQUIRED here: once real Stage C data exists in P.DATA the resume
# scan would find these cells already complete, run zero jobs, write no _DRY file,
# and the assertions below would silently read a stale file from an earlier run.
# The dry-run section must not depend on the data directory being empty.
_before = {f for f in os.listdir(P.DATA) if f.startswith("study2C_") and "_DRY" in f
           and f.endswith(".csv")}
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = S.main(["--models", "gpt", "--stimuli", "proto", "--dry-n", "4",
                 "--workers", "4", "--no-resume"])
out = buf.getvalue()
check(rc == 0, "the dry run exits 0")
check("[DRY RUN - zero network calls]" in out, "dry run is the DEFAULT (no --live given)")
dry = sorted({f for f in os.listdir(P.DATA) if f.startswith("study2C_") and "_DRY" in f
              and f.endswith(".csv")} - _before)
check(bool(dry), "a _DRY output file is written by THIS invocation (not a stale one)")
dpath = os.path.join(P.DATA, dry[-1])
drows = list(csv.DictReader(open(dpath)))
inc = [r for r in drows if r["included_in_analysis"] == "True"]
sup = [r for r in drows if r["superseded_by_retry"] == "True"]
check(list(csv.DictReader(open(dpath)).fieldnames) == S.COLS,
      "the _DRY file carries the full superset schema")
check(len(drows) == 2 * 4 * 4 + len(sup),
      "one row per planned trial (2 partners x 4 payoffs x 4) plus superseded retries",
      f"{len(drows)} rows, {len(sup)} superseded")
check(all(Counter(r["run_id"] for r in inc)[k] == 1
          for k in {r["run_id"] for r in inc}),
      "exactly one included_in_analysis row per run_id")
check(all(r["partner_condition"] in S.PARTNER_CONDITIONS for r in drows),
      "every row records a partner condition")
check({r["partner_condition"] for r in drows} == set(S.PARTNER_CONDITIONS),
      "both partner arms are present in the output")
check(all(r["tier"] == "zero_ceil" for r in drows),
      "every row carries the frozen tier for its stimulus",
      str({r["tier"] for r in drows}))
check({r["advantage_source"] for r in drows} <= {"confirmed", "provisional"},
      "advantage_source is exactly one of confirmed / provisional",
      str({r["advantage_source"] for r in drows}))
for r in drows[:1]:
    src = r["advantage_source"]
    want = r["confirmed_advantage"] if src == "confirmed" else r["provisional_advantage"]
    check(r["compatibility_advantage"] == want and want != "",
          "compatibility_advantage is the value advantage_source names",
          f"{src}: {r['compatibility_advantage']} vs {want}")
check(all(r["provisional_advantage"] not in ("", None) for r in drows),
      "the provisional value is carried on every row for provenance")
check(all(r["n_per_cell"] == "4" for r in drows),
      "n_per_cell records the cell size actually used", str({r["n_per_cell"] for r in drows}))
check(all(r["cell_key"].count("|") == 3 for r in drows),
      "cell_key is actor|stimulus|partner|safe (no pair component)",
      str(drows[0]["cell_key"]))
for r in drows:
    want = S.partner_sentence(S.partner_display(r["actor_model"], r["partner_condition"]))
    if r["partner_condition_text"] != want:
        check(False, "partner_condition_text matches the wording actually used",
              r["partner_condition_text"])
        break
else:
    check(True, "partner_condition_text matches the wording actually used")
check(len({r["partner_condition_text"] for r in drows}) == 2,
      "the two arms emit exactly two distinct clauses")
a, b = sorted({r["partner_condition_text"] for r in drows})
check(norm(a) == norm(b),
      "the two emitted clauses differ ONLY by the model name (post-hoc diffable)")
check(all(r["prompt_sha8"] for r in drows), "every row records its prompt_sha8")
check(len({r["prompt_sha8"] for r in drows}) == 8,
      "4 payoffs x 2 partner arms -> exactly 8 prompt hashes",
      str(len({r["prompt_sha8"] for r in drows})))
check(all(r["seed"] == str(S.SEED) for r in drows), "the seed is recorded on every row")
check(all(r["study"] == "study2" for r in drows), "rows are tagged study2")
vb = Counter((r["cell_key"], r["variant"]) for r in drows
             if r["superseded_by_retry"] == "False")
check(set(vb.values()) == {2}, "AB/BA balance survives into the written rows", str(vb))
os.remove(dpath); os.remove(dpath.replace(".csv", ".jsonl"))


# =========================================================== 7. config block ==
print("\n=== 7. config block ===")
check(S.SAFE_VALUES == list(FP.SAFE_PAYOFFS),
      "the payoff grid comes from FROZEN_PARAMS", str(S.SAFE_VALUES))
check(S.PARTNER_CONDITIONS == tuple(FP.PARTNER_CONDITIONS),
      "the partner conditions come from FROZEN_PARAMS")
check(not hasattr(S, "N_PER_CELL"),
      "there is no global n default left - every n comes from the design table")
check(not hasattr(S, "load_power_config") and not hasattr(S, "PAIRS_CSV"),
      "the superseded power-config and pairs-table hooks are gone")
check(S.DESIGN_TABLE.endswith(os.path.join("design", "frozen_design_table.csv")),
      "the runner reads the frozen design table", S.DESIGN_TABLE)
check(S.PRICING["claude"]["in_per_mtok"] == 5.00
      and S.PRICING["claude"]["out_per_mtok"] == 25.00,
      "Claude Opus 5 pricing is $5/$25 per MTok (claude-api skill)")
check(S.PRICING["gpt"]["verified"] is False,
      "GPT-5.5 pricing is flagged UNVERIFIED rather than asserted")
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    calls, lo, hi = S.estimate(rcells, S.n_for_cell(rmeta))
want = sum(int(round(sum(rmeta[S.cell_key(c)]["n_cell"] for c in rcells
                         if c["actor"] == m) * S.RETRY_ALLOWANCE))
           for m in ("gpt", "claude"))
check(calls == want,
      "the estimator sums the PER-CELL n (not cells x a global n) x retry allowance",
      f"{calls} vs {want}")
check(hi > lo > 0, "the estimator reports a positive cost range")
check("UNVERIFIED" in buf.getvalue(), "the estimate flags the unverified price")

# ==================================================== 8. information symmetry =
print("\n=== 8. information symmetry ===")
for label, txt in (("same/gpt", S.betting_prompt(5, GN)),
                   ("different/gpt", S.betting_prompt(5, CN))):
    leaks = [w for w in ("match rate", "empirical", "previously", "form consistency",
                         "we found", "data show", "study 1", "prior")
             if w in txt.lower()]
    check(not leaks, f"{label} prompt leaks no empirical results", str(leaks))
check("high" not in S.betting_prompt(5, GN).lower().split("cannot")[0].split()
      and "own-copy" not in S.betting_prompt(5, GN).lower(),
      "the prompt never reveals which member of the pair the stimulus is")
check(S.betting_prompt(5, GN).count("10 points") == 1
      and S.betting_prompt(5, CN).count("10 points") == 1,
      "both arms state the same ATTEMPT payoff exactly once")

shutil.rmtree(tmp, ignore_errors=True)

print("\n" + "=" * 62)
if NOTES:
    print(f"{len(NOTES)} DOCUMENTED DIVERGENCE(S) - recorded, not failures:")
    for n in NOTES:
        print("  -", n)
if FAIL:
    print(f"{len(FAIL)} CHECK(S) FAILED:")
    for f in FAIL:
        print("  -", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
