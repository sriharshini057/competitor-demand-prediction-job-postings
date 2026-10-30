# Official Dataset Validation & Specification Report: Microsoft (Strict Entity)

**Project**: Competitor Demand Prediction Using Job Postings  
**Official Single Target Subject**: **Microsoft** (`company_name == "Microsoft"`)  
**Specification Date**: October 3, 2026  
**Status**: Target dataset definition locked and documented.

---

## 1. Executive Summary & Locked Boundaries

1. **Single Target Company**: **Microsoft** is the **sole target company** for this project.
2. **Strict Entity Filtering**: Only records where `company_name == "Microsoft"` are included.
3. **Excluded Entities**:
   - Subsidiary corporate entities (e.g., `Microsoft Corporation`, `Microsoft Deutschland GmbH`, `Microsoft Operations Pte Ltd`, `Microsoft India`, `Microsoft Research Lab`, `Microsoft Corp.`) are explicitly excluded.
   - External recruitment agencies, staffing partners, and consulting firms (e.g., ShortHills Tech, Add Value, Cognizant, Octaware) are excluded.
4. **Official Project Dataset Size**: Exactly **498 job postings**.
5. **Primary Raw Source**: `data/raw/data_jobs.csv` (preserved in its original, unmodified state).
6. **Secondary Dataset**: EMSCAD (`data/raw/fake_job_postings.csv`) is preserved solely for NLP methodology and text-parsing benchmarking, introducing no additional target companies.

---

## 2. Statistical Profile of the 498-Posting Microsoft Dataset

### A. Temporal Continuity (Full Year 2023)
* **Date Range**: `2023-01-02 11:30:26` to `2023-12-31 13:32:24`
* **Weekly Coverage**: **52 out of 52 weeks** active (Mean: 9.58 postings/week; Median: 9.0; Range: 1 to 23).
* **Monthly Distribution**:
  * 2023-01: 71 postings
  * 2023-02: 37 postings
  * 2023-03: 24 postings
  * 2023-04: 10 postings *(Annual trough)*
  * 2023-05: 18 postings
  * 2023-06: 30 postings
  * 2023-07: 45 postings
  * 2023-08: 38 postings
  * 2023-09: 42 postings
  * 2023-10: 49 postings
  * 2023-11: 62 postings
  * 2023-12: 72 postings *(Annual peak)*

### B. Standardized Role Families (`job_title_short`)
1. **Software Engineer**: 173 (34.7%)
2. **Data Scientist**: 135 (27.1%)
3. **Senior Data Scientist**: 57 (11.4%)
4. **Data Engineer**: 44 (8.8%)
5. **Senior Data Engineer**: 34 (6.8%)
6. **Cloud Engineer**: 15 (3.0%)
7. **Business Analyst**: 13 (2.6%)
8. **Data Analyst**: 12 (2.4%)
9. **Machine Learning Engineer**: 10 (2.0%)
10. **Senior Data Analyst**: 5 (1.0%)

### C. Top Technical Skills
* **Coverage**: 393 of 498 postings (78.9%) have explicit skill tags.
* **Top 10 Technologies**:
  1. Azure: 241 postings (48.4%)
  2. Python: 175 postings (35.1%)
  3. SQL: 147 postings (29.5%)
  4. C#: 141 postings (28.3%)
  5. Java: 104 postings (20.9%)
  6. Spark: 101 postings (20.3%)
  7. C++: 77 postings (15.5%)
  8. Hadoop: 61 postings (12.2%)
  9. Windows: 58 postings (11.6%)
  10. Power BI: 57 postings (11.4%)

### D. Geographic Footprint
* **Remote Ratio**: 90.6% On-site/Hybrid (451), 9.4% Fully Remote (47).
* **Top Countries**: India (115), United States (60), China (46), Ireland (32), Costa Rica (31).
* **Top Hubs**: Hyderabad (56), Anywhere/Remote (47), Dublin (30), San José (26), Bengaluru (23), Suzhou (17), Herzliya (16), Redmond (13), Noida (13).

### E. Data Integrity
* **Exact Duplicate Rows**: 0 (0.00%)
* **Subset Duplicates `(title, location, date)`**: 0 (0.00%)
* **Missing Dates / Titles / Locations**: 0 (0.00%)

---

## 3. Project Alignment & Feasibility

The 498-posting Microsoft dataset fulfills all analytical prerequisites for the upcoming project stages:
* **Hiring Trend Analysis (Stage 6)**: Supported by 52 continuous weekly timestamps and seasonal variation.
* **Demand Forecasting (Stage 8)**: Supported by lag-feature construction across 52 sequential weeks.
* **Skill Demand Modeling (Stages 4 & 5)**: Supported by dense Microsoft tech stack signals.
* **NLP & Text Methodology**: Supported by EMSCAD as a secondary text parsing benchmark.
