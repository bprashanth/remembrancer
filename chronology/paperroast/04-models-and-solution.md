# 4 · Models, harnesses, and where we landed

## First, the framing: two different problems

Every form job falls into one of two buckets, and they deserve different
machinery:

**Bucket 1 — a completely new, unknown form.** No template, no anchors,
no domains. This is frontier-model + harness-engineering territory: the
challenge is *which model* and *which harness* preserve layout, content
and meaning at once — forcing page/region coverage, letting the model
zoom, keeping its output aligned to a structure you don't know in
advance. The form-idable project lives here, and even its best results
need a strong model driven carefully.

**Bucket 2 — a known layout.** If the form was designed (or *re*-designed)
by us, detection stops being perception research and becomes bounded
lookup: the template says where every cell is and what values it may hold.
**This is why taking an organisation's existing form and regenerating it
in a detectable format is such a lever** — one design-time step converts
every future submission from bucket 1 to bucket 2.

Everything below is about how far bucket 2 goes.

## What we measured about models

- **Size stops mattering once structure is supplied.** Architecture-
  controlled sweep, identical pipeline, only the model swapped: detected-
  bucket positional accuracy 0.943 (tuned 2B) ≈ 0.938 (untrained 8B) ≈
  0.943 (32B) ≈ 0.952 (gemini-2.5-flash) — with the 2B at 10 s/form
  locally vs 25–150 s for the rest. The sibling saw the same from the
  other side (a 72B beaten by much smaller models; top-band members
  distinguishable only by cost).
- **Crop/zoom is the capability gate.** Strong models can *request* their
  own crops and gain from it (+0.13 for an 8B). Weak models emit zero
  crops and an agentic protocol actively hurts them. The rule: strong
  model → let it crop; weak model → hand it deterministic crops. Our
  pipeline never asks the 2B for anything — it *receives* one rectified
  row band or one cell, computed from the template.
- **Harness beats parameters.** The same model spans 0.43→0.98 on one
  form depending only on how it is driven (coverage forced, then zoom
  allowed). Our verdicts are model-independent (2B and 32B agree 43/45)
  because they derive from geometry, not from the model.
