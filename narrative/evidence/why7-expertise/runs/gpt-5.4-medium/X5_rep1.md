# X5 rep1 x gpt-5.4-medium
Q: From the iChangeMyCity 2019-2022 complaints CSV on OpenCity, compute the straight-line distance between the two farthest apart garbage complaints in HSR Layout ward using the latitude and longitude columns. Show the two records and the haversine calculation. Citations.
elapsed:93s

---

Using the OpenCity `I Change My City Complaints Log - 2019 - 2022` CSV, I treated “garbage complaints in HSR Layout ward” as rows where `ward_title = HSR Layout` and `category_title = Garbage and Unsanitary Practices`, using the documented CSV fields `ward_title`, `category_title`, `latitude`, and `longitude`.[[1]](https://data.opencity.in/dataset/i-change-my-city-data/resource/a60abf5c-3a15-4967-af32-c3074248580f)[[2]](https://data.opencity.in/api/3/action/package_show?id=i-change-my-city-data) Among the 98 such HSR Layout rows with valid coordinates, the two farthest apart are about **4.484 km** apart by haversine distance.

## Two Farthest Records
**Record 1**
- `created_at`: `1-7-2019 13:39`
- `title`: `Garbage`
- `sub_category_title`: `Clearance Of Garbage Dump Or Black Spot`
- `location`: `10, Muneswara Nagar, Sector 6, Hsr Layout, Bengaluru, Karnataka 560068, India`
- `address`: `NIIT BACKSIDE`
- `latitude`: `12.91398619`
- `longitude`: `77.62564201`

**Record 2**
- `created_at`: `2/15/2020 16:35`
- `title`: `Road clearing material is just left. This place can be used to pl...`
- `sub_category_title`: `Clearance Of Garbage Dump Or Black Spot`
- `location`: `6Th Main Road, Bellandur, Bangalore, In, India`
- `address`: `NULL`
- `latitude`: `12.92323839`
- `longitude`: `77.66591406`

These values come from the published OpenCity complaints CSV resource for 2019-2022.[[1]](https://data.opencity.in/dataset/i-change-my-city-data/resource/a60abf5c-3a15-4967-af32-c3074248580f)[[2]](https://data.opencity.in/api/3/action/package_show?id=i-change-my-city-data)

## Haversine Calculation
Using Earth radius `R = 6371 km`:

- `phi1 = radians(12.91398619) = 0.225391578573`
- `phi2 = radians(12.92323839) = 0.225553059926`
- `dphi = radians(12.92323839 - 12.91398619) = 0.000161481353`
- `dlambda = radians(77.66591406 - 77.62564201) = 0.000702879869`

Formula:

```text
a = sin²(dphi/2) + cos(phi1) * cos(phi2) * sin²(dlambda/2)
c = 2 * atan2(sqrt(a), sqrt(1-a))
d = R * c
```

Substituting:

```text
a = sin²(0.000161481353/2)
  + cos(0.225391578573) * cos(0.225553059926) * sin²(0.000702879869/2)
  = 0.000000123855789

c = 2 * atan2(sqrt(a), sqrt(1-a))
  = 0.000703863038628

d = 6371 * 0.000703863038628
  = 4.484311419 km
```

So the straight-line distance between those two complaints is **4.484 km** (about **4,484 m**).

## Citations
[1] OpenCity CKAN resource page for `I Change My City Complaints Log - 2019 - 2022`: <https://data.opencity.in/dataset/i-change-my-city-data/resource/a60abf5c-3a15-4967-af32-c3074248580f>  
[2] OpenCity CKAN API `package_show` for `i-change-my-city-data`, including the direct CSV resource URL and schema metadata: <https://data.opencity.in/api/3/action/package_show?id=i-change-my-city-data>

If you want, I can also give you the exact Python snippet used to reproduce the result from the CSV.
