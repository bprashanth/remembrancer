# 2 · How a paper form comes into existence

Three entry paths, one destination: a **template descriptor** — the single
source of truth holding the columns, their types, their closed value
domains, the row count, and (once rendered) the exact geometry of every
cell in PDF points. Everything downstream — printing, filling, extraction,
scoring, the reviewer's spreadsheet — is expressed against this descriptor.

## Path A — design by hand

The builder UI: title, header fields, columns (serial / int / dec / date /
yes-no / choice-with-domain / name / text), row count. Design-time
guardrails live here: rows must fit the page, columns can't shrink below
writable width, landscape is suggested above 7 columns, choice columns get
their legend printed on the form itself ("N=Normal, MUW=Moderately
underweight…"). The designer's mistakes are refused at design time with a
readable message, not discovered in the field.

## Path B — from a photo of an existing form (model-assisted)

`POST /api/design_from_sample`: upload a photo of the paper form an
organisation already uses; a vision model reads it and proposes the
descriptor — title, header fields, columns with types, and **choice
domains read off the printed legends**. The proposal loads into the
designer for human review; nothing is created unapproved.

Which model does this matters less than you'd think, because it runs once
per form design, never per submission. Measured: the **local untrained
Qwen3-VL-8B produces a faithful, valid proposal** (fully offline path);
gemini-2.5-flash is marginally cleaner when online. The tuned 2B is *not*
used here — it was LoRA-trained to emit transcription rows, not JSON
schemas. Design-time is the one place we spend a bigger model.

## Path C — from a Kobo / ODK / SurveyCTO definition (no model at all)

`eval/xlsform_import.py` reverse-generates the paper form from the XLSForm
the organisation already deployed digitally — deterministic, zero model
calls:

- `settings.form_title` → the printed title
- top-level text/date/integer questions → header fields
- the **repeat group** → the table; each inner question → a column
- `select_one <list>` → a choice column whose **domain comes from the
  choices sheet** — the per-column value domain, for free, exactly the
  thing that most helps a small model disambiguate
- long word codes are auto-abbreviated to single letters when initials are
  unambiguous (male/female/other → M/F/O), with the legend printed on the
  form — which is how real registers are laid out anyway
- `repeat_count` → row count; both ODK's `name` and SurveyCTO's `value`
  choice conventions are handled

Demonstrated on a real public SurveyCTO household roster: imported →
rendered → hand-filled → extracted at 0.967, zero hallucination.

## What rendering adds (every path)

The renderer emits a vector PDF and *records* geometry rather than
inferring it later:

- a **QR form ID** (plus printed human-readable code) — upload-time
  template lookup; nobody ever guesses which form this is from pixels
- **OMR-style anchor marks**: a small filled square beside *every row
  rule* in both margins, a taller anchor bar marking the sequence start,
  and column ticks under the table — the geometry system that makes cheap
  extraction possible (doc 3 and 4)
- printed legends for choice columns and a notation footer ("a dot = 0, a
  tick = yes, leave blank if nothing to record")

## Synthetic filling (data engine for eval and training)

Because geometry is known exactly, `core/fill.py` writes handwriting into
known boxes and the golden spreadsheet is exact **by construction** — no
annotation step, no annotation errors:

- real NIST SD-19 hand-print glyphs, one writer cohort per sheet; ~22%
  pencil (measured as a distinct, harder medium)
- sector lexicons + deliberate out-of-vocabulary tokens
- fill density sampled ~uniform 0.1–1.0, filled top-down like real sheets
  (density was the sibling project's dominant training-data variable)
- field notation: dot=0, ticks, strike-throughs, corrections
  (struck-and-rewritten), skipped cells, occasional margin scribbles that
  the golden deliberately ignores
- phone-camera degradation: perspective, page bow, shadows, augraphy

One template yields unlimited (form image, exact golden) pairs — the same
machinery feeds evaluation today and LoRA training tomorrow.
