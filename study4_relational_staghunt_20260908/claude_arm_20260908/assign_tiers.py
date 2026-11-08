import json, csv
from collections import Counter
ARM = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study4_relational_staghunt_20260908/claude_arm_20260908"
rows = json.load(open(f"{ARM}/tiers_raw.json"))
FC, GAP_MIN, POS_MIN = 0.80, 0.20, 0.75
FC_BORDER = 0.75          # only for the explicit T1-borderline flag

def get(r, m): return {k[len(m)+1:]: v for k, v in r.items() if k.startswith(m + "_")}

def classify(r, th):
    G, C = get(r, "gpt"), get(r, "claude")
    cross = r["cross_model_identity_match"]
    def formok(D, f=FC): return D["form_consistency"] >= f and D["obj_modal_share"] >= th
    def posok(D): return D["form_consistency"] < FC and D["pos_modal_share"] >= POS_MIN
    def mixed(D): return D["form_consistency"] < FC and D["pos_modal_share"] < POS_MIN
    if formok(G) and formok(C):
        return (("T1_competing_form" if not r["same_obj_modal"] else "T3_shared_form_control"),
                "both", "")
    for foc, oth, fn, on in ((G, C, "gpt", "claude"), (C, G, "claude", "gpt")):
        if (formok(foc) and foc["identity_match_ci_lo"] > 0.50 and posok(oth)
                and foc["identity_match"] - cross >= GAP_MIN):
            return "T2_form_vs_position", fn, f"OTHER({on}) position policy {oth['pos_modal']} {oth['pos_modal_share']}"
    # unqualified - say why
    if mixed(G) and mixed(C): return "T0_both_mixed", "", ""
    if G["form_consistency"] < FC and C["form_consistency"] < FC:
        return "T0_no_focal_both_position", "", "neither model form-driven"
    for foc, oth, fn, on in ((G, C, "gpt", "claude"), (C, G, "claude", "gpt")):
        if formok(foc) and mixed(oth):
            return "T0_other_mixed_policy", fn, f"OTHER({on}) FC {oth['form_consistency']} pos {oth['pos_modal_share']} - neither clean form nor clean position"
        if formok(foc) and posok(oth):
            return "T0_gap_too_small", fn, f"gap {foc['identity_match']-cross:+.3f} < {GAP_MIN}"
    return "T0_unqualified", "", ""

for r in rows:
    G, C = get(r, "gpt"), get(r, "claude")
    for th, lab in ((0.75, "075"), (0.90, "090")):
        t, f, n = classify(r, th)
        r[f"tier_at_{lab}"], r[f"focal_at_{lab}"], r[f"note_at_{lab}"] = t, f, n
    # explicit borderline flag: would be T1 if the FC bar were .75 instead of .80
    r["t1_borderline"] = int(
        not r["same_obj_modal"]
        and min(G["form_consistency"], C["form_consistency"]) >= FC_BORDER
        and min(G["obj_modal_share"], C["obj_modal_share"]) >= 0.75
        and r["tier_at_075"] != "T1_competing_form")
    r["gpt_policy_type"] = ("form" if G["form_consistency"] >= FC else
                            "position" if G["pos_modal_share"] >= POS_MIN else "mixed")
    r["claude_policy_type"] = ("form" if C["form_consistency"] >= FC else
                               "position" if C["pos_modal_share"] >= POS_MIN else "mixed")

cols = list(rows[0].keys())
p = f"{ARM}/candidate_inventory_tiered.csv"
with open(p, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
json.dump(rows, open(f"{ARM}/tiers.json", "w"))
print("wrote", p, len(rows), "rows,", len(cols), "cols")
for lab, th in (("075", .75), ("090", .90)):
    print(f"\n=== at focal-strength >= {th} ===")
    for (t, f), n in sorted(Counter((r[f"tier_at_{lab}"], r[f"focal_at_{lab}"]) for r in rows).items()):
        fams = len({r["family"] for r in rows if r[f"tier_at_{lab}"] == t and r[f"focal_at_{lab}"] == f})
        print(f"   {t:28} focal={f or '-':7} {n:3}  ({fams} fam)")
print(f"\nT1-borderline (FC bar .75 not .80): {sum(r['t1_borderline'] for r in rows)}")
for r in rows:
    if r["t1_borderline"]: print("   ", r["stimulus_id"], r["battery"], r["family"], "cross", r["cross_model_identity_match"])
