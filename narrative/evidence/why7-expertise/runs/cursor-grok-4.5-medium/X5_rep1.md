# X5 rep1 x cursor-grok-4.5-medium
Q: From the iChangeMyCity 2019-2022 complaints CSV on OpenCity, compute the straight-line distance between the two farthest apart garbage complaints in HSR Layout ward using the latitude and longitude columns. Show the two records and the haversine calculation. Citations.
elapsed:111s

---

**4.484 km** separates the two farthest garbage complaints in HSR Layout (98 complaints with valid lat/lon in the OpenCity CSV).

### Filter
- Source: [I Change My City Complaints Log – 2019–2022](https://data.opencity.in/dataset/i-change-my-city-data/resource/a60abf5c-3a15-4967-af32-c3074248580f) ([dataset page](https://data.opencity.in/dataset/i-change-my-city-data); Janaagraha iCMyC via OpenCity)
- `ward_title` = `HSR Layout`
- `category_title` = `Garbage and Unsanitary Practices`
- Valid `latitude` / `longitude`

### Two farthest records

| Field | Record A | Record B |
|---|---|---|
| created_at | 1-7-2019 13:39 | 2/15/2020 16:35 |
| title | Garbage | Road clearing material is just left… |
| location | 10, Muneswara Nagar, Sector 6, Hsr Layout… | 6Th Main Road, Bellandur, Bangalore… |
| address | NIIT BACKSIDE | NULL |
| latitude | **12.91398619** | **12.92323839** |
| longitude | **77.62564201** | **77.66591406** |
| ward_title | HSR Layout | HSR Layout |
| category_title | Garbage and Unsanitary Practices | Garbage and Unsanitary Practices |
| sub_category_title | Clearance Of Garbage Dump Or Black Spot | Clearance Of Garbage Dump Or Black Spot |
| status | Resolved | Resolved |

### Haversine (mean Earth radius \(R = 6{,}371{,}000\) m)

\[
a = \sin^2\!\left(\frac{\Delta\phi}{2}\right) + \cos\phi_1\cos\phi_2\sin^2\!\left(\frac{\Delta\lambda}{2}\right),\quad
c = 2\,\mathrm{atan2}(\sqrt{a},\sqrt{1-a}),\quad
d = R\,c
\]

- \(\Delta\phi = 0.00925220^\circ = 1.6148135\times10^{-4}\) rad  
- \(\Delta\lambda = 0.04027205^\circ = 7.0287987\times10^{-4}\) rad  
- \(a = 1.23855789\times10^{-7}\)  
- \(c = 7.0386304\times10^{-4}\)  
- \(d = 4484.311\) m **= 4.484 km**

These are also the westernmost and easternmost garbage points in that ward filter.
