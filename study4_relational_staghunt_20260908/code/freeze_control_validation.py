"""STAGE 1 - freeze the shared-policy control validation BEFORE any call is made.

Everything the validation could otherwise be tuned to after seeing data is written
here first: the 7 array ids, each model's PREDICTED modal identity (taken from
discovery, never re-derived from validation), the pass thresholds, the rule that
picks 6 + 1 spare, and the rule matching retained controls to the asymmetric set.
"""
import csv, hashlib, json, os

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANP = os.path.join(EXP, "pilot", "PILOT_MANIFEST_LOCKED.json")
OUT = os.path.join(EXP, "pilot", "CONTROL_VALIDATION_LOCKED.json")

THRESH = dict(
    modal_identity_must_equal_prediction=True,   # not re-derived from validation
    min_modal_share=0.75,                        # BOTH models
    min_form_consistency=0.80,                   # BOTH models
    max_position_modal_share=0.50,               # "primarily position-driven" bar
    require_zero_parse_failures=True,
    require_exact_permutation_balance=True,      # each of 24 perms exactly once per cell
)

SELECTION_RULE = (
    "Among arrays that PASS, retain 6 by predeclared mechanism coverage: exactly one "
    "control per mechanism for nesting, noise_texture, line_contour and numerosity, and "
    "two for mirror - mirroring the asymmetric set's composition (mirror 3/8, numerosity "
    "2/8, one each of nesting/noise_texture/line_contour). Where a mechanism has more "
    "than one passing candidate, take the one whose Claude validation modal share is "
    "closest to the asymmetric set's mean Claude modal share (.962), breaking ties by "
    "array_id ascending. A seventh passing array is retained as a locked SPARE, promoted "
    "only to fill a mechanism slot left empty by a failure. If a mechanism has no passing "
    "candidate, the slot is filled by the highest-ranked unused passing array from any "
    "mechanism and the mechanism shortfall is reported explicitly."
)

MATCHING_RULE = (
    "Retained controls are matched to the 8 asymmetric arrays on: (a) mechanism coverage "
    "as above; (b) Claude focal-policy strength - report the difference in mean Claude "
    "modal share, mean form consistency and mean effective identity support between the "
    "two item types, with no post hoc substitution to improve balance; (c) no family may "
    "supply more than 2 of the 6 controls. Balance is REPORTED, never optimised after "
    "seeing strategic data."
)


def main():
    man = json.load(open(MANP))
    ctrl = man["controls"]
    assert len(ctrl) == 7, len(ctrl)
    asym = man["asymmetric"]
    spec = dict(
        stage="control_validation",
        purpose="independent n=24 replication of the shared-policy controls, ungreened, "
                "using the existing frozen four-option coordination prompt",
        stimuli=os.path.join(EXP, "stimuli5"),
        green_used=False,
        prompt="s4_common.STAGE_A_PROMPT (four-option; binary parent 3003ae1b)",
        models=man["checkpoints"],
        n_per_cell=24, perms="all 24, each exactly once, per model per array",
        pooling="none - new timestamped run dir, never pooled with discovery5",
        thresholds=THRESH,
        selection_rule=SELECTION_RULE,
        matching_rule=MATCHING_RULE,
        asymmetric_reference=dict(
            n=len(asym), mechanisms=sorted({a["mechanism"] for a in asym}),
            mean_claude_modal_share=round(sum(a["claude_modal_share"] for a in asym) / 8, 4),
            mean_claude_form_consistency=round(sum(a["claude_form_consistency"] for a in asym) / 8, 4),
            mean_claude_eff_identity_support=round(
                sum(a["claude_eff_identity_support"] for a in asym) / 8, 4),
            mechanism_counts={m: sum(1 for a in asym if a["mechanism"] == m)
                              for m in sorted({a["mechanism"] for a in asym})}),
        candidates=[dict(
            array_id=c["array_id"], mechanism=c["mechanism"], family=c["family"],
            role=c["role"], objects=c["objects"],
            predicted_modal_index=c["claude_modal_index"],
            predicted_modal_object=c["claude_modal_object"],
            predicted_same_for_both_models=True,
            discovery_claude_share=c["claude_modal_share"],
            discovery_gpt_share=c["gpt_modal_share"],
            discovery_claude_fc=c["claude_form_consistency"],
            discovery_gpt_fc=c["gpt_form_consistency"]) for c in ctrl])
    json.dump(spec, open(OUT, "w"), indent=1)
    h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    open(OUT + ".sha256", "w").write(h + "\n")
    print(f"frozen {len(ctrl)} control candidates")
    for c in spec["candidates"]:
        print(f"  {c['array_id']:17s} {c['mechanism']:13s} predict={c['predicted_modal_object']:20s}"
              f" (idx {c['predicted_modal_index']}) [{c['role']}]")
    print(f"\nasym reference: {spec['asymmetric_reference']}")
    print(f"sha256: {h}")


if __name__ == "__main__":
    main()
