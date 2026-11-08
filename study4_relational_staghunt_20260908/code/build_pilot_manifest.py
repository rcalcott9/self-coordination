"""Claude-focal relational pilot - FROZEN MANIFEST builder.

Resolves the asymmetric set from the n=72 CONFIRMATION run (never from discovery),
selects shared-policy controls from the battery5 discovery inventory, assigns green
under a seeded draw, and writes PILOT_MANIFEST_LOCKED.json + .sha256.

No API calls. Nothing outside pilot/ is written.

GREEN EXCLUSION RULE (stricter than the brief, deliberately). The brief says "exclude
GPT's strong modal identity when GPT has one". Implemented as: exclude any object
carrying >= GREEN_EXCL_SHARE of EITHER model's measured mass. Rationale - green pays 5
not 10, so marking an object distorts whoever was choosing it. If green sat on GPT's
modal, the OTHER condition would measure Claude best-responding to a GPT policy we had
ourselves perturbed. The bar is set at chance+.10 rather than .75 for that reason.
"""
import csv, hashlib, json, os, random

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(EXP, "confirm5_20260909_012018", "confirmation5_results.csv")
DISC = os.path.join(EXP, "discovery5_20260909_011211", "discovery5_inventory.csv")
TRACKS = os.path.join(EXP, "discovery5_20260909_011211", "discovery5_tracks.csv")
BAT = os.path.join(EXP, "stimuli5", "battery5_manifest.csv")
OUT = os.path.join(EXP, "pilot")

GREEN_SEED = 20260908
GREEN_EXCL_SHARE = 0.35          # chance is .25; .35 = "carries real mass"

# Controls, chosen BEFORE any strategic data exists, to span every mechanism in the
# asymmetric set. mirror x2 mirrors the asymmetric set's mirror-heavy composition.
CONTROL_LOCK = ["m1_nesting_v4", "m2_texture_v0", "m3_mirror_v3",
                "m3_mirror_v6", "m4_contour_v0", "m5_numerosity_v6"]
CONTROL_SPARE = ["m2_texture_v1"]        # validated too; promoted only if one above fails


def counts_to_shares(js):
    c = {int(k): v for k, v in json.loads(js).items()}
    n = sum(c.values())
    return {k: v / n for k, v in c.items()}, n


