"""
STUDY 2 (revised) - emit the FROZEN design table, one row per Stage C cell.

    python3 design_table.py            # write the table and validate
    python3 design_table.py --check    # validate an existing table, write nothing

NO API CALLS. Nothing here contacts a provider, and importing psc_common does not
either (its clients are constructed only inside make_clients()).

SINGLE SOURCE OF TRUTH. Every number comes from design/FROZEN_PARAMS.py. This module
declares no payoff, no sample size, no stimulus name and no tier label of its own; if
a literal appears here that FROZEN_PARAMS already defines, that is a bug.

OUTPUT: design/frozen_design_table.csv, one row per

    (actor_model x stimulus x partner_condition x safe_payoff)

= 2 actors x 8 stimuli x 2 partners x 4 payoffs = 128 cells.

RE-FROZEN 2026-08-22 (design/RE_FREEZE_RECORD.md). Tiers and cell sizes now come from
FROZEN_PARAMS.ACTIVE_GRADIENT (= CONFIRMED_GRADIENT), and `confirmed_advantage` is
FILLED from design/confirmed_compatibility.csv for every row, with
`advantage_source = confirmed`. `provisional_advantage` is retained from the
superseded FROZEN_PARAMS.GRADIENT as provenance and is never an analysis input.

VALIDATION (validate(), run automatically). Hard assertions:
  V1  total Stage C calls implied by the table == FROZEN_PARAMS.stage_c_calls()
  V2  every per-payoff cell size is EVEN, so AB/BA balance is exact
  V3  every stimulus named in ACTIVE_GRADIENT exists in the Study 1 stimulus registry
      - BOTH psc_common.BATTERY AND the frozen stimulus_manifest.csv
  V4  structural completeness: both partner arms and all four safe payoffs present
      for every (actor, stimulus); no duplicate cells; EVERY row carries a
      confirmed_advantage equal to confirmed_compatibility.csv, advantage_source
      is `confirmed`
  V5  every ACTIVE_GRADIENT stimulus has a CONFIRM_N entry
  V6  the recorded tier and n are exactly what FROZEN_PARAMS.allocation_for()
      assigns to that row's CONFIRMED advantage - the design matches the confirmed
      data as a machine-checked property, not a human assertion
Reported but NOT fatal (provenance, not design):
  P1  provisional advantages re-derived from pairs/cross_model_table.csv
  P2  the structural identity |GC - 1/2| = sqrt((GG - 1/2)(CC - 1/2)) re-verified
"""
import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)                      # study2_partner_policy_20260822/
PROJ = os.path.dirname(EXP)
DESIGN = os.path.join(EXP, "design")
STUDY1_CODE = os.path.join(
    PROJ, "policy_specific_self_coordination_20260812_1401", "code")

sys.path.insert(0, DESIGN)
import FROZEN_PARAMS as FP                        # noqa: E402  the only parameter source

OUT_CSV = os.path.join(DESIGN, "frozen_design_table.csv")
CROSS_TBL = os.path.join(EXP, "pairs", "cross_model_table.csv")
CONFIRMED_CSV = os.path.join(DESIGN, "confirmed_compatibility.csv")

COLS = [
    "actor_model", "stimulus", "tier", "partner_condition", "partner_model_named",
    "safe_payoff", "match_payoff", "mismatch_payoff", "framing",
    "n_cell", "n_cell_ab", "n_cell_ba", "n_partner_total",
    "advantage_def", "provisional_advantage", "confirmed_advantage",
    "advantage_source", "confirm_n", "gate_critical", "sensitivity_exclude",
]


# --------------------------------------------------------------- registry ----
def study1_registry():
    """(battery, manifest_ids, how). BATTERY + manifest from the Study 1 project.

    Preferred path is a real import of psc_common (which asserts the Stage A prompt
    hash 3003ae1b at import, so the registry cannot silently belong to a different
    prompt generation). Falls back to an `ast` parse + the manifest CSV on a machine
    without the Study 1 dependencies, so validation still runs with no keys.
    """
    sys.path.insert(0, STUDY1_CODE)
    try:
        import psc_common as psc
        battery = list(psc.BATTERY)
        manifest_path = psc.MANIFEST
        display = dict(psc.DISPLAY)
        how = f"import psc_common (prompt sha8 {psc.STEP1_SHA8})"
    except Exception as exc:                        # pragma: no cover - fallback path
        import ast
        src = open(os.path.join(STUDY1_CODE, "psc_common.py")).read()
        battery = None
        for node in ast.walk(ast.parse(src)):
            if (isinstance(node, ast.Assign)
                    and getattr(node.targets[0], "id", None) == "BATTERY"
                    and isinstance(node.value, ast.List)):
                battery = [ast.literal_eval(e) for e in node.value.elts]
                break
        if battery is None:
            raise RuntimeError("could not recover BATTERY from psc_common.py") from exc
        manifest_path = os.path.join(os.path.dirname(STUDY1_CODE),
                                     "stimulus_manifest.csv")
        display = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
        how = f"ast parse of psc_common.py (import failed: {type(exc).__name__})"
    manifest_ids = [r["stimulus_id"] for r in csv.DictReader(open(manifest_path))]
    return battery, manifest_ids, display, manifest_path, how


