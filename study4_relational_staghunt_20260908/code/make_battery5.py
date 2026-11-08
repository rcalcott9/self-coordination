"""Study 4 CUE-CONFLICT battery - 6 mechanisms x 7 variants = 42 four-object arrays.

CONSTRUCTION PRINCIPLE (from Phase 1). The four-option arrays that already produce the
target asymmetry are the NEAR-EQUIVALENCE families - fam_noise ("no focal point by
construction"), fam_mirror ("the same form up to isometry"), F27_linecount, F36_split.
The q_* factorial arrays failed because each had one corner that dominated every dimension
(closed_simple, one_thick, darkfill_darkedge) and both models simply took it.

So: no ladders, no dominant corner. Each array carries an explicit CUE TABLE naming the
plausible rules in play and which object each rule favours. Every object must win at least
one rule and no object may win more than two - asserted at build time.

Palette, panel ground and render format are inherited from study2_4opt/make_battery.py.
No labels, no letters, no green, no position cues.
"""
import csv, hashlib, io, itertools, json, os
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "stimuli5")
FILL, EDGE, PANEL = "#9AA3B2", "#3A4152", "#F1F2F4"
SEED = 20260909
INK_TOL = (0.35, 2.60)          # wider than battery4: ink IS an intended cue in some arrays


def _ax(ax):
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.set_frame_on(True); ax.set_facecolor(PANEL)
    return ax


# ---------------------------------------------------------------- primitives --
def rings(ax, n, lw, r0=0.92, spacing="even", jit=0.0):
    _ax(ax)
    if spacing == "even":
        rr = np.linspace(r0, r0 - 0.19 * (n - 1), n) if n > 1 else [r0]
    else:                                            # geometric = uneven
        rr = [r0 * (0.62 ** i) for i in range(n)]
    rng = np.random.default_rng(SEED + int(100 * r0) + n)
    for r in rr:
        r = r + (rng.uniform(-jit, jit) if jit else 0.0)
        if r > 0.09:
            ax.add_patch(Circle((0, 0), r, facecolor="none", edgecolor=EDGE, linewidth=lw))


def patch(ax, n, r, mode, seed, boundary=True):
    _ax(ax)
    if boundary:
        ax.add_patch(Circle((0, 0), 0.95, facecolor="white", edgecolor=EDGE, linewidth=2.4))
    lim = 0.95 - r - 0.02
    rng = np.random.default_rng(seed)
    if mode == "random":
        pts = []
        while len(pts) < n:
            p = rng.uniform(-lim, lim, 2)
            if np.hypot(*p) <= lim: pts.append(p)
    elif mode == "lattice":
        side = int(np.ceil(np.sqrt(n / (np.pi / 4)))) + 2
        g = np.linspace(-lim, lim, side)
        pts = [(x, y) for y in g for x in g if np.hypot(x, y) <= lim][:n]
    else:                                            # clustered
        pts = []
        cen = rng.uniform(-lim * 0.45, lim * 0.45, (3, 2))
        while len(pts) < n:
            p = cen[rng.integers(3)] + rng.normal(0, lim * 0.22, 2)
            if np.hypot(*p) <= lim: pts.append(p)
    for x, y in pts:
        ax.add_patch(Circle((x, y), r, facecolor=EDGE, edgecolor="none"))


def symshape(ax, fold, seed, scale=0.92, wobble=0.20):
    """k-fold symmetric outline; fold=1 gives an asymmetric blob."""
    _ax(ax)
    rng = np.random.default_rng(seed)
    a = np.linspace(0, 2 * np.pi, 360, endpoint=False)
    r = np.ones_like(a)
    if fold == 1:
        for k, amp in ((2, .20), (3, .13), (5, .08)):
            r += amp * np.sin(k * a + rng.uniform(0, 2 * np.pi))
    else:
        for h in range(1, 4):
            r += (wobble / h) * np.cos(fold * h * a + rng.uniform(0, 2 * np.pi) * 0)
    r = scale * r / r.max()
    ax.add_patch(Polygon(np.c_[r * np.cos(a), r * np.sin(a)], closed=True,
                         facecolor=FILL, edgecolor=EDGE, linewidth=2.5))


