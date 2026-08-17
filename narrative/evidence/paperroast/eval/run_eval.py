#!/usr/bin/env python3
"""Run extraction over the corpus for one provider; positional scores per form.

Usage:
  .venv/bin/python3 eval/run_eval.py --provider local-2b [--forms GLOB]
                                     [--limit N] [--tag NAME]

Writes results/<tag>.jsonl (one row per form) and prints a summary table.
Skips forms already present in the results file (resumable).
"""
import argparse
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.extract import extract, extraction_to_xlsx  # noqa: E402
from core.score import score_files  # noqa: E402

ROOT = Path(__file__).parent.parent


def summarize(rows):
    if not rows:
        return "no rows"
    ks = ["cell_acc", "filled_recall", "blank_acc", "halluc_rate", "wrong_rate",
          "miss_rate", "header_acc"]
    out = []
    for k in ks:
        vs = [r[k] for r in rows if k in r and r.get("error") is None]
        if vs:
            out.append(f"{k}={sum(vs)/len(vs):.3f}")
    n_err = sum(1 for r in rows if r.get("error"))
    verd = {}
    for r in rows:
        verd[r.get("verdict", "?")] = verd.get(r.get("verdict", "?"), 0) + 1
    lat = [r["latency_s"] for r in rows if r.get("latency_s")]
    return (f"n={len(rows)} err={n_err} verdicts={verd}\n  " + "  ".join(out)
            + (f"\n  latency avg={sum(lat)/len(lat):.1f}s" if lat else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True)
    ap.add_argument("--forms", default="*__PR*__s*")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    tag = a.tag or a.provider
    res_path = ROOT / "results" / f"{tag}.jsonl"
    res_path.parent.mkdir(exist_ok=True)
    done = set()
    rows = []
    if res_path.exists():
        for line in res_path.read_text().splitlines():
            r = json.loads(line)
            rows.append(r)
            done.add(r["form"])
    forms = sorted((ROOT / "data/forms").glob(a.forms))
    forms = [f for f in forms if (f / "golden.xlsx").exists()]
    if a.limit:
        forms = forms[:a.limit]
    with res_path.open("a") as fh:
        for d in forms:
            if d.name in done:
                continue
            row = {"form": d.name, "provider": a.provider}
            try:
                ex = extract(d / "input.jpg", a.provider)
                cand = d / f"candidate_{tag}.xlsx"
                extraction_to_xlsx(ex, cand)
                s = score_files(d / "golden.xlsx", cand)
                row.update({k: s[k] for k in
                            ("cell_acc", "filled_recall", "blank_acc",
                             "halluc_rate", "wrong_rate", "miss_rate",
                             "header_acc", "extra_rows")})
                row["multiset_all_f1"] = s["multiset"]["all"]["f1"]
                row["per_col"] = {k: v["cell_acc"]
                                  for k, v in s["per_col"].items()}
                row["verdict"] = ex.verdict
                row["flags"] = ex.stats.get("flags")
                row["latency_s"] = ex.stats.get("latency_s")
                row["model_calls"] = ex.stats.get("model_calls")
                row["meta"] = json.loads((d / "meta.json").read_text()) \
                    if (d / "meta.json").exists() else {}
                row["error"] = None
            except Exception as e:  # noqa: BLE001
                row["error"] = f"{type(e).__name__}: {e}"
                traceback.print_exc()
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            rows.append(row)
            print(f"{d.name}: cell_acc={row.get('cell_acc')} "
                  f"verdict={row.get('verdict')} err={row['error']}", flush=True)
    print("\n== SUMMARY ==")
    print(summarize(rows))


if __name__ == "__main__":
    main()
