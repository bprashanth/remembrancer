# S1 rep1 x claude-4.6-opus-high
Q: Which parts of Erode district saw the most growth in night-time lights between 2015 and 2023? Give citations I can check.
elapsed:75s

---

Based on my research, I need to be upfront: **there is no published study that specifically maps sub-district nighttime light growth within Erode district for 2015–2023.** However, existing research and open datasets let us identify which parts of the district likely saw the most growth, and you can verify this yourself. Here's what the evidence shows:

---

## Areas of Erode district with greatest night-time light growth (2015–2023)

Based on the available literature and geospatial data:

1. **Erode city and its urban agglomeration** — The built-up area expanded from 23.5 km² (2013) to 27.75 km² (2018), a 5.48% increase, with a predicted 39.61% further expansion by 2023. The municipal corporation boundary expanded from 8.35 km² to 109.52 km² to absorb surrounding towns. Textile and industrial corridors drove this.

2. **Perundurai industrial corridor** — The SIPCOT industrial complex at Perundurai (one of the 10 taluks) has attracted manufacturing and logistics investment, generating significant new illumination.

3. **The western corridor (Erode–Coimbatore axis)** — Sudalayandi et al. (2021) found that the "western corridor" of Tamil Nadu showed more urban growth in VIIRS nighttime lights than other parts of the state. Erode district sits squarely on this corridor.

4. **Gobichettipalayam and Bhavani taluks** — Secondary urban centres with growing commercial activity.

---

## Citable sources you can check

| # | Citation | What it provides | Link |
|---|----------|-----------------|------|
| 1 | Sudalayandi, R. S., Srinivasan, E., & Kasaragod, G. R. (2021). "Urban growth analysis of Tamil Nadu state, India using VIIRS DNB night data during 2012 and 2016." *Remote Sensing Applications: Society and Environment*, 23, 100559. | District-level and corridor-level classification of Tamil Nadu using VIIRS; western corridor (including Erode) identified as highest-growth region. | https://doi.org/10.1016/j.rsase.2021.100559 |
| 2 | Springer (2025). "Spatiotemporal Assessment of Urban Growth Dynamics Using Open-Source Remote Sensing Datasets: A Case Study of Tamil Nadu State." *Journal of the Indian Society of Remote Sensing*. | Uses VIIRS NTL composites (2015–2023) for Tamil Nadu cities; provides comparative NTL intensity figures. | https://link.springer.com/article/10.1007/s12524-025-02420-8 |
| 3 | Devendran, A. A. & Gnanappazham, L. (2020). "Prediction of urban sprawl using geospatial dataset — A case study for Erode urban area for smart city development." *AIP Conference Proceedings*, 2271, 030012. | Built-up area expansion in Erode city (2008–2018) with future projections. | https://doi.org/10.1063/5.0011019 |
| 4 | Kongu Nadu Region preprint (2025). "Urban Development in the Western Part of Tamil Nadu (Kongu Nadu Region), India: A Temporal Study Using Land Use Land Cover Change Detection Analysis." | LULC change across the 10-district Kongu Nadu region including Erode. | https://doi.org/10.21203/rs.3.rs-6314124/v1 |
| 5 | **SHRUG v2.1** — Development Data Lab. VIIRS Annual Nighttime Lights (sub-district level, 2012–2021). | Downloadable sub-district panel data — you can filter for Erode's taluks and compare 2015 vs 2021 yourself. | https://www.devdatalab.org/shrug (file: `viirs_annual_pc11subdist.dta`) |
| 6 | **India District Nightlights VIIRS** (open-source pipeline, 2012–2024). | District-level annual radiance stats (mean, sum, etc.) for all 641 districts including Erode. | https://github.com/yashveeeeeeer/india-district-nightlights-viirs |
| 7 | **India Built & Lit** — XKDR Forum. District panel of building volume + VIIRS NTL. | Monthly cleaned NTL per district using NighttimeLights.jl. | https://xkdr.github.io/India-Built-and-Lit/ |

---

## How to verify at sub-district level

For taluk-by-taluk comparison within Erode, your best bet is:

- Download the **SHRUG** sub-district VIIRS file (`viirs_annual_pc11subdist.dta`) and filter by `pc11_state_id = 33` (Tamil Nadu) and `pc11_district_id = 10` (Erode per Census 2011). Compare `viirs_annual_mean` or `viirs_annual_sum` for 2015 vs. 2021.
- Alternatively, use the open-source pipeline at GitHub (source #6 above) with Google Earth Engine to compute zonal stats for Erode's taluk boundaries through 2023.

The Erode city core + Perundurai industrial zone will almost certainly show the steepest rise in radiance.
