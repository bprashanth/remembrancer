#!/usr/bin/env python3
"""Fill a paperroast template with synthetic handwriting -> photo + exact golden.

The builder gives us exact cell geometry, so unlike the sibling's
fill_template.py we never re-derive structure from the PDF: we raster the
blank, composite real NIST SD-19 handwriting glyphs (via formgen2.Writer —
the piece the sibling measured as worth +0.10 F1 over handwriting fonts)
into known boxes, and record the golden grid as we write it.

Realism axes (BRIEF §4, in measured order of importance):
  * real ink: SD-19 glyph cohorts, one writer per sheet, pencil ~22%
  * vocabulary: sector lexicons + deliberate OOV tokens
  * notation: dot=0, ticks, strikes, corrections, occasional stray margin note
  * fill density: sampled ~uniform 0.1-1.0, filled top-down like real sheets
  * photo degradation: phone-camera pipeline + augraphy (cheap; low measured
    effect, so not over-invested in)

Golden is exact by construction: what we wrote is what we score against —
including cells left genuinely blank, which the scorer checks positionally.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).parent.parent
SIBLING_GEN = Path.home() / "src/github.com/bprashanth/form-idable/benchmarks/wide/gen"
sys.path.insert(0, str(SIBLING_GEN))
import formgen2 as fg                                    # noqa: E402

from .template import Template, empty_grid, grid_to_xlsx  # noqa: E402

MAX_DIM = 2200


def _load_lexicons():
    p = ROOT / "data" / "specs" / "lexicons.json"
    if p.exists():
        return json.loads(p.read_text())
    # minimal fallback so fill works before the lexicon file lands
    return {"person_first": fg.FIRST, "person_last": fg.LAST,
            "villages": fg.SITES, "health_diagnosis": ["fever", "cough"],
            "health_remarks": ["referred"], "edu_subjects": ["Maths"],
            "edu_remarks": ["good"], "shg_purpose": ["school fees"],
            "agri_crops": ["paddy", "tur"], "agri_remarks": ["late sowing"],
            "oov": ["Kanverappa", "Jothimani"]}


LEX = _load_lexicons()


def _text_pool(label: str, sector: str):
    lab = label.lower()
    if "diagnos" in lab or "complaint" in lab or "illness" in lab:
        return LEX["health_diagnosis"]
    if "purpose" in lab:
        return LEX["shg_purpose"]
    if "crop" in lab:
        return LEX["agri_crops"]
    if "subject" in lab:
        return LEX["edu_subjects"]
    if "village" in lab or "place" in lab or "address" in lab:
        return LEX["villages"]
    return LEX.get(f"{sector}_remarks", LEX["health_remarks"])


def _gen_value(col, rng, sector):
    """Generate the handwritten value for one cell -> (spec, golden_value).

    spec is what gets DRAWN; golden is what a perfect transcription would
    record for it (None = cell stays/reads empty)."""
    t = col.type
    if t == "int":
        lo = int(col.min if col.min is not None else 0)
        hi = int(col.max if col.max is not None else 250)
        v = rng.randint(lo, hi)
        r = rng.random()
        if v == 0 and r < 0.5:
            return ("dot",), "0"
        if r < 0.03:
            return ("strike",), None
        if r < 0.07:
            wrong = str(rng.randint(lo, hi))
            return ("corr", wrong, str(v)), str(v)
        return ("text", str(v)), str(v)
    if t == "dec":
        lo = float(col.min if col.min is not None else 0.5)
        hi = float(col.max if col.max is not None else 120.0)
        v = f"{rng.uniform(lo, hi):.1f}"
        if rng.random() < 0.04:
            wrong = f"{rng.uniform(lo, hi):.1f}"
            return ("corr", wrong, v), v
        return ("text", v), v
    if t == "date":
        v = f"{rng.randint(1,28):02d}/{rng.randint(1,12):02d}/{rng.choice(['25','26','2025','2026'])}"
        return ("text", v), v
    if t == "yn":
        r = rng.random()
        if r < 0.30:
            return ("tick",), "Y"
        v = rng.choice(["Y", "N", "Y", "N", "y", "n"])
        return ("text", v), v.upper()
    if t == "choice":
        v = rng.choice(col.domain)
        if rng.random() < 0.15 and v.isalpha():
            v = v.lower() if rng.random() < 0.5 else v
        return ("text", v), v
    if t == "name":
        if rng.random() < 0.08:
            v = rng.choice(LEX["oov"])
        else:
            v = rng.choice(LEX["person_first"])
            r = rng.random()
            if r < 0.35:
                v += " " + rng.choice(LEX["person_last"])
            elif r < 0.5:
                v += " " + rng.choice("ABCDGKMPRSV") + "."
        return ("text", v), v
    # text
    pool = _text_pool(col.label, sector)
    v = rng.choice(LEX["oov"]) if rng.random() < 0.05 else rng.choice(pool)
    return ("text", v), v


_MONTHS = ["January", "February", "March", "June", "July", "August",
           "September", "October", "November", "Jan", "Feb", "Jun", "Jul",
           "Aug", "Sept", "Oct", "Nov"]


def _gen_header_value(h, rng):
    """Label semantics first (a 'Month' field gets a month, whatever its
    declared type), then declared type, then village fallback."""
    lab = h.label.lower()
    if h.domain:
        return rng.choice([str(d) for d in h.domain])
    if "month" in lab:
        v = rng.choice(_MONTHS)
        return v + (" 2025" if rng.random() < 0.4 else "")
    if "year" in lab:
        return rng.choice(["2024-25", "2025-26", "2025", "2026"])
    if "class" in lab or "standard" in lab:
        return f"{rng.randint(1, 10)} {rng.choice('ABC')}" \
            if rng.random() < 0.6 else f"Std {rng.randint(1, 10)}"
    if "school" in lab or "centre" in lab or "center" in lab:
        return ("GPS " if rng.random() < 0.4 else "") + rng.choice(LEX["villages"])
    if h.type == "date" or "date" in lab:
        return f"{rng.randint(1,28):02d}/{rng.randint(1,12):02d}/25"
    if h.type == "name" or "name" in lab or "worker" in lab or "teacher" in lab:
        return rng.choice(LEX["person_first"]) + " " + rng.choice(LEX["person_last"])
    if h.type in ("int", "dec"):
        return str(rng.randint(1, 60))
    return rng.choice(LEX["villages"])


def _draw_spec(writer, img, box, spec, size):
    """Draw one cell spec into pixel box using the formgen2 Writer."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    k = spec[0]
    if k == "text":
        s = str(spec[1])
        wd = writer.measure(s, size)
        writer.text(img, (max(x0 + 6, cx - wd / 2), cy - size * 0.55), s,
                    size=size, max_w=x1 - x0 - 10)
    elif k == "dot":
        writer.dot(img, cx + writer.rng.uniform(-5, 5), cy + writer.rng.uniform(-3, 3))
    elif k == "strike":
        writer.strike(img, x0 + 6, x1 - 6, cy)
    elif k == "tick":
        writer.tick(img, cx, cy, size=size * 0.5)
    elif k == "corr":
        wrong, right = str(spec[1]), str(spec[2])
        wd = writer.measure(wrong, size * 0.9)
        sx = max(x0 + 5, cx - wd / 2)
        writer.text(img, (sx, cy - size * 0.40), wrong, size=size * 0.9)
        writer.strike(img, sx - 3, sx + wd + 3, cy + size * 0.05)
        writer.text(img, (sx + 3, y0 - size * 0.10), right, size=size * 0.72)


