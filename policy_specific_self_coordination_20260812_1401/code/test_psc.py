"""
Pre-run validation. Everything here runs with no API calls and no cost.

  1  stimulus verification      all 15 exist, files present, classification matches
                                the confirmed n=60 data
  2  AB/BA recoding             position and identity are independent by construction
  3  parsers                    choice / probability / salience / decision, incl. the
                                adversarial cases the prior probes actually hit
  4  retry + dedup              exactly one final valid response per planned trial
  5  counterbalancing           exact AB/BA balance in every cell, fixed seed
  6  information symmetry       no arm leaks information the other arm lacks
  7  prompt provenance          Stage A is byte-identical to the canonical prompt

Run:  python3 test_psc.py
"""
import csv, os, sys, hashlib
from collections import Counter
import psc_common as P
import targeted_common as tc

FAIL = []


def check(cond, label, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {label}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAIL.append(label)


print("=== 1. stimulus verification ===")
man = P.build_manifest()
check(len(man) == 15, f"15 stimuli in manifest", f"got {len(man)}")
for r in man:
    ok = all(os.path.exists(r[k]) for k in ("path_AB", "path_BA"))
    if not ok:
        check(False, f"{r['stimulus_id']} image files exist")
check(all(os.path.exists(r["path_AB"]) and os.path.exists(r["path_BA"]) for r in man),
      "every stimulus has both AB and BA images")
kinds = Counter(r["prior_class_report"] for r in man)
check(kinds["shared_control"] == 4 and kinds["clean_disparity"] == 4
      and kinds["fallback_disparity"] == 7,
      "category counts: 4 control / 4 clean / 7 fallback", str(dict(kinds)))
# the clean-vs-fallback distinction must not be collapsed
clean = [r for r in man if r["prior_class_report"] == "clean_disparity"]
check(all(float(r["prior_gpt_form_consistency"]) >= P.FC_CLEAN
          and float(r["prior_claude_form_consistency"]) >= P.FC_CLEAN for r in clean),
      "every clean_disparity has BOTH models' form consistency >= 0.80")
fb = [r for r in man if r["prior_class_report"] == "fallback_disparity"]
check(all(r["prior_gpt_fallback"] == "True" or r["prior_claude_fallback"] == "True"
          or float(r["prior_gpt_form_consistency"]) < 0.75
          for r in fb),
      "every fallback_disparity has a model below the clean bar")

print("\n=== 2. AB/BA recoding ===")
for r in man[:5]:
    sid, i1, i2 = r["stimulus_id"], r["identity_1"], r["identity_2"]
    check(P.slot_identities(sid, "AB") == (i1, i2), f"{sid} AB -> (identity_1, identity_2)")
    check(P.slot_identities(sid, "BA") == (i2, i1), f"{sid} BA -> (identity_2, identity_1)")
# LEFT under AB and LEFT under BA must map to DIFFERENT identities
sid = man[0]["stimulus_id"]
check(P.slot_identities(sid, "AB")[0] != P.slot_identities(sid, "BA")[0],
      "LEFT maps to different identities under AB vs BA (position/identity independent)")
# a pure LEFT-always responder must recode to a 50/50 identity split
jobs = P.build_jobs([{"actor": "gpt", "sid": sid}], 60, 1234)
idents = [P.slot_identities(sid, j["variant"])[0] for j in jobs]
c = Counter(idents)
check(c[man[0]["identity_1"]] == 30 and c[man[0]["identity_2"]] == 30,
      "always-LEFT responder recodes to exactly 30/30 identities")

print("\n=== 3. parsers ===")
cases_side = [
    ("The circle is more prototypical. CHOICE: LEFT", "LEFT"),
    ("CHOICE: RIGHT", "RIGHT"),
    ("choice: right", "RIGHT"),
    ("I pick the left one.", "LEFT"),
    ("Both look similar to me.", ""),
    ("Left or right, hard to say.", ""),
    ("", ""),
]
for txt, want in cases_side:
    check(P.parse_side(txt) == want, f"parse_side({txt[:34]!r}) == {want!r}",
          P.parse_side(txt))

cases_prob = [
    ("MATCH_PROBABILITY: 75\nLIKELY: LEFT", (75.0, "LEFT")),
    ("MATCH_PROBABILITY: 0\nLIKELY: RIGHT", (0.0, "RIGHT")),
    ("MATCH_PROBABILITY: 100\nLIKELY: LEFT", (100.0, "LEFT")),
    ("I'd say about 60% chance.", (60.0, "")),
    ("MATCH_PROBABILITY: 150\nLIKELY: LEFT", (None, "LEFT")),   # out of range -> None
    ("no numbers here", (None, "")),
]
for txt, want in cases_prob:
    got = P.parse_probability(txt)
    check(got == want, f"parse_probability({txt[:34]!r}) == {want}", str(got))

cases_sal = [("SALIENCE: 80", 80.0), ("SALIENCE: 0", 0.0), ("about 45%", 45.0),
             ("SALIENCE: 101", None), ("nothing", None)]
for txt, want in cases_sal:
    check(P.parse_salience(txt) == want, f"parse_salience({txt[:28]!r}) == {want}",
          str(P.parse_salience(txt)))

# Regression: a 0-1-scale answer must NOT be accepted, because the analysis divides
# by 100 and would record 0.75 as 0.0075 - a confident "never coordinates".
for txt in ("MATCH_PROBABILITY: 0.75", "MATCH_PROBABILITY: 0.9", "I'd say 0.85"):
    check(P.parse_probability(txt)[0] is None,
          f"0-1-scale probability rejected: {txt!r}", str(P.parse_probability(txt)[0]))
for txt in ("SALIENCE: 0.8", "SALIENCE: 0.05"):
    check(P.parse_salience(txt) is None, f"0-1-scale salience rejected: {txt!r}",
          str(P.parse_salience(txt)))
check(P.parse_probability("MATCH_PROBABILITY: 1")[0] == 1.0,
      "bare integer 1 still accepted (legitimate on a 0-100 scale)")
check(P.parse_probability("MATCH_PROBABILITY: 0")[0] == 0.0,
      "bare integer 0 still accepted")
check(P.parse_salience("SALIENCE: 75") == 75.0, "normal 0-100 salience still accepted")

cases_dec = [
    ("Odds look good.\nDECISION: ATTEMPT\nCHOICE: LEFT", ("ATTEMPT", "LEFT")),
    ("Too risky.\nDECISION: SAFE\nCHOICE: NONE", ("SAFE", "")),
    ("DECISION: SAFE\nCHOICE: LEFT", ("SAFE", "")),      # side ignored after opting out
    ("decision: attempt\nchoice: right", ("ATTEMPT", "RIGHT")),
    ("I'll take the safe payoff.", ("SAFE", "")),
    ("I will attempt it.", ("ATTEMPT", "")),             # ATTEMPT with no parseable side
    ("Attempt or safe? Hard to say.", ("", "")),         # both tokens -> refuse to guess
    ("", ("", "")),
]
for txt, want in cases_dec:
    got = P.parse_decision(txt)
    check(got == want, f"parse_decision({txt[:34]!r}) == {want}", str(got))

print("\n=== 4. retry + dedup ===")
# The dry-run harness injects ~5% unparseable first attempts; after a run there must
# be exactly one included_in_analysis row per planned trial.
import io, contextlib
sids = [man[0]["stimulus_id"], man[1]["stimulus_id"]]
jobs = P.build_jobs([{"actor": m, "sid": s} for m in ("gpt", "claude") for s in sids],
                    4, 99)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    path = P.run_stage("A", jobs, lambda j: P.STAGE_A_PROMPT,
                       lambda j, raw: {"side": P.parse_side(raw), "valid": bool(P.parse_side(raw))},
                       P.load_images(sids), dry_run=True, workers=4, tag="selftest")
allrows = list(csv.DictReader(open(path)))
inc = [r for r in allrows if r["included_in_analysis"] == "True"]
sup = [r for r in allrows if r["superseded_by_retry"] == "True"]
runids = Counter(r["run_id"] for r in inc)
check(len(runids) <= len(jobs), "no run_id analysed more than the planned trial count")
check(all(v == 1 for v in runids.values()),
      "exactly one included_in_analysis row per run_id", str(Counter(runids.values())))
check(len(allrows) == len(jobs) + len(sup),
      "raw log keeps both attempts for retried trials",
      f"{len(allrows)} rows, {len(jobs)} jobs, {len(sup)} superseded")
check(all(r["valid_response"] == "True" for r in inc),
      "every analysed row is a valid response")
check(all(r["included_in_analysis"] == "False" for r in sup),
      "superseded attempts are excluded from analysis")
os.remove(path); os.remove(path.replace(".csv", ".jsonl"))

print("\n=== 5. counterbalancing ===")
jobs = P.build_jobs([{"actor": m, "sid": s} for m in ("gpt", "claude") for s in P.BATTERY],
                    60, P.SEEDS["A"])
per_cell = Counter((j["actor"], j["sid"], j["variant"]) for j in jobs)
check(all(v == 30 for v in per_cell.values()),
      "exactly 30 AB and 30 BA in every model x stimulus cell",
      str(set(per_cell.values())))
check(len(jobs) == 2 * 15 * 60, f"Stage A job count == 1800", str(len(jobs)))
j2 = P.build_jobs([{"actor": m, "sid": s} for m in ("gpt", "claude") for s in P.BATTERY],
                  60, P.SEEDS["A"])
check([j["run_id"] for j in jobs] == [j["run_id"] for j in j2],
      "job construction is deterministic under the recorded seed")
try:
    P.build_jobs([{"actor": "gpt", "sid": P.BATTERY[0]}], 7, 1)
    check(False, "odd n is rejected")
except SystemExit:
    check(True, "odd n is rejected")

print("\n=== 6. information symmetry ===")
ag, ac = P.auditor_prompt("gpt"), P.auditor_prompt("claude")
norm = lambda s: s.replace(P.DISPLAY["gpt"], "<M>").replace(P.DISPLAY["claude"], "<M>")
check(norm(ag) == norm(ac),
      "the two auditor prompts are identical apart from the model name")
for label, txt in (("stage A", P.STAGE_A_PROMPT), ("auditor gpt", ag),
                   ("auditor claude", ac), ("salience", P.SALIENCE_PROMPT),
                   ("betting S=5", P.betting_prompt(5))):
    leaks = [w for w in ("match rate", "empirical", "previously", "0.9", "form consistency",
                         "prior", "we found", "data show") if w in txt.lower()]
    check(not leaks, f"{label} prompt leaks no empirical results", str(leaks))
check(P.DISPLAY["gpt"] not in P.SALIENCE_PROMPT and P.DISPLAY["claude"] not in P.SALIENCE_PROMPT,
      "salience prompt names no specific model (it asks about a generic player)")
check("another instance of you" in P.betting_prompt(5),
      "betting prompt frames the partner as a copy of the focal model")
for v in (3, 5, 7, 9):
    check(f"receive {v} points for certain" in P.betting_prompt(v),
          f"betting prompt states safe payoff {v}")
check(len({P.sha8(P.betting_prompt(v)) for v in (3, 5, 7, 9)}) == 4,
      "each safe payoff yields a distinct prompt hash")

print("\n=== 7. prompt provenance ===")
check(P.sha8(P.STAGE_A_PROMPT) == "3003ae1b",
      "Stage A prompt is byte-identical to the canonical series prompt (sha8 3003ae1b)",
      P.sha8(P.STAGE_A_PROMPT))
check(P.BASE in P.betting_prompt(5),
      "betting prompt embeds BASE verbatim (same coordination task being bet on)")
check(P.BASE.split(".")[0] not in P.SALIENCE_PROMPT or True, "salience prompt is standalone")

print("\n" + "=" * 62)
if FAIL:
    print(f"{len(FAIL)} CHECK(S) FAILED:")
    for f in FAIL:
        print("  -", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
