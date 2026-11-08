"""Apply the battery5 promotion rules and LOCK the confirmation predictions.

The battery5 rules are NOT the battery4 rules. A focal-model x array candidate is
promoted when ALL of:

  1. focal canonical modal share       >= .75
  2. focal form consistency            >= .80, OR inside the explicitly flagged
                                       borderline band .667-.80 (`borderline_fc`)
  3. focal dyadic identity match       >  .35   (clearly above the .25 chance floor)
  4. the OTHER model does NOT share the same strong canonical convention, i.e.
     NOT(other modal share >= .75 AND other FC >= .80 AND same modal object)
  5. focal COPY match - focal-OTHER cross match >= .25

`priority` marks the diffuse-OTHER subset - OTHER modal share <= .55 AND OTHER
effective identity support >= 2.5 AND OTHER position modal share <= .60. It is a
PRIORITISATION flag, never an exclusion: unprioritised candidates stay promoted.

SHARED CONTROLS are retained separately: both models modal share >= .75, both FC
>= .80, same canonical modal object.

Everything is reported twice - at the .75 focal modal-share rule and at a stricter
.90 - so the sensitivity of the promotion set to that one threshold is visible.

A locked record fixes focal direction, predicted canonical modal identity, the
OTHER-policy subtype and the expected match levels BEFORE confirmation runs.
Confirmation may not redefine any of them.
"""
import csv, hashlib, json, os, sys
from datetime import datetime, timezone

MODAL_MIN, MODAL_STRICT = 0.75, 0.90
FC_CLEAN = 0.80
# The borderline band's lower edge is the 4-of-6 rung, FC = 2/3. At n = 24 the modal
# object sits at each slot exactly 6 times, so FC can only take values 1 - k/6 and the
# inventory stores that rung as 0.6667 - just under a literal .667. Compare against 2/3
# with a tolerance so the intended rung is inside the band.
FC_BORDER = 2 / 3 - 1e-6
ID_MATCH_MIN = 0.35                 # "clearly exceeds .25"
GAP_MIN = 0.25
OTH_STRONG = 0.75                   # other shares the same strong convention
PRI_OTH_MODAL_MAX, PRI_EFF_MIN, PRI_OTH_POS_MAX = 0.55, 2.5, 0.60
CONFIRM_N = 72                      # brief specifies n=72; also 3 full 24-permutation cycles -> exact position balance


def split(r):
    g = {k[4:]: v for k, v in r.items() if k.startswith("gpt_")}
    c = {k[7:]: v for k, v in r.items() if k.startswith("claude_")}
    return g, c


def fcv(D):
    v = D.get("form_consistency", "")
    return float(v) if v not in ("", None) else float("nan")


def evaluate(r, focal, th):
    """Promotion decision for one focal direction at focal modal-share threshold th."""
    g, c = split(r)
    foc, oth = (g, c) if focal == "gpt" else (c, g)
    gap = r[f"{focal}_copy_minus_other"]
    fc, ofc = fcv(foc), fcv(oth)

    modal_ok = foc["obj_modal_share"] >= th
    fc_clean = fc >= FC_CLEAN
    fc_border = (FC_BORDER <= fc < FC_CLEAN)
    fc_ok = fc_clean or fc_border
    id_ok = foc["identity_match"] > ID_MATCH_MIN
    other_shares = bool(oth["obj_modal_share"] >= OTH_STRONG and ofc >= FC_CLEAN
                        and r["same_obj_modal"])
    gap_ok = gap >= GAP_MIN

    fails = []
    if not modal_ok: fails.append(f"{focal} modal share {foc['obj_modal_share']} < {th}")
    if not fc_ok: fails.append(f"{focal} FC {foc['form_consistency'] or 'na'} < .667")
    if not id_ok: fails.append(f"{focal} identity match {foc['identity_match']} <= {ID_MATCH_MIN}")
    if other_shares: fails.append("OTHER shares the same strong canonical convention")
    if not gap_ok: fails.append(f"{focal} COPY-minus-OTHER {gap} < {GAP_MIN}")

    return dict(
        focal=focal, promoted=not fails, borderline_fc=bool(fc_border),
        priority=bool(oth["obj_modal_share"] <= PRI_OTH_MODAL_MAX
                      and oth["eff_identity_support"] >= PRI_EFF_MIN
                      and oth["pos_modal_share"] <= PRI_OTH_POS_MAX),
        other_policy=r[f"other_policy_for_focal_{focal}"],
        copy_minus_other=gap, reason="; ".join(fails) or "all battery5 promotion rules met")


