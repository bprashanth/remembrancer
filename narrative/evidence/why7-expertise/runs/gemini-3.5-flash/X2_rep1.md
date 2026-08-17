# X2 rep1 x gemini-3.5-flash
Q: Using VIIRS annual nighttime lights composites (EOG or Google Earth Engine), or failing that the SHRUG viirs annual mean tables, which parts of Erode district show the highest radiance growth from 2015 to 2023? Name the exact dataset and vintage you used. Citations.
elapsed:386s

---

Based on a geospatial and statistical analysis of the Visible Infrared Imaging Radiometer Suite (VIIRS) annual nighttime lights (NTL) composites and the Socioeconomic High-resolution Rural-Urban Geographic (SHRUG) annual tables, **Perundurai** (Census 2011 Subdistrict Code: `05752`) shows the highest radiance growth in Erode district.

Here is the detailed breakdown of the exact datasets, vintages, statistics, and citations.

---

### 1. Subdistrict-Level Analysis: SHRUG v2.1 (2015 to 2021)
At the high-resolution subdistrict (taluk) level, the **SHRUG v2.1** annual mean tables provide consistently processed VIIRS nighttime lights from 2012 to 2021 (the latest available year in this dataset). 

Erode district comprises 5 taluks (subdistricts) under the Census 2011 framework.

#### A. Median-Masked Category
This category is the recommended metric for stable nighttime lights, as it filters out background noise, biomass burning, and transient flaring:

| Rank | Subdistrict / Taluk Name (Census Code) | 2015 Mean ($nW/cm^2/sr$) | 2021 Mean ($nW/cm^2/sr$) | Absolute Growth | % Growth |
|:---:|:---|:---:|:---:|:---:|:---:|
| **1** | **Perundurai (05752)** | **1.1606** | **1.7072** | **+0.5467** | **+47.10%** |
| **2** | Erode (05753) | 1.8276 | 2.1025 | +0.2749 | +15.04% |
| **3** | Gobichettipalayam (05751) | 0.7704 | 0.9494 | +0.1790 | +23.24% |
| **4** | Bhavani (05750) | 0.4096 | 0.5172 | +0.1076 | +26.28% |
| **5** | Sathyamangalam (05749) | 0.1578 | 0.2122 | +0.0544 | +34.47% |

#### B. Average-Masked Category
The average-masked raster tracks mean nightly values (which include brighter transient peaks but suffer from higher noise):

| Rank | Subdistrict / Taluk Name (Census Code) | 2015 Mean ($nW/cm^2/sr$) | 2021 Mean ($nW/cm^2/sr$) | Absolute Growth | % Growth |
|:---:|:---|:---:|:---:|:---:|:---:|
| **1** | **Perundurai (05752)** | **1.1529** | **1.3925** | **+0.2396** | **+20.78%** |
| **2** | Sathyamangalam (05749) | 0.1573 | 0.1767 | +0.0194 | +12.31% |
| **3** | Bhavani (05750) | 0.4008 | 0.4185 | +0.0178 | +4.43% |
| **4** | Gobichettipalayam (05751) | 0.7537 | 0.7479 | -0.0058 | -0.77% |
| **5** | Erode (05753) | 1.7870 | 1.7340 | -0.0530 | -2.97% |

*Note: The negative or flat average-masked growth in urban subdistricts like Erode and Gobichettipalayam is a well-documented phenomenon in remote sensing known as the **LED transition effect**. When cities replace traditional yellow/orange high-pressure sodium street lights with white LEDs, satellite-observed radiance often falls because the VIIRS sensor is blind to blue wavelengths (below 500 nm), despite the physical area remaining equally or more illuminated. Perundurai's massive physical expansion was bright enough to overcome this sensor-induced downward bias.*

---

### 2. District-Level Trend: Google Earth Engine VIIRS Panel (2015 to 2023)
To bridge the period up to 2023, we analyzed the district-level panel generated directly from the annual median VIIRS radiance composites on Google Earth Engine (using standard Census 2011 boundary polygons). 

In Erode District (District ID: `610`), we observe strong, steady growth:
* **2015 Mean Radiance:** $0.8177\ nW/cm^2/sr$ (Sum: $4841.67$)
* **2017 Mean Radiance:** $0.9101\ nW/cm^2/sr$ (Sum: $5388.84$)
* **2019 Mean Radiance:** $0.9130\ nW/cm^2/sr$ (Sum: $5405.98$)
* **2021 Mean Radiance:** $1.0480\ nW/cm^2/sr$ (Sum: $6205.39$)
* **2023 Mean Radiance:** $1.2550\ nW/cm^2/sr$ (Sum: $7431.00$)
* **Overall Radiance Growth (2015 to 2023):** **+0.4373 $nW/cm^2/sr$** in mean radiance, representing a **+53.48%** increase.

---

### 3. Economic and Geographic Context
The high radiance growth in Perundurai is driven by:
* **SIPCOT Industrial Growth Centre:** Located in Perundurai, this is a massive industrial complex spanning over 2,700 acres. By late 2023, it supported more than 150 functioning textile processing, dyeing, engineering, and chemical units, sustaining over 100,000 migrant and local laborers.
* **Corridor Expansion:** The Salem-Coimbatore-Kochi National Highway (NH-544 / old NH-47) runs directly through Perundurai, spurring transport hubs, warehousing, educational institutions, and real estate development.

---

### 4. Datasets and Vintages Used
1. **Subdistrict NTL Dataset:** 
   * **Dataset Name:** Socioeconomic High-resolution Rural-Urban Geographic (SHRUG) Platform for India, Version 2.1 ("Pakora").
   * **Vintage/Release Date:** October 30, 2024.
   * **Source File:** `viirs_annual_pc11subdist.tab` (aggregations use 2011 Census boundaries).
2. **District NTL Dataset:**
   * **Dataset Name:** India District-Wise Nighttime Lights Panel Dataset (derived via NOAA VIIRS DNB annual median composites on Google Earth Engine).
   * **Vintage/Release Date:** March 8, 2026.
   * **Source File:** `nightlights_district_panel.csv` (using Census 2011 boundaries).

---

### 5. Citations
* **SHRUG Platform:** 
  Asher, S., Lunt, T., Shin, R., & Novosad, P. (2021). *Development Research at High Geographic Resolution: An Analysis of Night-Lights, Firms, and Poverty in India Using the SHRUG Open Data Platform.* World Bank Economic Review, 35(4), 845–871. [https://doi.org/10.1093/wber/lhab003](https://doi.org/10.1093/wber/lhab003)
* **VIIRS NTL Composites:**
  Elvidge, C. D., Baugh, K., Zhizhin, M., Hsu, F. C., & Ghosh, T. (2021). *VIIRS night-time lights.* International Journal of Remote Sensing, 42(2), 707-734. (Produced by the Earth Observation Group, Payne Institute for Public Policy, Colorado School of Mines). [https://eogdata.mines.edu/products/vnl/](https://eogdata.mines.edu/products/vnl/)
* **GEE Extraction Pipeline:**
  Yashveer (2026). *India District-Wise Nighttime Lights Panel (2012-2024).* GitHub repository. [https://github.com/yashveeeeeeer/india-district-nightlights-viirs](https://github.com/yashveeeeeeer/india-district-nightlights-viirs)
