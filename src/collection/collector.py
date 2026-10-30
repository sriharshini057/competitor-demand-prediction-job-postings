"""Data Ingestion and Filtering Module.

Stage 1: Job posting ingestion, strict competitor filtering, and validation.
Filters raw job postings to the official single target company: Microsoft.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import logging
import pandas as pd

# Configure module logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Default file paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_RAW_FILE = PROJECT_ROOT / "data" / "raw" / "data_jobs.csv"
DEFAULT_PROCESSED_FILE = PROJECT_ROOT / "data" / "processed" / "microsoft_jobs.csv"
TARGET_COMPANY = "Microsoft"
EXPECTED_RECORD_COUNT = 498


def load_raw_dataset(file_path: Path = DEFAULT_RAW_FILE) -> pd.DataFrame:
    """Loads the raw job postings dataset from disk.

    Args:
        file_path: Path to the raw CSV file.

    Returns:
        pd.DataFrame containing the raw dataset.

    Raises:
        FileNotFoundError: If the raw data file does not exist.
    """
    if not file_path.exists():
        logger.error("Raw data file not found at: %s", file_path)
        raise FileNotFoundError(f"Raw data file not found at: {file_path}")

    logger.info("Loading raw dataset from: %s", file_path)
    df = pd.read_csv(file_path)
    logger.info("Raw dataset successfully loaded. Dimensions: %s rows, %s columns", f"{len(df):,}", len(df.columns))
    return df


def filter_target_company(
    df: pd.DataFrame,
    company_name: str = TARGET_COMPANY,
    case_insensitive: bool = False,
) -> pd.DataFrame:
    """Filters the dataset to the target company.

    Args:
        df: Input DataFrame of raw postings.
        company_name: Target company name string.
        case_insensitive: If True, matches company name case-insensitively.

    Returns:
        Filtered pd.DataFrame copy containing target company postings.
    """
    logger.info(
        "Filtering dataset for company match: company_name == '%s' (case_insensitive=%s)",
        company_name,
        case_insensitive,
    )
    if case_insensitive:
        mask = df["company_name"].astype(str).str.strip().str.lower() == company_name.strip().lower()
    else:
        mask = df["company_name"] == company_name
    filtered_df = df[mask].copy()
    logger.info("Filtered count: %d postings matched company_name == '%s'", len(filtered_df), company_name)
    return filtered_df


def validate_ingested_dataset(
    df: pd.DataFrame,
    expected_count: int = EXPECTED_RECORD_COUNT,
    expected_company: str = TARGET_COMPANY,
) -> Dict[str, Any]:
    """Validates data integrity and compliance requirements for the filtered dataset.

    Validation checks:
    1. Record count equals expected target count (498).
    2. Zero null values in job_title.
    3. Zero null values in job_posted_date.
    4. Zero null values in company_name.
    5. All company_name values strictly equal 'Microsoft'.

    Args:
        df: Filtered DataFrame to validate.
        expected_count: Expected record count.
        expected_company: Expected exact company name.

    Returns:
        Dictionary of validation results and metric checks.

    Raises:
        ValueError: If any critical validation check fails.
    """
    logger.info("Running validation checks on filtered dataset...")
    actual_count = len(df)
    null_titles = int(df["job_title"].isnull().sum())
    null_dates = int(df["job_posted_date"].isnull().sum())
    null_companies = int(df["company_name"].isnull().sum())
    non_matching_companies = int((df["company_name"] != expected_company).sum())

    results = {
        "actual_record_count": actual_count,
        "expected_record_count": expected_count,
        "count_matches": actual_count == expected_count,
        "null_job_titles": null_titles,
        "null_posting_dates": null_dates,
        "null_company_names": null_companies,
        "non_matching_company_records": non_matching_companies,
        "all_valid": (
            actual_count == expected_count
            and null_titles == 0
            and null_dates == 0
            and null_companies == 0
            and non_matching_companies == 0
        ),
    }

    if not results["count_matches"]:
        err_msg = f"Record count validation failed! Expected {expected_count}, got {actual_count}."
        logger.error(err_msg)
        raise ValueError(err_msg)

    if null_titles > 0 or null_dates > 0 or null_companies > 0:
        err_msg = f"Null value validation failed! Titles: {null_titles}, Dates: {null_dates}, Companies: {null_companies}."
        logger.error(err_msg)
        raise ValueError(err_msg)

    if non_matching_companies > 0:
        err_msg = f"Company identity validation failed! Found {non_matching_companies} non-matching company records."
        logger.error(err_msg)
        raise ValueError(err_msg)

    logger.info("All validation checks PASSED: %d records, 0 null critical fields, 100%% match for '%s'", actual_count, expected_company)
    return results


def save_processed_dataset(
    df: pd.DataFrame,
    output_path: Path = DEFAULT_PROCESSED_FILE,
) -> Path:
    """Saves the validated dataset to the processed data directory.

    Args:
        df: Validated DataFrame to save.
        output_path: Destination CSV file path.

    Returns:
        Path to the saved CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Saving processed dataset to: %s", output_path)
    df.to_csv(output_path, index=False)
    file_size_kb = output_path.stat().st_size / 1024
    logger.info("File successfully written (%0.2f KB, %d rows, %d columns)", file_size_kb, len(df), len(df.columns))
    return output_path


def ingest_microsoft_data(
    raw_path: Path = DEFAULT_RAW_FILE,
    output_path: Path = DEFAULT_PROCESSED_FILE,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Orchestrates the end-to-end ingestion and filtering pipeline.

    1. Loads the raw dataset from raw_path.
    2. Filters strictly by company_name == 'Microsoft'.
    3. Runs validation checks (count == 498, null checks, identity check).
    4. Saves the verified dataset to output_path.

    Args:
        raw_path: Path to the raw CSV file.
        output_path: Destination path for the processed CSV file.

    Returns:
        Tuple of (processed DataFrame, validation results dictionary).
    """
    logger.info("Starting Microsoft job postings ingestion pipeline...")
    raw_df = load_raw_dataset(raw_path)
    filtered_df = filter_target_company(raw_df, company_name=TARGET_COMPANY)
    validation_results = validate_ingested_dataset(filtered_df, expected_count=EXPECTED_RECORD_COUNT)
    save_processed_dataset(filtered_df, output_path=output_path)
    logger.info("Ingestion pipeline completed successfully.")
    return filtered_df, validation_results


if __name__ == "__main__":
    df_result, val_results = ingest_microsoft_data()
    print("\n" + "=" * 60)
    print("INGESTION EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Target Company: {TARGET_COMPANY}")
    print(f"Output File:    {DEFAULT_PROCESSED_FILE}")
    print(f"Final Rows:     {len(df_result):,}")
    print(f"Final Columns:  {len(df_result.columns)}")
    print(f"Validation:     {'PASSED' if val_results['all_valid'] else 'FAILED'}")
    print("=" * 60)
