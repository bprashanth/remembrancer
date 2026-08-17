#!/usr/bin/env python3
"""Template-constrained extraction — the detector.

We know the form (printed QR/ID -> template descriptor), so extraction is a
sequence of SMALL, bounded reads instead of one long free transcription:

  1. read form ID   — QR decode (multi-scale), no pixel fingerprinting ever
  2. align          — ORB homography photo -> blank render (identity fallback)
  3. ink map        — per-cell "is there handwriting here?" from pixels,
                      independent of the model (blank-vs-filled guardrail)
  4. band reads     — one model call per table row, headers + per-column value
                      domains in the prompt, one CSV line out, length-capped
  5. header reads   — one call per header field crop
  6. assemble       — grid shaped exactly like the template; per-cell flags

Per-cell flags (the guardrail currency):
  ok            — value read, domain-valid, consistent with ink map
  domain        — value outside the column's closed domain
  no_ink        — model produced a value where the ink map sees nothing
                  (dropped to blank; counts toward hallucination pressure)
  unread_ink    — ink present but model returned empty (a probable miss)
  serial_mismatch — the row's printed serial read back wrong (row identity
                  suspect: the model may have drifted a row)
  shape         — band returned wrong number of CSV fields

Form-level verdict from the flags: detected / review / reject.
"""
from __future__ import annotations

import csv
import io
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image

from .template import Template, load as load_template, empty_grid
from .score import norm

MAX_DIM = 2200
ROOT = Path(__file__).parent.parent


# ── image io ──────────────────────────────────────────────────────
def load_input(path: Path, page=0) -> Image.Image:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        doc = fitz.open(str(path))
        pg = doc[page]
        s = min(MAX_DIM / max(pg.rect.width, pg.rect.height), 4.0)
        pm = pg.get_pixmap(matrix=fitz.Matrix(s, s))
        im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
        doc.close()
        return im
    im = Image.open(path).convert("RGB")
    if max(im.size) > MAX_DIM:
        k = MAX_DIM / max(im.size)
        im = im.resize((int(im.width * k), int(im.height * k)))
    return im


def render_blank(t: Template, max_dim=MAX_DIM):
    pdf = ROOT / "data" / "templates" / t.form_id / "blank.pdf"
    doc = fitz.open(str(pdf))
    pg = doc[0]
    s = min(max_dim / max(pg.rect.width, pg.rect.height), 4.0)
    pm = pg.get_pixmap(matrix=fitz.Matrix(s, s))
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    doc.close()
    return im, s


# ── form id ───────────────────────────────────────────────────────
_ID_RE = re.compile(r"\bPR[A-Z2-9]{4}\b")


def read_form_id(img: Image.Image):
    """QR decode at several scales/rotations. Returns (form_id|None, how)."""
    det = cv2.QRCodeDetector()
    arr0 = np.array(img.convert("RGB"))
    for rot in (None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180,
                cv2.ROTATE_90_COUNTERCLOCKWISE):
        arr = cv2.rotate(arr0, rot) if rot is not None else arr0
        for scale in (1.0, 1.6, 2.4):
            a = cv2.resize(arr, None, fx=scale, fy=scale) if scale != 1.0 else arr
            try:
                val, pts, _ = det.detectAndDecode(a)
            except cv2.error:
                continue
            if val and _ID_RE.fullmatch(val.strip()):
                return val.strip(), f"qr(rot={rot},x{scale})"
    return None, "qr-failed"


def read_form_id_fallback(img: Image.Image, provider) -> str | None:
    """Model reads the printed ID (top-right corner crop, then whole page)."""
    from .vlm import ask
    crops = [img.crop((int(img.width * 0.6), 0, img.width, int(img.height * 0.25))),
             img]
    for c in crops:
        try:
            out = ask(c, "Find the printed form code that starts with PR "
                         "(format: PR followed by 4 characters). "
                         "Reply with the code only.", provider, max_tokens=16)
        except RuntimeError:
            continue
        m = _ID_RE.search(out.upper().replace(" ", ""))
        if m:
            return m.group(0)
    return None