OTHER = {"gpt": "claude", "claude": "gpt"}


# ------------------------------------------------- confirmed compatibility ----
def load_confirmed(path=CONFIRMED_CSV):
    """({(actor, stimulus): advantage}, {stimulus: is_ceiling}) from the n=180/120/60
    confirmation screen. WIDE form (advantage_gpt / advantage_claude per stimulus),
    which is what code/confirm_compat.py writes. Missing file is fatal here: after
    the re-freeze the table cannot be emitted without the confirmed values."""
    if not os.path.exists(path):
        raise SystemExit(
            f"no confirmed compatibility table at {path}\n"
            "The design table is re-frozen on the CONFIRMED advantages; emit the "
            "confirmation screen's output first (code/confirm_compat.py).")
    adv, ceil = {}, {}
    for r in csv.DictReader(open(path)):
        sid = r["stimulus"].strip()
        ceil[sid] = FP.is_ceiling(r["GG"], r["CC"])
        for actor in ("gpt", "claude"):
            v = r.get(f"advantage_{actor}", "").strip()
            if v != "":
                adv[(actor, sid)] = float(v)
    if not adv:
        raise SystemExit(f"{os.path.basename(path)} carries no advantage_* columns")
    return adv, ceil


PROVISIONAL = {(m, sid): a
               for m, tiers in FP.GRADIENT.items() for sid, a, _t, _n in tiers}


# ------------------------------------------------------------------ build ----
def build_rows(display, confirmed=None, ceiling=None):
    if confirmed is None:
        confirmed, ceiling = load_confirmed()
    rows = []
    for actor, tiers in FP.ACTIVE_GRADIENT.items():
        for stim, conf_adv, tier, n_partner in tiers:
            prov_adv = PROVISIONAL[(actor, stim)]
            csv_adv = confirmed[(actor, stim)]
            # ACTIVE_GRADIENT quotes 3 dp; the CSV carries full precision. The
            # tolerance is one rounding unit, not a licence to differ.
            assert abs(csv_adv - conf_adv) <= 1e-3, (
                f"ACTIVE_GRADIENT has {actor}/{stim} at {conf_adv:+.3f} but "
                f"confirmed_compatibility.csv says {csv_adv:+.4f}")
            want = FP.allocation_for(csv_adv, ceiling.get(stim, False))
            assert want == (tier, n_partner), (
                f"{actor}/{stim}: table says ({tier}, {n_partner}), the frozen "
                f"allocation rule assigns {want} to confirmed {csv_adv:+.4f}")
            n_cell = FP.per_payoff_n(n_partner)     # asserts divisibility itself
            for partner in FP.PARTNER_CONDITIONS:
                named = display[actor if partner == "same" else OTHER[actor]]
                for safe in FP.SAFE_PAYOFFS:
                    rows.append({
                        "actor_model": actor,
                        "stimulus": stim,
                        "tier": tier,
                        "partner_condition": partner,
                        "partner_model_named": named,
                        "safe_payoff": safe,
                        "match_payoff": FP.MATCH_PAYOFF,
                        "mismatch_payoff": FP.MISMATCH_PAYOFF,
                        "framing": FP.FRAMING,
                        "n_cell": n_cell,
                        "n_cell_ab": n_cell // 2,
                        "n_cell_ba": n_cell // 2,
                        "n_partner_total": n_partner,
                        "advantage_def": FP.ADVANTAGE_DEF,
                        "provisional_advantage": f"{prov_adv:+.3f}",
                        "confirmed_advantage": f"{csv_adv:+.4f}",
                        "advantage_source": "confirmed",
                        "confirm_n": FP.CONFIRM_N[stim],
                        "gate_critical": tier in FP.GATE_CRITICAL_TIERS,
                        "sensitivity_exclude": stim in FP.SENSITIVITY_EXCLUDE,
                    })
    return rows


def write(rows, path=OUT_CSV):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    return path


