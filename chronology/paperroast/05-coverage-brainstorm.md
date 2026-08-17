# 5 · Brainstorm — which forms can we handle, and what would unlock the rest

*(working document; opinions welcome, numbers from the census where they
exist)*

## Handled today

- **Single-table registers** (41% of surveyed real forms): header fields +
  one table, any mix of serial / int / dec / date / yn / choice / name /
  text columns, portrait or landscape, 3–13 columns.
- Blanks, sparse fill, struck cells, dot=0, ticks, corrections, margin
  scribbles — interpreted or ignored per the printed notation.
- **Skip logic** (`relevant`) mostly costs nothing on paper: it becomes
  "leave blank if not applicable", and blanks are first-class in our grid.
  A cheap upgrade: import the relevant-expressions as **cross-field
  consistency rules** (if "Irrigated"=N then "Water source" must be blank)
  and flag violations for review.
- **Constraints** import directly as min/max domains.
- **Likert grids** are just choice columns with 1–5 domains.

## Extensions already scoped (layout work, not research)

- **Card layout** — no repeat group; one page (or half-page) per
  respondent, label:value rows with anchor marks per row. Unlocks 21%.
- **Multi-region** — several sub-tables per page, each with its own mark
  pairs and anchor bar; regions extracted independently. Unlocks 17%.
- **Per-digit comb boxes** for amounts — the single highest-value change,
  since amounts are 0.70–0.80 for *every* model. Also the natural format
  for dates (DD/MM/YY combs) and phone numbers.

## The hard cases, with candidate solutions

**Cascading selects (district → block → village).** The printed legend
cannot depend on an earlier answer. Options, in rough order of promise:
1. **Print-time specialisation** — organisations print forms in batches
   per geography/context anyway. If the cascade root is known when the PDF
   is generated (this batch is for Block X), every downstream list
   collapses to a static domain. The importer could emit one template per
   root. Probably covers most real cascades with zero new detection work.
2. **Code sheets** — print the full hierarchical code list on the reverse
   page; the writer records a short code; extraction validates against the
   whole tree and review shows the decoded value.
3. **Free text + post-hoc validation** — accept handwriting, fuzzy-snap
   against the union of all cascade leaves, flag ambiguity for review.
   Works today with zero changes; weakest on OOV handwriting.

**Nested repeats (household → member → episode).** Paper solved this a
century ago with **linked registers**: a parent sheet and child sheets
joined by an ID. Concretely: the child template carries a "Parent ID"
header field (or the parent's QR is re-stamped per child sheet at print
time); extraction joins on it. This is template-set design plus a join —
no new perception machinery. Worth building when a real user needs it,
not before.

**select_multiple.** Two paper idioms: (a) ≤6 options → one Y/N tick
sub-column per option (imports as N yn columns — works today, just wide);
(b) many options → "write all codes" cell, validated as a subset of the
domain, invalid combos flagged. The importer currently maps these to free
text; upgrading to (a) for small domains is easy.

**Signatures / thumbprints.** Unreadable by design — but the **ink map
already detects presence without reading**. "Signed: yes/no" as a
presence-only cell type is nearly free and genuinely useful (attendance,
consent).

**Photos / GPS.** Not paper problems. If a survey is media-centric, digital
capture is the right tool; hybrid deployments (paper register + phone
photos keyed by the register's serial) are an integration question.

**Long free text** (remarks, qualitative answers). Extraction reads it,
accuracy is lexicon-dependent (the academic-forms result: title-like
columns pushed forms into review). Honest positioning: short remarks
columns are fine; essay fields belong in review-always cells or digital
capture.

**Multi-language / non-Latin scripts.** Rendering Hindi/Kannada/Tamil
labels is a font problem (solvable). *Handwriting* in Indic scripts is a
different research problem — the current stack (SD-19 glyphs, Qwen3-VL
heads, our lexicons) is Latin+digits. Flag clearly: vernacular *labels*
soon; vernacular *handwriting* is future work with its own data story.

## A classification rule of thumb for intake

When an organisation brings a survey:
1. repeat group + scalar questions → **register, today**
2. no repeat → **card** (soon)
3. sibling repeats → **multi-region** (soon)
4. cascading selects → ask "do you print per-geography batches?" → usually
   **print-time specialisation**
5. nested repeats → **linked registers**, scoped per case
6. media/GPS-centric → recommend digital capture, possibly hybrid