def twin(ax, seed, mirrored, gap=0.46, scale=0.44):
    """Two small components side by side; mirrored or translated copies."""
    _ax(ax)
    rng = np.random.default_rng(seed)
    a = np.linspace(0, 2 * np.pi, 240, endpoint=False)
    r = np.ones_like(a)
    for k, amp in ((2, .22), (3, .14), (5, .09)):
        r += amp * np.sin(k * a + rng.uniform(0, 2 * np.pi))
    r = scale * r / r.max()
    base = np.c_[r * np.cos(a), r * np.sin(a)]
    for s, dx in ((1, -gap), (-1 if mirrored else 1, gap)):
        ax.add_patch(Polygon(base * [s, 1] + [dx, 0], closed=True,
                             facecolor=FILL, edgecolor=EDGE, linewidth=2.2))


def strokes(ax, kind, n=3, lw=6):
    """Line/contour objects: components, continuity, closure, intersections."""
    _ax(ax)
    t = np.linspace(0, 1, 200)
    if kind == "segments":
        ys = np.linspace(0.62, -0.62, n)
        for y in ys:
            ax.plot([-0.82, 0.82], [y, y], color=EDGE, lw=lw, solid_capstyle="round")
    elif kind == "continuous":
        a = np.linspace(-np.pi * 0.95, np.pi * 0.95, 300)
        ax.plot(0.82 * np.cos(a), 0.72 * np.sin(a * 1.0), color=EDGE, lw=lw,
                solid_capstyle="round")
    elif kind == "closed":
        a = np.linspace(0, 2 * np.pi, 300)
        ax.plot(0.80 * np.cos(a), 0.80 * np.sin(a), color=EDGE, lw=lw)
    elif kind == "crossing":
        for ang in np.linspace(0, np.pi, n, endpoint=False):
            ax.plot([-0.85 * np.cos(ang), 0.85 * np.cos(ang)],
                    [-0.85 * np.sin(ang), 0.85 * np.sin(ang)],
                    color=EDGE, lw=lw, solid_capstyle="round")
    elif kind == "zigzag":
        x = np.linspace(-0.85, 0.85, n + 1)
        y = np.array([0.55 if i % 2 else -0.55 for i in range(n + 1)])
        ax.plot(x, y, color=EDGE, lw=lw, solid_capstyle="round", solid_joinstyle="round")
    elif kind == "arcs":
        for i, dy in enumerate(np.linspace(0.5, -0.5, n)):
            a = np.linspace(-1.1, 1.1, 120)
            ax.plot(0.8 * np.sin(a), dy + 0.30 * np.cos(a), color=EDGE, lw=lw,
                    solid_capstyle="round")


