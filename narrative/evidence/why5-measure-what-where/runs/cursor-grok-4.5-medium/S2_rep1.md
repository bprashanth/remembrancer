# S2 rep1 x cursor-grok-4.5-medium
Q: Has the built-up area around the Perundurai SIPCOT industrial estate expanded since 2015? How would you check? Citations please.
elapsed:236s

---

**Yes — built-up surface around Perundurai SIPCOT has expanded since 2015**, even though the estate’s cadastral footprint has stayed about the same size since the 1990s acquisition.

### What the evidence shows

**1. Open built-up data (2015 → 2020)**  
Using JRC **GHSL GHS-BUILT-S R2023A** (~90 m / 3″), built-up surface (m² of building footprint per cell) around ~11.22°N, 77.55°E rose:

| Buffer | 2015 | 2020 | Change |
|--------|------|------|--------|
| 2 km | ~147 ha | ~163 ha | **+11%** |
| 5 km | ~507 ha | ~567 ha | **+12%** |
| 10 km | ~1,667 ha | ~1,906 ha | **+14%** |

Growth is both inside the core and in the surrounding ring (2–10 km), so this is not only infill on already industrial plots. Dataset: [GHS-BUILT-S R2023A](https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S); method: Pesaresi et al., *International Journal of Digital Earth* (2024), [doi:10.1080/17538947.2024.2390454](https://doi.org/10.1080/17538947.2024.2390454).

**2. Estate size vs. occupation**  
The park is still ~**2,709 acres** ([The Hindu, Dec 2023](https://www.thehindu.com/news/cities/Coimbatore/work-to-establish-a-common-effluent-treatment-plant-begins-at-perundurai-sipcot/article67689780.ece)) — land taken mainly in **1991**, not a post-2015 boundary expansion ([The Hindu on compensation](https://www.thehindu.com/news/cities/Coimbatore/perundurai-sipcot-landowners-seek-compensation-as-per-high-court-order/article69686138.ece)). Vacant allottable land has shrunk sharply (hundreds of acres available in older SIPCOT listings vs ~**81 acres** recently on the [SIPCOT land portal](https://sipcot.tn.gov.in/portal/reports/landdetails)), and unit counts moved toward ~**150–157** industries by the late 2010s/2023 ([Erode CMP](https://www.tnurbantree.tn.gov.in/erode/wp-content/uploads/sites/143/2019/12/Erode-City-Mobility-Plan-Final1.pdf); [The Hindu](https://www.thehindu.com/news/cities/Coimbatore/work-to-establish-a-common-effluent-treatment-plant-begins-at-perundurai-sipcot/article67689780.ece)).

**3. Planning context**  
Erode’s mobility/planning work treats Perundurai SIPCOT as a **growth corridor** for future urbanization along the Coimbatore–Salem axis ([Erode City Mobility Plan](https://www.tnurbantree.tn.gov.in/erode/wp-content/uploads/sites/143/2019/12/Erode-City-Mobility-Plan-Final1.pdf)). That supports surrounding built-up growth even without a new estate boundary.

There is **no published, peer-reviewed LULC change paper focused only on Perundurai SIPCOT for 2015–present**; local remote-sensing work is mostly groundwater/LULC snapshot (e.g. Landsat 8 map for 2019 in [Research Square preprint rs-1000678](https://doi.org/10.21203/rs.3.rs-1000678/v1)).

---

### How you would check (recommended)

1. **Define AOI** — estate polygon (SIPCOT GIS / cadastral) plus buffers (e.g. 2 / 5 / 10 km).  
2. **Compare epochs** — Landsat 8 (2015+) and Sentinel-2 (2016+); classify built vs non-built (SVM/RF) or use ready products: **GHSL**, **World Settlement Footprint**, **ESA WorldCover**, **ISRO Bhuvan LULC 50K** ([NRSC LULC](https://www.nrsc.gov.in/nrscnew/Apps_LULC.php)).  
3. **Change detection** — post-classification differencing; report ha and %; separate **inside estate** (densification) vs **outside** (sprawl).  
4. **Validate** — Google Earth historical imagery; SIPCOT allotment/vacancy tables; Census / town-panchayat growth.  
5. **Caveats** — GHSL epochs are modeled/interpolated; industrial yards can be undercounted as “built”; cloud/season and bare soil vs roof confusion on optical data.

**Bottom line:** Since 2015 the **official estate acreage has not materially expanded**, but **built-up area in and around it has** — on the order of **~10–15% (2015–2020)** in GHSL within a few kilometres of the site.The GHSL tile download finished successfully. Comparing the 2015 and 2020 layers around Perundurai SIPCOT showed clear built-up growth: roughly **+11% within 2 km**, **+12% within 5 km**, and **+14% within 10 km**.
