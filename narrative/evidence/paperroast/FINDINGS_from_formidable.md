# Form transcription — cross-project findings

Written by the **form-idable** side (blind detection of *unknown* forms) for the
**paperroast** side (form builder + detection of *known* templates). These are
the findings that transfer between the two problems. Ecology specifics are
deliberately omitted.

Everything here is measured on real hand-filled forms with consensus goldens,
scored on token multisets (numbers + words + single-letter codes). Sample sizes
are small — read the caveats.

---

## 1. The harness matters more than the model

**The single most useful finding.** The same model scored **0.43 to 0.98** on
one form depending only on how it was driven.

| harness | ALL-F1 | recall | precision |
|---|---|---|---|
| whole-document agentic (model chooses where to look) | 0.432 | 0.276 | 0.987 |
| per-page, fixed tiles | ~0.85 | | |
| **per-page + crop/zoom** | **0.976** | 0.968 | 0.984 |

Two separable ingredients, and you need both:

**(a) Force coverage.** Whole-document agentic failed not from bad reading —
precision was 0.987 throughout — but because the model cropped three regions of
page 1, decided it was finished, and never opened pages 2-3. Scope the loop to
one page (or one region) at a time and drive the iteration yourself.

**(b) Then allow zoom.** With coverage forced, letting the model request closer
looks is worth roughly **+0.13** over fixed tiles.

Measured again on a second model across 6 forms: qwen3-vl-8b went
**0.500 → 0.634 (+0.134)** on identical forms purely from the harness change.

## 2. There is a hard capability gate: can the model drive a loop at all?

Give a model a crop protocol and count how often it actually uses it.

| model | crops/form | agentic | fixed tiles | verdict |
|---|---|---|---|---|
| qwen3-vl-8b | 6.3 | **0.634** | 0.500 | harness helps |
| mistral-small-3.2-24b | 4.5 | 0.592 | — | harness helps |
| gemma-3-12b | **0.0** | 0.593 | — | ignores protocol |
| tuned 2B (local) | **0.0** | 0.335 | **0.527** | harness *hurts* |

A model that emits `crops: 0` is running one-shot, and handing it an agentic
prompt **costs** accuracy — the 2B lost 0.19 because the agentic path showed it
one whole page where the tile path showed two half-page crops at the vision cap.
Less detail, more confusing instructions.

**Rule: strong model → let it request crops. Weak model → hand it deterministic
crops.** Do not share a harness between the two.

**This is directly relevant to paperroast**: template-driven row-band cropping is
the *correct* shape for a small model, because the model never has to *ask*. You
compute the crop from the template and hand it over. Measured on the blind side,
that pattern gave **+0.089 ALL-F1 and recall 0.70 → 0.86**.

## 3. Model tiers — and why you should not trust a ranking

Paired comparison, only forms every model completed (n=3, per-page):

| model | ALL-F1 | $/100 forms | sec/form |
|---|---|---|---|
| gemini-3.5-flash | 0.875 | $4.87 | 21 |
| gemini-3.6-flash | 0.872 | $4.35 | 24 |
| codex CLI (agentic) | 0.860 | subscription | **596** |
| qwen3.7-flash (agentic) | 0.804 | **$0.41** | 372 |
| gemini-2.5-flash | 0.799 | $1.15 | 29 |
| qwen2.5-vl-72b | 0.738 | $1.07 | 101 |
| gemma-3-12b (agentic) | 0.598 | **$0.05** | 314 |
| qwen3-vl-8b (agentic) | 0.533 | $0.88 | 113 |
| local tuned 2B | 0.421 | **$0** | 202 |

**CAUTION.** gemini-3.5-flash measured **0.857, 0.758 and 0.875** on overlapping
subsets of the same six forms. At n=3-6 the top five models are
indistinguishable. Report tiers, not ranks.

What survives every slicing:
- a **top band ~0.80-0.88** whose members you should choose between on cost and
  latency, not score
- a clear step down below it
- **cost spans ~100x** inside the usable range and is far more reliable than any
  accuracy difference