def group(ax, n, arrangement, r=None, seed=SEED):
    """Element radius is CAPPED and placement radius adapts to it.

    Ink-matching alone (r = 0.55/sqrt(n)) gives r = 0.39 at n = 2, and a row at +-0.80
    then runs to 1.19 against an axes limit of 1.2 - clipped at the panel edge. Count is
    an intended cue here, so a small ink imbalance at low n is accepted; clipping is not.
    """
    _ax(ax)
    r = r if r is not None else min(0.30, 0.55 / np.sqrt(n))
    place = min(0.80, 1.06 - r)
    if arrangement == "row":
        # a row of n across +-place has pitch 2*place/(n-1); shrink r so neighbours
        # never touch. Without this, n>=5 rows render as a chain of merged discs.
        r = min(r, 2 * place / ((n - 1) * 2.15)) if n > 1 else r
        place = min(0.80, 1.06 - r)
    if arrangement == "ring":
        a = np.linspace(0, 2 * np.pi, n, endpoint=False) + np.pi / 2
        pts = np.c_[place * np.cos(a), place * np.sin(a)]
    elif arrangement == "row":
        pts = np.c_[np.linspace(-place, place, n), np.zeros(n)]
    elif arrangement == "block":
        side = int(np.ceil(np.sqrt(n))); pitch = 2.35 * r
        g = np.linspace(-pitch * (side - 1) / 2, pitch * (side - 1) / 2, side)
        pts = [(x, y) for y in g[::-1] for x in g][:n]
    else:                                            # scatter
        rng = np.random.default_rng(seed); pts = []; tries = 0
        lim = min(0.78, 1.06 - r)
        while len(pts) < n and tries < 200000:
            tries += 1
            p = rng.uniform(-lim, lim, 2)
            if np.hypot(*p) <= lim and all(np.hypot(*(p - q)) > 2.15 * r for q in pts):
                pts.append(p)
        assert len(pts) == n, f"scatter n={n} could not be placed without overlap"
    pts = [tuple(p) for p in pts]
    for i in range(len(pts)):                      # hard no-overlap assertion
        for j in range(i + 1, len(pts)):
            d = np.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
            assert d > 2 * r + 0.005, (f"group(n={n},{arrangement}): elements overlap "
                                       f"(gap {d:.3f} vs 2r {2*r:.3f})")
    for x, y in pts:
        ax.add_patch(Circle((x, y), r, facecolor=FILL, edgecolor=EDGE, linewidth=2.0))


TONES = ["#D5D9E0", "#B6BCC8", "#98A0B0", "#7C8698"]


def row(ax, radii, tones=None, centre_big=False):
    _ax(ax)
    tones = tones or [FILL] * 4
    xs = np.linspace(-0.80, 0.80, 4)
    for x, rr, t in zip(xs, radii, tones):
        ax.add_patch(Circle((x, 0), rr, facecolor=t, edgecolor=EDGE, linewidth=2.2))


# ===================== ARRAYS: 6 mechanisms x 7 variants ======================
# Each entry: (variant_id, [(obj_name, draw_fn) x4], {rule_name: winning_obj_index})
# Rules are the plausible focal conventions a model might run. Build-time assertion:
# every object wins >= 1 rule, no object wins > 2.
A = []


def add(mech, family, variant, objs, rules, note):
    A.append(dict(mechanism=mech, family=family, variant=variant, objects=objs,
                  rules=rules, note=note))


# ---- M1 nesting: ring count / stroke weight / enclosure / spacing regularity --
NEST = [  # (n,lw,spacing,r0) x4  then rule winners
 ((2,3,"even",.92),(5,3,"even",.92),(3,10,"even",.92),(3,3,"geom",.92),
  dict(fewest_rings=0, most_rings=1, thickest_stroke=2, uneven_nesting=3, most_regular=1)),
 ((1,4,"even",.92),(6,3,"even",.92),(3,11,"even",.70),(4,3,"geom",.92),
  dict(fewest_rings=0, most_rings=1, thickest_stroke=2, smallest_extent=2, uneven_nesting=3)),
 ((2,3,"geom",.92),(4,4,"even",.92),(3,12,"even",.92),(7,2,"even",.92),
  dict(fewest_rings=0, uneven_nesting=0, mid_count=1, thickest_stroke=2, most_rings=3,
       thinnest_stroke=3)),
 ((3,3,"even",.62),(3,3,"even",.98),(5,5,"geom",.92),(2,9,"even",.92),
  dict(smallest_extent=0, largest_extent=1, most_rings=2, uneven_nesting=2, thickest_stroke=3)),
 ((4,3,"even",.92),(2,3,"even",.92),(4,8,"geom",.92),(3,3,"even",.55),
  dict(most_rings=0, most_regular=0, fewest_rings=1, thickest_stroke=2, smallest_extent=3)),
 ((5,2,"even",.92),(3,7,"even",.92),(2,3,"geom",.78),(4,3,"even",.66),
  dict(most_rings=0, thinnest_stroke=0, thickest_stroke=1, fewest_rings=2, smallest_extent=3)),
 ((3,3,"even",.92),(3,9,"geom",.92),(6,3,"even",.92),(2,3,"even",.72),
  dict(most_regular=0, thickest_stroke=1, uneven_nesting=1, most_rings=2, fewest_rings=3)),
]
for v, spec in enumerate(NEST):
    ps, rules = spec[:4], spec[4]
    add("nesting", "M1_nesting", v,
        [(f"n{p[0]}_lw{p[1]}_{p[2]}_r{int(p[3]*100)}",
          (lambda ax, p=p: rings(ax, p[0], p[1], p[3], p[2]))) for p in ps],
        rules, "ring count vs stroke weight vs extent vs spacing regularity")

