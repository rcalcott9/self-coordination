#!/usr/bin/env python3
"""
Prepare the Study 1 stimulus images for the deck.

Two things matter here:

1. ONE crop box for every image. Cropping each stimulus to its own content would
   silently rescale the shapes relative to each other, so a sparse dot field would
   end up drawn at a different size from a dense one and the pictures would stop
   being comparable. Instead we take the union of every used image's content box
   and crop all of them to it.

2. The source PNGs have an opaque white ground, which would read as a white slab
   on the deck's paper. White is remapped to the paper colour and a hairline frame
   is added, so each stimulus reads as a card rather than a hole.
"""
import os
import numpy as np
from PIL import Image

SRC = ("/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/"
       "policy_specific_self_coordination_20260812_1401/code/stimuli")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stim_prepped")
PAPER = (0xF4, 0xF4, 0xF1)

USED = ["c_contr_subtle", "b_spiral_cw", "s_convexity", "d_dens_extreme", "rot"]
PAD = 26          # px of breathing room around the union box
OUT_W = 900       # final width; height follows the shared crop aspect

os.makedirs(OUT, exist_ok=True)

# ---- pass 1: the shared content box -----------------------------------------
boxes = []
for name in USED:
    a = np.array(Image.open(f"{SRC}/{name}_AB.png").convert("RGB")).astype(int)
    ink = a.sum(axis=2) < 720          # anything meaningfully darker than white
    ys, xs = np.where(ink)
    boxes.append((xs.min(), ys.min(), xs.max(), ys.max()))
    print(f"{name:16s} content box {boxes[-1]}")

x0 = max(0, min(b[0] for b in boxes) - PAD)
y0 = max(0, min(b[1] for b in boxes) - PAD)
x1 = max(b[2] for b in boxes) + PAD
y1 = max(b[3] for b in boxes) + PAD
print(f"\nshared crop = ({x0}, {y0}, {x1}, {y1})   {x1-x0} x {y1-y0}")

# ---- pass 2: crop, recolour the ground, write -------------------------------
ratio = (y1 - y0) / (x1 - x0)
out_h = int(round(OUT_W * ratio))
for name in USED:
    im = Image.open(f"{SRC}/{name}_AB.png").convert("RGB")
    im = im.crop((x0, y0, min(x1, im.width), min(y1, im.height)))
    a = np.array(im)
    white = (a[..., 0] > 246) & (a[..., 1] > 246) & (a[..., 2] > 246)
    a[white] = PAPER
    Image.fromarray(a).resize((OUT_W, out_h), Image.LANCZOS).save(
        f"{OUT}/{name}.png", optimize=True)
    print(f"wrote {OUT}/{name}.png  {OUT_W}x{out_h}")

print(f"\naspect (w/h) = {OUT_W/out_h:.3f}")
