#!/usr/bin/env python3
"""Build the public site, leaving local-review narratives out."""

from __future__ import annotations

import html
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "narrative"
OUTPUT = ROOT / ".netlify-site"
MANIFEST = ROOT / "site.json"


def inject_published_links(source: str, narratives: list[dict]) -> str:
    links = []
    for narrative in narratives:
        if narrative["status"] != "published":
            continue
        title = html.escape(str(narrative["title"]))
        path = html.escape(str(narrative["path"]), quote=True)
        links.append(f'<a href="{path}">{title}</a>')
    if "</nav>" not in source:
        raise ValueError("landing page has no narrative nav")
    return source.replace("</nav>", "\n    " + "\n    ".join(links) + "\n  </nav>", 1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    narratives = manifest["narratives"]
    drafts = [item for item in narratives if item["status"] == "draft"]

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.copytree(
        SOURCE,
        OUTPUT,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    for local_only in ("README.md", "build_evidence_index.py", "sources"):
        target = OUTPUT / local_only
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()

    landing = OUTPUT / "index.html"
    landing.write_text(
        inject_published_links(landing.read_text(encoding="utf-8"), narratives),
        encoding="utf-8",
    )

    for draft in drafts:
        relative = Path(draft["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe draft path: {draft['path']}")
        target = (OUTPUT / relative).resolve()
        target.relative_to(OUTPUT.resolve())
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()

    print(f"built {OUTPUT.relative_to(ROOT)} without {len(drafts)} draft narratives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
