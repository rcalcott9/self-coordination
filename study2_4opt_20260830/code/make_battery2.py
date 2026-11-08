"""
EXPANSION BATTERY 2 - 25 NEW families x 3 variants = 75 stimuli (F17..F41).

WHY WIDEN RATHER THAN DEEPEN. Family is the unit of independence: eight variants of
one structural manipulation are replication, not eight observations. Discovery on
battery 1 gave GPT 14 policy-specific highs from only 6 families and 19 lows from
5, capping distinct-family pairs at 5 (GPT) / 4 (Claude). More families is the only
thing that raises that ceiling.

WHAT THE LOW MEMBER IS FOR. Not merely to create a large contrast. It tests whether
the focal model BACKS OFF when its own policy is unreliable *even when told the
partner is another instance of itself*. That is what rules out the trivial
heuristic "partner is my model, therefore coordinate". So the scarce resource is a
weak, NON-POSITIONAL convention for the same focal model that has a strong
model-specific convention elsewhere.

DESIGN SPLIT. Roughly half the families offer a defensible focal candidate
(extremes, odd-one-out, canonical orientation); the other half deliberately present
four near-equivalent options - transformations of one form, or a parameter varied
too finely to rank - which is where battery 1's non-positional lows came from
(F05_orient, F11_noise, F12_mirror, F16_aspect).

Variants t = 0,1,2 compress the distinguishing parameter: t=0 widest separation,
t=2 tightest. Which variant lands high or low is decided by Stage A, not here.

NOT ADVERSARIALLY ENGINEERED. Families were chosen for structural ambiguity in
general, written in one batch, and frozen before any Stage A call on them. No
family was designed because a named model was observed to prefer a named feature.

Run:  python3 make_battery2.py
"""
import os, json, csv, itertools
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (Circle, Polygon, Rectangle, RegularPolygon, Wedge,
                                Ellipse, FancyBboxPatch, Arc)
from make_battery import _ax, blob, ngon, dots, grey, arc, texture, FILL, EDGE, SEED

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "stimuli")


# ------------------------------------------------------------- primitives ----
def star(ax, n, inner=0.42, rot=0.0, scale=0.92):
    a = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False) + rot + np.pi / 2
    r = np.where(np.arange(2 * n) % 2 == 0, scale, scale * inner)
    _ax(ax).add_patch(Polygon(np.c_[r * np.cos(a), r * np.sin(a)],
                              facecolor=FILL, edgecolor=EDGE, linewidth=2.2))


def ellipse(ax, w, h, ang=0.0):
    _ax(ax).add_patch(Ellipse((0, 0), w, h, angle=ang, facecolor=FILL,
                              edgecolor=EDGE, linewidth=2.4))


def annulus(ax, hole):
    _ax(ax)
    ax.add_patch(Wedge((0, 0), 0.9, 0, 360, width=0.9 - hole, facecolor=FILL,
                       edgecolor=EDGE, linewidth=2.2))


def lines(ax, k, ang=90.0, span=1.4):
    _ax(ax)
    a = np.deg2rad(ang)
    dx, dy = np.cos(a), np.sin(a)
    offs = np.linspace(-0.55, 0.55, k) if k > 1 else [0.0]
    for o in offs:
        px, py = -dy * o, dx * o
        ax.plot([px - dx * span / 2, px + dx * span / 2],
                [py - dy * span / 2, py + dy * span / 2],
                color=EDGE, lw=4, solid_capstyle="round")


def notched(ax, depth, ang=90.0):
    a = np.linspace(0, 2 * np.pi, 240, endpoint=False)
    r = np.full_like(a, 0.9)
    c = np.deg2rad(ang)
    d = np.abs(np.angle(np.exp(1j * (a - c))))
    r -= depth * 0.9 * np.exp(-(d / 0.32) ** 2)
    _ax(ax).add_patch(Polygon(np.c_[r * np.cos(a), r * np.sin(a)],
                              facecolor=FILL, edgecolor=EDGE, linewidth=2.4))


