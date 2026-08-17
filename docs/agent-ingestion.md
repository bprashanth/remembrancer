# Agent workflow: producer chronology to Remembrancer

This is the hand-off procedure for an agent working in this repository.

## 1. Import a snapshot

From the Remembrancer root:

```bash
python3 tools/import_chronology.py ../paperroast/chronology \
  --source-id paperroast \
  --repo https://github.com/bprashanth/paperroast
```

The command copies Markdown into `chronology/<source-id>/` and writes
`_source.json` with the upstream repository, commit, import time and SHA-256 of
each file. The producer remains canonical. Re-run the command whenever its
chronology changes. The importer updates matching files but does not silently
delete files that disappeared upstream; use `--prune` only after checking why.

## 2. Copy the evidence cut

Read the imported files in filename order. For each measured claim, follow its
paths in the producer checkout. Copy the useful design, code, small data,
scores, results and raw runs to `narrative/evidence/<source-id>/`. Do not copy
caches, weights, credentials or a large generated working set without a reason.
Read [`evidence-policy.md`](evidence-policy.md) before making the cut.

Add a short README to the evidence folder saying what is present and what was
left out. Update `sources.json` with:

- the narrative pages;
- the imported chronology path;
- the local evidence path and what it contains;
- anything material that could not be copied.

Update `narrative/sources/index.html` with links to those local files. Remove
empty repository links. A citation is useful only if a reader can drill into
the result from this checkout.

## 3. Update, do not regenerate, the narrative

Follow [`narrative-authoring.md`](narrative-authoring.md). Compare the new
chronology with the existing page and preserve human-written phrasing unless a
new result makes it wrong. Add or change only the sections affected by new
understanding.

## 4. Verify

```bash
python3 tools/verify.py
python3 tools/serve.py
```

Open every changed page, follow its source links, and test one edit/save cycle.
Review `git diff` before committing. Remembrancer owns the narrative and
published site; it does not take ownership of producer code or raw private data.