def fill_form(t: Template, out_dir: Path, seed=0, density=None, photo=None,
              hard=False, medium=None, sector=None) -> dict:
    """Produce input.jpg (+input.pdf), golden.xlsx, meta.json in out_dir."""
    rng = random.Random(f"{t.form_id}:{seed}")
    density = density if density is not None else rng.uniform(0.1, 1.0)
    photo = photo if photo is not None else rng.choices(
        [None, "mild", "field", "rough"], [3, 3, 4, 2])[0]
    sector = sector or "health"

    blank_pdf = ROOT / "data" / "templates" / t.form_id / "blank.pdf"
    doc = fitz.open(str(blank_pdf))
    page = doc[0]
    scale = min(MAX_DIM / max(page.rect.width, page.rect.height), 4.0)
    pm = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
    img = Image.frombytes("RGB", (pm.width, pm.height), pm.samples).convert("RGBA")
    doc.close()

    writer = fg.Writer(rng, prose=rng.choice(["hybrid", "hybrid", "glyph"]),
                       medium=medium)
    geo = t.geometry
    golden = empty_grid(t)

    # header fields
    for h in t.header_fields:
        bbox = geo["header_fields"].get(h.key)
        if not bbox:
            continue
        v = _gen_header_value(h, rng)
        x0, y0, x1, y1 = [c * scale for c in bbox]
        size = max(16, min(30, (y1 - y0) * 0.95))
        writer.text(img, (x0 + 6, y0 + (y1 - y0) * 0.05), v, size=size,
                    max_w=x1 - x0 - 10)
        for i, (lab, _) in enumerate(golden["header"]):
            if lab == h.label:
                golden["header"][i] = (lab, v)

    # table cells, top-down to `density`
    xs, row_y = geo["table"]["x"], geo["table"]["row_y"]
    n_fill = max(1, round(t.rows * density))
    filled_cells = 0
    for r in range(n_fill):
        for ci, col in enumerate(t.columns):
            if col.type == "serial":
                continue
            if rng.random() < 0.07:                      # skipped cell
                continue
            spec, gold = _gen_value(col, rng, sector)
            box = (xs[ci] * scale, row_y[r] * scale,
                   xs[ci + 1] * scale, row_y[r + 1] * scale)
            size = max(13, min(36, (box[3] - box[1]) * 0.60))
            _draw_spec(writer, img, box, spec, size)
            if gold is not None:
                golden["table"][r + 1][ci] = gold
                filled_cells += 1

    # stray margin scribble (NOT in golden — extraction must ignore it)
    margin_note = None
    if rng.random() < 0.18:
        margin_note = rng.choice(["call AWW", str(rng.randint(100, 9999)),
                                  rng.choice(LEX["person_first"]),
                                  "check", "9" + str(rng.randint(100000000, 999999999))])
        my = geo["table"]["row_y"][-1] * scale + rng.uniform(20, 60)
        writer.text(img, (rng.uniform(60, 300), min(my, img.height - 60)),
                    margin_note, size=26)

    out_dir.mkdir(parents=True, exist_ok=True)
    final = fg.degrade(img, rng, hard=hard, photo=photo)
    final.save(out_dir / "input.jpg", "JPEG", quality=90)
    d2 = fitz.open()
    r2 = fitz.Rect(0, 0, final.width * 72 / 180, final.height * 72 / 180)
    d2.new_page(width=r2.width, height=r2.height).insert_image(
        r2, filename=str(out_dir / "input.jpg"))
    d2.save(out_dir / "input.pdf"); d2.close()

    grid_to_xlsx(golden, out_dir / "golden.xlsx")
    meta = {"form_id": t.form_id, "seed": seed, "density": round(density, 3),
            "photo": photo, "hard": hard, "medium": writer.medium,
            "cohort": writer.cohort, "filled_cells": filled_cells,
            "rows_filled": n_fill, "margin_note": margin_note}
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta
