import pandas as pd
import pytest

from src.features.feature_builder import (
    parse_skill_list,
    build_weekly_demand_features,
    build_weekly_skill_demand,
)


def make_sample_dataframe():
    """Create a small dataset for feature engineering tests."""
    return pd.DataFrame({
        "job_posted_date": [
            "2023-01-02",
            "2023-01-03",
            "2023-01-16",
        ],
        "extracted_skills": [
            '["Python", "SQL", "Python"]',
            '["Python"]',
            "[]",
        ],
    })


def test_parse_skill_list_json():
    result = parse_skill_list('["Python", "SQL"]')

    assert result == ["Python", "SQL"]


def test_parse_skill_list_python_format():
    result = parse_skill_list("['Python', 'SQL']")

    assert result == ["Python", "SQL"]


def test_parse_empty_skill_list():
    assert parse_skill_list("[]") == []
    assert parse_skill_list(None) == []


def test_weekly_demand_shape_and_counts():
    df = make_sample_dataframe()

    result = build_weekly_demand_features(df)

    assert len(result) == 3
    assert result["job_posting_count"].tolist() == [2, 0, 1]
    assert result["job_posting_count"].sum() == 3


def test_weekly_demand_lag_features():
    df = make_sample_dataframe()

    result = build_weekly_demand_features(df)

    assert pd.isna(result.loc[0, "demand_lag_1"])
    assert result.loc[1, "demand_lag_1"] == 2
    assert result.loc[2, "demand_lag_1"] == 0

    assert pd.isna(result.loc[0, "demand_lag_2"])
    assert result.loc[2, "demand_lag_2"] == 2


def test_rolling_mean_uses_previous_weeks():
    df = make_sample_dataframe()

    result = build_weekly_demand_features(df)

    assert pd.isna(result.loc[0, "rolling_mean_4"])
    assert result.loc[1, "rolling_mean_4"] == 2
    assert result.loc[2, "rolling_mean_4"] == 1


def test_weekly_skill_demand_counts():
    df = make_sample_dataframe()

    result = build_weekly_skill_demand(df)

    first_week = result[
        result["year_week"] == "2023-W01"
    ]

    python_count = first_week.loc[
        first_week["skill"] == "Python",
        "skill_posting_count"
    ].iloc[0]

    sql_count = first_week.loc[
        first_week["skill"] == "SQL",
        "skill_posting_count"
    ].iloc[0]

    assert python_count == 2
    assert sql_count == 1


def test_skill_count_does_not_exceed_weekly_postings():
    df = make_sample_dataframe()

    result = build_weekly_skill_demand(df)

    assert (
        result["skill_posting_count"]
        <= result["job_posting_count"]
    ).all()


def test_missing_date_column_raises_error():
    df = pd.DataFrame({
        "extracted_skills": ['["Python"]']
    })

    with pytest.raises(ValueError):
        build_weekly_demand_features(df)


def test_missing_skill_column_raises_error():
    df = pd.DataFrame({
        "job_posted_date": ["2023-01-02"]
    })

    with pytest.raises(ValueError):
        build_weekly_skill_demand(df)


def test_invalid_dates_raise_error():
    df = pd.DataFrame({
        "job_posted_date": ["invalid"],
        "extracted_skills": ['["Python"]'],
    })

    with pytest.raises(ValueError):
        build_weekly_demand_features(df)

    with pytest.raises(ValueError):
        build_weekly_skill_demand(df)