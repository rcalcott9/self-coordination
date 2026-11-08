"""
FROZEN EXPANSION BATTERY - 30 stimuli, 10 cue families x 3 members.

WHY. The original 15-stimulus battery yielded too few admissible matched pairs in
earlier models (GPT-5: 3 eligible / 2 selected; Opus 4.5: 3 eligible / 1 selected).
The fix is NOT to loosen the frozen selector. It is to enlarge the candidate universe
and ask whether the same rule can find enough contrasts.

METHODS WORDING (use verbatim):
"Because the original 15-stimulus battery yielded too few admissible matched pairs in
earlier models, we prospectively expanded the candidate stimulus universe while
retaining the original matching, exclusion, and non-reuse criteria."

DESIGN GOAL. Separate GENERIC/PUBLIC focality from MODEL-SPECIFIC self-copy
reliability. Every family below pits two defensible conventions against each other, so
that different policies can land on different rules. Obvious-salience contrasts are
deliberately under-represented - the original battery already covers those, and
GPT-4o's rho(match, salience) = +0.85 shows that obvious contrasts cannot separate the
two constructs.

NOT ADVERSARIALLY ENGINEERED. No stimulus here was designed because a named model was
observed to prefer a named feature. The families were chosen for structural ambiguity
in general, written in one batch, and frozen before any Stage A call. There was no
generate-test-regenerate loop.

FAMILIES (3 members each, varying cue strength within family)
  X1 symmetry strength          weak vs strong bilateral symmetry
  X2 local-vs-global            element shape conflicts with the shape they form
  X3 texture-vs-outline         same silhouette, different surface treatment
  X4 density-vs-boundary        interior count conflicts with border weight
  X5 convexity-vs-size          the convex form is the smaller one
  X6 orientation-vs-identity    canonical orientation conflicts with object class
  X7 closure subtlety           near-closed contours at three gap sizes
  X8 contrast subtlety          three ink differences, all small
  X9 pattern directionality     repeated elements implying opposite directions
  X10 competing centrality      two different cues each nominating a centre

GEOMETRY. 1040x520 PNG, two panels, `_AB` / `_BA`, identical palette and figure
geometry to the Step 1/1b/1c batteries, so the frozen prompt runs unchanged.

Run:  python3 make_expansion_stimuli.py
"""
import csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

REPO = os.path.expanduser("~/Desktop/Coordination/LLM_Coordination/Name_game_experiment")
OUT = os.path.join(REPO, "stimuli", "expansion")

FILL, EDGE = "#9AA3B2", "#3A4152"
LIGHT, DARK = "#C9CEd6", "#5A6172"
VLIGHT, VDARK = "#E8EAEE", "#2B3040"


def poly_xy(n, r=1.0, rot=0.0):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False) + rot
    return np.c_[r * np.cos(a), r * np.sin(a)]


def star_xy(points, r_out=1.0, r_in=0.45, rot=0.0):
    a = np.linspace(0, 2 * np.pi, points * 2, endpoint=False) + rot
    rad = np.where(np.arange(points * 2) % 2 == 0, r_out, r_in)
    return np.c_[rad * np.cos(a), rad * np.sin(a)]


def rot_xy(xy, deg):
    a = np.deg2rad(deg)
    return xy @ np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]).T


def ring_pts(r, gap_deg, n=200):
    a = np.deg2rad(np.linspace(gap_deg / 2, 360 - gap_deg / 2, n))
    return np.c_[r * np.cos(a), r * np.sin(a)]