# ── alignment ─────────────────────────────────────────────────────
def align(photo: Image.Image, blank: Image.Image):
    """Warp photo onto the blank template. ORB + RANSAC homography for the
    projective part, then a thin-plate spline on the spatially-bucketed
    inlier correspondences to absorb page bow (a phone photo of a curled
    register page is NOT projective — a homography alone leaves rows tens of
    px off near the bottom). Returns (aligned, ok, inliers)."""
    a = cv2.cvtColor(np.array(photo), cv2.COLOR_RGB2GRAY)
    b = cv2.cvtColor(np.array(blank), cv2.COLOR_RGB2GRAY)
    orb = cv2.ORB_create(6000)
    ka, da = orb.detectAndCompute(a, None)
    kb, db = orb.detectAndCompute(b, None)
    if da is None or db is None or len(ka) < 30:
        return photo.resize(blank.size), False, 0
    m = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    if len(m) < 25:
        return photo.resize(blank.size), False, 0
    m = sorted(m, key=lambda x: x.distance)[:1200]
    src = np.float32([ka[x.queryIdx].pt for x in m]).reshape(-1, 1, 2)
    dst = np.float32([kb[x.trainIdx].pt for x in m]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 6.0)
    if H is None or mask.sum() < 20:
        return photo.resize(blank.size), False, int(mask.sum() if mask is not None else 0)
    inl = int(mask.sum())
    photo_arr = np.array(photo)
    warped = cv2.warpPerspective(photo_arr, H, blank.size,
                                 borderValue=(255, 255, 255))

    # TPS refinement on inliers, mapped through H into blank space
    src_in = src[mask.ravel() == 1].reshape(-1, 2)
    dst_in = dst[mask.ravel() == 1].reshape(-1, 2)
    src_h = cv2.perspectiveTransform(src_in.reshape(-1, 1, 2), H).reshape(-1, 2)
    # residual after homography — TPS models what's left (the bow)
    # spatial bucketing: at most one correspondence per 90px cell, best first
    order = np.argsort(np.linalg.norm(src_h - dst_in, axis=1))
    seen, keep = set(), []
    for i in order:
        bx, by = int(dst_in[i, 0] // 90), int(dst_in[i, 1] // 90)
        if (bx, by) in seen:
            continue
        seen.add((bx, by))
        keep.append(i)
    keep = np.array(keep)
    if len(keep) >= 16:
        s = src_h[keep].astype(np.float32)
        d = dst_in[keep].astype(np.float32)
        # sanity: drop pairs whose residual is implausibly large
        res = np.linalg.norm(s - d, axis=1)
        good = res < np.median(res) + 3 * (np.percentile(res, 75)
                                           - np.percentile(res, 25) + 4)
        if good.sum() >= 16:
            s, d = s[good], d[good]
            warped = _tps_backwarp(warped, d, s - d)
    return Image.fromarray(warped), True, inl


def _tps_backwarp(img_arr, ctrl, disp, lam=8.0, lattice=28):
    """Backward-warp img by a thin-plate-spline displacement field.

    ctrl: (N,2) control points in OUTPUT (blank/template) space.
    disp: (N,2) displacement = (source_pos - output_pos) at each control point.
    For every output pixel we need where to SAMPLE the input:
    identity + TPS(disp). Field is evaluated on a coarse lattice and resized —
    TPS is smooth, the approximation is sub-pixel."""
    Hh, Ww = img_arr.shape[:2]
    N = len(ctrl)
    # TPS kernel matrix with regularization lam (px^2 units)
    d2 = ((ctrl[:, None, :] - ctrl[None, :, :]) ** 2).sum(-1)
    K = d2 * np.log(np.maximum(d2, 1e-9)) * 0.5
    K[np.arange(N), np.arange(N)] += lam
    P = np.concatenate([np.ones((N, 1)), ctrl], axis=1)
    A = np.zeros((N + 3, N + 3))
    A[:N, :N] = K
    A[:N, N:] = P
    A[N:, :N] = P.T
    rhs = np.zeros((N + 3, 2))
    rhs[:N] = disp
    try:
        Wc = np.linalg.solve(A, rhs)
    except np.linalg.LinAlgError:
        return img_arr
    gx = np.linspace(0, Ww - 1, lattice, dtype=np.float64)
    gy = np.linspace(0, Hh - 1, int(lattice * Hh / Ww), dtype=np.float64)
    GX, GY = np.meshgrid(gx, gy)
    pts = np.stack([GX.ravel(), GY.ravel()], axis=1)
    dd2 = ((pts[:, None, :] - ctrl[None, :, :]) ** 2).sum(-1)
    U = dd2 * np.log(np.maximum(dd2, 1e-9)) * 0.5
    phi = np.concatenate([U, np.ones((len(pts), 1)), pts], axis=1)
    delta = phi @ Wc                                # (M,2) displacements
    fx = (pts[:, 0] + delta[:, 0]).reshape(GY.shape).astype(np.float32)
    fy = (pts[:, 1] + delta[:, 1]).reshape(GY.shape).astype(np.float32)
    map_x = cv2.resize(fx, (Ww, Hh), interpolation=cv2.INTER_LINEAR)
    map_y = cv2.resize(fy, (Ww, Hh), interpolation=cv2.INTER_LINEAR)
    return cv2.remap(img_arr, map_x, map_y, cv2.INTER_LINEAR,
                     borderValue=(255, 255, 255))


# ── fiducial detection (primary geometry path) ────────────────────
def detect_fiducials(aligned: Image.Image, t: Template, scale):
    """Find the printed OMR-style marks. Each is an isolated dark blob in an
    otherwise clean margin, so detection is a windowed centroid — no line
    fitting, no warp models. Returns ({side: [(x,y)|None, ...]}, found_frac).
    """
    fid = t.geometry.get("fiducials")
    if not fid:
        return None, 0.0
    g = np.asarray(aligned.convert("L"))
    dark = (g < 150).astype(np.uint8)
    Hh, Ww = dark.shape
    row_h = (t.geometry["table"]["row_y"][1]
             - t.geometry["table"]["row_y"][0]) * scale
    win_y = int(row_h * 0.85)
    win_x = int(row_h * 1.2)
    exp_area = (7 * 4.6) * scale * scale * 0.3       # generous lower bound

    def strip_blobs(x0, x1, y0, y1):
        """All plausible mark blobs in a margin strip -> (x, y, w, h)."""
        x0, x1 = max(0, int(x0)), min(Ww, int(x1))
        y0, y1 = max(0, int(y0)), min(Hh, int(y1))
        w = dark[y0:y1, x0:x1]
        if w.size == 0:
            return []
        n, lab, stats, cent = cv2.connectedComponentsWithStats(w)
        got = []
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            bw, bh = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            if area < max(6, exp_area * 0.25) or area > exp_area * 15:
                continue
            if max(bw, bh) > 30 * scale:              # a rule or scribble
                continue
            got.append((x0 + cent[i][0], y0 + cent[i][1], bw, bh))
        return got

    def hough_shift(det, tpl, axis, tol):
        """Best 1-D shift matching detected marks to the template sequence —
        resolves mark IDENTITY globally, immune to the off-by-one failures
        of per-mark windowed search."""
        if not det:
            return None, 0
        dv = np.array([p[axis] for p in det])
        tv = np.array([p[axis] for p in tpl])
        cands = (dv[:, None] - tv[None, :]).ravel()
        best_s, best_n = None, 0
        for scand in cands:
            n = 0
            for team in tv:
                if np.min(np.abs(dv - (team + scand))) < tol:
                    n += 1
            if n > best_n:
                best_n, best_s = n, scand
        return best_s, best_n

    out = {}
    found = total = 0
    row_pitch = row_h

    def count_matches(blobs, tpl, axis, shift, tol):
        return sum(1 for p in tpl
                   if any(abs(b[axis] - (p[axis] + shift)) < tol
                          for b in blobs))

    def assign_seq(blobs, tpl, axis, shift, tol):
        """Sequential tracking from a locked start: a uniform shift cannot
        follow residual scale/bow — walk mark-to-mark, adapting pitch."""
        other = 1 - axis
        offs = []
        for p in tpl:
            cand = [b for b in blobs if abs(b[axis] - (p[axis] + shift)) < tol]
            if cand:
                b = min(cand, key=lambda b: abs(b[axis] - (p[axis] + shift)))
                offs.append(b[other] - p[other])
        moff = float(np.median(offs)) if offs else 0.0
        res, nfound = [], 0
        scale_est, prev = 1.0, None
        for k, p in enumerate(tpl):
            if k == 0:
                pred = p[axis] + shift
            else:
                pred = prev + (tpl[k][axis] - tpl[k - 1][axis]) * scale_est
            cand = [b for b in blobs
                    if abs(b[axis] - pred) < tol
                    and abs(b[other] - (p[other] + moff)) < 3 * tol]
            if cand:
                b = min(cand, key=lambda b: abs(b[axis] - pred))
                res.append((float(b[0]), float(b[1])))
                nfound += 1
                if k > 0:
                    g_tpl = tpl[k][axis] - tpl[k - 1][axis]
                    if g_tpl > 4:
                        obs = (b[axis] - prev) / g_tpl
                        if 0.7 < obs < 1.4:
                            scale_est = 0.7 * scale_est + 0.3 * obs
                prev = b[axis]
            else:
                q = [0.0, 0.0]
                q[axis] = pred
                q[other] = p[other] + moff
                res.append((q[0], q[1]))
                prev = pred
        return res, nfound

    # ── row marks: LEFT and RIGHT resolved JOINTLY. A page-border artifact
    # can fake one margin's anchor bar; the true shift must explain blobs on
    # BOTH margins, so score every candidate shift across both sides.
    sides = {}
    for side in ("left", "right"):
        tpl = [(px * scale, py * scale) for px, py in fid[side]]
        txs = [p[0] for p in tpl]
        tys = [p[1] for p in tpl]
        blobs = strip_blobs(min(txs) - 40, max(txs) + 40,
                            min(tys) - 3.5 * row_pitch,
                            max(tys) + 3.5 * row_pitch)
        anchor = None
        if len(blobs) >= 3:
            hs = sorted(b[3] for b in blobs)
            med_h = hs[len(hs) // 2]
            tall = [b for b in blobs if b[3] > med_h * 1.9]
            if len(tall) == 1:
                anchor = tall[0][1] - tys[0]
        sides[side] = (tpl, blobs, anchor)
    tol = row_pitch * 0.33
    cands = []
    for tpl, blobs, anchor in sides.values():
        if anchor is not None:
            cands.append(anchor)
        hs, hn = hough_shift(blobs, tpl, 1, tol)
        if hs is not None and hn >= max(3, len(tpl) // 3):
            cands.append(hs)
    best_shift, best_score = None, -1
    for s in cands:
        score = sum(count_matches(blobs, tpl, 1, s, tol)
                    for tpl, blobs, _ in sides.values())
        if score > best_score:
            best_shift, best_score = s, score
    for side, (tpl, blobs, anchor) in sides.items():
        total += len(tpl)
        if best_shift is None:
            out[side] = [None] * len(tpl)
            continue
        shift = best_shift
        # a side's own anchor may refine the start if it agrees globally
        if anchor is not None and abs(anchor - best_shift) < 0.5 * row_pitch:
            shift = anchor
        res, nf = assign_seq(blobs, tpl, 1, shift, tol)
        found += nf
        out[side] = res

    # ── column ticks, along x
    tpl = [(px * scale, py * scale) for px, py in fid["col"]]
    txs = [p[0] for p in tpl]
    tys = [p[1] for p in tpl]
    gaps = np.diff(sorted(txs))
    ctol = max(10.0, float(gaps.min()) * 0.38) if len(gaps) else 20.0
    blobs = strip_blobs(min(txs) - 40, max(txs) + 40,
                        min(tys) - 60, max(tys) + 60)
    total += len(tpl)
    shift, nmatch = hough_shift(blobs, tpl, 0, ctol)
    if shift is None or nmatch < max(3, len(tpl) // 3):
        out["col"] = [None] * len(tpl)
    else:
        res, nf = assign_seq(blobs, tpl, 0, shift, ctol)
        found += nf
        out["col"] = res
    return out, found / max(1, total)


def fiducial_geometry(fids, t: Template, scale):
    """Turn detected marks into per-row band quads and per-cell boxes.

    Row band r spans left/right marks r+1..r+2 in the mark arrays (index 0 is
    the table top rule, 1 the header/data boundary). Missing marks are
    interpolated from their neighbours (marks are at uniform row pitch)."""
    L, R = fids["left"], fids["right"]

    def fill(seq, tpl_pts):
        """Interpolate None entries using detected offsets of neighbours."""
        n = len(seq)
        idx = [i for i, s in enumerate(seq) if s is not None]
        if not idx:
            return None
        out = []
        for i in range(n):
            if seq[i] is not None:
                out.append(seq[i])
                continue
            tx, ty = tpl_pts[i][0] * scale, tpl_pts[i][1] * scale
            j = min(idx, key=lambda k: abs(k - i))
            ox = seq[j][0] - tpl_pts[j][0] * scale
            oy = seq[j][1] - tpl_pts[j][1] * scale
            out.append((tx + ox, ty + oy))
        return out

    tplL = t.geometry["fiducials"]["left"]
    tplR = t.geometry["fiducials"]["right"]
    L, R = fill(L, tplL), fill(R, tplR)
    if L is None or R is None:
        return None
    return {"left": L, "right": R}


def fiducial_band(aligned: Image.Image, geom, t: Template, scale, r, pad=6):
    """Perspective-rectify one data row using its four surrounding marks.
    Returns (band_img, col_x_edges_in_band)."""
    L, R = geom["left"], geom["right"]
    i0, i1 = r + 1, r + 2                      # skip table-top mark pair
    xs = t.geometry["table"]["x"]
    row_h = (t.geometry["table"]["row_y"][1]
             - t.geometry["table"]["row_y"][0]) * scale
    W = (xs[-1] - xs[0]) * scale
    # source quad: marks sit slightly outside the table; extend to mark x
    src = np.float32([L[i0], R[i0], R[i1], L[i1]])
    mark_dx = (xs[0] - t.geometry["fiducials"]["left"][0][0]) * scale
    out_w = int(W + 2 * mark_dx)
    dst = np.float32([[0, pad], [out_w, pad],
                      [out_w, pad + row_h], [0, pad + row_h]])
    M = cv2.getPerspectiveTransform(src, dst)
    band = cv2.warpPerspective(np.asarray(aligned.convert("RGB")), M,
                               (out_w, int(row_h + 2 * pad)),
                               borderValue=(255, 255, 255))
    col_x = [mark_dx + (x - xs[0]) * scale for x in xs]

    # The quad is exact at the MARKS (page margins); across a wide table the
    # rules still bow a few px mid-span, bleeding the neighbouring row into
    # the band. Straighten: find the band's own top/bottom rule per x-chunk
    # (tiny ±10px window — unambiguous) and remap vertically.
    g = cv2.cvtColor(band, cv2.COLOR_RGB2GRAY)
    Hb, Wb = g.shape
    dark = 255.0 - g.astype(np.float32)
    exp_t, exp_b = float(pad), float(pad + row_h)
    step, win = 40, 14
    chunks = list(range(0, Wb - step, step))
    profs = [dark[:, x0c:x0c + step].mean(axis=1) for x0c in chunks]
    med = float(np.median(dark))

    def trace(start_y):
        """Follow a rule with a continuity constraint, both directions,
        so mid-span sag larger than the window still gets tracked."""
        def one_dir(rng):
            ys, prev = {}, start_y
            for i in rng:
                prof = profs[i]
                lo = int(max(0, prev - win))
                hi = int(min(Hb, prev + win + 1))
                seg = prof[lo:hi]
                if seg.size and float(seg.max()) > med + 18:
                    prev = lo + int(np.argmax(seg))
                ys[i] = float(prev)
            return ys
        f = one_dir(range(len(chunks)))
        b = one_dir(range(len(chunks) - 1, -1, -1))
        return [(f[i] + b[i]) / 2 for i in range(len(chunks))]

    xs_c = [x0c + step // 2 for x0c in chunks]
    yt_c = trace(exp_t)
    yb_c = trace(exp_b)
    if len(xs_c) >= 3:
        xr = np.arange(Wb)
        ytop = np.interp(xr, xs_c, yt_c)
        ybot = np.interp(xr, xs_c, yb_c)
        h_out = int(row_h + 2 * pad)
        yy = np.arange(h_out, dtype=np.float32)[:, None]
        frac = (yy - pad) / row_h
        map_y = (ytop[None, :] + frac * (ybot - ytop)[None, :]).astype(np.float32)
        map_x = np.tile(xr.astype(np.float32), (h_out, 1))
        band = cv2.remap(band, map_x, map_y, cv2.INTER_LINEAR,
                         borderValue=(255, 255, 255))

    # snap interior column edges: the row marks fix y exactly, but vertical
    # rules can drift a few px in x; find each rule's actual position in
    # this band so cell crops and insets track it
    g2 = cv2.cvtColor(band, cv2.COLOR_RGB2GRAY)
    interior = 255.0 - g2[int(pad) + 4:int(pad + row_h) - 4, :].astype(np.float32)
    prof = interior.mean(axis=0)
    med = float(np.median(prof))
    snapped_x = [col_x[0]]
    for cxp in col_x[1:-1]:
        lo = int(max(0, cxp - 12))
        hi = int(min(len(prof) - 1, cxp + 13))
        seg = prof[lo:hi]
        if seg.size and float(seg.max()) > med + 20:
            snapped_x.append(float(lo + int(np.argmax(seg))))
        else:
            snapped_x.append(cxp)
    snapped_x.append(col_x[-1])
    return Image.fromarray(band), snapped_x


# ── grid-intersection rectification ───────────────────────────────
def _line_response(gray_dark):
    """Horizontal / vertical line response maps via morphological opening."""
    hker = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 1))
    vker = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 31))
    h = cv2.morphologyEx(gray_dark, cv2.MORPH_OPEN, hker)
    v = cv2.morphologyEx(gray_dark, cv2.MORPH_OPEN, vker)
    cross = cv2.GaussianBlur(np.minimum(h, v), (7, 7), 0)
    return cross


def _grid_points(t, scale):
    """All expected grid intersections (template space, pixels)."""
    geo = t.geometry
    xs = [x * scale for x in geo["table"]["x"]]
    ys = [geo["table"]["header_y"][0] * scale] + \
         [y * scale for y in geo["table"]["row_y"]]
    return xs, ys


def _fit_rule(resp, expected, lo, hi, win, horizontal, thresh=18):
    """Fit one printed rule as a straight line by following its ridge.

    resp: line-response map (hresp for horizontal rules, vresp for vertical).
    For a horizontal rule: y ≈ a + b·x over x in [lo, hi], searching y within
    ±win of `expected`. Returns (a, b, support_fraction).
    """
    Hh, Ww = resp.shape
    xs_s, ys_s = [], []
    for s in range(int(lo), int(hi), 18):
        if horizontal:
            y0, y1 = max(0, int(expected - win)), min(Hh, int(expected + win))
            col = resp[y0:y1, max(0, s - 6):s + 7].mean(axis=1)
        else:
            x0, x1 = max(0, int(expected - win)), min(Ww, int(expected + win))
            col = resp[max(0, s - 6):s + 7, x0:x1].mean(axis=0)
        if col.size < 5:
            continue
        # NEAREST strong peak, not the strongest: a neighbouring bolder rule
        # inside the window must not hijack the fit
        strong = np.where(col >= thresh)[0]
        if strong.size == 0:
            continue
        center = col.size / 2
        k = int(strong[np.argmin(np.abs(strong - center))])
        xs_s.append(s)
        ys_s.append((y0 if horizontal else x0) + k)
    n_expected = max(1, (int(hi) - int(lo)) // 18)
    if len(xs_s) < max(4, n_expected * 0.3):
        return None
    A = np.stack([np.ones(len(xs_s)), np.array(xs_s, float)], axis=1)
    b_vec = np.array(ys_s, float)
    coef, *_ = np.linalg.lstsq(A, b_vec, rcond=None)
    # one robust re-fit
    res = np.abs(A @ coef - b_vec)
    keep = res < max(4.0, np.percentile(res, 80))
    if keep.sum() >= 4:
        coef, *_ = np.linalg.lstsq(A[keep], b_vec[keep], rcond=None)
    return coef[0], coef[1], len(xs_s) / n_expected


def _isect(hrule, vrule):
    """Intersection of y = ah + bh·x and x = av + bv·y."""
    ah, bh, _ = hrule
    av, bv, _ = vrule
    x = (av + bv * ah) / (1 - bv * bh)
    y = ah + bh * x
    return x, y


def corner_pin(aligned: Image.Image, t: Template, scale):
    """Fallback perspective fix (used only when fiducials are absent): pin
    the table's four OUTER RULES — each fitted as a line along its whole
    length, corners taken as line intersections. Residual bow between pinned
    corners is handled downstream by per-rule snapping.
    Returns (aligned_img, corner_ok)."""
    gray = 255 - np.asarray(aligned.convert("L"), dtype=np.uint8)
    hker = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 1))
    vker = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 31))
    hresp = cv2.morphologyEx(gray, cv2.MORPH_OPEN, hker).astype(np.float32)
    vresp = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vker).astype(np.float32)
    xs, ys = _grid_points(t, scale)
    row_h = ys[2] - ys[1]
    win = max(30, int(row_h * 0.7))
    top = _fit_rule(hresp, ys[0], xs[0], xs[-1], win, True)
    bot = _fit_rule(hresp, ys[-1], xs[0], xs[-1], win, True)
    lef = _fit_rule(vresp, xs[0], ys[0], ys[-1], win, False)
    rig = _fit_rule(vresp, xs[-1], ys[0], ys[-1], win, False)
    if any(r is None for r in (top, bot, lef, rig)):
        return aligned, False
    det = [_isect(top, lef), _isect(top, rig), _isect(bot, rig),
           _isect(bot, lef)]
    corners_tpl = [(xs[0], ys[0]), (xs[-1], ys[0]),
                   (xs[-1], ys[-1]), (xs[0], ys[-1])]
    # sanity: detected quad must be within a plausible distance of expected
    d = np.linalg.norm(np.float32(det) - np.float32(corners_tpl), axis=1)
    if d.max() > row_h * 2.0:
        return aligned, False
    H = cv2.getPerspectiveTransform(np.float32(det), np.float32(corners_tpl))
    rect = cv2.warpPerspective(np.asarray(aligned.convert("RGB")), H,
                               aligned.size, borderValue=(255, 255, 255))
    return Image.fromarray(rect), True


