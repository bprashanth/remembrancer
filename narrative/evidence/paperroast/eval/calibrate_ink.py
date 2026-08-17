#!/usr/bin/env python3
"""Calibrate the ink detector against golden emptiness across the corpus.

For every form: run geometry only (no model), compute per-cell ink fraction,
join with golden (cell empty vs filled), sweep the threshold, report the
ROC and the operating point. The ink map gates model calls and anchors the
field-shift fix, so its FP rate directly becomes hallucination pressure and
its FN rate becomes misses.
"""
import json
import sys
from pathlib import Path

import numpy as np
import openpyxl

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.extract import (load_input, render_blank, align, detect_fiducials,
                          fiducial_geometry, fiducial_band,
                          stroke_mask, blank_band)  # noqa: E402
from core.template import load as load_t  # noqa: E402
import cv2  # noqa: E402

ROOT = Path(__file__).parent.parent


def cell_inks(d: Path):
    fid = d.name.split("__")[1]
    t = load_t(fid)
    photo = load_input(d / "input.jpg")
    blank, scale = render_blank(t)
    aligned, ok, inl = align(photo, blank)
    fids, ff = detect_fiducials(aligned, t, scale)
    geom = fiducial_geometry(fids, t, scale) if ff >= 0.5 else None
    if geom is None:
        return None
    wb = openpyxl.load_workbook(d / "golden.xlsx")
    rows = list(wb["table"].iter_rows(values_only=True))[1:]
    ncols = len(t.columns)
    out = []
    for r in range(t.rows):
        band, col_x = fiducial_band(aligned, geom, t, scale, r)
        arr = np.asarray(band.convert("L"))
        stroke = stroke_mask(arr, scale,
                             printed_gray=blank_band(blank, t, scale, r))
        for c in range(ncols):
            if t.columns[c].type == "serial":
                continue
            x0, x1 = int(col_x[c]) + 5, int(col_x[c + 1]) - 5
            cell = (stroke[11:-11, x0:x1] if stroke.shape[0] > 30
                    else stroke[:, x0:x1])
            frac = float(cell.mean()) if cell.size else 0.0
            g = rows[r][c] if r < len(rows) and c < len(rows[r]) else None
            filled = g is not None and str(g).strip() != ""
            out.append((frac, filled, ff))
    return out


def main():
    data = []
    forms = sorted((ROOT / "data/forms").glob("*__PR*__s*"))
    for d in forms:
        try:
            r = cell_inks(d)
        except Exception as e:  # noqa: BLE001
            print(f"{d.name}: ERR {e}")
            continue
        if r is None:
            print(f"{d.name}: no fiducial geometry")
            continue
        data.extend([(f, fl, d.name) for f, fl, _ in r])
    fr = np.array([x[0] for x in data])
    fl = np.array([x[1] for x in data])
    print(f"\ncells: {len(fr)}  filled: {fl.sum()} ({fl.mean():.1%})")
    print(f"{'thr':>8} {'FN(miss)':>9} {'FP(halluc)':>10} {'balacc':>7}")
    best = None
    for thr in [0.001, 0.002, 0.003, 0.004, 0.006, 0.008, 0.010, 0.014,
                0.020, 0.030]:
        pred = fr >= thr
        fn = ((~pred) & fl).sum() / max(1, fl.sum())
        fp = (pred & (~fl)).sum() / max(1, (~fl).sum())
        bal = 1 - (fn + fp) / 2
        print(f"{thr:8.3f} {fn:9.3%} {fp:10.3%} {bal:7.3f}")
        if best is None or bal > best[1]:
            best = (thr, bal)
    print(f"\nbest threshold {best[0]} (balanced acc {best[1]:.3f})")
    # where do FPs live? top FP forms at best thr
    from collections import Counter
    cnt = Counter(x[2] for x, p in zip(data, fr >= best[0])
                  if p and not x[1])
    print("top FP forms:", cnt.most_common(6))


if __name__ == "__main__":
    main()