def draw(ax, s):
    ax.set_xlim(-1.25, 1.25); ax.set_ylim(-1.25, 1.25)
    ax.set_aspect("equal"); ax.axis("off")
    k = s["kind"]
    kw = dict(facecolor=s.get("fc", FILL), edgecolor=s.get("ec", EDGE),
              linewidth=s.get("lw", 3))

    if k == "poly":
        ax.add_patch(Polygon(poly_xy(s["n"], s.get("r", .88), s.get("rot", 0)),
                             closed=True, **kw))
    elif k == "circle":
        ax.add_patch(Circle((0, 0), s.get("r", .85), **kw))
    elif k == "star":
        ax.add_patch(Polygon(star_xy(s["points"], s.get("r_out", .95),
                                     s.get("r_in", .5), s.get("rot", 0)),
                             closed=True, **kw))
    elif k == "symmetric":
        # bilateral symmetry of tunable strength: mirror the right half onto the left,
        # blending toward an asymmetric variant as `sym` falls
        rng = np.random.default_rng(s["seed"])
        n = 11
        base = .55 + .40 * rng.random(n)
        other = .55 + .40 * rng.random(n)
        half = base * s["sym"] + other * (1 - s["sym"])
        r = np.r_[base, half[::-1]]
        a = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False) + np.pi / 2
        ax.add_patch(Polygon(np.c_[r * np.cos(a), r * np.sin(a)], closed=True, **kw))
    elif k == "localglobal":
        # small elements of shape `elem` arranged on the outline of shape `glob`
        pts = (poly_xy(s["gn"], .82) if s["gn"] > 2 else poly_xy(3, .82))
        dense = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            for t in np.linspace(0, 1, s.get("per_edge", 5), endpoint=False):
                dense.append(p + (q - p) * t)
        for (x, y) in dense:
            if s["elem"] == "circle":
                ax.add_patch(Circle((x, y), .11, **kw))
            else:
                ax.add_patch(Polygon(poly_xy(s.get("en", 3), .15, np.pi / 2) + [x, y],
                                     closed=True, **kw))
    elif k == "texture":
        ax.add_patch(Circle((0, 0), .85, facecolor=s.get("fc", "white"),
                            edgecolor=EDGE, linewidth=3))
        if s["tex"] == "stripe":
            for y in np.arange(-.8, .81, .16):
                w = np.sqrt(max(.85 ** 2 - y ** 2, 0))
                ax.plot([-w, w], [y, y], color=EDGE, lw=2.2, solid_capstyle="butt")
        elif s["tex"] == "dot":
            rng = np.random.default_rng(s.get("seed", 1))
            for _ in range(46):
                a, rr = rng.random() * 2 * np.pi, .8 * np.sqrt(rng.random())
                ax.add_patch(Circle((rr * np.cos(a), rr * np.sin(a)), .055,
                                    facecolor=EDGE, edgecolor="none"))
    elif k == "density":
        ax.add_patch(Circle((0, 0), .92, facecolor="white", edgecolor=EDGE,
                            linewidth=s.get("border", 3)))
        rng = np.random.default_rng(s.get("seed", 2))
        for _ in range(s["count"]):
            a, rr = rng.random() * 2 * np.pi, .74 * np.sqrt(rng.random())
            ax.add_patch(Circle((rr * np.cos(a), rr * np.sin(a)), .07,
                                facecolor=FILL, edgecolor=EDGE, linewidth=1))
    elif k == "ring":
        ax.add_patch(Polygon(ring_pts(s.get("r", .85), s.get("gap", 0)),
                             closed=False, fill=False, edgecolor=EDGE,
                             linewidth=s.get("lw", 9)))
    elif k == "arrowsrow":
        for i, x in enumerate(np.linspace(-.75, .75, 4)):
            d = s["dir"]
            tri = np.array([[0, .22], [0, -.22], [.34 * d, 0]]) + [x - .1 * d, 0]
            ax.add_patch(Polygon(tri, closed=True, **kw))
    elif k == "centrality":
        # one large off-centre form (mass centre) + one small form at the frame centre
        sc = s.get("scale", 1.0)
        if s["cue"] == "mass":
            ax.add_patch(Circle((-.35, 0), .72 * sc, **kw))
            ax.add_patch(Circle((.62, 0), .22 * sc, facecolor="white",
                                edgecolor=EDGE, lw=3))
        else:
            ax.add_patch(Circle((0, 0), .30 * sc, **kw))
            for xy in ((-.85, .6), (.85, .6), (-.85, -.6), (.85, -.6)):
                ax.add_patch(Circle(xy, .17 * sc, facecolor="white",
                                    edgecolor=EDGE, lw=3))


P = []


def add(name, id1, s1, id2, s2, fam, manip, note):
    P.append((name, id1, s1, id2, s2, fam, manip, note))


# X1 symmetry strength -------------------------------------------------------
for tag, sym in (("hi", 1.00), ("mid", 0.60), ("lo", 0.25)):
    add(f"x1_sym_{tag}", "symmetric", dict(kind="symmetric", seed=11, sym=sym),
        "irregular", dict(kind="symmetric", seed=29, sym=0.0),
        "X1_symmetry", "bilateral symmetry vs irregular blob",
        f"symmetry strength {sym}; at low strength the 'symmetric' side is only "
        f"weakly so, leaving room for a different rule to dominate")

# X2 local vs global ---------------------------------------------------------
add("x2_lg_ct", "circles_form_triangle",
    dict(kind="localglobal", elem="circle", gn=3, per_edge=5),
    "triangles_form_circle",
    dict(kind="localglobal", elem="poly", en=3, gn=12, per_edge=2),
    "X2_local_global", "circle-elements in a triangle vs triangle-elements in a ring",
    "local and global shape are crossed; a local-first and a global-first rule give "
    "opposite answers")
add("x2_lg_sq", "squares_form_ring",
    dict(kind="localglobal", elem="poly", en=4, gn=14, per_edge=2),
    "circles_form_square",
    dict(kind="localglobal", elem="circle", gn=4, per_edge=4),
    "X2_local_global", "square-elements in a ring vs circle-elements in a square",
    "same crossing, different shape vocabulary")
