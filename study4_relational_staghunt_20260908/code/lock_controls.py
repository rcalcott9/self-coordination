"""Lock the final 6 controls from Stage 1 and report asymmetric-vs-control balance.

Selection is copied from the Stage 1 analyser's application of the PREDECLARED rule;
nothing is re-chosen here. Balance is reported, never optimised.
"""
import hashlib, json, os, sys
from collections import Counter

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(EXP, "pilot")


def main(run_dir):
    res = json.load(open(os.path.join(run_dir, "control_validation_results.json")))
    assert res["STAGE1_OK"], "Stage 1 did not pass"
    man = json.load(open(os.path.join(P, "PILOT_MANIFEST_LOCKED.json")))
    val = {r["array_id"]: r for r in res["arrays"]}
    keep = res["selected"]
    assert len(keep) == 6, keep

    ctrl = []
    for c in man["controls"]:
        if c["array_id"] not in keep:
            continue
        v = val[c["array_id"]]
        c = dict(c)
        c.update(validated=True, validation_run=os.path.basename(run_dir),
                 role="locked_control",
                 val_claude_share=float(v["claude_locked_share"]),
                 val_gpt_share=float(v["gpt_locked_share"]),
                 val_claude_fc=float(v["claude_form_consistency"]),
                 val_gpt_fc=float(v["gpt_form_consistency"]),
                 val_claude_pos_share=float(v["claude_pos_modal_share"]),
                 val_gpt_pos_share=float(v["gpt_pos_modal_share"]),
                 val_claude_eff_identity_support=float(v["claude_eff_identity_support"]),
                 val_n_per_model=24)
        ctrl.append(c)
    ctrl.sort(key=lambda r: r["array_id"])
    asym = man["asymmetric"]

    def mean(rs, k):
        return round(sum(r[k] for r in rs) / len(rs), 4)

    bal = dict(
        n_asymmetric=len(asym), n_control=len(ctrl),
        claude_modal_share=dict(
            asymmetric=mean(asym, "claude_modal_share"),
            control_validation=round(sum(c["val_claude_share"] for c in ctrl) / len(ctrl), 4),
            note="asymmetric from confirmation n=72; control from validation n=24"),
        claude_form_consistency=dict(
            asymmetric=mean(asym, "claude_form_consistency"),
            control_validation=round(sum(c["val_claude_fc"] for c in ctrl) / len(ctrl), 4)),
        claude_eff_identity_support=dict(
            asymmetric=mean(asym, "claude_eff_identity_support"),
            control_validation=round(sum(c["val_claude_eff_identity_support"]
                                         for c in ctrl) / len(ctrl), 4)),
        mechanism=dict(
            asymmetric=dict(Counter(a["mechanism"] for a in asym)),
            control=dict(Counter(c["mechanism"] for c in ctrl))),
        family=dict(
            asymmetric=dict(Counter(a["family"] for a in asym)),
            control=dict(Counter(c["family"] for c in ctrl))),
        shortfalls=res["shortfall"] + [
            "NO numerosity control: m5_numerosity_v6 was the only shared-policy "
            "candidate in that mechanism and it FAILED validation on form consistency "
            "for both models (Claude .667, GPT .500). The asymmetric set contains 2 "
            "numerosity arrays (m5_numerosity_v2, m5_numerosity_v4) with no "
            "mechanism-matched control. Any asymmetric-vs-control interaction must be "
            "re-checked with numerosity arrays dropped.",
            "Control policy strength is measured at n=24 against the asymmetric set's "
            "n=72, so control shares are less precisely estimated and sit at a ceiling "
            "(5 of 6 at 1.000) slightly above the asymmetric mean (.962)."])

    out = dict(man)
    out.update(controls=ctrl, control_lock=keep,
               control_failed=res["failed"], control_spare=[],
               control_validation=dict(run=os.path.basename(run_dir),
                                       locked_sha=res["locked_sha"],
                                       n_pass=res["n_pass"], n_fail=res["n_fail"]),
               balance=bal, stage1_complete=True)
    p = os.path.join(P, "PILOT_MANIFEST_FINAL.json")
    json.dump(out, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    open(p + ".sha256", "w").write(h + "\n")

    print(f"locked {len(ctrl)} controls: {keep}")
    print(f"dropped: {res['failed']}\n")
    print("BALANCE  asymmetric (n=72)  vs  control (validation n=24)")
    for k in ("claude_modal_share", "claude_form_consistency", "claude_eff_identity_support"):
        b = bal[k]
        print(f"  {k:30s} {b['asymmetric']:.3f}   {b['control_validation']:.3f}")
    print(f"  mechanism asym    {bal['mechanism']['asymmetric']}")
    print(f"  mechanism control {bal['mechanism']['control']}")
    print(f"  family    control {bal['family']['control']}")
    print("\nSHORTFALLS:")
    for s in bal["shortfalls"]:
        print(f"  - {s}")
    print(f"\nfinal manifest sha256: {h}")


if __name__ == "__main__":
    main(sys.argv[1])
