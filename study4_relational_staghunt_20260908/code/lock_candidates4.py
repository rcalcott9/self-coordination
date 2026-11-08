"""Apply Track A / Track B / shared-control promotion rules and LOCK the predictions.

A locked record fixes track, focal direction, predicted canonical modal object, and (Track B)
predicted OTHER screen position BEFORE confirmation runs. Confirmation may not redefine any
of them; an unconstrained confirmation mode is reported separately.
"""
import csv, hashlib, json, os, sys
from datetime import datetime, timezone

FC_CLEAN, POS_MIN, GAP_MIN = 0.80, 0.75, 0.20


def classify(r, th):
    g = {k[4:]: v for k, v in r.items() if k.startswith("gpt_")}
    c = {k[7:]: v for k, v in r.items() if k.startswith("claude_")}
    cross = r["cross_model_identity_match"]
    def fc(D): return float(D["form_consistency"]) if D["form_consistency"] != "" else float("nan")
    def formok(D): return fc(D) >= FC_CLEAN and D["obj_modal_share"] >= th
    def posdriven(D): return fc(D) < FC_CLEAN and D["pos_modal_share"] >= POS_MIN

    if formok(g) and formok(c):
        if r["same_obj_modal"]:
            return dict(track="shared_control", focal="both", reason="both form-driven, same modal object")
        if (g["identity_match"] - cross >= GAP_MIN and c["identity_match"] - cross >= GAP_MIN
                and not posdriven(g) and not posdriven(c)):
            return dict(track="A_competing_form", focal="both",
                        reason="both form-driven, different modal objects, cross below both COPY matches")
        return dict(track="fail", focal="",
                    reason=f"different modes but cross {cross} not materially below both COPY matches")
    for foc, oth, fn, on in ((g, c, "gpt", "claude"), (c, g, "claude", "gpt")):
        if formok(foc) and posdriven(oth) and foc["identity_match"] - cross >= GAP_MIN:
            return dict(track="B_form_vs_position", focal=fn,
                        reason=f"{fn} form-driven; {on} position-driven ({oth['pos_modal']} "
                               f"{oth['pos_modal_share']}); COPY-minus-OTHER "
                               f"{foc['identity_match']-cross:+.3f}")
    bits = []
    for nm, D in (("gpt", g), ("claude", c)):
        if D["obj_modal_share"] < th: bits.append(f"{nm} modal share {D['obj_modal_share']}<{th}")
        if fc(D) < FC_CLEAN and D["pos_modal_share"] < POS_MIN:
            bits.append(f"{nm} mixed (FC {D['form_consistency']}, pos {D['pos_modal_share']})")
        elif fc(D) < FC_CLEAN: bits.append(f"{nm} position-driven")
    return dict(track="fail", focal="", reason="; ".join(bits) or "no rule matched")


def main(run_dir):
    inv = json.load(open(os.path.join(run_dir, "discovery4_inventory.json")))
    integ = json.load(open(os.path.join(run_dir, "trial_integrity.json")))
    clean = not (integ["dupes"] or integ["missing"] or integ["bad_model"])
    locked, table = [], []
    for r in inv:
        a75, a90 = classify(r, 0.75), classify(r, 0.90)
        g = {k[4:]: v for k, v in r.items() if k.startswith("gpt_")}
        c = {k[7:]: v for k, v in r.items() if k.startswith("claude_")}
        table.append(dict(stimulus_id=r["stimulus_id"], family=r["family"],
                          hypothesised_track=r["track_hypothesis"],
                          track_at_075=a75["track"], focal_at_075=a75["focal"],
                          track_at_090=a90["track"], focal_at_090=a90["focal"],
                          reason=a75["reason"]))
        if a75["track"] in ("A_competing_form", "B_form_vs_position", "shared_control"):
            names = r["objects"].split("|")
            rec = dict(
                array_id=r["stimulus_id"], family=r["family"], mechanism=r["mechanism"],
                source_binary=r["source_binary"], proposed_track=a75["track"],
                focal_model=a75["focal"], stable_at_090=(a90["track"] == a75["track"]),
                predicted_focal_modal_object=None, predicted_other_modal_object=None,
                predicted_other_modal_position=None,
                discovery=dict(
                    n_per_cell=24, prompt_sha8=r["prompt_sha8"],
                    gpt=dict(modal=names[g["obj_modal"]], share=g["obj_modal_share"],
                             margin=g["obj_margin"], fc=g["form_consistency"],
                             identity_match=g["identity_match"], pos_modal=g["pos_modal"],
                             pos_share=g["pos_modal_share"], live=g["n_live_objects"],
                             policy=g["policy_type"]),
                    claude=dict(modal=names[c["obj_modal"]], share=c["obj_modal_share"],
                                margin=c["obj_margin"], fc=c["form_consistency"],
                                identity_match=c["identity_match"], pos_modal=c["pos_modal"],
                                pos_share=c["pos_modal_share"], live=c["n_live_objects"],
                                policy=c["policy_type"]),
                    cross_model_identity_match=r["cross_model_identity_match"],
                    gpt_copy_minus_other=r["gpt_copy_minus_other"],
                    claude_copy_minus_other=r["claude_copy_minus_other"]),
                intended_confirmation=dict(
                    n_per_model_per_array=60, prompt="unchanged, sha8 d40ea45d",
                    permutations="24, balanced (60 = 2 full cycles + 12 -> use n=48 or 72 for exact balance)",
                    tests=["focal modal object reproduces at share >= .75",
                           "focal form consistency >= .80",
                           ("OTHER modal screen position reproduces at share >= .75"
                            if a75["track"] == "B_form_vs_position" else
                            "OTHER modal object reproduces"),
                           "COPY-minus-OTHER identity advantage >= .20",
                           "no parse failures, exact checkpoint on every row"]),
                locked_utc=datetime.now(timezone.utc).isoformat(),
                discovery_integrity_clean=clean)
            if a75["track"] == "A_competing_form":
                rec["predicted_focal_modal_object"] = {"gpt": names[g["obj_modal"]],
                                                       "claude": names[c["obj_modal"]]}
            elif a75["track"] == "shared_control":
                rec["predicted_focal_modal_object"] = names[g["obj_modal"]]
            else:
                foc, oth = (g, c) if a75["focal"] == "gpt" else (c, g)
                rec["predicted_focal_modal_object"] = names[foc["obj_modal"]]
                rec["predicted_other_modal_position"] = oth["pos_modal"]
                rec["predicted_other_modal_object"] = names[oth["obj_modal"]]
            locked.append(rec)

    body = json.dumps(locked, indent=1, sort_keys=True)
    h = hashlib.sha256(body.encode()).hexdigest()[:16]
    open(os.path.join(run_dir, "CONFIRMATION_CANDIDATES_LOCKED.json"), "w").write(body)
    open(os.path.join(run_dir, "CONFIRMATION_CANDIDATES_LOCKED.sha256"), "w").write(h + "\n")
    with open(os.path.join(run_dir, "discovery4_tracks.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(table[0].keys())); w.writeheader(); w.writerows(table)
    print(f"locked {len(locked)} candidates, manifest sha256[:16] = {h}")
    for t in table:
        print(f"  {t['stimulus_id']:18} hyp={t['hypothesised_track']}  "
              f".75={t['track_at_075']:20} .90={t['track_at_090']:20} focal={t['focal_at_075'] or '-'}")
    return locked, table


if __name__ == "__main__":
    main(sys.argv[1])
