"""Data Cleaning and Tabular Preprocessing Module.

Stage 2: Missing value imputation, deduplication, date normalization,
salary standardization, location parsing, and schema validation.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import ast
import logging
import numpy as np
import pandas as pd

# Configure module logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Default paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "microsoft_jobs.csv"
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "microsoft_jobs_cleaned.csv"
STANDARD_WORKING_HOURS_PER_YEAR = 2080  # 40 hrs/wk * 52 wks


def load_input_dataset(file_path: Path = DEFAULT_INPUT_FILE) -> pd.DataFrame:
    """Loads the ingested job postings dataset.

    Args:
        file_path: Path to the ingested CSV file.

    Returns:
        pd.DataFrame containing the dataset.

    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if not file_path.exists():
        logger.error("Input file not found at: %s", file_path)
        raise FileNotFoundError(f"Input file not found at: {file_path}")

    logger.info("Loading dataset for cleaning from: %s", file_path)
    df = pd.read_csv(file_path)
    logger.info("Dataset loaded successfully: %d rows, %d columns", len(df), len(df.columns))
    return df


def standardize_company_name(
    df: pd.DataFrame,
    target_company: str = "Microsoft",
) -> pd.DataFrame:
    """Standardizes the company name column to canonical capitalization and stripped whitespace.

    Args:
        df: Input DataFrame.
        target_company: Canonical company name string.

    Returns:
        DataFrame copy with normalized company_name.
    """
    df = df.copy()
    if "company_name" in df.columns:
        df["company_name"] = df["company_name"].astype(str).str.strip()
        # Canonicalize Microsoft mentions
        mask = df["company_name"].str.lower() == target_company.lower()
        df.loc[mask, "company_name"] = target_company
    return df


def normalize_dates(
    df: pd.DataFrame,
    date_col: str = "job_posted_date",
) -> pd.DataFrame:
    """Parses posting timestamps and generates structured temporal features.

    Features generated:
    - job_posted_date (datetime64[ns])
    - posted_date (string YYYY-MM-DD)
    - posted_year (int)
    - posted_month (int, 1-12)
    - posted_week (int, ISO week 1-53)
    - posted_day (int, 1-31)
    - posted_dayofweek (int, 0=Mon, 6=Sun)
    - posted_quarter (int, 1-4)
    - posted_year_week (string, YYYY-WW)

    Args:
        df: Input DataFrame.
        date_col: Name of the raw datetime column.

    Returns:
        DataFrame copy with temporal features.
    """
    df = df.copy()
    logger.info("Normalizing dates and generating temporal features from column: '%s'", date_col)
    dt_series = pd.to_datetime(df[date_col], errors="coerce")

    if dt_series.isnull().any():
        null_count = dt_series.isnull().sum()
        logger.warning("Found %d unparseable dates in '%s'", null_count, date_col)

    df[date_col] = dt_series
    df["posted_date"] = dt_series.dt.strftime("%Y-%m-%d")
    df["posted_year"] = dt_series.dt.year.astype("Int64")
    df["posted_month"] = dt_series.dt.month.astype("Int64")
    df["posted_week"] = dt_series.dt.isocalendar().week.astype("Int64")
    df["posted_day"] = dt_series.dt.day.astype("Int64")
    df["posted_dayofweek"] = dt_series.dt.dayofweek.astype("Int64")
    df["posted_quarter"] = dt_series.dt.quarter.astype("Int64")
    df["posted_year_week"] = dt_series.dt.strftime("%Y-W%V")

    return df


