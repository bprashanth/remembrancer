# Remembrancer

<img src="assets/remembrancer.png" alt="The Remembrancer" width="240">

This is where we keep what we have learnt from experiments and benchmarks.

Producer repositories do the work and append notes to `chronology/`.
Remembrancer imports those notes, copies the evidence that matters, turns the
current understanding into a readable page, and publishes it on Netlify.

```text
producer repo                 remembrancer                         consumer
-------------                 ------------                         --------
code + data          |------> imported chronology
experiments          |        source/evidence             -------> idlisseus
chronology/ ---------|        narrative + Netlify
```

## The lightweight hand-off

A producer needs only timestamped Markdown:

```text
chronology/
  2026-08-16T0915-what-we-tried.md
  2026-08-16T1440-what-we-found.md
```

Each file needs a heading and free-form notes. Measured claims should end with
ordinary Markdown links to their data, code or repository. Numbered legacy
chronologies are accepted too.

- [Chronology protocol](docs/chronology-protocol.md)
- [How an agent imports chronology into Remembrancer](docs/agent-ingestion.md)
- [How to compress chronology into a narrative](docs/narrative-authoring.md)
- [What evidence we copy and how citations work](docs/evidence-policy.md)
- [How we write here](docs/writing-style.md)
- [Machine-readable source and evidence registry](sources.json)

## Import from a producer

```bash
python3 tools/import_chronology.py ../paperroast/chronology \
  --source-id paperroast \
  --repo https://github.com/bprashanth/paperroast
```

Imported notes live in `chronology/<source-id>/`; `_source.json` records where
they came from. The producer still owns the work. Remembrancer keeps the small
evidence cut needed to check the published claims.

## Edit the site locally

```bash
python3 tools/serve.py                 # 127.0.0.1:6000
```

Open <http://127.0.0.1:6000>, enter any narrative, and use **Edit**. The local
editor shows Markdown on the left and a live preview on the right. A line
containing `---` starts a new section. Figure explanations are editable in the
same source. The preview updates in place and keeps its scroll position while
you type. **Save** writes the rendered continuous page atomically back to that
page's `index.html`, closes the editor and shows the normal page; a timestamped backup is kept under
`.remembrancer-backups/`. The deployed Netlify site has no editing controls and
no file-writing endpoint.

The local index shows both published and draft narratives from `site.json`.
Drafts are for review and are removed from the Netlify build. Change a
narrative's status to `published` only after checking it.

### Edit from a laptop through SSH

The safest setup keeps the editor bound to loopback on the server. On the
server, run the command above. On the laptop, run:

```bash
ssh -N -L 6000:127.0.0.1:6000 <user>@<server>
```

Then open <http://127.0.0.1:6000> on the laptop. SSH carries the request to the
server's loopback socket, so no public listening port is required.

If a container or network namespace makes a wildcard bind necessary, use:

```bash
python3 tools/serve.py --host 0.0.0.0
```

Keep using the SSH tunnel and block TCP 6000 in the server's public firewall.
The site may be read over a non-loopback connection, but the save endpoint
rejects it; file writes are accepted only when the server sees a loopback
client. Stop the process when editing is finished.

After editing:

```bash
python3 tools/verify.py
git diff
git add -A && git commit
```

## Publish

Netlify runs `python3 tools/build_site.py` and publishes `.netlify-site/`. The
build copies the static site and removes every narrative marked `draft` in
`site.json`. The Python editor still serves the full `narrative/` directory.

## Repository layout

```text
assets/               repository branding
chronology/           provenance-preserving producer snapshots
docs/                 protocol and authoring instructions
narrative/            the static site published by Netlify
tools/import_chronology.py
tools/serve.py         localhost editor and static server
tools/verify.py        structural checks
sources.json           narrative to checked-in evidence map
site.json              published or local-review status for each narrative
netlify.toml
```
