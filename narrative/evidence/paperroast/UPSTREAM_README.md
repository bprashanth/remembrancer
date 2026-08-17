# paperroast

Form builder + detector for hand-filled paper forms, built around one idea:
**if you designed the form, extraction is a geometry problem first and a
vision-model problem second.**

Templates carry a QR form ID and printed OMR-style anchor marks. Extraction
rectifies each row off the marks, asks a small local VLM one bounded question
per written row (with the column value domains), anchors the answers to the
ink, and emits a spreadsheet **in the same grid as the paper** — blanks
included — with a deterministic verdict: `detected` / `review` / `reject`.

Results, method, and everything that failed: **[FINDINGS.md](FINDINGS.md)**.
Project constraints and context: [BRIEF.md](BRIEF.md).

## Run the app

```
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 7500
```

- **Design** — build a form (or upload a photo of an existing paper form and
  let a model propose the template), preview, download the printable PDF,
  generate synthetic hand-filled samples.
- **Templates** — gallery of saved templates.
- **Verify** — upload a filled photo; side-by-side aligned image vs
  extracted grid, flagged cells highlighted, click any cell for a zoomed
  crop + correction box, export xlsx / corrected CSV.

Needs the local vLLM 2B on `:8010` (see `core/vlm.py` for providers).

## Layout

```
core/       template.py (descriptor)  render.py (PDF+fiducials)
            fill.py (synthetic filler)  extract.py (detector)
            score.py (positional metric)  vlm.py (model client)
app/        FastAPI backend + static frontend
eval/       gen_corpus.py  run_eval.py  report.py
            calibrate_ink.py  ablate_domains.py
data/       templates/ (descriptors+PDFs)  forms/ (eval corpus)  specs/
results/    per-provider jsonl
tests/      scorer tests (run: .venv/bin/python3 tests/test_score.py)
```
