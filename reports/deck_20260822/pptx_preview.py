#!/usr/bin/env python3
"""
Render a .pptx back to SVG by reading the shapes that are actually in the file.

This is a verification pass, not a converter: it re-draws every autoshape,
connector and text box from the saved XML so the geometry can be eyeballed
before the deck is handed over. Font metrics are approximated, so text may wrap
slightly differently than PowerPoint will — positions and marks are exact.
"""
import sys, html
from pptx import Presentation
from pptx.util import Emu

EMU = 914400.0
SCALE = 96.0  # px per inch in the preview


def hexof(color_fmt, default=None):
    try:
        if color_fmt and color_fmt.type is not None:
            return "#%s" % str(color_fmt.rgb)
    except Exception:
        pass
    return default


def fill_of(sh):
    try:
        f = sh.fill
        if f.type is None:
            return None
        if f.type == 5:          # background / none
            return None
        if f.type == 1:          # solid
            return hexof(f.fore_color, "#000000")
    except Exception:
        pass
    return None


def line_of(sh):
    try:
        ln = sh.line
        col = hexof(ln.color, None)
        w = ln.width.pt if ln.width is not None else 0.75
        dash = None
        try:
            dash = ln.dash_style
        except Exception:
            pash = None
        if col is None:
            return None, 0, None
        return col, w, dash
    except Exception:
        return None, 0, None


def run_svg(sh, out):
    if not sh.has_text_frame:
        return
    tf = sh.text_frame
    x = sh.left / EMU * SCALE
    y = sh.top / EMU * SCALE
    w = sh.width / EMU * SCALE
    cy = y
    for p in tf.paragraphs:
        txt = "".join(r.text for r in p.runs)
        if not txt.strip():
            cy += 12
            continue
        r0 = p.runs[0]
        size = r0.font.size.pt if r0.font.size else 11
        fam = r0.font.name or "Arial"
        col = hexof(r0.font.color, "#000000")
        bold = "bold" if r0.font.bold else "normal"
        ital = "italic" if r0.font.italic else "normal"
        align = str(p.alignment or "")
        px = x
        anchor = "start"
        if "CENTER" in align:
            px = x + w / 2; anchor = "middle"
        elif "RIGHT" in align:
            px = x + w; anchor = "end"
        # crude wrap so long paragraphs show their real extent
        cpl = max(6, int(w / (size * 0.52)))
        words, lineb, lines = txt.split(), "", []
        for wd in words:
            if len(lineb) + len(wd) + 1 <= cpl:
                lineb = (lineb + " " + wd).strip()
            else:
                lines.append(lineb); lineb = wd
        if lineb:
            lines.append(lineb)
        lh = size * 1.34 * (p.line_spacing or 1.25) / 1.25
        for ln in lines:
            cy += size * 0.98
            out.append(
                f'<text x="{px:.1f}" y="{cy:.1f}" font-family="{fam}" '
                f'font-size="{size:.1f}" fill="{col}" font-weight="{bold}" '
                f'font-style="{ital}" text-anchor="{anchor}">{html.escape(ln)}</text>')
            cy += lh - size * 0.98
        cy += 2


def render(path, out_prefix):
    prs = Presentation(path)
    Wp = prs.slide_width / EMU * SCALE
    Hp = prs.slide_height / EMU * SCALE
    files = []
    for idx, slide in enumerate(prs.slides, 1):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wp:.0f}" '
               f'height="{Hp:.0f}" viewBox="0 0 {Wp:.0f} {Hp:.0f}">']
        bg = "#FFFFFF"
        try:
            bg = "#%s" % str(slide.background.fill.fore_color.rgb)
        except Exception:
            pass
        out.append(f'<rect width="{Wp}" height="{Hp}" fill="{bg}"/>')
        for sh in slide.shapes:
            st = str(sh.shape_type)
            x = sh.left / EMU * SCALE
            y = sh.top / EMU * SCALE
            w = sh.width / EMU * SCALE
            h = sh.height / EMU * SCALE
            col, lw, dash = line_of(sh)
            fl = fill_of(sh)
            if "CONNECTOR" in st or sh.element.tag.endswith("}cxnSp"):
                xfrm = sh.element.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm")
                fh = xfrm is not None and xfrm.get("flipH") in ("1", "true")
                fv = xfrm is not None and xfrm.get("flipV") in ("1", "true")
                x1, x2 = (x + w, x) if fh else (x, x + w)
                y1, y2 = (y + h, y) if fv else (y, y + h)
                d = ' stroke-dasharray="5 4"' if dash and "DASH" in str(dash) else ""
                out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
                           f'y2="{y2:.1f}" stroke="{col or "#000"}" '
                           f'stroke-width="{lw*1.33:.2f}"{d}/>')
                continue
            try:
                st = st + " " + str(sh.auto_shape_type)
            except Exception:
                pass
            if "PICTURE" in st:
                import base64
                blob = sh.image.blob
                b64 = base64.b64encode(blob).decode()
                out.append(f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
                           f'height="{h:.1f}" href="data:image/png;base64,{b64}"/>')
                continue
            if "OVAL" in st:
                out.append(f'<ellipse cx="{x+w/2:.1f}" cy="{y+h/2:.1f}" '
                           f'rx="{w/2:.1f}" ry="{h/2:.1f}" '
                           f'fill="{fl or "none"}" stroke="{col or "none"}" '
                           f'stroke-width="{lw*1.33:.2f}"/>')
            elif "RECTANGLE" in st:
                out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
                           f'height="{h:.1f}" fill="{fl or "none"}" '
                           f'stroke="{col or "none"}" stroke-width="{lw*1.33:.2f}"/>')
            run_svg(sh, out)
        out.append("</svg>")
        fn = f"{out_prefix}{idx:02d}.svg"
        open(fn, "w").write("\n".join(out))
        files.append(fn)
    return files


if __name__ == "__main__":
    for f in render(sys.argv[1], sys.argv[2]):
        print(f)
