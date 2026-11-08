"""Battery 6 - targeted GPT-focal REPAIR arrays, driven by GPT_POSITION_DIAGNOSIS.md.

The diagnosis: the two failed GPT-focal arrays are not weak (share .83-.90, advantage
+.41/+.58). They lose the locked object at SCREEN POSITION 1 only, and in each case the
entire loss is absorbed by ONE named rival. Nesting additionally has unmatched extent
(outer radii .62/.98/.92/.92).

So each repair does four things and nothing else:
  1. equalise outer extent and visual mass across all four objects;
  2. modestly weaken the specific rival that absorbed the loss;
  3. modestly strengthen the locked object on ONE dimension only;
  4. remove directional/orientation cues that could interact with slot order.

NOT done: no ladders, no odd-one-out, no strengthening on every dimension, no palette
variants, no trivial distractors, no optimisation against confirmation data (the rivals were
identified from the POSITION table, not from which object scored best).

Primitives are imported from make_battery5 so geometry and palette are identical.
"""
import csv, hashlib, importlib.util, io, itertools, json, os
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("mb5", os.path.join(HERE, "make_battery5.py"))
mb5 = importlib.util.module_from_spec(_spec)
_src = open(os.path.join(HERE, "make_battery5.py")).read().split("# =============================== QA + RENDER")[0]
exec(compile(_src, "mb5", "exec"), mb5.__dict__)

OUT = os.path.join(os.path.dirname(HERE), "stimuli6")
PANEL, EDGE, FILL = mb5.PANEL, mb5.EDGE, mb5.FILL
_ax, rings, patch, strokes = mb5._ax, mb5.rings, mb5.patch, mb5.strokes
INK_TOL = (0.55, 1.80)          # tighter than battery5: mass matching IS the repair
CENTRE_TOL = 0.020              # ink centroid vs panel centre, as a fraction of panel width
MARGIN_TOL = 0.035              # |left-right| and |top-bottom| bbox margin difference
R_OUT = 0.88                    # every object inscribed in the SAME outer radius


def ring_set(ax, radii, lw):
    """Concentric rings at explicit radii, always reaching R_OUT so extent is matched."""
    _ax(ax)
    for r in radii:
        ax.add_patch(Circle((0, 0), r, facecolor="none", edgecolor=EDGE, linewidth=lw))


def geom_rings(ax, n, lw, ratio=0.66):
    ring_set(ax, [R_OUT * ratio ** i for i in range(n)], lw)


def even_rings(ax, n, lw):
    ring_set(ax, list(np.linspace(R_OUT, R_OUT * 0.30, n)) if n > 1 else [R_OUT], lw)


def jit_rings(ax, n, lw, seed=7):
    rng = np.random.default_rng(seed)
    base = np.linspace(R_OUT, R_OUT * 0.30, n)
    ring_set(ax, [b + rng.uniform(-0.055, 0.055) for b in base[:-1]] + [base[-1]], lw)


def ring_closed(ax, lw):
    _ax(ax); ax.add_patch(Circle((0, 0), R_OUT, facecolor="none", edgecolor=EDGE, linewidth=lw))


def spokes(ax, n, lw):
    """n full diameters => 2n radial arms, centred, no directional bias (evenly spread)."""
    _ax(ax)
    for a in np.linspace(0, np.pi, n, endpoint=False):
        ax.plot([-R_OUT * np.cos(a), R_OUT * np.cos(a)], [-R_OUT * np.sin(a), R_OUT * np.sin(a)],
                color=EDGE, lw=lw, solid_capstyle="round")


def bars(ax, n, lw):
    """n parallel chords inside the same circumscribed radius - matched extent."""
    _ax(ax)
    ys = np.linspace(R_OUT * 0.78, -R_OUT * 0.78, n)
    for y in ys:
        half = np.sqrt(max(R_OUT ** 2 - y ** 2, 0.01))
        ax.plot([-half, half], [y, y], color=EDGE, lw=lw, solid_capstyle="round")


def conc_arcs(ax, n, lw, span=150):
    """n concentric open arcs, symmetric about the vertical axis (no direction cue)."""
    _ax(ax)
    for r in np.linspace(R_OUT, R_OUT * 0.34, n):
        a = np.deg2rad(np.linspace(90 - span / 2, 90 + span / 2, 120))
        ax.plot(r * np.cos(a), r * np.sin(a), color=EDGE, lw=lw, solid_capstyle="round")
        ax.plot(r * np.cos(a), -r * np.sin(a), color=EDGE, lw=lw, solid_capstyle="round")


