# G1 rep1 x cursor-grok-4.5-medium
Q: In the Bengaluru complaints data, what is the distance in km between the two farthest apart garbage complaints in HSR Layout ward? The data has latitude and longitude. Give citations.
elapsed:156s

---

**~4.48 km** (haversine; ~4.49 km on WGS84).

Using the [I Change My City Complaints Log (2019–2022)](https://data.opencity.in/dataset/i-change-my-city-data) from OpenCity / Janaagraha — which includes `latitude`, `longitude`, and `ward_title` — there are **98** complaints in **HSR Layout** under **Garbage and Unsanitary Practices**. The maximum pairwise distance is between:

| | Coordinates | Location (in data) |
|---|---|---|
| A | 12.91398619, 77.62564201 | Muneswara Nagar, Sector 6, HSR Layout |
| B | 12.92323839, 77.66591406 | 6th Main Road, Bellandur (ward tagged HSR Layout) |

Both are subcategory **Clearance Of Garbage Dump Or Black Spot**.

**Citations**
- Dataset: [I Change My City Data – OpenCity CKAN](https://data.opencity.in/dataset/i-change-my-city-data)
- Resource: [Complaints Log 2019–2022 (CSV)](https://data.opencity.in/dataset/i-change-my-city-data/resource/a60abf5c-3a15-4967-af32-c3074248580f)
