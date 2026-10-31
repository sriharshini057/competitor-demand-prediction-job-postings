"""Stage 4 Pipeline Orchestrator: NER and Skill Extraction.

Extracts named entities (using spaCy NER) and technical skills (using deterministic
spaCy PhraseMatcher/Matcher) from Microsoft job postings, producing a structured
output artifact with category tagging and JSON serialization.

Input  : data/processed/microsoft_jobs_nlp.csv      (Sprint 3 output — read-only)
Output : data/processed/microsoft_jobs_skills.csv   (Sprint 4 artifact — additive columns only)

New columns added (all Sprint 3 columns are strictly preserved):
    extracted_entities : str — JSON-serialized List[Dict[str, str]] of named entities [{'text': ..., 'label': ...}]
    extracted_skills   : str — JSON-serialized List[str] of deduplicated, normalized canonical skills
    skill_categories   : str — JSON-serialized Dict[str, List[str]] mapping skill categories to skills
    skill_count        : int — Count of unique extracted skills
    entity_count       : int — Count of unique extracted named entities
"""

import ast
import json
import logging
from numbers import Integral
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.skills.ner_extractor import DEFAULT_SPACY_MODEL, NamedEntityExtractor, load_spacy_model
from src.skills.skill_extractor import SKILL_TAXONOMY, SkillExtractor

# ---------------------------------------------------------------------------
# Console encoding safety for Windows
# ---------------------------------------------------------------------------
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "microsoft_jobs_nlp.csv"
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "microsoft_jobs_skills.csv"


def format_job_text(row: pd.Series, text_column: Optional[str] = None) -> str:
    """Extracts or formats the text to be processed for entity and skill extraction.

    If an explicit `text_column` (or 'job_description' / 'description') exists
    in the row and is non-null, its text is returned directly.

    If no free-text description column exists (as in the primary Luke Barousse
    data_jobs dataset), a composite job posting representation is built from
    the structured fields: company name, job title, job location, and normalized skills.

    Args:
        row: A pandas Series representing a job posting.
        text_column: Optional name of the text column to prioritize.

    Returns:
        String containing the text for extraction.
    """
    if text_column and text_column in row and pd.notna(row[text_column]):
        return str(row[text_column])

    # Check common free-text description column names
    for col in ("job_description", "description", "job_summary"):
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            return str(row[col])

    # Composite formatting for structured postings
    company = str(row.get("company_name", "Microsoft")).strip()
    title = str(row.get("job_title", "")).strip()
    location = str(row.get("job_location", "")).strip()

    # Retrieve skills from normalized skills or skill lists if available
    skills_text = ""
    for skill_col in ("job_skills_normalized", "job_skills_list", "job_skills_parsed", "job_skills"):
        if skill_col in row and pd.notna(row[skill_col]):
            val = row[skill_col]
            if isinstance(val, str):
                val_str = val.strip()
                if val_str.startswith("[") and val_str.endswith("]"):
                    try:
                        parsed = ast.literal_eval(val_str)
                        if isinstance(parsed, list):
                            skills_text = ", ".join(str(s) for s in parsed)
                            break
                    except Exception:
                        pass
                else:
                    skills_text = val_str
                    break
            elif isinstance(val, (list, set, tuple)):
                skills_text = ", ".join(str(s) for s in val)
                break

    parts = []
    if company:
        parts.append(f"Company: {company}.")
    if title:
        parts.append(f"Job Title: {title}.")
    if location:
        parts.append(f"Location: {location}.")
    if skills_text:
        parts.append(f"Required Skills and Technologies: {skills_text}.")

    return " ".join(parts).strip()