- **OCR specialists lose conceptually and empirically.** Conceptually:
  form extraction is *interpretation* (dot=0, tally=sum, tick=yes), and
  OCR models faithfully transcribe the dot. Empirically: DeepSeek-OCR had
  the best precision of anything tested and still failed notation-heavy
  forms; Nanonets-OCR2-3B, tested head-to-head on 240 identical
  pre-rectified cell crops, came **last on handwritten names** (0.767 vs
  the tuned 2B's 0.867) — reading, not instruction-following, was its
  bottleneck. Meanwhile the LoRA'd 2B has the best *local* handwriting
  head, beating the 4×-larger untrained 8B — ink-realistic training data
  bought what parameters didn't.
- **Amounts are hard for everyone** (0.70–0.80 from 2B to gemini): a
  form-design problem (per-digit comb boxes), not a model-selection
  problem.

## The solutioning that got us here (each one measured)

1. **Positional cell-level metric first** — everything else was steered
   by it.
2. **Printed QR form ID** — template lookup, never pixel fingerprinting.
3. **OMR fiducial marks** (per-row margin squares + tall anchor bar +
   column ticks) — per-row geometry by lookup; sequence identity solved
   by joint left/right shift scoring + sequential tracking with adaptive
   pitch; TPS refinement using the found marks as control points.
4. **Per-band rectification** — each row straightened by its own quad,
   plus in-band rule tracing and column-edge snapping.
5. **Ink map** (contrast-based strokes minus the known printed layer,
   component-filtered, calibrated to ~1% FN/FP) — knows *which* cells are
   written before any model runs.
6. **Ink-anchored field assignment** — the model supplies ordered values,
   the ink map supplies positions; kills the dropped-empty-field shift.
7. **Bounded reads** — one row band per call, headers + per-column value
   domains in the prompt, output length capped, repetition penalty 1.05;
   per-cell fallback when counts disagree.
8. **Two-pass disagreement on numbers** — band read vs cell read; the only
   signal that catches a domain-valid wrong digit.
9. **Domains + legends printed on the form** — +5pp on codes for the 2B;
   codes 0.93–1.00 with domains across all models.
10. **Lexicon fuzzy-snapping** for designer-supplied vocabularies
    (villages, blocks) — "Shimoa"→"Shimoga".
11. **Deterministic three-way verdict** — detected / review / reject from
    per-signal thresholds calibrated against measured accuracy; rejection
    happens *before* the first model call when anchors aren't found.
12. **Review UX that matches the paper** — same-grid spreadsheet, flagged
    cells highlighted, click-to-zoom the actual ink next to an editable
    value, corrected-CSV export.

## Where it lands

**Give an organisation a template with a QR code and the OMR anchor dots,
and a small LoRA-trained local model can reliably "diff" the filled sheet
against the template** — 0.94 positional accuracy on auto-accepted forms,
~0.2% hallucination, honest refusals, ~10 s/form on local hardware, no
data egress. The template supplies geometry and vocabulary; the anchors
supply per-row truth under page bow; the small model only ever answers
tiny, bounded, domain-constrained questions; and the verdict system says
so when a photo can't be trusted.

## ⟨form-idable⟩ Bucket 1 in numbers — which frontier model, and what it costs

The paperroast pipeline converts bucket 1 → bucket 2 at design time. But
**bucket 1 never disappears**: the first submission of any un-regenerated
form, legacy archives, and anything a partner photographs before onboarding
all arrive without a template. Those need a frontier model driven well, and
the ranking below is what we measured on 24 real hand-filled partner forms
(scans + phone photos), consensus goldens, token-multiset scoring.

Paired comparison — only forms every model completed, per-page + fixed tiles,
**reasoning disabled** on every Gemini:

| model | ALL-F1 | $/100 forms | sec/form | note |
|---|---|---|---|---|
| gemini-3.5-flash | 0.875 | $4.87 | 21 | clean |
| gemini-3.6-flash | 0.872 | $4.35 | 24 | *helped build goldens* |
| **codex CLI** (the incumbent) | 0.860 | subscription | **596** | *helped build goldens* |
| qwen3.7-flash + agentic | 0.804 | **$0.41** | 372 | clean |
| gemini-2.5-flash | 0.799 | $1.15 | 29 | clean |
| qwen2.5-vl-72b | 0.738 | $1.07 | 101 | clean |
| gemma-3-12b + agentic | 0.598 | **$0.05** | 314 | clean |
| trained 8B (local) + tiles | 0.680 | **$0** | 200 | private |
| trained 2B (local) + tiles | 0.552 | **$0** | 123 | private |

**Read this as tiers, not a ranking.** gemini-3.5-flash measured 0.857, 0.758
and 0.875 on overlapping subsets of the *same six forms*. At n=3–6 the top five
are statistically indistinguishable. What survives every slicing:

- a **top band ≈0.80–0.88** — choose on cost and latency, not score;
- **cost spans ~100×** inside the usable range ($0.05 → $4.87 / 100 forms), and
  that difference is far more reliable than any accuracy difference;
- **codex ranks third and its score is inflated** (it helped write the goldens
  it is scored against) while being ~25× slower than either Gemini. On the
  evidence it should be retired from the default path and kept as manual
  escalation;
- **scale is not the lever** — the 72B loses to several much smaller models.

**Recommended tiers for bucket 1.** HIGH: a Gemini flash — 2.5 at $1.15/100 if
cost matters, 3.5 at $4.87/100 if quality does; they are within noise of each
other. MEDIUM: qwen3.7-flash at **$0.41/100** — statistically tied with
gemini-2.5-flash at a third of the price, and its 6 min/form is irrelevant to a
batch-and-email workflow. LOW: gemma-3-12b at **$0.05/100**.

### One API gotcha that silently costs money
The reasoning switch differs by generation, and getting it wrong benchmarks a
model with reasoning **on**:

| config | 2.5-flash | 3.5-flash | 3.6-flash |
|---|---|---|---|
| `thinkingBudget: 0` | works | works | **rejected** |
| `thinkingLevel: "minimal"` | n/a | works, 0 thinking tokens | works, 0 thinking tokens |
| `includeThoughts: false` | — | still emits thinking tokens | still emits — only *hides* them |

Also: gemini-3.x bills ~5,800–7,500 input tokens per form against 2.5's
~2,100–3,200 for the **same images**. Different image tokenisation, and that is
most of the price gap — not model quality.

## ⟨form-idable⟩ How the small models were actually LoRA-trained

Same recipe for both; only the base model changed.

**Adapter.** LoRA r=32 on attention + MLP (`q,k,v,o,gate,up,down`), vision tower
frozen. 34.9M trainable params for the 2B — about **140 MB**, hot-swappable, so
a per-sector adapter is a deployment detail rather than a new model. 2 epochs,
cosine schedule, lr 1e-4 (2B) / 7e-5 (8B), batch 1 × grad-accum 8.
**~90 min for the 2B, ~2.5 h for the 8B** on one GB10.

**Corpus: 774 synthetic forms** (612 generated archetypes + 163 fills of real
downloaded blank templates). Everything is synthetic because the golden is then
exact by construction — the fill values are known before rendering.

**The three ingredients that mattered, in measured order:**

1. **Fill density matched to deployment — the single biggest lever.** Training
   on 100% densely-filled forms taught the model that pages are full of rows: it
   read correctly and then invented more, emitting **13× too many cells** with
   precision 0.30. Re-weighting toward sparse took unseen-layout accuracy
   **0.351 → 0.575**. But over-correcting cost **−0.145** on genuinely dense
   forms (recall 0.774 → 0.630). **Sample density ~uniformly over 0.1–1.0.**
   Both extremes are traps.
2. **Real ink, not handwriting fonts.** Digits and single-letter codes are
   composited from **NIST SD-19** — 26,040 real hand-print glyphs, 62 classes ×
   7 writer cohorts, one cohort per form so a sheet looks like one person filled
   it. Synthetic-vs-real handwriting was the largest remaining gap (**−0.10**),
   and SD-19 closes part of it. It is hand-*print*, though: cursive and pencil
   remain the hard cases, and pencil (low-contrast grey, thin strokes) is worth
   modelling explicitly.
3. **Real template structures.** Layouts we invented ourselves produced a model
   that scored 0.668 on familiar shapes and **0.337 on unseen ones** — pure
   overfitting to our own generator. Filling *downloaded* blank templates fixed
   it. The filler reads grid geometry and printed labels **straight from the PDF
   vector data**, so there are no CV thresholds to tune, and it fills only cells
   that are empty in the blank — no semantic understanding needed.

Also in the recipe, lower-value but cheap: augraphy degradation, phone-camera
geometry (perspective, page bow, finger occlusion, shadow, background), page
furniture (spiral binding, clips), and a vernacular-name lexicon mined from the
partners' own transcriptions.

**What training bought.** 8B: **+0.207** on fixed tiles (0.437 → 0.644 paired;
0.500 → 0.680 across six forms) — the largest single training gain measured.
2B: 0.351 → 0.575 on unseen layouts. And **specialisation beat scale** — a
trained 2B (0.552) outperformed an *untrained* 8B (0.500).

**The trap we hit, which matters for anyone extending this.** Fine-tuning on
always-emit-CSV targets **suppresses crop-loop behaviour**: the trained 8B's
crops fell 6.3 → 4.7 and it became *worse* with the agentic harness (0.587) than
with plain tiles (0.644), while the untrained 8B showed the opposite ordering.
Training and the agentic harness **conflict** unless the crop protocol is itself
in the training data as multi-turn examples (low-res page → `CROP …` → crop →
values). We never generated those. For paperroast this is moot — you hand the
model deterministic crops and it never needs to ask — but it explains why the
two levers did not compound.

## The four-quadrant answer (both projects, one harness)

With form-idable's 8B LoRA finished, all four quadrants of the BRIEF's
open question ran through the *same* paperroast structured harness on the
same paired forms:

| | untrained | LoRA-trained |
|---|---|---|
| **2B** | unusable (degenerate loops) | ALL 0.731 · detected 0.942 · ~10 s/form |
| **8B** | ALL 0.777 · detected 0.938 | ALL 0.780 · detected 0.946 · headers 0.69 |

- In the **auto-accept bucket everything ties (≈0.94)** — the structure
  saturates it; model choice is a latency/cost decision there.
- The 8B's edge lives **off the trusted path** (the review bucket,
  +0.07) — and it is *scale*, not training: the trained and untrained 8B
  score identically there.
- **Training was existential for the 2B and cosmetic for the 8B** (+0.003
  ALL; its real gains were headers 0.54→0.69 and free-text cells, where it
  posts the best local cell-bench score, 0.863, within noise of gemini).
- Deployment recipe: **trained 2B as the detected-tier workhorse; 8B
  (training optional) as the review-tier and free-text reader; both
  local.** Frontier models only for bucket-1 forms and online review
  drafts.