add("x2_lg_dense", "many_small_global_tri",
    dict(kind="localglobal", elem="circle", gn=3, per_edge=9),
    "few_large_global_tri",
    dict(kind="localglobal", elem="circle", gn=3, per_edge=3),
    "X2_local_global", "dense vs sparse sampling of the same global form",
    "global shape held CONSTANT so only element count varies - isolates whether "
    "numerosity or form drives the choice")

# X3 texture vs outline ------------------------------------------------------
add("x3_tex_sd", "striped", dict(kind="texture", tex="stripe"),
    "dotted", dict(kind="texture", tex="dot", seed=3),
    "X3_texture", "striped fill vs dotted fill",
    "identical silhouette and border; only surface treatment differs")
add("x3_tex_sp", "striped", dict(kind="texture", tex="stripe"),
    "plain", dict(kind="texture", tex="none"),
    "X3_texture", "striped fill vs plain fill",
    "texture presence vs absence at matched silhouette")
add("x3_tex_dp", "dotted", dict(kind="texture", tex="dot", seed=7),
    "plain", dict(kind="texture", tex="none"),
    "X3_texture", "dotted fill vs plain fill",
    "third leg of the texture triangle so the family is internally comparable")

# X4 density vs boundary -----------------------------------------------------
add("x4_db_a", "many_thin_border", dict(kind="density", count=26, border=2, seed=4),
    "few_thick_border", dict(kind="density", count=7, border=9, seed=5),
    "X4_density_boundary", "many elements + thin border vs few + thick border",
    "interior numerosity and border weight are put in direct conflict")
add("x4_db_b", "many_thick_border", dict(kind="density", count=26, border=9, seed=6),
    "few_thin_border", dict(kind="density", count=7, border=2, seed=8),
    "X4_density_boundary", "many + thick vs few + thin",
    "the aligned version of x4_db_a; brackets it")
add("x4_db_sub", "slightly_more", dict(kind="density", count=16, border=3, seed=9),
    "slightly_fewer", dict(kind="density", count=11, border=3, seed=10),
    "X4_density_boundary", "16 vs 11 elements, border matched",
    "a deliberately SUBTLE numerosity contrast - obvious density contrasts already "
    "exist in the original battery")

# X5 convexity vs size -------------------------------------------------------
add("x5_cs_a", "convex_small", dict(kind="poly", n=7, r=.62),
    "concave_large", dict(kind="star", points=7, r_out=.98, r_in=.72),
    "X5_convexity_size", "small convex vs large concave",
    "convexity and size nominate different forms")
add("x5_cs_b", "convex_large", dict(kind="poly", n=7, r=.95),
    "concave_small", dict(kind="star", points=7, r_out=.66, r_in=.48),
    "X5_convexity_size", "large convex vs small concave",
    "the aligned control for x5_cs_a")
add("x5_cs_sub", "convex_slightly_small", dict(kind="poly", n=9, r=.78),
    "concave_slightly_large", dict(kind="star", points=9, r_out=.90, r_in=.74),
    "X5_convexity_size", "mild size and mild concavity",
    "both cues weakened so neither obviously dominates")

# X6 orientation vs identity -------------------------------------------------
add("x6_oi_a", "upright_square", dict(kind="poly", n=4, r=.85, rot=np.pi / 4),
    "tilted_triangle", dict(kind="poly", n=3, r=.92, rot=.55),
    "X6_orientation_identity", "axis-aligned square vs tilted triangle",
    "canonical orientation and object class nominate different forms")
add("x6_oi_b", "tilted_square", dict(kind="poly", n=4, r=.85, rot=.35),
    "upright_triangle", dict(kind="poly", n=3, r=.92, rot=np.pi / 2),
    "X6_orientation_identity", "tilted square vs upright triangle",
    "mirror of x6_oi_a so the family is balanced")
add("x6_oi_c", "upright_pentagon", dict(kind="poly", n=5, r=.88, rot=np.pi / 2),
    "tilted_pentagon", dict(kind="poly", n=5, r=.88, rot=np.pi / 2 + .42),
    "X6_orientation_identity", "same pentagon, upright vs tilted",
    "identity held CONSTANT so only orientation varies - isolates the orientation cue")

# X7 closure subtlety --------------------------------------------------------
for tag, gap in (("wide", 60), ("mid", 26), ("fine", 10)):
    add(f"x7_close_{tag}", "closed", dict(kind="ring", r=.85, gap=0, lw=9),
        "open", dict(kind="ring", r=.85, gap=gap, lw=9),
        "X7_closure", f"closed ring vs ring with a {gap}-degree gap",
        "closure at three gap sizes; the fine gap is near the limit of easy detection")

