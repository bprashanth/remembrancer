# G2 rep1 x cursor-grok-4.5-medium
Q: Using the latitude and longitude in the Bengaluru complaints data, which roughly 500m area of Bellandur ward has the densest cluster of complaints? Citations please.
elapsed:219s

---

**Kasavanahalli** (Eastwood Township / Hosa Road area), centered near **12.9057°N, 77.6760°E**.

Using the geo-tagged [I Change My City Complaints Log (2019–2022)](https://data.opencity.in/dataset/i-change-my-city-data) on OpenCity (Janaagraha), filtered to ward **Bellanduru** (727 complaints with lat/long):

- A sliding **~500 m** window (250 m radius) peaks at **39 complaints** around that point — denser than any other pocket in the ward.
- Offset **500 m × 500 m** grids also peak there (up to **42** complaints), not at Bellandur Junction.
- Complaints are mostly road/pothole and streetlight issues along Kasavanahalli / Eastwood Twp / Hosa Rd.

Map: [OpenStreetMap at the cluster center](https://www.openstreetmap.org/?mlat=12.90569&mlon=77.67602#map=17/12.90569/77.67602)

**Citations**
1. [I Change My City Complaints Log – 2019–2022 (OpenCity / Janaagraha)](https://data.opencity.in/dataset/i-change-my-city-data) — fields include `latitude`, `longitude`, `ward_title`
2. Resource page / data dictionary: [a60abf5c… on OpenCity](https://data.opencity.in/dataset/i-change-my-city-data/resource/a60abf5c-3a15-4967-af32-c3074248580f)

Runner-up pockets: **AET Junction, Doddakannelli** (~37 in 250 m) and **Bellandur Main Road / ORR near Central Mall** (~12.925°N, 77.674°E).
