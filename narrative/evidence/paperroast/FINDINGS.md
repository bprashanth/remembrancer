# paperroast — findings

Metric: **positional cell accuracy** (`core/score.py`) — fraction of template
cells whose extracted value equals the golden at the same (row, col), blanks
included. This is the metric the BRIEF demanded; the token-multiset score is
computed but never steered on (the scorer's unit test proves the BRIEF's
linearised-failure example scores multiset-F1 >0.75 while cell_acc <0.15).

Corpus: 48 synthetic forms = 6 templates (PHC immunization, OPD register,
school attendance, exam marks, SHG ledger, kharif crop survey — zero ecology)
× 8 seeds; real NIST SD-19 ink (one writer cohort per sheet, ~22% pencil),
sector lexicons + OOV tokens, fill density ~U(0.1, 1.0), augraphy + phone-photo
degradation (perspective, page bow, shadows). Goldens exact by construction.

## The system

Builder (template descriptor: columns, types, closed domains, exact geometry;
QR form ID) → **printed OMR-style fiducials** (marks beside every row rule,
tall anchor bar, column ticks) → detector:

1. QR → template lookup (no pixel fingerprinting).
2. ORB + numpy thin-plate-spline alignment to the blank render.
3. Fiducial detection: margin blob candidates → joint left/right shift
   scoring (1-D Hough + anchor bar) → sequential mark tracking with adaptive
   pitch → per-row perspective quads; optional TPS refinement on found marks.
4. Per-band rectification + in-band rule straightening + column-edge snap.
5. Ink map: local-contrast strokes minus the KNOWN printed layer,
   component-filtered. Calibrated (`eval/calibrate_ink.py`): FN/FP ≈ 1% on
   geometry-trusted forms at cell-fraction threshold 0.004.
6. One model call per inked row (headers + per-column value domains in the
   prompt, one CSV line out, length-capped, repetition penalty 1.05);
   **ink-guided field re-anchoring** (the ink map supplies positions, the
   model supplies ordered values — kills CSV field-shift, the failure that
   made the sibling's output unusable); per-cell fallback when counts
   disagree; per-cell always for int/dec columns with **band-vs-cell
   two-pass disagreement flagged** (a wrong digit is domain-valid — only
   self-disagreement catches it).
7. Deterministic verdict: **detected / review / reject** (fiducial
   integrity ≥ 0.95 to trust geometry; serial-mismatch; malformed rows;
   domain violations; unread ink; two-pass disagreement). Rejection happens
   BEFORE any model call when anchors can't be found.

## Headline: architecture-controlled comparison (identical pipeline, only the model swapped)

48 forms, v4 pipeline. "DET" = the auto-accept bucket.

| model | ALL acc | det n | DET acc | DET floor | DET halluc | s/form |
|---|---|---|---|---|---|---|
| **tuned Qwen3-VL-2B (local)** | 0.725 | 17 | **0.943** | 0.83 | **0.002** | **10.4** |
| Qwen3-VL-8B fp8 (local, untrained) | 0.777 | 14 | 0.938 | 0.78 | 0.004 | 24.5 |
| Qwen3-VL-8B (OpenRouter) | 0.780 | 15 | 0.938 | 0.86 | 0.001 | 40.2 |
| Qwen3-VL-32B (OpenRouter) | 0.792 | 19 | 0.943 | 0.83 | 0.001 | 46.1 |
| gemini-2.5-flash | 0.755 | 19 | 0.952 | 0.87 | 0.002 | 149.6 |

**Finding 1 — structure beats scale.** In the auto-accept bucket the 2B
matches the 8B and the 32B (0.94), at 2.4–4.5× lower latency, fully offline.
The constraint machinery (known geometry, ink anchoring, domains, bounded
outputs) does the work that scale otherwise buys.

**Finding 2 — verdicts are a geometry property, not a model property.**
2B and 32B agree on 43/45 verdicts. Refusal can therefore be decided
cheaply and identically regardless of which model will read the form.

**Finding 3 — escalation is for the review bucket, and it helps but does
not rescue.** On the 2B's 31 review forms: 2B 0.61 acc / 0.36 halluc;
local-8B 0.68 / 0.15; 32B 0.70 / 0.12. Policy: detected → 2B result;
review → bigger-model draft + human per-cell correction (the UI highlights
flagged cells with zoom-and-correct); reject → retake the photo.

**Finding 4 — value domains buy +5pp on code columns for the 2B**
(choice 0.727→0.777, Y/N 0.854→0.903, `eval/ablate_domains.py`) *on top of*
a structured path that already constrains reads to single rows. Per-column,
domain-constrained columns are the best in the corpus: Subject 0.98,
Sex 0.96, Grade/Pass 0.95, Vaccine 0.94, Irrigated 1.00.

**Finding 5 — long digit strings are the 2B's real weakness** (5–6-digit
rupee amounts: 0.62 band-mode → 0.72 per-cell). Designer guardrail: prefer
per-digit boxes for amounts, or accept per-cell review. Two-pass
disagreement flags most residual digit errors for human eyes.