- **scale is not the lever** — the 72B is beaten by several much smaller models
- the agentic CLI is ~25x slower for no measurable accuracy gain

### Gemini reasoning: the knob differs by generation
| config | 2.5-flash | 3.5-flash | 3.6-flash |
|---|---|---|---|
| `thinkingBudget: 0` | works | works | **rejected** |
| `thinkingLevel: "minimal"` | n/a | works, 0 thinking tokens | works, 0 thinking tokens |
| `includeThoughts: false` | — | still 80 thinking tokens | still 72 — only *hides* them |

Getting this wrong silently benchmarks a model with reasoning ON. Also note 3.x
bills ~7,500 input tokens per form vs 2.5's ~2,100 for the **same images** —
different image tokenisation, and that is most of the price gap.

## 4. A general VLM beats an OCR specialist

Counter-intuitive, so worth stating plainly. DeepSeek-OCR (3B, purpose-built)
had the **highest precision of anything tested (0.96)** and still lost: 0.82
overall, **0.66 on real scans**, and it failed exactly the notation-dependent
forms (0.67 with tally marks, 0.60 with checkboxes).

OCR specialists are trained for *document → faithful glyphs*. Form extraction is
*form → interpreted values*: "a lone dot means 0", "tally marks sum to an
integer", "a tick means present", "a struck-through cell means no entry". A
general VLM can be **instructed**; an OCR model transcribes the dot.

Same reasoning applies to olmOCR2 / Chandra-8B / Nanonets-OCR2 (none on
OpenRouter; all document→markdown). There is no OCR-specific Gemma.

**Use an instruction-followable general VLM. Reach for an OCR specialist only
when the task really is transcription without interpretation.**

## 5. Training data: match the deployment distribution

Fill density — what fraction of a form's rows actually contain data — turned out
to be the dominant training-data variable.

| training data | result on unseen layouts |
|---|---|
| 100% densely-filled forms | over-produces: cell_frac **13x**, precision 0.30 |
| sparse-weighted | 0.351 → **0.575** ALL-F1, precision 0.30 → 0.59 |
| but over-corrected | dense real forms regressed **-0.145**, recall 0.774 → 0.630 |

**Sample density roughly uniformly over your deployment range.** Both extremes
are traps: dense-only makes the model keep emitting rows forever; sparse-only
makes it stop too early on genuinely full forms.

Other data findings, in order of measured size:
- **real handwriting vs synthetic: -0.10**, the largest single gap. Composited
  NIST SD-19 glyphs are real *hand-print*; real writers are cursive, and pencil
  is a distinct and much harder case.
- **vocabulary matters** — words scored worst of the three buckets (0.475 vs
  numbers 0.531, codes 0.567). A VLM reads handwriting through language priors,
  so an out-of-vocabulary name is unreadable scrawl. Build a domain lexicon, and
  include OOV tokens so the model does not snap everything onto it.
- **single-character code columns: -0.10**. N/M/W, L/C/E, 4/H/Y are genuinely
  ambiguous from pixels. This is where a **known value domain per column** should
  pay off most — paperroast can supply that and nobody has measured the gain yet.
- **photo degradation: no measurable effect** (0.564 clean vs 0.586 degraded).
- **form size/complexity: not a bottleneck** — large tables scored *best*.

The last two were the surprises, and they redirected effort away from camera
realism toward ink realism and vocabulary.

## 6. Approaches that FAILED — do not repeat

| approach | result | why |
|---|---|---|
| template fingerprinting (identify a form from pixels) | precision **0.00** held-out; DINOv2 3x better but still 0.75/0.30 | use a printed form ID instead of guessing |
| printed-layer subtraction (align to blank, erase print) | **-0.114** | handwriting *overlaps* printed rules, so erasing print erases parts of digits; the model also uses printed context |
| degenerate-tail trimming (cut output where it repeats) | **-0.017** | confounded with real content: code columns are legitimately repetitive and serial-number columns *are* arithmetic progressions |

## 7. Metric traps that cost us real time