# ── grid-line snapping ────────────────────────────────────────────
def snap_grid(aligned: Image.Image, t: Template, scale):
    """Refine the template grid against the actual (globally aligned) photo.

    A phone photo has page bow that a single homography cannot remove, so the
    printed rules end up a few px to a few tens of px away from where the
    template says. Because we KNOW where every rule should be, we can search a
    small window around each expected line for the strongest dark-line
    response and snap to it — deterministic, per-line, no CV tuning treadmill.

    Returns (xs, ys, integrity) where xs/ys are snapped pixel edges and
    integrity is the fraction of grid lines confidently found (a guardrail:
    low integrity == photo too warped/cropped/occluded to trust geometry).

    ys[r] is returned per-row as an ARRAY over x (the bow makes a line's y
    vary along its length): ys[r][k] is the y of rule r at x-sample k.
    """
    a = np.asarray(aligned.convert("L")).astype(np.float32)
    Hh, Ww = a.shape
    geo = t.geometry
    xs0 = [x * scale for x in geo["table"]["x"]]
    ys0 = [y * scale for y in geo["table"]["row_y"]]
    row_h = (ys0[1] - ys0[0])
    dark = 255.0 - a                               # line = high value

    # Stage 0: small residual global offset (corners are already pinned by
    # rectify(), so this is a safety net, deliberately sub-row-period).
    x0i, x1i = int(xs0[0]), int(xs0[-1])
    y0i, y1i = int(ys0[0]), int(ys0[-1])
    prof_y = dark[:, max(0, x0i):x1i].mean(axis=1)
    lim = max(4, int(row_h * 0.30))
    best, dy_g = -1.0, 0
    for dy in range(-lim, lim + 1):
        idx = [int(y) + dy for y in ys0]
        if idx[0] < 1 or idx[-1] >= Hh - 1:
            continue
        s = sum(prof_y[i - 1:i + 2].max() for i in idx)
        if s > best:
            best, dy_g = s, dy
    prof_x = dark[max(0, y0i + dy_g):y1i + dy_g, :].mean(axis=0)
    colw = min(np.diff(xs0)) if len(xs0) > 1 else 60
    limx = int(min(colw * 0.9, 50))
    best, dx_g = -1.0, 0
    for dx in range(-limx, limx + 1):
        idx = [int(x) + dx for x in xs0]
        if idx[0] < 1 or idx[-1] >= Ww - 1:
            continue
        s = sum(prof_x[i - 1:i + 2].max() for i in idx)
        if s > best:
            best, dx_g = s, dx
    xs0 = [x + dx_g for x in xs0]
    ys0 = [y + dy_g for y in ys0]

    win = int(min(row_h * 0.42, 26))

    # sample columns across the table width for piecewise horizontal lines
    NSAMP = 9
    xsamp = np.linspace(xs0[0] + 8, xs0[-1] - 8, NSAMP).astype(int)
    seg_w = max(8, int((xs0[-1] - xs0[0]) / (NSAMP * 2)))

    found = 0
    ys = []
    for y0 in ys0:
        yy = int(y0)
        row_pts, row_ok = [], 0
        for xc in xsamp:
            x0s, x1s = max(0, xc - seg_w), min(Ww, xc + seg_w)
            lo, hi = max(1, yy - win), min(Hh - 1, yy + win)
            if hi <= lo:
                row_pts.append(y0)
                continue
            # mean darkness of a 3px-tall band at each candidate y
            band = dark[lo - 1:hi + 2, x0s:x1s]
            prof = (band[:-2] + band[1:-1] + band[2:]).mean(axis=1)
            k = int(np.argmax(prof))
            score = prof[k]
            base = np.median(prof)
            if score > base + 25:                  # a real line, not noise
                row_pts.append(lo + k)
                row_ok += 1
            else:
                row_pts.append(y0)
        # smooth: fill unfound samples from neighbours
        ys.append(np.array(row_pts, dtype=np.float32))
        if row_ok >= NSAMP // 2 + 1:
            found += 1

    xs = []
    ytop, ybot = int(ys0[0]), int(ys0[-1])
    for x0 in xs0:
        xx = int(x0)
        lo, hi = max(1, xx - win), min(Ww - 1, xx + win)
        band = dark[ytop:ybot, lo - 1:hi + 2]
        prof = (band[:, :-2] + band[:, 1:-1] + band[:, 2:]).mean(axis=0)
        k = int(np.argmax(prof))
        if prof[k] > np.median(prof) + 25:
            xs.append(float(lo + k))
            found += 1
        else:
            xs.append(float(x0))
    integrity = found / (len(ys0) + len(xs0))
    return xs, ys, xsamp, integrity, (dx_g, dy_g)


