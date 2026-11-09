-- Sprint 5: Relational Database Schema
-- Project: Competitor Demand Prediction Using Job Postings
-- Database: SQLite

PRAGMA foreign_keys = ON;

-- 1. Companies
CREATE TABLE IF NOT EXISTS companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL UNIQUE
);

-- 2. Job postings
CREATE TABLE IF NOT EXISTS job_postings (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_row_number INTEGER NOT NULL UNIQUE,
    company_id INTEGER NOT NULL,

    job_title_short TEXT,
    job_title TEXT,
    job_location TEXT,
    job_via TEXT,
    job_schedule_type TEXT,
    job_work_from_home INTEGER CHECK (job_work_from_home IN (0,1)),
    search_location TEXT,
    job_posted_date TEXT,
    job_no_degree_mention INTEGER CHECK (job_no_degree_mention IN (0,1)),
    job_health_insurance INTEGER CHECK (job_health_insurance IN (0,1)),
    job_country TEXT,
    salary_rate TEXT,
    salary_year_avg REAL,
    salary_hour_avg REAL,

    job_skills TEXT,
    job_type_skills TEXT,
    posted_date TEXT,
    posted_year INTEGER,
    posted_month INTEGER,
    posted_week INTEGER,
    posted_day INTEGER,
    posted_dayofweek INTEGER,
    posted_quarter INTEGER,
    posted_year_week TEXT,
    salary_annual_standardized REAL,
    has_salary_data INTEGER CHECK (has_salary_data IN (0,1)),
    job_skills_parsed TEXT,
    job_skills_count INTEGER,
    has_skills_specified INTEGER CHECK (has_skills_specified IN (0,1)),
    job_type_skills_parsed TEXT,
    job_city TEXT,
    job_title_tokens TEXT,
    job_skills_list TEXT,
    job_skills_normalized TEXT,
    extracted_entities TEXT,
    extracted_skills TEXT,
    skill_categories TEXT,
    skill_count INTEGER,
    entity_count INTEGER,

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);

-- 3. Unique extracted skills
CREATE TABLE IF NOT EXISTS skills (
    skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL UNIQUE
);

-- 4. Job-to-skill relationship
CREATE TABLE IF NOT EXISTS job_skill_map (
    job_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES job_postings(job_id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);

-- 5. Skill categories
CREATE TABLE IF NOT EXISTS skill_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE
);

-- 6. Skill-to-category relationship
CREATE TABLE IF NOT EXISTS skill_category_map (
    skill_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (skill_id, category_id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id),
    FOREIGN KEY (category_id) REFERENCES skill_categories(category_id)
);

-- 7. Extracted named entities
CREATE TABLE IF NOT EXISTS entities (
    entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_text TEXT NOT NULL,
    entity_label TEXT NOT NULL,
    UNIQUE (entity_text, entity_label)
);

-- 8. Job-to-entity relationship
CREATE TABLE IF NOT EXISTS job_entities (
    job_id INTEGER NOT NULL,
    entity_id INTEGER NOT NULL,
    mention_count INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (job_id, entity_id),
    FOREIGN KEY (job_id) REFERENCES job_postings(job_id),
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_jobs_company
ON job_postings(company_id);

CREATE INDEX IF NOT EXISTS idx_jobs_posted_date
ON job_postings(posted_date);

CREATE INDEX IF NOT EXISTS idx_jobs_year_month
ON job_postings(posted_year, posted_month);

CREATE INDEX IF NOT EXISTS idx_jobs_title
ON job_postings(job_title_short);

CREATE INDEX IF NOT EXISTS idx_jobs_location
ON job_postings(job_location);

CREATE INDEX IF NOT EXISTS idx_job_skill_skill
ON job_skill_map(skill_id);

CREATE INDEX IF NOT EXISTS idx_job_entity_entity
ON job_entities(entity_id);

CREATE INDEX IF NOT EXISTS idx_entities_label
ON entities(entity_label);
