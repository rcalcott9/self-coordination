"""
FROZEN deterministic pair selector for the 5.4/4.8 procedural replication.

Written and committed BEFORE any Stage A result was inspected. Implements §5 of
REPLICATION_5.4_4.8_SPEC.md exactly; given Stage A+B outputs it returns one pair set
with no further judgement. Nothing here may be retuned after seeing Stage C.

Thresholds are anchored to values REALISED BY THE ORIGINAL nine candidates (so the rule
would have admitted the original design) - not to this generation's data, which did not
exist when this file was written.

    E1  d_true_select        >= 0.25     original minimum was 0.287
    E2  holdout_sign_agrees  == True     required; all 9 originals passed
    E3  d_true_holdout       >= 0.20     original minimum was 0.405
    E4  |d_salience_holdout| <= 0.10     original maximum was 0.083
    E5  |d_auditor_holdout|  <= 0.10     original maximum was 0.089
    E6  |z_salience| <= 0.85 and |z_auditor| <= 0.85   original maximum was 0.82

CORRECTION, 2026-08-14, made BEFORE any Stage A result was inspected. E6 was first
written at 0.35 (the SMALL_PUBLIC_Z constant used for the descriptive `pair_diagnostic`
label). Replaying the rule on the original 5.5/Opus-5 matched_pairs.csv showed that
threshold rejects 3 of the 5 pairs the original study actually approved (z_aud up to
0.82), leaving only 3 eligible - i.e. it would have run a STRICTER design than the one
being replicated, violating "as close as possible to the original". E6 is now anchored
the same way E1-E5 are: to the maximum realised by the original approved set. Verified:
all 5 original approved pairs pass at 0.85. The substantive public-matching constraint
is E4/E5, which cap the HOLDOUT gaps at 0.10 in probability units.
    E7  >= 25 valid trials per member per half
    E8  pair_diagnostic defined

Ranking uses the SELECT half only. The holdout is a gate, never a ranking input -
otherwise the split's winner's-curse protection is spent.

Run:  . replication_5_4_4_8/env.sh && python3 select_pairs_replication.py
"""
import csv, math, os, sys
import psc_common as P

E1_MIN_SELECT_GAP = 0.25
E3_MIN_HOLDOUT_GAP = 0.20
E4_MAX_SAL = 0.10
E5_MAX_AUD = 0.10
E6_MAX_PUBLIC_Z = 0.85
E7_MIN_TRIALS_PER_HALF = 25
TARGET = {"gpt": 3, "claude": 2}
TARGET_TOTAL = 5
FC_CLEAN = P.FC_CLEAN

PAIRS_DIR = os.path.join(P.EXP, "pairs")


def f(v, default=float("nan")):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def HI(p):
    return p.get("stimulus_high") or p.get("high_stimulus")


def LO(p):
    return p.get("stimulus_low") or p.get("low_stimulus")


