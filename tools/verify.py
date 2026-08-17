#!/usr/bin/env python3
"""Check site structure, registry paths and imported chronology manifests."""

from __future__ import annotations

from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "narrative"
errors: list[str] = []
PUBLISHED_PAGES = {
    SITE / "index.html",
    SITE / "field-notes" / "index.html",
    SITE / "form-data" / "index.html",
    SITE / "form-data-deep" / "index.html",
    SITE / "sources" / "index.html",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.sections = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = (values.get("class") or "").split()
        if tag == "section" and "entry" in classes:
            self.sections += 1
        identifier = values.get("id")
        if identifier:
            if identifier in self.ids:
                errors.append(f"duplicate id {identifier!r}")
            self.ids.add(identifier)
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")


def check_page(path: Path) -> None:
    parser = PageParser()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
    except Exception as error:
        errors.append(f"{path.relative_to(ROOT)}: HTML parse failed: {error}")
        return
    for href in parser.links:
        if path in PUBLISHED_PAGES and "://" in href:
            errors.append(
                f"{path.relative_to(ROOT)}: external citation {href}; copy evidence locally"
            )
            continue
        link_path = urlsplit(href).path
        if not link_path or link_path.startswith("/") or "://" in href:
            continue
        target = (path.parent / link_path).resolve()
        if target.is_dir():
            target /= "index.html"
        if not target.is_file():
            errors.append(f"{path.relative_to(ROOT)}: broken link {href}")
    print(f"page     {path.relative_to(ROOT)} ({parser.sections} sections)")


def check_registry() -> None:
    registry = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    for narrative in registry.get("narratives", []):
        for page in narrative.get("pages", []):
            if not (ROOT / page).is_file():
                errors.append(f"sources.json: missing page {page}")
        chronology = narrative.get("chronology")
        if chronology and not (ROOT / chronology / "_source.json").is_file():
            errors.append(f"sources.json: chronology lacks _source.json: {chronology}")
        evidence = narrative.get("evidence")
        if not evidence:
            errors.append(f"sources.json: {narrative.get('id')} has no evidence")
        elif not (ROOT / evidence.get("path", "")).is_dir():
            errors.append(
                f"sources.json: missing local evidence {evidence.get('path')}"
            )
        print(f"source   {narrative.get('id')}")


def check_site_manifest() -> None:
    manifest = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    seen: set[str] = set()
    for narrative in manifest.get("narratives", []):
        title = narrative.get("title")
        path_value = narrative.get("path")
        status = narrative.get("status")
        if not isinstance(path_value, str):
            errors.append(f"site.json: {title} has no path")
            continue
        relative = Path(path_value)
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"site.json: unsafe path {path_value}")
            continue
        normal = relative.as_posix().rstrip("/") + "/"
        if normal in seen:
            errors.append(f"site.json: duplicate path {normal}")
        seen.add(normal)
        if status not in {"published", "draft"}:
            errors.append(f"site.json: {title} has invalid status {status}")
        if not (SITE / relative / "index.html").is_file():
            errors.append(f"site.json: missing narrative {path_value}")
        print(f"site     {str(status):9} {normal}")


def check_imports() -> None:
    for manifest_path in sorted((ROOT / "chronology").glob("*/_source.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest.get("files", []):
            path = manifest_path.parent / item["name"]
            if not path.is_file():
                errors.append(f"{manifest_path.relative_to(ROOT)}: missing {item['name']}")
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != item["sha256"]:
                errors.append(f"{path.relative_to(ROOT)}: differs from import manifest")
        print(f"import   {manifest_path.parent.relative_to(ROOT)}")


def main() -> int:
    for path in sorted(SITE.glob("**/index.html")):
        check_page(path)
    check_site_manifest()
    check_registry()
    check_imports()
    if errors:
        print("\nVerification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
