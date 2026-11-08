"""Confirmation analysis - TESTS the locked focal identity; never re-chooses a winner.

The unconstrained confirmation mode (whatever the data's own modal object is) is computed
and reported SEPARATELY, so a locked prediction that failed cannot be quietly replaced by
whatever won instead.
"""
import csv, glob, json, math, os, sys
from collections import Counter, defaultdict

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/calypsocalcott/Desktop/Coordination/LLM_Coordination/Name_game_experiment")
import targeted_common as tc

FC_BAR, SHARE_BAR, ADV_BAR, CHANCE = 0.80, 0.75, 0.25, 0.25


def cell(rows, man, target=None):
    n = len(rows)
    ic = Counter(r["item"] for r in rows)
    pc = Counter(r["pos"] for r in rows)
    uncon, uk = ic.most_common(1)[0]
    tgt = uncon if target is None else target
    k = ic.get(tgt, 0)
    byslot = defaultdict(list)
    for r in rows:
        byslot[man[str(r["perm"])].index(tgt)].append(int(r["item"] == tgt))
    hit = {p: sum(v) / len(v) for p, v in byslot.items() if v}
    fc = 1 - (max(hit.values()) - min(hit.values())) if len(hit) == 4 else float("nan")
    ranked = [v for _, v in ic.most_common()]
    return dict(n=n, target=tgt, target_share=round(k / n, 4),
                target_fc=round(fc, 4) if fc == fc else None,
                identity_match=round(tc.unbiased_match(ic), 4),
                eff_support=round(1 / sum((v / n) ** 2 for v in ic.values()), 3),
                margin=round((ranked[0] - (ranked[1] if len(ranked) > 1 else 0)) / n, 4),
                unconstrained_modal=uncon, unconstrained_share=round(uk / n, 4),
                pos_modal_share=round(pc.most_common(1)[0][1] / n, 4),
                counts={str(i): ic.get(i, 0) for i in range(4)})


def main(cf_dir):
    bat = {r["array_id"]: r for r in
           csv.DictReader(open(os.path.join(EXP, "stimuli5", "battery5_manifest.csv")))}
    locked = json.load(open(os.path.join(cf_dir, "LOCKED_INPUT.json")))
    asym = [r for r in locked if r["track"] != "shared_control"]

    cells = defaultdict(list)
    integ = dict(rows=0, ok=0, parse_ok=0, bad_model=0, missing=[])
    for f in glob.glob(os.path.join(cf_dir, "data", "stageA_confirm5*.csv")):
        for r in csv.DictReader(open(f)):
            integ["rows"] += 1; integ["ok"] += r["ok"] == "True"
            integ["parse_ok"] += r["parse_ok"] == "True"
            exp = "gpt-5.5" if r["model"] == "gpt" else "claude-opus-5"
            if exp not in (r["api_model"] or ""): integ["bad_model"] += 1
            if r["parse_ok"] == "True":
                cells[(r["model"], r["array_id"])].append(
                    dict(item=int(r["chosen_item"]), pos=int(r["chosen_position"]),
                         perm=int(r["perm_id"])))
    for (m, sid), v in cells.items():
        if len(v) != 72: integ["missing"].append((m, sid, len(v)))

    mans, out = {}, []
    for L in asym:
        sid, f, o = L["array_id"], L["focal_model"], L["other_model"]
        if sid not in mans:
            mans[sid] = json.load(open(os.path.join(EXP, "stimuli5", sid, "manifest.json")))
        man = mans[sid]
        tgt = L["predicted_focal_modal_identity"]["index"]
        F = cell(cells[(f, sid)], man, target=tgt)
        O = cell(cells[(o, sid)], man)
        fn, on = sum(F["counts"].values()), sum(O["counts"].values())
        cross = sum(F["counts"][k] / fn * O["counts"][k] / on for k in F["counts"])
        adv = round(F["identity_match"] - cross, 4)
        names = bat[sid]["objects"].split("|")
        shared_strong = (O["unconstrained_share"] >= SHARE_BAR
                         and O["unconstrained_modal"] == tgt)
        tests = dict(
            focal_share_ge_75=F["target_share"] >= SHARE_BAR,
            focal_fc_ge_80=(F["target_fc"] is not None and F["target_fc"] >= FC_BAR),
            adv_ge_25=adv >= ADV_BAR,
            no_shared_strong_convention=not shared_strong,
            no_focal_position_artifact=F["pos_modal_share"] <= 0.60,
            clean_trials=len(cells[(f, sid)]) == 72 and len(cells[(o, sid)]) == 72)
        out.append(dict(
            array_id=sid, family=L["family"], mechanism=L["mechanism"],
            variant=L["variant"], focal_model=f, other_model=o,
            locked_focal_object=names[tgt], locked_focal_index=tgt,
            locked_other_policy=L["other_policy"],
            disc_focal_share=L["discovery"][f]["share"],
            disc_adv=L["expected_copy_minus_other"],
            conf_n_focal=F["n"], conf_focal_share=F["target_share"],
            conf_focal_fc=F["target_fc"], conf_focal_margin=F["margin"],
            conf_focal_identity_match=F["identity_match"],
            conf_focal_pos_share=F["pos_modal_share"],
            conf_other_share=O["unconstrained_share"],
            conf_other_modal=names[O["unconstrained_modal"]],
            conf_other_eff_support=O["eff_support"],
            conf_other_pos_share=O["pos_modal_share"],
            conf_cross_model_match=round(cross, 4), conf_copy_minus_other=adv,
            unconstrained_focal_modal=names[F["unconstrained_modal"]],
            unconstrained_focal_share=F["unconstrained_share"],
            locked_prediction_held=int(F["unconstrained_modal"] == tgt),
            **{f"test_{k}": int(v) for k, v in tests.items()},
            CONFIRMED=int(all(tests.values())),
            focal_counts=json.dumps(F["counts"]), other_counts=json.dumps(O["counts"])))

    p = os.path.join(cf_dir, "confirmation5_results.csv")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    json.dump(out, open(os.path.join(cf_dir, "confirmation5_results.json"), "w"))
    json.dump(integ, open(os.path.join(cf_dir, "confirmation_integrity.json"), "w"), indent=1)
    print("wrote", p, len(out), "candidate rows")
    print("integrity:", {k: (v if not isinstance(v, list) else len(v)) for k, v in integ.items()})
    return out


if __name__ == "__main__":
    main(sys.argv[1])
