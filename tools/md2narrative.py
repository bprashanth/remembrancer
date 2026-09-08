#!/usr/bin/env python3
"""Turn a producer-repo markdown narrative into a published site page.

Usage:
  python3 tools/md2narrative.py SOURCE.md narrative/<slug>/ --title "Page title" [--sub "Subtitle"]

Writes narrative/<slug>/index.html in the house style. The markdown stays the
source of truth in the producer repo; rerun this after editing it. The first
"# " heading becomes the subtitle unless --sub is given. Supported markdown:
## headings, paragraphs, > quotes, numbered and * lists, [links](url),
`code`, _italics_.
"""
import argparse, html, pathlib, re

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a class="ev" href="\2">\1</a>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\b_([A-Za-z][^_]*)_\b', r'<i>\1</i>', t)
    return t

def convert(md):
    lines = md.split("\n")
    out, i, mode = [], 0, [None]
    def close():
        if mode[0] == "ul": out.append("</ul>")
        if mode[0] == "ol": out.append("</ol>")
        if mode[0] == "p": out.append("</p>")
        mode[0] = None
    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith("## "):
            close(); out.append(f"<h2>{inline(ln[3:])}</h2>")
        elif ln.startswith(">"):
            close(); out.append('<div class="quote">')
            buf = []
            while i < len(lines) and lines[i].rstrip().startswith(">"):
                t = lines[i].rstrip()[1:].strip()
                buf.append("</p><p>" if t == "" else inline(t))
                i += 1
            out.append("<p>" + " ".join(buf).replace(" </p><p> ", "</p><p>") + "</p></div>")
            continue
        elif re.match(r'^\d+\. ', ln):
            if mode[0] != "ol": close(); out.append('<ol class="obs">'); mode[0] = "ol"
            item = [re.sub(r'^\d+\. ', '', ln)]
            while i + 1 < len(lines) and lines[i+1].startswith("   ") and lines[i+1].strip():
                i += 1; item.append(lines[i].strip())
            out.append(f"<li>{inline(' '.join(item))}</li>")
        elif ln.startswith("* "):
            if mode[0] != "ul": close(); out.append('<ul class="obs">'); mode[0] = "ul"
            item = [ln[2:]]
            while i + 1 < len(lines) and lines[i+1].startswith("  ") and not lines[i+1].lstrip().startswith("* ") and lines[i+1].strip():
                i += 1; item.append(lines[i].strip())
            out.append(f"<li>{inline(' '.join(item))}</li>")
        elif ln.strip() == "":
            close()
        else:
            if mode[0] != "p": close(); out.append("<p>"); mode[0] = "p"
            else: out.append(" ")
            out.append(inline(ln))
        i += 1
    close()
    return "\n".join(out)

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#ffffff">
<title>%(title)s</title>
<style>
*{box-sizing:border-box}
html,body{margin:0}
body{background:#fff;color:#000;font:17px/1.6 Arial,Helvetica,sans-serif}
a{color:#000;text-underline-offset:3px}
#content{max-width:800px;margin:0 auto;padding:58px 22px 80px}
h1{font-size:clamp(28px,5vw,46px);line-height:1.15;margin:.4em 0;text-wrap:balance;font-weight:700}
h2{font-size:clamp(22px,3.4vw,30px);line-height:1.2;margin:1.2em 0 .4em;text-wrap:balance}
p{max-width:64ch}
.sub{font-size:18px;max-width:60ch}
.tag{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;letter-spacing:.14em;text-transform:uppercase}
code{font-family:ui-monospace,Menlo,monospace;font-size:14.5px}
ol.obs,ul.obs{max-width:66ch;padding-left:1.3em}
ol.obs li,ul.obs li{margin:.7em 0}
.quote{border-left:2px solid #000;padding:2px 0 2px 14px;margin:12px 0;font-size:15.5px;max-width:62ch}
a.ev{text-decoration:underline;text-underline-offset:3px}
.home{position:fixed;top:14px;left:16px;z-index:8;color:#000;font:12px/1.3 ui-monospace,Menlo,monospace;padding:7px 9px;background:#fff}
@media (max-width:640px){
  body{font-size:15.5px}
  #content{padding:50px 16px 60px}
  .sub{font-size:16px}
}
</style>
</head>
<body>
<a class="home" href="../">Index</a>
<main id="content">
<div class="tag">Field notes</div>
<h1>%(title)s</h1>
<p class="sub">%(sub)s</p>
%(body)s
</main>
</body>
</html>
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source"); ap.add_argument("dest")
    ap.add_argument("--title", required=True); ap.add_argument("--sub", default=None)
    a = ap.parse_args()
    md = pathlib.Path(a.source).read_text()
    m = re.match(r'^# (.+)\n', md)
    sub = a.sub if a.sub is not None else (m.group(1) if m else "")
    if m: md = md[m.end():]
    dest = pathlib.Path(a.dest); dest.mkdir(parents=True, exist_ok=True)
    (dest / "index.html").write_text(PAGE % {"title": html.escape(a.title), "sub": inline(sub), "body": convert(md)})
    print(f"wrote {dest/'index.html'}")

if __name__ == "__main__":
    main()