# ---- M2 noise / texture -------------------------------------------------------
TEX = [  # (n, r, mode, boundary) x4
 ((60,.055,"random",True),(240,.028,"random",True),(150,.036,"lattice",True),(150,.036,"clustered",True),
  dict(sparsest=0, coarsest_grain=0, densest=1, finest_grain=1, most_regular=2, most_clustered=3)),
 ((110,.042,"lattice",True),(110,.042,"random",True),(40,.070,"random",True),(300,.024,"clustered",True),
  dict(most_regular=0, mid_random=1, sparsest=2, coarsest_grain=2, densest=3, most_clustered=3)),
 ((90,.046,"random",False),(90,.046,"lattice",True),(200,.030,"random",True),(45,.062,"clustered",True),
  dict(no_boundary=0, most_regular=1, densest=2, sparsest=3, most_clustered=3)),
 ((160,.034,"lattice",True),(60,.056,"lattice",True),(160,.034,"random",True),(160,.034,"clustered",True),
  dict(dense_regular=0, sparsest=1, coarsest_grain=1, most_random=2, most_clustered=3)),
 ((70,.050,"clustered",True),(280,.026,"lattice",True),(120,.040,"random",True),(70,.050,"random",False)),
 ((200,.031,"random",True),(160,.034,"lattice",True),(90,.052,"clustered",True),(60,.038,"random",False)),
 ((130,.038,"lattice",False),(130,.038,"clustered",True),(55,.058,"random",True),(260,.027,"random",True)),
]
TEXRULES = [None, None, None, None,
 dict(most_clustered=0, densest=1, most_regular=1, mid_random=2, coarsest_grain=0, no_boundary=3),
 dict(densest=0, finest_grain=0, most_regular=1, coarsest_grain=2, most_clustered=2,
      sparsest=3, no_boundary=3),
 dict(most_regular=0, no_boundary=0, most_clustered=1, sparsest=2, coarsest_grain=2, densest=3)]
for v, spec in enumerate(TEX):
    ps = spec[:4]
    rules = spec[4] if len(spec) > 4 else TEXRULES[v]
    add("noise_texture", "M2_texture", v,
        [(f"n{p[0]}_r{int(p[1]*1000)}_{p[2]}{'_nb' if not p[3] else ''}",
          (lambda ax, p=p, i=i: patch(ax, p[0], p[1], p[2], SEED + 700 + v * 4 + i, p[3])))
         for i, p in enumerate(ps)],
        rules, "grain vs density vs global regularity vs boundary clarity")