def gates(p):
    """Return (eligible, [reasons_failed]) for one candidate row.

    Reads matched_pairs.csv, which is the FULL table. stage_c_candidates.csv is a
    17-column view with no z_* - passing it here silently NaNs E6 and fails every
    pair. Verified against the original 5.5/Opus-5 run before this rule was used.
    """
    bad = []
    d_sel = f(p.get("delta_true_select"), f(p.get("d_true_select")))
    d_ho = f(p.get("delta_true_holdout"), f(p.get("d_true_holdout")))
    d_sal = f(p.get("delta_salience_holdout"), f(p.get("d_salience_holdout")))
    d_aud = f(p.get("delta_auditor_holdout"), f(p.get("d_auditor_holdout")))
    z_sal = f(p.get("z_salience"))
    z_aud = f(p.get("z_auditor"))
    sign_ok = str(p.get("holdout_sign_agrees", "")).strip().lower() == "true"
    n_hi_s = f(p.get("n_select_high"), float("nan"))
    n_hi_h = f(p.get("n_holdout_high"), float("nan"))
    n_lo_s = f(p.get("n_select_low"), float("nan"))
    n_lo_h = f(p.get("n_holdout_low"), float("nan"))

    if not (d_sel >= E1_MIN_SELECT_GAP):
        bad.append(f"E1 select gap {d_sel:.3f} < {E1_MIN_SELECT_GAP}")
    if not sign_ok:
        bad.append("E2 holdout sign does not agree")
    if not (d_ho >= E3_MIN_HOLDOUT_GAP):
        bad.append(f"E3 holdout gap {d_ho:.3f} < {E3_MIN_HOLDOUT_GAP}")
    if not (abs(d_sal) <= E4_MAX_SAL):
        bad.append(f"E4 |salience gap| {abs(d_sal):.3f} > {E4_MAX_SAL}")
    if not (abs(d_aud) <= E5_MAX_AUD):
        bad.append(f"E5 |auditor gap| {abs(d_aud):.3f} > {E5_MAX_AUD}")
    if not (abs(z_sal) <= E6_MAX_PUBLIC_Z and abs(z_aud) <= E6_MAX_PUBLIC_Z):
        bad.append(f"E6 public z too large (sal {z_sal:.2f}, aud {z_aud:.2f})")
    ns = [n for n in (n_hi_s, n_hi_h, n_lo_s, n_lo_h) if n == n]
    if ns and min(ns) < E7_MIN_TRIALS_PER_HALF:
        bad.append(f"E7 only {min(ns):.0f} trials in a half")
    diag = (p.get("pair_diagnostic") or "").strip()
    if not diag or diag.lower() in ("nan", "undefined"):
        bad.append("E8 pair_diagnostic undefined")
    return (not bad), bad


def score(p):
    """matching_score_public on the SELECT half. Higher is better."""
    z_t = f(p.get("z_true")); z_s = f(p.get("z_salience")); z_a = f(p.get("z_auditor"))
    if any(v != v for v in (z_t, z_s, z_a)):
        return -math.inf
    return z_t - abs(z_s) - abs(z_a)


def sort_key(p):
    """Deterministic ordering: score desc, then the frozen tie-breakers."""
    return (-score(p),
            -f(p.get("delta_true_holdout"), f(p.get("d_true_holdout"), 0.0)),
            abs(f(p.get("delta_salience_holdout"), f(p.get("d_salience_holdout"), 9.9))),
            abs(f(p.get("delta_auditor_holdout"), f(p.get("d_auditor_holdout"), 9.9))),
            p.get("pair_id", ""))


def both_form_rule(p):
    return (f(p.get("form_consistency_high"), f(p.get("fresh_form_consistency_high"))) >= FC_CLEAN
            and f(p.get("form_consistency_low"), f(p.get("fresh_form_consistency_low"))) >= FC_CLEAN)


def select(cands):
    """Apply §5.3 selection to the eligible pool. Returns (chosen, notes)."""
    notes = []
    chosen = []
    for m in ("gpt", "claude"):
        pool = sorted([p for p in cands if p["focal_model"] == m], key=sort_key)
        used, picked = set(), []
        for p in pool:                                  # greedy, no reuse within model
            hi, lo = HI(p), LO(p)
            if hi in used or lo in used:
                continue
            picked.append(p); used.update((hi, lo))
            if len(picked) >= TARGET[m]:
                break

        # §5.3.4 representation: force in one both-form-rule contrast if any exists
        bf = [p for p in pool if both_form_rule(p)]
        if bf and not any(both_form_rule(p) for p in picked):
            forced = bf[0]
            hi, lo = HI(forced), LO(forced)
            drop = None
            for cand in reversed(picked):               # lowest-ranked first
                rest = {s for q in picked if q is not cand for s in (HI(q), LO(q))}
                if hi not in rest and lo not in rest:
                    drop = cand
                    break
            if drop is not None:
                picked = [q for q in picked if q is not drop] + [forced]
                notes.append(f"{m}: forced both-form-rule pair {forced['pair_id']} in, "
                             f"displacing {drop['pair_id']}")
            else:
                notes.append(f"{m}: both-form-rule pair {forced['pair_id']} could not be "
                             f"forced in without stimulus reuse; left out")
        elif not bf:
            notes.append(f"{m}: no both-form-rule contrast available among eligible pairs")
        chosen.append((m, picked))

    flat = [p for _, picked in chosen for p in picked]

    # §5.3.3 backfill across models up to 5
    if len(flat) < TARGET_TOTAL:
        have = {p["pair_id"] for p in flat}
        extra = sorted([p for p in cands if p["pair_id"] not in have], key=sort_key)
        for p in extra:
            same = [q for q in flat if q["focal_model"] == p["focal_model"]]
            used = {s for q in same for s in (HI(q), LO(q))}
            if HI(p) in used or LO(p) in used:
                continue
            flat.append(p)
            notes.append(f"backfilled {p['pair_id']} to reach {TARGET_TOTAL}")
            if len(flat) >= TARGET_TOTAL:
                break
    return sorted(flat, key=sort_key), notes


