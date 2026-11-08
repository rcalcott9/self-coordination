"""FROZEN BATTERY EXTENSION - 75 stimuli, 25 cue families x 3 members.

WHY. A single-focal-model replication needs ~120 candidate stimuli to yield >=20
independent matched pairs (DESIGN_v3_ONEFOCAL.md S3). 45 exist (15 Study 1 + 30
frozen expansion); these are the missing 75.

METHODS WORDING (verbatim, inherited from the frozen expansion battery):
"Because the original 15-stimulus battery yielded too few admissible matched
pairs, we prospectively expanded the candidate stimulus universe while retaining
the original matching, exclusion, and non-reuse criteria."

DESIGN RULES, inherited and unchanged:
  * every family pits TWO DEFENSIBLE CONVENTIONS against each other, so different
    policies can land on different rules;
  * obvious-salience contrasts are deliberately under-represented;
  * NOT ADVERSARIALLY ENGINEERED - no stimulus was designed because a named model
    was observed to prefer a named feature. Families were chosen for structural
    ambiguity in general, written in ONE BATCH, and frozen before any Stage A
    call. There was NO generate-test-regenerate loop;
  * within each family, 3 members vary CUE STRENGTH, so the family spans a range
    rather than repeating one contrast.

GEOMETRY. 1040x520 PNG, two panels, `_AB` / `_BA`, identical palette and figure
geometry to Step 1/1b/1c and the expansion battery, so the canonical prompt
(sha8 3003ae1b) runs unchanged.
"""
import csv, hashlib, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle, Wedge

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "stimuli", "v3")

FILL, EDGE = "#9AA3B2", "#3A4152"
LIGHT, DARK = "#C9CEd6", "#5A6172"
VLIGHT, VDARK = "#E8EAEE", "#2B3040"


def poly_xy(n, r=1.0, rot=0.0):
    a = np.linspace(0, 2*np.pi, n, endpoint=False) + rot
    return np.c_[r*np.cos(a), r*np.sin(a)]


def star_xy(pts, r_out=1.0, r_in=0.45, rot=0.0):
    a = np.linspace(0, 2*np.pi, pts*2, endpoint=False) + rot
    rad = np.where(np.arange(pts*2) % 2 == 0, r_out, r_in)
    return np.c_[rad*np.cos(a), rad*np.sin(a)]