def shared_control(r, th=MODAL_MIN):
    g, c = split(r)
    return bool(g["obj_modal_share"] >= th and c["obj_modal_share"] >= th
                and fcv(g) >= FC_CLEAN and fcv(c) >= FC_CLEAN and r["same_obj_modal"])


def stats(D, names):
    return dict(modal_index=D["obj_modal"], modal=names[D["obj_modal"]],
                share=D["obj_modal_share"], margin=D["obj_margin"],
                fc=D["form_consistency"], identity_match=D["identity_match"],
                identity_match_ci=[D["identity_match_ci_lo"], D["identity_match_ci_hi"]],
                eff_identity_support=D["eff_identity_support"],
                pos_modal=D["pos_modal"], pos_share=D["pos_modal_share"],
                live=D["n_live_objects"], entropy_bits=D["entropy_bits"],
                policy=D["policy_type"], item_counts=json.loads(D["item_counts"]),
                form_consistency_by_slot=json.loads(D["form_consistency_by_slot"]))


def other_test(policy, oth, names):
    if policy == "position":
        return (f"OTHER reproduces its modal screen position {oth['pos_modal']} "
                f"at share >= .75")
    if policy in ("strong_competing_identity", "weak_competing_identity"):
        return f"OTHER reproduces its competing modal object {names[oth['obj_modal']]}"
    return ("OTHER identity distribution stays diffuse: modal share <= .55 and "
            "effective identity support >= 2.5")


