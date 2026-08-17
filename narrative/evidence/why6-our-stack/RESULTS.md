# WHY-6 results: same questions, our stack (lora9b003 + algebra + connectors), 2026-07-18

## Determinism: 7/7 questions, 3 repeats each - identical compiled plan AND identical executed
result every time. Responder-mode population answer: 3 repeats, identical text (greedy decoding).
The why2 chart's counterpart: where agents gave five cited unemployment figures, our stack gives
one (6.38%, World Bank/ILO series, basis stamped in provenance) three times out of three.

## The contrast table (agent benchmarks vs our stack, same questions)
| q | agents (why1/2/5) | our stack |
|---|---|---|
| Hoodi road complaints 2020 | 25 or 332 depending on source draw | 25, ICMC basis stamped, x3 identical |
| India unemployment 2021 | five figures (4.2 to 7.9), five bases | 6.38 (WB/ILO), x3 identical |
| Bellandur garbage trend | up or down depending on dataset | "falling" w/ slope note, ICMC basis, x3 |
| dyeing wages (never collected) | honest prose or laundered proxy | typed hole -> clarifying question (?proxy) |
| youth farm-exit (never collected) | prose refusals | typed data_request: "no data source maps this entity; add a connector or refine the term" |
| shops near bus stand (underspecified) | asked back (mostly) | typed hole ?place -> clarifying question, x3 |
| within 1 km of Bellandur lake | give-up / centroid-only estimate | WRONG (see below) but deterministic + self-explaining |

## The honest cell: our G4 is wrong, and that is the most instructive row
Our answer (2,708) mis-resolved "Bellandur lake" to the "lake complaints" category - caused by
our own week-old complaint-qualifier repair over-firing on the RELATE anchor - and the "about
1 km" never bound to threshold_km. BUT: the error is visible in ONE provenance line
("resolved: lake complaints, 54 rows"), reproduced identically 3/3, and the fix is a named
resolver rule + a regold. Compare: when agents were wrong (why2/why3) the error was invisible,
unreproducible, and unfixable. The claim this row supports is not "we are always right"; it is
"our wrongness is auditable and repairable." Bug filed for the harness (qualifier must not
rewrite RELATE anchors; threshold faithfulness) - fix + regold per golden discipline.

## Coverage, stated not hidden
Not expressible in the released algebra: all-wards ranking (needs GROUP - ALG-003, RFC open),
farthest-pair / densest-cluster / dispersion (spatial analysis ops - ALG-010, proposed). These
rows point at live governance proposals; the language grows through that pipeline, not ad hoc.

## Responder-mode population answer (R5)
District figure with rural/urban split, source document named, plus "no more recent count
exists; next census due" - and identical across repeats. Limitation noted honestly: it answered
the district basis only (the pack has no city figure); top agents surfaced the city/UA/district
three-way split more richly here.
