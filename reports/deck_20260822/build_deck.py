#!/usr/bin/env python3
"""
Build the self-coordination summary deck as a .pptx.

Every chart is drawn from NATIVE PowerPoint shapes (ovals, connectors, rectangles,
text boxes) rather than an embedded image, so each mark stays selectable and
editable after the file is opened in PowerPoint or imported into Google Slides.

Numbers come from the project's own CSVs, not from the PDF's rendered figures:
  policy_specific_self_coordination_20260812_1401/data/attempt_rates.csv
  policy_specific_self_coordination_20260812_1401/data/matched_pair_results.csv
  study2_partner_policy_20260822/pairs/cross_model_table.csv
  generation_ladder_20260814/figures/coordination_sensitivity_ladder.csv

Figure style follows the house academic rules: Arial throughout the plots, series
distinguished by filled/open markers and solid/dashed lines (not by hue) so the
slides survive greyscale, thin black axes, ticks outward, no background gridlines.
"""

import os

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.dml import MSO_LINE_DASH_STYLE as DASH

# ----------------------------------------------------------------- palette ---
PAPER = RGBColor(0xF4, 0xF4, 0xF1)   # chosen neutral: faint green-grey, not cream
INK   = RGBColor(0x1A, 0x1A, 0x18)
INK2  = RGBColor(0x56, 0x56, 0x4E)
INK3  = RGBColor(0x8C, 0x8C, 0x82)
RULE  = RGBColor(0xD9, 0xD9, 0xD1)
ACC   = RGBColor(0xA0, 0x3A, 0x2B)   # madder — the single accent

DISPLAY = "Georgia"   # available on Windows, macOS and Google Slides
BODY    = "Arial"

W, H = 13.333, 7.5
L, R = 0.9, 12.433          # content margins
CW   = R - L

prs = Presentation()
prs.slide_width  = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]


# ------------------------------------------------------------- primitives ---
def new_slide():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = PAPER
    return s


def set_spc(run, pts):
    """Letter-spacing, which python-pptx does not expose directly."""
    run.font._rPr.set("spc", str(int(pts * 100)))


def txt(slide, x, y, w, h, text, size=11, font=BODY, color=INK, bold=False,
        italic=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
        line_spacing=1.25, space_after=0, spc=None):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paras = text.split("\n")
    for i, ptext in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = ptext
        r.font.size = Pt(size)
        r.font.name = font
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
        if spc:
            set_spc(r, spc)
    return box


