"""Unit tests for Stage 1 Data Collection and Ingestion."""

import pytest
import pandas as pd
from src.collection.collector import (
    filter_target_company,
    validate_ingested_dataset,
    TARGET_COMPANY,
)


@pytest.fixture
def sample_jobs_df():
    """Generates synthetic job postings DataFrame for testing."""
    return pd.DataFrame(
        {
            "job_title_short": ["Data Scientist", "Software Engineer", "Data Analyst"],
            "job_title": ["Data Scientist II", "Software Engineer", "Analyst"],
            "job_location": ["Redmond, WA", "Dublin, Ireland", "San Jose, CA"],
            "job_posted_date": ["2023-01-15 10:00:00", "2023-02-20 12:00:00", "2023-03-05 14:00:00"],
            "company_name": ["Microsoft", "microsoft", "OtherCorp"],
        }
    )


def test_filter_target_company_exact(sample_jobs_df):
    """Verifies exact case filtering for Microsoft."""
    result = filter_target_company(sample_jobs_df, company_name=TARGET_COMPANY, case_insensitive=False)
    assert len(result) == 1
    assert (result["company_name"] == "Microsoft").all()


def test_filter_target_company_case_insensitive(sample_jobs_df):
    """Verifies case-insensitive filtering matches all variations."""
    result = filter_target_company(sample_jobs_df, company_name="Microsoft", case_insensitive=True)
    assert len(result) == 2
    assert "OtherCorp" not in result["company_name"].values


def test_validate_ingested_dataset_success():
    """Verifies validation succeeds with matching count and zero nulls."""
    df = pd.DataFrame(
        {
            "job_title": ["Engineer 1", "Engineer 2"],
            "job_posted_date": ["2023-01-01", "2023-01-02"],
            "company_name": ["Microsoft", "Microsoft"],
        }
    )
    results = validate_ingested_dataset(df, expected_count=2, expected_company="Microsoft")
    assert results["all_valid"] is True
    assert results["count_matches"] is True


def test_validate_ingested_dataset_count_mismatch():
    """Verifies validation raises ValueError on count mismatch."""
    df = pd.DataFrame(
        {
            "job_title": ["Engineer 1"],
            "job_posted_date": ["2023-01-01"],
            "company_name": ["Microsoft"],
        }
    )
    with pytest.raises(ValueError, match="Record count validation failed"):
        validate_ingested_dataset(df, expected_count=2)


def test_validate_ingested_dataset_null_title():
    """Verifies validation raises ValueError when null titles exist."""
    df = pd.DataFrame(
        {
            "job_title": [None, "Engineer 2"],
            "job_posted_date": ["2023-01-01", "2023-01-02"],
            "company_name": ["Microsoft", "Microsoft"],
        }
    )
    with pytest.raises(ValueError, match="Null value validation failed"):
        validate_ingested_dataset(df, expected_count=2)
