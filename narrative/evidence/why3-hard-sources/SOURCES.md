# WHY-3: hard-source questions, how each answer was actually pulled out

Same spirit as WHY-1's ASSET.md: plain words, no jargon. These are 5 questions where the true
answer cannot be found by searching the open web or opening a friendly CSV. Each one required
opening a real document or a real system and digging. This file records exactly how, so anyone
can redo the same steps and get the same number.

All five were opened and checked personally on 2026-07-19. Nothing here comes from training
memory — every number below was read off a file or an API response fetched this session.

## H1 — Fair price shops in Thalavadi taluk (pdf-table)

**How found:** Searched for "Erode District Statistical Handbook pdf". The district's own website
(erode.nic.in) linked straight to the 2023-24 edition, a 183-page PDF hosted on the government's
shared S3WaaS cloud.

**Extraction trail:** Downloaded the PDF, ran it through `pdftotext -layout` (plain fetch tools
choke on PDFs — you get raw PDF object code back, not readable text). Found the table of contents,
jumped to section 9 "Civil Supplies", table 9.1 "Number of Fair Price Shops", read the row for
Thalavadi taluk: 15 full-time + 25 part-time = 40 total, sourced in the table itself to the
District Supply Office, Erode.

**Hardness: 3/5.** The PDF itself is one search away and not hidden. What makes it hard is that
it is a 183-page scanned-style government PDF with no usable text unless you extract it properly,
and the actual number is two menu-clicks plus 45 pages deep, not summarized anywhere else on the
web (no news article or aggregator reports Thalavadi's ration shop count specifically).

## H2 — Villages under Anthiyur taluk (portal)

**How found:** The brief suggested trying MGNREGA's nregastrep.nic.in first. That portal refused
every request this session (503/403 no matter the URL, subdomain, or browser fingerprint used —
see NOTES.md). Swapped to a different real government portal per the fallback instruction: the
Tamil Nadu Public Distribution System citizen site, tnpds.gov.in, which needs the same kind of
click-through (state to district to taluk to village) that a field worker would actually do.

**Extraction trail:** tnpds.gov.in is a modern single-page app — fetching the page gives you an
empty shell (`<div id="root"></div>`), no data. Downloaded its compiled JavaScript bundle
(`main.<hash>.js`) and searched it for API route strings, which surfaced the backend host
`portalwebservice.tnpds.gov.in` and the route names `district/getall`, `taluk?districtid=`,
`village?talukid=`. Called `district/getall` directly, found Erode's district id (12). Called
`taluk?districtid=12`, found Anthiyur's taluk id (244). Called `village?talukid=244`, got back a
JSON array of exactly 35 villages.

**Hardness: 5/5.** No form, no visible link, no documentation anywhere describes this API. It only
came out of reading the minified JavaScript the site ships to browsers, then chaining three calls
in the right order using ids each previous call revealed. A plain web search for "how many
villages in Anthiyur taluk Erode" turns up census-style numbers from generic data-aggregator
sites, not this portal's own count, so a model that just searches will not land here.

## H3 — Bank with the most branches in Erode (data-deposit)

**How found:** Went to ICRISAT's District Level Database first (the brief's suggested example) —
both `data.icrisat.org` and `dataverse.icrisat.org` refused the connection outright this session,
and the Dataverse listing for the dataset only exposed 3 documentation PDFs, saying the actual
data "is too large to download" as one file. Disqualified that path and moved to the SHRUG
platform (Development Data Lab), which hosts an "external contributions" table of India datasets
alongside its own core modules.

**Extraction trail:** `devdatalab.org/shrug_download/` builds its table from a public Google Sheet
(found by reading the page's own script tag). That sheet listed an "RBI Bank Branches" dataset
with a Google Drive download link. Downloaded it (an 8.6MB zip), unzipped it, and got a plain CSV
of 154,835 individual bank branch rows across India, each tagged with a 2011-Census district id
but no district name. Filtered to Tamil Nadu (`pc11_state_id=33`) and confirmed which numeric
`pc11_district_id` was Erode by checking which id's rows had Erode pincodes (638xxx) and addresses
that literally say "ERODE DISTRICT" (id 610 — a neighbouring id, 609, turned out to be Namakkal,
caught only because its pincodes were 636xxx/637xxx, not Erode's). Grouped the 427 Erode rows by
bank name: Canara Bank has the most, 50 branches.

**Hardness: 4/5.** The intended official source (ICRISAT) was completely unreachable. The dataset
that did work is a real researcher-contributed deposit (cites an IEG working paper), buried behind
a chain of Sheet-to-Drive links, delivered as a 150k-row unlabelled-by-name CSV where you have to
reverse-engineer which numeric code is your district before you can answer anything.

## H4 — Hired labour cost for organic turmeric in Erode (supplementary)

**How found:** Searched for turmeric-economics papers specific to Erode district. Several came up
on ResearchGate and Academia.edu, but both blocked direct fetches (403 Forbidden without a login).
Kept searching and found a mirror of a similarly-themed paper hosted directly by its journal,
International Journal of Research in Engineering, Science and Management (IJRESM), with a working
direct-download PDF link.

**Extraction trail:** Downloaded the PDF, extracted with `pdftotext`. The abstract only states the
headline cost-per-quintal and benefit-cost-ratio numbers. The actual labour cost is in Table 2,
"Cost and Returns of Organic Turmeric in the Sample Farms (Rs./ha)", row 2, "Hired Human Labour":
Rs 55,660/ha, 27.07% of total cost.

**Hardness: 3/5.** Getting to a working, openly downloadable PDF took several dead ends (two
paywalled/blocked mirrors first). Once open, the number itself is a genuinely buried line-item in
an itemised cost table, not something the abstract or any citation summary repeats.

## H5 — Milk co-op societies in Erode, historic (archived)

**How found:** Tried to find an older edition of the Erode handbook still linked from the live
site — the current site only lists 2023-24. Went looking for a delisted-but-once-real URL by
querying the Wayback Machine's CDX index for `erode.nic.in` pages mentioning "handbook", which
surfaced old index pages from 2008-09 through 2013-14 (`stathandbookYYYY.htm`), each of which used
to link to 47 small per-table PDFs (`dhYYYY-1.pdf` ... `dhYYYY-47.pdf`).

**Extraction trail:** Most of those 47-per-year PDF fragments were never actually captured by the
Wayback Machine (checked via the CDX API — empty results for most years). Found one that was: the
2011-12 edition's file 5 (`dh1112-5.pdf`, animal husbandry section) has a real snapshot from 2017.
Fetched the Wayback copy, extracted text, and read table 5.4 "Dairy Development": 713 societies
(including 3 milk chilling plants), 8,43,59,940 litres produced, valued at Rs 1,54,63,19,326.
Confirmed the original live URL (`erode.nic.in/dh1112/dh1112-5.pdf`) now returns 404 — the
document is genuinely gone from the current site, this is the only copy left.

**Hardness: 5/5.** This took real archaeology: find the old index pages via CDX search, discover
that most of the individual PDFs were never crawled, and get lucky that this particular one was.
A plain web search will not find this — the URL is gone from every current page and from Google's
index, it only exists as one specific timestamped Wayback snapshot.