def standardize_salaries(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates standardized annual salary across yearly and hourly compensation fields.

    Logic:
    1. If salary_year_avg is present and > 0, use salary_year_avg.
    2. Else if salary_hour_avg is present and > 0, convert to annual:
       hourly * 2080 (40 hours/week * 52 weeks).
    3. Adds boolean flag has_salary_data.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame copy with standardized salary metrics.
    """
    df = df.copy()
    logger.info("Standardizing compensation data...")

    salary_annual = pd.Series(np.nan, index=df.index, dtype="float64")

    # Use reported yearly salary where valid
    if "salary_year_avg" in df.columns:
        year_mask = df["salary_year_avg"].notnull() & (df["salary_year_avg"] > 0)
        salary_annual.loc[year_mask] = df.loc[year_mask, "salary_year_avg"]

    # Convert hourly salary to annual where yearly is not provided
    if "salary_hour_avg" in df.columns:
        hour_mask = (
            salary_annual.isnull()
            & df["salary_hour_avg"].notnull()
            & (df["salary_hour_avg"] > 0)
        )
        salary_annual.loc[hour_mask] = df.loc[hour_mask, "salary_hour_avg"] * STANDARD_WORKING_HOURS_PER_YEAR

    df["salary_annual_standardized"] = salary_annual
    df["has_salary_data"] = salary_annual.notnull()

    sal_count = int(df["has_salary_data"].sum())
    logger.info("Standardized salary calculated: %d records have compensation data.", sal_count)
    return df


def parse_skills_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Parses serialized list and dictionary strings of skills into structured Python objects.

    Adds:
    - job_skills_parsed: List of lowercase skill strings.
    - job_skills_count: Integer number of explicit skills listed.
    - has_skills_specified: Boolean flag indicating presence of skills.
    - job_type_skills_parsed: Dictionary mapping skill category to list of skills.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame copy with structured skill fields.
    """
    df = df.copy()
    logger.info("Parsing skill columns into structured objects...")

    def safe_parse_list(val: Any) -> List[str]:
        if pd.isna(val) or val is None or str(val).strip() == "":
            return []
        if isinstance(val, list):
            return [str(s).strip().lower() for s in val]
        try:
            parsed = ast.literal_eval(str(val))
            if isinstance(parsed, list):
                return [str(s).strip().lower() for s in parsed]
        except (ValueError, SyntaxError):
            pass
        return [s.strip().lower() for s in str(val).split(",") if s.strip()]

    def safe_parse_dict(val: Any) -> Dict[str, List[str]]:
        if pd.isna(val) or val is None or str(val).strip() == "":
            return {}
        if isinstance(val, dict):
            return {
                str(k).strip().lower(): [str(s).strip().lower() for s in v]
                for k, v in val.items()
                if isinstance(v, list)
            }
        try:
            parsed = ast.literal_eval(str(val))
            if isinstance(parsed, dict):
                return {
                    str(k).strip().lower(): [str(s).strip().lower() for s in v]
                    for k, v in parsed.items()
                    if isinstance(v, list)
                }
        except (ValueError, SyntaxError):
            pass
        return {}

    if "job_skills" in df.columns:
        parsed_skills = df["job_skills"].apply(safe_parse_list)
        df["job_skills_parsed"] = parsed_skills
        df["job_skills_count"] = parsed_skills.apply(len)
        df["has_skills_specified"] = df["job_skills_count"] > 0
    else:
        df["job_skills_parsed"] = [[] for _ in range(len(df))]
        df["job_skills_count"] = 0
        df["has_skills_specified"] = False

    if "job_type_skills" in df.columns:
        df["job_type_skills_parsed"] = df["job_type_skills"].apply(safe_parse_dict)
    else:
        df["job_type_skills_parsed"] = [{} for _ in range(len(df))]

    return df


def clean_locations(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts standardized city and country names from job location strings.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame copy with parsed city and country attributes.
    """
    df = df.copy()
    logger.info("Cleaning location attributes...")

    def extract_city(loc_str: Any) -> str:
        if pd.isna(loc_str) or not str(loc_str).strip():
            return "Unspecified"
        s = str(loc_str).strip()
        if s.lower() == "anywhere":
            return "Remote/Anywhere"
        # Fix known character encoding artifacts in location names (e.g. San Jos -> San José)
        s = s.replace("San Jos\ufffd Province", "San José").replace("San Jos\ufffd", "San José")
        # Split on comma (e.g. "Dublin, Ireland" -> "Dublin")
        parts = [p.strip() for p in s.split(",")]
        city = parts[0] if parts else "Unspecified"
        if "San José" in city:
            return "San José"
        return city

    if "job_location" in df.columns:
        df["job_city"] = df["job_location"].apply(extract_city)
    else:
        df["job_city"] = "Unspecified"

    if "job_country" in df.columns:
        df["job_country"] = df["job_country"].fillna("Unspecified").astype(str).str.strip()

    return df


def handle_missing_categorical_values(df: pd.DataFrame) -> pd.DataFrame:
    """Imputes missing categorical attributes with standardized placeholders.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame copy with imputed categorical values.
    """
    df = df.copy()
    if "job_schedule_type" in df.columns:
        df["job_schedule_type"] = df["job_schedule_type"].fillna("Unspecified").astype(str).str.strip()

    if "salary_rate" in df.columns:
        df["salary_rate"] = df["salary_rate"].fillna("Unspecified").astype(str).str.strip()

    for bool_col in ["job_work_from_home", "job_no_degree_mention", "job_health_insurance"]:
        if bool_col in df.columns:
            df[bool_col] = df[bool_col].fillna(False).astype(bool)

    return df


def deduplicate_postings(
    df: pd.DataFrame,
    subset_cols: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, int]:
    """Identifies and removes duplicate job postings.

    Args:
        df: Input DataFrame.
        subset_cols: Columns used to determine uniqueness. Defaults to
                     ['job_title', 'job_location', 'job_posted_date', 'company_name'].

    Returns:
        Tuple of (deduplicated DataFrame, count of duplicates removed).
    """
    if subset_cols is None:
        subset_cols = ["job_title", "job_location", "job_posted_date", "company_name"]

    existing_subset = [c for c in subset_cols if c in df.columns]
    initial_len = len(df)
    df_dedup = df.drop_duplicates(subset=existing_subset).copy()
    dropped_count = initial_len - len(df_dedup)

    if dropped_count > 0:
        logger.warning("Removed %d duplicate records based on subset: %s", dropped_count, existing_subset)
    else:
        logger.info("Deduplication check passed: 0 duplicate records found.")

    return df_dedup, dropped_count


def validate_cleaned_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates schema integrity and data completeness post-cleaning.

    Validation checks:
    - Non-empty DataFrame.
    - Zero nulls in primary identifiers (job_title, job_posted_date, company_name).
    - Valid datetime types for temporal columns.
    - Consistency of company_name == 'Microsoft'.

    Args:
        df: Cleaned DataFrame to validate.

    Returns:
        Dictionary of validation results.

    Raises:
        ValueError: If a critical validation check fails.
    """
    logger.info("Validating cleaned dataset integrity...")
    total_records = len(df)
    if total_records == 0:
        raise ValueError("Validation failed: Cleaned DataFrame is empty!")

    null_titles = int(df["job_title"].isnull().sum())
    null_dates = int(df["job_posted_date"].isnull().sum())
    null_companies = int(df["company_name"].isnull().sum())
    non_microsoft = int((df["company_name"] != "Microsoft").sum())

    results = {
        "total_records": total_records,
        "null_titles": null_titles,
        "null_dates": null_dates,
        "null_companies": null_companies,
        "non_microsoft_records": non_microsoft,
        "has_temporal_features": "posted_week" in df.columns and "posted_year" in df.columns,
        "has_parsed_skills": "job_skills_parsed" in df.columns,
        "has_standardized_salary": "salary_annual_standardized" in df.columns,
    }

    if null_titles > 0 or null_dates > 0 or null_companies > 0:
        raise ValueError(
            f"Validation failed with nulls: Titles={null_titles}, Dates={null_dates}, Companies={null_companies}"
        )

    if non_microsoft > 0:
        raise ValueError(f"Validation failed: Found {non_microsoft} non-Microsoft records!")

    logger.info("Validation passed successfully: %d records verified.", total_records)
    return results


def save_cleaned_dataset(
    df: pd.DataFrame,
    output_path: Path = DEFAULT_OUTPUT_FILE,
) -> Path:
    """Persists cleaned dataset to CSV. Serializes complex Python objects (lists/dicts) to JSON-compatible strings.

    Args:
        df: Cleaned DataFrame to serialize.
        output_path: Path to destination file.

    Returns:
        Path to the saved CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_to_save = df.copy()

    # Convert list/dict objects to string representations for CSV persistence
    if "job_skills_parsed" in df_to_save.columns:
        df_to_save["job_skills_parsed"] = df_to_save["job_skills_parsed"].apply(str)
    if "job_type_skills_parsed" in df_to_save.columns:
        df_to_save["job_type_skills_parsed"] = df_to_save["job_type_skills_parsed"].apply(str)

    df_to_save.to_csv(output_path, index=False)
    file_size_kb = output_path.stat().st_size / 1024
    logger.info("Cleaned dataset successfully saved to: %s (%.2f KB, %d records)", output_path, file_size_kb, len(df))
    return output_path


def clean_job_postings(df: pd.DataFrame) -> pd.DataFrame:
    """Executes the complete in-memory data cleaning pipeline on a job postings DataFrame.

    Steps:
    1. Standardize company name.
    2. Normalize datetime and generate calendar features.
    3. Standardize salary metrics.
    4. Parse skills strings into lists and dictionaries.
    5. Clean and parse locations.
    6. Impute categorical missing values.
    7. Deduplicate postings.

    Args:
        df: Raw or ingested postings DataFrame.

    Returns:
        Cleaned, enriched DataFrame.
    """
    df_clean = df.copy()
    df_clean = standardize_company_name(df_clean, target_company="Microsoft")
    df_clean = normalize_dates(df_clean, date_col="job_posted_date")
    df_clean = standardize_salaries(df_clean)
    df_clean = parse_skills_columns(df_clean)
    df_clean = clean_locations(df_clean)
    df_clean = handle_missing_categorical_values(df_clean)
    df_clean, _ = deduplicate_postings(df_clean)
    return df_clean


def run_cleaning_pipeline(
    input_path: Path = DEFAULT_INPUT_FILE,
    output_path: Path = DEFAULT_OUTPUT_FILE,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Orchestrates end-to-end cleaning pipeline from raw/processed file to cleaned artifact.

    Args:
        input_path: Source CSV path.
        output_path: Destination CSV path.

    Returns:
        Tuple of (cleaned DataFrame, validation metrics).
    """
    logger.info("Executing Stage 2 Data Cleaning pipeline...")
    df_in = load_input_dataset(input_path)
    df_clean = clean_job_postings(df_in)
    metrics = validate_cleaned_dataset(df_clean)
    save_cleaned_dataset(df_clean, output_path=output_path)
    logger.info("Stage 2 Data Cleaning pipeline completed successfully.")
    return df_clean, metrics


if __name__ == "__main__":
    cleaned_df, validation_metrics = run_cleaning_pipeline()
    print("\n" + "=" * 60)
    print("STAGE 2: DATA CLEANING EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total Postings Processed:   {len(cleaned_df):,}")
    print(f"Columns in Cleaned Dataset: {len(cleaned_df.columns)}")
    print(f"Postings with Skills:       {int(cleaned_df['has_skills_specified'].sum())} ({cleaned_df['has_skills_specified'].mean():.1%})")
    print(f"Postings with Salary Info:  {int(cleaned_df['has_salary_data'].sum())} ({cleaned_df['has_salary_data'].mean():.1%})")
    print(f"Output File:                {DEFAULT_OUTPUT_FILE}")
    print(f"Validation Status:          SUCCESS")
    print("=" * 60)
