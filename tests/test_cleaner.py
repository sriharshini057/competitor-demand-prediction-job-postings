"""Unit tests for Stage 2 Data Cleaning and Tabular Preprocessing."""

import pytest
import numpy as np
import pandas as pd
from src.preprocessing.cleaner import (
    standardize_company_name,
    normalize_dates,
    standardize_salaries,
    parse_skills_columns,
    clean_locations,
    handle_missing_categorical_values,
    deduplicate_postings,
    clean_job_postings,
    validate_cleaned_dataset,
)


@pytest.fixture
def raw_sample_data():
    """Generates synthetic uncleaned job postings."""
    return pd.DataFrame(
        {
            "job_title_short": ["Software Engineer", "Data Scientist", "Software Engineer"],
            "job_title": ["Software Engineer", "Senior Data Scientist", "Software Engineer"],
            "job_location": ["Dublin, Ireland", "Redmond, WA, USA", "Dublin, Ireland"],
            "job_via": ["via LinkedIn", "via Indeed", "via LinkedIn"],
            "job_schedule_type": ["Full-time", None, "Full-time"],
            "job_work_from_home": [False, True, False],
            "search_location": ["Ireland", "United States", "Ireland"],
            "job_posted_date": [
                "2023-01-10 14:30:00",
                "2023-06-15 09:15:00",
                "2023-01-10 14:30:00",  # Duplicate row
            ],
            "job_no_degree_mention": [False, True, False],
            "job_health_insurance": [False, True, False],
            "job_country": ["Ireland", "United States", "Ireland"],
            "salary_rate": [None, "hour", None],
            "salary_year_avg": [120000.0, None, 120000.0],
            "salary_hour_avg": [None, 65.0, None],
            "company_name": ["Microsoft", "microsoft ", "Microsoft"],
            "job_skills": ["['python', 'azure', 'sql']", "['r', 'python']", "['python', 'azure', 'sql']"],
            "job_type_skills": [
                "{'cloud': ['azure'], 'programming': ['python', 'sql']}",
                "{'programming': ['r', 'python']}",
                "{'cloud': ['azure'], 'programming': ['python', 'sql']}",
            ],
        }
    )


def test_standardize_company_name(raw_sample_data):
    """Verifies all company name variations are converted to canonical 'Microsoft'."""
    res = standardize_company_name(raw_sample_data, target_company="Microsoft")
    assert (res["company_name"] == "Microsoft").all()


def test_normalize_dates(raw_sample_data):
    """Verifies datetime conversion and temporal feature extraction."""
    res = normalize_dates(raw_sample_data)
    assert pd.api.types.is_datetime64_any_dtype(res["job_posted_date"])
    assert "posted_year" in res.columns
    assert "posted_week" in res.columns
    assert "posted_month" in res.columns
    assert res.loc[0, "posted_year"] == 2023
    assert res.loc[0, "posted_month"] == 1
    assert res.loc[0, "posted_week"] == 2


def test_standardize_salaries(raw_sample_data):
    """Verifies annualization of hourly rates (hour * 2080) and preservation of yearly rates."""
    res = standardize_salaries(raw_sample_data)
    # First row: year salary 120,000
    assert res.loc[0, "salary_annual_standardized"] == 120000.0
    # Second row: hourly rate $65 -> 65 * 2080 = 135,200
    assert res.loc[1, "salary_annual_standardized"] == 65.0 * 2080
    assert res["has_salary_data"].all()


def test_parse_skills_columns(raw_sample_data):
    """Verifies parsing of string lists/dicts into native Python objects."""
    res = parse_skills_columns(raw_sample_data)
    assert isinstance(res.loc[0, "job_skills_parsed"], list)
    assert res.loc[0, "job_skills_parsed"] == ["python", "azure", "sql"]
    assert res.loc[0, "job_skills_count"] == 3
    assert bool(res.loc[0, "has_skills_specified"]) is True
    assert isinstance(res.loc[0, "job_type_skills_parsed"], dict)
    assert res.loc[0, "job_type_skills_parsed"]["cloud"] == ["azure"]


def test_clean_locations(raw_sample_data):
    """Verifies city and country parsing."""
    res = clean_locations(raw_sample_data)
    assert res.loc[0, "job_city"] == "Dublin"
    assert res.loc[1, "job_city"] == "Redmond"


def test_handle_missing_categorical_values(raw_sample_data):
    """Verifies missing schedule types and rates are replaced with 'Unspecified'."""
    res = handle_missing_categorical_values(raw_sample_data)
    assert res.loc[1, "job_schedule_type"] == "Unspecified"
    assert res.loc[0, "salary_rate"] == "Unspecified"


def test_deduplicate_postings(raw_sample_data):
    """Verifies duplicates are detected and removed."""
    res, dropped = deduplicate_postings(raw_sample_data)
    assert dropped == 1
    assert len(res) == 2


def test_clean_job_postings_end_to_end(raw_sample_data):
    """Verifies complete cleaning pipeline runs end-to-end and validates."""
    cleaned = clean_job_postings(raw_sample_data)
    assert len(cleaned) == 2
    metrics = validate_cleaned_dataset(cleaned)
    assert metrics["total_records"] == 2
    assert metrics["null_titles"] == 0
    assert metrics["null_dates"] == 0
    assert metrics["non_microsoft_records"] == 0