# ---- M3 mirror structure ------------------------------------------------------
MIR = [  # ('sym',fold) or ('twin',mirrored)
 (("sym",1),("sym",2),("twin",True),("twin",False),
  dict(most_irregular=0, bilateral_symmetry=1, mirrored_pair=2, most_compact=1, repeated_pair=3)),
 (("sym",2),("sym",4),("twin",True),("sym",1),
  dict(bilateral_symmetry=0, most_symmetric=1, most_compact=1, mirrored_pair=2, most_irregular=3)),
 (("twin",False),("sym",3),("sym",1),("twin",True),
  dict(repeated_pair=0, threefold_symmetry=1, most_compact=1, most_irregular=2, mirrored_pair=3)),
 (("sym",1),("sym",6),("twin",True),("sym",2),
  dict(most_irregular=0, most_symmetric=1, mirrored_pair=2, bilateral_symmetry=3, most_compact=3)),
 (("twin",True),("twin",False),("sym",2),("sym",1),
  dict(mirrored_pair=0, repeated_pair=1, bilateral_symmetry=2, most_compact=2, most_irregular=3)),
 (("sym",4),("sym",1),("twin",False),("sym",3),
  dict(most_symmetric=0, most_compact=0, most_irregular=1, repeated_pair=2, threefold_symmetry=3)),
 (("sym",3),("twin",True),("sym",1),("sym",2),
  dict(threefold_symmetry=0, mirrored_pair=1, most_irregular=2, bilateral_symmetry=3, most_compact=3)),
]
for v, spec in enumerate(MIR):
    ps, rules = spec[:4], spec[4]
    def mk(p, i, v=v):
        if p[0] == "sym":
            return (lambda ax, p=p, i=i: symshape(ax, p[1], SEED + 900 + v * 4 + i))
        return (lambda ax, p=p, i=i: twin(ax, SEED + 900 + v * 4 + i, p[1]))
    add("mirror", "M3_mirror", v,
        [(f"{p[0]}{p[1]}", mk(p, i)) for i, p in enumerate(ps)], rules,
        "global symmetry vs mirrored components vs compactness vs irregularity")

# ---- M4 line count / contour --------------------------------------------------
LIN = [  # (kind, n, lw)
 (("segments",2,7),("segments",5,4),("closed",1,7),("crossing",3,6),
  dict(fewest_components=0, most_components=1, only_closed=2, most_intersections=3, thickest=0)),
 (("continuous",1,7),("segments",4,5),("crossing",4,5),("closed",1,10),
  dict(single_continuous=0, most_components=1, most_intersections=2, only_closed=3, thickest=3)),
 (("zigzag",5,6),("segments",2,8),("closed",1,6),("arcs",4,5),
  dict(most_direction_changes=0, fewest_components=1, thickest=1, only_closed=2, most_curved=3)),
 (("closed",1,6),("crossing",5,4),("continuous",1,8),("segments",3,6),
  dict(only_closed=0, most_intersections=1, single_continuous=2, thickest=2, mid_components=3)),
 (("segments",6,3),("continuous",1,9),("crossing",2,7),("closed",1,6),
  dict(most_components=0, single_continuous=1, thickest=1, most_intersections=2, only_closed=3)),
 (("arcs",3,6),("closed",1,7),("zigzag",6,5),("segments",2,7),
  dict(most_curved=0, only_closed=1, most_direction_changes=2, fewest_components=3, most_components=2)),
 (("crossing",4,5),("segments",3,6),("continuous",1,8),("arcs",5,4),
  dict(most_intersections=0, mid_components=1, single_continuous=2, thickest=2, most_curved=3)),
]
for v, spec in enumerate(LIN):
    ps, rules = spec[:4], spec[4]
    add("line_contour", "M4_contour", v,
        [(f"{p[0]}{p[1]}_lw{p[2]}", (lambda ax, p=p: strokes(ax, p[0], p[1], p[2])))
         for p in ps], rules,
        "component count vs continuity vs closure vs curvature vs intersections")

