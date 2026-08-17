#!/usr/bin/env python3
"""paperroast web app — design forms, print them, upload filled photos,
verify the extraction side-by-side. Everything local.

    .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 7500
"""
from __future__ import annotations

import base64
import io
import json
import secrets
import sys
import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import (FileResponse, HTMLResponse, JSONResponse,
                               Response)

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core import template as T                      # noqa: E402
from core.render import render_from_spec            # noqa: E402
from core.extract import extract, extraction_to_xlsx  # noqa: E402
from core.fill import fill_form                     # noqa: E402

app = FastAPI(title="paperroast")

# recent extractions kept in memory for the review UI
JOBS: dict[str, dict] = {}
MAX_JOBS = 40

DEFAULT_PROVIDER = "local-2b"


@app.get("/", response_class=HTMLResponse)
def index():
    return (ROOT / "app" / "static" / "index.html").read_text()


@app.get("/static/{name}")
def static(name: str):
    p = ROOT / "app" / "static" / name
    if not p.exists() or ".." in name:
        raise HTTPException(404)
    ctype = {"js": "application/javascript", "css": "text/css",
             "html": "text/html"}.get(p.suffix[1:], "application/octet-stream")
    return Response(p.read_bytes(), media_type=ctype)


# ── templates ─────────────────────────────────────────────────────
@app.get("/api/templates")
def api_templates():
    return T.list_templates()


@app.post("/api/templates")
def api_create_template(spec: dict):
    try:
        t = render_from_spec(spec)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"form_id": t.form_id, "preview": f"/api/templates/{t.form_id}/preview.png",
            "pdf": f"/api/templates/{t.form_id}/blank.pdf"}


@app.get("/api/templates/{form_id}")
def api_get_template(form_id: str):
    try:
        return T.to_dict(T.load(form_id))
    except FileNotFoundError:
        raise HTTPException(404, f"no template {form_id}")


@app.get("/api/templates/{form_id}/{fname}")
def api_template_file(form_id: str, fname: str):
    if fname not in ("blank.pdf", "preview.png"):
        raise HTTPException(404)
    p = T.TEMPLATES_DIR / form_id / fname
    if not p.exists():
        raise HTTPException(404)
    mt = "application/pdf" if fname.endswith("pdf") else "image/png"
    return FileResponse(p, media_type=mt,
                        filename=f"{form_id}_{fname}" if fname.endswith("pdf") else None)


@app.post("/api/templates/{form_id}/sample")
def api_sample(form_id: str, seed: int = Form(None), density: float = Form(None)):
    """Generate a synthetic hand-filled sample of this template (demo/test)."""
    try:
        t = T.load(form_id)
    except FileNotFoundError:
        raise HTTPException(404, f"no template {form_id}")
    seed = seed if seed is not None else secrets.randbelow(10 ** 6)
    d = Path(tempfile.mkdtemp(prefix="pr_sample_"))
    meta = fill_form(t, d, seed=seed, density=density)
    img = (d / "input.jpg").read_bytes()
    return {"meta": meta,
            "image": "data:image/jpeg;base64," + base64.b64encode(img).decode()}


# ── extraction ────────────────────────────────────────────────────
@app.post("/api/extract")
async def api_extract(f: UploadFile = File(...), provider: str = Form(DEFAULT_PROVIDER),
                      form_id: str = Form(None)):
    raw = await f.read()
    suffix = Path(f.filename or "u.jpg").suffix.lower() or ".jpg"
    tmp = Path(tempfile.mkdtemp(prefix="pr_up_")) / f"input{suffix}"
    tmp.write_bytes(raw)
    tpl = None
    if form_id:
        try:
            tpl = T.load(form_id)
        except FileNotFoundError:
            raise HTTPException(400, f"unknown form_id {form_id}")
    try:
        ex = extract(tmp, provider, template=tpl)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"extraction failed: {type(e).__name__}: {e}")
    token = secrets.token_urlsafe(8)
    xlsx = tmp.parent / "extracted.xlsx"
    if ex.grid:
        extraction_to_xlsx(ex, xlsx)
    JOBS[token] = {"ex": ex, "xlsx": xlsx if ex.grid else None,
                   "t": time.time(), "name": Path(f.filename or "form").stem}
    while len(JOBS) > MAX_JOBS:
        JOBS.pop(next(iter(JOBS)))
    tpl_geo = None
    if ex.form_id:
        try:
            tpl_geo = T.to_dict(T.load(ex.form_id))
        except FileNotFoundError:
            pass
    return {
        "token": token, "form_id": ex.form_id, "verdict": ex.verdict,
        "overlay": ex.overlay,
        "reasons": ex.reasons, "stats": ex.stats, "flags": ex.flags,
        "grid": {"table": ex.grid["table"],
                 "header": ex.grid["header"]} if ex.grid else None,
        "template": tpl_geo,
        "aligned": ("data:image/png;base64,"
                    + base64.b64encode(ex.aligned_png).decode())
        if ex.aligned_png else None,
        "xlsx": f"/api/download/{token}" if ex.grid else None,
    }