def _patch6(ax, pts, r):
    _ax(ax)
    ax.add_patch(Circle((0, 0), 0.95, facecolor="white", edgecolor=EDGE, linewidth=2.4))
    for x, y in pts:
        ax.add_patch(Circle((x, y), r, facecolor=EDGE, edgecolor="none"))


def lattice(ax, n, r, seed):
    """Lattice points chosen NEAREST-TO-CENTRE, so the mark centroid is centred.

    make_battery5.patch() takes the first n points of a top-to-bottom raster scan, which
    biases the centroid upward (0.029 off centre, caught by the new centring assertion).
    battery5 shipped with that; it is corrected here rather than by editing battery5.
    """
    lim = 0.95 - r - 0.02
    side = int(np.ceil(np.sqrt(n / (np.pi / 4)))) + 4
    g = np.linspace(-lim, lim, side)
    pts = [(x, y) for y in g for x in g if np.hypot(x, y) <= lim]
    pts.sort(key=lambda p: np.hypot(*p))
    _patch6(ax, pts[:n], r)


def rnd(ax, n, r, seed):
    """Uniform in the disc, then mean-centred so the centroid is exact."""
    lim = 0.95 - r - 0.02
    rng = np.random.default_rng(seed)
    pts = []
    while len(pts) < n:
        q = rng.uniform(-lim, lim, 2)
        if np.hypot(*q) <= lim: pts.append(q)
    pts = np.array(pts); pts -= pts.mean(axis=0)
    _patch6(ax, pts, r)


def clus(ax, n, r, seed):
    """Three clusters placed symmetrically at 120 degrees, then mean-centred."""
    lim = 0.95 - r - 0.02
    rng = np.random.default_rng(seed)
    cen = np.c_[0.42 * lim * np.cos(np.linspace(0, 2*np.pi, 3, endpoint=False) + np.pi/2),
                0.42 * lim * np.sin(np.linspace(0, 2*np.pi, 3, endpoint=False) + np.pi/2)]
    pts = []
    while len(pts) < n:
        q = cen[len(pts) % 3] + rng.normal(0, lim * 0.20, 2)
        if np.hypot(*q) <= lim: pts.append(q)
    pts = np.array(pts); pts -= pts.mean(axis=0)
    _patch6(ax, pts, r)


S = 20260909
A = []


def add(mech, variant, objs, rules, intended, note):
    A.append(dict(mechanism=mech, family=f"R_{mech}", variant=variant, objects=objs,
                  rules=rules, intended_gpt=intended, note=note))


# ---- line_contour: locked = the single CLOSED ring; rival to weaken = crossing star -----
for v, (lw_lock, n_spokes, lw_spoke, n_bars, n_arcs) in enumerate(
        [(8, 3, 7, 5, 4), (8, 3, 8, 6, 5), (9, 3, 7, 6, 3)]):
    add("line_contour", v,
        [("closed_ring",  (lambda ax, w=lw_lock: ring_closed(ax, w))),
         ("parallel_bars", (lambda ax, n=n_bars: bars(ax, n, 5))),
         ("radial_spokes", (lambda ax, n=n_spokes, w=lw_spoke: spokes(ax, n, w))),
         ("concentric_arcs", (lambda ax, n=n_arcs: conc_arcs(ax, n, 5)))],
        dict(only_closed=0, thickest_stroke=0, most_components=1, parallel_alignment=1,
             most_intersections=2, radial_symmetry=2, most_curved_open=3, nested_repetition=3),
        "closed_ring",
        "rival radial-star weakened STRUCTURALLY to %d diameters (was 4); stroke kept at "
        "lw %d so the weakening is not merely an ink reduction; all objects inscribed in R_OUT"
        % (n_spokes, lw_spoke))

# ---- nesting: locked = many geometric rings; rival to weaken = the thick 2-ring ---------
for v, (n_lock, lw_lock, lw_rival, n_even, n_jit) in enumerate(
        [(5, 4, 5, 3, 4), (6, 4, 4, 3, 4), (5, 5, 4, 4, 3)]):
    add("nesting", v,
        [("geom_rings",  (lambda ax, n=n_lock, w=lw_lock: geom_rings(ax, n, w))),
         ("even_rings",  (lambda ax, n=n_even: even_rings(ax, n, 4))),
         ("thick_pair",  (lambda ax, w=lw_rival: even_rings(ax, 2, w))),
         ("jitter_rings", (lambda ax, n=n_jit: jit_rings(ax, n, 4)))],
        dict(most_rings=0, centre_dense=0, most_regular=1, mid_count=1,
             thickest_stroke=2, fewest_rings=2, irregular_spacing=3, mid_density=3),
        "geom_rings",
        "extent equalised at R_OUT for all four (v3 had radii .62/.98/.92/.92); "
        "thick-pair rival thinned to lw %d" % lw_rival)

# ---- noise_texture: independent 3rd mechanism, locked = the regular lattice -------------
for v, (n_lat, r_lat) in enumerate([(150, .036), (190, .032)]):
    n_coarse, r_coarse = int(n_lat * 0.36), r_lat * 5 / 3
    add("noise_texture", v,
        [("fine_lattice",   (lambda ax, n=n_lat, r=r_lat, i=v: lattice(ax, n, r, S + 300 + i))),
         ("coarse_lattice", (lambda ax, n=n_coarse, r=r_coarse, i=v: lattice(ax, n, r, S + 350 + i))),
         ("random",         (lambda ax, n=n_lat, r=r_lat, i=v: rnd(ax, n, r, S + 400 + i))),
         ("clustered",      (lambda ax, n=n_lat, r=r_lat, i=v: clus(ax, n, r, S + 500 + i)))],
        dict(finest_grain=0, most_uniform_coverage=0, coarsest_grain=1, fewest_marks=1,
             most_irregular=2, mid_density=2, most_clustered=3, most_structured_globally=3),
        "fine_lattice",
        "TWO lattices (fine and coarse) so regularity is NOT unique to the intended object - "
        "the first draft made the single lattice an obvious odd-one-out among three scatters")


# =============================== QA + RENDER ==================================
def object_png(fn, dpi=100):
    fig, ax = plt.subplots(figsize=(3.1, 3.4), dpi=dpi)
    fn(ax); fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    buf = io.BytesIO(); fig.savefig(buf, facecolor=PANEL); plt.close(fig)
    return buf.getvalue()


def _mask(png):
    import matplotlib.image as mpimg
    a = mpimg.imread(io.BytesIO(png))[:, :, :3]
    L = a @ np.array([0.2126, 0.7152, 0.0722])
    bgL = np.array([int(PANEL[i:i+2], 16)/255 for i in (1, 3, 5)]) @ np.array([0.2126, 0.7152, 0.0722])
    return a, (L < bgL - 0.15)


def ink_fraction(png):
    return float(_mask(png)[1].mean())


def centring(png):
    """(centroid offset, |L-R| margin diff, |T-B| margin diff), all as fractions of size."""
    _, m = _mask(png)
    h, w = m.shape
    ys, xs = np.where(m)
    cx, cy = xs.mean() / w, ys.mean() / h
    off = float(np.hypot(cx - 0.5, cy - 0.5))
    lr = abs(xs.min() / w - (1 - xs.max() / w))
    tb = abs(ys.min() / h - (1 - ys.max() / h))
    return off, float(lr), float(tb)


def bbox_ok(png, margin=3):
    _, m = _mask(png)
    if not m.any(): return False
    ys, xs = np.where(m); h, w = m.shape
    return bool(ys.min() > margin and xs.min() > margin
                and ys.max() < h-1-margin and xs.max() < w-1-margin)


def palette_ok(png, tol=0.16):
    a, _ = _mask(png); return bool(np.ptp(a, axis=2).max() <= tol)


def min_contrast(png):
    a, _ = _mask(png)
    bg = np.array([int(PANEL[i:i+2], 16)/255 for i in (1, 3, 5)])
    return float(np.abs(a - bg).sum(axis=2).max())


def no_unique_colour(pngs, tol=0.05):
    vs = []
    for p in pngs:
        a, m = _mask(p); px = a[m]
        mu = px.mean(axis=0) if len(px) else np.zeros(3)
        vs.append(mu - mu.mean())
    worst = max(float(np.linalg.norm(vs[i] - np.mean([vs[j] for j in range(4) if j != i], axis=0)))
                for i in range(4))
    return worst <= tol, round(worst, 4)


def render(sid, objs):
    d = os.path.join(OUT, sid); os.makedirs(d, exist_ok=True)
    man = {}
    for pi, perm in enumerate(itertools.permutations(range(4))):
        fig, axes = plt.subplots(1, 4, figsize=(12.4, 3.4), dpi=100)
        for pos, ax in enumerate(axes):
            objs[perm[pos]][1](ax)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.03, wspace=0.16)
        fig.savefig(os.path.join(d, f"perm{pi:02d}.png"), facecolor="white"); plt.close(fig)
        man[str(pi)] = list(perm)
    json.dump(man, open(os.path.join(d, "manifest.json"), "w"), indent=1)
    return d


