# X4 rep1 x cursor-grok-4.5-medium
Q: For India's 2021 unemployment rate, give me all three: the ILO modelled estimate (World Bank SL.UEM.TOTL.ZS), the PLFS usual status and current weekly status figures, and the CMIE estimate. Label each with its methodology and say which one a district NGO report should use. Citations.
elapsed:95s

---

India’s 2021 unemployment figures differ sharply by source because the methods are not the same.

### 1. ILO modelled estimate (World Bank `SL.UEM.TOTL.ZS`)
**6.38%** (calendar year 2021)

**Methodology:** Harmonized ILO modelled estimate of unemployed as a share of the labour force (age 15+), built from national surveys plus statistical models/imputations for cross-country comparability. Not a raw national survey release.

**Source:** World Bank WDI API / ILOEST (`SL.UEM.TOTL.ZS`), value for IND 2021 = 6.38; metadata: [World Bank glossary](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SL.UEM.TOTL.ZS).

---

### 2. PLFS (MoSPI/NSO) — survey year July 2020–June 2021
| Measure | Rate | Methodology |
|---|---|---|
| **Usual status (ps+ss)** | **4.2%** | Activity status over the **past 365 days** (principal + subsidiary). Captures more chronic/structural unemployment. |
| **Current weekly status (CWS)** | **7.5%** | Status over the **past 7 days**. Closer to the international “last week” concept; picks up shorter-term joblessness. |

**Methodology:** Official nationally representative household labour-force survey. Person is unemployed if without work but seeking/available for work over the relevant reference period.

**Sources:** PLFS Annual Report 2020–21 (MoSPI/NSO); coverage in [Indian Express](https://indianexpress.com/article/explained/fall-in-unemployment-rate-in-2020-21-labour-survey-what-it-means-7971285/) and [Financial Express](https://www.financialexpress.com/policy/economy-labour-survey-reveals-sharp-drop-in-jobless-rate-in-2020-21-2560662/).

---

### 3. CMIE Consumer Pyramids estimate
**~7.8%** (average of monthly rates for calendar 2021)

Monthly path included spikes such as **11.8% in May 2021** (second COVID wave) and **7.9% in December 2021**.

**Methodology:** Private panel household survey (Consumer Pyramids Household Survey). Unemployment = share of the labour force that is not employed and is actively looking for work; published as monthly / 30-day moving averages, not an official MoSPI series.

**Sources:** CMIE Unemployment in India series / Mahesh Vyas updates (e.g. Dec 2021 at 7.9%); calendar-year average ~7.8% reported in secondary summaries such as [NewsClick](https://www.newsclick.in/Jobless-Numbers-Are-Touching-5-Crore) (simple mean of published monthly rates ≈ 7.8%).

---

### Which one a district NGO report should use
**Use PLFS** — specifically **usual status (4.2%)** as the headline annual figure for program/context writing, and cite **CWS (7.5%)** if you need a short-term or internationally comparable reading.

Reasons: it is India’s **official** labour-force series; methodology is transparent and accepted by government and most funders; state-level PLFS tables exist for local benchmarking. ILO modelled estimates are for **global comparison**, not district program design. CMIE is useful for **timely monthly tracking**, but it is private and not the standard citation for formal NGO/government reporting.
