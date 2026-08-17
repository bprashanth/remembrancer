# 1 · The form landscape — what's actually out there

*(chronology of the paperroast narrative; numbers from
`data/xlsforms/harvest/census.json`, harvested 2026-08-01)*

## Where the data came from

We wanted real survey definitions, not forms we invented ourselves — the
fastest way to overfit is to design your own benchmark. Digital survey
tools (ODK, KoboToolbox, SurveyCTO, ArcGIS Survey123) all share one open
format, **XLSForm**, and organisations publish these on GitHub. We crawled
public repositories (`eval/harvest_xlsforms.py`) and pulled 41 files from
ten sources:

| source | what it is |
|---|---|
| getodk/xlsform-template | the official ODK template |
| XLSForm/pyxform | the reference XLSForm parser's test forms (incl. a real UCL biomass field form) |
| stats4sd/xlsform_examples | Statistics for Sustainable Development's example library |
| bkkhiang/SurveyCTOBuilder360_HHRoster | ready-to-deploy SurveyCTO household-roster templates |
| kobotoolbox/kobocat | KoboToolbox server fixtures |
| Edouard-Legoupil/kobocruncher | UNHCR-adjacent Kobo analysis toolkit samples |
| unhcr-americas/surveyDesigner | UNHCR Americas' survey referential |
| palavido-dev/survey123-designer | ArcGIS Survey123 example forms (inventory, inspections) |
| Ar5h71/XLS_to_MARKDOWN_REPORT | an Indian research institute's ODK-based academic reporting forms (visits, awards, courses taught) |
| hjanesh/odk_survey_kunnamkulam | a Kerala municipal health survey |

Caveat worth keeping: GitHub-visible forms skew toward templates, demos
and test fixtures; production NGO forms mostly live in private accounts.
The census below is a floor on diversity, not a ceiling.

## The census

Of 41 files, 12 were not XLSForms at all (data exports, deliberately
broken parser fixtures). Of the **29 genuine survey definitions**:

| class | n | share | what it means for paper |
|---|---|---|---|
| **register** | 12 | **41%** | one repeat group with 2–12 columns — maps 1:1 onto a paper table register, imports **as-is** today |
| **card** | 6 | 21% | no repeat group, just a list of questions per respondent — needs a label:value "card" page layout (planned, same anchor scheme) |
| **multi-region** | 5 | 17% | several sibling repeat groups (e.g. household members + assets) — needs multiple sub-tables per page, each with its own anchor marks (planned) |
| **not flattenable** | 6 | 21% | see below |

So **~41% of real surveys flatten onto a paper register today, and ~79%
are reachable** once the two additional layouts (card, multi-region)
exist. Both reuse the exact same printed-anchor machinery per region —
they are layout work, not research work.

## Why the last ~21% resists

Three distinct reasons, in decreasing order of fundamentality:

1. **Cascading selects** — the option list of one question depends on the
   answer to a previous one (district → block → village). A printed legend
   cannot be context-dependent. This is the one *semantic* blocker; it
   needs either question flattening (print the full code list), per-page
   pre-printing (if the cascade root is known before printing), or
   acceptance as free text + post-hoc validation against the cascade.
2. **Nested repeats** — a repeat inside a repeat (per household → per
   member → per illness episode). Paper can express this only by exploding
   into multiple linked sheets; possible but a genuinely different design.
3. **Too little paper-mappable content** — media/GPS-centric or logic-demo
   forms (photos, geopoints, calculations). These are not paper forms in
   spirit; digital capture is simply the right tool for them.

The one harvested form combining reasons 1+2 was, fittingly, an ecology
field form (UCL biomass plots) — the domain this project is explicitly
firewalled from.

## Did the imported forms actually work?

Yes — this was the anti-overfitting test. All 12 register-class forms —
layouts nobody on this project designed — went import → render → synthetic
hand-fill → extraction with **zero pipeline failures** (24 runs). The
auto-accept bucket hit **0.971 positional cell accuracy with zero
hallucination**; the text-heavy academic forms (columns holding paper and
conference titles — long, out-of-lexicon handwriting) correctly fell to
*review* rather than degrading silently. Detail in `FINDINGS.md`,
Experiment 1.
