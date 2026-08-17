# R4 rep1 x gpt-5.4-medium
Q: Garbage complaints in Bellandur ward, Bengaluru: from 2019 to 2022 did they go up or come down? Citations.
elapsed:80s

---

They **came down** in the comparable `2019-2022` ward-level complaints log I found.

Using OpenCity’s **“I Change My City Complaints Log - 2019 - 2022”** dataset, and counting Bellandur as the ward name used there (`Bellanduru`) with complaint category `Garbage and Unsanitary Practices`, the counts are:

- **2019:** 26
- **2020:** 13
- **2021:** 3
- **2022:** 3

So from **2019 to 2022**, garbage complaints in Bellandur **fell from 26 to 3**, a drop of about **88%**. Source dataset: [CKAN page](https://data.opencity.in/dataset/i-change-my-city-data/resource/a60abf5c-3a15-4967-af32-c3074248580f), [direct CSV](https://newdata.opencity.in/dataset/9183b0b2-b49a-40a9-b36d-275e1eaedb3f/resource/a60abf5c-3a15-4967-af32-c3074248580f/download/5f99b09a-64b5-45f0-ab18-4cf0a0cabf6d.csv).

One caveat: the more official-looking OpenCity **BBMP Grievances Data** series starts only in **2020**, not 2019, so it does **not** support a like-for-like official `2019 vs 2022` comparison on that portal. OpenCity’s BBMP dataset page explicitly lists years from **2020 onward**: [dataset page](https://data.opencity.in/dataset/bbmp-grievances-data). If you want, I can also give you the exact filter logic so you can reproduce the count yourself.
