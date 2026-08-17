#!/usr/bin/env python3
"""Generate the validation corpus: every registered template × seeds, with
density sampled ~uniform 0.1-1.0 and photo levels mixed (both are seed-driven
inside fill_form). Goldens exact by construction.

Usage: .venv/bin/python3 eval/gen_corpus.py [--seeds 8] [--out data/forms]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.template import load  # noqa: E402
from core.fill import fill_form  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--out", default="data/forms")
    a = ap.parse_args()
    root = Path(__file__).parent.parent
    slug_to_id = json.loads((root / "data/specs/slug_to_id.json").read_text())
    out = root / a.out
    made = 0
    for slug, fid in slug_to_id.items():
        t = load(fid)
        sector = slug.split("_")[0]
        sector = {"edu": "edu", "livelihoods": "shg", "agri": "agri",
                  "health": "health"}.get(sector, "health")
        for s in range(a.seeds):
            d = out / f"{slug}__{fid}__s{s}"
            if (d / "golden.xlsx").exists():
                continue
            m = fill_form(t, d, seed=s, sector=sector)
            made += 1
            print(f"{d.name}: density={m['density']} photo={m['photo']} "
                  f"medium={m['medium']} cells={m['filled_cells']}", flush=True)
    print(f"DONE generated {made}")


if __name__ == "__main__":
    main()
