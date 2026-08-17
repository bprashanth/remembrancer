#!/usr/bin/env python3
"""Harvest real XLSForms from public GitHub sources and run the
flattenability census (NEXT_STEPS experiment 1).

Sources: a curated repo list (official/NGO/example collections) plus GitHub
repository-search results for survey-tool keywords. For each repo the git
tree is listed once (recursive) and every plausible .xlsx (5 KB–2 MB, not
starting with ~$) is downloaded and classified with
eval/xlsform_import.analyze().

Unauthenticated GitHub API: ~60 core requests/hr, 10 searches/min — the
script budgets both and degrades gracefully.

Usage:
  .venv/bin/python3 eval/harvest_xlsforms.py [--max-files 60] [--out data/xlsforms/harvest]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from eval.xlsform_import import analyze  # noqa: E402

API = "https://api.github.com"
HDRS = {"Accept": "application/vnd.github+json",
        "User-Agent": "paperroast-harvest"}

CURATED = [
    "getodk/xlsform-template",
    "XLSForm/pyxform",
    "stats4sd/xlsform_examples",
    "bkkhiang/SurveyCTOBuilder360_HHRoster",
    "kobotoolbox/kobocat",
    "hotosm/hotosm-forms",
    "OpenSRP/opensrp-forms",
]

SEARCHES = [
    "xlsform survey",
    "kobotoolbox forms",
    "surveycto form xlsx",
    "odk forms health survey",
    "xlsform agriculture questionnaire",
]


def gh(url, **kw):
    r = requests.get(url, headers=HDRS, timeout=30, **kw)
    if r.status_code == 403:
        return None                                   # rate limited
    if r.status_code != 200:
        return None
    return r.json()


def repo_xlsx(full_name):
    """List candidate xlsx paths in a repo via one recursive tree call."""
    meta = gh(f"{API}/repos/{full_name}")
    if not meta:
        return []
    branch = meta.get("default_branch", "main")
    tree = gh(f"{API}/repos/{full_name}/git/trees/{branch}?recursive=1")
    if not tree:
        return []
    out = []
    for it in tree.get("tree", []):
        p = it.get("path", "")
        if not p.lower().endswith((".xlsx", ".xls")):
            continue
        name = p.rsplit("/", 1)[-1]
        if name.startswith("~$"):
            continue
        size = it.get("size") or 0
        if not 5_000 <= size <= 2_000_000:
            continue
        out.append((p, size,
                    f"https://raw.githubusercontent.com/{full_name}/{branch}/{p}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-files", type=int, default=60)
    ap.add_argument("--max-per-repo", type=int, default=6)
    ap.add_argument("--out", default="data/xlsforms/harvest")
    a = ap.parse_args()
    out = Path(__file__).parent.parent / a.out
    out.mkdir(parents=True, exist_ok=True)

    repos = list(CURATED)
    for q in SEARCHES:
        res = gh(f"{API}/search/repositories",
                 params={"q": q, "per_page": 6, "sort": "stars"})
        time.sleep(7)                                  # search rate limit
        if not res:
            continue
        for it in res.get("items", []):
            fn = it["full_name"]
            if fn not in repos:
                repos.append(fn)

    print(f"scanning {len(repos)} repos", flush=True)
    rows = []
    seen_names = set()
    n = 0
    for fn in repos:
        if n >= a.max_files:
            break
        cands = repo_xlsx(fn)
        time.sleep(1.2)
        for p, size, url in cands[:a.max_per_repo]:
            if n >= a.max_files:
                break
            name = p.rsplit("/", 1)[-1]
            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())
            dst = out / f"{fn.replace('/', '__')}__{name}"
            try:
                r = requests.get(url, timeout=60)
                r.raise_for_status()
                dst.write_bytes(r.content)
            except Exception as e:  # noqa: BLE001
                print(f"  DL FAIL {url}: {e}", flush=True)
                continue
            rep = analyze(dst)
            rep["repo"] = fn
            rep["path"] = p
            rep["size"] = size
            rows.append(rep)
            n += 1
            print(f"  [{n}] {fn}/{name}: {rep['verdict']} "
                  f"{'; '.join(rep.get('reasons', []))[:60]}", flush=True)

    (out / "census.json").write_text(json.dumps(rows, indent=2))
    from collections import Counter
    c = Counter(r["verdict"] for r in rows)
    print("\n== CENSUS ==")
    for k, v in c.most_common():
        print(f"  {k:16s} {v}")
    print(f"total {len(rows)} -> {out}/census.json")


if __name__ == "__main__":
    main()
