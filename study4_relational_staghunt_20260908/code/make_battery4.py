"""Study 4 four-object arrays - CROSSED-FACTOR extensions of the binary candidates.

DESIGN RULE (from STIMULUS_HUNT_PLAN.md v2 sec 4): extend a binary contrast by CROSSING A
SECOND FACTOR, never by lengthening a one-dimensional perceptual ladder. A ladder produces
endpoint-only responding - F10_curvature put 99.2% of draws on its two extreme rungs. A 2x2
factorial gives four defensible corners and, as a bonus, identifies WHICH factor a model's
convention actually tracks (its modal corner).

Every array: exactly 4 objects, all 24 position permutations, uniform panel geometry and
numeric labels, no green marker (green is assigned only after policies are measured).

Track B (focal form policy vs OTHER position policy)
  q_closure_cplx   compete/c_open_cplx  closure x complexity   - breaks a real confound
  q_nesting_weight Y7_nesting           ring count x stroke weight
  q_sizerank_shape Y17_size_rank        rank direction x element shape
  q_grain_arrange  D_density/d_texture  grain x arrangement    (CLAUDE-focal direction)
Track A (competing form policies)
  q_tone_stroke    X8_contrast          tone x stroke weight
  q_chevron_4way   A_semantic           four canonical orientations (natural 4-way set)
  q_numer_arrange  Y9_numerosity        count x arrangement

Geometry, palette and panel ground are inherited from study2_4opt make_battery.py so the
4-option runner and prompt work unchanged.
"""
import csv, hashlib, io, itertools, json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "stimuli4")

FILL, EDGE = "#9AA3B2", "#3A4152"
LIGHT, VLIGHT = "#C9CEd6", "#E8EAEE"
PANEL = "#F1F2F4"
SEED = 20260908
ASC, DESC = [.11, .16, .21, .26], [.26, .21, .16, .11]   # pitch 0.533 > max adj sum 0.47
F_LIGHT, F_DARK = "#D5D9E0", "#98A0B0"      # fill tones, both clear of PANEL
E_LIGHT, E_DARK = "#8A93A5", "#3A4152"      # edge tones
INK_TOL = (0.45, 2.10)          # per-object ink vs array mean


def _ax(ax):
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_frame_on(True)
    ax.set_facecolor(PANEL)
    return ax


# ------------------------------------------------------------------ shapes ----
def star_pts(points, r_out, r_in, rot=0.0):
    a = np.linspace(0, 2 * np.pi, points * 2, endpoint=False) + rot
    rad = np.where(np.arange(points * 2) % 2 == 0, r_out, r_in)
    return np.c_[rad * np.cos(a), rad * np.sin(a)]


def outline(ax, pts, lw, closed=True):
    p = np.vstack([pts, pts[:1]]) if closed else pts
    ax.plot(p[:, 0], p[:, 1], color=EDGE, lw=lw, solid_capstyle="round",
            solid_joinstyle="round")


def gapped(pts, gap_deg):
    """Drop the vertices whose angle falls inside a gap centred at 90 degrees."""
    if gap_deg <= 0:
        return pts, True
    ang = (np.degrees(np.arctan2(pts[:, 1], pts[:, 0])) - 90) % 360
    half = gap_deg / 2.0
    keep = ~((ang < half) | (ang > 360 - half))
    idx = np.where(keep)[0]
    # rotate so the retained run is contiguous and open
    split = np.argmax(np.diff(np.r_[idx, idx[0] + len(pts)]) > 1)
    order = np.r_[idx[split + 1:], idx[:split + 1]]
    return pts[order], False


def ring(ax, r=0.88, gap=0, lw=6, n=240):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = np.c_[r * np.cos(a), r * np.sin(a)]
    p, closed = gapped(pts, gap)
    outline(_ax(ax), p, lw, closed)


def star_outline(ax, points=12, r_out=0.92, r_in=0.55, gap=0, lw=6):
    p, closed = gapped(star_pts(points, r_out, r_in), gap)
    outline(_ax(ax), p, lw, closed)


def nested(ax, rings=4, lw=3, r0=0.88, step=0.19):
    _ax(ax)
    for i in range(rings):
        r = r0 - i * step
        if r > 0.10:
            ax.add_patch(Circle((0, 0), r, facecolor="none", edgecolor=EDGE, linewidth=lw))


TONES = ["#D5D9E0", "#B6BCC8", "#98A0B0", "#7C8698"]     # light -> dark, all clear of PANEL


