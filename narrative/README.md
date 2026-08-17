# Published narrative site

This directory holds the full static site, including local-review drafts. The repository-level
[`README.md`](../README.md) explains importing chronology, authoring narratives,
local file-writing edits and deployment.

Pages:

- `index.html` — the Remembrancer index;
- `field-notes/index.html` — Field notes from Insight Out;
- `form-data/index.html` — short Form data narrative;
- `form-data-deep/index.html` - Form data 2;
- `sources/index.html` — links into the checked-in evidence;
- `evidence/` — benchmark code, data, results and runs used by the narratives.

Do not use `python3 -m http.server` for authoring: it cannot save. From the
repository root, use:

```bash
python3 tools/serve.py
```

The default address is `127.0.0.1:6000`. It lists both published and draft
narratives from `site.json`. Netlify builds a separate public folder with draft
pages removed. The deployed site stays static. Only
the development server injects the editor, and file writes remain restricted to
loopback clients. See the repository README for SSH forwarding and the optional
`--host 0.0.0.0` mode.