def build_skills_features(
    df: pd.DataFrame,
    text_column: Optional[str] = None,
    nlp_model_name: str = DEFAULT_SPACY_MODEL,
    ner_extractor: Optional[NamedEntityExtractor] = None,
    skill_extractor: Optional[SkillExtractor] = None,
) -> pd.DataFrame:
    """Applies NER and skill extraction across all rows of the input DataFrame.

    Adds five new columns without modifying or dropping any existing column:
        extracted_entities : str (JSON List[Dict[str, str]])
        extracted_skills   : str (JSON List[str])
        skill_categories   : str (JSON Dict[str, List[str]])
        skill_count        : int
        entity_count       : int

    Args:
        df: Input DataFrame (e.g. Sprint 3 microsoft_jobs_nlp.csv).
        text_column: Optional column to read text from. If None, uses format_job_text.
        nlp_model_name: spaCy model name to load if extractors are not passed.
        ner_extractor: Optional pre-initialized NamedEntityExtractor.
        skill_extractor: Optional pre-initialized SkillExtractor.

    Returns:
        A copy of df with the five new columns appended.
    """
    df_out = df.copy()

    # Share spaCy NLP instance between extractors for efficiency
    if ner_extractor is None or skill_extractor is None:
        nlp = load_spacy_model(nlp_model_name)
        if ner_extractor is None:
            ner_extractor = NamedEntityExtractor(nlp=nlp)
        if skill_extractor is None:
            skill_extractor = SkillExtractor(nlp=nlp)

    logger.info("Extracting named entities and skills for %d records ...", len(df_out))

    extracted_entities_list: List[str] = []
    extracted_skills_list: List[str] = []
    skill_categories_list: List[str] = []
    skill_counts: List[int] = []
    entity_counts: List[int] = []

    for _, row in df_out.iterrows():
        text = format_job_text(row, text_column=text_column)

        # 1. Named Entity Recognition
        entities = ner_extractor.extract_entities(text)
        entity_cnt = len(entities)

        # 2. Skill Extraction
        skill_res = skill_extractor.extract_skills(text)
        skills = skill_res["skills"]
        categories = skill_res["categories"]
        skill_cnt = skill_res["skill_count"]

        # Serialize structured objects as valid JSON strings
        extracted_entities_list.append(json.dumps(entities, ensure_ascii=False))
        extracted_skills_list.append(json.dumps(skills, ensure_ascii=False))
        skill_categories_list.append(json.dumps(categories, ensure_ascii=False))
        skill_counts.append(skill_cnt)
        entity_counts.append(entity_cnt)

    df_out["extracted_entities"] = extracted_entities_list
    df_out["extracted_skills"] = extracted_skills_list
    df_out["skill_categories"] = skill_categories_list
    df_out["skill_count"] = skill_counts
    df_out["entity_count"] = entity_counts

    logger.info(
        "Feature engineering complete. Added 5 columns: "
        "extracted_entities, extracted_skills, skill_categories, skill_count, entity_count."
    )
    return df_out


