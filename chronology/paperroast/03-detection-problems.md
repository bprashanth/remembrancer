# 3 · Why detecting hand-filled forms is hard

*(paperroast's view; the form-idable agent will extend this with the blind
side's war stories — sections marked ⟨form-idable⟩ are his to fill.)*

## 1. Layout is the product, and most metrics can't see it

The bar is not "did the model read the values" — it is **does the output
spreadsheet look like the paper form, with the right values in the right
cells, blanks included?** If a reviewer has to mentally re-map rows and
columns, the artefact is worthless at any token accuracy.

The failure that motivated this project: a model emitted every value
roughly correctly — header fields linearised, two column headers dropped,
rows with inconsistent cell counts — and scored 0.85 on a token-multiset
metric while being **unusable**. Worse, the standard scorers are blind to
it: token multisets ignore position entirely, and a common "drop tokens
shorter than 2 chars" denoising rule silently unscored 59–70% of
code-heavy forms whose *data is single letters*. Rule one of this project:
**build the positional cell-level metric first** (fraction of template
cells whose value matches the golden at the same row and column). Our
scorer's unit test enshrines the original failure: the linearised output
scores >0.75 multiset and <0.15 positional.

A subtler layout problem: cheap models **drop empty CSV fields**, so every
value after a blank slides one column left — token-perfect, layout-wrong,
and invisible to any per-value check.

## 2. Geometry: paper is not flat

A phone photo of a curled register page is not a projective transform of
the blank. Measured failures, in order tried: global homography leaves
rows tens of pixels off near the page bottom; pinning the table's four
corners gets hijacked by bolder interior line-crossings; fitting a
quadratic mesh to detected grid crossings under-corrects exactly where
detection fails. The deepest trap is **row identity**: when residual warp
exceeds half a row pitch, any local search snaps to the *neighbouring*
rule and every band reads the row above/below — catastrophic and silent.
Bands that cut across two rows also make the model see (and emit) content
from both.

## 3. Content and handwriting

- **Real ink is the biggest gap** — synthetic handwriting fonts flatter
  every model; real hand-print costs ~0.10, cursive and **pencil** more.
  Pencil is its own regime: strokes at gray 195–235 that an absolute
  darkness threshold erases entirely (ours did, silently).
- **Domain-specific words**: a VLM reads handwriting through language
  priors, so an out-of-vocabulary word — a vernacular crop name, a local
  village, a person's name — is unreadable scrawl. Words score *worse*
  than numbers and codes. Lexicons help; but include OOV tokens or the
  model snaps everything onto the lexicon.
- **Single-character codes** are genuinely ambiguous from pixels: N/M/W,
  L/C/E, 4/H/Y, P/A/L in a narrow attendance column. This is where a
  known per-column value domain pays (+5pp measured for a 2B; codes reach
  0.93–1.00 with domains vs 0.70–0.87 without).
- **Long digit strings** (5–6-digit rupee amounts) are hard for *every*
  model we measured — 0.70–0.80 from a 2B all the way to gemini. One
  misread digit is domain-valid and undetectable by rules; only reading
  the cell twice and comparing catches it.

## 4. Interpretation, not transcription

Field forms have a notation system that must be *interpreted*: a lone dot
means 0; tally marks sum to an integer; a tick means yes; a
struck-through cell means "no entry" (empty, not "-"); a struck value
with a rewrite above means the rewrite; a circled value is just the
value; "+" chains (9+2+3+4) are legitimate cell content; ditto squiggles
mean "same as above". A pure OCR transcriber faithfully outputs the dot —
and is wrong. This is the conceptual line between OCR models and
instructable general VLMs (doc 4).

## 5. Honesty: knowing when to refuse

Some photos should not be extracted — too warped, too cropped, too dark.
Emitting plausible garbage is the worst outcome; a wrong-but-confident
spreadsheet poisons downstream data quietly. Refusal ("retake the photo,
flatter and fully in frame") must be **cheap, deterministic and decided
before the model runs**, and review must point a human at exactly the
uncertain cells, not at the whole document.

## ⟨form-idable⟩ — what we tried on the blind side, and why it failed

Everything here was tried *before* the QR/OMR approach existed, on unknown
forms with no template. Recorded so the dead ends stay dead.

**Template fingerprinting — identify a form from its pixels. Precision 0.00.**
The idea was to skip asking the user which form this is: two filled copies of
one template share their printed layer, so fingerprint the printed structure and
match. Hand-built geometry (rule positions, crop-invariant 1-D RANSAC alignment)
scored **precision 0.00 / recall 0.00** on held-out templates — 0 true positives,
4 false positives out of 190 pairs. A pretrained DINOv2 embedding was ~3× better
(AP 0.44) but still only **0.75 precision / 0.30 recall**.
Two lessons. First, an early "it works!" reading came from **three hand-picked
pairs** — an anecdote, not an evaluation; a proper held-out protocol killed it
within the hour. Second, the cost asymmetry decides the design: a false positive
applies the *wrong* template and produces confidently wrong output, while a false
negative merely falls back to the general path. That asymmetry is exactly why
**a printed ID beats any amount of clever matching**, and why paperroast's QR is
the right call rather than a shortcut.

**Tesseract as a cheap layout/fingerprint source — coverage too unstable.**
Confidence filtering *does* separate printed from handwritten *within* one image
(at `conf ≥ 75` it returns precisely the printed labels). But coverage swings
wildly with photo quality: the same invoice template gave **13** high-confidence
tokens in one photo and **5** in another, intersecting on a single word; a pencil
sheet gave **zero**. Fine for a one-off read of a good scan, useless as a stable
signal across submissions.

**Textract for structure-first extraction — not actually in the loop.** Worth
recording because we nearly built on it: an older prompt in the production repo
is Textract-backed and explicitly says *don't crop to verify cell values*. It is
**dead code** — `worker.py` loads the crop/zoom prompt and no Textract call
survives in the worker path. As a standalone transcriber Textract scored 0.89
with the **highest precision** of any API option, and its `tables` output is a
genuine grid — but at $0.015/page it costs more than a whole-form Gemini call,
and it cannot apply notation rules (dot=0, tally→sum). We never tested
Textract-for-geometry + cheap-model-for-values; paperroast's template makes that
combination unnecessary.

**Printed-layer subtraction ("redacting the print") — −0.114 F1.** With the blank
template aligned to the filled photo, erase every pixel the blank has ink on, and
hand the model *only handwriting in a known box*. It made things **worse**:
band-only 0.681 → band+subtract 0.567, precision 0.622 → 0.463. Handwriting
**overlaps** the printed rules and labels, so erasing print erases parts of
digits; and the model uses printed context to interpret a cell. **Cropping to a
known row is what pays (+0.089, recall 0.70 → 0.86); subtracting the print is
not.** Two-copy pixel intersection to *recover* a blank template is a separate
idea and remains untested.

**Degenerate-tail trimming — −0.017, and it destroyed good forms.** Small models
read correctly then ramble, so cutting the tail looked free. Both detection
signals are confounded with real form content: ecology-style tables are
**legitimately repetitive** (a column of `N N N N N`), and a serial-number column
**is** an arithmetic progression — so the detector cut at the *start* of good
tables, taking a 0.977 form to 0.280. You cannot detect "the model went off the
rails" by inspecting its output text. **Measure the document instead** — bounding
output by the row count detected on the page recovered +0.14 in simulation.

**Whole-document agentic coverage failure.** Given a crop tool and a whole
document, a strong model cropped three regions of page 1, decided it was
finished, and never opened pages 2–3: **recall 0.276 with precision 0.987**. It
read everything it looked at perfectly. Scoping the loop to one page took the
same model to **0.976**. Coverage must be driven by the harness, never left to
the model's judgement.

**Small models and unconstrained output — the core failure mode.** A LoRA'd 2B
reached **recall 0.86 — higher than gemini-2.5-flash's 0.83** — and still scored
0.41, because on 47 of 76 forms it never emitted a stop and kept inventing rows.
**17 forms scored exactly 0.000 while having recall above 0.5.** Perception was
never the problem; output control was. Prompt tweaks and repetition penalties
treat the symptom (though penalty 1.05 is worth keeping, recall-neutral); the
causes are training-data density (doc 4) and, structurally, **bounding what you
ask for** — which is what a row band or a single cell does by construction.

**Instruction-following is a hard capability gate.** Count how often a model
actually uses a crop protocol it has been given:

| model | crops/form | agentic | fixed tiles |
|---|---|---|---|
| qwen3-vl-8b | 6.3 | 0.634 | 0.500 |
| mistral-small-3.2-24b | 4.5 | 0.592 | — |
| gemma-3-12b | **0** | 0.593 | — |
| LoRA'd 2B | **0** | 0.335 | **0.527** |

A model emitting **zero crops** is running one-shot, and handing it an agentic
prompt actively *costs* accuracy — the 2B lost 0.19 because the agentic path
showed it one whole page where the tile path showed two half-page crops at the
vision cap. Less detail, more confusing instructions. Note this is **not** purely
a size gate: a 12B ignored the protocol while an 8B used it.

**Metric traps that cost us weeks.** Three, all the same shape — a hard-coded
assumption silently discarding data.
*(a)* The scorer inherited `len(token) >= 2` to drop OCR noise, so
**single-letter tokens went unscored** — 59–70% of code-heavy forms invisible,
everything biased toward numbers. *(b)* **Token-multiset scoring is blind to
position**: our output was token-accurate and unusable — header fields
linearised, column headers dropped, inconsistent cell counts per row. This is the
same conclusion doc 3 opens with, reached the expensive way. *(c)* Three scripts
each copied a fixed list of metric keys; when a metric was added they silently
dropped it and one comparison reported a fabricated **0.000**. A fourth variant:
when a server was down, an empty response scored as 0.000 rather than erroring —
**"no output" and "wrong output" must not be scored the same way.**


