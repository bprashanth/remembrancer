#!/usr/bin/env python3
"""Render a Template to a blank vector PDF and record exact geometry.

The PDF is drawn with real vector lines and text, so:
  * geometry is EXACT — recorded here at draw time in PDF points, never
    inferred from pixels downstream;
  * the sibling's fill_template.extract_structure() can independently
    re-derive the grid from the file (used as a sanity check in tests).

The page carries the form ID twice: a QR code (machine path) and printed
text (human path + model-readable fallback). Choice-column legends are
printed on the form itself — the paper tells the writer what the allowed
codes are, which is both good form design and the small model's biggest
disambiguation aid.
"""
from __future__ import annotations

import io
from pathlib import Path

import fitz

from .template import Template, save as save_template, TEMPLATES_DIR

A4 = (595.276, 841.890)
MARGIN = 36.0
FONT, FONT_B = "helv", "hebo"
INKLINE = (0.25, 0.25, 0.28)
FAINT = (0.55, 0.55, 0.58)


def _wrap(text, width, fontsize, fontname=FONT_B):
    """Greedy word wrap to fit `width` points."""
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if fitz.get_text_length(t, fontname=fontname, fontsize=fontsize) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def _qr_png(data: str, box=3) -> bytes:
    import qrcode
    qr = qrcode.QRCode(border=1, box_size=box,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.get_image().save(buf, "PNG")
    return buf.getvalue()


def col_widths(t: Template, total: float) -> list[float]:
    from .template import DEFAULT_WEIGHT
    ws = []
    for c in t.columns:
        base = c.width if c.width else DEFAULT_WEIGHT.get(c.type, 2.0)
        # a column must at least fit its longest allowed code
        if c.type == "choice" and c.domain:
            base = max(base, 0.5 + 0.22 * max(len(d) for d in c.domain))
        ws.append(base)
    widths = [w / sum(ws) * total for w in ws]
    # hard floor so no column collapses below writable width
    MINW = 26.0
    if any(w < MINW for w in widths):
        if MINW * len(widths) > total:
            raise ValueError("too many columns for this page — use landscape "
                             "or drop columns")
        fixed = [max(w, MINW) for w in widths]
        over = sum(fixed) - total
        big = [i for i, w in enumerate(fixed) if w > MINW]
        red = sum(fixed[i] - MINW for i in big)
        for i in big:
            fixed[i] -= over * (fixed[i] - MINW) / red
        widths = fixed
    return widths


def render(t: Template, out_dir: Path = None) -> dict:
    """Draw the blank form. Writes blank.pdf + preview.png, returns geometry
    (also stored into t.geometry and persisted)."""
    out_dir = out_dir or (TEMPLATES_DIR / t.form_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    W, H = A4 if t.orientation == "portrait" else A4[::-1]
    doc = fitz.open()
    page = doc.new_page(width=W, height=H)
    geo = {"page": [W, H], "margin": MARGIN}

    # ── title + form id ──────────────────────────────────────────
    qr_size = 44.0
    qr_x0, qr_y0 = W - MARGIN - qr_size, 18.0
    page.insert_image(fitz.Rect(qr_x0, qr_y0, qr_x0 + qr_size, qr_y0 + qr_size),
                      stream=_qr_png(t.form_id))
    idw = fitz.get_text_length(t.form_id, fontname=FONT_B, fontsize=8)
    page.insert_text((qr_x0 + qr_size / 2 - idw / 2, qr_y0 + qr_size + 9),
                     t.form_id, fontname=FONT_B, fontsize=8)
    geo["qr"] = [qr_x0, qr_y0, qr_x0 + qr_size, qr_y0 + qr_size]

    title_size = 15 if len(t.title) < 60 else 12
    tw = fitz.get_text_length(t.title, fontname=FONT_B, fontsize=title_size)
    page.insert_text((max(MARGIN, (W - tw) / 2), 40), t.title,
                     fontname=FONT_B, fontsize=title_size)
    y = 58.0

    # ── header fields ────────────────────────────────────────────
    geo["header_fields"] = {}
    if t.header_fields:
        per_row = 2 if t.orientation == "portrait" else 3
        n = len(t.header_fields)
        per_row = min(per_row, n)
        colw = (W - 2 * MARGIN) / per_row
        fh = 24.0
        for i, h in enumerate(t.header_fields):
            r, c = divmod(i, per_row)
            x = MARGIN + c * colw
            yy = y + r * fh
            label = h.label + ":"
            page.insert_text((x, yy + 13), label, fontname=FONT, fontsize=9.5)
            lx = x + fitz.get_text_length(label, fontname=FONT, fontsize=9.5) + 6
            x1 = x + colw - 14
            page.draw_line(fitz.Point(lx, yy + 16), fitz.Point(x1, yy + 16),
                           color=FAINT, width=0.7)
            geo["header_fields"][h.key] = [lx, yy - 2, x1, yy + 16]
        y += fh * ((n + per_row - 1) // per_row) + 10
    else:
        y += 6

    # ── table ────────────────────────────────────────────────────
    left, right = MARGIN, W - MARGIN
    widths = col_widths(t, right - left)
    xs = [left]
    for w in widths:
        xs.append(xs[-1] + w)
    xs[-1] = right

    # wrapped header labels
    hdr_size = 8.5
    wrapped = [_wrap(c.label, widths[i] - 6, hdr_size) for i, c in enumerate(t.columns)]
    hdr_lines = max(len(ws) for ws in wrapped)
    header_h = 8 + hdr_lines * (hdr_size + 2.5)
    table_top = y
    # legend + footer space
    legends = [(c.label, c.legend) for c in t.columns if c.legend]
    legend_h = 14 + 10.5 * len(legends) if legends else 0
    footer_h = 16
    avail = H - table_top - header_h - legend_h - footer_h - 8
    if t.rows * t.row_height > avail:
        max_rows = int(avail // t.row_height)
        raise ValueError(
            f"{t.rows} rows do not fit on one {t.orientation} page with this "
            f"header (max {max_rows}). Reduce rows, shrink row height, or "
            f"switch orientation.")

    # header cells
    for i, ws_ in enumerate(wrapped):
        cx = (xs[i] + xs[i + 1]) / 2
        ty = table_top + 6 + hdr_size
        for ln in ws_:
            lw = fitz.get_text_length(ln, fontname=FONT_B, fontsize=hdr_size)
            page.insert_text((cx - lw / 2, ty), ln, fontname=FONT_B,
                             fontsize=hdr_size)
            ty += hdr_size + 2.5
    data_top = table_top + header_h
    table_bot = data_top + t.rows * t.row_height

    # serial numbers pre-printed
    for ci, c in enumerate(t.columns):
        if c.type == "serial":
            for r in range(t.rows):
                s = str(r + 1)
                sw = fitz.get_text_length(s, fontname=FONT, fontsize=8.5)
                page.insert_text(((xs[ci] + xs[ci + 1]) / 2 - sw / 2,
                                  data_top + r * t.row_height + t.row_height / 2 + 3),
                                 s, fontname=FONT, fontsize=8.5, color=INKLINE)

    # grid lines
    page.draw_line(fitz.Point(left, table_top), fitz.Point(right, table_top),
                   color=INKLINE, width=1.1)
    page.draw_line(fitz.Point(left, data_top), fitz.Point(right, data_top),
                   color=INKLINE, width=1.1)
    yy = data_top
    row_y = [data_top]
    for r in range(t.rows):
        yy += t.row_height
        row_y.append(yy)
        page.draw_line(fitz.Point(left, yy), fitz.Point(right, yy),
                       color=INKLINE, width=0.7 if r < t.rows - 1 else 1.1)
    for x in xs:
        page.draw_line(fitz.Point(x, table_top), fitz.Point(x, table_bot),
                       color=INKLINE, width=0.8)

    geo["table"] = {"x": xs, "header_y": [table_top, data_top], "row_y": row_y}

    # ── fiducial marks (OMR-style) ───────────────────────────────
    # A phone photo of a curled page bows nonlinearly; generic warp recovery
    # is fragile. Because WE print the form, we anchor it instead: a filled
    # square beside every row rule in both margins, and a tick under every
    # column edge. Extraction then reads geometry off the marks, row by row.
    fid = {"left": [], "right": [], "col": []}
    mw, mh = 7.0, 4.6                      # mark size in pt
    for k, yy in enumerate([table_top, data_top] + row_y[1:]):
        # the first mark is a TALL bar — an unambiguous sequence anchor so
        # detection can never be off by one row
        h = mh * 2.8 if k == 0 else mh
        for side, x0f in (("left", left - 14 - mw), ("right", right + 14)):
            page.draw_rect(fitz.Rect(x0f, yy - h / 2, x0f + mw, yy + h / 2),
                           color=None, fill=(0, 0, 0))
            fid[side].append([x0f + mw / 2, yy])
    ty = table_bot + 5.5
    for x in xs:
        page.draw_rect(fitz.Rect(x - mh / 2, ty, x + mh / 2, ty + mw),
                       color=None, fill=(0, 0, 0))
        fid["col"].append([x, ty + mw / 2])
    geo["fiducials"] = fid

    # ── legends + footer ─────────────────────────────────────────
    ly = table_bot + 22                      # below the column fiducial ticks
    # collapse runs of columns that share one legend ("D1-D8: P=Present, ...")
    grouped, i = [], 0
    while i < len(legends):
        j = i
        while j + 1 < len(legends) and legends[j + 1][1] == legends[i][1]:
            j += 1
        lab = legends[i][0] if i == j else f"{legends[i][0]} – {legends[j][0]}"
        grouped.append((lab, legends[i][1]))
        i = j + 1
    for label, legend in grouped:
        page.insert_text((left, ly), f"{label}:  {legend}",
                         fontname=FONT, fontsize=8, color=INKLINE)
        ly += 10.5
    foot = ("Write inside the boxes. A dot = 0. A tick = yes. "
            "Leave a cell blank if there is nothing to record.")
    page.insert_text((left, H - 22), foot, fontname=FONT, fontsize=7.5,
                     color=FAINT)
    page.insert_text((right - fitz.get_text_length(
        f"paperroast · {t.form_id}", fontname=FONT, fontsize=7.5), H - 22),
        f"paperroast · {t.form_id}", fontname=FONT, fontsize=7.5, color=FAINT)

    doc.save(str(out_dir / "blank.pdf"))
    # preview png
    pm = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    pm.save(str(out_dir / "preview.png"))
    doc.close()

    t.geometry = geo
    save_template(t, out_dir.parent)
    return geo


def render_from_spec(spec: dict, out_root: Path = None) -> Template:
    from .template import from_spec
    t = from_spec(spec)
    render(t, (out_root or TEMPLATES_DIR) / t.form_id)
    return t
