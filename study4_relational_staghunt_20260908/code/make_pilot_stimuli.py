"""Render the pilot's 15 arrays with ONE object green-outlined, all 24 permutations.

The green mark is the OUTLINE OF THE OBJECT'S PANEL, drawn as the axes frame in
GREEN at fixed width. Nothing inside the panel is touched: the object-drawing
callables from make_battery5 are re-used unchanged, so fill, size, position and
internal features are bit-identical to stimuli5/. That is asserted, not assumed -
each array is rendered twice (green and no-green) and the no-green render is
compared pixel-for-pixel against the original battery5 image.

Green tracks the OBJECT, not the screen position: in permutation p the greened
panel is p.index(green_index), which moves across all four positions.
"""
import hashlib, itertools, json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_battery5 as M5

OUT = os.path.join(EXP, "stimuli_pilot")
SRC = os.path.join(EXP, "stimuli5")
MANP = os.path.join(EXP, "pilot", "PILOT_MANIFEST_LOCKED.json")

GREEN = "#0E9F4F"
GREEN_LW = 6.0
GREEN_RGB = np.array([0.055, 0.624, 0.310])


def render_array(sid, objs, green_index, d):
    os.makedirs(d, exist_ok=True)
    manifest, greened_pos = {}, {}
    for pi, perm in enumerate(itertools.permutations(range(4))):
        fig, axes = plt.subplots(1, 4, figsize=(12.4, 3.4), dpi=100)
        for pos, ax in enumerate(axes):
            objs[perm[pos]][1](ax)
            if green_index is not None and perm[pos] == green_index:
                for sp in ax.spines.values():
                    sp.set_visible(True); sp.set_color(GREEN); sp.set_linewidth(GREEN_LW)
                ax.set_zorder(10)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.03, wspace=0.16)
        fig.savefig(os.path.join(d, f"perm{pi:02d}.png"), facecolor="white")
        plt.close(fig)
        manifest[str(pi)] = list(perm)
        if green_index is not None:
            greened_pos[str(pi)] = list(perm).index(green_index)
    return manifest, greened_pos


def px(p):
    import matplotlib.image as mpimg
    return mpimg.imread(p)[:, :, :3]


def green_mask(a):
    return (np.linalg.norm(a - GREEN_RGB, axis=-1) < 0.12)