def validate_skills_output(
    df: pd.DataFrame,
    expected_row_count: Optional[int] = None,
    expected_original_cols: Optional[List[str]] = None,
    expected_original_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Validates the Sprint 4 output DataFrame prior to saving.

    Checks:
    1. Output is non-empty.
    2. Row count matches expected baseline (e.g. 498 records).
    3. All 5 new Sprint 4 columns are present.
    4. 0 null values in any new column.
    5. All original columns are present and their row values are unchanged.
    6. 100% Microsoft postings.
    7. Every structured JSON value is parseable and has the expected type.
    8. Skill and entity counts are non-negative integers.

    Args:
        df: Enriched DataFrame.
        expected_row_count: Expected record count (default: 498 if len(df) == 498).
        expected_original_cols: List of original column names that must be present.
        expected_original_df: Sprint 3 DataFrame used to verify original values
            and row order.

    Returns:
        Dictionary of validation metrics.

    Raises:
        ValueError: If any validation check fails.
    """
    logger.info("Validating Sprint 4 enriched dataset ...")

    if len(df) == 0:
        raise ValueError("Validation failed: Output DataFrame is empty.")

    if expected_row_count is not None and len(df) != expected_row_count:
        raise ValueError(
            f"Validation failed: Expected {expected_row_count} rows, but got {len(df)}."
        )

    new_cols = [
        "extracted_entities",
        "extracted_skills",
        "skill_categories",
        "skill_count",
        "entity_count",
    ]
    for col in new_cols:
        if col not in df.columns:
            raise ValueError(f"Validation failed: Missing new column '{col}'.")

    # Check for nulls in new columns, reporting the first affected cell.
    null_counts = {col: int(df[col].isnull().sum()) for col in new_cols}
    for col in new_cols:
        null_rows = df[col].isnull().to_numpy().nonzero()[0]
        if len(null_rows):
            raise ValueError(
                f"Validation failed: Null value in column '{col}' at row "
                f"{int(null_rows[0]) + 1}."
            )

    original_cols = expected_original_cols
    if original_cols is None and expected_original_df is not None:
        original_cols = expected_original_df.columns.tolist()

    # Check that all original columns are present.
    if original_cols is not None:
        missing_orig = set(original_cols) - set(df.columns)
        if missing_orig:
            missing_col = sorted(missing_orig)[0]
            raise ValueError(
                f"Validation failed: Original column '{missing_col}' is missing."
            )

    # Compare values positionally so the Sprint 3 row order must be preserved.
    if expected_original_df is not None:
        if len(expected_original_df) != len(df):
            raise ValueError(
                "Validation failed: Original input has "
                f"{len(expected_original_df)} rows, but output has {len(df)}."
            )
        for col in expected_original_df.columns:
            expected_values = expected_original_df[col].reset_index(drop=True)
            actual_values = df[col].reset_index(drop=True)
            matching = actual_values.eq(expected_values).fillna(False) | (
                actual_values.isna() & expected_values.isna()
            )
            mismatch_rows = (~matching).to_numpy().nonzero()[0]
            if len(mismatch_rows):
                raise ValueError(
                    f"Validation failed: Original value changed in column '{col}' "
                    f"at row {int(mismatch_rows[0]) + 1}."
                )

    # Verify company is 100% Microsoft if company_name column exists
    if "company_name" in df.columns:
        non_microsoft_rows = (
            df["company_name"].ne("Microsoft").fillna(True).to_numpy().nonzero()[0]
        )
        non_microsoft = len(non_microsoft_rows)
        if non_microsoft:
            raise ValueError(
                "Validation failed: non-Microsoft records detected in column "
                f"'company_name' at row {int(non_microsoft_rows[0]) + 1} "
                f"(total: {non_microsoft})."
            )
    else:
        non_microsoft = 0

    json_structures = {
        "extracted_entities": lambda value: isinstance(value, list)
        and all(isinstance(entity, dict) for entity in value),
        "extracted_skills": lambda value: isinstance(value, list)
        and all(isinstance(skill, str) for skill in value),
        "skill_categories": lambda value: isinstance(value, dict)
        and all(
            isinstance(category, str)
            and isinstance(skills, list)
            and all(isinstance(skill, str) for skill in skills)
            for category, skills in value.items()
        ),
    }
    for col, has_expected_structure in json_structures.items():
        for row_number, serialized_value in enumerate(df[col]):
            try:
                parsed_value = json.loads(serialized_value)
            except (TypeError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"Validation failed: Invalid JSON in column '{col}' at row "
                    f"{row_number + 1}: {exc}"
                ) from exc
            if not has_expected_structure(parsed_value):
                raise ValueError(
                    f"Validation failed: Invalid data structure in column '{col}' "
                    f"at row {row_number + 1}."
                )

    for col in ("skill_count", "entity_count"):
        for row_number, value in enumerate(df[col]):
            if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
                raise ValueError(
                    f"Validation failed: column '{col}' must contain non-negative "
                    f"integers; invalid value at row {row_number + 1}: {value!r}."
                )

    metrics = {
        "total_records": len(df),
        "total_columns": len(df.columns),
        "new_columns_added": new_cols,
        "null_counts": null_counts,
        "non_microsoft_records": non_microsoft,
        "total_skills_extracted": int(df["skill_count"].sum()),
        "avg_skills_per_posting": round(float(df["skill_count"].mean()), 2),
        "total_entities_extracted": int(df["entity_count"].sum()),
        "avg_entities_per_posting": round(float(df["entity_count"].mean()), 2),
    }

    logger.info(
        "Sprint 4 validation PASSED: %d records, %d columns, 0 nulls.",
        len(df),
        len(df.columns),
    )
    return metrics


def save_skills_dataset(df: pd.DataFrame, output_path: Path = DEFAULT_OUTPUT_FILE) -> Path:
    """Saves the Sprint 4 enriched DataFrame to a CSV file.

    Args:
        df: Enriched DataFrame to persist.
        output_path: Destination file path.

    Returns:
        Path of the persisted CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    file_size_kb = output_path.stat().st_size / 1024
    logger.info(
        "Sprint 4 dataset saved: %s (%.2f KB, %d records, %d columns)",
        output_path,
        file_size_kb,
        len(df),
        len(df.columns),
    )
    return output_path


def run_skills_pipeline(
    input_path: Path = DEFAULT_INPUT_FILE,
    output_path: Path = DEFAULT_OUTPUT_FILE,
    text_column: Optional[str] = None,
    nlp_model_name: str = DEFAULT_SPACY_MODEL,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Runs the end-to-end Sprint 4 NER and Skill Extraction pipeline.

    Steps:
    1. Load Sprint 3 NLP dataset.
    2. Extract entities and skills via :func:`build_skills_features`.
    3. Validate enriched DataFrame via :func:`validate_skills_output`.
    4. Save to CSV via :func:`save_skills_dataset`.

    Args:
        input_path: Path to input CSV (default: data/processed/microsoft_jobs_nlp.csv).
        output_path: Path to output CSV (default: data/processed/microsoft_jobs_skills.csv).
        text_column: Optional column to read text from.
        nlp_model_name: spaCy model name.

    Returns:
        Tuple of (enriched DataFrame, validation metrics dictionary).

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If validation fails.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info("Starting Stage 4 NER and Skill Extraction pipeline ...")
    logger.info("Input : %s", input_path)
    logger.info("Output: %s", output_path)

    df_in = pd.read_csv(input_path)
    original_cols = df_in.columns.tolist()
    expected_rows = len(df_in)
    logger.info("Loaded %d rows x %d columns from Sprint 3 artifact.", expected_rows, len(original_cols))

    df_out = build_skills_features(
        df_in,
        text_column=text_column,
        nlp_model_name=nlp_model_name,
    )

    metrics = validate_skills_output(
        df_out,
        expected_row_count=expected_rows,
        expected_original_cols=original_cols,
        expected_original_df=df_in,
    )

    save_skills_dataset(df_out, output_path=output_path)
    logger.info("Stage 4 pipeline completed successfully.")
    return df_out, metrics


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for running the Sprint 4 pipeline.

    Args:
        argv: Optional list of command-line arguments. Defaults to sys.argv[1:].

    Returns:
        0 on success; 1 on failure.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Stage 4: NER and Skill Extraction Pipeline")
    parser.add_argument(
        "--input-file",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help="Path to input CSV (default: data/processed/microsoft_jobs_nlp.csv)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to output CSV (default: data/processed/microsoft_jobs_skills.csv)",
    )
    parser.add_argument(
        "--text-column",
        type=str,
        default=None,
        help="Optional name of the text column to extract from",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=DEFAULT_SPACY_MODEL,
        help="spaCy language model to load (default: en_core_web_sm)",
    )
    parsed_args = parser.parse_args(argv)

    try:
        df_result, metrics = run_skills_pipeline(
            input_path=parsed_args.input_file,
            output_path=parsed_args.output_file,
            text_column=parsed_args.text_column,
            nlp_model_name=parsed_args.model_name,
        )

        print("\n" + "=" * 65)
        print("STAGE 4: NER & SKILL EXTRACTION EXECUTION SUMMARY")
        print("=" * 65)
        print(f"Total Postings Processed     : {metrics['total_records']:,}")
        print(f"Total Columns (incl. 5 new)  : {metrics['total_columns']}")
        print(f"New Columns Added            : {', '.join(metrics['new_columns_added'])}")
        print(f"Total Skills Extracted       : {metrics['total_skills_extracted']:,}")
        print(f"Average Skills per Posting   : {metrics['avg_skills_per_posting']}")
        print(f"Total Entities Extracted     : {metrics['total_entities_extracted']:,}")
        print(f"Average Entities per Posting : {metrics['avg_entities_per_posting']}")
        print(f"Non-Microsoft Records        : {metrics['non_microsoft_records']}")
        print(f"Output File                  : {parsed_args.output_file}")
        print(f"Validation Status            : SUCCESS")
        print("=" * 65)
        return 0
    except Exception as exc:
        logger.error("Stage 4 pipeline failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