def sizerank(ax, radii, tones):
    """Size gradient x tone gradient - two ordered cues of comparable salience.

    Radii and spacing are chosen so no two neighbours touch: max adjacent sum
    0.21+0.26 = 0.47 against a 0.533 pitch (asserted in main()).
    """
    _ax(ax)
    for x, r, t in zip(np.linspace(-0.80, 0.80, 4), radii, tones):
        ax.add_patch(Circle((x, 0), r, facecolor=t, edgecolor=EDGE, linewidth=2.2))


def stipple(ax, n, r, arrangement, seed):
    """Fixed disc, matched total ink; grain x arrangement."""
    _ax(ax)
    ax.add_patch(Circle((0, 0), 0.95, facecolor="white", edgecolor=EDGE, linewidth=2.4))
    lim = 0.95 - r - 0.02
    if arrangement == "random":
        rng = np.random.default_rng(seed)
        pts, tries = [], 0
        while len(pts) < n and tries < 200000:
            tries += 1
            p = rng.uniform(-lim, lim, 2)
            if np.hypot(*p) > lim:
                continue
            pts.append(p)
    else:                                          # periodic lattice
        side = int(np.ceil(np.sqrt(n / (np.pi / 4)))) + 2
        g = np.linspace(-lim, lim, side)
        pts = [(x, y) for y in g for x in g if np.hypot(x, y) <= lim]
        pts = pts[:n]
    for x, y in pts:
        ax.add_patch(Circle((x, y), r, facecolor=EDGE, edgecolor="none"))


def toned_disc(ax, fill, edge, lw=5.0):
    """Fill tone x edge tone, stroke weight held constant.

    v1 crossed tone with stroke WEIGHT; stroke was far more salient than tone, so the
    array would have been organised on stroke and the tone divergence that motivates it
    (GPT darker / Claude lighter on x8_contr_c) swamped. Both factors are now tonal.
    """
    _ax(ax).add_patch(Circle((0, 0), 0.85, facecolor=fill, edgecolor=edge, linewidth=lw))


def chevron(ax, deg, half_angle=52, L=0.95, w=0.30):
    half = np.deg2rad(half_angle)
    pts = np.array([[-L * np.sin(half), L * np.cos(half)], [0, 0],
                    [L * np.sin(half), L * np.cos(half)]])
    t = np.deg2rad(deg)
    R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    pts = pts @ R.T
    _ax(ax)
    ax.plot(pts[:, 0], pts[:, 1], color=EDGE, lw=w * 34, solid_capstyle="round",
            solid_joinstyle="round")


def elements(ax, n, arrangement, total_area=0.55):
    """Count x arrangement with total element area held constant."""
    _ax(ax)
    r = total_area / np.sqrt(n)
    if arrangement == "block":                     # compact, centred, non-overlapping
        side = int(np.ceil(np.sqrt(n)))
        pitch = 2.25 * r                           # > 2r, so neighbours never touch
        half = pitch * (side - 1) / 2.0
        g = np.linspace(-half, half, side) if side > 1 else np.array([0.0])
        pts = [(x, y) for y in g[::-1] for x in g][:n]
    else:                                          # dispersed ring
        a = np.linspace(0, 2 * np.pi, n, endpoint=False) + np.pi / 2
        pts = list(np.c_[0.86 * np.cos(a), 0.86 * np.sin(a)])
    for x, y in pts:
        ax.add_patch(Circle((x, y), r, facecolor=FILL, edgecolor=EDGE, linewidth=2.0))


