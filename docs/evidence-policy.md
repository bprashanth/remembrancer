# Keep the evidence here

Remembrancer should be useful on its own. If a narrative says a benchmark found
something, a reader should be able to click through to the benchmark without
hunting through another repository.

## What to copy

Put an evidence cut under `narrative/evidence/<source-id>/`. Copy the smallest
set that lets somebody inspect the claim:

- the benchmark design and question bank;
- answer keys or scoring rules;
- the code that ran and scored it;
- raw or per-model runs;
- aggregate results;
- small input data and manifests.

Do not copy a whole working directory by default. Leave out caches, model
weights, generated corpora, credentials, private data and large raw files that
do not help a reader check the result. Say what was left out in the evidence
folder's `README.md`.

## How citations work

Narrative citations use relative links into `narrative/evidence/`. Do not add a
repository home page as a substitute for evidence. Do not keep an empty source
entry just because a producer repository exists.

A useful citation lands on one of these:

- a result or scoring file for a headline claim;
- a run index when several runs make the point;
- an exact run when the prose discusses one answer;
- an evidence index when the sentence describes the whole benchmark.

The public Netlify site serves the same evidence tree, so these links work both
on the site and in the checkout.

## When the data cannot be copied

Be direct. Keep the runnable code, schemas, manifest and aggregate result if
they are safe to publish. In the evidence README, name what is missing and why.
Do not invent a link and do not imply that a result is fully reproducible when
the private input is unavailable.

## Updating an evidence cut

Treat copied evidence as a snapshot. Do not edit a raw run to match the
narrative. Copy a fresh cut from the producer, check the diff, update
`sources.json`, rebuild any browser indexes, then update the prose only where
the evidence changed.
