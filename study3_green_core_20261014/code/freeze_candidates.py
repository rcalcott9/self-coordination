"""Freeze the existing GREEN-game candidates BEFORE any new outcome exists. Reads only the archived manifest,
run spec and stimulus files; never opens pilot responses. Old labels are kept as HISTORICAL STRATA, not as
properties of the current game. No candidate is dropped here or later because its new measurements disagree
with its old label.

Also re-checks m3_mirror_v6: the archived renderer (make_pilot_stimuli.render_array + make_battery5 object
callables) reproduces the archived greened images pixel-for-pixel. The PNG bytes differ (encoder metadata),
so the ARCHIVED files, by sha256, are the stimuli; re-renders are a check only.
"""
import hashlib, json, os, sys, tempfile
S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study4_relational_staghunt_20260908"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    man = json.load(open(os.path.join(S4, "pilot", "PILOT_MANIFEST_FINAL.json")))
    run = json.load(open(os.path.join(S4, "pilot", "STRATEGIC_RUN_LOCKED.json")))
    recs = {r["array_id"]: r for r in man["asymmetric"] + man["controls"]}
    assert sorted(run["arrays"]) == sorted(recs), "pilot arrays != manifest records"
    items = []
    for sid in sorted(run["arrays"]):
        r, d = recs[sid], os.path.join(S4, "stimuli_pilot", sid)
        g = json.load(open(os.path.join(d, "green.json")))
        assert g["green_index"] == r["green_index"] and g["objects"] == r["objects"], sid
        items.append(dict(
            array_id=sid, objects=r["objects"], green_index=r["green_index"], green_object=r["green_object"],
            historical_stratum=r["item_type"], historical_mechanism=r["mechanism"],
            historical_label_source=r["evidence"] + ("; ctrlval " + r["validation_run"] if r.get("validation_run") else ""),
            historical_label_prompt="s4_common.STAGE_A_PROMPT d40ea45d (pure coordination with a copy, no green, no payoffs)",
            perm_png_sha256=[sha(os.path.join(d, f"perm{i:02d}.png")) for i in range(24)],
            manifest_sha256=sha(os.path.join(d, "manifest.json")), green_json_sha256=sha(os.path.join(d, "green.json"))))
    # m3_mirror_v6 restoration check
    sys.path.insert(0, os.path.join(S4, "code"))
    import numpy as np, make_pilot_stimuli as G, make_battery5 as M5
    spec = [s for s in M5.A if f"{s['family']}_v{s['variant']}".lower() == "m3_mirror_v6"][0]
    arch = os.path.join(S4, "stimuli_pilot", "m3_mirror_v6")
    with tempfile.TemporaryDirectory() as t:
        mf, gp = G.render_array("m3_mirror_v6", spec["objects"], 3, t)
        maxdiff = max(float(np.abs(G.px(f"{t}/perm{i:02d}.png") - G.px(f"{arch}/perm{i:02d}.png")).max()) for i in range(24))
    restore = dict(array_id="m3_mirror_v6", objects=[o[0] for o in spec["objects"]], cue_rules=spec.get("rules"),
                   green_index=3, green_object="sym2",
                   manifest_identical=mf == json.load(open(f"{arch}/manifest.json")),
                   green_positions_identical=gp == json.load(open(f"{arch}/green.json"))["greened_position_by_perm"],
                   max_pixel_diff=maxdiff, png_bytes_identical=False,
                   use="archived PNG files by sha256; re-render is a check only")
    assert restore["manifest_identical"] and restore["green_positions_identical"] and maxdiff == 0.0
    out = dict(frozen_utc=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
               note="frozen before any new GREEN-core outcome; pilot responses not opened by this script",
               source_manifest_sha256=sha(os.path.join(S4, "pilot", "PILOT_MANIFEST_FINAL.json")),
               source_run_spec_sha256=sha(os.path.join(S4, "pilot", "STRATEGIC_RUN_LOCKED.json")),
               green_hex="#0E9F4F", green_lw=6.0, items=items, m3_mirror_v6_restore=restore,
               not_in_pilot=dict(m5_numerosity_v6="failed ctrlval form consistency before the pilot (not an outcome-based drop); rendered in stimuli_pilot but never run",
                                 m2_texture_v1="validated spare; never promoted or run"))
    p = os.path.join(HERE, "FROZEN_CANDIDATES.json")
    json.dump(out, open(p, "w"), indent=1)
    open(p + ".sha256", "w").write(sha(p) + "\n")
    print(len(items), "items frozen;", restore, "\nsha256", sha(p))


if __name__ == "__main__":
    main()