def rounded(ax, rad):
    _ax(ax).add_patch(FancyBboxPatch((-0.62, -0.62), 1.24, 1.24,
                                     boxstyle=f"round,pad=0,rounding_size={rad}",
                                     facecolor=FILL, edgecolor=EDGE, linewidth=2.4))


def nested(ax, k):
    _ax(ax)
    for i in range(k):
        ax.add_patch(Circle((0, 0), 0.9 - i * (0.72 / max(k, 1)), facecolor="none",
                            edgecolor=EDGE, linewidth=3.0))


def split_bar(ax, frac):
    _ax(ax)
    ax.add_patch(Rectangle((-0.8, -0.34), 1.6 * frac, 0.68, facecolor=EDGE,
                           edgecolor=EDGE, linewidth=1.5))
    ax.add_patch(Rectangle((-0.8 + 1.6 * frac, -0.34), 1.6 * (1 - frac), 0.68,
                           facecolor="#DDE0E5", edgecolor=EDGE, linewidth=1.5))


def two_circles(ax, sep):
    _ax(ax)
    for s in (-1, 1):
        ax.add_patch(Circle((s * sep / 2, 0), 0.46, facecolor=FILL, edgecolor=EDGE,
                            linewidth=2.2, alpha=0.85))


def hatched(ax, kind):
    _ax(ax)
    hs = {"solid": None, "diag": "///", "dot": "...", "cross": "xxx"}[kind]
    ax.add_patch(Circle((0, 0), 0.85, facecolor=FILL if hs is None else "white",
                        edgecolor=EDGE, linewidth=2.4, hatch=hs))


def contained(ax, pos):
    _ax(ax)
    ax.add_patch(Rectangle((-0.85, -0.85), 1.7, 1.7, facecolor="none",
                           edgecolor=EDGE, linewidth=2.4))
    ax.add_patch(Circle(pos, 0.24, facecolor=FILL, edgecolor=EDGE, linewidth=2.0))


def crossing(ax, ang):
    _ax(ax)
    for a in (0.0, np.deg2rad(ang)):
        dx, dy = np.cos(a), np.sin(a)
        ax.plot([-dx, dx], [-dy, dy], color=EDGE, lw=4, solid_capstyle="round")


def cap_line(ax, cap):
    _ax(ax)
    ax.plot([-0.7, 0.7], [0, 0], color=EDGE, lw=6,
            solid_capstyle={"butt": "butt", "round": "round",
                            "proj": "projecting"}.get(cap, "butt"))
    if cap == "dot":
        for x in (-0.7, 0.7):
            ax.add_patch(Circle((x, 0), 0.15, facecolor=EDGE, edgecolor="none"))


def wedge_gap(ax, clock):
    arc(ax, 46, rot=clock)


def jitter_poly(ax, amt, seed):
    rng = np.random.default_rng(seed)
    a = np.linspace(0, 2 * np.pi, 9, endpoint=False)
    r = 0.9 * (1 + amt * rng.uniform(-1, 1, 9))
    _ax(ax).add_patch(Polygon(np.c_[r * np.cos(a), r * np.sin(a)],
                              facecolor=FILL, edgecolor=EDGE, linewidth=2.4))


def subdiv(ax, k):
    _ax(ax)
    ax.add_patch(Rectangle((-0.8, -0.8), 1.6, 1.6, facecolor="none", edgecolor=EDGE,
                           linewidth=2.4))
    for i in range(1, k):
        x = -0.8 + 1.6 * i / k
        ax.plot([x, x], [-0.8, 0.8], color=EDGE, lw=2.2)


def gradient(ax, ang):
    g = np.linspace(0, 1, 128)[None, :].repeat(128, 0)
    g = np.rot90(g, k=int(round(ang / 90.0)) % 4)
    ax.imshow(g, cmap="gray", vmin=-0.3, vmax=1.3, interpolation="bilinear")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)