def band_box(xs, ys, xsamp, r):
    """Bounding box of row r between snapped (bowed) rules."""
    y0 = float(np.min(ys[r])); y1 = float(np.max(ys[r + 1]))
    return xs[0], y0, xs[-1], y1


def cell_box(xs, ys, xsamp, r, c):
    """Axis-aligned box for cell (r,c) using local line positions at the
    cell's x-position."""
    xc = (xs[c] + xs[c + 1]) / 2
    k = int(np.clip(np.searchsorted(xsamp, xc), 0, len(xsamp) - 1))
    return xs[c], float(ys[r][k]), xs[c + 1], float(ys[r + 1][k])


# ── ink map ───────────────────────────────────────────────────────
def stroke_mask(arr_gray: np.ndarray, scale: float = 2.6,
                printed_gray: np.ndarray = None) -> np.ndarray:
    """Handwriting-stroke mask for a band image.

    We KNOW the printed layer — `printed_gray` is the same band cropped from
    the blank template render. Everything printed (rules, serials, labels)
    is masked out with dilation; what remains dark & locally-contrasted and
    bigger than speckle is handwriting. No rule-shape heuristics: measured,
    they either let sloped rules through or ate genuine '1's and dashes."""
    a = arr_gray.astype(np.int16)
    bg = cv2.medianBlur(arr_gray, 21).astype(np.int16)
    # contrast-only: an absolute darkness cut silently erased pencil, whose
    # strokes sit at gray 195-235 — but local contrast separates cleanly
    # (measured: filled-cell p99.5 ≈ 22-63, empty-cell ≈ 1)
    raw = (bg - a) > 26
    if printed_gray is not None:
        pg = printed_gray
        if pg.shape != arr_gray.shape:
            pg = cv2.resize(pg, (arr_gray.shape[1], arr_gray.shape[0]))
        printed = cv2.dilate((pg < 200).astype(np.uint8),
                             np.ones((13, 9), np.uint8))
        raw = raw & (printed == 0)
    raw = raw.astype(np.uint8)
    if not raw.any():
        return raw.astype(bool)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(raw)
    diff = (bg - a).astype(np.float64)
    sums = np.bincount(lab.ravel(), weights=np.where(raw.ravel() > 0,
                                                     diff.ravel(), 0),
                       minlength=n)
    keep = np.zeros(n, dtype=bool)
    min_area = max(8, int(4 * scale))
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        w, h = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        if area < min_area or max(w, h) < int(2.2 * scale):
            continue                                  # speckle
        if sums[i] / max(1, area) < 34:
            continue                                  # weak smudge/shadow edge
        keep[i] = True
    return keep[lab]


