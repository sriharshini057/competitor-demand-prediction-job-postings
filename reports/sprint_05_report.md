# Sprint 5 Report: Database Storage and SQL Analysis

## 1. Sprint Overview

**Sprint:** 5
**Project:** Competitor Demand Prediction Using Job Postings
**Focus:** SQLite Database Design, Data Ingestion, and SQL Analysis
**Dataset Scope:** Microsoft job postings

Sprint 5 implements a relational SQLite database to store the processed Microsoft job-posting data, extracted skills, skill categories, and named entities.

## 2. Database Architecture

The database is stored at:

`data/database/competitor_demand.db`

The database contains eight application tables:

1. `companies`
2. `job_postings`
3. `skills`
4. `job_skill_map`
5. `skill_categories`
6. `skill_category_map`
7. `entities`
8. `job_entities`

The schema includes primary keys, foreign-key relationships, unique constraints, validation checks, and indexes.

## 3. Database Implementation

Implementation file:

`src/database/db_manager.py`

The `DatabaseManager` implementation supports:

- SQLite database connections.
- Database initialization using the SQL schema.
- Data cleaning and structured-value parsing.
- Loading processed job-posting data.
- Duplicate-load protection.
- Read-only SQL query execution.
- Database table-count inspection.

Foreign-key enforcement is enabled on database connections.

## 4. Data Ingestion Results

The processed Microsoft dataset was successfully imported into SQLite.

| Database table | Records |
|---|---:|
| companies | 1 |
| job_postings | 498 |
| skills | 47 |
| job_skill_map | 1,686 |
| skill_categories | 8 |
| skill_category_map | 47 |
| entities | 195 |
| job_entities | 2,056 |

## 5. SQL Analysis

Two SQL query files were implemented:

- `sql/competitor_queries.sql`
- `sql/trend_queries.sql`

The competitor analysis queries cover company overview, job titles, locations, schedule types, remote work, skill demand, salary overview, and entity analysis.

The trend analysis queries cover monthly, yearly, weekly, and quarterly posting trends, weekday patterns, skill demand over time, salary trends, job-title trends, remote-work trends, and location trends.

**Validation:** All 20 SQL queries passed testing (10 competitor queries and 10 trend queries).

## 6. Database Validation

The following checks were completed:

- SQLite integrity check returned `ok`.
- Foreign-key enforcement was enabled.
- Foreign-key violations: 0.
- Orphan skill links: 0.
- Orphan entity links: 0.
- Dataset schema matched the database ingestion requirements.
- Structured JSON values were validated during preflight checks.

## 7. Unit Testing

Database-specific tests are implemented in:

`tests/test_database.py`

The tests cover database initialization, data loading, missing salary handling, entity mentions, duplicate-load protection, empty input rejection, read-only query execution, write-operation blocking, and foreign-key integrity.

**Full project test result:**

`169 passed in 10.04s`

No test failures or warnings were reported in the final full-suite run.

## 8. Sprint 5 Deliverables

- `sql/schema.sql`
- `sql/competitor_queries.sql`
- `sql/trend_queries.sql`
- `src/database/db_manager.py`
- `tests/test_database.py`
- `data/database/competitor_demand.db`
- `reports/sprint_05_report.md`

## 9. Conclusion

Sprint 5 successfully implemented and validated SQLite database storage for the processed Microsoft job-posting dataset. The database contains job postings, skills, skill categories, and extracted entities with relational mappings.

All 20 SQL analysis queries passed validation, and the complete project test suite passed with 169 tests.

The database implementation establishes a structured foundation for subsequent analysis and reporting.

**Sprint 5 Status: Completed and Validated.**