def arc_pts(r, a0, a1, n=160):
    a = np.deg2rad(np.linspace(a0, a1, n))
    return np.c_[r*np.cos(a), r*np.sin(a)]


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
    elif k == "aspect":                       # equal-area rectangle, tunable ratio
        ar = s["ar"]; area = s.get("area", 1.9)
        w = np.sqrt(area*ar)/2; h = np.sqrt(area/ar)/2
        ax.add_patch(Rectangle((-w, -h), 2*w, 2*h, **kw))
    elif k == "stroke":                       # size vs stroke weight
        ax.add_patch(Circle((0, 0), s["r"], facecolor="white",
                            edgecolor=EDGE, linewidth=s["lw"]))
    elif k == "nested":                       # concentric rings vs one thick ring
        for i in range(s["rings"]):
            r = s.get("r", .88) - i*s.get("step", .19)
            if r > .08:
                ax.add_patch(Circle((0, 0), r, facecolor="none",
                                    edgecolor=EDGE, linewidth=s.get("lw", 3)))
    elif k == "arcpair":                      # curvature sign: convex vs concave
        sgn = s["sgn"]; sp = s.get("span", 150)
        for dx in (-.42, .42):
            p = arc_pts(s.get("r", .78), -sp/2, sp/2)
            p = p * [sgn, 1]
            ax.plot(p[:, 0]+dx, p[:, 1], color=EDGE, lw=s.get("lw", 8),
                    solid_capstyle="round")
    elif k == "grid":                         # numerosity x element size, area held
        n = s["n"]; side = int(np.ceil(np.sqrt(n)))
        rad = s.get("total_area", .55)/np.sqrt(n)
        xs = np.linspace(-.72, .72, side)
        k2 = 0
        for y in xs[::-1]:
            for x in xs:
                if k2 >= n: break
                ax.add_patch(Circle((x, y), rad, **kw)); k2 += 1
    elif k == "occlude":                      # completion vs visible-fragment rule
        ax.add_patch(Circle((-.18, 0), .62, **kw))
        ax.add_patch(Rectangle((.02, -.85), s["cover"], 1.7,
                               facecolor="white", edgecolor=EDGE, lw=3))
    elif k == "polarity":                     # figure/ground contrast polarity
        bg, fg = (EDGE, "white") if s["inv"] else ("white", EDGE)
        ax.add_patch(Rectangle((-1.1, -1.1), 2.2, 2.2, facecolor=bg,
                               edgecolor=EDGE, lw=2))
        ax.add_patch(Polygon(poly_xy(s.get("n", 3), .62, np.pi/2), closed=True,
                             facecolor=fg, edgecolor=EDGE, lw=2))
    elif k == "mixed":                        # element homogeneity vs global form
        rng = np.random.default_rng(s.get("seed", 3))
        pts = poly_xy(s.get("gn", 4), .74)
        dense = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i+1) % len(pts)]
            for t in np.linspace(0, 1, s.get("per_edge", 3), endpoint=False):
                dense.append(p + (q-p)*t)
        for j, (x, y) in enumerate(dense):
            if s["hetero"] and rng.random() < s.get("mix", .5):
                ax.add_patch(Polygon(poly_xy(4, .13, np.pi/4) + [x, y],
                                     closed=True, **kw))
            else:
                ax.add_patch(Circle((x, y), .12, **kw))
    elif k == "stripes":                      # texture orientation / spatial freq
        ax.add_patch(Circle((0, 0), .85, facecolor="white", edgecolor=EDGE, lw=3))
        step = s.get("step", .16)
        for v in np.arange(-.8, .81, step):
            w = np.sqrt(max(.85**2 - v**2, 0))
            if s["ori"] == "h":
                ax.plot([-w, w], [v, v], color=EDGE, lw=s.get("lw", 2.2),
                        solid_capstyle="butt")
            else:
                ax.plot([v, v], [-w, w], color=EDGE, lw=s.get("lw", 2.2),
                        solid_capstyle="butt")
    elif k == "gapring":                      # gap position: top vs side
        gap = s.get("gap", 40); at = s.get("at", 90)
        p = arc_pts(s.get("r", .85), at+gap/2, at+360-gap/2)
        ax.plot(p[:, 0], p[:, 1], color=EDGE, lw=s.get("lw", 9),
                solid_capstyle="round")
    elif k == "wedge":                        # radial vs tangential arrangement
        for i in range(s["n"]):
            a = 360*i/s["n"]
            ax.add_patch(Wedge((0, 0), .88, a, a+s.get("width", 22), **kw))
    elif k == "sizerank":                     # size order vs position order
        xs = np.linspace(-.78, .78, 4)
        rr = s["radii"]
        for x, r in zip(xs, rr):
            ax.add_patch(Circle((x, 0), r, **kw))
    else:
        raise ValueError(f"unknown kind {k!r}")


P = []
def add(name, id1, s1, id2, s2, fam, manip, note):
    P.append((name, id1, s1, id2, s2, fam, manip, note))


# =========================== 25 FAMILIES x 3 MEMBERS ==========================
# Each family pits two defensible conventions; members vary CUE STRENGTH.

# Y1 vertex parity vs size ----------------------------------------------------
for t, (r1, r2) in (("hi", (.92, .58)), ("mid", (.85, .72)), ("lo", (.82, .80))):
    add(f"y1_parity_{t}", "odd_sided", dict(kind="poly", n=3, r=r1, rot=np.pi/2),
        "even_sided", dict(kind="poly", n=4, r=r2, rot=np.pi/4),
        "Y1_parity_size", "odd-sided larger vs even-sided smaller",
        f"parity and size are crossed at ratio {r1/r2:.2f}; a size rule and a parity rule disagree")

