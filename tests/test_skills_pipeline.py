"""Integration tests for Stage 4 NER and Skill Extraction Pipeline.

Tests cover:
- In-memory DataFrame feature building
- Preservation of all original Sprint 3 columns
- 0 null values in new Sprint 4 columns
- Handling null and empty job description fields
- JSON string serialization and deserialization compatibility
- Dataset row count preservation
- Microsoft-only dataset integrity
- Output CSV generation and re-readability with pandas
- Validation checks (empty dataframe, corrupt rows, non-Microsoft)
"""

import json
from pathlib import Path
import tempfile

import pandas as pd
import pytest

from src.skills.extractor import (
    build_skills_features,
    format_job_text,
    run_skills_pipeline,
    save_skills_dataset,
    validate_skills_output,
)
from src.skills.ner_extractor import NamedEntityExtractor
from src.skills.skill_extractor import SkillExtractor


@pytest.fixture(scope="module")
def shared_extractors():
    """Module-level fixture to initialize extractors once for all tests."""
    from src.skills.ner_extractor import load_spacy_model

    nlp = load_spacy_model()
    ner = NamedEntityExtractor(nlp=nlp)
    skill = SkillExtractor(nlp=nlp)
    return ner, skill


@pytest.fixture
def sample_pipeline_df():
    """Synthetic DataFrame mirroring Sprint 3 schema with varied job texts and edge cases."""
    return pd.DataFrame(
        {
            "job_title": [
                "Senior Software Engineer",
                "Data Scientist",
                "Azure Cloud Architect",
                "Operations Coordinator",
            ],
            "company_name": ["Microsoft", "Microsoft", "Microsoft", "Microsoft"],
            "job_location": ["Redmond, WA", "Dublin, Ireland", "Remote", "Seattle, WA"],
            "job_posted_date": ["2023-01-15", "2023-04-10", "2023-07-22", "2023-10-05"],
            "job_skills_list": [
                "['python', 'c#', 'azure']",
                "['r', 'python', 'scikit-learn']",
                "['azure', 'kubernetes', 'docker']",
                "[]",
            ],
            "job_skills_normalized": [
                "['python', 'c#', 'azure']",
                "['r', 'python', 'scikit-learn']",
                "['azure', 'kubernetes', 'docker']",
                "[]",
            ],
            # Simulate Sprint 3 features
            "job_title_tokens": [
                "['software', 'engineer']",
                "['data', 'scientist']",
                "['azure', 'cloud', 'architect']",
                "['operations', 'coordinator']",
            ],
        }
    )


@pytest.fixture
def sample_skills_output(sample_pipeline_df, shared_extractors):
    """Build a valid Sprint 4 output for validation tests."""
    ner, skill = shared_extractors
    return build_skills_features(
        sample_pipeline_df,
        ner_extractor=ner,
        skill_extractor=skill,
    )


