#!/usr/bin/env python3
"""Import every register-class harvested XLSForm, render it, hand-fill it,
extract it — the anti-overfitting check: does the pipeline survive layouts
nobody on this project designed?

  .venv/bin/python3 eval/eval_harvested.py [--provider or-8b] [--seeds 2]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from eval.xlsform_import import import_xlsform  # noqa: E402

ROOT = Path(__file__).parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="or-8b")
    ap.add_argument("--seeds", type=int, default=2)
    a = ap.parse_args()
    census = json.loads(
        (ROOT / "data/xlsforms/harvest/census.json").read_text())
    regs = [c for c in census if c["verdict"] == "register"]
    print(f"{len(regs)} register-class forms")
    from core.render import render_from_spec
    from core.fill import fill_form
    from core.template import load as load_t
    from core.extract import extract, extraction_to_xlsx
    from core.score import score_files
    rows = []
    for c in regs:
        src = ROOT / "data/xlsforms/harvest" / c["file"]
        try:
            spec = import_xlsform(src)
            t = render_from_spec(spec)
        except Exception as e:  # noqa: BLE001
            rows.append({"file": c["file"], "stage": "import/render",
                         "error": f"{type(e).__name__}: {e}"})
            print(f"  {c['file'][:60]}: RENDER FAIL {e}", flush=True)
            continue
        for s in range(a.seeds):
            d = ROOT / "data/forms_harvest" / f"{t.form_id}__s{s}"
            try:
                fill_form(t, d, seed=s)
                ex = extract(d / "input.jpg", a.provider)
                extraction_to_xlsx(ex, d / "cand.xlsx")
                r = score_files(d / "golden.xlsx", d / "cand.xlsx")
                rows.append({"file": c["file"], "form_id": t.form_id,
                             "seed": s, "cols": len(t.columns),
                             "orient": t.orientation,
                             "verdict": ex.verdict,
                             "cell_acc": r["cell_acc"],
                             "halluc": r["halluc_rate"],
                             "integrity": ex.stats.get("grid_integrity")})
                print(f"  {t.form_id} s{s} [{c['file'][:44]}]: "
                      f"{ex.verdict} acc {r['cell_acc']:.3f}", flush=True)
            except Exception as e:  # noqa: BLE001
                rows.append({"file": c["file"], "form_id": t.form_id,
                             "seed": s, "stage": "fill/extract",
                             "error": f"{type(e).__name__}: {e}"})
                print(f"  {t.form_id} s{s}: FAIL {e}", flush=True)
    out = ROOT / "results" / "harvested_eval.json"
    out.write_text(json.dumps(rows, indent=1))
    ok = [r for r in rows if "cell_acc" in r]
    det = [r for r in ok if r["verdict"] == "detected"]
    import statistics as st
    print(f"\nforms evaluated {len(ok)}, render/pipeline failures "
          f"{len(rows) - len(ok)}")
    if ok:
        print(f"all: acc {st.mean(r['cell_acc'] for r in ok):.3f}")
    if det:
        print(f"detected (n={len(det)}): "
              f"acc {st.mean(r['cell_acc'] for r in det):.3f} "
              f"halluc {st.mean(r['halluc'] for r in det):.3f}")


if __name__ == "__main__":
    main()