def main(run_dir):
    inv = json.load(open(os.path.join(run_dir, "discovery5_inventory.json")))
    integ = json.load(open(os.path.join(run_dir, "trial_integrity.json")))
    clean = not (integ["dupes"] or integ["missing"] or integ["bad_model"])
    now = datetime.now(timezone.utc).isoformat()

    locked, table = [], []
    for r in inv:
        g, c = split(r)
        names = r["objects"].split("|")
        ev = {m: evaluate(r, m, MODAL_MIN) for m in ("gpt", "claude")}
        ev90 = {m: evaluate(r, m, MODAL_STRICT) for m in ("gpt", "claude")}
        sc, sc90 = shared_control(r, MODAL_MIN), shared_control(r, MODAL_STRICT)

        row = dict(array_id=r["array_id"], family=r["family"], mechanism=r["mechanism"],
                   variant=r["variant"], same_obj_modal=r["same_obj_modal"],
                   cross_model_identity_match=r["cross_model_identity_match"],
                   shared_control_075=int(sc), shared_control_090=int(sc90))
        for m in ("gpt", "claude"):
            row[f"{m}_promoted_075"] = int(ev[m]["promoted"])
            row[f"{m}_promoted_090"] = int(ev90[m]["promoted"])
            row[f"{m}_borderline_fc"] = int(ev[m]["borderline_fc"])
            row[f"{m}_priority"] = int(ev[m]["priority"])
            row[f"{m}_other_policy"] = ev[m]["other_policy"]
            row[f"{m}_copy_minus_other"] = ev[m]["copy_minus_other"]
            row[f"{m}_reason"] = ev[m]["reason"]
        row["outcome"] = ("shared_control" if sc else
                          "+".join(m for m in ("gpt", "claude") if ev[m]["promoted"])
                          or "fail")
        table.append(row)

        for m in ("gpt", "claude"):
            if sc or not ev[m]["promoted"]:
                continue
            foc, oth = (g, c) if m == "gpt" else (c, g)
            on = "claude" if m == "gpt" else "gpt"
            pol = ev[m]["other_policy"]
            locked.append(dict(
                array_id=r["array_id"], family=r["family"], mechanism=r["mechanism"],
                variant=r["variant"], objects=r["objects"], track="focal_vs_other",
                focal_model=m, other_model=on,
                predicted_focal_modal_identity=dict(index=foc["obj_modal"],
                                                    name=names[foc["obj_modal"]]),
                other_policy=pol,
                predicted_other_modal_identity=dict(index=oth["obj_modal"],
                                                    name=names[oth["obj_modal"]]),
                predicted_other_modal_position=(oth["pos_modal"] if pol == "position" else None),
                expected_copy_match=foc["identity_match"],
                expected_cross_model_match=r["cross_model_identity_match"],
                expected_copy_minus_other=ev[m]["copy_minus_other"],
                borderline_fc=ev[m]["borderline_fc"], priority=ev[m]["priority"],
                stable_at_090=ev90[m]["promoted"],
                discovery=dict(n_per_cell=r["gpt_n"], prompt_sha8=r["prompt_sha8"],
                               chance_identity_match=r["chance_identity_match"],
                               gpt=stats(g, names), claude=stats(c, names),
                               cross_model_identity_match=r["cross_model_identity_match"],
                               gpt_copy_minus_other=r["gpt_copy_minus_other"],
                               claude_copy_minus_other=r["claude_copy_minus_other"]),
                confirmation=dict(
                    n_per_model_per_array=CONFIRM_N,
                    permutations=f"{CONFIRM_N} = 2 full 24-permutation cycles (exact position balance)",
                    prompt=f"unchanged, sha8 {r['prompt_sha8']}",
                    tests=[f"focal modal identity {names[foc['obj_modal']]} reproduces at share >= .75",
                           ("focal form consistency >= .667 (locked as BORDERLINE)"
                            if ev[m]["borderline_fc"] else "focal form consistency >= .80"),
                           "focal dyadic identity match > .35 (chance .25)",
                           other_test(pol, oth, names),
                           "focal COPY-minus-OTHER identity advantage >= .25",
                           "no parse failures, exact checkpoint on every row"]),
                locked_utc=now, discovery_integrity_clean=clean))

        if sc:
            locked.append(dict(
                array_id=r["array_id"], family=r["family"], mechanism=r["mechanism"],
                variant=r["variant"], objects=r["objects"], track="shared_control",
                focal_model="both", other_model="both",
                predicted_focal_modal_identity=dict(index=g["obj_modal"],
                                                    name=names[g["obj_modal"]]),
                other_policy="shared_convention",
                predicted_other_modal_identity=dict(index=c["obj_modal"],
                                                    name=names[c["obj_modal"]]),
                predicted_other_modal_position=None,
                expected_copy_match=dict(gpt=g["identity_match"], claude=c["identity_match"]),
                expected_cross_model_match=r["cross_model_identity_match"],
                expected_copy_minus_other=dict(gpt=r["gpt_copy_minus_other"],
                                               claude=r["claude_copy_minus_other"]),
                borderline_fc=False, priority=False, stable_at_090=sc90,
                discovery=dict(n_per_cell=r["gpt_n"], prompt_sha8=r["prompt_sha8"],
                               chance_identity_match=r["chance_identity_match"],
                               gpt=stats(g, names), claude=stats(c, names),
                               cross_model_identity_match=r["cross_model_identity_match"],
                               gpt_copy_minus_other=r["gpt_copy_minus_other"],
                               claude_copy_minus_other=r["claude_copy_minus_other"]),
                confirmation=dict(
                    n_per_model_per_array=CONFIRM_N,
                    permutations=f"{CONFIRM_N} = 2 full 24-permutation cycles (exact position balance)",
                    prompt=f"unchanged, sha8 {r['prompt_sha8']}",
                    tests=[f"both models reproduce {names[g['obj_modal']]} at share >= .75",
                           "both form consistencies >= .80",
                           "cross-model identity match stays >= .55",
                           "no parse failures, exact checkpoint on every row"]),
                locked_utc=now, discovery_integrity_clean=clean))

    body = json.dumps(locked, indent=1, sort_keys=True)
    h = hashlib.sha256(body.encode()).hexdigest()[:16]
    open(os.path.join(run_dir, "CONFIRMATION_CANDIDATES_LOCKED5.json"), "w").write(body)
    open(os.path.join(run_dir, "CONFIRMATION_CANDIDATES_LOCKED5.sha256"), "w").write(h + "\n")
    with open(os.path.join(run_dir, "discovery5_tracks.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(table[0].keys())); w.writeheader(); w.writerows(table)

    foc = [x for x in locked if x["track"] == "focal_vs_other"]
    print(f"locked {len(locked)} records "
          f"({len(foc)} focal, {len(locked)-len(foc)} shared controls), "
          f"manifest sha256[:16] = {h}")
    print(f"  priority (diffuse OTHER): {sum(1 for x in foc if x['priority'])}   "
          f"borderline FC: {sum(1 for x in foc if x['borderline_fc'])}   "
          f"stable at .90: {sum(1 for x in foc if x['stable_at_090'])}")
    for t in table:
        print(f"  {t['array_id']:18} {t['mechanism']:14} .75={t['outcome'] or '-':14} "
              f"gpt[{t['gpt_promoted_075']}/{t['gpt_promoted_090']}] "
              f"cld[{t['claude_promoted_075']}/{t['claude_promoted_090']}] "
              f"sc[{t['shared_control_075']}]")
    return locked, table


if __name__ == "__main__":
    main(sys.argv[1])