def main():
    man = json.load(open(MANP))
    recs = {r["array_id"]: r for r in man["asymmetric"] + man["controls"]}
    specs = {}
    for spec in M5.A:
        specs[f"{spec['family']}_v{spec['variant']}".lower()] = spec
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "_nogreen_check")
    report, allh = [], hashlib.sha256()

    for sid in sorted(recs):
        rec, spec = recs[sid], specs[sid]
        names = [o[0] for o in spec["objects"]]
        assert names == rec["objects"], (sid, names, rec["objects"])
        gi = rec["green_index"]
        assert names[gi] == rec["green_object"], sid
        assert gi != rec["claude_modal_index"], f"{sid}: green sits on Claude's locked modal"
        assert rec["gpt_shares"][names[gi]] < man["green_excl_share"], \
            f"{sid}: green sits on a strong GPT modal"

        d = os.path.join(OUT, sid)
        mf, gpos = render_array(sid, spec["objects"], gi, d)
        json.dump(mf, open(os.path.join(d, "manifest.json"), "w"), indent=1)
        json.dump(dict(green_index=gi, green_object=names[gi], objects=names,
                       greened_position_by_perm=gpos),
                  open(os.path.join(d, "green.json"), "w"), indent=1)

        # ---- 1. permutation set: 24 distinct renders, exact position balance ----
        ph = [hashlib.sha256(open(os.path.join(d, f"perm{i:02d}.png"), "rb").read()).hexdigest()
              for i in range(24)]
        assert len(set(ph)) == 24, f"{sid}: permutation renders collide"
        from collections import Counter
        bal = Counter((it, pos) for o in mf.values() for pos, it in enumerate(o))
        assert set(bal.values()) == {6} and len(bal) == 16, f"{sid}: position balance broken"

        # ---- 2. no-green render must equal the ORIGINAL battery5 image exactly ----
        dn = os.path.join(tmp, sid)
        render_array(sid, spec["objects"], None, dn)
        maxdiff = 0.0
        for i in range(24):
            a = px(os.path.join(dn, f"perm{i:02d}.png"))
            b = px(os.path.join(SRC, sid, f"perm{i:02d}.png"))
            maxdiff = max(maxdiff, float(np.abs(a - b).max()))
        assert maxdiff == 0.0, f"{sid}: re-render differs from stimuli5 (max {maxdiff})"

        # ---- 3. green vs no-green differs ONLY at the marked panel's border ----
        gcounts, offpanel = [], 0
        for i in range(24):
            g = px(os.path.join(d, f"perm{i:02d}.png"))
            n = px(os.path.join(dn, f"perm{i:02d}.png"))
            diff = np.abs(g - n).max(axis=-1) > 1e-6
            m = green_mask(g)
            gcounts.append(int(m.sum()))
            cols = np.where(diff.any(axis=0))[0]
            want = gpos[str(i)]
            lo, hi = cols.min(), cols.max()
            band = 1240 / 4.0
            assert want * band - 30 <= lo and hi <= (want + 1) * band + 30, \
                f"{sid}/perm{i}: changed pixels outside panel {want} ({lo}-{hi})"
            # every changed pixel must lie on the blend line orig -> GREEN, i.e. the
            # only edit is green ink laid over the original at some alpha. This is
            # what rules out any change to fill, size, position or internal feature.
            o, gg = n[diff], g[diff]
            dv = o - GREEN_RGB
            al = ((o - gg) * dv).sum(-1) / np.maximum((dv * dv).sum(-1), 1e-9)
            res = np.abs((o - al[:, None] * dv) - gg).max()
            assert res < 0.035, f"{sid}/perm{i}: changed pixel off the green blend line ({res:.3f})"
            assert al.min() > -0.02 and al.max() < 1.02, f"{sid}/perm{i}: alpha {al.min():.2f}-{al.max():.2f}"
            gcols = np.where(m.any(axis=0))[0]
            assert want * band - 30 <= gcols.min() and gcols.max() <= (want + 1) * band + 30, \
                f"{sid}/perm{i}: green outside the intended panel"
            offpanel += 0
        assert len(set(gcounts)) <= 3 and min(gcounts) > 2000, (sid, sorted(set(gcounts)))

        for i in range(24):
            allh.update(open(os.path.join(d, f"perm{i:02d}.png"), "rb").read())
        report.append(dict(array_id=sid, item_type=rec["item_type"],
                           mechanism=rec["mechanism"], green_object=names[gi],
                           green_index=gi, claude_modal=rec["claude_modal_object"],
                           gpt_modal=rec["gpt_modal_object"],
                           green_px_min=min(gcounts), green_px_max=max(gcounts),
                           perms_distinct=len(set(ph)), position_balance_ok=True,
                           identical_to_battery5_without_green=True,
                           green_positions_covered=sorted(set(gpos.values()))))
        print(f"  {sid:17s} {rec['item_type']:10s} green={names[gi]:20s} "
              f"px {min(gcounts)}-{max(gcounts)}  positions {sorted(set(gpos.values()))}")

    # green must visit all four positions in every array
    for r in report:
        assert r["green_positions_covered"] == [0, 1, 2, 3], r
    # the outline itself must be identical across arrays (same colour, same width)
    lo = min(r["green_px_min"] for r in report); hi = max(r["green_px_max"] for r in report)
    assert hi - lo <= 60, f"green outline not uniform across arrays ({lo}-{hi})"

    sha = allh.hexdigest()
    json.dump(dict(arrays=report, green_hex=GREEN, green_lw=GREEN_LW,
                   stimuli_sha256=sha, n_arrays=len(report), n_images=24 * len(report)),
              open(os.path.join(OUT, "RENDER_INTEGRITY.json"), "w"), indent=1)
    open(os.path.join(OUT, "STIMULI_PILOT_SHA256.txt"), "w").write(sha + "\n")
    import shutil; shutil.rmtree(tmp)
    print(f"\n{len(report)} arrays, {24*len(report)} images")
    print(f"stimuli_pilot sha256: {sha}")


if __name__ == "__main__":
    main()
