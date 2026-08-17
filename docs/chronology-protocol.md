# The chronology protocol

Chronology is the small hand-off between a producer repository and
Remembrancer. It is deliberately plain Markdown. There is no database, schema
package or generator to install.

## Producer layout

```text
chronology/
  README.md                         # optional: scope and reading note
  2026-08-16T0915-form-census.md
  2026-08-16T1440-first-extraction.md
  2026-08-18T1030-what-failed.md
```

The timestamp is local time in `YYYY-MM-DDTHHMM` form. Because filenames sort
lexically, `ls chronology/` is the reading order. Add a short lowercase slug
after the timestamp. Do not rewrite old entries just to make the final story
cleaner; add a new entry that corrects or supersedes them.

Older repositories with numbered files such as `01-landscape.md` are valid
legacy chronologies. Remembrancer preserves their filename order. New entries
should use timestamps.

## Entry format

Only two things are required:

```markdown
# A clear title

Free-form Markdown explaining what happened and what we now think.
```

For an experiment or benchmark, add a final evidence section:

```markdown
## Evidence

- [data](../data/run-17/results.json)
- [runner](../benchmarks/run_forms.py)
- [design notes](../benchmarks/run-17/README.md)
```

Links are ordinary paths relative to the chronology file. They are instructions
for the Remembrancer agent: copy the useful benchmark code, data and results
into Remembrancer and cite that local snapshot from the narrative. If data
cannot be copied, say why and point to the runner, manifest or result that can
be copied. A repository home page on its own is not evidence.

## What belongs in chronology

- a new observation;
- an experiment and its result;
- a failed approach worth remembering;
- a decision and the evidence behind it;
- a correction to an earlier belief;
- an open question that changes the next experiment.

Chronology is not polished documentation. It is an appendable trail from which
a narrative can later be made.
