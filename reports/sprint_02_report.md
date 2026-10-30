# CadetX Sprint 2 Deliverable Report: Data Cleaning, Imputation & Date Normalization

**Project**: Competitor Demand Prediction Using Job Postings  
**Target Subject**: Microsoft (`company_name == "Microsoft"`)  
**Sprint**: Sprint 2 (Stage 2: Tabular Data Cleaning and Temporal Preprocessing)  
**Date**: October 27, 2026  
**Status**: COMPLETE — Ready for Review and Submission  

---

## 1. Executive Summary & Objective

Sprint 2 transitions the ingested, filtered Microsoft job postings slice (`data/processed/microsoft_jobs.csv`, 498 records) into a fully cleaned, structurally enriched, and normalized tabular dataset (`data/processed/microsoft_jobs_cleaned.csv`).
The primary objectives of Sprint 2:
1. **Handle Missing Values**: Systematically impute missing values across categorical variables and flag sparse fields without data loss.
2. **Date Normalization & Temporal Decomposition**: Parse ISO timestamps and engineer calendar features (`posted_year`, `posted_month`, `posted_week`, `posted_day`, `posted_dayofweek`, `posted_quarter`, `posted_year_week`) required for downstream time-series demand modeling.
3. **Salary Standardization**: Unify annual and hourly compensation reporting into an annualized metric (`salary_annual_standardized`) based on the standard 2,080 annual working hours benchmark.
4. **Structured Skill Parsing**: Transform raw serialized string representations of lists and category dictionaries into native Python collections, accompanied by frequency counts and availability indicators.
5. **Location Normalization**: Extract standardized city names, resolve remote work postings, and correct character encoding artifacts in location strings.
6. **Deduplication & Schema Validation**: Assert record uniqueness, schema integrity, zero null primary keys, and strict company identity.

---

## 2. Input and Output File Specifications

| Attribute | Input File | Output File |
| :--- | :--- | :--- |
| **Path** | `data/processed/microsoft_jobs.csv` | `data/processed/microsoft_jobs_cleaned.csv` |
| **Origin** | Sprint 1 Ingestion (`src/collection/collector.py`) | Sprint 2 Cleaning (`src/preprocessing/cleaner.py`) |
| **Record Count** | 498 | 498 |
| **Total Columns** | 17 | 32 (15 newly engineered features) |
| **File Size** | 138.38 KB (135.14 KB uncompressed) | 226.09 KB |
| **Git Status** | Ignored by Git (`.gitignore`: `data/processed/*`) | Ignored by Git (`.gitignore`: `data/processed/*`) |
| **Target Filter** | `company_name == 'Microsoft'` | `company_name == 'Microsoft'` (100% verified) |

---

## 3. Methodology & Transformation Pipeline

### 3.1 Company Name Standardization
- Canonicalized all `company_name` records by stripping whitespace and enforcing title-casing (`"Microsoft"`).
- Target company validation confirmed 498 of 498 records (100.0%) strictly match `"Microsoft"`.

### 3.2 Date Normalization & Temporal Feature Generation
The raw timestamp column `job_posted_date` was converted to `datetime64[ns]`. All 498 records were parsed with zero conversion errors.

Eight temporal attributes were derived for time-series forecasting:
- `posted_date`: ISO date string (`YYYY-MM-DD`)
- `posted_year`: Integer year (`2023` for all 498 records)
- `posted_month`: Integer month (`1` to `12`)
- `posted_week`: ISO calendar week (`1` to `52`, covering all 52 weeks of 2023)
- `posted_day`: Day of month (`1` to `31`)
- `posted_dayofweek`: Integer day of week (`0` = Monday to `6` = Sunday)
- `posted_quarter`: Integer financial quarter (`1` to `4`)
- `posted_year_week`: Standard formatted string identifier (`YYYY-Www`)

### 3.3 Salary Standardization
- In the raw dataset, only 15 postings include compensation data:
  - 13 postings specify `salary_year_avg`.
  - 2 postings specify `salary_hour_avg` ($65.00/hr and $24.00/hr).
- Implemented `standardize_salaries()`:
  - For hourly postings, calculated annualized compensation: $\text{Hourly Rate} \times 2,080 \text{ hours}$.
    - $65.00/hr $\rightarrow$ $135,200.00/yr.
    - $24.00/hr $\rightarrow$ $49,920.00/yr.
  - Yearly salaries were preserved directly.
  - Added boolean indicator `has_salary_data` (15 `True`, 483 `False`).
- Summary statistics for the 15 standardized salaries:
  - Minimum: $49,920.00
  - 25th Percentile: $91,800.00
  - Median (50th): $150,000.00
  - Mean: $136,269.33
  - 75th Percentile: $170,250.00
  - Maximum: $217,500.00

### 3.4 Skill Field Parsing
- The raw columns `job_skills` and `job_type_skills` contain serialized Python syntax strings (e.g. `"['c#', 'azure', 'windows']"`).
- Implemented `parse_skills_columns()` utilizing safe parsing (`ast.literal_eval`):
  - `job_skills_parsed`: Native Python `list[str]` of lowercase skill tags. Missing values default to empty list `[]`.
  - `job_type_skills_parsed`: Native Python `dict[str, list[str]]` mapping skill domains (e.g. `cloud`, `programming`, `os`) to lists. Missing values default to `{}`.
  - `job_skills_count`: Exact integer skill count per posting (Mean: 4.27, Median: 3.0, Max: 24).
  - `has_skills_specified`: Boolean indicator confirming explicit skill tags are present (393 postings = 78.9% coverage).

