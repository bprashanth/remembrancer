#!/usr/bin/env python3
"""Serve the static narrative and save local browser edits back to HTML."""

from __future__ import annotations

import argparse
from datetime import datetime
import html
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import shutil
import tempfile
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "narrative"
BACKUP_ROOT = ROOT / ".remembrancer-backups"
EDITOR_JS_PATH = ROOT / "tools" / "editor.js"
SITE_MANIFEST_PATH = ROOT / "site.json"
MAX_BODY = 2 * 1024 * 1024
EDITOR_INJECTION = '<script src="/__remembrancer/editor.js"></script>'


VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class EditableContentParser(HTMLParser):
    """Find the raw inner HTML of main#content without reserialising the page."""

    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=False)
        self.source = source
        self.line_offsets = [0]
        for line in source.splitlines(keepends=True):
            self.line_offsets.append(self.line_offsets[-1] + len(line))
        self.active_depth = 0
        self.active_start: int | None = None
        self.region: tuple[int, int] | None = None

    def absolute_position(self) -> int:
        line, column = self.getpos()
        return self.line_offsets[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.active_depth:
            if tag not in VOID_ELEMENTS:
                self.active_depth += 1
            return
        attributes = dict(attrs)
        if tag == "main" and attributes.get("id") == "content":
            self.active_depth = 1
            self.active_start = self.absolute_position() + len(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        if not self.active_depth or tag in VOID_ELEMENTS:
            return
        self.active_depth -= 1
        if self.active_depth == 0 and self.active_start is not None:
            self.region = (self.active_start, self.absolute_position())
            self.active_start = None


def replace_content(source: str, replacement: str) -> str:
    parser = EditableContentParser(source)
    parser.feed(source)
    parser.close()
    if parser.region is None:
        raise ValueError("page does not contain main#content")
    start, end = parser.region
    return source[:start] + "\n" + replacement.strip() + "\n" + source[end:]


def inject_local_narratives(source: str) -> str:
    """Add published and draft narratives to the local landing page."""
    manifest = json.loads(SITE_MANIFEST_PATH.read_text(encoding="utf-8"))
    links = []
    for narrative in manifest.get("narratives", []):
        title = html.escape(str(narrative["title"]))
        path = html.escape(str(narrative["path"]), quote=True)
        links.append(
            f'<a href="{path}" data-remembrancer-local="true">{title}</a>'
        )
    if links and "</nav>" in source:
        source = source.replace("</nav>", "\n    " + "\n    ".join(links) + "\n  </nav>", 1)
    return source


def target_for_url(raw_path: str) -> Path:
    path = unquote(urlsplit(raw_path).path).lstrip("/")
    if not path:
        path = "index.html"
    elif path.endswith("/"):
        path += "index.html"
    target = (SITE_ROOT / path).resolve()
    target.relative_to(SITE_ROOT.resolve())
    if target.name != "index.html" or not target.is_file():
        raise ValueError("only existing narrative index.html pages are editable")
    return target


def atomic_write(target: Path, content: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    relative = target.relative_to(SITE_ROOT)
    backup = BACKUP_ROOT / timestamp / relative
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=target.parent, delete=False
    ) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, target)
    return backup


class Handler(SimpleHTTPRequestHandler):
    server_version = "RemembrancerLocal/1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE_ROOT), **kwargs)

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def loopback_client(self) -> bool:
        try:
            return ipaddress.ip_address(self.client_address[0]).is_loopback
        except ValueError:
            return False

    def do_GET(self) -> None:
        if self.path == "/__remembrancer/editor.js":
            body = EDITOR_JS_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/__remembrancer/ping":
            self.send_json(200, {"local_editor": True})
            return
        try:
            target = target_for_url(self.path)
        except (ValueError, OSError):
            super().do_GET()
            return
        source = target.read_text(encoding="utf-8")
        if target == SITE_ROOT / "index.html":
            source = inject_local_narratives(source)
        if "</body>" in source:
            source = source.replace("</body>", EDITOR_INJECTION + "\n</body>", 1)
        body = source.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/__remembrancer/save":
            self.send_json(404, {"error": "not found"})
            return
        if not self.loopback_client():
            self.send_json(403, {"error": "editor accepts loopback clients only"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "invalid content length"})
            return
        if length <= 0 or length > MAX_BODY:
            self.send_json(413, {"error": "invalid or oversized request"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            path = payload.get("path")
            content = payload.get("content")
            if not isinstance(path, str) or not isinstance(content, str):
                raise ValueError("expected path and content")
            if not content.strip():
                raise ValueError("content must not be empty")
            target = target_for_url(path)
            source = target.read_text(encoding="utf-8")
            updated = replace_content(source, content)
            backup = atomic_write(target, updated)
        except (ValueError, OSError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error)})
            return
        self.send_json(
            200,
            {
                "ok": True,
                "path": str(target.relative_to(ROOT)),
                "backup": str(backup.relative_to(ROOT)),
            },
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="listen address (default: 127.0.0.1; 0.0.0.0 is allowed for tunnels)",
    )
    parser.add_argument("--port", type=int, default=6000, help="listen port (default: 6000)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        bind_address = ipaddress.ip_address(args.host)
    except ValueError as error:
        raise SystemExit(f"--host must be an IP address: {error}") from error
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    if bind_address.is_loopback:
        print(f"Remembrancer: http://{args.host}:{args.port}")
    else:
        print(f"Remembrancer is listening on {args.host}:{args.port}.")
        print("WARNING: narrative pages are visible on every interface allowed by your firewall.")
        print("File saves still accept loopback clients only; connect through an SSH tunnel.")
        print(
            f"Laptop command: ssh -N -L {args.port}:127.0.0.1:{args.port} <user>@<server>"
        )
        print(f"Then open: http://127.0.0.1:{args.port}")
    print("Edit/save is ON for loopback clients. Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
