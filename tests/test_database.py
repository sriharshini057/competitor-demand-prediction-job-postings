import json
from pathlib import Path

import pandas as pd
import pytest

from src.database.db_manager import DatabaseManager


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "sql" / "schema.sql"


def make_sample_dataframe():
    columns = [
        "job_title_short", "job_title", "job_location", "job_via",
        "job_schedule_type", "job_work_from_home", "search_location",
        "job_posted_date", "job_no_degree_mention",
        "job_health_insurance", "job_country", "salary_rate",
        "salary_year_avg", "salary_hour_avg", "job_skills",
        "job_type_skills", "posted_date", "posted_year", "posted_month",
        "posted_week", "posted_day", "posted_dayofweek",
        "posted_quarter", "posted_year_week",
        "salary_annual_standardized", "has_salary_data",
        "job_skills_parsed", "job_skills_count", "has_skills_specified",
        "job_type_skills_parsed", "job_city", "job_title_tokens",
        "job_skills_list", "job_skills_normalized",
        "extracted_entities", "extracted_skills", "skill_categories",
        "skill_count", "entity_count",
    ]

    base = {column: None for column in columns}

    base.update({
        "job_title_short": "Data Engineer",
        "job_title": "Junior Data Engineer",
        "job_location": "Hyderabad, India",
        "job_via": "LinkedIn",
        "job_schedule_type": "Full-time",
        "job_work_from_home": 0,
        "search_location": "India",
        "job_posted_date": "2023-05-10",
        "job_no_degree_mention": 0,
        "job_health_insurance": 1,
        "job_country": "India",
        "salary_rate": "year",
        "salary_year_avg": float("nan"),
        "salary_hour_avg": float("nan"),
        "job_skills": '["python", "sql"]',
        "job_type_skills": "{}",
        "posted_date": "2023-05-10",
        "posted_year": 2023,
        "posted_month": 5,
        "posted_week": 19,
        "posted_day": 10,
        "posted_dayofweek": 2,
        "posted_quarter": 2,
        "posted_year_week": "2023-19",
        "salary_annual_standardized": float("nan"),
        "has_salary_data": 0,
        "job_skills_parsed": '["python", "sql"]',
        "job_skills_count": 2,
        "has_skills_specified": 1,
        "job_type_skills_parsed": "{}",
        "job_city": "Hyderabad",
        "job_title_tokens": '["junior", "data", "engineer"]',
        "job_skills_list": '["python", "sql"]',
        "job_skills_normalized": '["python", "sql"]',
        "extracted_entities": json.dumps([
            {"text": "Microsoft", "label": "ORG"},
            {"text": "Python", "label": "SKILL"},
            {"text": "Python", "label": "SKILL"},
        ]),
        "extracted_skills": json.dumps(["Python", "SQL"]),
        "skill_categories": json.dumps({
            "Programming": ["Python"],
            "Database": ["SQL"],
        }),
        "skill_count": 2,
        "entity_count": 3,
        "company_name": "Microsoft",
    })

    first = base.copy()
    second = base.copy()
    second.update({
        "job_title": "Data Analyst",
        "job_title_short": "Data Analyst",
        "extracted_entities": json.dumps([
            {"text": "Python", "label": "SKILL"},
        ]),
        "extracted_skills": json.dumps(["Python", "Pandas"]),
        "skill_categories": json.dumps({
            "Programming": ["Python"],
            "Data Analysis": ["Pandas"],
        }),
        "job_skills_count": 2,
        "skill_count": 2,
        "entity_count": 1,
    })

    return pd.DataFrame([first, second], columns=["company_name"] + columns)


@pytest.fixture
def manager(tmp_path):
    db_path = tmp_path / "test_database.db"
    db_manager = DatabaseManager(
        db_path=db_path,
        schema_path=SCHEMA,
    )
    db_manager.initialize_database()
    return db_manager


def test_initialize_database_creates_all_tables(manager):
    rows = manager.execute_query(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    )
    table_names = {row["name"] for row in rows}

    expected = {
        "companies",
        "job_postings",
        "skills",
        "job_skill_map",
        "skill_categories",
        "skill_category_map",
        "entities",
        "job_entities",
    }

    assert expected.issubset(table_names)


def test_load_dataframe_inserts_normalized_data(manager):
    stats = manager.load_dataframe(make_sample_dataframe())

    assert stats["jobs_loaded"] == 2
    assert stats["companies_loaded"] == 1
    assert stats["skills_loaded"] == 3
    assert stats["categories_loaded"] == 3
    assert stats["entities_loaded"] == 2

    counts = manager.get_table_counts()

    assert counts["job_postings"] == 2
    assert counts["companies"] == 1
    assert counts["skills"] == 3
    assert counts["job_skill_map"] == 4
    assert counts["entities"] == 2
    assert counts["job_entities"] == 3


def test_missing_salary_values_are_stored_as_null(manager):
    manager.load_dataframe(make_sample_dataframe())

    rows = manager.execute_query(
        "SELECT salary_year_avg, salary_hour_avg "
        "FROM job_postings"
    )

    assert len(rows) == 2
    assert all(row["salary_year_avg"] is None for row in rows)
    assert all(row["salary_hour_avg"] is None for row in rows)


def test_repeated_entity_mentions_are_counted(manager):
    manager.load_dataframe(make_sample_dataframe())

    rows = manager.execute_query(
        """
        SELECT je.mention_count
        FROM job_entities je
        JOIN entities e ON e.entity_id = je.entity_id
        JOIN job_postings j ON j.job_id = je.job_id
        WHERE e.entity_text = 'Python'
          AND e.entity_label = 'SKILL'
          AND j.source_row_number = 1
        """
    )

    assert len(rows) == 1
    assert rows[0]["mention_count"] == 2


def test_duplicate_load_is_rejected_without_adding_rows(manager):
    sample = make_sample_dataframe()
    manager.load_dataframe(sample)

    with pytest.raises(ValueError, match="already contains job postings"):
        manager.load_dataframe(sample)

    assert manager.get_table_counts()["job_postings"] == 2


def test_empty_dataframe_is_rejected(manager):
    with pytest.raises(ValueError, match="empty DataFrame"):
        manager.load_dataframe(pd.DataFrame())


def test_execute_query_returns_dictionary_rows(manager):
    manager.load_dataframe(make_sample_dataframe())

    rows = manager.execute_query(
        "SELECT job_title FROM job_postings ORDER BY source_row_number"
    )

    assert isinstance(rows, list)
    assert isinstance(rows[0], dict)
    assert rows[0]["job_title"] == "Junior Data Engineer"


def test_execute_query_blocks_write_operations_inside_cte(manager):
    query = """
        WITH attempt AS (
            SELECT 'blocked_test' AS company_name
        )
        INSERT INTO companies (company_name)
        SELECT company_name FROM attempt
    """

    with pytest.raises(Exception, match="readonly database"):
        manager.execute_query(query)

    assert manager.get_table_counts()["companies"] == 0


def test_database_has_no_foreign_key_violations(manager):
    manager.load_dataframe(make_sample_dataframe())

    violations = manager.execute_query("PRAGMA foreign_key_check")

    assert violations == []
