#!/usr/bin/env python3
"""Regenerate the evidence browser pages. Run after copying new runs in:
   cd narrative && python3 build_evidence_index.py
Netlify serves no directory listings, so every runs/ folder needs a real index.html."""
import html, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence")
ASSETS = [
 ("why1-agents-as-answerers","Naive questions, four question kinds","What happens when you ask plainly and trust the answer"),
 ("why2-repeatability","Same question, three times","The source lottery"),
 ("why3-hard-sources","Answers buried in PDFs, portals, archives","Does diligence hold when the source is hard"),
 ("why4-prodding","Pressure turn: are you sure?","Does pushing back make models more honest or less"),
 ("why5-measure-what-where","What to measure, where, with what budget","Estimation, coordinates, satellite"),
 ("why6-our-stack","The same questions through our own stack","Determinism and auditable failure"),
 ("why7-expertise","The same questions, expert phrasing","What domain knowledge buys"),
]
CSS = """body{background:#fff;color:#000;font:16px/1.6 Arial,Helvetica,sans-serif;margin:0}
.w{max-width:860px;margin:0 auto;padding:52px 22px 80px}
h1{font-size:31px;margin:.2em 0}h2{font-size:17px;margin:26px 0 6px;color:#000}
a{color:#000;text-decoration:underline;text-underline-offset:3px}
p{color:#000;max-width:66ch}
table{border-collapse:collapse;width:100%;margin-top:20px;font-size:15px}
td,th{text-align:left;padding:9px 12px 9px 0;border-bottom:1px solid #000;vertical-align:top}
th{font-size:12px;text-transform:uppercase;color:#000}
td.n{font-family:ui-monospace,Menlo,monospace}
.s{font-size:13px;color:#000;margin-top:3px}
.files{display:flex;flex-wrap:wrap;gap:8px 16px;font-family:ui-monospace,Menlo,monospace;font-size:13px;margin:6px 0 2px}
code{background:#fff;border:1px solid #000;padding:1px 6px;font-size:13px}"""

def page(title, body):
    return f"<title>{html.escape(title)}</title><style>{CSS}</style><div class=\"w\">{body}</div>"

def run_files(d):
    out = []
    rd = os.path.join(ROOT, d, "runs")
    if not os.path.isdir(rd): return out
    for sub in sorted(os.listdir(rd)):
        p = os.path.join(rd, sub)
        if os.path.isdir(p):
            fs = sorted(f for f in os.listdir(p) if f.endswith((".md",".json",".txt")))
            out.append((sub, [(f, f"{sub}/{f}") for f in fs]))
        elif sub.endswith((".md",".json",".txt")):
            out.append(("(top level)", [(sub, sub)]))
    return out

total = 0
rows = []
for d, title, sub in ASSETS:
    if not os.path.isdir(os.path.join(ROOT, d)): continue
    groups = run_files(d)
    n = sum(len(fs) for _, fs in groups)
    total += n
    # per-asset runs index
    body = [f'<p><a href="../../">Index of runs</a></p><h1>{html.escape(title)}</h1>',
            f'<p>{html.escape(sub)}. {n} run files. Each file is one model answering one question, saved exactly as returned.</p>']
    for model, fs in groups:
        body.append(f"<h2>{html.escape(model)}</h2><div class='files'>" +
                    " ".join(f'<a href="{html.escape(u)}">{html.escape(f)}</a>' for f, u in fs) + "</div>")
    os.makedirs(os.path.join(ROOT, d, "runs"), exist_ok=True)
    open(os.path.join(ROOT, d, "runs", "index.html"), "w").write(page(title + " - runs", "".join(body)))
    docs = sorted(f for f in os.listdir(os.path.join(ROOT, d))
                  if f.endswith((".md",".json",".py")) and os.path.isfile(os.path.join(ROOT, d, f)))
    links = " ".join(f'<a href="{d}/{html.escape(f)}">{html.escape(f)}</a>' for f in docs)
    rows.append(f"""<tr><td><b>{html.escape(title)}</b><div class="s">{html.escape(sub)}</div>
      <div class="files">{links}</div></td><td class="n">{n}</td>
      <td><a href="{d}/runs/">browse runs</a></td></tr>""")

paperroast = os.path.join(ROOT, "paperroast")
paperroast_link = ""
if os.path.isdir(paperroast):
    result_dir = os.path.join(paperroast, "results")
    result_files = sorted(f for f in os.listdir(result_dir)
                          if f != "index.html" and os.path.isfile(os.path.join(result_dir, f)))
    result_links = " ".join(
        f'<a href="{html.escape(f)}">{html.escape(f)}</a>' for f in result_files
    )
    open(os.path.join(result_dir, "index.html"), "w").write(page(
        "Form data results",
        '<p><a href="../">Form data evidence</a></p><h1>Benchmark results</h1>'
        f'<div class="files">{result_links}</div>'
    ))
    open(os.path.join(paperroast, "index.html"), "w").write(page(
        "Form data evidence",
        '<p><a href="../">All evidence</a></p><h1>Form data evidence</h1>'
        '<p>Code, small benchmark data and results copied into Remembrancer.</p>'
        '<div class="files"><a href="README.md">snapshot note</a> '
        '<a href="FINDINGS.md">findings</a> '
        '<a href="data/xlsforms/harvest/census.json">form census</a> '
        '<a href="data/cellbench/manifest.json">cell benchmark manifest</a> '
        '<a href="eval/cellbench.py">cell benchmark code</a> '
        '<a href="eval/xlsform_import.py">XLSForm import code</a> '
        '<a href="results/">results</a></div>'
    ))
    paperroast_link = '<p><a href="paperroast/">Form data evidence</a></p>'

open(os.path.join(ROOT, "index.html"), "w").write(page("Index of runs", f"""
<p><a href="../">Back to the field notes</a></p>
<h1>Index of runs</h1>
{paperroast_link}
<p>This is the raw material behind the five findings, {total} run files in total. Nothing here is edited after
the fact. Each folder holds the question bank (with the answers I verified by hand before running anything),
the collector script, one file per model answer, and a results write-up that includes the parts where my
expectations turned out wrong.</p>
<p>How to read a run file: the question sits at the top, then the model's full answer as returned. The score
for each answer and the one line reason behind it live in <code>scoring.json</code> or the folder's
<code>RESULTS.md</code>.</p>
<table><tr><th>benchmark</th><th>run files</th><th></th></tr>{''.join(rows)}</table>
<p class="s" style="margin-top:26px">Protocol: cursor agent CLI, plain settings, web access on, one isolated
container per run with an empty working directory, so no run could see our files or another run's downloads.
Models: claude-4.6-opus-high, gpt-5.4-medium, cursor-grok-4.5-medium, gemini-3.5-flash. Our own stack (why6):
Qwen3.5-9B + LoRA adapter-003 + the query algebra + connectors.</p>"""))
print(f"wrote index + {len(rows)} runs pages, {total} run files")
