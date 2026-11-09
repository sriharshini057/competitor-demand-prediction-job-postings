
"""Feature engineering module.

Sprint 6: Generate weekly demand features and weekly skill-demand data.
"""

import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "data" / "processed" / "microsoft_jobs_skills.csv"
OUTPUT_DIR = ROOT / "data" / "processed"


def parse_skill_list(value):
    """Convert a serialized skill list into a Python list."""
    if isinstance(value, list):
        return value

    if value is None:
        return []

    if isinstance(value, float) and np.isnan(value):
        return []

    if not isinstance(value, str) or not value.strip():
        return []

    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return []

    if not isinstance(parsed, (list, tuple, set)):
        return []

    return [
        str(skill).strip()
        for skill in parsed
        if str(skill).strip()
    ]


def build_weekly_demand_features(df):
    """Build weekly posting counts and historical demand features."""
    if "job_posted_date" not in df.columns:
        raise ValueError("Missing required column: job_posted_date")

    data = df.copy()

    data["job_posted_date"] = pd.to_datetime(
        data["job_posted_date"], errors="coerce"
    )
    data = data.dropna(subset=["job_posted_date"])

    if data.empty:
        raise ValueError("No valid job posting dates found.")

    data["week_start"] = (
        data["job_posted_date"]
        .dt.to_period("W-SUN")
        .dt.start_time
    )

    weekly = (
        data.groupby("week_start")
        .size()
        .rename("job_posting_count")
        .to_frame()
    )

    complete_weeks = pd.date_range(
        start=weekly.index.min(),
        end=weekly.index.max(),
        freq="W-MON"
    )

    weekly = weekly.reindex(complete_weeks, fill_value=0)
    weekly.index.name = "week_start"
    weekly = weekly.reset_index()

    weekly["year_week"] = weekly["week_start"].dt.strftime("%G-W%V")
    weekly["year"] = weekly["week_start"].dt.year
    weekly["month"] = weekly["week_start"].dt.month
    weekly["quarter"] = weekly["week_start"].dt.quarter
    weekly["week_of_year"] = (
        weekly["week_start"].dt.isocalendar().week.astype(int)
    )

    for lag in [1, 2, 4]:
        weekly[f"demand_lag_{lag}"] = (
            weekly["job_posting_count"].shift(lag)
        )

    previous_demand = weekly["job_posting_count"].shift(1)

    weekly["rolling_mean_4"] = (
        previous_demand.rolling(window=4, min_periods=1).mean()
    )

    weekly["rolling_std_4"] = (
        previous_demand.rolling(window=4, min_periods=2).std()
    )

    return weekly


def build_weekly_skill_demand(df):
    """Calculate weekly job-posting demand for each extracted skill."""
    required = {"job_posted_date", "extracted_skills"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = df.copy()

    data["job_posted_date"] = pd.to_datetime(
        data["job_posted_date"], errors="coerce"
    )
    data = data.dropna(subset=["job_posted_date"])

    if data.empty:
        raise ValueError("No valid job posting dates found.")

    data["week_start"] = (
        data["job_posted_date"]
        .dt.to_period("W-SUN")
        .dt.start_time
    )

    data["skills"] = data["extracted_skills"].apply(parse_skill_list)
    data["skills"] = data["skills"].apply(
        lambda skills: sorted(set(skills))
    )

    data["job_posting_count"] = (
        data.groupby("week_start")["job_posted_date"].transform("size")
    )

    skill_data = data.explode("skills").dropna(subset=["skills"])

    if skill_data.empty:
        return pd.DataFrame(columns=[
            "week_start", "year_week", "skill",
            "skill_posting_count", "job_posting_count",
            "skill_demand_share"
        ])

    result = (
        skill_data.groupby(
            ["week_start", "skills", "job_posting_count"]
        )
        .size()
        .reset_index(name="skill_posting_count")
        .rename(columns={"skills": "skill"})
    )

    result["year_week"] = result["week_start"].dt.strftime("%G-W%V")

    result["skill_demand_share"] = (
        result["skill_posting_count"] / result["job_posting_count"]
    )

    return result[[
        "week_start",
        "year_week",
        "skill",
        "skill_posting_count",
        "job_posting_count",
        "skill_demand_share"
    ]].sort_values(
        ["week_start", "skill"]
    ).reset_index(drop=True)


def save_feature_datasets(input_file=INPUT_FILE, output_dir=OUTPUT_DIR):
    """Generate and save both Sprint 6 feature datasets."""
    input_file = Path(input_file)
    output_dir = Path(output_dir)

    if not input_file.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_file}")

    df = pd.read_csv(input_file)

    weekly_features = build_weekly_demand_features(df)
    weekly_skills = build_weekly_skill_demand(df)

    output_dir.mkdir(parents=True, exist_ok=True)

    demand_path = output_dir / "weekly_demand_features.csv"
    skills_path = output_dir / "weekly_skill_demand.csv"

    weekly_features.to_csv(demand_path, index=False)
    weekly_skills.to_csv(skills_path, index=False)

    print("Sprint 6 feature engineering completed.")
    print(f"Weekly demand dataset: {demand_path}")
    print(f"Weekly skill dataset: {skills_path}")
    print(f"Weekly observations: {len(weekly_features)}")
    print(f"Skill-demand records: {len(weekly_skills)}")

    return demand_path, skills_path


if __name__ == "__main__":
    save_feature_datasets()