**Finding 6 — pencil requires a contrast-only ink detector.** Absolute
darkness thresholds silently erased pencil (strokes at gray 195–235 on
degraded photos); local contrast (bg−a > 26) separates filled vs empty
cells at p99.5 ≈ 60 vs ≈ 1.

## What did NOT work (measured, so nobody repeats it)

- Global homography alone: page bow leaves rows tens of px off at the
  bottom of the page.
- Table-corner pinning: L-junction responses are weak; bolder interior
  crossings hijack the fit (off-by-one-row, silent).
- Quadratic mesh fitted on line-crossing detections: under-corrects exactly
  where detection fails.
- Per-mark windowed fiducial search: identity slips a row when residual
  exceeds half the pitch. Sequence-level matching (tall anchor bar + joint
  left/right scoring + sequential tracking) fixed it.
- Rule-shape heuristics in the ink mask: either passed sloped rules or ate
  genuine '1's/dashes. Subtracting the known printed layer won.
- A single blended "fraction flagged" verdict: over-flagged sparse forms.
  Per-signal thresholds calibrated on measured accuracy work.

## Guardrails a user actually sees (all realistic; none restrict handwriting)

- "Only N% of the form's anchor marks were found — retake flatter, closer,
  fully in frame" (pre-model rejection).
- Printed legends for code columns on the form itself.
- Design-time enforcement: rows must fit the page, minimum writable column
  widths, landscape suggested above 7 columns.
- Margin scribbles are ignored by construction; struck-through cells read
  as empty; a lone dot reads as 0 (printed on the form footer).

## Reproduce

```
.venv/bin/python3 tests/test_score.py                 # metric sanity
.venv/bin/python3 eval/gen_corpus.py --seeds 8        # corpus
.venv/bin/python3 eval/calibrate_ink.py               # CV calibration (no model)
.venv/bin/python3 eval/run_eval.py --provider local-2b --tag local-2b-v4
.venv/bin/python3 eval/report.py                      # comparison table
.venv/bin/python3 eval/ablate_domains.py              # domain ablation
.venv/bin/uvicorn app.main:app --port 7500            # the product UI
```

Local models: tuned 2B on :8010 (shared vLLM container), 8B fp8 via
`form-idable/benchmarks/wide/gpu_run.sh` on :8011 (see BRIEF §7 host rules).

## Design Q&A

**What are the OMR fiducial marks actually for?** They convert "where is
every cell in this warped photo" from an inference problem into a lookup.
A phone photo of a curled page is not projective; every generic recovery we
tried (homography, corner pinning, quadratic meshes on detected crossings)
failed measurably. The printed marks give: (1) per-row anchors on both
margins → each row is rectified by its own quad, immune to page bow;
(2) sequence identity via the tall anchor bar → the off-by-one-row failure
class is eliminated; (3) a free confidence signal — the fraction of marks
found IS the refusal criterion, computed before any model call. They cost a
7×5 pt square per row in the margins and constrain the writer not at all.

**Would OCR specialists (olmOCR-2, Chandra, Nanonets-OCR2) help?** Probably
not where it matters, for a structural reason: those models are trained to
convert whole documents into markdown/HTML — their strength is layout
parsing, reading order and table structure, which this pipeline already
gets deterministically from the template + marks. Inside our loop the model
only ever sees one pre-rectified row (or one cell) and must follow output
contracts ("one CSV line with N fields", "one of P, A, L, or EMPTY") — and
the sibling project's data point on this class is cautionary: DeepSeek-OCR
3B scored the highest precision of any local model on clean forms but could
not follow notation instructions (tallies/checkbox semantics lost) and fell
to 0.66 on real scans. The interesting narrow bet is their handwriting
head: if olmOCR-2/Chandra read messy ink better than Qwen3-VL, they would
lift the `wrong` rate on name/amount cells. They are all servable by vLLM /
OpenAI-compatible endpoints, so testing one is a one-line provider entry in
`core/vlm.py` plus a sweep — a cheap future experiment. What they cannot
replace is the geometry, the ink anchoring, or the refusal logic, which is
where this system's accuracy actually comes from.

