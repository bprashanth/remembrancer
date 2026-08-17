# WHY-3: what got disqualified, and why

Honest-gap log, same spirit as GAPS.md elsewhere in this program. These are candidate hard-source
questions that were tried this session and dropped because the source could not actually be
opened, not because the topic was uninteresting.

- **MGNREGA MIS (nregastrep.nic.in)**, suggested as the default H2 pick — every request this
  session came back 503 or 403, tried with plain curl, a browser user-agent, and a different
  MGNREGA subdomain (nreganarep.nic.in). Disqualified per the brief's own fallback rule, swapped
  to the Tamil Nadu PDS citizen portal instead (see H2 in SOURCES.md).
- **eCourts NJDG (njdg.ecourts.gov.in)**, tried as a possible portal-navigation source for case
  pendency numbers — it is a JavaScript dashboard with no discoverable public data API found in
  the time available, and the district-court sibling site (districts.ecourts.gov.in) refused the
  connection outright. Disqualified.
- **Agmarknet 2.0** (mandi price portal) — actually found its real backend API
  (`api.agmarknet.gov.in/v1/daily-price-arrival/report`) and the correct internal ids for Turmeric
  and Erode, but never found the correct "dashboard" identifier the report endpoint needs; every
  guess returned an unrelated default result (Pear prices from Maharashtra) instead of an error.
  Disqualified rather than guess an unverified number.
- **UDISE+ district report cards** — Tamil Nadu does not feed its raw school data into the
  national UDISE+ portal the normal way (it keeps its own MIS and bulk-uploads), so no clean
  Erode district report card could be located within the time budget. Disqualified.
- **ICRISAT District Level Database** (the brief's suggested H3 example) — both
  `data.icrisat.org` and `dataverse.icrisat.org` refused the connection this session, and the one
  page that did load said the full dataset is "too large to download" with only documentation
  PDFs offered individually. Disqualified in favour of a SHRUG-hosted contributed dataset instead.
- **RBI DBIE** (`dbie.rbi.org.in` / `data.rbi.org.in`) — TLS certificate mismatch on one hostname,
  empty client-rendered shell on the other. Would need a real browser session to navigate its
  report builder, not achievable with the fetch tools available this session. Disqualified.