# ------------------------------------------------------------------ arrays ----
# Each entry: id -> (family, mechanism, source_binary, factor_a, factor_b, [(obj_name, fn)*4])
ARRAYS = {
 "q_closure_cplx": dict(
    family="Q1_closure_complexity", mechanism="closure x complexity",
    source="c_open_cplx (compete)", track="B", factors=("closure", "complexity"),
    objects=[
      ("open_simple",   lambda ax: ring(ax, gap=70, lw=7)),
      ("closed_simple", lambda ax: ring(ax, gap=0,  lw=7)),
      ("open_complex",  lambda ax: star_outline(ax, gap=70, lw=5)),
      ("closed_complex",lambda ax: star_outline(ax, gap=0,  lw=5)),
    ]),
 "q_nesting_weight": dict(
    family="Q2_nesting_weight", mechanism="ring count x stroke weight",
    source="y7_nested_hi (Y7_nesting)", track="B", factors=("count", "weight"),
    objects=[
      ("many_thin",  lambda ax: nested(ax, rings=4, lw=3)),
      ("many_thick", lambda ax: nested(ax, rings=4, lw=6)),
      ("one_thin",   lambda ax: nested(ax, rings=1, lw=6)),
      ("one_thick",  lambda ax: nested(ax, rings=1, lw=13)),
    ]),
 "q_sizerank_tone": dict(
    family="Q3_sizerank_tone", mechanism="size-gradient direction x tone-gradient direction",
    source="y17_sizerank_hi (Y17_size_rank)", track="B", factors=("size_gradient", "tone_gradient"),
    objects=[
      ("size_up_tone_up",     lambda ax: sizerank(ax, ASC,  TONES)),
      ("size_up_tone_down",   lambda ax: sizerank(ax, ASC,  TONES[::-1])),
      ("size_down_tone_up",   lambda ax: sizerank(ax, DESC, TONES)),
      ("size_down_tone_down", lambda ax: sizerank(ax, DESC, TONES[::-1])),
    ]),
 "q_grain_arrange": dict(
    family="Q4_grain_arrangement", mechanism="grain x arrangement",
    source="d_texture (D_density)", track="B", factors=("grain", "arrangement"),
    objects=[
      ("fine_random",     lambda ax: stipple(ax, 340, .028, "random",   SEED + 1)),
      ("fine_periodic",   lambda ax: stipple(ax, 340, .028, "periodic", SEED + 1)),
      ("coarse_random",   lambda ax: stipple(ax,  85, .056, "random",   SEED + 2)),
      ("coarse_periodic", lambda ax: stipple(ax,  85, .056, "periodic", SEED + 2)),
    ]),
 "q_tone_fill_edge": dict(
    family="Q5_fill_edge_tone", mechanism="fill tone x edge tone",
    source="x8_contr_c (X8_contrast)", track="A", factors=("fill_tone", "edge_tone"),
    objects=[
      ("lightfill_lightedge", lambda ax: toned_disc(ax, F_LIGHT, E_LIGHT)),
      ("lightfill_darkedge",  lambda ax: toned_disc(ax, F_LIGHT, E_DARK)),
      ("darkfill_lightedge",  lambda ax: toned_disc(ax, F_DARK,  E_LIGHT)),
      ("darkfill_darkedge",   lambda ax: toned_disc(ax, F_DARK,  E_DARK)),
    ]),
 "q_chevron_4way": dict(
    family="Q6_chevron_orientation", mechanism="four canonical orientations",
    source="a_chev_ud (A_semantic)", track="A", factors=("orientation", "-"),
    objects=[
      ("up",    lambda ax: chevron(ax, 180)),
      ("down",  lambda ax: chevron(ax, 0)),
      ("left",  lambda ax: chevron(ax, 270)),
      ("right", lambda ax: chevron(ax, 90)),
    ]),
 "q_numer_arrange": dict(
    family="Q7_numerosity_arrangement", mechanism="count x arrangement",
    source="y9_numer_lo (Y9_numerosity)", track="A", factors=("count", "arrangement"),
    objects=[
      ("few_block",   lambda ax: elements(ax, 4, "block")),
      ("few_ring",    lambda ax: elements(ax, 4, "ring")),
      ("many_block",  lambda ax: elements(ax, 9, "block")),
      ("many_ring",   lambda ax: elements(ax, 9, "ring")),
    ]),
}


# ------------------------------------------------------------------ checks ----
def object_png(fn):
    fig, ax = plt.subplots(figsize=(3.1, 3.4), dpi=100)
    fn(ax)
    buf = io.BytesIO()
    fig.savefig(buf, facecolor="white"); plt.close(fig)
    return buf.getvalue()


