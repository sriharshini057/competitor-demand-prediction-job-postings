-- ============================================================
-- CadetX Sprint 5: Hiring Trend Analysis Queries
-- Database: SQLite
-- Dataset: Microsoft job postings
-- ============================================================

-- 1. Monthly job posting trends
SELECT
    posted_year,
    posted_month,
    COUNT(*) AS total_postings
FROM job_postings
WHERE posted_year IS NOT NULL
  AND posted_month IS NOT NULL
GROUP BY posted_year, posted_month
ORDER BY posted_year, posted_month;


-- 2. Yearly job posting trends
SELECT
    posted_year,
    COUNT(*) AS total_postings
FROM job_postings
WHERE posted_year IS NOT NULL
GROUP BY posted_year
ORDER BY posted_year;


-- 3. Weekly job posting activity
SELECT
    posted_year_week,
    COUNT(*) AS total_postings
FROM job_postings
WHERE posted_year_week IS NOT NULL
GROUP BY posted_year_week
ORDER BY posted_year_week;


-- 4. Quarterly job posting distribution
SELECT
    posted_year,
    posted_quarter,
    COUNT(*) AS total_postings
FROM job_postings
WHERE posted_year IS NOT NULL
  AND posted_quarter IS NOT NULL
GROUP BY posted_year, posted_quarter
ORDER BY posted_year, posted_quarter;


-- 5. Job postings by day of the week
SELECT
    posted_dayofweek,
    COUNT(*) AS total_postings
FROM job_postings
WHERE posted_dayofweek IS NOT NULL
GROUP BY posted_dayofweek
ORDER BY total_postings DESC;


-- 6. Monthly demand for extracted skills
SELECT
    j.posted_year,
    j.posted_month,
    s.skill_name,
    COUNT(DISTINCT j.job_id) AS job_demand
FROM job_postings j
JOIN job_skill_map m
    ON j.job_id = m.job_id
JOIN skills s
    ON m.skill_id = s.skill_id
WHERE j.posted_year IS NOT NULL
  AND j.posted_month IS NOT NULL
GROUP BY
    j.posted_year,
    j.posted_month,
    s.skill_name
ORDER BY
    j.posted_year,
    j.posted_month,
    job_demand DESC;


-- 7. Salary availability by year
SELECT
    posted_year,
    COUNT(*) AS total_postings,
    COUNT(salary_annual_standardized) AS postings_with_salary,
    ROUND(AVG(salary_annual_standardized), 2) AS average_annual_salary
FROM job_postings
WHERE posted_year IS NOT NULL
GROUP BY posted_year
ORDER BY posted_year;


-- 8. Job title demand over time
SELECT
    posted_year,
    job_title_short,
    COUNT(*) AS total_postings
FROM job_postings
WHERE posted_year IS NOT NULL
  AND job_title_short IS NOT NULL
GROUP BY posted_year, job_title_short
ORDER BY posted_year, total_postings DESC;


-- 9. Remote work trends by year
SELECT
    posted_year,
    CASE
        WHEN job_work_from_home = 1 THEN 'Remote'
        WHEN job_work_from_home = 0 THEN 'Not Remote'
        ELSE 'Not Specified'
    END AS work_arrangement,
    COUNT(*) AS total_postings
FROM job_postings
WHERE posted_year IS NOT NULL
GROUP BY posted_year, work_arrangement
ORDER BY posted_year, total_postings DESC;


-- 10. Job posting trends by location
SELECT
    posted_year,
    job_location,
    COUNT(*) AS total_postings
FROM job_postings
WHERE posted_year IS NOT NULL
  AND job_location IS NOT NULL
GROUP BY posted_year, job_location
ORDER BY posted_year, total_postings DESC;