**(a) Single-character tokens were being discarded.** The scorer inherited
`len(token) >= 2` to drop OCR noise. In form data single letters *are* the data
— **59-70% of code-heavy forms went unscored**, biasing everything toward
numbers. Fixing it immediately revealed that two frontier models differ
substantially on codes vs numbers, which had been invisible.

**(b) Token-multiset scoring is blind to position.** A model can score 0.85 while
putting every value in the wrong cell. Our output was token-accurate and
**unusable**: header fields linearised, column headers dropped, inconsistent
cell counts per row. A reviewer cannot diff that against the paper.
**Build a positional cell-level metric first.** This is the single most important
thing for paperroast, and the reason its problem framing is better than ours.

**(c) Hard-coded metric lists.** Three separate scripts each copied a fixed list
of metric keys; when a new metric was added they silently dropped it and one
comparison reported a fabricated **0.000**. Propagate whatever the scorer emits.

## 8. RESOLVED: training an 8B pays — but the levers CONFLICT

**Hypothesis was WRONG as stated.** It predicted the 8B would stack training AND
harness. It does not: you get one or the other.

Paired on 3 forms (every config completed):

| config | ALL-F1 | recall | prec | crops | sec |
|---|---|---|---|---|---|
| **trained 8B + fixed tiles** | **0.644** | 0.72 | 0.70 | 0 | 200 |
| trained 8B + agentic | 0.587 | 0.70 | 0.64 | 4.7 | 202 |
| untrained 8B + agentic | 0.507 | 0.52 | 0.64 | 6.3 | 89 |
| trained 2B + tiles | 0.486 | 0.65 | 0.44 | 0 | 86 |
| untrained 8B + tiles | 0.437 | 0.41 | 0.53 | 0 | 69 |

Across all 6 forms: trained-8B tiles **0.680**, trained-8B agentic 0.642,
untrained-8B agentic 0.634, trained 2B 0.552, untrained-8B tiles 0.500.

**What we learned:**
- **Training is worth +0.207** on fixed tiles (0.437 -> 0.644) — the largest
  single training gain measured.
- **Fine-tuning partially SUPPRESSES loop-driving.** Crops fell 6.3 -> 4.7, and
  the trained model does WORSE with the agentic harness than with tiles, while
  the untrained model does BETTER. Training on always-emit-CSV targets teaches
  the model to answer immediately, which is exactly what the loop needs it not
  to do. If you want both, the crop protocol has to be IN the training data.
- **Best local config: trained 8B + deterministic tiles, 0.680**, ~200 s/form,
  $0, fully private. That puts the privacy tier ~0.12-0.18 F1 behind the API
  band (0.80-0.86), down from ~0.25 before training.
- **Latency, not accuracy, is now the binding constraint locally.**

Caveat: n=3 paired / n=6 unpaired, and the small-sample instability in section 3
applies here too.

### The original hypothesis, kept for honesty

The case for it:
- the 8B is the only local model that **clears the capability gate** — it drives
  the crop loop (6.3 crops/form, +0.134) where the 2B and gemma-12b emit 0
- so it is the only local option that stacks **training AND harness**
- **specialisation already beat scale**: a trained 2B (0.552) outperformed an
  *untrained* 8B on fixed tiles (0.500)

The case against:
- **scale is demonstrably not the lever here** — the 72B loses to much smaller
  models
- the 2B's large training gain came mostly from fixing a defect in our own data
  (100% dense), which is already fixed, so the 8B gets no equivalent windfall
- it trains on 774 samples where the 2B had 1020

If the 8B lands near the top band while running locally at zero cost, the
privacy tier becomes viable. If it lands near the untrained 8B, the conclusion
is that harness and data — not parameters — are the whole story, which would be
just as useful to know.

---

*Full detail, including the chronological log of what broke and why, is in*
`form-idable/benchmarks/wide/CHECKPOINT.md` *and* `README.md`.
*GPU safety on the shared box:* `GPU_COORDINATION.md` *— read it before starting
any GPU job; this machine has been hard-frozen twice.*
