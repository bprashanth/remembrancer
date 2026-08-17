# WHY-7 expertise results (2026-07-20, 15 runs: 3 models x 5 expert-phrased questions)

## Headline
Rewrite the question the way a domain person would (name the dataset, the instrument, the
method) and the same tools that shrugged at naive phrasing suddenly work, AND agree with each
other.

## The clean exhibit: the Bellandur lake question
Naive phrasing (why5): opus asked for a file upload 4 times, gpt said the workspace was empty,
grok computed centroid-only (~4-5 points), gemini cited news articles. Nobody had the answer.
Expert phrasing (name the CSV, name the OSM polygon, say shoreline-not-centroid, say haversine):
- grok: 283 complaints within 1 km of shoreline (edge and vertex methods both 283)
- gpt: 283, validated at three shoreline sampling resolutions (10m / 5m / 2m spacing, all 283)
- gemini-flash: fetched the polygon's 410 shoreline nodes from the OSM API, spherical
  point-to-segment distance over all 16,071 complaints: 283
Three models, three independent implementations, one answer. The naive version had produced
zero answers; the expert version produced perfect cross-model agreement.

## Other rows
- X3 imputation: grok gave an 11-15% youth unemployment band for Anthiyur block WITH a power
  analysis (a 400-household pilot is too weak; ~1,200 households / 35 FSUs is the smallest
  design that validates the band). That is professional survey-statistician output, unlocked
  purely by the phrasing. gpt and gemini both produced grounded calculations with census
  village-level inputs.
- X4 all-bases: every model produced the labeled three-basis unemployment answer (ILO modelled
  vs PLFS US/CWS vs CMIE) and recommended PLFS for NGO reporting with sane caveats. The claim-1
  source lottery disappears when the asker knows to request all bases. The asker almost never
  knows.
- X5 farthest-pair: grok computed 4.484 km with the full haversine working shown (west/east
  extremes). Note the naive gpt run had produced 2.36 km from a partial slice; scoring the
  discrepancy is on the follow-up list.
- X2 nightlights: the one weak row. grok timed out at 900s mid-computation; gpt named taluk
  claims with thin sourcing (treated as unverified); gemini gave the correct instrument and an
  extraction pipeline without running it. Raster work at question-time remains the frontier's
  least reliable skill even with expert phrasing.

## What this means
Domain knowledge in the question buys capability AND consistency. The knowledge required
(which CSV, which polygon, shoreline vs centroid, which survey concept, what sample size) is
exactly what NGO field staff should not need to carry. Moving it into the tool is goal 2 of
the proposal.