# Y2 vertex count vs area -----------------------------------------------------
for t, n2 in (("hi", 12), ("mid", 8), ("lo", 6)):
    add(f"y2_vcount_{t}", "few_vertices_large", dict(kind="poly", n=3, r=.95, rot=np.pi/2),
        "many_vertices_small", dict(kind="poly", n=n2, r=.62),
        "Y2_vertex_area", f"3-gon large vs {n2}-gon small",
        "vertex count rises while area falls; complexity and size rules disagree")

# Y3 star points vs spikiness -------------------------------------------------
for t, ri in (("hi", .28), ("mid", .45), ("lo", .60)):
    add(f"y3_star_{t}", "few_deep_points", dict(kind="star", points=5, r_in=ri),
        "many_shallow_points", dict(kind="star", points=9, r_in=.66),
        "Y3_star_depth", f"5 deep points (r_in {ri}) vs 9 shallow points",
        "point count and point depth are crossed")

# Y4 canonical orientation ----------------------------------------------------
for t, rot in (("hi", 0.0), ("mid", np.pi/12), ("lo", np.pi/7)):
    add(f"y4_orient_{t}", "upright", dict(kind="poly", n=3, r=.86, rot=np.pi/2),
        "tilted", dict(kind="poly", n=3, r=.86, rot=np.pi/2 + np.pi/4 - rot),
        "Y4_orientation", "canonically upright vs rotated triangle",
        f"same shape; only orientation differs, tilt reduced by {rot:.2f} rad across members")

# Y5 aspect ratio at equal area ----------------------------------------------
for t, ar in (("hi", 5.0), ("mid", 2.6), ("lo", 1.7)):
    add(f"y5_aspect_{t}", "wide", dict(kind="aspect", ar=ar),
        "tall", dict(kind="aspect", ar=1.0/ar),
        "Y5_aspect", f"wide vs tall rectangle, equal area, ratio {ar}",
        "area is held constant so only elongation direction differs")

# Y6 size vs stroke weight ----------------------------------------------------
for t, lw in (("hi", 14), ("mid", 9), ("lo", 6)):
    add(f"y6_stroke_{t}", "large_thin", dict(kind="stroke", r=.92, lw=3),
        "small_thick", dict(kind="stroke", r=.58, lw=lw),
        "Y6_size_stroke", f"large thin outline vs small thick outline (lw {lw})",
        "extent and ink weight are crossed")

# Y7 concentric rings vs single ring ------------------------------------------
for t, n in (("hi", 4), ("mid", 3), ("lo", 2)):
    add(f"y7_nested_{t}", "many_rings", dict(kind="nested", rings=n, lw=3),
        "one_thick_ring", dict(kind="nested", rings=1, lw=11),
        "Y7_nesting", f"{n} concentric thin rings vs one thick ring",
        "ink is roughly matched; repetition and weight rules disagree")

# Y8 curvature sign -----------------------------------------------------------
for t, sp in (("hi", 170), ("mid", 130), ("lo", 95)):
    add(f"y8_curve_{t}", "convex_arcs", dict(kind="arcpair", sgn=1, span=sp),
        "concave_arcs", dict(kind="arcpair", sgn=-1, span=sp),
        "Y8_curvature", f"outward vs inward arcs, span {sp} deg",
        "identical strokes, opposite curvature sign")

# Y9 numerosity vs element size ----------------------------------------------
for t, n in (("hi", 16), ("mid", 9), ("lo", 6)):
    add(f"y9_numer_{t}", "few_large", dict(kind="grid", n=4),
        "many_small", dict(kind="grid", n=n),
        "Y9_numerosity", f"4 large elements vs {n} small, total area matched",
        "count and element size are crossed with total ink roughly held")

# Y10 completion under occlusion ---------------------------------------------
for t, cov in (("hi", .70), ("mid", .45), ("lo", .26)):
    add(f"y10_occl_{t}", "occluded", dict(kind="occlude", cover=cov),
        "unoccluded", dict(kind="circle", r=.62),
        "Y10_occlusion", f"partly covered disc (cover {cov}) vs whole disc",
        "an amodal-completion rule and a visible-fragment rule disagree")

