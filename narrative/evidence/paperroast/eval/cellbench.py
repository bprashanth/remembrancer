#!/usr/bin/env python3
"""Handwriting-head benchmark: identical pre-rectified CELL crops, identical
prompts, different models. Isolates 'can this model read one cell of
handwriting' from harness, geometry and interpretation (NEXT_STEPS exp 2).

build : cut cell crops + goldens from geometry-trusted corpus forms
        (fiducial pipeline, no model calls), balanced across value types
run   : ask one provider to read every crop (plain prompt and, for typed
        cells, a domain prompt) -> results/cellbench_<tag>.jsonl
report: exact-match table by value type and prompt mode

Usage:
  .venv/bin/python3 eval/cellbench.py build [--per-type 60]
  .venv/bin/python3 eval/cellbench.py run --provider or-8b [--tag or-8b]
  .venv/bin/python3 eval/cellbench.py report
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent
BENCH = ROOT / "data" / "cellbench"


def build(per_type=60):
    import openpyxl
    from core.extract import (load_input, render_blank, align,
                              detect_fiducials, fiducial_geometry,
                              fiducial_band)
    from core.template import load as load_t
    BENCH.mkdir(parents=True, exist_ok=True)
    pools = {}
    rng = random.Random(7)
    forms = sorted((ROOT / "data/forms").glob("*__PR*__s*"))
    for d in forms:
        fid = d.name.split("__")[1]
        try:
            t = load_t(fid)
        except FileNotFoundError:
            continue
        photo = load_input(d / "input.jpg")
        blank, scale = render_blank(t)
        aligned, ok, _ = align(photo, blank)
        fids, ff = detect_fiducials(aligned, t, scale)
        if ff < 0.98:
            continue                       # only geometry-trusted crops
        geom = fiducial_geometry(fids, t, scale)
        wb = openpyxl.load_workbook(d / "golden.xlsx")
        rows = list(wb["table"].iter_rows(values_only=True))[1:]
        for r in range(t.rows):
            bandimg = None
            for c, col in enumerate(t.columns):
                if col.type == "serial":
                    continue
                g = rows[r][c] if r < len(rows) and c < len(rows[r]) else None
                if g is None or not str(g).strip():
                    continue
                kind = ("amount" if col.type in ("int", "dec")
                        else "code" if col.type in ("choice", "yn")
                        else "date" if col.type == "date"
                        else "name" if col.type == "name" else "text")
                if bandimg is None:
                    bandimg, col_x = fiducial_band(aligned, geom, t, scale, r)
                cc = bandimg.crop((max(0, int(col_x[c]) - 4), 0,
                                   min(bandimg.width, int(col_x[c + 1]) + 4),
                                   bandimg.height))
                k = max(1.0, min(4.0, 320 / max(cc.size)))
                if k > 1:
                    cc = cc.resize((int(cc.width * k), int(cc.height * k)))
                pools.setdefault(kind, []).append(
                    {"form": d.name, "r": r, "c": c, "golden": str(g).strip(),
                     "type": kind, "col_label": col.label,
                     "domain": col.domain, "img": cc})
    manifest = []
    for kind, items in pools.items():
        rng.shuffle(items)
        for i, it in enumerate(items[:per_type]):
            name = f"{kind}_{i:03d}.png"
            it["img"].save(BENCH / name)
            manifest.append({k: v for k, v in it.items() if k != "img"}
                            | {"png": name})
    (BENCH / "manifest.json").write_text(json.dumps(manifest, indent=1))
    from collections import Counter
    print("built:", dict(Counter(m["type"] for m in manifest)),
          "->", BENCH)


PLAIN = ("This image is one cell of a hand-filled paper form. Read the "
         "handwritten value. Reply with the value only — no explanation. "
         "A lone dot means 0. A tick means Y. If empty, reply EMPTY.")


def domain_prompt(m):
    if m["domain"]:
        dom = " or ".join(m["domain"])
        return (f'One cell of a paper form, column "{m["col_label"]}". The '
                f"handwritten value is one of: {dom}. Reply with that value "
                f"only. A tick means Y.")
    kind = {"amount": "a number", "date": "a date",
            "name": "a person's name"}.get(m["type"], "a short value")
    return (f'One cell of a paper form, column "{m["col_label"]}". It '
            f"contains {kind}. Reply with the value only. A lone dot "
            f"means 0.")


def run(provider, tag):
    from PIL import Image
    from core.vlm import ask
    from core.score import norm
    manifest = json.loads((BENCH / "manifest.json").read_text())
    out = ROOT / "results" / f"cellbench_{tag}.jsonl"
    done = set()
    if out.exists():
        done = {(json.loads(l)["png"], json.loads(l)["mode"])
                for l in out.read_text().splitlines()}
    with out.open("a") as fh:
        for m in manifest:
            im = Image.open(BENCH / m["png"])
            for mode, prompt in (("plain", PLAIN),
                                 ("domain", domain_prompt(m))):
                if (m["png"], mode) in done:
                    continue
                try:
                    got = ask(im, prompt, provider, max_tokens=32)
                except Exception as e:  # noqa: BLE001
                    got = f"__ERR__{e}"
                got1 = got.strip().splitlines()[0].strip() if got.strip() else ""
                ok = norm(got1) == norm(m["golden"])
                fh.write(json.dumps({**{k: m[k] for k in
                                        ("png", "type", "golden")},
                                     "mode": mode, "got": got1,
                                     "ok": ok}) + "\n")
                fh.flush()
    print(f"done -> {out}")


def report():
    import statistics as st
    from collections import defaultdict
    print(f"{'tag':22s} {'mode':7s}" + "".join(
        f" {k:>7s}" for k in ("name", "amount", "code", "date", "text",
                              "ALL")))
    for p in sorted((ROOT / "results").glob("cellbench_*.jsonl")):
        rows = [json.loads(l) for l in p.read_text().splitlines()
                if "__ERR__" not in l]
        for mode in ("plain", "domain"):
            sub = [r for r in rows if r["mode"] == mode]
            if not sub:
                continue
            by = defaultdict(list)
            for r in sub:
                by[r["type"]].append(r["ok"])
            cells = []
            for k in ("name", "amount", "code", "date", "text"):
                cells.append(f" {st.mean(by[k]):7.3f}" if by.get(k)
                             else f" {'—':>7s}")
            allv = st.mean(r["ok"] for r in sub)
            print(f"{p.stem[10:]:22s} {mode:7s}" + "".join(cells)
                  + f" {allv:7.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "run", "report"])
    ap.add_argument("--per-type", type=int, default=60)
    ap.add_argument("--provider")
    ap.add_argument("--tag")
    a = ap.parse_args()
    if a.cmd == "build":
        build(a.per_type)
    elif a.cmd == "run":
        run(a.provider, a.tag or a.provider)
    else:
        report()