# X8 contrast subtlety -------------------------------------------------------
for tag, (a, b) in (("a", (LIGHT, FILL)), ("b", (FILL, DARK)), ("c", (VLIGHT, LIGHT))):
    add(f"x8_contr_{tag}", "lighter", dict(kind="circle", fc=a),
        "darker", dict(kind="circle", fc=b),
        "X8_contrast", "lighter vs darker fill at small separation",
        "geometry identical; only ink differs, and by less than the original "
        "contrast stimuli")

# X9 pattern directionality --------------------------------------------------
add("x9_dir_a", "rightward", dict(kind="arrowsrow", dir=1),
    "leftward", dict(kind="arrowsrow", dir=-1),
    "X9_direction", "row of rightward vs leftward triangles",
    "reading-order and shape-pointing conventions may or may not agree")
add("x9_dir_b", "rightward_dense", dict(kind="arrowsrow", dir=1, lw=7, fc=DARK),
    "leftward_dense", dict(kind="arrowsrow", dir=-1, lw=7, fc=DARK),
    "X9_direction", "same contrast, heavier ink",
    "replicate of x9_dir_a at a heavier stroke and darker fill")
add("x9_dir_c", "rightward_small", dict(kind="arrowsrow", dir=1, lw=1.5),
    "leftward_small", dict(kind="arrowsrow", dir=-1, lw=1.5),
    "X9_direction", "same contrast, lighter ink",
    "third weight so the family spans a range")

# X10 competing centrality ---------------------------------------------------
add("x10_cen_a", "mass_centre", dict(kind="centrality", cue="mass"),
    "frame_centre", dict(kind="centrality", cue="frame"),
    "X10_centrality", "large off-centre mass vs small centred form",
    "'the big one' and 'the middle one' nominate different forms")
add("x10_cen_b", "mass_centre_alt", dict(kind="centrality", cue="mass", scale=0.75),
    "frame_centre_alt", dict(kind="centrality", cue="frame", scale=1.25),
    "X10_centrality", "same conflict, second realisation at different scales",
    "the mass form is smaller and the centred form larger than in x10_cen_a, so the "
    "two family members are not the same picture twice")
add("x10_cen_c", "single_large", dict(kind="circle", r=.95),
    "single_small_centred", dict(kind="circle", r=.42),
    "X10_centrality", "large vs small, both centred",
    "the pure size baseline for the family, with centrality removed")


def make(name, ls, rs):
    fig, axes = plt.subplots(1, 2, figsize=(8, 4), dpi=130)
    for ax, s in zip(axes, (ls, rs)):
        draw(ax, s)
    fig.subplots_adjust(left=.02, right=.98, top=.98, bottom=.02, wspace=.15)
    fig.savefig(os.path.join(OUT, f"{name}.png"), facecolor="white")
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    seen = set()
    for name, id1, s1, id2, s2, *_ in P:
        if name in seen:
            raise SystemExit(f"duplicate stimulus id: {name}")
        if id1 == id2:
            raise SystemExit(f"{name}: identities must differ")
        seen.add(name)
        make(f"{name}_AB", s1, s2)      # identity_1 on the LEFT
        make(f"{name}_BA", s2, s1)      # identity_2 on the LEFT

    with open(os.path.join(OUT, "manifest.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stimulus_id", "family", "manipulation",
                    "identity_1", "identity_1_description",
                    "identity_2", "identity_2_description",
                    "image_path_AB", "image_path_BA", "generation_notes"])
        for name, id1, _s1, id2, _s2, fam, manip, note in P:
            lo, hi = manip.split(" vs ") if " vs " in manip else (manip, manip)
            w.writerow([name, fam, manip, id1, lo, id2, hi,
                        f"stimuli/expansion/{name}_AB.png",
                        f"stimuli/expansion/{name}_BA.png", note])

    import hashlib
    digest = {}
    for name, *_ in P:
        for v in ("AB", "BA"):
            h = hashlib.sha256(open(os.path.join(OUT, f"{name}_{v}.png"), "rb").read()
                               ).hexdigest()
            digest.setdefault(h, []).append(f"{name}_{v}")
    dupes = {h: v for h, v in digest.items() if len(v) > 1}
    if dupes:
        raise SystemExit(f"IDENTICAL RENDERS - fix before use: {list(dupes.values())}")
    print("  duplicate-render check: passed (all 60 images distinct)")

    fams = {}
    for name, *_rest in P:
        fams.setdefault(_rest[4], []).append(name)
    print(f"  wrote {len(P)} stimuli x 2 variants -> {OUT}")
    for f, names in sorted(fams.items()):
        print(f"    {f:26} {len(names)}  {', '.join(names)}")


if __name__ == "__main__":
    main()