def rich(slide, x, y, w, h, chunks, size=11, font=BODY, color=INK,
         line_spacing=1.35, align=PP_ALIGN.LEFT):
    """chunks = list of (text, bold, color_or_None) inside one paragraph."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    for text, bold, col in chunks:
        r = p.add_run()
        r.text = text
        r.font.size = Pt(size)
        r.font.name = font
        r.font.bold = bold
        r.font.color.rgb = col or color
    return box


def line(slide, x1, y1, x2, y2, color=INK, width=0.75, dash=None):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                   Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(width)
    if dash:
        c.line.dash_style = dash
    return c


def dot(slide, cx, cy, r=0.055, kind="fill"):
    """kind: fill | open | acc | both  (both = filled dot inside an open ring)."""
    if kind == "both":
        ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r * 1.75),
                                      Inches(cy - r * 1.75), Inches(r * 3.5), Inches(r * 3.5))
        ring.fill.background()
        ring.line.color.rgb = INK
        ring.line.width = Pt(0.9)
        ring.shadow.inherit = False
        inner = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r * 0.72),
                                       Inches(cy - r * 0.72), Inches(r * 1.44), Inches(r * 1.44))
        inner.fill.solid(); inner.fill.fore_color.rgb = INK
        inner.line.fill.background()
        inner.shadow.inherit = False
        return ring
    sh = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r), Inches(cy - r),
                                Inches(2 * r), Inches(2 * r))
    sh.shadow.inherit = False
    if kind == "fill":
        sh.fill.solid(); sh.fill.fore_color.rgb = INK
        sh.line.color.rgb = PAPER; sh.line.width = Pt(1.0)
    elif kind == "open":
        sh.fill.solid(); sh.fill.fore_color.rgb = PAPER
        sh.line.color.rgb = INK; sh.line.width = Pt(1.1)
    elif kind == "acc":
        sh.fill.solid(); sh.fill.fore_color.rgb = ACC
        sh.line.color.rgb = PAPER; sh.line.width = Pt(1.0)
    return sh


def box(slide, x, y, w, h, fill=None, outline=INK, width=0.75):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                Inches(w), Inches(h))
    sh.shadow.inherit = False
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if outline is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = outline; sh.line.width = Pt(width)
    return sh


# --------------------------------------------------------- slide furniture ---
def eyebrow(slide, num, label):
    txt(slide, L, 0.46, 0.4, 0.22, num, size=8.5, color=ACC, bold=True, spc=1.4)
    line(slide, L + 0.36, 0.565, L + 0.66, 0.565, RULE, 0.75)
    txt(slide, L + 0.76, 0.46, 6.0, 0.22, label.upper(), size=8.5, color=INK3, spc=1.4)


def heading(slide, text, y=0.82, size=27, w=10.6):
    return txt(slide, L, y, w, 1.0, text, size=size, font=DISPLAY, color=INK,
               line_spacing=1.12)


def readout(slide, x, y, w, chunks, size=11.5):
    box(slide, x, y, 0.028, 0.62, fill=ACC, outline=None)
    return rich(slide, x + 0.20, y + 0.02, w - 0.20, 0.6, chunks,
                size=size, line_spacing=1.35)


def caption(slide, y, text, w=None, x=None):
    return txt(slide, x if x is not None else L, y, w or CW, 0.8, text,
               size=7.8, color=INK3, line_spacing=1.4)


def legend(slide, x, y, items):
    """items = list of (kind, label). kind: fill|open|acc|both|solid|dash|accbar|barfill|baropen"""
    cx = x
    for kind, label in items:
        cy = y + 0.075
        if kind in ("fill", "open", "acc", "both"):
            dot(slide, cx + 0.06, cy, 0.05, kind)
            tx = cx + 0.19
        elif kind == "solid":
            line(slide, cx, cy, cx + 0.26, cy, INK, 1.5)
            dot(slide, cx + 0.13, cy, 0.05, "fill")
            tx = cx + 0.36
        elif kind == "dash":
            line(slide, cx, cy, cx + 0.26, cy, INK, 1.3, DASH.DASH)
            dot(slide, cx + 0.13, cy, 0.05, "open")
            tx = cx + 0.36
        elif kind == "accbar":
            box(slide, cx + 0.03, cy - 0.075, 0.032, 0.15, fill=ACC, outline=None)
            tx = cx + 0.16
        elif kind == "barfill":
            box(slide, cx, cy - 0.06, 0.13, 0.12, fill=INK, outline=None)
            tx = cx + 0.22
        elif kind == "baropen":
            box(slide, cx, cy - 0.06, 0.13, 0.12, fill=PAPER, outline=INK, width=1.1)
            tx = cx + 0.22
        elif kind == "nodata":
            line(slide, cx, cy, cx + 0.16, cy, RULE, 1.5)
            tx = cx + 0.26
        t = txt(slide, tx, y, 3.0, 0.16, label, size=8.5, color=INK2)
        cx = tx + 0.062 * len(label) + 0.42
    return cx


# ============================================================ SLIDE 1 ========
s = new_slide()
line(s, L, 1.52, L + 0.72, 1.52, INK, 1.0)
line(s, L, 1.60, L + 0.72, 1.60, ACC, 1.4)
txt(s, L, 1.86, 10.5, 1.9, "Do models know\ntheir own conventions?",
    size=44, font=DISPLAY, color=INK, line_spacing=1.08)
txt(s, L, 3.86, 7.5, 1.0,
    "Two copies of one model look at the same picture and must pick the same thing, "
    "with no way to talk. What the model believes about its own policy — and whether "
    "it acts on that belief — is the whole experiment.",
    size=13, font=DISPLAY, color=INK2, line_spacing=1.45)

line(s, L, 5.28, R, 5.28, RULE, 0.75)
meta = [("MODELS", "GPT-5.5 · Claude Opus 5\nplus 7 earlier generations"),
        ("PARADIGM", "One-shot visual coordination,\nself-play, no communication"),
        ("EVIDENCE", "~12,000 independent API calls\nacross five experiments"),
        ("STATUS", "Pilots + Study 1 complete\nStudy 2 in design")]
for i, (k, v) in enumerate(meta):
    x = L + i * (CW / 4)
    txt(s, x, 5.50, 2.6, 0.2, k, size=8, color=INK3, spc=1.4)
    txt(s, x, 5.76, 2.7, 0.8, v, size=10.5, color=INK, line_spacing=1.35)

txt(s, L, 6.85, 8.0, 0.2, "Rachel Calcott  ·  self-coordination  ·  2026-08-22",
    size=8.5, color=INK3, spc=0.6)


# ============================================================ SLIDE 2 ========
s = new_slide()
eyebrow(s, "01", "Background")
heading(s, "Coordination without communication\nis a self-knowledge problem.")
txt(s, L, 2.55, 5.1, 2.4,
    "When two agents must match and cannot talk, each one has to predict what the "
    "other will do. If the other agent is a copy of you, that prediction is a "
    "question about yourself: what does my own policy do when it looks at this?",
    size=11.5, color=INK2, line_spacing=1.5)
txt(s, L, 3.90, 5.1, 1.6,
    "That gives a sharp, testable set of questions — and they come apart. A model "
    "can be reliable without knowing it is, and confident without being right.",
    size=11.5, color=INK2, line_spacing=1.5)

qs = [("Q1", "Does it know which conventions its own policy implements?",
       "Not “is it accurate in general” — does it know the specific picture on "
       "which its copies will actually agree?"),
      ("Q2", "Does that knowledge change what it does?",
       "Knowledge that never reaches behaviour is not doing any work."),
      ("Q3", "Can it say so?",
       "If the knowledge steers the choice, does it also appear in the model’s "
       "stated reasons?")]
y = 2.55
for tag, head, sub in qs:
    txt(s, 6.7, y + 0.02, 0.45, 0.2, tag, size=9, color=ACC, bold=True, spc=0.8)
    txt(s, 7.25, y, 5.15, 0.4, head, size=11.5, color=INK, bold=True, line_spacing=1.3)
    txt(s, 7.25, y + 0.42, 5.15, 0.7, sub, size=10.5, color=INK2, line_spacing=1.4)
    y += 1.32
line(s, 6.7, 6.72, R, 6.72, RULE, 0.75)


# ============================================================ SLIDE 3 ========
s = new_slide()
eyebrow(s, "02", "The task")
heading(s, "One picture, two copies, one shot.")

# --- diagram, native shapes
dx = 0.55
box(s, dx + 1.55, 2.10, 1.55, 0.62, fill=None, outline=INK)
dot(s, dx + 1.95, 2.41, 0.155, "open")
box(s, dx + 2.55, 2.26, 0.30, 0.30, fill=INK, outline=None)
txt(s, dx + 3.24, 2.24, 1.3, 0.4, "one image,\ntwo forms", size=8.5, color=INK3,
    line_spacing=1.3)

line(s, dx + 2.33, 2.72, dx + 2.33, 3.02, RULE)
line(s, dx + 0.78, 3.02, dx + 3.88, 3.02, RULE)
line(s, dx + 0.78, 3.02, dx + 0.78, 3.24, RULE)
line(s, dx + 3.88, 3.02, dx + 3.88, 3.24, RULE)

for cx, name in ((dx + 0.78, "Copy A"), (dx + 3.88, "Copy B")):
    box(s, cx - 0.78, 3.24, 1.56, 0.60, fill=None, outline=INK)
    txt(s, cx - 0.78, 3.38, 1.56, 0.2, name, size=11, color=INK, bold=True,
        align=PP_ALIGN.CENTER)
    txt(s, cx - 0.78, 3.58, 1.56, 0.2, "no history, no channel", size=8, color=INK3,
        align=PP_ALIGN.CENTER)

line(s, dx + 0.78, 3.84, dx + 0.78, 4.12, RULE)
line(s, dx + 3.88, 3.84, dx + 3.88, 4.12, RULE)
line(s, dx + 0.78, 4.12, dx + 3.88, 4.12, RULE)
line(s, dx + 1.55, 4.12, dx + 1.55, 4.36, RULE)
line(s, dx + 3.11, 4.12, dx + 3.11, 4.36, RULE)

for cx, big, small in ((dx + 1.55, "match → 10", "same form"),
                       (dx + 3.11, "miss → 0", "different forms")):
    box(s, cx - 0.74, 4.36, 1.48, 0.58, fill=None, outline=INK)
    txt(s, cx - 0.74, 4.48, 1.48, 0.2, big, size=10.5, color=INK, bold=True,
        align=PP_ALIGN.CENTER)
    txt(s, cx - 0.74, 4.68, 1.48, 0.2, small, size=8, color=INK3, align=PP_ALIGN.CENTER)

line(s, dx + 0.81, 5.14, dx + 3.85, 5.14, RULE)
txt(s, dx + 0.55, 5.26, 3.6, 0.2, "…or take a guaranteed 3, 5, 7 or 9",
    size=10, color=ACC, bold=True, align=PP_ALIGN.CENTER)

txt(s, 6.7, 2.20, 5.7, 1.2,
    "Each trial is a fresh, independent call. No conversation history, no messages "
    "between the copies, and the left/right position of the two forms is randomised "
    "per player — so agreeing on “the one on the left” does not work.",
    size=11.5, color=INK2, line_spacing=1.5)
txt(s, 6.7, 3.55, 5.7, 1.3,
    "The safe payoff is the instrument that matters. Offering a guaranteed "
    "alternative forces the model to price its own reliability: attempting only "
    "beats taking 9 points if it believes its copy will match more than 90% of the time.",
    size=11.5, color=INK2, line_spacing=1.5)
caption(s, 5.05,
        "15 visual stimuli spanning shared focal points, ambiguous pictures, and "
        "pictures where the two labs’ models diverge.\n60 trials per model per "
        "stimulus for ground truth.", w=5.7, x=6.7)


# ============================================================ SLIDE 4 ========
s = new_slide()
eyebrow(s, "03", "Pilot · what drives coordination")
heading(s, "What you’re looking at matters.\nWho you think you’re playing barely does.")

X0, X1 = 2.35, 10.55
Y_TOP, Y_BOT = 2.28, 4.86          # 1.0 -> 0.4
fy = lambda v: Y_BOT - (v - 0.4) / 0.6 * (Y_BOT - Y_TOP)

line(s, X0, Y_TOP, X0, Y_BOT, INK, 0.9)
line(s, X0, Y_BOT, X1, Y_BOT, INK, 0.9)
for v in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
    line(s, X0 - 0.06, fy(v), X0, fy(v), INK, 0.9)
    txt(s, X0 - 0.62, fy(v) - 0.075, 0.5, 0.16, f"{v:.1f}", size=8.5, color=INK2,
        align=PP_ALIGN.RIGHT)
txt(s, 0.30, 2.90, 1.6, 1.4, "match rate\nbetween\ntwo copies", size=8.5, color=INK2,
    align=PP_ALIGN.RIGHT, line_spacing=1.35)
line(s, X0, fy(0.5), X1, fy(0.5), RULE, 0.9, DASH.DASH)
txt(s, X1 - 1.5, fy(0.5) + 0.06, 1.5, 0.16, "chance = 0.50", size=8, color=INK3,
    align=PP_ALIGN.RIGHT)

frames = [("“copies of you”", 1.000, 0.557),
          ("“same distribution”", 1.000, 0.563),
          ("“a different AI”", 0.920, 0.517),
          ("unknown partner", 1.000, 0.511)]
xs = [3.20, 5.20, 7.20, 9.20]
for (label, hi, lo), x in zip(frames, xs):
    line(s, x, fy(hi), x, fy(lo), RULE, 0.75)
    dot(s, x, fy(hi), 0.058, "fill")
    dot(s, x, fy(lo), 0.058, "open")
    txt(s, x - 0.6, fy(hi) - 0.24, 1.2, 0.16, f"{hi:.2f}", size=9, color=INK,
        bold=True, align=PP_ALIGN.CENTER)
    txt(s, x - 0.6, fy(lo) - 0.24, 1.2, 0.16, f"{lo:.2f}", size=9, color=INK,
        bold=True, align=PP_ALIGN.CENTER)
    txt(s, x - 1.0, Y_BOT + 0.10, 2.0, 0.18, label, size=9, color=INK2,
        align=PP_ALIGN.CENTER)
txt(s, X0, Y_BOT + 0.34, X1 - X0, 0.18,
    "what the model was told about its partner", size=8, color=INK3,
    align=PP_ALIGN.CENTER)

# the 0.44 gap
gx = 10.05
line(s, gx, fy(1.0), gx, fy(0.557), ACC, 1.1)
line(s, gx - 0.06, fy(1.0), gx + 0.06, fy(1.0), ACC, 1.1)
line(s, gx - 0.06, fy(0.557), gx + 0.06, fy(0.557), ACC, 1.1)
txt(s, gx + 0.12, (fy(1.0) + fy(0.557)) / 2 - 0.18, 0.9, 0.4, "gap\n0.44", size=9.5,
    color=ACC, bold=True, line_spacing=1.2)

legend(s, L, 5.40, [("fill", "Picture with an obvious answer"),
                    ("open", "Ambiguous picture (mean of two matched sets)")])
readout(s, L, 5.78, 8.4,
        [("Swapping the picture moves coordination by ", False, INK),
         ("0.44", True, INK),
         (". Swapping the partner’s identity moves it by ", False, INK),
         ("0.05", True, INK),
         (" — and that much is not distinguishable from noise.", False, INK)])
caption(s, 6.62,
        "GPT-5.4, one-shot, position counterbalanced, no communication. Pooled across two runs, n = 48 per arm. "
        "“Copies of you” vs unknown partner on the matched sets: +0.046, 95% CI [−0.024, +0.124], p = 0.10 — "
        "positive in both runs and on both matched sets, but underpowered. Ambiguous = mean of the noise and mirror sets.")


# ============================================================ SLIDE 5 ========
# Same-model pairings collapsed: GPT-with-GPT and Claude-with-Claude are pooled
# into one "with a copy of itself" rate, contrasted against the single
# GPT-with-Claude rate. Rows ordered by the resulting gap.
s = new_slide()
eyebrow(s, "04", "Pilot · whose convention is it")
heading(s, "Some conventions only work\nwith a copy of yourself.")

PX0, PX1 = 4.35, 9.75
fx = lambda v: PX0 + v * (PX1 - PX0)
#        label                    stimulus                self   cross
rows = [("Shared convention",     "circle vs square",     1.000, 1.000),
        ("No convention at all",  "dense vs sparse",      0.493, 0.500),
        ("Nearly shared",         "spiral direction",     0.827, 0.783),
        ("Partly private",        "open vs closed",       0.764, 0.633),
        ("Mostly private",        "fine vs coarse texture", 0.673, 0.444),
        ("Opposite conventions",  "chevrons up vs down",  0.831, 0.167)]
Y0, STEP = 2.50, 0.400
AXY = Y0 + 5 * STEP + 0.34

# column headers
txt(s, 10.05, Y0 - 0.42, 1.5, 0.16, "SELF  ·  OTHER", size=7.5, color=INK3, spc=1.0)
txt(s, 11.55, Y0 - 0.42, 0.88, 0.16, "GAP", size=7.5, color=INK3, spc=1.0,
    align=PP_ALIGN.RIGHT)
line(s, 10.05, Y0 - 0.24, R, Y0 - 0.24, RULE, 0.7)

line(s, fx(0.5), Y0 - 0.26, fx(0.5), AXY, RULE, 0.9, DASH.DASH)
for i, (lab, sub, self_r, cross_r) in enumerate(rows):
    y = Y0 + i * STEP
    gap = self_r - cross_r
    line(s, PX0, y, PX1, y, RULE, 0.7)
    txt(s, 1.5, y - 0.15, 2.68, 0.18, lab, size=10, color=INK, bold=True,
        align=PP_ALIGN.RIGHT)
    txt(s, 1.5, y + 0.03, 2.68, 0.18, sub, size=8, color=INK3, align=PP_ALIGN.RIGHT)
    # the gap itself is the mark: an accent segment from cross to self
    if abs(gap) > 0.02:
        line(s, fx(cross_r), y, fx(self_r), y, ACC, 2.2)
    if abs(gap) < 0.02:
        dot(s, fx(self_r), y, 0.055, "both")
    else:
        dot(s, fx(cross_r), y, 0.058, "open")
        dot(s, fx(self_r), y, 0.058, "fill")
    txt(s, 10.05, y - 0.09, 1.5, 0.18, f"{self_r:.2f}  ·  {cross_r:.2f}",
        size=9.5, color=INK)
    big = gap >= 0.10
    txt(s, 11.55, y - 0.09, 0.88, 0.18,
        ("+" if gap >= 0 else "−") + f"{abs(gap):.2f}",
        size=9.5, color=ACC if big else INK3, bold=big, align=PP_ALIGN.RIGHT)

line(s, PX0, AXY, PX1, AXY, INK, 0.9)
for v in (0, 0.5, 1.0):
    line(s, fx(v), AXY, fx(v), AXY + 0.06, INK, 0.9)
    txt(s, fx(v) - 0.4, AXY + 0.10, 0.8, 0.16, f"{v:g}" if v != 0.5 else "0.5",
        size=8.5, color=INK2, align=PP_ALIGN.CENTER)
txt(s, PX0, AXY + 0.32, PX1 - PX0, 0.18,
    "probability the two players pick the same form", size=8, color=INK3,
    align=PP_ALIGN.CENTER)

legend(s, L, 5.42, [("fill", "Playing a copy of itself (both models pooled)"),
                    ("open", "Playing the other lab’s model"),
                    ("both", "both, same value")])
readout(s, L, 5.80, 10.6,
        [("On the chevrons, a model matches a copy of itself ", False, INK),
         ("83%", True, INK),
         (" of the time. Put the two models together and they match ", False, INK),
         ("17%", True, INK),
         (": GPT says “up”, Claude says “down”, almost every time.", False, INK)])
caption(s, 6.62,
        "GPT-5.5 and Claude Opus 5, n = 60 per model per stimulus; six of the fifteen stimuli, ordered by gap. "
        "SELF is the mean of the two models’ own-copy rates (bias-corrected); OTHER is the single cross-model rate "
        "(plug-in estimate from the two choice distributions).\nPooling hides one thing worth stating: on “open vs closed” "
        "and “fine vs coarse texture” the two models’ own-copy rates are far apart (1.00 vs 0.53 and 0.50 vs 0.85), "
        "so SELF there averages two very different models rather than describing either.")

# ========================================================= SLIDE 5b ==========
# The matched pairs as pictures. Every image is cropped to ONE shared box (see
# prep_stimuli.py) so shape sizes stay comparable across rows.
s = new_slide()
eyebrow(s, "05", "Study 1 · the stimuli")
heading(s, "Study 1’s matched pairs, as the model saw them.", size=26)

STIM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stim_prepped")
IW = 1.96
IH = IW / 2.211
CAN_X, CANT_X = 2.78, 5.30
NOTE_X, NOTE_W = 7.85, 3.55

# column headers
txt(s, CAN_X, 1.58, IW, 0.16, "RELIABLE", size=7.5, color=INK, spc=1.2,
    bold=True, align=PP_ALIGN.CENTER)
txt(s, CAN_X, 1.74, IW, 0.16, "its copies agree", size=7.5, color=INK3,
    align=PP_ALIGN.CENTER)
txt(s, CANT_X, 1.58, IW, 0.16, "UNRELIABLE", size=7.5, color=INK, spc=1.2,
    bold=True, align=PP_ALIGN.CENTER)
txt(s, CANT_X, 1.74, IW, 0.16, "agreement drops, often to chance", size=7.5,
    color=INK3, align=PP_ALIGN.CENTER)
txt(s, 11.55, 1.58, 0.88, 0.16, "Δ P(ATTEMPT)", size=7.5, color=INK3, spc=1.0,
    align=PP_ALIGN.RIGHT)
line(s, CAN_X, 1.94, R, 1.94, RULE, 0.75)

#      model      can-stim          can rate  can n     cant-stim         cant rate cant n   rule                                   failure                                            delta  xref
GRID = [
 ("GPT-5.5",      "c_contr_subtle", "1.00", "60/60",   "b_spiral_cw",    "0.65", "47/60",
  "Takes the darker of two greys — every trial.",
  "Spiral direction: a rule, but a soft one.", "+0.30", "same picture as row 3"),
 ("",             "s_convexity",    "0.97", "59/60",   "d_dens_extreme", "0.49", "31/60",
  "Takes the concave form over the convex one.",
  "Dot density: no form rule at all — it just takes a side.", "+0.18", None),
 ("Claude Opus 5","b_spiral_cw",    "1.00", "60/60",   "rot",            "0.49", "30/60",
  "Takes the counter-clockwise spiral — every trial.",
  "Rotated blob: no form rule — it just takes a side.", "+0.12", "same picture as row 1"),
 ("",             "s_convexity",    "1.00", "60/60",   "d_dens_extreme", "0.54", "39/60",
  "Takes the concave form over the convex one.",
  "Dot density: no form rule — it just takes a side.", "+0.08", None),
]

YS = [1.98, 3.12, 4.44, 5.58]
line(s, L, 4.26, R, 4.26, RULE, 0.75)

for (model, can_s, can_r, can_n, cant_s, cant_r, cant_n,
     rule_txt, fail_txt, delta, xref), y in zip(GRID, YS):
    if model:
        txt(s, L, y + 0.02, 1.72, 0.2, model, size=10.5, color=INK, bold=True,
            align=PP_ALIGN.RIGHT)
        txt(s, L, y + 0.24, 1.72, 0.2, "two matched pairs", size=8, color=INK3,
            align=PP_ALIGN.RIGHT)
    for px, stim, rate, n, accent in ((CAN_X, can_s, can_r, can_n, False),
                                      (CANT_X, cant_s, cant_r, cant_n, True)):
        s.shapes.add_picture(os.path.join(STIM, stim + ".png"),
                             Inches(px), Inches(y), Inches(IW), Inches(IH))
        box(s, px, y, IW, IH, fill=None, outline=RULE, width=0.75)
        rich(s, px, y + IH + 0.045, IW, 0.18,
             [("own-copy ", False, INK3), (rate, True, ACC if accent else INK),
              ("   " + n, False, INK3)], size=8.5, align=PP_ALIGN.CENTER)
    txt(s, NOTE_X, y + 0.08, NOTE_W, 0.34, rule_txt, size=9.5, color=INK,
        line_spacing=1.35)
    txt(s, NOTE_X, y + 0.46, NOTE_W, 0.34, fail_txt, size=9.5, color=INK2,
        line_spacing=1.35)
    if xref:
        txt(s, NOTE_X, y + 0.84, NOTE_W, 0.16, "↳ " + xref, size=8, color=ACC)
    txt(s, 11.55, y + 0.08, 0.88, 0.2, delta, size=11, color=ACC, bold=True,
        align=PP_ALIGN.RIGHT)

rich(s, L, 6.80, 11.0, 0.2,
     [("The spirals are the same picture in both rows: ", False, INK),
      ("GPT cannot rely on them, Claude coordinates on them perfectly.", True, INK)],
     size=10.5)
caption(s, 7.04,
        "Each panel is one stimulus: two forms shown side by side. Left/right position was randomised per player, so the arrangement here is one of two. "
        "All panels share a single crop box, so shape sizes are comparable across rows.\n"
        "Own-copy = probability two fresh copies of the model pick the same form (n = 60). "
        "n/60 = how often the model chose its own modal form — near 30/60 with no form rule means it is choosing a side, not a shape. Note that unreliable does not always mean chance: GPT’s spirals sit at 0.65, reduced rather than absent.")

# ============================================================ SLIDE 6 ========
s = new_slide()
eyebrow(s, "06", "Study 1 · the main result")
heading(s, "Models bet more on the pictures\ntheir own copies actually match on.")

FX0, FX1 = 3.05, 7.95           # -0.10 .. +0.45
ffx = lambda v: FX0 + (v + 0.10) / 0.55 * (FX1 - FX0)
pairs = [("gpt", "Pair 1", "1.00 vs 0.65 own-copy", 0.300, 0.19, 0.40, True),
         ("gpt", "Pair 2", "0.97 vs 0.49 own-copy", 0.183, 0.11, 0.27, True),
         ("gpt", "Pair 3", "1.00 vs 0.49 own-copy", 0.042, -0.06, 0.14, False),
         ("cl",  "Pair 4", "1.00 vs 0.49 own-copy", 0.117, 0.00, 0.23, True),
         ("cl",  "Pair 5", "1.00 vs 0.54 own-copy", 0.083, 0.03, 0.15, True)]
FY = 2.35
txt(s, L, FY - 0.28, 2.0, 0.18, "GPT-5.5", size=8.5, color=INK3, spc=0.8)
line(s, L, FY - 0.09, FX1 + 0.9, FY - 0.09, RULE, 0.7)
ys = []
y = FY + 0.10
for i, (grp, lab, sub, d, lo, hi, sig) in enumerate(pairs):
    if i == 3:
        y += 0.30
        txt(s, L, y - 0.28, 2.4, 0.18, "Claude Opus 5", size=8.5, color=INK3, spc=0.8)
        line(s, L, y - 0.09, FX1 + 0.9, y - 0.09, RULE, 0.7)
        y += 0.10
    ys.append(y)
    txt(s, 1.3, y - 0.155, 1.62, 0.18, lab, size=10, color=INK, bold=True,
        align=PP_ALIGN.RIGHT)
    txt(s, 0.75, y + 0.02, 2.17, 0.18, sub, size=7.6, color=INK3, align=PP_ALIGN.RIGHT)
    col = ACC if sig else INK
    line(s, ffx(lo), y, ffx(hi), y, col, 1.0)
    line(s, ffx(lo), y - 0.06, ffx(lo), y + 0.06, col, 1.0)
    line(s, ffx(hi), y - 0.06, ffx(hi), y + 0.06, col, 1.0)
    dot(s, ffx(d), y, 0.058, "acc" if sig else "open")
    txt(s, FX1 + 0.20, y - 0.09, 0.8, 0.18, f"+{d:.2f}", size=9.5,
        color=ACC if sig else INK, bold=True)
    y += 0.44

AY = ys[-1] + 0.40
line(s, ffx(0), FY - 0.05, ffx(0), AY, INK, 0.8)
line(s, FX0, AY, FX1, AY, INK, 0.9)
for v in (-0.1, 0, 0.2, 0.4):
    line(s, ffx(v), AY, ffx(v), AY + 0.06, INK, 0.9)
    lbl = "0" if v == 0 else (f"{v:+.1f}".replace("+0.", "+0.").replace("-0.", "−0."))
    txt(s, ffx(v) - 0.4, AY + 0.10, 0.8, 0.16, lbl, size=8.5, color=INK2,
        align=PP_ALIGN.CENTER)
txt(s, FX0, AY + 0.32, FX1 - FX0, 0.18,
    "Δ probability of attempting coordination", size=8, color=INK3,
    align=PP_ALIGN.CENTER)

txt(s, 8.95, 2.30, 3.48, 1.5,
    "Each pair is two pictures matched on how coordinable they look from outside "
    "— same generic salience, same prediction from an external model auditing "
    "them — but differing sharply in how often the model’s own copies actually agree.",
    size=10.5, color=INK2, line_spacing=1.45)
txt(s, 8.95, 3.85, 3.48, 1.1,
    "An outside observer has no basis to prefer one over the other. The model does, "
    "and it uses it: all five pairs lean toward the reliable member, four decisively.",
    size=10.5, color=INK2, line_spacing=1.45)
readout(s, 8.95, 4.92, 3.48,
        [("The gaps were selected on one half of the data and held up on the other in ",
          False, INK), ("8 of 8", True, INK), (" cases.", False, INK)], size=10.5)

legend(s, L, 5.80, [("acc", "p ≤ 0.001"),
                    ("open", "not significant (p = 0.139)")])
txt(s, 4.75, 5.80, 3.0, 0.18, "bars = 95% interval", size=8.5, color=INK2)
caption(s, 6.45,
        "Stage C: 30 trials per cell across safe payoffs {3, 5, 7, 9}; 1,200 trials. Δ pooled across payoffs. "
        "Pre-registered one-sided permutation test on raw counts.\nBayesian pair-constrained model agrees: "
        "μδ = +0.82, 90% CrI [+0.27, +1.40], P(μδ > 0) = 0.986.")


# ============================================================ SLIDE 7 ========
s = new_slide()
eyebrow(s, "07", "Study 1 · where the effect lives")
heading(s, "The knowledge only shows up\nonce playing gets expensive.")

PY_TOP, PY_BOT = 2.45, 4.95
fpy = lambda v: PY_BOT - v * (PY_BOT - PY_TOP)
panels = [(1.95, "GPT-5.5", [1.00, 1.00, 0.9667, 0.40], [1.00, 0.8667, 0.30, 0.00],
           [(9, "0.40", 0.14, -0.10)], [(9, "0.00", 0.14, -0.34)]),
          (7.35, "Claude Opus 5", [1.00, 1.00, 0.9333, 0.10], [1.00, 1.00, 0.5667, 0.00],
           [(7, "0.93", 0.14, -0.28), (9, "0.10", 0.14, -0.10)],
           [(7, "0.57", -0.84, -0.10)])]
for px0, name, high, low, hlabels, llabels in panels:
    px1 = px0 + 3.55
    xs = [px0 + i * (px1 - px0) / 3 for i in range(4)]
    txt(s, px0, PY_TOP - 0.34, 3.0, 0.2, name, size=10.5, color=INK, bold=True)
    line(s, px0, PY_TOP, px0, PY_BOT, INK, 0.9)
    line(s, px0, PY_BOT, px1, PY_BOT, INK, 0.9)
    for v in (0, 0.5, 1.0):
        line(s, px0 - 0.06, fpy(v), px0, fpy(v), INK, 0.9)
        txt(s, px0 - 0.62, fpy(v) - 0.075, 0.5, 0.16,
            {0: "0", 0.5: "0.5", 1.0: "1.0"}[v], size=8.5, color=INK2,
            align=PP_ALIGN.RIGHT)
    for x, p in zip(xs, (3, 5, 7, 9)):
        line(s, x, PY_BOT, x, PY_BOT + 0.06, INK, 0.9)
        txt(s, x - 0.3, PY_BOT + 0.10, 0.6, 0.16, str(p), size=8.5, color=INK2,
            align=PP_ALIGN.CENTER)
    for i in range(3):
        line(s, xs[i], fpy(high[i]), xs[i + 1], fpy(high[i + 1]), INK, 1.5)
        line(s, xs[i], fpy(low[i]), xs[i + 1], fpy(low[i + 1]), INK, 1.3, DASH.DASH)
    for i in range(4):
        if abs(high[i] - low[i]) < 0.02:
            dot(s, xs[i], fpy(high[i]), 0.05, "both")
        else:
            dot(s, xs[i], fpy(high[i]), 0.055, "fill")
            dot(s, xs[i], fpy(low[i]), 0.055, "open")
    for p, lbl, dx, dy in hlabels:
        i = {3: 0, 5: 1, 7: 2, 9: 3}[p]
        txt(s, xs[i] + dx, fpy(high[i]) + dy, 0.7, 0.18, lbl, size=9,
            color=INK, bold=True,
            align=PP_ALIGN.RIGHT if dx < 0 else PP_ALIGN.LEFT)
    for p, lbl, dx, dy in llabels:
        i = {3: 0, 5: 1, 7: 2, 9: 3}[p]
        txt(s, xs[i] + dx, fpy(low[i]) + dy, 0.7, 0.18, lbl, size=9,
            color=INK, bold=True,
            align=PP_ALIGN.RIGHT if dx < 0 else PP_ALIGN.LEFT)
txt(s, L, PY_BOT + 0.36, CW, 0.2,
    "safe payoff — points offered to walk away   (attempting pays 10 if the copies match, 0 if not)",
    size=8.5, color=INK2, align=PP_ALIGN.CENTER)
txt(s, 0.30, 3.05, 1.5, 0.9, "P(attempt\ncoordination)", size=8.5, color=INK2,
    align=PP_ALIGN.RIGHT, line_spacing=1.35)

legend(s, L, 5.52, [("solid", "Higher own-copy match"),
                    ("dash", "Lower own-copy match"),
                    ("both", "both, same value")])
readout(s, L, 5.90, 9.6,
        [("At a safe payoff of 3 or 5, both models play everything — there is "
          "nothing to reveal. The curves separate at ", False, INK),
         ("7 and 9", True, INK),
         (", exactly where the model has to decide whether its own copies are "
          "reliable enough to be worth the gamble.", False, INK)])
caption(s, 6.72,
        "One representative pair per model, n = 30 per point. GPT: c_contr_subtle vs b_spiral_cw. Claude: b_spiral_cw vs rot. "
        "A methodological consequence for the next study: cells at a safe payoff of 3 and 5 sit at ceiling and carry no information, "
        "so future designs concentrate trials at 7 and 9.")


# ============================================================ SLIDE 8 ========
s = new_slide()
eyebrow(s, "08", "Study 1 · introspection")
heading(s, "The behaviour knows.\nThe stated reason doesn’t.")

BY_BOT, BY_TOP = 4.95, 2.42     # 0 .. 100%
fby = lambda v: BY_BOT - v * (BY_BOT - BY_TOP)
line(s, 2.55, BY_TOP - 0.10, 2.55, BY_BOT, INK, 0.9)
line(s, 2.55, BY_BOT, 8.55, BY_BOT, INK, 0.9)
for v in (0, .25, .5, .75, 1.0):
    line(s, 2.49, fby(v), 2.55, fby(v), INK, 0.9)
    txt(s, 1.95, fby(v) - 0.075, 0.5, 0.16, f"{int(v*100)}%", size=8.5, color=INK2,
        align=PP_ALIGN.RIGHT)
txt(s, 0.55, 3.10, 1.3, 0.9, "rationale\nasserts a\nshared rule", size=8.5, color=INK2,
    align=PP_ALIGN.RIGHT, line_spacing=1.35)

bars = [(3.25, 0.91, "91%", "n = 570", True), (4.05, 0.92, "92%", "n = 357", False),
        (6.55, 0.08, "8%", "n = 127", True), (7.35, 0.06, "6%", "n = 106", False)]
BW = 0.76
for bx, v, lbl, n, filled in bars:
    h = BY_BOT - fby(v)
    box(s, bx, fby(v), BW, h, fill=INK if filled else PAPER,
        outline=None if filled else INK, width=1.1)
    txt(s, bx - 0.2, fby(v) - 0.24, BW + 0.4, 0.18, lbl, size=10, color=INK,
        bold=True, align=PP_ALIGN.CENTER)
    txt(s, bx - 0.2, BY_BOT + 0.10, BW + 0.4, 0.16, n, size=8, color=INK3,
        align=PP_ALIGN.CENTER)
for gx0, gx1, glab in ((3.25, 4.81, "attempted coordination"),
                       (6.55, 8.11, "took the safe payoff")):
    line(s, gx0, BY_BOT + 0.36, gx1, BY_BOT + 0.36, RULE, 0.9)
    txt(s, gx0 - 0.7, BY_BOT + 0.44, (gx1 - gx0) + 1.4, 0.18, glab, size=9.5,
        color=INK, bold=True, align=PP_ALIGN.CENTER)
# "identical" bracket over the two attempt bars
top = min(fby(0.91), fby(0.92)) - 0.30
line(s, 3.63, top + 0.10, 3.63, top, ACC, 1.1)
line(s, 4.43, top + 0.10, 4.43, top, ACC, 1.1)
line(s, 3.63, top, 4.43, top, ACC, 1.1)
txt(s, 3.23, top - 0.22, 1.6, 0.18, "identical", size=9, color=ACC, bold=True,
    align=PP_ALIGN.CENTER)

legend(s, L, 5.78, [("barfill", "Stimulus its copies can coordinate on"),
                    ("baropen", "Stimulus its copies can’t")])

txt(s, 8.95, 2.40, 3.48, 1.5,
    "Every Stage C trial comes with the model’s own written reasoning. We asked a "
    "simple question of those 1,160 traces: does the rationale claim there is a "
    "shared focal rule in the picture?",
    size=10.5, color=INK2, line_spacing=1.45)
txt(s, 8.95, 3.85, 3.48, 1.3,
    "When the model attempts, it claims one about 91% of the time either way — "
    "whether or not its copies will actually agree.",
    size=10.5, color=INK2, line_spacing=1.45)
readout(s, 8.95, 4.80, 3.48,
        [("The model’s choices are sensitive to a fact about its own policy that "
          "its explanations are blind to.", False, INK)], size=10.5)
caption(s, 6.25,
        "1,160 reasoning traces, frozen lexicon with a negation guard — a bare keyword match counted “not focal enough” "
        "as an assertion and had to be corrected. Rates, not counts, because the denominators are unequal.\n"
        "The SAFE contrast is close to tautological: declining to play and declining to claim a focal point are nearly the same act.",
        w=8.6)


# ============================================================ SLIDE 9 ========
s = new_slide()
eyebrow(s, "09", "Generation ladder")
heading(s, "Newer models price their own\nconventions more sharply.")

LX = [2.75, 4.55, 6.35, 8.15, 9.95]
LY_BOT, LY_TOP = 4.72, 2.42     # 0 .. 0.20
fly = lambda v: LY_BOT - v / 0.20 * (LY_BOT - LY_TOP)
line(s, LX[0] - 0.55, LY_TOP - 0.10, LX[0] - 0.55, LY_BOT, INK, 0.9)
line(s, LX[0] - 0.55, LY_BOT, 10.9, LY_BOT, INK, 0.9)
for v in (0, .05, .10, .15, .20):
    line(s, LX[0] - 0.61, fly(v), LX[0] - 0.55, fly(v), INK, 0.9)
    txt(s, LX[0] - 1.25, fly(v) - 0.075, 0.6, 0.16, "0" if v == 0 else f"+{v:.2f}",
        size=8.5, color=INK2, align=PP_ALIGN.RIGHT)
txt(s, 0.15, 2.95, 1.3, 1.2, "Δ P(attempt):\nreliable vs\nunreliable\nstimulus",
    size=8.5, color=INK2, align=PP_ALIGN.RIGHT, line_spacing=1.3)

openai = [(1, None, "GPT-4o"), (2, 0.008, "GPT-5"), (3, 0.081, "GPT-5.4"),
          (4, 0.175, "GPT-5.5")]
anthro = [(1, None, "Opus 4.5"), (2, None, "Opus 4.6"), (3, 0.063, "Opus 4.7"),
          (4, 0.026, "Opus 4.8"), (5, 0.100, "Opus 5")]

def draw_series(pts, dash, kind, above, ox=0.0):
    real = [(i, v) for i, v, _ in pts if v is not None]
    for a, b in zip(real, real[1:]):
        line(s, LX[a[0] - 1] + ox, fly(a[1]), LX[b[0] - 1] + ox, fly(b[1]), INK,
             1.5 if not dash else 1.3, DASH.DASH if dash else None)
    for i, v, name in pts:
        x = LX[i - 1] + ox
        if v is None:
            # no interpretable estimate — a dash on the baseline; the legend says why
            line(s, x - 0.11, fly(0.0) - 0.20, x + 0.11, fly(0.0) - 0.20, RULE, 1.6)
        else:
            hot = (name == "GPT-5.5")
            dot(s, x, fly(v), 0.058, "acc" if hot else kind)
            dy = -0.26 if above else 0.10
            txt(s, x - 0.6, fly(v) + dy, 1.2, 0.18,
                "+.%03d" % round(v * 1000),
                size=9, color=ACC if hot else INK, bold=True, align=PP_ALIGN.CENTER)

draw_series(openai, False, "fill", True, -0.15)
draw_series(anthro, True, "open", False, +0.15)
for i, _, name in openai:
    txt(s, LX[i - 1] - 0.85, LY_BOT + 0.10, 1.4, 0.16, name, size=8, color=INK3,
        align=PP_ALIGN.CENTER)
for i, _, name in anthro:
    txt(s, LX[i - 1] - 0.55, LY_BOT + 0.28, 1.4, 0.16, name, size=8, color=INK3,
        align=PP_ALIGN.CENTER)
txt(s, LX[0] - 0.55, LY_BOT + 0.52, 10.9 - LX[0] + 0.55, 0.18,
    "successive releases within each family →", size=8.5, color=INK2,
    align=PP_ALIGN.CENTER)

legend(s, L, 5.52, [("solid", "OpenAI"), ("dash", "Anthropic"),
                    ("nodata", "no interpretable estimate")])
readout(s, L, 5.90, 10.6,
        [("Across the OpenAI line the effect rises monotonically, roughly ", False, INK),
         ("twenty-fold", True, INK),
         (" from GPT-5 to GPT-5.5. The Anthropic line is flat and noisy — ", False, INK),
         ("not yet a trend", True, INK),
         (", and it should not be read as one.", False, INK)])
caption(s, 6.72,
        "Same frozen pipeline at every rung; pairs re-derived from each generation’s own ground truth, never carried over. "
        "GPT-4o and Opus 4.5 / 4.6 yield no estimate: 4.5 and 4.6 attempt coordination essentially always, even at a safe payoff of 9, "
        "so there is no variation to explain.\nOpus 4.7 and 4.8 are prospective 8- and 7-pair samples; 4.7’s initial 3-pair estimate "
        "was −0.103 and both are reported.")


# ============================================================ SLIDE 10 =======
s = new_slide()
eyebrow(s, "10", "Where this goes")
heading(s, "Where it stands, and the next test.")

line(s, L, 2.15, R, 2.15, RULE, 0.9)
cards = [("Coordination is set by the picture",
          "Partner framing moves it by ~0.05 and not reliably; the stimulus moves it by 0.44."),
         ("Conventions can be model-specific",
          "Two models can each be certain, and certain of opposite answers — 0.17 cross-model match."),
         ("Models bet on their own reliability",
          "All 5 matched pairs, 4 decisively, holding out 8 of 8 on split-sample validation."),
         ("The reason given doesn’t track it",
          "91% vs 92% assertion of a shared rule, whether or not one exists.")]
cwid = CW / 4
for i, (head, sub) in enumerate(cards):
    x = L + i * cwid
    txt(s, x, 2.32, cwid - 0.45, 0.16, "ESTABLISHED", size=7.5, color=ACC, spc=1.3)
    txt(s, x, 2.56, cwid - 0.45, 0.5, head, size=11, color=INK, bold=True,
        line_spacing=1.28)
    txt(s, x, 3.16, cwid - 0.45, 0.9, sub, size=9.5, color=INK2, line_spacing=1.4)
line(s, L, 3.98, R, 3.98, RULE, 0.9)

nexts = [("NEXT", "Study 2 — does the bet depend on who the partner is?",
          "A model that knows its own convention should bet it only against a partner "
          "who shares it. The test is a stimulus × partner crossover: one picture "
          "where a copy of itself is the better partner, one where the other lab’s model is."),
         ("OPEN", "The design rests on one stimulus.",
          "The chevrons carry about 85% of the predicted interaction, and they are "
          "measured at n = 60 with a wide interval. Confirming that number is the gate "
          "on everything downstream."),
         ("OPEN", "What kind of self-knowledge is this?",
          "Behaviour is sensitive to a property of the model’s own policy that its "
          "explanations cannot name. Whether that is introspection or a learned "
          "regularity is not settled here.")]
y = 4.22
for tag, head, sub in nexts:
    txt(s, L, y + 0.02, 0.55, 0.18, tag, size=8.5, color=ACC, bold=True, spc=1.0)
    rich(s, L + 0.72, y, 10.4, 0.6,
         [(head + "  ", True, INK), (sub, False, INK2)], size=10.5, line_spacing=1.42)
    y += 0.92
    line(s, L + 0.72, y - 0.16, R, y - 0.16, RULE, 0.7)

OUT = "self-coordination-deck.pptx"
prs.save(OUT)
print("wrote", OUT, "slides:", len(prs.slides.__iter__.__self__._sldIdLst))