def blank_band(blank: Image.Image, t: Template, scale, r, pad=6):
    """The blank template's band r in the same frame as fiducial_band."""
    xs = t.geometry["table"]["x"]
    row_y = t.geometry["table"]["row_y"]
    mark_dx = (xs[0] - t.geometry["fiducials"]["left"][0][0]) * scale \
        if t.geometry.get("fiducials") else 20 * scale
    x0 = xs[0] * scale - mark_dx
    x1 = xs[-1] * scale + mark_dx
    y0 = row_y[r] * scale - pad
    y1 = row_y[r + 1] * scale + pad
    return np.asarray(blank.convert("L").crop(
        (int(x0), int(y0), int(x1), int(y1))))


def ink_map(aligned: Image.Image, blank: Image.Image, t: Template, scale,
            snapped=None, shift=(0, 0)):
    """Fraction of handwriting-ink pixels per (row, col) cell and per header
    field, computed by masking out the printed layer. Uses the snapped grid
    when available. Also masks a margin inside each cell so residual rule
    misalignment does not read as ink."""
    a8 = np.asarray(aligned.convert("L"))
    a = a8.astype(np.int16)
    b = np.asarray(blank.convert("L")).astype(np.int16)
    printed = (b < 200).astype(np.uint8)
    printed = cv2.dilate(printed, np.ones((5, 5), np.uint8))
    # dark AND locally contrasted (see band detector for rationale)
    bg = cv2.medianBlur(a8, 21).astype(np.int16)
    ink = (a < 150) & ((bg - a) > 30) & (printed == 0)
    geo = t.geometry
    out = {}
    for r in range(t.rows):
        for c in range(len(t.columns)):
            if snapped:
                xs, ys, xsamp = snapped
                x0, y0, x1, y1 = cell_box(xs, ys, xsamp, r, c)
            else:
                x0 = geo["table"]["x"][c] * scale
                x1 = geo["table"]["x"][c + 1] * scale
                y0 = geo["table"]["row_y"][r] * scale
                y1 = geo["table"]["row_y"][r + 1] * scale
            x0, y0, x1, y1 = int(x0) + 4, int(y0) + 4, int(x1) - 4, int(y1) - 4
            cell = ink[y0:y1, x0:x1]
            out[(r, c)] = float(cell.mean()) if cell.size else 0.0
    hdr = {}
    dx, dy = shift
    for key, bb in geo.get("header_fields", {}).items():
        x0, y0, x1, y1 = [int(v * scale) for v in bb]
        cell = ink[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
        hdr[key] = float(cell.mean()) if cell.size else 0.0
    return out, hdr


def extract_band(aligned: Image.Image, xs, ys, xsamp, r, pad=6):
    """Cut row r as a dewarped horizontal strip: per-x vertical shift so the
    row's top rule becomes straight. Kills page bow inside the band."""
    arr = np.asarray(aligned.convert("RGB"))
    Hh, Ww = arr.shape[:2]
    x0, x1 = int(max(0, xs[0] - pad)), int(min(Ww, xs[-1] + pad))
    xr = np.arange(x0, x1)
    ytop = np.interp(xr, xsamp, ys[r])
    ybot = np.interp(xr, xsamp, ys[r + 1])
    h = int(np.max(ybot - ytop)) + 2 * pad
    map_x = np.tile(xr.astype(np.float32), (h, 1))
    map_y = (ytop - pad)[None, :] + np.arange(h, dtype=np.float32)[:, None]
    map_y = np.clip(map_y, 0, Hh - 1).astype(np.float32)
    band = cv2.remap(arr, map_x, map_y, cv2.INTER_LINEAR,
                     borderValue=(255, 255, 255))
    return Image.fromarray(band)


# Calibrated on the synthetic corpus (eval/calibrate_ink.py):
# at 0.004, forms with fiducial integrity >= GEOM_TRUST have cell-level
# ink FN ~1% / FP ~1%; below GEOM_TRUST the ink map is untrustworthy and the
# form must be refused BEFORE any model call.
INK_THRESHOLD = 0.004
GEOM_TRUST = 0.95


# ── prompts ───────────────────────────────────────────────────────
def _domain_line(i, c):
    if c.type == "serial":
        return f"{i}. {c.label}: printed serial number"
    if c.type == "int":
        rng = (f" between {int(c.min)} and {int(c.max)}"
               if c.min is not None and c.max is not None else "")
        return f"{i}. {c.label}: whole number{rng}, or empty"
    if c.type == "dec":
        rng = (f" between {c.min:g} and {c.max:g}"
               if c.min is not None and c.max is not None else "")
        return f"{i}. {c.label}: decimal number{rng}, or empty"
    if c.type == "date":
        return f"{i}. {c.label}: date like 12/04/25, or empty"
    if c.type in ("yn", "choice"):
        dom = " or ".join(c.domain)
        return f"{i}. {c.label}: exactly one of {dom}, or empty"
    if c.type == "name":
        return f"{i}. {c.label}: a person's name, or empty"
    return f"{i}. {c.label}: short handwritten text, or empty"


def band_prompt(t: Template, serial_val=None):
    cols = "\n".join(_domain_line(i + 1, c) for i, c in enumerate(t.columns))
    n = len(t.columns)
    extra = ""
    if serial_val is not None:
        extra = (f"\nThe printed serial number in column 1 of this row "
                 f"is {serial_val}.")
    return (f"This image is ONE row of a hand-filled paper form. "
            f"The {n} columns, left to right, are:\n{cols}\n{extra}\n"
            f"Transcribe the handwriting into exactly one CSV line with "
            f"{n} fields in that order. Rules: empty field for an empty cell; "
            f"a lone dot means 0; a struck-through cell is empty; a tick "
            f"means Y. Ignore anything written outside the row. "
            f"Output only the CSV line.")


def cell_prompt(col):
    if col.type in ("yn", "choice"):
        dom = " or ".join(col.domain)
        return (f'One cell of a paper form, column "{col.label}". The '
                f"handwritten value is one of: {dom}. Reply with that value "
                f"only, or EMPTY if the cell is blank. A tick means Y.")
    kind = {"int": "a whole number", "dec": "a number",
            "date": "a date", "name": "a person's name"}.get(
        col.type, "a short handwritten value")
    return (f'One cell of a paper form, column "{col.label}". It contains '
            f"{kind} or nothing. A lone dot means 0. A struck-through entry "
            f"means EMPTY. Reply with the value only, or EMPTY.")


def header_prompt(h):
    kind = {"date": "a date", "name": "a person's name",
            "int": "a number", "dec": "a number"}.get(h.type, "a short value")
    return (f'This is the "{h.label}" field of a paper form. The label is '
            f"printed; the value is handwritten ({kind}). "
            f"Reply with the handwritten value only, or the single word "
            f"EMPTY if nothing is written.")


# ── extraction ────────────────────────────────────────────────────
@dataclass
class Extraction:
    form_id: str | None
    grid: dict = None
    flags: list = field(default_factory=list)     # per-cell issue dicts
    verdict: str = "detected"                     # detected|review|reject
    reasons: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    aligned_png: bytes | None = None
    overlay: dict | None = None      # detected mark rows for exact UI overlay


def _parse_band(text, ncols):
    line = next((l for l in text.splitlines() if l.strip()), "")
    line = line.strip().strip("`")
    try:
        vals = next(csv.reader(io.StringIO(line)))
    except StopIteration:
        vals = []
    vals = [v.strip() for v in vals]
    shape_ok = len(vals) == ncols
    if len(vals) < ncols:
        vals += [""] * (ncols - len(vals))
    return vals[:ncols], shape_ok


def fuzzy_snap(v, options, cutoff=0.78):
    """Snap a near-miss read onto a known vocabulary ('Shimoa'->'Shimoga').
    Only for words long enough that similarity is meaningful, and only when
    the best match is unambiguous."""
    import difflib
    nv = norm(v)
    if not nv or len(nv) < 4:
        return None
    cand = {o: norm(o) for o in options if len(norm(o)) >= 4}
    if not cand:
        return None
    hits = difflib.get_close_matches(nv, list(cand.values()), n=2,
                                     cutoff=cutoff)
    if len(hits) == 1 or (len(hits) > 1 and
                          difflib.SequenceMatcher(None, nv, hits[0]).ratio()
                          - difflib.SequenceMatcher(None, nv, hits[1]).ratio()
                          > 0.08):
        for o, no in cand.items():
            if no == hits[0]:
                return o
    return None


def _domain_ok(col, v):
    if not v:
        return True
    if col.type in ("yn", "choice"):
        return norm(v) in {norm(d) for d in col.domain}
    if col.type == "int":
        try:
            f = float(v.replace(",", "."))
        except ValueError:
            return False
        if f != int(f):
            return False
    if col.type in ("int", "dec"):
        try:
            f = float(v.replace(",", "."))
        except ValueError:
            return False
        lo = col.min if col.min is not None else -1e12
        hi = col.max if col.max is not None else 1e12
        return lo <= f <= hi
    return True


def extract(input_path: Path, provider, template: Template = None,
            progress=None, cell_types: set = None) -> Extraction:
    """Run the full pipeline. `provider` is a core.vlm provider name/cfg.
    cell_types: column types that are ALWAYS read cell-by-cell instead of
    trusting the row-band CSV. Defaults to {'dec','int'}: long digit strings
    are the band mode's measured weakness (+0.10 on rupee columns)."""
    if cell_types is None:
        cell_types = {"dec", "int"}
    from .vlm import ask
    t0 = time.time()
    say = progress or (lambda *_: None)
    photo = load_input(input_path)

    # 1. identity
    form_id, how = read_form_id(photo)
    if form_id is None and template is None:
        say("QR failed; asking model for printed ID")
        form_id = read_form_id_fallback(photo, provider)
        how = "model" if form_id else how
    if template is None:
        if form_id is None:
            return Extraction(form_id=None, verdict="reject",
                              reasons=["form ID unreadable (QR and printed "
                                       "code both failed) — cannot select a "
                                       "template"])
        try:
            template = load_template(form_id)
        except FileNotFoundError:
            return Extraction(form_id=form_id, verdict="reject",
                              reasons=[f"form ID {form_id} is not a known "
                                       f"template on this system"])
    t = template
    form_id = form_id or t.form_id

    # 2. align: ORB homography + TPS bow removal
    blank, scale = render_blank(t)
    aligned, align_ok, inliers = align(photo, blank)
    say(f"aligned: {align_ok} ({inliers} inliers)")

    grid = empty_grid(t)
    flags = []
    ncols = len(t.columns)
    serial_cols = [i for i, c in enumerate(t.columns) if c.type == "serial"]

    # 3. geometry. PRIMARY: printed fiducial marks — per-row quads, exact
    # under page bow. FALLBACK (older templates without marks): pin the table
    # corners, then snap every rule. integrity = anchors found (guardrail).
    fids, fid_frac = detect_fiducials(aligned, t, scale)
    if 0.3 <= fid_frac < 0.98:
        # refine: the FOUND marks are exact template-known control points —
        # far better warp anchors than ORB features. TPS on them, re-detect.
        ctrl, disp = [], []
        for side, pts in (t.geometry.get("fiducials") or {}).items():
            for tpl_pt, det in zip(pts, fids.get(side) or []):
                if det is None:
                    continue
                tx, ty = tpl_pt[0] * scale, tpl_pt[1] * scale
                ctrl.append((tx, ty))
                disp.append((det[0] - tx, det[1] - ty))
        if len(ctrl) >= 8:
            re_warped = Image.fromarray(_tps_backwarp(
                np.asarray(aligned.convert("RGB")),
                np.array(ctrl, np.float32), np.array(disp, np.float32)))
            fids2, frac2 = detect_fiducials(re_warped, t, scale)
            say(f"fiducial TPS refine: {fid_frac:.2f} -> {frac2:.2f}")
            if frac2 > fid_frac:
                aligned, fids, fid_frac = re_warped, fids2, frac2
    geom = fiducial_geometry(fids, t, scale) if fid_frac >= 0.5 else None
    corners_ok = geom is not None
    bands = {}
    cells_ink = {}
    if geom is not None:
        integrity = fid_frac
        say(f"fiducials: {fid_frac:.2f}")
        for r in range(t.rows):
            band, col_x = fiducial_band(aligned, geom, t, scale, r)
            bands[r] = (band, col_x)
            arr = np.asarray(band.convert("L"))
            stroke = stroke_mask(arr, scale,
                                 printed_gray=blank_band(blank, t, scale, r))
            for c in range(ncols):
                x0, x1 = int(col_x[c]) + 5, int(col_x[c + 1]) - 5
                cell = (stroke[11:-11, x0:x1] if stroke.shape[0] > 30
                        else stroke[:, x0:x1])
                cells_ink[(r, c)] = (float(cell.mean()) if cell.size else 0.0)
    elif t.geometry.get("fiducials"):
        # the form HAS anchor marks and we still can't find them — the photo
        # cannot be trusted; refuse before spending a single model call
        return Extraction(
            form_id=form_id, grid=empty_grid(t), verdict="reject",
            reasons=[f"only {fid_frac:.0%} of the form's anchor marks were "
                     f"found — the photo is too warped, dark or cropped to "
                     f"locate cells. Retake flatter, closer and fully in "
                     f"frame."],
            stats={"align_ok": align_ok, "inliers": inliers,
                   "id_how": how, "grid_integrity": round(fid_frac, 3),
                   "model_calls": 0, "inked_cells": 0,
                   "latency_s": round(time.time() - t0, 1), "flags": {}})
    else:
        aligned, corners_ok = corner_pin(aligned, t, scale)
        sxs, sys_, sxsamp, integrity, _shift = snap_grid(aligned, t, scale)
        say(f"grid integrity (snap fallback): {integrity:.2f}")
        snapped = (sxs, sys_, sxsamp)
        cells_ink, _ = ink_map(aligned, blank, t, scale, snapped=snapped)
        for r in range(t.rows):
            bands[r] = (extract_band(aligned, sxs, sys_, sxsamp, r), None)
    _hs = (0, 0)
    if geom is not None:
        tplL0 = t.geometry["fiducials"]["left"][0]
        tplR0 = t.geometry["fiducials"]["right"][0]
        _hs = (int(((geom["left"][0][0] - tplL0[0] * scale)
                    + (geom["right"][0][0] - tplR0[0] * scale)) / 2),
               int(((geom["left"][0][1] - tplL0[1] * scale)
                    + (geom["right"][0][1] - tplR0[1] * scale)) / 2))
    _, hdr_ink = ink_map(aligned, blank, t, scale, shift=_hs)

    # 4. bands — skip rows with no ink at all (saves calls, kills tail risk)
    calls = 0
    for r in range(t.rows):
        row_ink = max(cells_ink.get((r, c), 0.0) for c in range(ncols)
                      if c not in serial_cols)
        if row_ink < INK_THRESHOLD:
            continue
        crop = bands[r][0]
        k = min(3.0, 1000 / max(crop.size))
        if k > 1:
            crop = crop.resize((int(crop.width * k), int(crop.height * k)))
        sv = r + 1 if serial_cols else None
        out = ask(crop, band_prompt(t, sv), provider,
                  max_tokens=16 * ncols + 32)
        calls += 1
        vals, shape_ok = _parse_band(out, ncols)
        # a model failure mode: echoing the column labels instead of reading.
        # With a known template we can detect it outright.
        labels = [norm(c.label) for c in t.columns]
        echoes = sum(1 for v in vals if v and norm(v) in labels)
        if echoes >= max(2, ncols // 3):
            vals = [""] * ncols
            shape_ok = False
            flags.append({"row": r, "col": None, "flag": "shape",
                          "detail": f"echoed column labels: {out[:80]}"})

        def clean(v, col):
            if v and norm(v) in ("empty", "blank", "-", "na"):
                return "" if col.type != "text" else v
            return v

        vals = [clean(v, t.columns[ci]) for ci, v in enumerate(vals)]
        inked = [ci for ci in range(ncols) if ci not in serial_cols
                 and cells_ink.get((r, ci), 0.0) >= INK_THRESHOLD]
        nonempty = [(ci, v) for ci, v in enumerate(vals)
                    if ci not in serial_cols and v]

        forced = [ci for ci in inked
                  if cell_types and t.columns[ci].type in cell_types]

        # THE field-shift fix. A cheap model drops empty fields and every
        # later value slides one column left — token-accurate, layout-wrong.
        # The ink map knows WHICH cells are written; when counts agree, the
        # model supplies ordered VALUES and the ink map supplies POSITIONS.
        def read_cell(ci):
            """One bounded read: crop the cell, ask for a single value."""
            nonlocal calls
            col = t.columns[ci]
            band_img, col_x = bands[r]
            if col_x is not None:
                cx0 = max(0, int(col_x[ci]) - 4)
                cx1 = min(band_img.width, int(col_x[ci + 1]) + 4)
                cc = band_img.crop((cx0, 0, cx1, band_img.height))
            else:
                fx = [x * scale for x in t.geometry["table"]["x"]]
                w0 = fx[0] - 6
                cc = band_img.crop((max(0, int(fx[ci] - w0) - 4), 0,
                                    int(fx[ci + 1] - w0) + 4,
                                    band_img.height))
            kk = max(1.0, min(4.0, 320 / max(cc.size)))
            if kk > 1:
                cc = cc.resize((int(cc.width * kk), int(cc.height * kk)))
            try:
                cv = ask(cc, cell_prompt(col), provider, max_tokens=24)
                calls += 1
            except RuntimeError:
                cv = ""
            cv = cv.strip().splitlines()[0].strip() if cv.strip() else ""
            cv = clean(cv, col)
            return "" if norm(cv) == "empty" else cv

        if len(nonempty) == len(inked):
            placed = {ci: v for ci, (_, v) in zip(inked, nonempty)}
            if [ci for ci, _ in nonempty] != inked:
                flags.append({"row": r, "col": None, "flag": "shift_fixed",
                              "detail": f"{len(inked)} values re-anchored"})
        else:
            # counts disagree — band read is unreliable; re-read each inked
            # cell individually (bounded: one value per call, no shift risk)
            placed = {ci: read_cell(ci) for ci in inked}
            flags.append({"row": r, "col": None, "flag": "cell_mode",
                          "detail": f"band gave {len(nonempty)} values for "
                                    f"{len(inked)} inked cells"})
        # columns the caller wants read cell-by-cell regardless (e.g. long
        # numbers, where band CSV digit accuracy is the measured weakness).
        # The band already produced a value — TWO independent reads of the
        # same ink. Agreement = confidence; disagreement = flag the cell.
        # A wrong digit is domain-valid and no rule can catch it otherwise.
        for ci in forced:
            band_v = placed.get(ci, "")
            cell_v = read_cell(ci)
            if band_v and cell_v and norm(band_v) != norm(cell_v):
                flags.append({"row": r, "col": ci, "flag": "disagree",
                              "detail": f"band {band_v!r} vs cell {cell_v!r}"})
            placed[ci] = cell_v or band_v

        # serial cross-check (row identity)
        for ci in serial_cols:
            v = vals[ci] if ci < len(vals) else ""
            if v and norm(v) != str(r + 1):
                flags.append({"row": r, "col": ci, "flag": "serial_mismatch",
                              "detail": f"read {v!r}, printed {r + 1}"})

        for ci, col in enumerate(t.columns):
            if col.type == "serial":
                continue
            v = placed.get(ci, "")
            if v and col.domain and not _domain_ok(col, v):
                snap = fuzzy_snap(v, col.domain)
                if snap is not None:
                    v = snap
            if v and not _domain_ok(col, v):
                flags.append({"row": r, "col": ci, "flag": "domain",
                              "detail": v})
            if (not v) and ci in inked:
                flags.append({"row": r, "col": ci, "flag": "unread_ink"})
            grid["table"][r + 1][ci] = v if v else None
        say(f"row {r + 1}: {[placed.get(ci, '') for ci in range(ncols)]}")

    # 5. header fields. The header sits above the table where no fiducials
    # live; the top mark pair tells us the local residual offset — use it.
    hdx, hdy = _hs
    for hf in t.header_fields:
        bb = t.geometry["header_fields"].get(hf.key)
        if not bb:
            continue
        if hdr_ink.get(hf.key, 0.0) < INK_THRESHOLD:
            continue
        x0, y0, x1, y1 = [v * scale for v in bb]
        x0, x1 = x0 + hdx, x1 + hdx
        y0, y1 = y0 + hdy, y1 + hdy
        # include the printed label just left of the rule for context
        crop = aligned.crop((max(0, int(x0) - 110), int(y0) - 8,
                             int(x1) + 4, int(y1) + 10))
        k = min(3.0, 900 / max(crop.size))
        if k > 1:
            crop = crop.resize((int(crop.width * k), int(crop.height * k)))
        out = ask(crop, header_prompt(hf), provider, max_tokens=48)
        calls += 1
        v = out.strip().splitlines()[0].strip() if out.strip() else ""
        if norm(v) in ("empty", "blank"):
            v = ""
        if v and hf.domain:
            snap = fuzzy_snap(v, hf.domain)
            if snap is not None:
                v = snap
        for i, (lab, _) in enumerate(grid["header"]):
            if lab == hf.label:
                grid["header"][i] = (lab, v or None)

    # 6. verdict
    nflag = {k: sum(1 for f in flags if f["flag"] == k)
             for k in ("shape", "serial_mismatch", "domain", "no_ink",
                       "unread_ink", "shift_fixed", "cell_mode", "disagree")}
    inked_cells = sum(1 for (r, c), v in cells_ink.items()
                      if v >= INK_THRESHOLD and c not in serial_cols
                      and r < t.rows)
    reasons = []
    verdict = "detected"
    if not align_ok:
        verdict = "review"
        reasons.append("could not align the photo to the template — check the "
                       "photo is flat, complete and the right form")
    if not corners_ok:
        verdict = "review"
        reasons.append("table corners not found — the full table must be "
                       "visible in the photo")
    if integrity < GEOM_TRUST:
        verdict = "reject" if integrity < 0.5 else "review"
        reasons.append(f"only {integrity:.0%} of the form's anchor marks "
                       f"were found — the photo is too warped or cropped to "
                       f"trust cell positions. Retake flatter, closer and "
                       f"fully in frame.")
    if inked_cells == 0:
        verdict = "reject"
        reasons.append("no handwriting found anywhere on the form")
    # Per-signal thresholds calibrated on the 48-form 2B baseline: each
    # signal below separated good (≥0.9 cell_acc) from bad forms; a single
    # blended "frac_bad" over-flagged sparse forms (small denominators).
    rows_read = len({f.get("row") for f in flags if f.get("row") is not None} |
                    {r for r in range(t.rows)
                     if any(cells_ink.get((r, c), 0) >= INK_THRESHOLD
                            for c in range(ncols) if c not in serial_cols)})
    dom_frac = nflag["domain"] / max(1, inked_cells)
    unread_frac = nflag["unread_ink"] / max(1, inked_cells)
    cellm_frac = nflag["cell_mode"] / max(1, rows_read)
    review_why = []
    if nflag["serial_mismatch"]:
        review_why.append(f"{nflag['serial_mismatch']} row(s) read a wrong "
                          f"printed serial (row identity suspect)")
    if nflag["shape"]:
        review_why.append(f"{nflag['shape']} row(s) returned malformed output")
    if unread_frac > 0.10:
        review_why.append(f"{nflag['unread_ink']} written cells could not be "
                          f"read")
    if dom_frac > 0.15:
        review_why.append(f"{nflag['domain']} values fall outside their "
                          f"column's allowed values")
    if nflag["disagree"] / max(1, inked_cells) > 0.15:
        review_why.append(f"{nflag['disagree']} cells read differently on "
                          f"two passes (uncertain digits)")
    if cellm_frac > 0.40:
        review_why.append("most rows needed unreliable cell-by-cell "
                          "re-reading")
    if len(review_why) >= 3 or (verdict != "detected" and review_why):
        verdict = "reject" if verdict == "reject" else "review"
    if review_why:
        if verdict == "detected":
            verdict = "review"
        reasons.extend(review_why)
        reasons.append("flagged cells are highlighted for review")

    buf = io.BytesIO()
    aligned.save(buf, "PNG")
    overlay = None
    if geom is not None:
        overlay = {"left": [[round(x, 1), round(y, 1)] for x, y in geom["left"]],
                   "right": [[round(x, 1), round(y, 1)] for x, y in geom["right"]],
                   "col_x": [round(x * scale, 1)
                             for x in t.geometry["table"]["x"]]}
    return Extraction(
        form_id=form_id, grid=grid, flags=flags, verdict=verdict,
        reasons=reasons, overlay=overlay,
        stats={"align_ok": align_ok, "inliers": inliers, "id_how": how,
               "grid_integrity": round(integrity, 3),
               "model_calls": calls, "inked_cells": inked_cells,
               "latency_s": round(time.time() - t0, 1), "flags": nflag},
        aligned_png=buf.getvalue())


def extraction_to_xlsx(ex: Extraction, path: Path):
    from .template import grid_to_xlsx
    return grid_to_xlsx(ex.grid, path)
