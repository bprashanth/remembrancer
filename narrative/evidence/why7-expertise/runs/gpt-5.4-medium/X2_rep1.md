# X2 rep1 x gpt-5.4-medium
Q: Using VIIRS annual nighttime lights composites (EOG or Google Earth Engine), or failing that the SHRUG viirs annual mean tables, which parts of Erode district show the highest radiance growth from 2015 to 2023? Name the exact dataset and vintage you used. Citations.
elapsed:643s

---

I treated “parts of Erode district” as its taluks/subdistricts, using the LGD-based `LGD_Subdistricts.parquet` boundary release from India Geodata (`admin/subdistricts`, published 2026-03-08). For lights, I did **not** use SHRUG; I used the public Figshare mirror of the **EOG annual VIIRS `average_masked` composites**, specifically `SRUNet_NPP_VIIRS_V2_Like_2015.tif` and `SRUNet_NPP_VIIRS_V2_Like_2023.tif` from Figshare DOI `10.6084/m9.figshare.22262545.v9`. That mirror explicitly states its 2012-2021 layers are EOG Annual NPP-VIIRS NTL Version 2.0 and its 2022-2024 layers are EOG Version 2.2 `average_masked`, originally obtained from EOG; EOG documents these annual products as 15-arc-second global GeoTIFFs in WGS84 with radiance in nW/cm²/sr. [Figshare v9](https://doi.org/10.6084/m9.figshare.22262545.v9) [Figshare API metadata](https://api.figshare.com/v2/articles/22262545) [EOG product page](https://eogdata.mines.edu/products/vnl/) [India Geodata subdistrict release](https://github.com/yashveeeeeeer/india-geodata/releases/tag/admin/subdistricts)

By **increase in mean annual radiance** from 2015 to 2023, the strongest-growing parts of Erode district were:

| Part of Erode district | 2015 mean | 2023 mean | Growth |
| --- | ---: | ---: | ---: |
| `Erode` | 4.769 | 6.368 | **+1.599** |
| `Perundurai` | 0.930 | 2.350 | **+1.420** |
| `Modakkurichi` | 0.606 | 1.660 | **+1.054** |
| `Bhavani` | 0.780 | 1.695 | **+0.915** |
| `Kodumudi` | 0.477 | 1.361 | **+0.885** |
| `Gobichettipalayam` | 0.640 | 1.444 | **+0.803** |
| `Nambiyur` | 0.166 | 0.905 | **+0.739** |
| `Anthiyur` | 0.316 | 1.009 | **+0.693** |
| `Sathyamangalam` | 0.166 | 0.404 | **+0.238** |
| `Thalavadi` | 0.003 | 0.038 | **+0.035** |

So the clearest answer is: **the biggest broad-based radiance growth was in `Erode` taluk, followed closely by `Perundurai`, then `Modakkurichi`**.

At the pixel-hotspot level, growth was even more concentrated than the taluk means suggest. The **single strongest jump pixels** were in `Modakkurichi` (around `11.2875 N, 77.7625 E`), but the **densest hotspot cluster** was in `Perundurai` around `11.23 N, 77.54-77.57 E`. In fact, among pixels in the **top 0.5% of district-wide growth**, `Perundurai` contained **78 of 122** hotspot pixels, versus `Erode` 30, `Nambiyur` 7, and `Modakkurichi` 4. That means the district’s most intense new cluster is in the **Perundurai industrial belt**, while `Erode` shows the strongest overall taluk-wide brightening and `Modakkurichi` contains the sharpest individual pixel spikes. [MapIt point-to-boundary service](https://global.mapit.mysociety.org/) [Perundurai Growth Centre location](https://web.archive.org/web/20100212225135/www.sipcot.com/Industrial_complex_Perundurai.htm)

If you want, I can turn this into a small map of Erode district with the taluk ranking and hotspot coordinates labeled.