def main():
    src = os.path.join(P.EXP, "matched_pairs.csv")      # FULL table, carries z_*
    if not os.path.exists(src):
        sys.exit(f"missing {src} - run analyze_stage_ab.py first")
    cands = list(csv.DictReader(open(src)))
    # delta_true_select is DERIVED, not stored by analyze_stage_ab. Without this every
    # E1 test reads nan and no pair can ever qualify. Direction (which member is HIGH)
    # is already fixed by the select half upstream, so this is a plain difference.
    for p_ in cands:
        try:
            p_["delta_true_select"] = str(float(p_["true_self_match_high_select"])
                                          - float(p_["true_self_match_low_select"]))
        except (KeyError, TypeError, ValueError):
            pass
    os.makedirs(PAIRS_DIR, exist_ok=True)

    eligible, rejected = [], []
    for p in cands:
        ok, why = gates(p)
        (eligible if ok else rejected).append((p, why))

    print(f"\n  candidates {len(cands)}   eligible {len(eligible)}   "
          f"failed gates {len(rejected)}")

    with open(os.path.join(PAIRS_DIR, "candidate_pairs.csv"), "w", newline="") as fh:
        keys = sorted({k for p in cands for k in p})
        w = csv.DictWriter(fh, fieldnames=keys + ["eligible", "gate_failures",
                                                  "matching_score_public"],
                           restval="")
        w.writeheader()
        for p, why in [(p, w_) for p, w_ in eligible] + rejected:
            w.writerow({**p, "eligible": not why, "gate_failures": "; ".join(why),
                        "matching_score_public": round(score(p), 4)
                        if score(p) != -math.inf else ""})

    with open(os.path.join(PAIRS_DIR, "rejected_pairs.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["pair_id", "focal_model", "reason"])
        for p, why in rejected:
            w.writerow([p["pair_id"], p["focal_model"], "; ".join(why)])

    elig = [p for p, _ in eligible]
    if len(elig) < 3:
        print(f"\n  *** STOP CONDITION MET: only {len(elig)} eligible pairs (< 3).")
        print("  *** Per spec §5.6, Stage C must NOT run.")
        for p, why in rejected:
            print(f"      {p['pair_id']}: {'; '.join(why)}")
        sys.exit(2)

    chosen, notes = select(elig)
    with open(os.path.join(PAIRS_DIR, "approved_pairs.csv"), "w", newline="") as fh:
        keys = sorted({k for p in chosen for k in p})
        w = csv.DictWriter(fh, fieldnames=keys, restval="")
        w.writeheader()
        for p in chosen:
            w.writerow(p)

    print(f"\n  SELECTED {len(chosen)} pairs (frozen rule, no manual input):\n")
    hdr = (f"    {'pair_id':44}{'sel':>7}{'ho':>7}{'sal':>7}{'aud':>7}{'score':>7}  diag")
    print(hdr)
    for p in chosen:
        print(f"    {p['pair_id']:44}{f(p.get('delta_true_select')):7.3f}"
              f"{f(p['delta_true_holdout']):7.3f}{f(p['delta_salience_holdout']):7.3f}"
              f"{f(p['delta_auditor_holdout']):7.3f}{score(p):7.3f}  {p['pair_diagnostic']}")
    for n in notes:
        print(f"    note: {n}")
    if len(chosen) < TARGET_TOTAL:
        print(f"\n  NOTE: only {len(chosen)} pairs qualified (< {TARGET_TOTAL}). "
              f"Proceeding per §5.6 with reduced power.")
    print(f"\n  -> {PAIRS_DIR}/approved_pairs.csv")


if __name__ == "__main__":
    main()