# ---------------------------------------------------------------- families ----
# t = 0 widest separation -> 2 tightest.
def F17_gapclock(t):
    sp = [90, 55, 30][t]
    return [lambda ax, c=i * sp: wedge_gap(ax, c) for i in range(4)]


def F18_stroke(t):
    ws = [[1.2, 3.0, 5.5, 9.0], [2.0, 3.4, 5.0, 7.0], [3.0, 3.9, 4.8, 5.8]][t]
    def f(ax, w):
        _ax(ax).add_patch(Circle((0, 0), 0.82, facecolor="none", edgecolor=EDGE,
                                 linewidth=w))
    return [lambda ax, w=w: f(ax, w) for w in ws]


def F19_fill(t):
    ks = [["solid", "diag", "dot", "cross"], ["diag", "dot", "cross", "solid"],
          ["dot", "cross", "diag", "solid"]][t]
    return [lambda ax, k=k: hatched(ax, k) for k in ks]


def F20_corner(t):
    rs = [[0.02, 0.22, 0.42, 0.60], [0.10, 0.24, 0.38, 0.52],
          [0.20, 0.28, 0.36, 0.44]][t]
    return [lambda ax, r=r: rounded(ax, r) for r in rs]


def F21_notch(t):
    ds = [[0.05, 0.30, 0.55, 0.80], [0.15, 0.32, 0.49, 0.66],
          [0.28, 0.38, 0.48, 0.58]][t]
    return [lambda ax, d=d: notched(ax, d) for d in ds]


def F22_star(t):
    ns = [[3, 5, 8, 12], [4, 6, 8, 10], [6, 7, 8, 9]][t]
    return [lambda ax, n=n: star(ax, n) for n in ns]


def F23_ellipse_ang(t):
    ar = [3.0, 2.0, 1.4][t]
    return [lambda ax, a=a: ellipse(ax, 1.6, 1.6 / ar, ang=a)
            for a in (0, 45, 90, 135)]


def F24_subdiv(t):
    ks = [[1, 2, 4, 8], [2, 3, 4, 6], [3, 4, 5, 6]][t]
    return [lambda ax, k=k: subdiv(ax, k) for k in ks]


def F25_nested(t):
    ks = [[1, 2, 4, 7], [2, 3, 4, 5], [3, 4, 5, 6]][t]
    return [lambda ax, k=k: nested(ax, k) for k in ks]


def F26_bumploc(t):
    amp = [0.55, 0.36, 0.20][t]
    return [lambda ax, c=c, a=amp: notched(ax, -a, ang=c)
            for c in (0, 90, 180, 270)]


def F27_linecount(t):
    ks = [[1, 2, 4, 7], [2, 3, 4, 5], [3, 4, 5, 6]][t]
    return [lambda ax, k=k: lines(ax, k) for k in ks]


def F28_dotarrange(t):
    sc = [1.0, 0.72, 0.5][t]
    def f(ax, pts):
        _ax(ax)
        for x, y in pts:
            ax.add_patch(Circle((x * sc, y * sc), 0.15, facecolor=EDGE,
                                edgecolor="none"))
    A = [(-.6, 0), (-.2, 0), (.2, 0), (.6, 0)]
    B = [(-.45, -.45), (.45, -.45), (-.45, .45), (.45, .45)]
    C = [(0, -.6), (-.6, 0), (.6, 0), (0, .6)]
    D = [(-.5, -.5), (-.5, .1), (-.5, .6), (.4, -.5)]
    return [lambda ax, p=p: f(ax, p) for p in (A, B, C, D)]


def F29_arcdir(t):
    sp = [1.0, 0.62, 0.35][t]
    def f(ax, rot):
        _ax(ax)
        ax.add_patch(Arc((0, 0), 1.7, 1.7 * sp, angle=rot, theta1=200, theta2=340,
                         edgecolor=EDGE, linewidth=4))
    return [lambda ax, r=r: f(ax, r) for r in (0, 90, 180, 270)]


