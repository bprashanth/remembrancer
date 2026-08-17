# WHY-5 design: where should you measure what (benchmark-3) - STATUS: designing, not yet run

## The claim to test
When data is missing, the most useful answer is a SPECIFIC data request: what to measure, where,
how much, and what can be safely estimated instead. We test whether agents can do the
estimate-vs-collect split that our system does by construction (estimate with stated basis
behind a gate; data request when the gate fails).

## Buckets (12 Q x 4 models x 1 rep = 48 runs, same isolated container protocol)
E1-E4 ESTIMATE-AND-REQUEST: partial data exists (census 2011, MGNREGA, MSME), question asks a
  present-day/block-level figure with no direct source. Good answer = labeled estimate with basis
  + uncertainty + targeted request. Includes THE BUDGET QUESTION: "We have Rs 2 lakh for data
  collection in Erode to understand livelihoods. What should we measure, where, and what can we
  estimate from existing data instead?" We score it against our pack + GAPS.md: recommending
  collection of data that ALREADY EXISTS = waste; claiming estimation where no basis exists =
  overreach. Only we can score this because we built the pack.
  Scoring dims: estimate-labeled-with-basis | request-specific (what/where/sample/frequency) |
  impute-vs-collect distinguished | recommends-collecting-what-exists (fail).
E.g. E2: "What is youth unemployment in Anthiyur block right now?" E3: "How many powerloom
  workers live in Chithode area today?" E4: "Are dyeing units in Perundurai paying more than
  farm work nearby?"
G1-G4 POINTS DATA (lat/lon): the public BBMP/ICMC complaint CSVs carry latitude/longitude
  columns. Questions answerable ONLY by using coordinates, not ward labels: "From the Bengaluru
  complaints data, what is the distance between the two farthest-apart garbage complaints in
  HSR Layout?" / "Which ~500m patch of Bellandur has the densest cluster of complaints?"
  Score: used-coordinates-and-computed | answered-by-ward-label-instead | didn't reach data.
S1-S3 SATELLITE-DERIVED (non-ecology: nightlights, built-up): "Which parts of Erode district
  saw the most nighttime-lights growth 2015-2023?" / "Has built-up area around the Perundurai
  SIPCOT expanded since 2015?" Public instruments exist (VIIRS nightlights, GHSL built-up).
  Score: touched-actual-data | named-instrument-with-access-path | vague-or-papers-only.
  Hypothesis: zero agents touch rasters; the good ones name the instrument.

## Chart (draft headline)
"Agents can tell you a number is missing. They rarely tell you what it would cost to know it,
and they never touch the instruments that could measure it."
## Files when run: bank.json, collect (reuse why2 container collector), runs/, digest, RESULTS.md
## NEXT ACTIONS: write bank.json golds/rubrics (E-bucket rubric from pack+GAPS.md), adapt
collector, launch 48 runs, judge, RESULTS + ASSET per onion contract. Register in INDEX.md.
