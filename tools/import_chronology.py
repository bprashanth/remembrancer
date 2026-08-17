#!/usr/bin/env python3
"""Import a producer's Markdown chronology with a provenance manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
IMPORT_ROOT = ROOT / "chronology"
SOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}(?:-[a-z0-9-]+)?\.md$")
LEGACY_RE = re.compile(r"^\d{2,4}[-_].+\.md$")


def git_value(path: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, target)
    finally:
        temporary_path.unlink(missing_ok=True)


def atomic_json(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=target.parent, delete=False
    ) as temporary:
        json.dump(payload, temporary, indent=2, ensure_ascii=False)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy a chronology/ snapshot into Remembrancer."
    )
    parser.add_argument("source", type=Path, help="producer chronology directory")
    parser.add_argument("--source-id", required=True, help="stable lowercase import id")
    parser.add_argument("--repo", help="public repository URL; inferred from git when omitted")
    parser.add_argument(
        "--prune",
        action="store_true",
        help="remove imported Markdown no longer present upstream",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    if not source.is_dir():
        raise SystemExit(f"chronology directory not found: {source}")
    if not SOURCE_ID_RE.fullmatch(args.source_id):
        raise SystemExit("--source-id must contain lowercase letters, digits and hyphens")

    files = sorted(path for path in source.glob("*.md") if path.is_file())
    entries = [path for path in files if path.name.lower() != "readme.md"]
    if not entries:
        raise SystemExit(f"no chronology Markdown entries found in {source}")

    warnings: list[str] = []
    for path in entries:
        if not (TIMESTAMP_RE.fullmatch(path.name) or LEGACY_RE.fullmatch(path.name)):
            warnings.append(
                f"{path.name}: non-standard name; preserved in lexical order"
            )
        if not path.read_text(encoding="utf-8").lstrip().startswith("#"):
            warnings.append(f"{path.name}: entry does not begin with a Markdown heading")

    git_root_value = git_value(source, "rev-parse", "--show-toplevel")
    git_root = Path(git_root_value) if git_root_value else None
    revision = git_value(source, "rev-parse", "HEAD")
    repository = args.repo
    if not repository and git_root:
        repository = git_value(git_root, "remote", "get-url", "origin")

    target = (IMPORT_ROOT / args.source_id).resolve()
    target.relative_to(IMPORT_ROOT.resolve())
    target.mkdir(parents=True, exist_ok=True)

    source_names = {path.name for path in files}
    if args.prune:
        for old_file in target.glob("*.md"):
            if old_file.name not in source_names:
                old_file.unlink()
                print(f"pruned  {old_file.relative_to(ROOT)}")

    manifest_files = []
    for path in files:
        destination = target / path.name
        atomic_copy(path, destination)
        manifest_files.append(
            {
                "name": path.name,
                "sha256": digest(path),
                "bytes": path.stat().st_size,
            }
        )
        print(f"copied  {destination.relative_to(ROOT)}")

    source_path = str(source)
    if git_root:
        try:
            source_path = str(source.relative_to(git_root))
        except ValueError:
            pass

    manifest = {
        "protocol_version": 1,
        "source_id": args.source_id,
        "repository": repository,
        "source_path": source_path,
        "source_revision": revision,
        "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ordering": "lexical filename order",
        "files": manifest_files,
        "warnings": warnings,
    }
    atomic_json(target / "_source.json", manifest)
    print(f"wrote   {(target / '_source.json').relative_to(ROOT)}")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