### 3.5 Location Cleaning
- Cleaned location strings and parsed primary city hub via `clean_locations()`:
  - Remote postings (`"Anywhere"`) mapped to `"Remote/Anywhere"` (47 postings).
  - Resolved character encoding artifacts from raw dump (`"San Jos\ufffd Province"` normalized to canonical `"San José"`).
  - Top municipal hubs identified:
    1. Hyderabad, India (56 postings)
    2. Remote / Anywhere (47 postings)
    3. Dublin, Ireland (30 postings)
    4. San José, Costa Rica (26 postings)
    5. Bengaluru, India (23 postings)
- Standardized country strings (`job_country`) across 498 records.

### 3.6 Missing Categorical Value Imputation
- `job_schedule_type`: 2 missing records imputed to `"Unspecified"`.
- `salary_rate`: 483 missing records imputed to `"Unspecified"`.
- Boolean fields (`job_work_from_home`, `job_no_degree_mention`, `job_health_insurance`): verified and filled with `False` if null.

### 3.7 Deduplication & Integrity
- Evaluated duplicates across compound identifier `['job_title', 'job_location', 'job_posted_date', 'company_name']`.
- Exactly 0 duplicate postings detected; all 498 records represent distinct posting instances.

---

## 4. Validation Results & Sanity Checks

| Check | Requirement | Result | Status |
| :--- | :--- | :--- | :--- |
| **Output File Presence** | File exists at `data/processed/microsoft_jobs_cleaned.csv` | File generated (226.09 KB) | **PASS** |
| **Record Count** | Exactly 498 records | 498 records | **PASS** |
| **Target Company Uniformity** | 100% `company_name == 'Microsoft'` | 498 / 498 (100.0%) | **PASS** |
| **Title Completeness** | 0 null `job_title` or `job_title_short` | 0 nulls | **PASS** |
| **Date Completeness** | 0 null `job_posted_date` | 0 nulls | **PASS** |
| **Temporal Span** | 52 consecutive ISO weeks in 2023 | 52 distinct weeks (2023-01-02 to 2023-12-31) | **PASS** |
| **Standardized Salary Field** | `salary_annual_standardized` populated where salary exists | 15 populated, 483 NaN; `has_salary_data` matches | **PASS** |
| **Skills Coverage** | Explicit skill tags parsed | 393 postings (78.9%), 105 default to `[]` | **PASS** |
| **Raw Data Integrity** | Raw data files unmodified and ignored by Git | Unchanged (231,152,089 bytes & 50,061,601 bytes); ignored | **PASS** |

---

## 5. Tests Actually Executed

Automated unit tests were executed using `pytest 9.1.1` on Python 3.13.5 (Windows):

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.7.0
rootdir: Competitor Demand Prediction Using Job Postings
collected 13 items

tests/test_cleaner.py::test_standardize_company_name PASSED              [  7%]
tests/test_cleaner.py::test_normalize_dates PASSED                       [ 15%]
tests/test_cleaner.py::test_standardize_salaries PASSED                  [ 23%]
tests/test_cleaner.py::test_parse_skills_columns PASSED                  [ 30%]
tests/test_cleaner.py::test_clean_locations PASSED                       [ 38%]
tests/test_cleaner.py::test_handle_missing_categorical_values PASSED     [ 46%]
tests/test_cleaner.py::test_deduplicate_postings PASSED                  [ 53%]
tests/test_cleaner.py::test_clean_job_postings_end_to_end PASSED         [ 61%]
tests/test_collector.py::test_filter_target_company_exact PASSED         [ 69%]
tests/test_collector.py::test_filter_target_company_case_insensitive PASSED [ 76%]
tests/test_collector.py::test_validate_ingested_dataset_success PASSED   [ 84%]
tests/test_collector.py::test_validate_ingested_dataset_count_mismatch PASSED [ 92%]
tests/test_collector.py::test_validate_ingested_dataset_null_title PASSED [100%]

============================= 13 passed in 0.62s ==============================
```

---

## 6. Known Limitations & Downstream Recommendations

1. **Salary Sparsity**: Only 3.0% (15 of 498) of Microsoft postings disclose explicit compensation figures. Salary cannot be used as a primary continuous regression predictor for hiring volume, but serves as an informative categorical indicator (`has_salary_data`).
2. **Missing Job Descriptions**: The primary tabular dataset (`data_jobs.csv`) contains structured role titles, locations, and extracted skill arrays rather than raw full-text descriptions. For Sprint 3 (NLP Preprocessing), text normalization and phrase modeling will target `job_title` variations, standardized role taxonomy, and the secondary benchmark corpus (`data/raw/fake_job_postings.csv`) where raw full-text descriptions are available.
3. **Skill Array Serialization in CSV**: Writing Python lists and dicts to CSV serializes them back to strings for disk persistence. In Sprint 5 (SQLite Relational Database), these structures will be modeled into normalized relational tables (`postings`, `skills`, and a junction table `posting_skills`) to enable native SQL joins and aggregations.
