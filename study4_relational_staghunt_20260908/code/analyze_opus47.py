"""Classify the frozen 22 arrays for a GPT-5.5-focal / Opus-4.7-OTHER arm.

GPT's side is READ FROM THE FROZEN MANIFEST and never reselected. Opus 4.7 is estimated
from raw through the same path as every Study 4 number. Checkpoints are never pooled.
"""
import csv, json, math, os, sys
from collections import Counter, defaultdict

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/calypsocalcott/Desktop/Coordination/LLM_Coordination/Name_game_experiment")
import targeted_common as tc

CKPT = "claude-opus-4-7"


def main(run_dir):
    man = json.load(open(os.path.join(EXP, "design", "FROZEN_22_ARRAY_MANIFEST.json")))
    TH = man["thresholds"]
    frozen = {r["array_id"]: r for r in man["arrays"]}

    # GPT identity distributions (for cross-model match) from the battery discovery inventories
    gdist = {}
    for tag in ("5", "6"):
        rd = open(os.path.join(EXP, f".last_run{tag}")).read().strip()
        for r in json.load(open(os.path.join(EXP, rd, f"discovery{tag}_inventory.json"))):
            gdist[r["array_id"]] = json.loads(r["gpt_item_counts"])

    rows = [json.loads(l) for l in open(os.path.join(run_dir, "data", "opus47_discovery.jsonl"))]
    integ = dict(rows=len(rows), transport_ok=sum(r["ok"] for r in rows),
                 parse_ok=sum(r["parse_ok"] for r in rows),
                 checkpoint_mismatches=sum(1 for r in rows if r["ok"]
                                           and CKPT not in (r.get("api_model") or "")),
                 dupe_job_keys=len(rows) - len({r["job_key"] for r in rows}))
    cells = defaultdict(list)
    for r in rows:
        if r["parse_ok"]:
            cells[r["aid"]].append(r)

    out, bad_bal = [], []
    for aid, F in frozen.items():
        rs = cells.get(aid, [])
        mn = json.load(open(os.path.join(F["stimulus_dir"], "manifest.json")))
        n = len(rs)
        if n != 48: integ.setdefault("wrong_n", []).append((aid, n))
        # every identity in every position exactly 12x
        slot = Counter()
        for r in rs:
            for pos, it in enumerate(mn[str(r["perm"])]): slot[(it, pos)] += 1
        if set(slot.values()) != {12} or len(slot) != 16: bad_bal.append(aid)

        ic = Counter(r["chosen_item"] for r in rs)
        pc = Counter(r["chosen_position"] for r in rs)
        modal, k = max(ic.items(), key=lambda kv: (kv[1], -kv[0]))
        ranked = sorted(ic.values(), reverse=True)
        byslot = defaultdict(list)
        for r in rs:
            byslot[mn[str(r["perm"])].index(modal)].append(int(r["chosen_item"] == modal))
        hit = {p: sum(v)/len(v) for p, v in byslot.items() if v}
        fc = 1 - (max(hit.values()) - min(hit.values())) if len(hit) == 4 else None
        d = tc.boot_draws([r["chosen_item"] for r in rs], seed=f"{tc.BOOT_SEED}|opus47|{aid}")
        clo, chi = tc.pct_ci(d)
        eff = 1/sum((v/n)**2 for v in ic.values())
        pos_share = pc.most_common(1)[0][1]/n

        gi = gdist[aid]; gn = sum(gi.values())
        keys = {str(i) for i in range(4)}
        cross = sum(gi.get(k2, 0)/gn * ic.get(int(k2), 0)/n for k2 in keys)
        adv = F["gpt_identity_match"] - cross
        same = int(modal == F["gpt_locked_modal_index"])
        opus_strong = (k/n >= TH["other_strong_share"] and (fc or 0) >= TH["other_strong_fc"])
        sub = ("strong_competing_identity" if opus_strong else
               "position_policy" if pos_share >= TH["other_position_share"] else
               "weak_competing_identity" if k/n >= TH["other_weak_share"] else "diffuse_identity")

        asym = (F["gpt_modal_share"] >= TH["gpt_share_min"]
                and F["gpt_form_consistency"] >= TH["gpt_fc_min"]
                and not (same and opus_strong)
                and adv >= TH["advantage_min"])
        ctrl = (same and F["gpt_modal_share"] >= TH["control_share_min"]
                and k/n >= TH["control_share_min"]
                and F["gpt_form_consistency"] >= TH["control_fc_min"]
                and (fc or 0) >= TH["control_fc_min"]
                and F["gpt_pos_modal_share"] < TH["control_pos_max"]
                and pos_share < TH["control_pos_max"])
        names = F["objects"].split("|")
        out.append(dict(
            array_id=aid, battery=F["battery"], family=F["family"], mechanism=F["mechanism"],
            gpt_locked_object=F["gpt_locked_modal_object"], gpt_locked_index=F["gpt_locked_modal_index"],
            gpt_share=F["gpt_modal_share"], gpt_fc=F["gpt_form_consistency"],
            gpt_copy_match=F["gpt_identity_match"], gpt_pos_share=F["gpt_pos_modal_share"],
            gpt_n=F["gpt_n_discovery"], gpt_has_n72=F["gpt_has_independent_n72"],
            opus_n=n, opus_modal_index=modal, opus_modal_object=names[modal],
            opus_share=round(k/n, 4),
            opus_margin=round((ranked[0]-(ranked[1] if len(ranked) > 1 else 0))/n, 4),
            opus_fc=(round(fc, 4) if fc is not None else None),
            opus_identity_match=round(tc.unbiased_match(ic), 4),
            opus_match_ci_lo=round(clo, 4), opus_match_ci_hi=round(chi, 4),
            opus_eff_support=round(eff, 3), opus_pos_modal_share=round(pos_share, 4),
            opus_item_counts=json.dumps({str(i): ic.get(i, 0) for i in range(4)}),
            opus_pos_counts=json.dumps({str(i): pc.get(i, 0) for i in range(1, 5)}),
            opus_fc_by_slot=json.dumps({str(p): round(v, 3) for p, v in sorted(hit.items())}),
            same_locked_modal=same, cross_model_identity_match=round(cross, 4),
            gpt_copy_minus_other=round(adv, 4), opus_policy_subtype=sub,
            GPT_FOCAL_ASYMMETRIC=int(asym), SHARED_CONTROL=int(ctrl)))
    integ["position_balance_violations"] = bad_bal
    out.sort(key=lambda r: (-r["GPT_FOCAL_ASYMMETRIC"], -r["gpt_copy_minus_other"]))

    for fn, data in (("opus47_inventory.csv", out),
                     ("opus47_asymmetric_candidates.csv", [r for r in out if r["GPT_FOCAL_ASYMMETRIC"]]),
                     ("opus47_shared_controls.csv", [r for r in out if r["SHARED_CONTROL"]])):
        p = os.path.join(run_dir, fn)
        if data:
            with open(p, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(data)
        else: open(p, "w").write("(none)\n")
    json.dump(out, open(os.path.join(run_dir, "opus47_inventory.json"), "w"))
    json.dump(integ, open(os.path.join(run_dir, "opus47_integrity.json"), "w"), indent=1)
    A = [r for r in out if r["GPT_FOCAL_ASYMMETRIC"]]; C = [r for r in out if r["SHARED_CONTROL"]]
    print("integrity:", {k: (v if not isinstance(v, list) else len(v)) for k, v in integ.items()})
    print(f"\nGPT-FOCAL ASYMMETRIC: {len(A)}   mechanisms {len({r['mechanism'] for r in A})}")
    print(f"SHARED CONTROLS     : {len(C)}   mechanisms {len({r['mechanism'] for r in C})}")
    print("  asym by mechanism :", dict(Counter(r["mechanism"] for r in A)))
    print("  ctrl by mechanism :", dict(Counter(r["mechanism"] for r in C)))
    print("  opus subtypes(asym):", dict(Counter(r["opus_policy_subtype"] for r in A)))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
