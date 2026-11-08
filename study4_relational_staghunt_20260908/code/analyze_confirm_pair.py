"""Confirmation analysis for the GPT-5.5-focal / older-Claude-OTHER pairing.

TESTS the locked GPT identity; never reselects. Unconstrained modes reported separately.
"""
import csv, json, os, sys
from collections import Counter, defaultdict
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/calypsocalcott/Desktop/Coordination/LLM_Coordination/Name_game_experiment")
import targeted_common as tc
FC_BAR, SHARE_BAR, ADV_BAR, POS_BAR = 0.80, 0.75, 0.25, 0.60


def cell(rs, mn, target=None):
    n = len(rs); ic = Counter(r["chosen_item"] for r in rs)
    pc = Counter(r["chosen_position"] for r in rs)
    unc, uk = max(ic.items(), key=lambda kv: (kv[1], -kv[0]))
    tgt = unc if target is None else target
    byslot = defaultdict(list)
    for r in rs: byslot[mn[str(r["perm"])].index(tgt)].append(int(r["chosen_item"] == tgt))
    hit = {p: sum(v)/len(v) for p, v in byslot.items() if v}
    fc = 1 - (max(hit.values()) - min(hit.values())) if len(hit) == 4 else None
    ranked = sorted(ic.values(), reverse=True)
    return dict(n=n, target=tgt, share=round(ic.get(tgt, 0)/n, 4),
                fc=(round(fc, 4) if fc is not None else None),
                identity_match=round(tc.unbiased_match(ic), 4),
                eff=round(1/sum((v/n)**2 for v in ic.values()), 3),
                margin=round((ranked[0]-(ranked[1] if len(ranked) > 1 else 0))/n, 4),
                unc_modal=unc, unc_share=round(uk/n, 4),
                pos_share=round(pc.most_common(1)[0][1]/n, 4),
                counts={str(i): ic.get(i, 0) for i in range(4)},
                fc_by_slot={str(p): round(v, 3) for p, v in sorted(hit.items())})


def main(cf):
    lock = json.load(open(sys.argv[2]))
    frozen = {r["array_id"]: r for r in json.load(
        open(os.path.join(EXP, "design", "FROZEN_22_ARRAY_MANIFEST.json")))["arrays"]}
    rows = [json.loads(l) for l in open(os.path.join(cf, "data", "confirm_pair.jsonl"))]
    cells = defaultdict(list)
    for r in rows:
        if r["parse_ok"]: cells[(r["actor"], r["aid"])].append(r)
    out = []
    for c in lock["candidates"]:
        aid = c["array_id"]; tgt = c["predicted_focal_modal_identity"]["index"]
        mn = json.load(open(os.path.join(frozen[aid]["stimulus_dir"], "manifest.json")))
        G = cell(cells[("gpt", aid)], mn, target=tgt)
        O = cell(cells[("claude", aid)], mn)
        gn, on = sum(G["counts"].values()), sum(O["counts"].values())
        cross = sum(G["counts"][k]/gn * O["counts"][k]/on for k in G["counts"])
        adv = round(G["identity_match"] - cross, 4)
        opus_strong = O["unc_share"] >= SHARE_BAR and (O["fc"] or 0) >= FC_BAR
        shares = opus_strong and O["unc_modal"] == tgt
        t = dict(gpt_share_ge_75=G["share"] >= SHARE_BAR,
                 gpt_fc_ge_80=(G["fc"] is not None and G["fc"] >= FC_BAR),
                 adv_ge_25=adv >= ADV_BAR,
                 other_not_same_strong=not shares,
                 no_gpt_position_artifact=G["pos_share"] <= POS_BAR,
                 clean=len(cells[("gpt", aid)]) == 72 and len(cells[("claude", aid)]) == 72)
        names = frozen[aid]["objects"].split("|")
        out.append(dict(array_id=aid, mechanism=c["mechanism"], family=c["family"],
            locked_object=c["predicted_focal_modal_identity"]["name"],
            disc_adv=c["expected_copy_minus_other"],
            gpt_n=G["n"], gpt_share=G["share"], gpt_fc=G["fc"], gpt_margin=G["margin"],
            gpt_copy_match=G["identity_match"], gpt_pos_share=G["pos_share"],
            gpt_unconstrained_modal=names[G["unc_modal"]], gpt_unc_share=G["unc_share"],
            locked_held=int(G["unc_modal"] == tgt),
            opus_n=O["n"], opus_modal=names[O["unc_modal"]], opus_share=O["unc_share"],
            opus_fc=O["fc"], opus_eff=O["eff"], opus_pos_share=O["pos_share"],
            cross_model_match=round(cross, 4), copy_minus_other=adv,
            other_subtype=c["other_policy_subtype"],
            gpt_fc_by_slot=json.dumps(G["fc_by_slot"]),
            **{f"test_{k}": int(v) for k, v in t.items()},
            CONFIRMED=int(all(t.values()))))
    out.sort(key=lambda r: (-r["CONFIRMED"], -r["copy_minus_other"]))
    p = os.path.join(cf, "confirm_pair_results.csv")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    json.dump(out, open(os.path.join(cf, "confirm_pair_results.json"), "w"))
    C = [r for r in out if r["CONFIRMED"]]
    h = f"{'array':22}{'mech':14}{'locked':>18}{'shr':>6}{'FC':>6}{'ADV':>8}{'oShr':>6}{'oFC':>6}  held CONF  failed"
    print(h); print("-"*len(h))
    for r in out:
        ft = [k[5:] for k, v in r.items() if k.startswith("test_") and not v]
        print(f"{r['array_id']:22}{r['mechanism'][:13]:14}{r['locked_object'][:17]:>18}"
              f"{r['gpt_share']:>6.2f}{(r['gpt_fc'] or 0):>6.2f}{r['copy_minus_other']:>+8.3f}"
              f"{r['opus_share']:>6.2f}{(r['opus_fc'] or 0):>6.2f}  {'Y' if r['locked_held'] else 'N'}"
              f"   {'YES' if r['CONFIRMED'] else 'no '}  {','.join(ft)}")
    print(f"\nCONFIRMED {len(C)}/{len(out)}   mechanisms {sorted({r['mechanism'] for r in C})}")
    print("locked prediction held:", sum(r["locked_held"] for r in out), "/", len(out))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