# Y11 figure/ground polarity --------------------------------------------------
for t, n in (("hi", 3), ("mid", 4), ("lo", 6)):
    add(f"y11_polarity_{t}", "dark_on_light", dict(kind="polarity", inv=False, n=n),
        "light_on_dark", dict(kind="polarity", inv=True, n=n),
        "Y11_polarity", f"dark-on-light vs light-on-dark {n}-gon",
        "same form, inverted contrast polarity")

# Y12 element heterogeneity ---------------------------------------------------
for t, mix in (("hi", .5), ("mid", .3), ("lo", .15)):
    add(f"y12_hetero_{t}", "mixed_elements", dict(kind="mixed", hetero=True, mix=mix),
        "uniform_elements", dict(kind="mixed", hetero=False),
        "Y12_heterogeneity", f"mixed vs uniform elements (mix {mix})",
        "global arrangement held constant; only element homogeneity differs")

# Y13 texture orientation -----------------------------------------------------
for t, lw in (("hi", 3.2), ("mid", 2.2), ("lo", 1.5)):
    add(f"y13_texori_{t}", "horizontal", dict(kind="stripes", ori="h", lw=lw),
        "vertical", dict(kind="stripes", ori="v", lw=lw),
        "Y13_texture_orientation", f"horizontal vs vertical stripes, lw {lw}",
        "identical disc; only stripe orientation differs")

# Y14 spatial frequency -------------------------------------------------------
for t, st in (("hi", .08), ("mid", .13), ("lo", .19)):
    add(f"y14_freq_{t}", "fine", dict(kind="stripes", ori="h", step=st),
        "coarse", dict(kind="stripes", ori="h", step=.30),
        "Y14_spatial_frequency", f"fine (step {st}) vs coarse stripes",
        "same orientation; only stripe density differs")

# Y15 gap position ------------------------------------------------------------
for t, g in (("hi", 60), ("mid", 38), ("lo", 20)):
    add(f"y15_gappos_{t}", "gap_top", dict(kind="gapring", at=90, gap=g),
        "gap_side", dict(kind="gapring", at=0, gap=g),
        "Y15_gap_position", f"ring gap at top vs at side, gap {g} deg",
        "identical ring; only the gap's location differs")

# Y16 radial spoke count ------------------------------------------------------
for t, n in (("hi", 3), ("mid", 5), ("lo", 7)):
    add(f"y16_spokes_{t}", "few_wide_spokes", dict(kind="wedge", n=n, width=40),
        "many_narrow_spokes", dict(kind="wedge", n=12, width=14),
        "Y16_spokes", f"{n} wide wedges vs 12 narrow wedges",
        "spoke count and spoke width are crossed at roughly matched ink")

# Y17 size rank vs position ---------------------------------------------------
for t, rr in (("hi", [.30,.24,.18,.12]), ("mid", [.26,.22,.19,.15]), ("lo", [.23,.21,.20,.18])):
    add(f"y17_sizerank_{t}", "descending", dict(kind="sizerank", radii=rr),
        "ascending", dict(kind="sizerank", radii=rr[::-1]),
        "Y17_size_rank", "size decreasing vs increasing left-to-right",
        f"a size-order rule and a position rule disagree; contrast {rr[0]/rr[-1]:.2f}")

# Y18 symmetry axis -----------------------------------------------------------
for t, rot in (("hi", np.pi/4), ("mid", np.pi/6), ("lo", np.pi/12)):
    add(f"y18_symaxis_{t}", "vertical_axis", dict(kind="star", points=4, r_in=.42, rot=np.pi/2),
        "diagonal_axis", dict(kind="star", points=4, r_in=.42, rot=np.pi/2 + rot),
        "Y18_symmetry_axis", f"vertical vs diagonal mirror axis, offset {rot:.2f}",
        "same form, different axis of bilateral symmetry")

# Y19 interior density vs border weight --------------------------------------
for t, c in (("hi", 26), ("mid", 15), ("lo", 8)):
    add(f"y19_dens_{t}", "dense_thin_border", dict(kind="grid", n=c, total_area=.5),
        "sparse_thick_border", dict(kind="stroke", r=.86, lw=13),
        "Y19_density_border", f"{c} interior elements vs a heavy empty border",
        "interior content and boundary weight compete for attention")