# ---- M5 numerosity / arrangement ---------------------------------------------
NUM = [  # (n, arrangement)
 ((3,"scatter"),(8,"scatter"),(5,"ring"),(4,"block"),
  dict(fewest=0, most=1, most_regular_spacing=2, symmetric_global_shape=3, most_scattered=1)),
 ((6,"ring"),(3,"block"),(9,"scatter"),(6,"row"),
  dict(most_regular_spacing=0, fewest=1, symmetric_global_shape=1, most=2, most_scattered=2, linear=3)),
 ((4,"ring"),(7,"row"),(4,"scatter"),(10,"block"),
  dict(symmetric_global_shape=0, most_regular_spacing=0, linear=1, most_scattered=2, most=3)),
 ((5,"block"),(2,"row"),(8,"ring"),(5,"scatter"),
  dict(compact_block=0, fewest=1, linear=1, most=2, most_regular_spacing=2, most_scattered=3)),
 ((9,"ring"),(4,"row"),(6,"scatter"),(3,"block"),
  dict(most=0, most_regular_spacing=0, linear=1, most_scattered=2, fewest=3, compact_block=3)),
 ((6,"block"),(11,"scatter"),(4,"ring"),(2,"scatter"),
  dict(compact_block=0, most=1, most_scattered=1, symmetric_global_shape=2, fewest=3)),
 ((7,"scatter"),(5,"row"),(3,"ring"),(9,"block"),
  dict(most_scattered=0, linear=1, fewest=2, symmetric_global_shape=2, most=3, compact_block=3)),
]
for v, spec in enumerate(NUM):
    ps, rules = spec[:4], spec[4]
    add("numerosity", "M5_numerosity", v,
        [(f"n{p[0]}_{p[1]}", (lambda ax, p=p, i=i: group(ax, p[0], p[1], seed=SEED + 500 + v * 4 + i)))
         for i, p in enumerate(ps)], rules,
        "count vs grouping vs spacing regularity vs global shape")

# ---- M6 size rank / hierarchy -------------------------------------------------
EQ = [.20, .20, .20, .20]
ASC, DESC = [.11, .16, .21, .26], [.26, .21, .16, .11]
PEAK, VALL = [.12, .26, .26, .12], [.26, .12, .12, .26]
SZ = [
 (ASC, DESC, EQ, PEAK, dict(ascending=0, descending=1, equal_regular=2, centre_emphasis=3)),
 (DESC, EQ, VALL, ASC, dict(descending=0, equal_regular=1, edge_emphasis=2, ascending=3)),
 (EQ, PEAK, ASC, VALL, dict(equal_regular=0, centre_emphasis=1, ascending=2, edge_emphasis=3)),
 (PEAK, ASC, VALL, EQ, dict(centre_emphasis=0, ascending=1, edge_emphasis=2, equal_regular=3)),
 (VALL, EQ, DESC, PEAK, dict(edge_emphasis=0, equal_regular=1, descending=2, centre_emphasis=3)),
 (ASC, VALL, PEAK, DESC, dict(ascending=0, edge_emphasis=1, centre_emphasis=2, descending=3)),
 (DESC, PEAK, EQ, VALL, dict(descending=0, centre_emphasis=1, equal_regular=2, edge_emphasis=3)),
]
TONESETS = [None, TONES, None, TONES[::-1], None, TONES, None]
for v, spec in enumerate(SZ):
    rs, rules = spec[:4], spec[4]
    ts = TONESETS[v]
    rules = dict(rules)
    if ts is not None:
        rules["tonal_ordering"] = 0 if v % 2 else 3
    def nm(r):
        return {tuple(ASC): "asc", tuple(DESC): "desc", tuple(EQ): "equal",
                tuple(PEAK): "peak", tuple(VALL): "valley"}[tuple(r)]
    add("size_rank", "M6_sizerank", v,
        [(nm(r) + ("_toned" if ts else ""), (lambda ax, r=r, ts=ts: row(ax, r, ts)))
         for r in rs], rules,
        "size order vs centre/edge emphasis vs regularity vs tonal ordering")


# =============================== QA + RENDER ==================================
def object_png(fn, dpi=100):
    """Render ONE object with the axes filling the whole figure.

    The panel must be the entire image: otherwise the white figure margin reads as ink
    against the tinted panel ground and every object looks clipped.
    """
    fig, ax = plt.subplots(figsize=(3.1, 3.4), dpi=dpi)
    fn(ax)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    buf = io.BytesIO(); fig.savefig(buf, facecolor=PANEL); plt.close(fig)
    return buf.getvalue()


def _arr(png):
    import matplotlib.image as mpimg
    return mpimg.imread(io.BytesIO(png))[:, :, :3]


