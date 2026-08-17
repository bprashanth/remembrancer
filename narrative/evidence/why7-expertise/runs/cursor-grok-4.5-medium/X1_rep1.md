# X1 rep1 x cursor-grok-4.5-medium
Q: Using the Janaagraha iChangeMyCity complaints CSV on OpenCity (it has latitude and longitude columns) and the OpenStreetMap polygon for Bellandur lake, how many complaints fall within 1 km of the lake? Use haversine distance to the lake shoreline, not just the centroid. Show your working and citations.
elapsed:177s

---

**283 complaints** fall within 1 km of Bellandur Lake’s shoreline.

### Sources
1. **Complaints:** [OpenCity — I Change My City Complaints Log (2019–2022)](https://data.opencity.in/dataset/i-change-my-city-data/resource/a60abf5c-3a15-4967-af32-c3074248580f) (Janaagraha iCMyC), with `latitude` / `longitude` columns — 16,071 rows, all geocoded.
2. **Lake polygon:** OpenStreetMap [relation 19751547](https://www.openstreetmap.org/relation/19751547) (*Bellandur Lake* / *Bellandur Tank*, `natural=water`, `water=lake`, Wikidata [Q4883488](https://www.wikidata.org/wiki/Q4883488)), fetched via Overpass (OSM base timestamp 2026-07-20). Confirmed via Nominatim as a MultiPolygon (~3.17 km² across 4 outer rings).

### Method
1. Extract the multipolygon outer rings (410 shoreline edges).
2. For each complaint, if it lies **inside** any ring → distance = 0; else compute **minimum haversine distance to the shoreline** (closest point on each edge via local equirectangular projection, then haversine with \(R = 6{,}371{,}000\) m).
3. Count points with distance ≤ 1,000 m.

### Result
| Metric | Count |
|---|---|
| Complaints with valid coords | 16,071 |
| **Within 1 km of shoreline** | **283** |
| Of those inside the lake polygon | 1 |
| Within 1 km of polygon centroid (comparison only) | 4 |

Centroid distance is a poor proxy here because the lake is ~3–4 km long; shoreline distance is the right measure. Edge-based and vertex-only haversine both gave **283** with a wider search pad, so the count is stable.
