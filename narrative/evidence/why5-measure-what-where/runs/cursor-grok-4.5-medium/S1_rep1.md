# S1 rep1 x cursor-grok-4.5-medium
Q: Which parts of Erode district saw the most growth in night-time lights between 2015 and 2023? Give citations I can check.
elapsed:442s

---

**Perundurai taluk** (especially around SIPCOT) saw the strongest night-light growth in Erode district between 2015 and 2023; **Erode taluk** (the city and its fringe) was second.

### What the data show

Using annual VIIRS VNL radiance (Zenodo COGs derived from EOG Annual VNL V2) clipped to GADM taluks for Erode:

| Taluk | Mean radiance 2015 → 2023 | Change |
|---|---|---|
| **Perundurai** | 1.25 → 2.37 | **+1.12 (+90%)** |
| Erode | 1.64 → 2.34 | +0.70 (+43%) |
| Gobichettipalayam | 0.86 → 1.29 | +0.43 (+50%) |
| Bhavani | 0.40 → 0.65 | +0.25 (+62%) |
| Sathyamangalam | 0.18 → 0.32 | +0.14 (+82%) |

- **Perundurai** also leads on total light (sum), lit-area expansion, and share of the brightest growth pixels.
- The strongest pixel-level jumps cluster near **SIPCOT Perundurai** (~11.23–11.25°N, 77.54–77.56°E), matching the industrial estate location.
- **Erode city** stayed brightest overall; a secondary hotspot is on the city’s southeastern fringe (~11.28°N, 77.77°E).
- District-wide mean radiance rose from **0.82 → 1.26 (+54%)** in an independent India district VIIRS panel.

GADM uses the older five-taluk map (before later splits such as Anthiyur/Modakurichi), so “Perundurai” and “Erode” here are those broader units.

### Citations you can check

1. **Source radiance rasters (2015 & 2023):** Zenodo record [17294744](https://zenodo.org/records/17294744) — annual VIIRS VNL averages (from Elvidge et al. Annual VNL V2).
2. **Method paper for Annual VNL V2:** Elvidge et al. (2021), *Remote Sensing* — [doi:10.3390/rs13050922](https://doi.org/10.3390/rs13050922); product page: [eogdata.mines.edu/products/vnl/](https://eogdata.mines.edu/products/vnl/).
3. **District-level confirmation (Erode 2015–2023):** [india-district-nightlights-viirs panel CSV](https://raw.githubusercontent.com/yashveeeeeeer/india-district-nightlights-viirs/main/output/csv/nightlights_district_panel.csv) (Erode, Tamil Nadu: mean 0.818 → 1.255).
4. **Why Perundurai is the expected industrial growth node:** [Erode City Mobility Plan](https://www.tnurbantree.tn.gov.in/erode/wp-content/uploads/sites/143/2019/12/Erode-City-Mobility-Plan-Final1.pdf) (Perundurai SIPCOT / satellite-town growth corridor).
5. **SIPCOT location (matches the hotspots):** ~11.24°N, 77.54°E — e.g. [DigiPin listing](https://digipin.net.in/pa/search-by-map?lat=11.241117&long=77.540991) and [Wikimapia Perundurai SIPCOT](http://wikimapia.org/13017866/Perundurai-SIPCOT).
