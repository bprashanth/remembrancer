#!/usr/bin/env python3
"""Ablation: value domains in prompts ON vs OFF — the BRIEF's open question
'how much does a known value domain buy on ambiguous single-char cells?'

Monkeypatches the prompt builders to hide domains, runs the same forms
through the same pipeline, and reports per-column-type accuracy.

  .venv/bin/python3 eval/ablate_domains.py [--provider local-2b] [--seeds 4]
"""
import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import core.extract as X  # noqa: E402
from core.extract import extract, extraction_to_xlsx  # noqa: E402
from core.score import score_files  # noqa: E402
from core.template import load as load_t  # noqa: E402

ROOT = Path(__file__).parent.parent

_orig_domain_line = X._domain_line
_orig_cell_prompt = X.cell_prompt


def _blind_domain_line(i, c):
    if c.type == "serial":
        return f"{i}. {c.label}: printed serial number"
    if c.type in ("yn", "choice"):
        return f"{i}. {c.label}: a short handwritten code, or empty"
    return _orig_domain_line(i, c)


def _blind_cell_prompt(col):
    if col.type in ("yn", "choice"):
        return (f'One cell of a paper form, column "{col.label}". It contains '
                f"a short handwritten code or nothing. Reply with the code "
                f"only, or EMPTY if the cell is blank. A tick means Y.")
    return _orig_cell_prompt(col)


def run(forms, provider, blind):
    if blind:
        X._domain_line = _blind_domain_line
        X.cell_prompt = _blind_cell_prompt
    else:
        X._domain_line = _orig_domain_line
        X.cell_prompt = _orig_cell_prompt
    per_type = {"choice": [], "yn": [], "all": []}
    for d in forms:
        fid = d.name.split("__")[1]
        t = load_t(fid)
        ex = extract(d / "input.jpg", provider)
        if not ex.grid or ex.verdict == "reject":
            continue
        cand = d / f"cand_ablate_{'blind' if blind else 'dom'}.xlsx"
        extraction_to_xlsx(ex, cand)
        r = score_files(d / "golden.xlsx", cand)
        per_type["all"].append(r["cell_acc"])
        for col in t.columns:
            pc = r["per_col"].get(col.label)
            if pc and pc["filled"] > 0 and col.type in per_type:
                per_type[col.type].append(pc["cell_acc"])
    return per_type


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="local-2b")
    ap.add_argument("--seeds", type=int, default=4)
    a = ap.parse_args()
    # choice-heavy templates only
    slugs = ["edu_attendance", "health_immunization", "edu_exam_marks"]
    ids = json.loads((ROOT / "data/specs/slug_to_id.json").read_text())
    forms = []
    for s in slugs:
        for k in range(a.seeds):
            d = ROOT / "data/forms" / f"{s}__{ids[s]}__s{k}"
            if (d / "golden.xlsx").exists():
                forms.append(d)
    print(f"{len(forms)} forms, provider {a.provider}")
    for blind in (False, True):
        r = run(forms, a.provider, blind)
        lab = "domains HIDDEN" if blind else "domains IN PROMPT"
        print(f"\n{lab}:")
        for k, vs in r.items():
            if vs:
                print(f"  {k:7s} n={len(vs):3d}  acc {st.mean(vs):.3f}")


if __name__ == "__main__":
    main()
