"""
FROZEN 4-OPTION BATTERY - 15 families x 8 members = 120 stimuli.

DESIGN GOAL. Supply BOTH ends of a matched pair: stimuli where a policy lands on a
strong convention (self-match >= .75) and stimuli where it has a weak or ambiguous
convention (<= .45) that is NOT positional fallback. At 2 options the second kind
cannot exist - .50 is the floor and it is exactly where a position-responder sits.
At 4 options chance is .25, so a weak-but-real form rule occupies its own band.

Each family varies ONE parameter across 8 members, from a setting where the focal
pull should be strong to one where it should be weak. Which member lands where is
an empirical question answered by Stage A, not by this file.

NOT ADVERSARIALLY ENGINEERED. No stimulus was designed because a named model was
observed to prefer a named feature. Families were chosen for structural ambiguity
in general, written in one batch, and frozen before any API call. There is no
generate-test-regenerate loop. Same discipline and same wording as the Step-1
expansion battery (make_expansion_stimuli.py).

METHODS WORDING (use verbatim):
"We prospectively constructed a four-alternative battery because the two-alternative
format cannot dissociate weak model-specific conventions from positional fallback:
with two options the dyadic self-match statistic has a floor of .50, which is also
its value under position-based responding."

GEOMETRY. Each stimulus is a row of 4 panels, 1240x340 px, numbered 1-4 above each
panel. All 24 orderings of the 4 items are rendered as perm00..perm23.png with a
manifest mapping perm index -> item at each position. Palette and figure geometry
match the Step 1 batteries so nothing but arity changes.

Run:  python3 make_battery.py
"""
import os, json, csv, itertools
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle, RegularPolygon, Wedge

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "stimuli")

FILL, EDGE = "#9AA3B2", "#3A4152"
SEED = 20260830


# ----------------------------------------------------------------- drawing ----
PANEL = "#F1F2F4"          # panel ground: groups each option's marks unambiguously


def _ax(ax):
    # A tinted panel ground is not decoration. Sparse random-placement families
    # (dots) otherwise spill visually across panel gaps, so an option's marks
    # cannot be attributed to its own number - caught on F13_count at render
    # review, where a 1-vs-2-vs-3-vs-5 dot count was unreadable.
    # NB: ax.axis("off") sets frame_on=False, and in matplotlib the axes patch
    # visibility IS frame_on - so the ground must be kept by hiding spines and
    # ticks individually rather than by axis("off").
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_frame_on(True)
    ax.set_facecolor(PANEL)
    return ax


def blob(ax, seed, spike=0.0, n=180, scale=0.9, rot=0.0):
    rng = np.random.default_rng(seed)
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = np.ones(n)
    for k, amp in zip((2, 3, 5, 7), (0.18, 0.12, 0.07, 0.05)):
        r += amp * np.sin(k * a + rng.uniform(0, 2 * np.pi))
    if spike:
        r += spike * 0.30 * np.sin(11 * a + rng.uniform(0, 2 * np.pi))
    r = scale * r / r.max()
    xy = np.c_[r * np.cos(a + rot), r * np.sin(a + rot)]
    _ax(ax).add_patch(Polygon(xy, facecolor=FILL, edgecolor=EDGE, linewidth=2.5))


def ngon(ax, k, rot=0.0, scale=0.9):
    _ax(ax).add_patch(RegularPolygon((0, 0), k, radius=scale, orientation=rot,
                                     facecolor=FILL, edgecolor=EDGE, linewidth=2.5))


def dots(ax, count, seed, r=0.075):
    # Placement radius is deliberately well inside the panel (0.72, not 0.95) so
    # marks stay attributable to their own option even at count = 1.
    rng = np.random.default_rng(seed)
    _ax(ax)
    lim = 0.72
    pts, tries = [], 0
    while len(pts) < count and tries < 40000:
        tries += 1
        p = rng.uniform(-lim, lim, 2)
        if np.hypot(*p) > lim:
            continue
        if all(np.hypot(*(p - q)) > 2.2 * r for q in pts):
            pts.append(p)
    for p in pts:
        ax.add_patch(Circle(p, r, facecolor=EDGE, edgecolor="none"))


def grey(ax, level):
    _ax(ax).add_patch(Circle((0, 0), 0.9, facecolor=str(level), edgecolor=EDGE,
                             linewidth=2.5))


def arc(ax, gap_deg, rot=0.0):
    _ax(ax).add_patch(Wedge((0, 0), 0.92, rot + gap_deg / 2, rot + 360 - gap_deg / 2,
                            width=0.26, facecolor=FILL, edgecolor=EDGE, linewidth=2.5))