class TestSkillsPipelineIntegration:
    """Integration test suite for the end-to-end extraction pipeline."""

    def test_build_skills_features_columns_added(self, sample_pipeline_df, shared_extractors):
        """Pipeline adds all five required output columns and preserves original columns."""
        ner, skill = shared_extractors
        orig_cols = sample_pipeline_df.columns.tolist()

        df_out = build_skills_features(
            sample_pipeline_df,
            ner_extractor=ner,
            skill_extractor=skill,
        )

        # All original columns preserved
        for col in orig_cols:
            assert col in df_out.columns

        # New columns present
        new_cols = [
            "extracted_entities",
            "extracted_skills",
            "skill_categories",
            "skill_count",
            "entity_count",
        ]
        for col in new_cols:
            assert col in df_out.columns

        assert len(df_out) == len(sample_pipeline_df)

    def test_zero_nulls_in_new_columns(self, sample_pipeline_df, shared_extractors):
        """None of the five new Sprint 4 columns contain null values."""
        ner, skill = shared_extractors
        df_out = build_skills_features(
            sample_pipeline_df,
            ner_extractor=ner,
            skill_extractor=skill,
        )

        for col in ["extracted_entities", "extracted_skills", "skill_categories", "skill_count", "entity_count"]:
            assert df_out[col].isnull().sum() == 0

    def test_structured_json_serialization(self, sample_pipeline_df, shared_extractors):
        """Serialized string columns parse back to valid Python lists and dicts via json.loads."""
        ner, skill = shared_extractors
        df_out = build_skills_features(
            sample_pipeline_df,
            ner_extractor=ner,
            skill_extractor=skill,
        )

        for _, row in df_out.iterrows():
            entities = json.loads(row["extracted_entities"])
            skills = json.loads(row["extracted_skills"])
            categories = json.loads(row["skill_categories"])

            assert isinstance(entities, list)
            assert isinstance(skills, list)
            assert isinstance(categories, dict)
            assert row["skill_count"] == len(skills)
            assert row["entity_count"] == len(entities)

    def test_handle_missing_and_empty_descriptions(self, shared_extractors):
        """DataFrame with null or empty job descriptions is processed without failure."""
        ner, skill = shared_extractors
        df_sparse = pd.DataFrame(
            {
                "company_name": ["Microsoft", "Microsoft"],
                "job_title": ["Data Analyst", ""],
                "job_description": [None, ""],
                "job_skills_list": [None, "[]"],
            }
        )

        df_out = build_skills_features(
            df_sparse,
            text_column="job_description",
            ner_extractor=ner,
            skill_extractor=skill,
        )

        assert len(df_out) == 2
        assert df_out["extracted_skills"].iloc[0] == "[]"
        assert df_out["skill_count"].iloc[0] == 0
        assert df_out["extracted_skills"].iloc[1] == "[]"
        assert df_out["skill_count"].iloc[1] == 0

    def test_format_job_text_priority(self):
        """format_job_text prioritizes explicit description column, falling back to composite."""
        row_with_desc = pd.Series(
            {
                "company_name": "Microsoft",
                "job_title": "Engineer",
                "job_description": "Custom job description text.",
            }
        )
        assert format_job_text(row_with_desc) == "Custom job description text."

        row_without_desc = pd.Series(
            {
                "company_name": "Microsoft",
                "job_title": "Data Scientist",
                "job_location": "Dublin",
                "job_skills_normalized": "['python', 'azure']",
            }
        )
        composite = format_job_text(row_without_desc)
        assert "Microsoft" in composite
        assert "Data Scientist" in composite
        assert "Dublin" in composite
        assert "python, azure" in composite

    def test_validate_skills_output_success(self, sample_pipeline_df, sample_skills_output):
        """validate_skills_output passes when constraints are met."""
        metrics = validate_skills_output(
            sample_skills_output,
            expected_row_count=len(sample_pipeline_df),
            expected_original_cols=sample_pipeline_df.columns.tolist(),
            expected_original_df=sample_pipeline_df,
        )

        assert metrics["total_records"] == 4
        assert metrics["total_columns"] == len(sample_skills_output.columns)
        assert metrics["non_microsoft_records"] == 0

    def test_validate_skills_output_detects_changed_original_value(
        self, sample_pipeline_df, sample_skills_output
    ):
        """Changed original Sprint 3 values report the column and row."""
        df_out = sample_skills_output.copy()
        df_out.loc[1, "job_title"] = "Changed title"

        with pytest.raises(
            ValueError,
            match=r"column 'job_title'.*row 2",
        ):
            validate_skills_output(df_out, expected_original_df=sample_pipeline_df)

    def test_validate_skills_output_detects_missing_original_column(
        self, sample_pipeline_df, sample_skills_output
    ):
        """Missing Sprint 3 columns are identified by name."""
        df_out = sample_skills_output.drop(columns=["job_location"])

        with pytest.raises(ValueError, match=r"Original column 'job_location' is missing"):
            validate_skills_output(df_out, expected_original_df=sample_pipeline_df)

    def test_validate_skills_output_detects_original_row_reordering(
        self, sample_pipeline_df, sample_skills_output
    ):
        """Original values must remain in their Sprint 3 row order."""
        df_out = sample_skills_output.iloc[::-1].reset_index(drop=True)

        with pytest.raises(ValueError, match=r"Original value changed.*row 1"):
            validate_skills_output(df_out, expected_original_df=sample_pipeline_df)

    def test_validate_skills_output_parses_json_after_row_five(
        self, sample_pipeline_df, shared_extractors
    ):
        """Malformed structured output beyond the fifth row is rejected."""
        ner, skill = shared_extractors
        original_df = pd.concat(
            [sample_pipeline_df, sample_pipeline_df.iloc[:3]],
            ignore_index=True,
        )
        df_out = build_skills_features(
            original_df,
            ner_extractor=ner,
            skill_extractor=skill,
        )
        df_out.loc[5, "extracted_skills"] = "["

        with pytest.raises(
            ValueError,
            match=r"column 'extracted_skills'.*row 6",
        ):
            validate_skills_output(df_out, expected_original_df=original_df)

    @pytest.mark.parametrize(
        ("column", "invalid_json"),
        [
            ("extracted_entities", json.dumps(["not an entity dictionary"])),
            ("extracted_skills", json.dumps([{"skill": "Python"}])),
            ("skill_categories", json.dumps({"Cloud": "Microsoft Azure"})),
        ],
    )
    def test_validate_skills_output_rejects_invalid_json_structure(
        self, sample_pipeline_df, sample_skills_output, column, invalid_json
    ):
        """Valid JSON with an invalid schema reports the affected cell."""
        df_out = sample_skills_output.copy()
        df_out.loc[2, column] = invalid_json

        with pytest.raises(
            ValueError,
            match=rf"column '{column}'.*row 3",
        ):
            validate_skills_output(df_out, expected_original_df=sample_pipeline_df)

    @pytest.mark.parametrize(
        ("column", "invalid_value"),
        [("skill_count", -1), ("entity_count", 1.5)],
    )
    def test_validate_skills_output_rejects_invalid_counts(
        self, sample_pipeline_df, sample_skills_output, column, invalid_value
    ):
        """Counts must be non-negative integers and identify their invalid cell."""
        df_out = sample_skills_output.copy()
        df_out[column] = df_out[column].astype(object)
        df_out.loc[1, column] = invalid_value

        with pytest.raises(
            ValueError,
            match=rf"column '{column}'.*row 2",
        ):
            validate_skills_output(df_out, expected_original_df=sample_pipeline_df)

    def test_validate_skills_output_empty_df_raises(self):
        """Empty DataFrame raises ValueError."""
        with pytest.raises(ValueError, match="Output DataFrame is empty"):
            validate_skills_output(pd.DataFrame())

    def test_validate_skills_output_row_count_mismatch_raises(self, sample_pipeline_df, shared_extractors):
        """Row count mismatch raises ValueError."""
        ner, skill = shared_extractors
        df_out = build_skills_features(sample_pipeline_df, ner_extractor=ner, skill_extractor=skill)
        with pytest.raises(ValueError, match="Expected 10 rows, but got 4"):
            validate_skills_output(df_out, expected_row_count=10)

    def test_validate_skills_output_non_microsoft_raises(self, sample_pipeline_df, shared_extractors):
        """Non-Microsoft record raises ValueError."""
        ner, skill = shared_extractors
        df_dirty = sample_pipeline_df.copy()
        df_dirty.loc[0, "company_name"] = "Google"

        df_out = build_skills_features(df_dirty, ner_extractor=ner, skill_extractor=skill)
        with pytest.raises(ValueError, match="non-Microsoft records detected"):
            validate_skills_output(df_out)

    def test_save_and_reload_csv(self, sample_pipeline_df, shared_extractors):
        """Persisted CSV can be reloaded using pandas without schema corruption."""
        ner, skill = shared_extractors
        df_out = build_skills_features(
            sample_pipeline_df,
            ner_extractor=ner,
            skill_extractor=skill,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            test_csv = Path(tmpdir) / "test_skills.csv"
            save_skills_dataset(df_out, output_path=test_csv)

            assert test_csv.exists()
            assert test_csv.stat().st_size > 0

            df_reloaded = pd.read_csv(test_csv)
            assert len(df_reloaded) == len(sample_pipeline_df)
            assert "extracted_skills" in df_reloaded.columns

            # Verify JSON parseability from reloaded CSV
            parsed_skills = json.loads(df_reloaded["extracted_skills"].iloc[0])
            assert isinstance(parsed_skills, list)