def F30_pairratio(t):
    rs = [[1.0, 1.6, 2.4, 3.6], [1.0, 1.4, 1.9, 2.5], [1.0, 1.2, 1.45, 1.7]][t]
    def f(ax, r):
        _ax(ax)
        ax.add_patch(Circle((-0.42, 0), 0.34, facecolor=FILL, edgecolor=EDGE, lw=2.2))
        ax.add_patch(Circle((0.46, 0), 0.34 * r / 2.2, facecolor=FILL,
                            edgecolor=EDGE, lw=2.2))
    return [lambda ax, r=r: f(ax, r) for r in rs]


def F31_overlap(t):
    ss = [[0.15, 0.55, 0.95, 1.35], [0.35, 0.62, 0.89, 1.16],
          [0.55, 0.72, 0.89, 1.06]][t]
    return [lambda ax, s=s: two_circles(ax, s) for s in ss]


def F32_tilt(t):
    step = [15, 9, 5][t]
    return [lambda ax, a=i * step: ngon(ax, 4, rot=np.deg2rad(a), scale=0.86)
            for i in range(4)]


def F33_hole(t):
    hs = [[0.10, 0.35, 0.55, 0.75], [0.25, 0.40, 0.55, 0.70],
          [0.38, 0.47, 0.56, 0.65]][t]
    return [lambda ax, h=h: annulus(ax, h) for h in hs]


def F34_jitter(t):
    js = [[0.02, 0.14, 0.28, 0.44], [0.08, 0.17, 0.26, 0.35],
          [0.16, 0.22, 0.28, 0.34]][t]
    return [lambda ax, j=j, s=SEED + 2000 + t * 4 + i: jitter_poly(ax, j, s)
            for i, j in enumerate(js)]


def F35_gradang(t):
    return [lambda ax, a=a: gradient(ax, a) for a in (0, 90, 180, 270)]


def F36_split(t):
    fs = [[0.12, 0.38, 0.62, 0.88], [0.28, 0.42, 0.58, 0.72],
          [0.40, 0.47, 0.54, 0.61]][t]
    return [lambda ax, f=f: split_bar(ax, f) for f in fs]


def F37_mirroraxis(t):
    sd = SEED + 2100 + t
    def f(ax, k):
        rng = np.random.default_rng(sd)
        a = np.linspace(0, 2 * np.pi, 160, endpoint=False)
        r = 0.9 * (1 + 0.22 * np.sin(3 * a + rng.uniform(0, 6)))
        xy = np.c_[r * np.cos(a), r * np.sin(a)]
        th = np.deg2rad(k)
        M = np.array([[np.cos(2 * th), np.sin(2 * th)],
                      [np.sin(2 * th), -np.cos(2 * th)]])
        _ax(ax).add_patch(Polygon(xy @ M.T, facecolor=FILL, edgecolor=EDGE, lw=2.4))
    return [lambda ax, k=k: f(ax, k) for k in (0, 45, 90, 135)]


def F38_endcap(t):
    ks = [["butt", "round", "proj", "dot"], ["round", "proj", "dot", "butt"],
          ["proj", "dot", "butt", "round"]][t]
    return [lambda ax, k=k: cap_line(ax, k) for k in ks]


def F39_spacing(t):
    sp = [[0.16, 0.30, 0.44, 0.58], [0.24, 0.33, 0.42, 0.51],
          [0.32, 0.37, 0.42, 0.47]][t]
    def f(ax, s):
        _ax(ax)
        for i in range(5):
            ax.add_patch(Circle(((i - 2) * s, 0), 0.11, facecolor=EDGE,
                                edgecolor="none"))
    return [lambda ax, s=s: f(ax, s) for s in sp]


