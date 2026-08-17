# WHY-2 repeatability pilot results (2026-07-18, 60 runs: 4 models x 5 questions x 3 repeats)

Protocol: each run in an isolated container (no host filesystem, fresh empty workdir, web on),
so no run could see our files or another run's downloads. Same question, asked 3 times.

## Headline
Ask the same agent the same question three times and you often get different numbers, from
different sources, each time confidently cited. The clearest case: "What was India's
unemployment rate in 2021?" produced FIVE different figures across 12 runs, all with citations:
4.2% (PLFS), 5.98% (attributed to World Bank, actual WB value is 6.38 - wrong number under a
correct-looking citation), 6.38% (World Bank/ILO), ~7.9% (CMIE), 7.8% (GlobalData). Nothing
was invented; every number exists somewhere. The user just never knows which one they got.

## Agreement per model (3 repeats agree on number AND source basis)
| model | consistent questions (of 5) | notes |
|---|---|---|
| cursor-grok-4.5 | 5/5 | most consistent; always named its basis and the data window |
| gpt-5.4 | 4/5 | R3 rep1 said 5.98% citing the WB indicator whose real value is 6.38% |
| claude-4.6-opus | 3/5 | R3 rep1 grabbed GlobalData 7.8%, reps 2-3 used WB 6.38% |
| gemini-3.5-flash | 1/5 | three repeats of R1 used three different bases (news articles, BBMP CSV, ICMC yellow-spot rows) |

## Second finding: consistency within a model does not mean agreement between models
grok answered 4.2% (PLFS) all three times; gpt and opus mostly 6.38% (WB/ILO). Both self-
consistent, permanently 2.2 points apart. Two NGO staffers using different tools would build
contradicting dashboards forever, each reproducible, each cited.

## Third finding: the good behavior exists and is scoreable
On "population of Erode" most models presented city vs agglomeration vs district as separate
labeled figures (a 13x spread) instead of picking one silently. That is exactly the
"name your basis" behavior our system enforces by construction. It happened reliably on the
population question (ambiguity is famous) and almost never on the unemployment question
(ambiguity is just as real - usual status vs weekly status vs private trackers - but less known).

## Scoring notes
Where repeats went to the same dataset (BBMP grievances), agreement was perfect across all
models (R1: 332 x12; R2: Rajarajeshwari Nagar x12). Divergence appears exactly where multiple
legitimate sources exist. So the driver is source lottery, not sampling randomness.
Raw transcripts: runs/. Digest: repeat-digest.md. Per-run outcomes: repeat-digest + this file
serve as the reviewed record for the pilot; benchmark-2 full run will get scoring.json form.

## Verdict on expanding to 20 questions
Not needed to establish the effect. Worth doing later ONLY for the two-source question class
(the R1/R2/R4 type) to estimate the divergence RATE precisely. The pilot already gives the
narrative its chart: one question, twelve trusted answers, five numbers.