def ink_fraction(png):
    import matplotlib.image as mpimg
    a = mpimg.imread(io.BytesIO(png))[:, :, :3]
    bg = np.array([int(PANEL[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return float((np.abs(a - bg).sum(axis=2) > 0.06).mean())


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def check_ground_contrast(min_delta=0.035):
    """Every declared fill tone must be clearly distinguishable from the panel ground.

    v1 used VLIGHT (#E8EAEE) against PANEL (#F1F2F4) - a delta of ~0.02, and the disc
    nearly vanished into its own panel. Caught at render review, now asserted.
    """
    g = lum(PANEL)
    bad = [(n, round(abs(lum(t) - g), 3)) for n, t in
           (("F_LIGHT", F_LIGHT), ("F_DARK", F_DARK), *((f"TONES[{i}]", t)
                                                        for i, t in enumerate(TONES)))
           if abs(lum(t) - g) < min_delta]
    assert not bad, f"fill tone(s) too close to panel ground: {bad} (min {min_delta})"


def check_no_overlap():
    """No array may contain touching or overlapping elements.

    Two separate layouts had this defect at render review - the size-rank row (largest
    neighbours merged into one blob) and the 9-element block (discs heavily overlapped).
    Both are now checked analytically before any image is written.
    """
    pitch = 1.60 / 3.0                                        # size-rank row
    for name, rr in (("ASC", ASC), ("DESC", DESC)):
        worst = max(rr[i] + rr[i + 1] for i in range(3))
        assert worst < pitch - 0.02, f"{name}: neighbours touch ({worst:.3f} vs pitch {pitch:.3f})"
    for n in (4, 9):                                          # element blocks
        r = 0.55 / np.sqrt(n)
        assert 2.25 * r > 2 * r + 0.02, f"block n={n}: elements touch"
    for n in (4, 9):                                          # element rings
        chord = 2 * 0.86 * np.sin(np.pi / n)
        r = 0.55 / np.sqrt(n)
        assert chord > 2 * r + 0.02, f"ring n={n}: elements touch ({chord:.3f} vs {2*r:.3f})"


def check_ring_counts():
    """nested() must draw exactly the requested number of rings."""
    for rings in (1, 4):
        drawn = sum(1 for i in range(rings) if 0.88 - i * 0.19 > 0.10)
        assert drawn == rings, f"nested(rings={rings}) draws {drawn}"


def render(sid, objects):
    d = os.path.join(OUT, sid)
    os.makedirs(d, exist_ok=True)
    manifest = {}
    for pi, perm in enumerate(itertools.permutations(range(4))):
        fig, axes = plt.subplots(1, 4, figsize=(12.4, 3.4), dpi=100)
        for pos, ax in enumerate(axes):
            objects[perm[pos]][1](ax)
            ax.set_title(str(pos + 1), fontsize=19, color="#222", pad=8)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.02, wspace=0.16)
        fig.savefig(os.path.join(d, f"perm{pi:02d}.png"), facecolor="white")
        plt.close(fig)
        manifest[str(pi)] = list(perm)
    json.dump(manifest, open(os.path.join(d, "manifest.json"), "w"), indent=1)
    return d


def main():
    os.makedirs(OUT, exist_ok=True)
    check_ground_contrast()
    check_no_overlap()
    check_ring_counts()
    rows, report = [], []
    for sid, spec in ARRAYS.items():
        objs = spec["objects"]
        assert len(objs) == 4, f"{sid}: needs exactly 4 objects"
        names = [o[0] for o in objs]
        assert len(set(names)) == 4, f"{sid}: duplicate object names"
        # (1) no duplicate objects
        pngs = [object_png(fn) for _, fn in objs]
        digs = [hashlib.sha256(p).hexdigest() for p in pngs]
        assert len(set(digs)) == 4, f"{sid}: two objects render identically"
        # (3) ink balance
        ink = [ink_fraction(p) for p in pngs]
        mean = sum(ink) / 4
        ratios = [i / mean for i in ink]
        bad = [(n, round(r, 2)) for n, r in zip(names, ratios)
               if not (INK_TOL[0] <= r <= INK_TOL[1])]
        assert not bad, f"{sid}: ink imbalance {bad} (tol {INK_TOL})"
        d = render(sid, objs)
        # (2) all 24 perms distinct
        ph = [hashlib.sha256(open(os.path.join(d, f"perm{i:02d}.png"), "rb").read()).hexdigest()
              for i in range(24)]
        assert len(set(ph)) == 24, f"{sid}: permutation renders collide"
        rows.append(dict(stimulus_id=sid, family=spec["family"], member=0, n_options=4,
                         n_perms=24, dir=d, batch="q1", track=spec["track"],
                         mechanism=spec["mechanism"], source_binary=spec["source"],
                         factor_a=spec["factors"][0], factor_b=spec["factors"][1],
                         objects="|".join(names),
                         ink_ratios="|".join(f"{r:.2f}" for r in ratios)))
        report.append((sid, ratios))
        print(f"  {sid:20} 4 objects, 24 perms, ink {['%.2f' % r for r in ratios]}")
    with open(os.path.join(OUT, "battery4_manifest.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda x: x["stimulus_id"]):
        for i in range(24):
            h.update(open(os.path.join(r["dir"], f"perm{i:02d}.png"), "rb").read())
    open(os.path.join(OUT, "BATTERY4_SHA256.txt"), "w").write(h.hexdigest() + "\n")
    print(f"\n{len(rows)} arrays, {24*len(rows)} images")
    print(f"battery sha256: {h.hexdigest()}")


if __name__ == "__main__":
    main()
