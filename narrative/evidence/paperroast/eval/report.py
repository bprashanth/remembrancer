#!/usr/bin/env python3
"""Comparison table across providers from results/*.jsonl."""
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load(tag):
    p = ROOT / "results" / f"{tag}.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines()]


def summarize(tag):
    rows = [r for r in load(tag) if not r.get("error")]
    if not rows:
        return None
    det = [r for r in rows if r["verdict"] == "detected"]
    out = {
        "tag": tag, "n": len(rows),
        "all_acc": st.mean(r["cell_acc"] for r in rows),
        "det_n": len(det),
        "det_acc": st.mean(r["cell_acc"] for r in det) if det else float("nan"),
        "det_floor": min((r["cell_acc"] for r in det), default=float("nan")),
        "det_halluc": st.mean(r["halluc_rate"] for r in det) if det else float("nan"),
        "hdr": st.mean(r["header_acc"] for r in det) if det else float("nan"),
        "lat": st.mean(r["latency_s"] for r in rows if r.get("latency_s")),
        "calls": st.mean(r["model_calls"] for r in rows
                         if r.get("model_calls") is not None),
    }
    return out


def main():
    tags = sys.argv[1:] or [p.stem for p in (ROOT / "results").glob("*.jsonl")]
    print(f"{'provider':18s} {'n':>3} {'ALLacc':>7} {'det':>4} {'DETacc':>7} "
          f"{'floor':>6} {'halluc':>7} {'hdr':>5} {'lat_s':>6} {'calls':>6}")
    for t in sorted(tags):
        s = summarize(t)
        if not s:
            continue
        print(f"{s['tag']:18s} {s['n']:3d} {s['all_acc']:7.3f} {s['det_n']:4d} "
              f"{s['det_acc']:7.3f} {s['det_floor']:6.2f} {s['det_halluc']:7.3f} "
              f"{s['hdr']:5.2f} {s['lat']:6.1f} {s['calls']:6.1f}")


if __name__ == "__main__":
    main()