def bar_group(ax, heights):
    _ax(ax)
    w, x0 = 0.34, -0.75
    for i, h in enumerate(heights):
        ax.add_patch(Rectangle((x0 + i * 0.5, -0.9), w, 1.8 * h,
                               facecolor=FILL, edgecolor=EDGE, linewidth=2.0))


def texture(ax, seed, res):
    rng = np.random.default_rng(seed)
    ax.imshow(rng.random((res, res)), cmap="gray", vmin=0, vmax=1,
              interpolation="nearest")
    ax.axis("off")


# ---------------------------------------------------------------- families ----
# Each entry: name -> (member_param -> list of 4 item drawers).
# `t` runs 0..7 across the 8 members and modulates how strong the focal pull is.
def fam_odd_one_out(t):
    """3 identical + 1 different; the difference shrinks as t rises."""
    d = 0.85 - 0.11 * t
    return [lambda ax: ngon(ax, 6), lambda ax: ngon(ax, 6), lambda ax: ngon(ax, 6),
            lambda ax, d=d: ngon(ax, 6, scale=0.9 * (1 - 0.5 * d))]


def fam_size_ladder(t):
    """Four sizes; spacing compresses as t rises."""
    sp = 0.22 - 0.026 * t
    return [lambda ax, s=0.45 + i * sp: ngon(ax, 20, scale=s) for i in range(4)]


def fam_symmetry(t):
    """3/4/5/6-fold symmetry; rotation jitter grows with t."""
    j = 0.13 * t
    return [lambda ax, k=k, r=j * (i % 2): ngon(ax, k, rot=r)
            for i, k in enumerate((3, 4, 5, 6))]


def fam_complexity(t):
    """Vertex count; the range narrows as t rises."""
    base = [3, 5, 8, 14]
    ks = [max(3, int(round(3 + (k - 3) * (1 - 0.09 * t)))) for k in base]
    return [lambda ax, k=k: ngon(ax, k) for k in ks]


def fam_orientation(t):
    """One asymmetric blob at 4 rotations; blob identity varies with t."""
    return [lambda ax, r=r, s=SEED + 700 + t: blob(ax, s, rot=r)
            for r in (0.0, np.pi / 2, np.pi, 3 * np.pi / 2)]


def fam_density(t):
    """Dot count; the ratio between members compresses as t rises."""
    lo, hi = 3, 28 - 3 * t
    cs = np.round(np.geomspace(lo, max(lo + 3, hi), 4)).astype(int)
    return [lambda ax, c=int(c), s=SEED + 800 + t + i: dots(ax, c, s)
            for i, c in enumerate(cs)]


def fam_contrast(t):
    """Four greys; the spread narrows as t rises."""
    sp = 0.30 - 0.033 * t
    return [lambda ax, g=0.5 + (i - 1.5) * sp: grey(ax, min(0.95, max(0.05, g)))
            for i in range(4)]


def fam_closure(t):
    """Arc gap size; gaps converge as t rises."""
    gaps = [4 + i * (40 - 4.4 * t) for i in range(4)]
    return [lambda ax, g=max(2, g): arc(ax, g) for g in gaps]


def fam_convexity(t):
    """Two convex, two spiky; spikiness falls as t rises."""
    sp = 1.0 - 0.12 * t
    return [lambda ax: ngon(ax, 12), lambda ax: ngon(ax, 4),
            lambda ax, s=sp: blob(ax, SEED + 901, spike=s),
            lambda ax, s=sp: blob(ax, SEED + 902, spike=s)]


def fam_curvature(t):
    """Four blobs, spikiness ladder; ladder compresses as t rises."""
    return [lambda ax, s=(i * (0.9 - 0.1 * t)) / 3.0, sd=SEED + 1000 + t * 4 + i:
            blob(ax, sd, spike=s) for i in range(4)]


def fam_noise(t):
    """Four independent textures - no focal point by construction. Resolution varies."""
    res = [24, 20, 16, 12, 10, 8, 6, 5][t]
    return [lambda ax, s=SEED + 1100 + t * 4 + i, r=res: texture(ax, s, r)
            for i in range(4)]


def fam_mirror(t):
    """A blob, its mirror, and two rotations - all the same form up to isometry."""
    sd = SEED + 1200 + t
    return [lambda ax, s=sd: blob(ax, s),
            lambda ax, s=sd: blob(ax, s, rot=np.pi),
            lambda ax, s=sd + 40: blob(ax, s),
            lambda ax, s=sd + 40: blob(ax, s, rot=np.pi)]


