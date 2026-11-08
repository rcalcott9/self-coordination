"""
Generate 4-ALTERNATIVE coordination stimuli (chance = 25%).

Two sets:
  proto4  circle / square / triangle / pentagon  -> predict focal point (circle)
  noise4  four independent random grayscale textures -> predict no focal point

Each set has 4 fixed "items". We render all 24 position-permutations of the row
so a probe can draw a random arrangement per player (position can't be used to
coordinate). A manifest maps perm_index -> [item_at_pos1..4]; the probe reads a
model's CHOICE: <1-4> and maps it back to the item via this manifest.
"""
import os, json, itertools
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, RegularPolygon

BASE = os.path.dirname(os.path.abspath(__file__))
FILL, EDGE = "#9AA3B2", "#3A4152"   # neutral slate, no hue salience

def draw_shape(ax, kind):
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal"); ax.axis("off")
    kw = dict(facecolor=FILL, edgecolor=EDGE, linewidth=3)
    if kind == "circle":   ax.add_patch(Circle((0, 0), 0.82, **kw))
    elif kind == "square": ax.add_patch(Rectangle((-0.72, -0.72), 1.44, 1.44, **kw))
    elif kind == "triangle": ax.add_patch(RegularPolygon((0, 0), 3, radius=0.95, orientation=0, **kw))
    elif kind == "pentagon": ax.add_patch(RegularPolygon((0, 0), 5, radius=0.9, orientation=0, **kw))

def draw_noise(ax, seed):
    rng = np.random.default_rng(seed)
    ax.imshow(rng.random((24, 24)), cmap="gray", vmin=0, vmax=1, interpolation="nearest")
    ax.axis("off")

SETS = {
    "proto4": dict(kind="shape", items=["circle", "square", "triangle", "pentagon"]),
    "noise4": dict(kind="noise", items=[101, 202, 303, 404]),  # fixed seeds = fixed textures
}

def render(setname, spec):
    out = os.path.join(BASE, "stimuli", setname); os.makedirs(out, exist_ok=True)
    items = spec["items"]; manifest = {}
    for pi, perm in enumerate(itertools.permutations(range(4))):
        fig, axes = plt.subplots(1, 4, figsize=(12, 3.4), dpi=120)
        for pos, ax in enumerate(axes):
            item = items[perm[pos]]
            if spec["kind"] == "shape": draw_shape(ax, item)
            else: draw_noise(ax, item)
            ax.set_title(str(pos + 1), fontsize=20, color="#222", pad=8)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.02, wspace=0.18)
        fig.savefig(os.path.join(out, f"perm{pi:02d}.png"), facecolor="white"); plt.close(fig)
        manifest[pi] = [str(items[perm[pos]]) for pos in range(4)]  # item at position 1..4
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print(f"{setname}: wrote 24 perms + manifest  (items={items})")

for name, spec in SETS.items():
    render(name, spec)

# a small gallery (perm00 of each) to eyeball
fig, axes = plt.subplots(2, 1, figsize=(12, 7), dpi=110)
for ax, name in zip(axes, SETS):
    ax.imshow(plt.imread(os.path.join(BASE, "stimuli", name, "perm00.png"))); ax.axis("off")
    ax.set_title(f"{name}  (positions 1-4; randomized per player)", fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(BASE, "stimuli", "gallery_4opt.png"), facecolor="white"); plt.close(fig)
print("gallery -> stimuli/gallery_4opt.png")