@app.get("/api/cell/{token}/{r}/{c}")
def api_cell_crop(token: str, r: int, c: int):
    """Zoomed crop of one cell from the stored aligned image, using the
    detected mark geometry when available (review UX)."""
    import io as _io
    from PIL import Image as _Image
    j = JOBS.get(token)
    if not j:
        raise HTTPException(404)
    ex = j["ex"]
    if not ex.aligned_png or not ex.form_id:
        raise HTTPException(404)
    t = T.load(ex.form_id)
    im = _Image.open(_io.BytesIO(ex.aligned_png))
    from core.extract import MAX_DIM
    import fitz as _fitz
    pdf = T.TEMPLATES_DIR / ex.form_id / "blank.pdf"
    doc = _fitz.open(str(pdf))
    pg = doc[0]
    scale = min(MAX_DIM / max(pg.rect.width, pg.rect.height), 4.0)
    doc.close()
    xs = t.geometry["table"]["x"]
    if not (0 <= r < t.rows and 0 <= c < len(xs) - 1):
        raise HTTPException(400)
    if ex.overlay:
        yl = ex.overlay["left"]
        y0 = min(yl[r + 1][1], ex.overlay["right"][r + 1][1])
        y1 = max(yl[r + 2][1], ex.overlay["right"][r + 2][1])
    else:
        ys = t.geometry["table"]["row_y"]
        y0, y1 = ys[r] * scale, ys[r + 1] * scale
    x0, x1 = xs[c] * scale, xs[c + 1] * scale
    pad = 10
    crop = im.crop((int(x0) - pad, int(y0) - pad, int(x1) + pad, int(y1) + pad))
    k = max(1.0, min(5.0, 420 / max(crop.size)))
    if k > 1:
        crop = crop.resize((int(crop.width * k), int(crop.height * k)))
    buf = _io.BytesIO()
    crop.save(buf, "PNG")
    return Response(buf.getvalue(), media_type="image/png")


@app.get("/api/download/{token}")
def api_download(token: str):
    j = JOBS.get(token)
    if not j or not j.get("xlsx") or not Path(j["xlsx"]).exists():
        raise HTTPException(404)
    return FileResponse(j["xlsx"], filename=f"{j['name']}_extracted.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


DESIGN_PROMPT = """You are looking at a photo or scan of a PAPER FORM (it may
be blank or hand-filled). Propose a reusable digital template for it as JSON:

{"title": str,
 "orientation": "portrait"|"landscape",
 "rows": int,                       // data rows the table should have
 "header_fields": [{"label": str, "type": "text"|"date"|"name"|"int"}],
 "columns": [{"label": str,
              "type": "serial"|"int"|"dec"|"date"|"yn"|"choice"|"name"|"text",
              "domain": [..],       // choice only: the allowed codes/values
              "legend": str}]}      // choice only, e.g. "P=Present, A=Absent"

Rules: use "serial" for a printed running-number column; use "choice" with a
domain whenever the column holds codes from a small set (read any legend
printed on the form); prefer short realistic labels. Output ONLY the JSON.
"""


@app.post("/api/design_from_sample")
async def api_design_from_sample(f: UploadFile = File(...),
                                 provider: str = Form("gemini-flash")):
    from core.vlm import ask
    from core.extract import load_input
    raw = await f.read()
    suffix = Path(f.filename or "s.jpg").suffix.lower() or ".jpg"
    tmp = Path(tempfile.mkdtemp(prefix="pr_ds_")) / f"sample{suffix}"
    tmp.write_bytes(raw)
    img = load_input(tmp)
    try:
        out = ask(img, DESIGN_PROMPT, provider, max_tokens=1500)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"model call failed: {e}")
    txt = out.strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        txt = txt[txt.find("{"):]
    try:
        spec = json.loads(txt[txt.find("{"):txt.rfind("}") + 1])
        T.from_spec(spec)                       # validate; raises ValueError
    except ValueError as e:
        return JSONResponse({"spec": spec, "warning": str(e)})
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"could not parse a template from the "
                                 f"model's answer: {e}")
    return {"spec": spec}


@app.get("/api/providers")
def api_providers():
    from core.vlm import PROVIDERS
    return {"default": DEFAULT_PROVIDER, "providers": list(PROVIDERS)}