def fam_count(t):
    """Element counts 1/2/3/5; counts converge as t rises."""
    cs = [1, 2, 3, 5] if t < 4 else [2, 3, 4, 5]
    return [lambda ax, c=c, s=SEED + 1300 + t: dots(ax, c, s, r=0.16) for c in cs]


def fam_bars(t):
    """Bar-height profiles: rising, falling, flat, peaked; contrast falls with t."""
    a = 1.0 - 0.1 * t
    return [lambda ax: bar_group(ax, [0.3, 0.5, 0.7, 0.9 * a]),
            lambda ax: bar_group(ax, [0.9 * a, 0.7, 0.5, 0.3]),
            lambda ax: bar_group(ax, [0.6, 0.6, 0.6, 0.6]),
            lambda ax: bar_group(ax, [0.35, 0.9 * a, 0.9 * a, 0.35])]


def fam_ring(t):
    """Ring of k elements, k = 3..6; element size varies with t."""
    r = 0.16 - 0.011 * t
    def ring(ax, k, rr):
        _ax(ax)
        for j in range(k):
            a = 2 * np.pi * j / k + np.pi / 2
            ax.add_patch(Circle((0.62 * np.cos(a), 0.62 * np.sin(a)), rr,
                                facecolor=FILL, edgecolor=EDGE, linewidth=2.0))
    return [lambda ax, k=k, rr=r: ring(ax, k, rr) for k in (3, 4, 5, 6)]


def fam_aspect(t):
    """Four rectangles by aspect ratio; the ladder compresses as t rises."""
    ars = [1.0, 1.5, 2.2, 3.2]
    ars = [1 + (a - 1) * (1 - 0.1 * t) for a in ars]
    def rect(ax, a):
        _ax(ax)
        h = 0.85 / max(1.0, a) ** 0.5
        w = h * a
        ax.add_patch(Rectangle((-w, -h), 2 * w, 2 * h, facecolor=FILL,
                               edgecolor=EDGE, linewidth=2.5))
    return [lambda ax, a=a: rect(ax, a) for a in ars]


FAMILIES = {
    "F01_oddone": fam_odd_one_out, "F02_size": fam_size_ladder,
    "F03_symmetry": fam_symmetry, "F04_complexity": fam_complexity,
    "F05_orient": fam_orientation, "F06_density": fam_density,
    "F07_contrast": fam_contrast, "F08_closure": fam_closure,
    "F09_convexity": fam_convexity, "F10_curvature": fam_curvature,
    "F11_noise": fam_noise, "F12_mirror": fam_mirror,
    "F13_count": fam_count, "F14_bars": fam_bars,
    "F15_ring": fam_ring, "F16_aspect": fam_aspect,
}
MEMBERS = 8


# ----------------------------------------------------------------- render -----
def render(sid, drawers):
    d = os.path.join(OUT, sid)
    os.makedirs(d, exist_ok=True)
    manifest = {}
    for pi, perm in enumerate(itertools.permutations(range(4))):
        fig, axes = plt.subplots(1, 4, figsize=(12.4, 3.4), dpi=100)
        for pos, ax in enumerate(axes):
            drawers[perm[pos]](ax)
            ax.set_title(str(pos + 1), fontsize=19, color="#222", pad=8)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.02, wspace=0.16)
        fig.savefig(os.path.join(d, f"perm{pi:02d}.png"), facecolor="white")
        plt.close(fig)
        manifest[str(pi)] = list(perm)          # item index at position 0..3
    json.dump(manifest, open(os.path.join(d, "manifest.json"), "w"), indent=1)
    return d


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for fam, fn in FAMILIES.items():
        for t in range(MEMBERS):
            sid = f"{fam}_m{t}"
            render(sid, fn(t))
            rows.append(dict(stimulus_id=sid, family=fam, member=t, n_options=4,
                             n_perms=24, dir=os.path.join(OUT, sid)))
            print(f"  {sid}")
    with open(os.path.join(OUT, "battery_manifest.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\n{len(rows)} stimuli x 24 perms -> {OUT}")

    fig, axes = plt.subplots(len(FAMILIES), 1, figsize=(12, 2.0 * len(FAMILIES)),
                             dpi=70)
    for ax, fam in zip(axes, FAMILIES):
        ax.imshow(plt.imread(os.path.join(OUT, f"{fam}_m0", "perm00.png")))
        ax.axis("off"); ax.set_title(f"{fam}  (member 0 of {MEMBERS})", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "gallery.png"), facecolor="white")
    plt.close(fig)
    print(f"gallery -> {os.path.join(OUT, 'gallery.png')}")


if __name__ == "__main__":
    main()
