-- ============================================================
-- CadetX Sprint 5: Company and Competitor Demand Queries
-- Current dataset: Microsoft job postings only
-- Database: SQLite
-- ============================================================

-- 1. Company job posting overview
SELECT
    c.company_name,
    COUNT(j.job_id) AS total_job_postings
FROM companies c
LEFT JOIN job_postings j
    ON c.company_id = j.company_id
GROUP BY c.company_name
ORDER BY total_job_postings DESC;


-- 2. Most frequently advertised job titles
SELECT
    job_title_short,
    COUNT(*) AS posting_count
FROM job_postings
WHERE job_title_short IS NOT NULL
GROUP BY job_title_short
ORDER BY posting_count DESC
LIMIT 15;


-- 3. Job posting distribution by location
SELECT
    job_location,
    COUNT(*) AS posting_count
FROM job_postings
WHERE job_location IS NOT NULL
GROUP BY job_location
ORDER BY posting_count DESC
LIMIT 15;


-- 4. Job posting distribution by schedule type
SELECT
    job_schedule_type,
    COUNT(*) AS posting_count
FROM job_postings
WHERE job_schedule_type IS NOT NULL
GROUP BY job_schedule_type
ORDER BY posting_count DESC;


-- 5. Remote versus non-remote job postings
SELECT
    CASE
        WHEN job_work_from_home = 1 THEN 'Remote'
        WHEN job_work_from_home = 0 THEN 'Not Remote'
        ELSE 'Not Specified'
    END AS work_arrangement,
    COUNT(*) AS posting_count
FROM job_postings
GROUP BY work_arrangement
ORDER BY posting_count DESC;


-- 6. Most demanded skills
SELECT
    s.skill_name,
    COUNT(DISTINCT m.job_id) AS job_demand
FROM skills s
JOIN job_skill_map m
    ON s.skill_id = m.skill_id
GROUP BY s.skill_name
ORDER BY job_demand DESC, s.skill_name
LIMIT 20;


-- 7. Skill demand by category
SELECT
    sc.category_name,
    COUNT(DISTINCT scm.skill_id) AS unique_skills,
    COUNT(DISTINCT jsm.job_id) AS job_postings
FROM skill_categories sc
JOIN skill_category_map scm
    ON sc.category_id = scm.category_id
JOIN job_skill_map jsm
    ON scm.skill_id = jsm.skill_id
GROUP BY sc.category_name
ORDER BY job_postings DESC;


-- 8. Salary availability overview
SELECT
    COUNT(*) AS total_postings,
    COUNT(salary_annual_standardized) AS postings_with_salary,
    ROUND(AVG(salary_annual_standardized), 2) AS average_annual_salary,
    MIN(salary_annual_standardized) AS minimum_annual_salary,
    MAX(salary_annual_standardized) AS maximum_annual_salary
FROM job_postings;


-- 9. Entity distribution by entity label
SELECT
    e.entity_label,
    COUNT(DISTINCT e.entity_id) AS unique_entities,
    SUM(je.mention_count) AS total_mentions
FROM entities e
JOIN job_entities je
    ON e.entity_id = je.entity_id
GROUP BY e.entity_label
ORDER BY total_mentions DESC;


-- 10. Top entities mentioned in job postings
SELECT
    e.entity_text,
    e.entity_label,
    SUM(je.mention_count) AS total_mentions
FROM entities e
JOIN job_entities je
    ON e.entity_id = je.entity_id
GROUP BY e.entity_text, e.entity_label
ORDER BY total_mentions DESC
LIMIT 20;