def read(path=OUT_CSV):
    return list(csv.DictReader(open(path)))


# --------------------------------------------------------------- validate ----
def validate(rows, verbose=True):
    battery, manifest_ids, _display, manifest_path, how = study1_registry()
    say = print if verbose else (lambda *a, **k: None)
    say("=" * 78)
    say("VALIDATION - study2 frozen design table")
    say("=" * 78)
    say(f"registry source : {how}")
    say(f"manifest        : {manifest_path}  ({len(manifest_ids)} stimuli)")
    say(f"rows            : {len(rows)}")

    n = lambda r: int(r["n_cell"])

    # V1 -- total Stage C calls
    total = sum(n(r) for r in rows)
    expected = FP.stage_c_calls()
    say(f"\nV1 total Stage C calls  : {total} vs FROZEN_PARAMS.stage_c_calls() "
        f"= {expected}  {'OK' if total == expected else 'MISMATCH'}")
    assert total == expected, f"Stage C total {total} != {expected}"

    # V2 -- AB/BA balance
    odd = sorted({(r["actor_model"], r["stimulus"], n(r)) for r in rows if n(r) % 2}
                 )
    say(f"V2 per-payoff cells even: {len(rows)}/{len(rows)} "
        f"(sizes {sorted({n(r) for r in rows})})  {'OK' if not odd else odd}")
    assert not odd, f"odd per-payoff cell sizes: {odd}"
    for r in rows:
        assert int(r["n_cell_ab"]) + int(r["n_cell_ba"]) == n(r), r

    # V3 -- stimuli exist in the Study 1 registry
    used = sorted({r["stimulus"] for r in rows})
    miss_b = [s for s in used if s not in battery]
    miss_m = [s for s in used if s not in manifest_ids]
    say(f"V3 stimuli in BATTERY   : {len(used) - len(miss_b)}/{len(used)}  "
        f"{'OK' if not miss_b else 'MISSING ' + str(miss_b)}")
    say(f"   stimuli in manifest  : {len(used) - len(miss_m)}/{len(used)}  "
        f"{'OK' if not miss_m else 'MISSING ' + str(miss_m)}")
    assert not miss_b, f"not in psc_common.BATTERY: {miss_b}"
    assert not miss_m, f"not in stimulus_manifest.csv: {miss_m}"

    # V4 -- structural completeness
    keys = [(r["actor_model"], r["stimulus"], r["partner_condition"],
             int(r["safe_payoff"])) for r in rows]
    assert len(keys) == len(set(keys)), "duplicate design cells"
    for actor, tiers in FP.ACTIVE_GRADIENT.items():
        for stim, _a, _t, n_partner in tiers:
            sub = [r for r in rows
                   if r["actor_model"] == actor and r["stimulus"] == stim]
            assert {r["partner_condition"] for r in sub} == set(FP.PARTNER_CONDITIONS)
            assert {int(r["safe_payoff"]) for r in sub} == set(FP.SAFE_PAYOFFS)
            got = sum(n(r) for r in sub)
            assert got == n_partner * len(FP.PARTNER_CONDITIONS), (actor, stim, got)
    confirmed, ceiling = load_confirmed()
    blank = [r for r in rows if str(r["confirmed_advantage"]).strip() == ""]
    badsrc = [r for r in rows if r.get("advantage_source") != "confirmed"]
    drift = [(r["actor_model"], r["stimulus"]) for r in rows
             if not blank and abs(float(r["confirmed_advantage"])
                                  - confirmed[(r["actor_model"], r["stimulus"])]) > 1e-6]
    say(f"V4 cells complete/unique: OK   confirmed_advantage filled: "
        f"{len(rows) - len(blank)}/{len(rows)}  "
        f"{'OK' if not blank else str(len(blank)) + ' BLANK'}")
    say(f"   advantage_source=confirmed: "
        f"{'OK' if not badsrc else str(len(badsrc)) + ' WRONG'}   "
        f"matches confirmed_compatibility.csv: "
        f"{'OK' if not drift else 'DRIFT ' + str(sorted(set(drift)))}")
    assert not blank, ("confirmed_advantage must be filled for every row after the "
                       "re-freeze (design/RE_FREEZE_RECORD.md)")
    assert not badsrc, "advantage_source must be 'confirmed' on every row"
    assert not drift, f"confirmed_advantage disagrees with the confirmation screen: {drift}"

    # V5 -- confirmation coverage
    no_conf = [s for s in used if s not in FP.CONFIRM_N]
    say(f"V5 CONFIRM_N covers all : {'OK' if not no_conf else 'MISSING ' + str(no_conf)}"
        f"   confirmation calls = "
        f"{sum(FP.CONFIRM_N.values()) * len(FP.CONFIRM_MODELS)}")
    assert not no_conf, no_conf

    # V6 -- the design IS the allocation rule applied to the confirmed advantages
    mism = []
    for r in rows:
        a, sid = r["actor_model"], r["stimulus"]
        want = FP.allocation_for(confirmed[(a, sid)], ceiling.get(sid, False))
        got = (r["tier"], int(r["n_partner_total"]))
        if want != got:
            mism.append((a, sid, got, want))
    say(f"V6 tier/n == allocation_for(confirmed advantage) : "
        f"{'OK' if not mism else 'MISMATCH ' + str(sorted(set(mism)))}"
        f"   ({len(rows) - len(mism)}/{len(rows)} rows)")
    assert not mism, f"recorded tier/n does not follow from the confirmed advantage: {mism}"

    provenance(rows, say)
    say("\nALL HARD CHECKS PASSED")
    return True