def ink_fraction(png):
    """Fraction of DARK marks.

    Not "differs from the panel ground": a bounded texture patch paints a white backing
    disc, which differs from the ground over ~2.8 axes-units and swamps the actual marks -
    it made an unbounded patch look 4x lighter than a bounded one with identical dots.
    Ink is what is drawn in EDGE, so measure luminance below the ground.
    """
    a = _arr(png)
    L = a @ np.array([0.2126, 0.7152, 0.0722])
    bgL = np.array([int(PANEL[i:i + 2], 16) / 255 for i in (1, 3, 5)]) @ \
        np.array([0.2126, 0.7152, 0.0722])
    return float((L < bgL - 0.15).mean())


def min_contrast(png):
    """Largest deviation from the panel ground anywhere in the object."""
    a = _arr(png)
    bg = np.array([int(PANEL[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return float(np.abs(a - bg).sum(axis=2).max())


def bbox_ok(png, margin=3):
    """Nothing touches the panel edge (no clipping)."""
    a = _arr(png)
    bg = np.array([int(PANEL[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    m = np.abs(a - bg).sum(axis=2) > 0.06
    if not m.any(): return False
    ys, xs = np.where(m)
    h, w = m.shape
    return (ys.min() > margin and xs.min() > margin
            and ys.max() < h - 1 - margin and xs.max() < w - 1 - margin)


def palette_ok(png, tol=0.16):
    """Consistent with the established neutral blue-grey palette.

    NB the project palette is NOT pure grey - EDGE #3A4152 and FILL #9AA3B2 both have
    channel spread ~0.094, and TONES[3] #7C8698 ~0.110. A pure-achromatic test rejects
    the battery's own colours; the requirement is no UNIQUELY coloured object, which is
    checked across objects by no_unique_colour().
    """
    a = _arr(png)
    return bool(np.ptp(a, axis=2).max() <= tol)


def mean_chroma_vec(png):
    """Mean hue direction of an object's ink, luminance-normalised."""
    a = _arr(png)
    bg = np.array([int(PANEL[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    m = np.abs(a - bg).sum(axis=2) > 0.06
    px = a[m]
    if not len(px): return np.zeros(3)
    mu = px.mean(axis=0)
    return mu - mu.mean()


def no_unique_colour(pngs, tol=0.05):
    """No object may sit off on its own in hue relative to the other three."""
    vs = [mean_chroma_vec(p) for p in pngs]
    worst = 0.0
    for i in range(4):
        others = np.mean([vs[j] for j in range(4) if j != i], axis=0)
        worst = max(worst, float(np.linalg.norm(vs[i] - others)))
    return worst <= tol, round(worst, 4)


def render(sid, objs):
    d = os.path.join(OUT, sid); os.makedirs(d, exist_ok=True)
    manifest = {}
    for pi, perm in enumerate(itertools.permutations(range(4))):
        fig, axes = plt.subplots(1, 4, figsize=(12.4, 3.4), dpi=100)
        for pos, ax in enumerate(axes):
            objs[perm[pos]][1](ax)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.03, wspace=0.16)
        fig.savefig(os.path.join(d, f"perm{pi:02d}.png"), facecolor="white")
        plt.close(fig)
        manifest[str(pi)] = list(perm)
    json.dump(manifest, open(os.path.join(d, "manifest.json"), "w"), indent=1)
    return d


def main():
    os.makedirs(OUT, exist_ok=True)
    rows, cues, qa = [], [], []
    for spec in A:
        sid = f"{spec['family'].split('_')[0].lower()}_{spec['mechanism'][:4]}_v{spec['variant']}"
        sid = f"{spec['family']}_v{spec['variant']}".lower()
        objs, rules = spec["objects"], spec["rules"]
        names = [o[0] for o in objs]
        assert len(objs) == 4, sid
        assert len(set(names)) == 4, f"{sid}: duplicate object names {names}"

        # ---- cue-conflict audit: every object wins >=1 rule, none wins >2 ----
        wins = Counter(rules.values())
        missing = [i for i in range(4) if wins[i] == 0]
        dom = [i for i in range(4) if wins[i] > 2]
        assert not missing, f"{sid}: object(s) {missing} favoured by NO rule"
        assert not dom, f"{sid}: object(s) {dom} favoured by >2 rules (dominant)"
        assert len(rules) >= 4, f"{sid}: only {len(rules)} rules recorded"

        pngs = [object_png(fn) for _, fn in objs]
        digs = [hashlib.sha256(p).hexdigest() for p in pngs]
        assert len(set(digs)) == 4, f"{sid}: objects render identically"
        for nm, p in zip(names, pngs):
            assert palette_ok(p), f"{sid}/{nm}: off-palette colour"
            assert min_contrast(p) >= 0.25, f"{sid}/{nm}: too faint vs panel ground"
            assert bbox_ok(p), f"{sid}/{nm}: touches or exceeds the panel edge"
        ok_col, worst_col = no_unique_colour(pngs)
        assert ok_col, f"{sid}: uniquely coloured object (hue outlier {worst_col})"
        ink = [ink_fraction(p) for p in pngs]
        mean = sum(ink) / 4
        ratios = [i / mean for i in ink]
        bad = [(n, round(r, 2)) for n, r in zip(names, ratios)
               if not (INK_TOL[0] <= r <= INK_TOL[1])]
        assert not bad, f"{sid}: ink imbalance {bad}"

        d = render(sid, objs)
        ph = [hashlib.sha256(open(os.path.join(d, f"perm{i:02d}.png"), "rb").read()).hexdigest()
              for i in range(24)]
        assert len(set(ph)) == 24, f"{sid}: permutation renders collide"
        man = json.load(open(os.path.join(d, "manifest.json")))
        bal = Counter((it, pos) for o in man.values() for pos, it in enumerate(o))
        assert set(bal.values()) == {6} and len(bal) == 16, f"{sid}: position balance broken"

        rows.append(dict(array_id=sid, family=spec["family"], mechanism=spec["mechanism"],
                         variant=spec["variant"], n_options=4, n_perms=24, dir=d,
                         objects="|".join(names), n_rules=len(rules),
                         ink_ratios="|".join(f"{r:.2f}" for r in ratios),
                         note=spec["note"]))
        for rule, w in sorted(rules.items()):
            cues.append(dict(array_id=sid, mechanism=spec["mechanism"], rule=rule,
                             favoured_object_index=w, favoured_object=names[w]))
        qa.append(dict(array_id=sid, wins_per_object="|".join(str(wins[i]) for i in range(4)),
                       max_wins=max(wins.values()), min_wins=min(wins[i] for i in range(4)),
                       n_rules=len(rules), ink_min=round(min(ratios), 2),
                       ink_max=round(max(ratios), 2), hue_outlier=worst_col,
                       perms_distinct=len(set(ph)),
                       position_balance_ok=True))
        print(f"  {sid:26} {spec['mechanism']:14} rules={len(rules)} wins={[wins[i] for i in range(4)]} ink {min(ratios):.2f}-{max(ratios):.2f}")

    for fn, data in (("battery5_manifest.csv", rows), ("cue_table.csv", cues),
                     ("qa_report.csv", qa)):
        with open(os.path.join(OUT, fn), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader(); w.writerows(data)
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda x: x["array_id"]):
        for i in range(24):
            h.update(open(os.path.join(r["dir"], f"perm{i:02d}.png"), "rb").read())
    open(os.path.join(OUT, "BATTERY5_SHA256.txt"), "w").write(h.hexdigest() + "\n")
    mech = Counter(r["mechanism"] for r in rows)
    print(f"\n{len(rows)} arrays, {24*len(rows)} images, {len(cues)} cue rows")
    print(f"mechanisms: {dict(mech)}")
    top = max(mech.values()) / len(rows)
    print(f"largest mechanism share: {top:.1%} (cap 25%)  {'OK' if top <= 0.25 else 'FAIL'}")
    print(f"battery sha256: {h.hexdigest()}")


if __name__ == "__main__":
    main()