def main():
    os.makedirs(OUT, exist_ok=True)
    bat = {r["array_id"]: r for r in csv.DictReader(open(BAT))}
    disc = {r["array_id"]: r for r in csv.DictReader(open(DISC))}
    tracks = {r["array_id"]: r for r in csv.DictReader(open(TRACKS))}
    conf = list(csv.DictReader(open(CONF)))

    # ---------------------------------------------------------------- asymmetric --
    asym = []
    for r in conf:
        if r["CONFIRMED"] != "1" or r["focal_model"] != "claude":
            continue
        sid = r["array_id"]
        names = bat[sid]["objects"].split("|")
        assert len(names) == 4, (sid, names)
        c_share, c_n = counts_to_shares(r["focal_counts"])
        g_share, g_n = counts_to_shares(r["other_counts"])
        c_idx = int(r["locked_focal_index"])
        assert names[c_idx] == r["locked_focal_object"], (sid, names, r["locked_focal_object"])
        assert c_n == g_n == 72, (sid, c_n, g_n)          # independent confirmation, not discovery
        g_idx = max(g_share, key=g_share.get)
        asym.append(dict(
            array_id=sid, item_type="asymmetric", family=bat[sid]["family"],
            mechanism=r["mechanism"], objects=names,
            claude_modal_index=c_idx, claude_modal_object=r["locked_focal_object"],
            claude_modal_share=float(r["conf_focal_share"]),
            claude_form_consistency=float(r["conf_focal_fc"]),
            claude_pos_modal_share=float(r["conf_focal_pos_share"]),
            claude_eff_identity_support=float(r["conf_focal_identity_match"]),
            gpt_modal_index=g_idx, gpt_modal_object=names[g_idx],
            gpt_modal_share=float(r["conf_other_share"]),
            gpt_pos_modal_share=float(r["conf_other_pos_share"]),
            gpt_policy_subtype=r["locked_other_policy"],
            cross_model_identity_match=float(r["conf_cross_model_match"]),
            claude_shares={names[i]: round(c_share.get(i, 0.0), 4) for i in range(4)},
            gpt_shares={names[i]: round(g_share.get(i, 0.0), 4) for i in range(4)},
            evidence="confirm5_20260909_012018 n=72 per model (independent of discovery5)",
            n_claude=72, n_gpt=72))

    assert len(asym) == 8, f"expected 8 Claude-focal confirmed entries, got {len(asym)}"
    assert len({a['array_id'] for a in asym}) == 8, "asymmetric arrays not distinct"
    mechs = sorted({a["mechanism"] for a in asym})
    assert len(mechs) == 5, (len(mechs), mechs)
    # m4_contour_v4 is ONE physical array that also supports a GPT-focal entry
    dual = [r for r in conf if r["array_id"] == "m4_contour_v4" and r["CONFIRMED"] == "1"]
    assert len(dual) == 2 and {d["focal_model"] for d in dual} == {"claude", "gpt"}

    # ------------------------------------------------------------------ controls --
    ctrl = []
    for sid in CONTROL_LOCK + CONTROL_SPARE:
        d, t = disc[sid], tracks[sid]
        names = bat[sid]["objects"].split("|")
        assert t["shared_control_075"] in ("1", "True", "TRUE"), sid
        gi, ci = int(d["gpt_obj_modal"]), int(d["claude_obj_modal"])
        assert gi == ci, f"{sid}: modal identities differ ({gi} vs {ci})"
        gs, cs = float(d["gpt_obj_modal_share"]), float(d["claude_obj_modal_share"])
        gf, cf = float(d["gpt_form_consistency"]), float(d["claude_form_consistency"])
        assert gs >= .75 and cs >= .75, (sid, gs, cs)
        assert gf >= .80 and cf >= .80, (sid, gf, cf)
        assert d["gpt_policy_type"] != "position" and d["claude_policy_type"] != "position", sid
        c_share, _ = counts_to_shares(d["claude_item_counts"])
        g_share, _ = counts_to_shares(d["gpt_item_counts"])
        ctrl.append(dict(
            array_id=sid, item_type="control",
            role="locked" if sid in CONTROL_LOCK else "spare",
            family=bat[sid]["family"], mechanism=d["mechanism"], objects=names,
            claude_modal_index=ci, claude_modal_object=names[ci],
            claude_modal_share=cs, claude_form_consistency=cf,
            claude_pos_modal_share=float(d["claude_pos_modal_share"]),
            claude_eff_identity_support=float(d["claude_identity_match"]),
            gpt_modal_index=gi, gpt_modal_object=names[gi], gpt_modal_share=gs,
            gpt_form_consistency=gf, gpt_pos_modal_share=float(d["gpt_pos_modal_share"]),
            gpt_policy_subtype="shared_convention",
            cross_model_identity_match=float(d["cross_model_identity_match"]),
            claude_shares={names[i]: round(c_share.get(i, 0.0), 4) for i in range(4)},
            gpt_shares={names[i]: round(g_share.get(i, 0.0), 4) for i in range(4)},
            evidence="discovery5_20260909_011211 n=24 per model - DISCOVERY ONLY, "
                     "requires the pilot's own independent validation run before locking",
            validated=False, n_claude=24, n_gpt=24))

    # --------------------------------------------------------------- green draw --
    rng = random.Random(GREEN_SEED)
    for rec in asym + ctrl:                       # deterministic order = sorted array_id
        pass
    for rec in sorted(asym, key=lambda r: r["array_id"]) + \
               sorted(ctrl, key=lambda r: r["array_id"]):
        names = rec["objects"]
        excl, why = set(), {}
        excl.add(rec["claude_modal_index"]); why[rec["claude_modal_index"]] = "claude_locked_modal"
        for i, nm in enumerate(names):
            if rec["gpt_shares"].get(nm, 0) >= GREEN_EXCL_SHARE:
                excl.add(i); why.setdefault(i, f"gpt_share_{rec['gpt_shares'][nm]:.3f}_ge_{GREEN_EXCL_SHARE}")
            if rec["claude_shares"].get(nm, 0) >= GREEN_EXCL_SHARE and i not in excl:
                excl.add(i); why.setdefault(i, f"claude_share_{rec['claude_shares'][nm]:.3f}_ge_{GREEN_EXCL_SHARE}")
        elig = [i for i in range(4) if i not in excl]
        assert elig, f"{rec['array_id']}: no green-eligible object"
        g = rng.choice(sorted(elig))
        rec.update(green_index=g, green_object=names[g],
                   green_eligible_indices=sorted(elig),
                   green_eligible_objects=[names[i] for i in sorted(elig)],
                   green_excluded={names[i]: why[i] for i in sorted(excl)},
                   green_seed=GREEN_SEED, green_rule=f"exclude claude locked modal + any "
                                                     f"object >= {GREEN_EXCL_SHARE} of either model")
        assert g != rec["claude_modal_index"], rec["array_id"]
        assert rec["gpt_shares"][names[g]] < GREEN_EXCL_SHARE, rec["array_id"]

    man = dict(
        pilot="claude_focal_relational_pilot",
        built_utc=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
        checkpoints=dict(claude="claude-opus-5", gpt="gpt-5.5-2026-04-23"),
        green_seed=GREEN_SEED, green_excl_share=GREEN_EXCL_SHARE,
        asymmetric=sorted(asym, key=lambda r: r["array_id"]),
        controls=sorted(ctrl, key=lambda r: r["array_id"]),
        control_lock=CONTROL_LOCK, control_spare=CONTROL_SPARE,
        provenance=dict(confirmation=CONF, discovery=DISC, battery=BAT))
    p = os.path.join(OUT, "PILOT_MANIFEST_LOCKED.json")
    json.dump(man, open(p, "w"), indent=1, sort_keys=False)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    open(p + ".sha256", "w").write(h + "\n")

    print(f"asymmetric : {len(asym)} arrays / {len(mechs)} mechanisms {mechs}")
    for a in sorted(asym, key=lambda r: r["array_id"]):
        print(f"  {a['array_id']:17s} {a['mechanism']:13s} claude={a['claude_modal_object']:20s}"
              f" sh={a['claude_modal_share']:.3f} fc={a['claude_form_consistency']:.2f}"
              f" | gpt={a['gpt_modal_object']:20s} sh={a['gpt_modal_share']:.3f}"
              f" {a['gpt_policy_subtype']:26s} | GREEN={a['green_object']}"
              f" (of {len(a['green_eligible_indices'])})")
    print(f"\ncontrols   : {len(CONTROL_LOCK)} locked + {len(CONTROL_SPARE)} spare")
    for c in sorted(ctrl, key=lambda r: r["array_id"]):
        print(f"  {c['array_id']:17s} {c['mechanism']:13s} shared={c['claude_modal_object']:20s}"
              f" c_sh={c['claude_modal_share']:.3f} g_sh={c['gpt_modal_share']:.3f}"
              f" c_fc={c['claude_form_consistency']:.2f} g_fc={c['gpt_form_consistency']:.2f}"
              f" [{c['role']}] | GREEN={c['green_object']}"
              f" (of {len(c['green_eligible_indices'])})")
    print(f"\nmanifest sha256: {h}")


if __name__ == "__main__":
    main()