def provenance(rows, say):
    """P1/P2 - reported, never fatal. Provisional values are superseded anyway."""
    if not os.path.exists(CROSS_TBL):
        say("\n[P1/P2] cross_model_table.csv absent - provenance check skipped")
        return
    import math
    tbl = {r["stimulus"]: r for r in csv.DictReader(open(CROSS_TBL))}
    own_col = {"gpt": "own_gpt", "claude": "own_claude"}

    say("\n[P1] SUPERSEDED provisional advantage vs pairs/cross_model_table.csv "
        "(own - cross); reported, not asserted, and read by nothing")
    say(f"     {'actor':<8}{'stimulus':<14}{'frozen':>9}{'re-derived':>12}{'diff':>9}")
    worst = 0.0
    for actor, tiers in FP.GRADIENT.items():          # the PROVISIONAL record
        for stim, prov, _t, _n in tiers:
            r = tbl.get(stim)
            if not r:
                continue
            red = float(r[own_col[actor]]) - float(r["cross"])
            d = red - prov
            worst = max(worst, abs(d))
            flag = "   <- differs" if abs(d) > 0.005 else ""
            say(f"     {actor:<8}{stim:<14}{prov:>+9.3f}{red:>+12.3f}{d:>+9.3f}{flag}")
    say(f"     max |diff| = {worst:.3f}")

    say("\n[P2] structural identity |GC-1/2| = sqrt((GG-1/2)(CC-1/2)) over the full "
        "battery")
    resid = []
    for r in tbl.values():
        GG, CC, GC = float(r["own_gpt"]), float(r["own_claude"]), float(r["cross"])
        dev = math.sqrt(max(GG - .5, 0) * max(CC - .5, 0))
        pred = .5 + dev if r["same_modal_identity"] == "True" else .5 - dev
        resid.append(abs(GC - pred))
    say(f"     n = {len(resid)} stimuli, mean |residual| = {sum(resid)/len(resid):.4f}, "
        f"max = {max(resid):.4f}")


# ------------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="validate the existing CSV, write nothing")
    args = ap.parse_args()

    if args.check:
        rows = read()
        print(f"read {len(rows)} rows from {OUT_CSV}\n")
    else:
        _b, _m, display, _p, _h = study1_registry()
        rows = build_rows(display)
        write(rows)
        print(f"-> {OUT_CSV}  ({len(rows)} rows)\n")

    validate(rows)

    print("\nALLOCATION SUMMARY (n per actor x stimulus x partner x payoff cell)")
    print(f"  {'actor':<8}{'stimulus':<14}{'tier':<12}{'conf adv':>9}{'prov adv':>10}"
          f"{'n/partner':>11}{'n/cell':>8}{'confirm n':>11}")
    for actor, tiers in FP.ACTIVE_GRADIENT.items():
        for stim, adv, tier, np_ in tiers:
            print(f"  {actor:<8}{stim:<14}{tier:<12}{adv:>+9.3f}"
                  f"{PROVISIONAL[(actor, stim)]:>+10.3f}{np_:>11}"
                  f"{FP.per_payoff_n(np_):>8}{FP.CONFIRM_N[stim]:>11}")
    print(f"\n  Stage C calls       {FP.stage_c_calls()}")
    print(f"  Confirmation calls  "
          f"{sum(FP.CONFIRM_N.values()) * len(FP.CONFIRM_MODELS)}")
    print(f"  TOTAL               "
          f"{FP.stage_c_calls() + sum(FP.CONFIRM_N.values()) * len(FP.CONFIRM_MODELS)}")


if __name__ == "__main__":
    main()
