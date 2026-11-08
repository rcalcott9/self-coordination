"""Complete contact sheet for the 120-stimulus Study 1 battery (AB order).

The sheet already in stimuli/v3 covers only the 75 v3_new stimuli. This one covers
all 120, grouped by provenance, because the battery is assembled from three sources.
"""
import csv, os, collections
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = list(csv.DictReader(open(os.path.join(HERE, "stimulus_manifest.csv"))))
ORDER = [("study1_original", "Original Study 1 battery"),
         ("expansion_frozen", "Frozen expansion"),
         ("v3_new", "v3 battery, built for this design")]
COLS, TH, PAD, LAB, HDR = 10, 96, 9, 13, 30      # thumb height, padding, label, header
TW = int(TH * 1040 / 520)

def font(sz, bold=False):
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
              "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()

f_lab, f_hdr, f_ttl = font(9), font(12, True), font(17, True)
groups = [(t, sorted([r for r in M if r["source"] == s],
                     key=lambda r: (r["family"], r["stimulus_id"]))) for s, t in ORDER]
rows_per = [ -(-len(g) // COLS) for _, g in groups ]
W = COLS * (TW + PAD) + PAD
H = 46 + sum(HDR + n * (TH + LAB + PAD) + PAD for n in rows_per)
sheet = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(sheet)
d.text((PAD, 12), f"Study 1 stimulus battery — {len(M)} stimuli, AB order shown",
       fill="black", font=f_ttl)
y = 46
for (title, g), nrow in zip(groups, rows_per):
    fams = len({r["family"] for r in g})
    d.text((PAD, y + 8), f"{title}  ·  {len(g)} stimuli, {fams} families",
           fill="#1D2027", font=f_hdr)
    d.line([(PAD, y + HDR - 4), (W - PAD, y + HDR - 4)], fill="#C9CDD4", width=1)
    y += HDR
    for i, r in enumerate(g):
        cx = PAD + (i % COLS) * (TW + PAD)
        cy = y + (i // COLS) * (TH + LAB + PAD)
        im = Image.open(r["local_AB"]).convert("RGB").resize((TW, TH), Image.LANCZOS)
        sheet.paste(im, (cx, cy))
        d.rectangle([cx, cy, cx + TW - 1, cy + TH - 1], outline="#C9CDD4")
        name = r["stimulus_id"]
        while d.textlength(name, font=f_lab) > TW and len(name) > 4:
            name = name[:-1]
        d.text((cx, cy + TH + 2), name, fill="#3B414C", font=f_lab)
    y += nrow * (TH + LAB + PAD) + PAD
out = os.path.expanduser("~/Downloads/self-coordination-figures/study1_stimulus_battery_120.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
sheet.save(out, dpi=(300, 300))
sheet.save(os.path.join(HERE, "stimuli", "contact_sheet_120.png"), dpi=(300, 300))
print(f"wrote {out}  ({sheet.size[0]}x{sheet.size[1]})")
for t, g in groups:
    print(f"   {t:36} {len(g):3d} stimuli")
