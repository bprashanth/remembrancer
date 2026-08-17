# Compressing chronology into narrative

A chronology records the work in time order. A narrative explains the present
understanding in argument order. Compression is editorial, not mechanical.

## Read before writing

1. Read every chronology entry in filename order, including corrections.
2. Open the checked-in results, data and code for the claims that carry the story.
3. Read the current narrative. Browser-edited prose is authored work, not a
   generated cache.
4. Check the entry in `sources.json` and the imported `_source.json` manifest.

## Make the cut

Write down five things before touching HTML:

1. What problem were we actually trying to solve?
2. What did we observe in the real world?
3. Which explanations survived measurement?
4. What did we try that failed, and why should it stay failed?
5. Where did the design land, and what remains uncertain?

Then group chronology entries under those ideas. Do not make one section per
entry. Time order is useful for discovery; argument order is useful for a
reader.

## Section contract

Each section should contain one idea in a single flowing page:

```html
<section class="entry"><div class="inner">
  <div class="tag">where this sits in the argument</div>
  <h2>The claim in plain language</h2>
  <p class="lead">Why it matters.</p>
  <p>The smallest amount of evidence needed to support it.</p>
  <p class="small"><a href="../sources/#source-id">sources</a></p>
</div></section>
```

Prefer a short version that a domain practitioner can follow. Add a second
version only when experiment detail materially changes how the result should be
trusted.

## Voice

- Use plain Indian English: direct, concrete and not over-polished.
- Explain technical words at first use.
- Keep exact numbers only when they carry the argument.
- Record uncertainty honestly: “in these 24 forms” is better than “models do”.
- Keep retractions and failed approaches. They are part of the understanding.
- Do not turn every paragraph into bullets or every result into a dashboard.

## Evidence rule

Every benchmark or experiment needs a local evidence trail. Keep, where
possible:

1. small checked-in data plus code and experiment design;
2. answer keys, scoring and raw runs;
3. checked-in results;
4. a clear note for private or deliberately omitted large inputs.

Put compact relative links in the relevant section and maintain the local map
in `narrative/sources/index.html` and `sources.json`. Do not use a repository
home page as a citation. See [`evidence-policy.md`](evidence-policy.md).

## Human refinement

Run `python3 tools/serve.py`, open the printed URL and choose a narrative. Press
**Edit** to open Markdown on the left and a live preview on the right. Separate
ideas with a line containing `---`. Interactive graphics remain embedded;
their `explanation` blocks are ordinary editable Markdown and open in the same
side panel on the published page. The preview updates without reloading and
keeps its scroll position. Press **Save** to write the rendered sections back
into the corresponding HTML file and return to the normal page. Commit the resulting diff normally.
The Netlify build contains only static HTML and does not expose the editor or
save endpoint. See the README for the exact workflow.

## Draft and published pages

Every narrative is listed in `site.json` with one of two statuses:

- `draft`: shown by the local Python server and left out of the Netlify build;
- `published`: shown locally and included in the Netlify build.

Keep a new or unverified narrative as `draft`. Promotion is one edit to
`site.json`; the landing-page links and Netlify output are generated from that
file. Run `python3 tools/build_site.py` if you want to inspect the exact public
folder before pushing.