def F40_crossang(t):
    st = [[20, 45, 70, 90], [35, 50, 65, 80], [45, 53, 61, 69]][t]
    return [lambda ax, a=a: crossing(ax, a) for a in st]


def F41_contain(t):
    d = [0.5, 0.32, 0.16][t]
    return [lambda ax, p=p: contained(ax, (p[0] * d, p[1] * d))
            for p in ((-1, -1), (1, -1), (-1, 1), (1, 1))]


FAMILIES = {
    "F17_gapclock": F17_gapclock, "F18_stroke": F18_stroke, "F19_fill": F19_fill,
    "F20_corner": F20_corner, "F21_notch": F21_notch, "F22_star": F22_star,
    "F23_ellipseang": F23_ellipse_ang, "F24_subdiv": F24_subdiv,
    "F25_nested": F25_nested, "F26_bumploc": F26_bumploc,
    "F27_linecount": F27_linecount, "F28_dotarrange": F28_dotarrange,
    "F29_arcdir": F29_arcdir, "F30_pairratio": F30_pairratio,
    "F31_overlap": F31_overlap, "F32_tilt": F32_tilt, "F33_hole": F33_hole,
    "F34_jitter": F34_jitter, "F35_gradang": F35_gradang, "F36_split": F36_split,
    "F37_mirroraxis": F37_mirroraxis, "F38_endcap": F38_endcap,
    "F39_spacing": F39_spacing, "F40_crossang": F40_crossang,
    "F41_contain": F41_contain,
}
MEMBERS = 3

# Families deliberately built from near-equivalent options (transformations of one
# form, or a parameter varied too finely to rank). Recorded, not used as a filter.
NEAR_EQUIVALENT = {"F17_gapclock", "F23_ellipseang", "F26_bumploc", "F28_dotarrange",
                   "F29_arcdir", "F32_tilt", "F35_gradang", "F37_mirroraxis",
                   "F38_endcap", "F41_contain", "F19_fill", "F34_jitter"}


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
        manifest[str(pi)] = list(perm)
    json.dump(manifest, open(os.path.join(d, "manifest.json"), "w"), indent=1)


def main():
    os.makedirs(OUT, exist_ok=True)
    mp = os.path.join(OUT, "battery_manifest.csv")
    rows = list(csv.DictReader(open(mp))) if os.path.exists(mp) else []
    have = {r["stimulus_id"] for r in rows}
    new = []
    for fam, fn in FAMILIES.items():
        for t in range(MEMBERS):
            sid = f"{fam}_m{t}"
            if sid in have:
                continue
            render(sid, fn(t))
            new.append(dict(stimulus_id=sid, family=fam, member=t, n_options=4,
                            n_perms=24, dir=os.path.join(OUT, sid)))
            print(f"  {sid}")
    allrows = rows + new
    for r in allrows:
        r.setdefault("batch", "")
    for r in new:
        r["batch"] = "2"
    for r in allrows:
        if not r["batch"]:
            r["batch"] = "1"
    with open(mp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(allrows[0].keys()))
        w.writeheader(); w.writerows(allrows)
    print(f"\n{len(new)} new stimuli ({len(FAMILIES)} families x {MEMBERS}); "
          f"battery now {len(allrows)} total")

    fig, axes = plt.subplots(len(FAMILIES), 1, figsize=(12, 2.0 * len(FAMILIES)),
                             dpi=68)
    for ax, fam in zip(axes, FAMILIES):
        ax.imshow(plt.imread(os.path.join(OUT, f"{fam}_m0", "perm00.png")))
        ax.axis("off")
        tag = " [near-equivalent]" if fam in NEAR_EQUIVALENT else ""
        ax.set_title(f"{fam} (m0 of {MEMBERS}){tag}", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "gallery_batch2.png"), facecolor="white")
    plt.close(fig)
    print("gallery -> gallery_batch2.png")


if __name__ == "__main__":
    main()