**How does design-from-sample work, and does it need a big model?** It is a
one-off, design-time call (`POST /api/design_from_sample`): the model sees a
photo of an existing form and emits the template spec JSON (title, header
fields, columns with types, choice domains read from printed legends); the
spec is validated by `core/template.from_spec` and loaded into the designer
for HUMAN review — nothing is created without a person approving it.
Measured: the **local untrained 8B produces a faithful, valid proposal**
(tested on the OPD register — title, all headers, serial, Sex M/F domain
with legend), so the flow works fully offline; gemini-flash is slightly
cleaner when online. The tuned 2B is NOT used for this: it was fine-tuned to
emit transcription rows, not JSON schemas, and this is the one place a
bigger model is the right default — it runs once per form design, not once
per submission. Detection remains 2B-only.

**What about non-flat forms — multiple subtables?** Today the descriptor is
one header block + one table, which covers the large majority of field
registers. The approach does not require flattening everything: the fiducial
scheme is per-region (each banded region gets its own mark pairs and its own
anchor bar), so a multi-table descriptor is an extension of the same
machinery — regions extracted independently, one grid sheet per region.
That said, part of the product thesis is that the builder SHOULD nudge
designers toward regular structures: a "two side-by-side code grids" sheet
(like the sibling's germination form) is strictly harder for writer, model
and reviewer alike than the same data as two pages or two stacked tables,
and the builder is the right place to encode that preference. Flattening is
a recommended guardrail, not a requirement of the method.

**Were the eval forms derived from real Kobo/ODK surveys?** The v4 corpus
was not — it uses six sector archetypes patterned on the sibling project's
field-validated social-sector layouts (BRIEF source (a)/(c)). Source (b) is
now wired: `eval/xlsform_import.py` reverse-generates a paper register from
a real XLSForm — settings→title, top-level questions→header fields, the
repeat group→the table, `select_one` lists→choice domains (with automatic
single-letter code abbreviation + printed legend, the way real registers
are laid out; handles ODK `name` and SurveyCTO `value` choice columns).
Demonstrated end-to-end on a real public SurveyCTO household-roster XLSForm
(github.com/bkkhiang/SurveyCTOBuilder360_HHRoster): imported → rendered →
hand-filled → extracted at **cell_acc 0.967, zero hallucination, verdict
detected**. Growing the corpus from harvested real XLSForms is now a
one-command-per-form exercise.

## Trained 2B vs trained 8B (the BRIEF's open question, all four quadrants)

form-idable finished its 8B LoRA (`merged-8b-v4`, same recipe as the 2B);
both trained models ran through the identical structured harness on the
same 49 forms (paired), plus the 240-crop cell benchmark:

| through this harness | ALL acc | detected acc | headers | s/form |
|---|---|---|---|---|
| trained 2B | 0.731 | 0.942 | 0.55 | 23* |
| untrained 8B | 0.777 | 0.938 | 0.54 | 25 |
| **trained 8B** | **0.780** | 0.946 | 0.69 | 48* |

*\*both local servers shared the GPU during this run; standalone the 2B is
~10 s/form.*

Paired findings (n=49; 8bT beats 2bT on 32 forms, ties 13, loses 4):

1. **The auto-accept bucket stays saturated** — 0.942 vs 0.946 (and 0.965
   vs 0.947 on the both-detected subset): at ≈0.94–0.96, geometry +
   domains + bounded reads leave models nothing to differ on.
2. **Scale, not training, helps off the trusted path.** On the 2B's
   review bucket the trained 8B scores 0.666 — statistically identical to
   the *untrained* 8B's 0.675. The 8B's +0.05 ALL-acc advantage is
   general capability, and LoRA training added nothing there.
3. **Training the 8B bought language, not perception**: headers 0.54→0.69
   and free-text cells 0.817 (vs 2B's 0.700) on the cell benchmark, where
   it posts the best local score overall (0.863, edging gemini's 0.858
   within noise). Names/amounts/codes: tied with the trained 2B.
4. **Training the 2B was existential** (unusable → 0.94-detected);
   **training the 8B was cosmetic** (+0.003 ALL). Same recipe, opposite
   value — matching form-idable's prediction that the 2B's gain came from
   capability it lacked, which the 8B already had.

Deployment recipe that falls out: **trained 2B as the detected-tier
workhorse** (2× faster, same accuracy where accuracy is trusted), **8B —
training optional — as the review-tier reader and header/free-text
specialist**, both fully local. Escalate beyond 8B only for review drafts
when online.

## Experiment 1 — real-survey flattenability census (anti-overfitting check)

Harvested 41 public files from GitHub survey repos (`eval/harvest_xlsforms.py`
→ `data/xlsforms/harvest/census.json`; sources include the official ODK
template, SurveyCTO roster templates, UNHCR surveyDesigner, Kobo fixtures,
Survey123 examples, and an Indian research institute's ODK-based academic
reporting forms). Of the 29 genuine XLSForms:

| class | n | share | meaning |
|---|---|---|---|
| register (imports as-is) | 12 | 41% | one repeat group, 2–12 columns |
| card (no repeat) | 6 | 21% | needs a label:value per-respondent layout |
| multi_region (sibling repeats) | 5 | 17% | needs multi-subtable descriptors |
| not_flattenable | 6 | 21% | nested repeats / cascading selects / media-centric |

So **~40% of real surveys are paper-register-flattenable today, ~80% with
the two layout extensions already sketched** (card + multi-region, each of
which reuses the same fiducial scheme per region). Cascading selects are
the one semantic blocker: their domains depend on earlier answers, which a
static printed legend cannot express.

End-to-end on the 12 register-class imports — layouts nobody on this
project designed (`eval/eval_harvested.py`, or-8b, 2 seeds each):
**24/24 rendered, filled and extracted with zero pipeline failures;
detected bucket n=8 at 0.971 cell accuracy, zero hallucination.** The
text-heavy academic forms (columns like paper/venue titles — long
out-of-lexicon handwriting) landed mostly in *review*, which is the correct
honest behaviour, not a silent degradation. The fiducial scheme survived
every imported layout (portrait & landscape, 3–8 columns).

## Experiment 2 — OCR-specialist handwriting head (isolated)

`eval/cellbench.py`: 240 identical pre-rectified cell crops (60 each of
name / amount / code / free-text) from geometry-trusted forms; every model
gets identical crops and prompts; exact-match scoring. Nanonets-OCR2-3B
served locally via vLLM (nightly needs the tied `lm_head` materialized
into the checkpoint).

| model | ALL (domain prompt) | name | amount | code |
|---|---|---|---|---|
| gemini-2.5-flash | 0.858 | 0.833 | 0.750 | 1.000 |
| **tuned 2B (ours)** | 0.838 | **0.867** | **0.800** | 0.983 |
| qwen3-vl-8B (untrained) | 0.833 | 0.850 | 0.700 | 0.933 |
| Nanonets-OCR2-3B | 0.804 | 0.767 | 0.733 | 0.950 |

Three conclusions (n=60/type, treat ±0.05 as noise):

1. **The OCR specialist does not have a better handwriting head.** Nanonets
   is last on names — the one place it could have justified itself — and
   ties on amounts. Combined with the sibling's DeepSeek-OCR result
   (interpretation failures), the OCR-specialist route is closed unless a
   future model demonstrably beats this table.
2. **The LoRA'd 2B has the best local handwriting head** — it beats the
   4×-larger untrained 8B on names and amounts. Ink-realistic training
   data, not parameters, bought that.
3. **Amounts are hard for everyone** (0.70–0.80 across 2B→gemini). The
   long-digit weakness is model-universal, which settles the remedy: it is
   a form-design problem (per-digit boxes / comb fields), not a
   model-selection problem.

Domain prompts helped every model (+0.03–0.07 ALL; codes 0.93–1.00), and
the OCR specialist benefited too — instruction-following was not its
bottleneck, reading was.

## Open threads

- Header fields (0.58) lag table cells (0.94): no fiducials above the
  table; label-anchored crops + designer-supplied domains (village/block
  lists, fuzzy-snapped) are wired and waiting for templates that use them.
- Review-bucket geometry: extreme warp still lands ~30 forms in review.
  The honest fix is UX (instant "retake" feedback at capture time), not CV.
- LoRA on builder-rendered forms (sibling's recipe, ~90 min) if 2B digit
  accuracy needs a push; not yet justified — the errors concentrate where
  review flags already point.
