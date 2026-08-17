# WHY-5: where should you measure what

Status: benchmark-3, scored (47/52; stragglers collecting) | 2026-07-18 | isolated protocol

Question this asset answers: when data is missing, can agents tell you what to measure, where,
with what budget - and do they reach for the instruments (coordinates, satellite) that could
answer questions directly?

Buckets: estimate-and-request (incl. the Rs 2 lakh budget question and the 300-household survey
design, scored against our pack + GAPS key: waste = recommending collection of data that exists;
overreach = claiming estimation with no basis) | points data (lat/lon in public complaint CSVs;
scored computed-from-coordinates / label-fallback / no-reach) | satellite-derived (nightlights,
built-up; scored touched-data / named-instrument-with-path / vague).
Files: bank.json (questions + per-question rubric inline), collect5.py, runs/, digest5.md,
RESULTS.md. Key honest finding: our estimation-gap hypothesis did not survive; the real finding
is ceiling-vs-floor variance. See RESULTS.md.
