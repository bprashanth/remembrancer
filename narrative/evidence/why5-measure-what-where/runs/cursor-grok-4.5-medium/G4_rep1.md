# G4 rep1 x cursor-grok-4.5-medium
Q: How many complaints in the Bengaluru data were logged within about 1 km of Bellandur lake? Use the coordinates in the data. Citations please.
elapsed:376s

---

**283 complaints** fall within about 1 km of Bellandur Lake.

### Method
Used OpenCity’s **I Change My City Complaints Log (2019–2022)** — 16,071 rows with `latitude` / `longitude`. Measured geodesic distance from each complaint to the **Bellandur Lake shoreline** (OpenStreetMap MultiPolygon), not the lake center. Counted points with distance ≤ 1.0 km (including one mapped on the lake itself).

Most of these are in Bellanduru (134), then Koramangala (40), HSR Layout (37), and Agaram (36).

### Citations
1. [I Change My City Data – Complaints Log 2019–2022 (OpenCity / Janaagraha)](https://data.opencity.in/dataset/i-change-my-city-data) — resource `a60abf5c-3a15-4967-af32-c3074248580f`
2. [Bellandur Lake geometry](https://www.openstreetmap.org/relation/19751547) — OSM relation 19751547 (via Nominatim)
3. [Bellandur Lake](https://en.wikipedia.org/wiki/Bellandur_Lake) — location reference (~12.934°N, 77.663°E)

**Note:** A 1 km circle around the lake *centroid* only yields ~4–5 points, because the lake itself is ~3.6 km long. Shoreline distance is the right reading of “within about 1 km of the lake.”
