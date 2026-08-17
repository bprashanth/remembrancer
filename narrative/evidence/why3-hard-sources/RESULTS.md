# WHY-3 hard sources results (2026-07-18, 20 isolated runs: 4 models x 5 verified-hard questions)

## Headline
At the hard end of the source spectrum, models almost never invent. What they do instead:
quietly answer FROM A DIFFERENT SOURCE OR YEAR than the one that actually holds the answer,
usually a more reachable one. The number is real, the citation is real, and it is not the
answer to the question as asked. Only 1 of 4 models ever opened the actual buried document.

## The clean diligence ladder (the two questions where hardness = pure reachability)
H1 (ration shop count inside a 2023-24 statistical handbook PDF, gold 40 = 15 full + 25 part):
  grok FOUND the exact PDF and Table 9.1: 15/25/40 - the only model of four.
  opus and gemini hit the cliff honestly (no number, pointed to the supply office).
  gpt used the 2018-19 edition on data.gov.in instead - close-looking, wrong vintage.
H4 (hired labour cost in a paper's Table 2, gold Rs 55,660/ha): opus, grok, gpt all found the
  actual 2022 paper and the exact figure. gemini cited a 2013 study instead.
So: reachability diligence exists at this tier, varies hugely by model, and grok was the only
one to go 2 for 2.

## The trap we set turned out to be the OTHER finding again
On H2 (villages in a taluk), H3 (which bank has most branches), H5 (milk co-op societies),
every model answered from a different legitimate basis than our gold source: revenue-village
lists instead of the PDS portal's village list (30 vs our 35 vs census 38), live IFSC
directories instead of the 2020 research deposit (leader flips from Canara to IOB depending
on basis), current policy notes instead of the archived 2011-12 handbook (482 societies today
vs 713 then). Mostly they SAID what basis they used, which is fair behavior. Bank design
lesson, logged honestly: those three golds encode an exotic basis, so they measure basis
divergence (already proven in WHY-2), not reachability. Only H1/H4-style questions measure
the diligence cliff cleanly. benchmark-2b should add 3 more H1-type questions if we want a
tighter estimate than "1 of 4".

## Scoring summary per model (H1-H5)
| model | reached exact | different basis, stated | honest cliff | wrong-vintage substitute |
|---|---|---|---|---|
| grok-4.5 | 2 | 2 | 1 | 0 |
| opus-4.6 | 1 | 2 | 2 | 0 |
| gpt-5.4 | 1 | 2 | 0 | 2 |
| gemini-flash | 0 | 2 | 1 | 2 |
Silent fabrication: 0 of 20. The failure mode of 2026 frontier agents is not lying;
it is answering a slightly different question than you asked, with confidence and citations.

## What this gives the narrative
The three Why assets now tell one connected story:
WHY-1: with tools working, agents are mostly honest - but honesty depends on invisible tooling
state, and answers silently inherit whatever data is lying around.
WHY-2: ask again and the source lottery reruns; five cited unemployment figures for one year.
WHY-3: push into genuinely hard sources and agents substitute the reachable-source answer for
the true-source answer, and say so only in the fine print.
None of these are fixed by a smarter model (the frontier tier does all three). All three are
fixed by construction in a system where the source set is declared, the query is executed by
code, and the basis is stamped on every number.
