# WHY-5 results (2026-07-18, 47/52 runs judged; stragglers pending)

## The hinge verdict, stated plainly: the estimation gap we hypothesized is NOT there at the top tier
On the budget question (Rs 2 lakh, what to measure vs estimate), grok and opus produced genuinely
competent plans: both explicitly said "spend primary collection only on what existing public data
cannot give you", used Census/SECC/MGNREGA as the sampling layer, and targeted collection at
earnings/contracts/debt (real GAPS). grok's 300-household answer named six specific blocks with
agro-economic reasons (canal commercial belt vs groundwater-stressed vs hill millet). Nobody
recommended collecting data that already exists. gpt even offered "a rough Chithode-only estimate
clearly labeled as an estimate rather than an official figure" unprompted, and offered to draft
the data request to the block office. Only gemini was generic (budget line-items with no
exists/does-not-exist analysis).
So per our own decision rule: benchmark-4 proceeds as the REDUCED core. Our epistemic layer's
pitch is not "agents cannot do this" - it is "agents do this only at the top tier, only
sometimes, and you cannot tell which time you got."

## The reliability finding (this is the real chart)
Same model, adjacent questions, wildly different diligence:
- opus: 0/4 on points questions - it assumed "the Bengaluru complaints data" meant a local file,
  saw an empty workspace, and asked for an upload. The SAME model found OpenCity by itself in
  three earlier benchmarks. One phrasing assumption zeroed its capability.
- gpt: computed a real haversine distance (2.36 km) from a Supabase API on G1, then on G4
  claimed the workspace was empty and gave up - same session type, same data need, minutes apart.
- gpt's "densest cluster" was actually rows sharing identical default coordinates (a data entry
  artifact it did not flag); grok found a real 250m cluster and even distinguished lake-centroid
  vs shoreline distance on G4 using the OSM lake polygon.
Capability ceiling: high. Capability floor: low. Position in between: unpredictable per question.

## Satellite: our hypothesis was WRONG for one model, recorded happily
Prediction was "no agent touches rasters." grok downloaded GHSL tiles and computed built-up
growth around Perundurai SIPCOT (+11% within 2km, +12% within 5km, +14% within 10km, 2015-2020)
and ran the Erode vs Gobichettipalayam comparison from GHSL data (Erode more in absolute terms,
Gobi faster in percent). gpt produced built-up km2 figures (likely UCDB tables), opus named the
exact instruments and access paths (SHRUG VIIRS columns, GEE pipeline) without touching them,
gemini cited papers. Ladder: touched-data (grok) > data-adjacent (gpt) > named-with-path (opus)
> vague (gemini).

## What this settles for the narrative and benchmark-4
The Why story's final form: frontier agents have impressive PEAK behavior on measurement
planning, geodata, even satellite - and no floor. Across 240+ runs the constant is variance:
by tooling state (why1), by source draw (why2), by reachability (why3), by pressure (why4),
by question phrasing and model tier (why5). The system we built makes the ceiling the floor:
deterministic execution, declared sources, coordinates and rasters as connectors, estimates
gated and labeled, gaps returned as typed requests. Benchmark-4 (reduced): same questions
through our stack - repeatability contrast, points determinism, typed DataRequest display -
scored on the same legends. NOT claiming smarter estimation than frontier; claiming reliable.

## Collection completeness note (final, corrected): 48/48 COMPLETE. The bank holds 12 questions
(5 estimate-request, 4 points, 3 satellite) x 4 models; the earlier "52" was an arithmetic slip
in the run announcement, recorded here for honesty. One thin run: gemini E5 returned only a tool
error and is scored as no-answer.