# Y20 convexity vs extent -----------------------------------------------------
for t, ri in (("hi", .22), ("mid", .38), ("lo", .55)):
    add(f"y20_convex_{t}", "convex_small", dict(kind="poly", n=6, r=.60),
        "concave_large", dict(kind="star", points=6, r_out=.98, r_in=ri),
        "Y20_convexity_extent", f"small convex hexagon vs large concave star (r_in {ri})",
        "convexity and extent are crossed")

# Y21 element shape vs global shape -------------------------------------------
for t, pe in (("hi", 6), ("mid", 4), ("lo", 3)):
    add(f"y21_localglob_{t}", "square_of_discs", dict(kind="mixed", hetero=False, gn=4, per_edge=pe),
        "triangle_of_discs", dict(kind="mixed", hetero=False, gn=3, per_edge=pe),
        "Y21_global_form", f"square vs triangular global arrangement, {pe} per edge",
        "identical elements; only the global form they trace differs")

# Y22 ring closure ------------------------------------------------------------
for t, g in (("hi", 8), ("mid", 26), ("lo", 55)):
    add(f"y22_closure_{t}", "nearly_closed", dict(kind="gapring", at=45, gap=g),
        "clearly_open", dict(kind="gapring", at=45, gap=110),
        "Y22_closure", f"gap {g} deg vs gap 110 deg",
        "closure strength varies while gap position is held constant")

# Y23 stroke weight at equal extent -------------------------------------------
for t, lw in (("hi", 16), ("mid", 10), ("lo", 6)):
    add(f"y23_weight_{t}", "heavy", dict(kind="nested", rings=1, r=.85, lw=lw),
        "light", dict(kind="nested", rings=1, r=.85, lw=3),
        "Y23_stroke_weight", f"heavy (lw {lw}) vs light ring, same radius",
        "extent held constant; only ink weight differs")

# Y24 point count at equal depth ----------------------------------------------
for t, p2 in (("hi", 11), ("mid", 8), ("lo", 6)):
    add(f"y24_points_{t}", "few_points", dict(kind="star", points=4, r_in=.45),
        "many_points", dict(kind="star", points=p2, r_in=.45),
        "Y24_point_count", f"4-point vs {p2}-point star, equal depth",
        "only the number of repeated features differs")

# Y25 aspect vs vertex count --------------------------------------------------
for t, ar in (("hi", 3.4), ("mid", 2.2), ("lo", 1.5)):
    add(f"y25_aspect_vertex_{t}", "elongated_rect", dict(kind="aspect", ar=ar),
        "regular_polygon", dict(kind="poly", n=5, r=.72),
        "Y25_aspect_vertex", f"elongated rectangle (ar {ar}) vs regular pentagon",
        "elongation and regularity compete")


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
        if name in seen: raise SystemExit(f"duplicate id: {name}")
        if id1 == id2: raise SystemExit(f"{name}: identities must differ")
        seen.add(name)
        make(f"{name}_AB", s1, s2)
        make(f"{name}_BA", s2, s1)
    fams = sorted({p[5] for p in P})
    with open(os.path.join(OUT, "manifest.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stimulus_id","family","manipulation","identity_1","identity_2",
                    "image_path_AB","image_path_BA","generation_notes"])
        for name, id1, _a, id2, _b, fam, manip, note in P:
            w.writerow([name, fam, manip, id1, id2,
                        f"stimuli/v3/{name}_AB.png", f"stimuli/v3/{name}_BA.png", note])
    h = hashlib.sha256()
    for name, *_ in P:
        for v in ("AB","BA"):
            h.update(open(os.path.join(OUT, f"{name}_{v}.png"), "rb").read())
    open(os.path.join(OUT, "BATTERY_SHA256.txt"), "w").write(h.hexdigest()+"\n")
    print(f"{len(P)} stimuli in {len(fams)} families, {2*len(P)} images")
    print(f"battery sha256: {h.hexdigest()}")
    per = {}
    for p in P: per[p[5]] = per.get(p[5],0)+1
    assert all(v==3 for v in per.values()), per
    assert len(P)==75, len(P)


if __name__ == "__main__":
    main()