def main():
    os.makedirs(OUT, exist_ok=True)
    rows, cues, qa = [], [], []
    for spec in A:
        sid = f"{spec['family']}_v{spec['variant']}".lower()
        objs, rules = spec["objects"], spec["rules"]
        names = [o[0] for o in objs]
        assert len(objs) == 4 and len(set(names)) == 4, sid
        wins = Counter(rules.values())
        assert all(wins[i] >= 1 for i in range(4)), f"{sid}: object favoured by no rule"
        assert all(wins[i] <= 2 for i in range(4)), f"{sid}: dominant object {wins}"
        assert spec["intended_gpt"] in names, f"{sid}: intended object not present"
        ig = names.index(spec["intended_gpt"])
        assert wins[ig] <= 2, f"{sid}: intended GPT object dominates ({wins[ig]} rules)"

        pngs = [object_png(fn) for _, fn in objs]
        assert len({hashlib.sha256(p).hexdigest() for p in pngs}) == 4, f"{sid}: identical objects"
        cen = []
        for nm, p in zip(names, pngs):
            assert palette_ok(p), f"{sid}/{nm}: off-palette"
            assert min_contrast(p) >= 0.25, f"{sid}/{nm}: too faint"
            assert bbox_ok(p), f"{sid}/{nm}: clipped"
            off, lr, tb = centring(p)
            assert off <= CENTRE_TOL, f"{sid}/{nm}: centroid off-centre {off:.3f}"
            assert lr <= MARGIN_TOL and tb <= MARGIN_TOL, f"{sid}/{nm}: unequal margins {lr:.3f}/{tb:.3f}"
            cen.append((off, lr, tb))
        okc, worstc = no_unique_colour(pngs)
        assert okc, f"{sid}: uniquely coloured object {worstc}"
        ink = [ink_fraction(p) for p in pngs]; mean = sum(ink)/4
        ratios = [i/mean for i in ink]
        bad = [(n, round(r, 2)) for n, r in zip(names, ratios) if not (INK_TOL[0] <= r <= INK_TOL[1])]
        assert not bad, f"{sid}: ink imbalance {bad}"

        d = render(sid, objs)
        ph = [hashlib.sha256(open(os.path.join(d, f"perm{i:02d}.png"), "rb").read()).hexdigest()
              for i in range(24)]
        assert len(set(ph)) == 24, f"{sid}: permutation renders collide"
        m = json.load(open(os.path.join(d, "manifest.json")))
        bal = Counter((it, pos) for o in m.values() for pos, it in enumerate(o))
        assert set(bal.values()) == {6} and len(bal) == 16, f"{sid}: balance broken"

        rows.append(dict(array_id=sid, family=spec["family"], mechanism=spec["mechanism"],
                         variant=spec["variant"], n_options=4, n_perms=24, dir=d,
                         objects="|".join(names), n_rules=len(rules),
                         intended_gpt_object=spec["intended_gpt"], intended_gpt_index=ig,
                         ink_ratios="|".join(f"{r:.2f}" for r in ratios),
                         max_centroid_off=round(max(c[0] for c in cen), 4),
                         max_margin_diff=round(max(max(c[1], c[2]) for c in cen), 4),
                         note=spec["note"]))
        for rule, w in sorted(rules.items()):
            cues.append(dict(array_id=sid, mechanism=spec["mechanism"], rule=rule,
                             favoured_object_index=w, favoured_object=names[w],
                             is_intended_gpt_object=int(w == ig)))
        qa.append(dict(array_id=sid, wins_per_object="|".join(str(wins[i]) for i in range(4)),
                       intended_gpt_wins=wins[ig], n_rules=len(rules),
                       ink_min=round(min(ratios), 2), ink_max=round(max(ratios), 2),
                       max_centroid_off=round(max(c[0] for c in cen), 4),
                       max_margin_diff=round(max(max(c[1], c[2]) for c in cen), 4),
                       hue_outlier=worstc, perms_distinct=len(set(ph)), balance_ok=True))
        print(f"  {sid:24} {spec['mechanism']:14} wins={[wins[i] for i in range(4)]} "
              f"ink {min(ratios):.2f}-{max(ratios):.2f} centre<={max(c[0] for c in cen):.3f}")

    for fn, data in (("battery6_manifest.csv", rows), ("cue_table6.csv", cues), ("qa_report6.csv", qa)):
        with open(os.path.join(OUT, fn), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys())); w.writeheader(); w.writerows(data)
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda x: x["array_id"]):
        for i in range(24):
            h.update(open(os.path.join(r["dir"], f"perm{i:02d}.png"), "rb").read())
    open(os.path.join(OUT, "BATTERY6_SHA256.txt"), "w").write(h.hexdigest() + "\n")
    print(f"\n{len(rows)} arrays, {24*len(rows)} images, {len(cues)} cue rows")
    print("mechanisms:", dict(Counter(r["mechanism"] for r in rows)))
    print("battery sha256:", h.hexdigest())


if __name__ == "__main__":
    main()
