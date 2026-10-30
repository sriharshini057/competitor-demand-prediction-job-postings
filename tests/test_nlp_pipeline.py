"""Unit tests for Stage 3 NLP Preprocessing Pipeline.

All tests use synthetic in-memory fixtures — no disk I/O, no network calls.
Tests cover every public function in src/preprocessing/nlp_pipeline.py and
verify that Sprint 2 columns are never modified.
"""

import ast

import pandas as pd
import pytest

from src.preprocessing.nlp_pipeline import (
    CANONICAL_SKILL_ALIASES,
    DOMAIN_STOPWORDS,
    build_nlp_features,
    deserialize_skill_list,
    lemmatize_tokens,
    normalize_skills_list,
    normalize_skill_token,
    normalize_text,
    preprocess_job_title,
    remove_stopwords,
    tokenize,
    validate_nlp_output,
)


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_nlp_df():
    """Small synthetic DataFrame that mirrors the Sprint 2 cleaned schema.

    Includes edge cases:
    - A null ``job_skills_parsed`` row (row 2)
    - A malformed ``job_skills_parsed`` row (row 3)
    - Varied job titles including senior/junior prefixes and Roman numerals
    """
    return pd.DataFrame(
        {
            # Sprint 2 primary identifiers (must remain untouched after NLP)
            "job_title": [
                "Senior Software Engineers II",
                "Data Scientist",
                "Senior Data Engineer",
                "Machine Learning Engineer",
            ],
            "job_posted_date": [
                "2023-01-10",
                "2023-06-15",
                "2023-09-01",
                "2023-11-20",
            ],
            "company_name": ["Microsoft", "Microsoft", "Microsoft", "Microsoft"],
            # Sprint 2 skills column (serialized list strings)
            "job_skills_parsed": [
                "['python', 'azure', 'sql']",
                "['r', 'python', 'power bi']",
                None,                           # null → deserialize to []
                "NOT_A_VALID_LIST",             # malformed → deserialize to []
            ],
            # Minimal additional Sprint 2 columns for completeness
            "job_title_short": [
                "Software Engineer",
                "Data Scientist",
                "Senior Data Engineer",
                "Machine Learning Engineer",
            ],
            "posted_year": [2023, 2023, 2023, 2023],
            "job_skills_count": [3, 3, 0, 0],
            "has_skills_specified": [True, True, False, False],
        }
    )


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------

class TestNormalizeText:
    """Tests for normalize_text()."""

    def test_lowercases_input(self):
        """Verifies that uppercase characters are lowercased."""
        result = normalize_text("SENIOR SOFTWARE ENGINEER")
        assert result == result.lower()

    def test_strips_surrounding_whitespace(self):
        """Verifies leading and trailing whitespace is removed."""
        result = normalize_text("  Data Scientist  ")
        assert result == result.strip()
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_removes_parentheses_and_punctuation(self):
        """Verifies parentheses and common punctuation are stripped."""
        result = normalize_text("Software Engineer (II)")
        assert "(" not in result
        assert ")" not in result

    def test_preserves_hyphens(self):
        """Verifies hyphens are preserved (e.g. full-stack, year-over-year)."""
        result = normalize_text("Full-Stack Developer")
        assert "-" in result

    def test_collapses_extra_whitespace(self):
        """Verifies multiple spaces are collapsed to a single space."""
        result = normalize_text("data   scientist")
        assert "  " not in result

    def test_null_input_returns_empty_string(self):
        """Verifies NaN and None inputs return an empty string."""
        assert normalize_text(None) == ""
        assert normalize_text(float("nan")) == ""

    def test_empty_string_input(self):
        """Verifies empty string input returns empty string."""
        assert normalize_text("") == ""


# ---------------------------------------------------------------------------
# tokenize
# ---------------------------------------------------------------------------

class TestTokenize:
    """Tests for tokenize()."""

    def test_splits_on_whitespace(self):
        """Verifies text is split into correct word tokens."""
        result = tokenize("senior software engineer")
        assert result == ["senior", "software", "engineer"]

    def test_empty_string_returns_empty_list(self):
        """Verifies empty input returns an empty list."""
        assert tokenize("") == []

    def test_single_word(self):
        """Verifies a single-word string returns a one-element list."""
        assert tokenize("python") == ["python"]

    def test_no_empty_tokens_produced(self):
        """Verifies no empty strings appear in the returned token list."""
        result = tokenize("  data   scientist  ")
        assert all(len(tok) > 0 for tok in result)

    def test_filters_standalone_punctuation(self):
        """Verifies standalone punctuation tokens (-, /, etc.) are filtered out."""
        assert tokenize("-") == []
        assert tokenize(" / ") == []
        assert tokenize("--") == []
        result = tokenize("full-stack c# c++ -")
        assert result == ["full-stack", "c#", "c++"]

    def test_trims_boundary_punctuation(self):
        """Verifies boundary punctuation is trimmed while preserving internal symbols."""
        result = tokenize("-webxt engineer-")
        assert result == ["webxt", "engineer"]


# ---------------------------------------------------------------------------
# remove_stopwords
# ---------------------------------------------------------------------------

class TestRemoveStopwords:
    """Tests for remove_stopwords()."""

    def test_filters_common_english_stopwords(self):
        """Verifies common stop-words ('at', 'the', 'in') are removed."""
        tokens = ["engineer", "at", "the", "company", "in", "seattle"]
        result = remove_stopwords(tokens)
        assert "at" not in result
        assert "the" not in result
        assert "in" not in result
        assert "engineer" in result

    def test_extra_stopwords_are_excluded(self):
        """Verifies custom extra stop-words are also filtered out."""
        tokens = ["software", "engineer", "acme", "corp"]
        result = remove_stopwords(tokens, extra_stopwords={"acme", "corp"})
        assert "acme" not in result
        assert "corp" not in result
        assert "software" in result

    def test_empty_token_list_returns_empty(self):
        """Verifies empty input returns empty list."""
        assert remove_stopwords([]) == []

    def test_content_words_are_preserved(self):
        """Verifies that meaningful content words survive filtering."""
        tokens = ["python", "azure", "sql", "spark"]
        result = remove_stopwords(tokens)
        assert set(result) == {"python", "azure", "sql", "spark"}


# ---------------------------------------------------------------------------
# lemmatize_tokens
# ---------------------------------------------------------------------------

class TestLemmatizeTokens:
    """Tests for lemmatize_tokens()."""

    def test_plurals_reduced_to_singular(self):
        """Verifies plural nouns are lemmatized to singular form."""
        result = lemmatize_tokens(["engineers", "scientists"])
        assert "engineer" in result
        assert "scientist" in result

    def test_empty_list_returns_empty(self):
        """Verifies empty input returns empty list."""
        assert lemmatize_tokens([]) == []

    def test_already_base_form_unchanged(self):
        """Verifies tokens already in base form are returned unchanged."""
        result = lemmatize_tokens(["python", "azure"])
        assert "python" in result
        assert "azure" in result

    def test_output_length_matches_input(self):
        """Verifies output list length equals input list length."""
        tokens = ["data", "scientists", "engineers"]
        result = lemmatize_tokens(tokens)
        assert len(result) == len(tokens)


# ---------------------------------------------------------------------------
# preprocess_job_title (pipeline composition)
# ---------------------------------------------------------------------------

class TestPreprocessJobTitle:
    """Tests for preprocess_job_title() — full pipeline composition."""

    def test_senior_prefix_removed(self):
        """Verifies 'senior' is removed via DOMAIN_STOPWORDS."""
        result = preprocess_job_title("Senior Software Engineer")
        assert "senior" not in result

    def test_roman_numeral_ii_removed(self):
        """Verifies 'ii' (Roman numeral) is removed via DOMAIN_STOPWORDS."""
        result = preprocess_job_title("Software Engineer II")
        assert "ii" not in result

    def test_content_tokens_preserved(self):
        """Verifies meaningful role tokens survive the full pipeline."""
        result = preprocess_job_title("Data Scientist")
        assert "data" in result
        assert "scientist" in result

    def test_plural_lemmatized(self):
        """Verifies plural role words are lemmatized to singular."""
        result = preprocess_job_title("Software Engineers")
        assert "engineer" in result

    def test_null_input_returns_empty_list(self):
        """Verifies None and NaN inputs return an empty list."""
        assert preprocess_job_title(None) == []
        assert preprocess_job_title(float("nan")) == []

    def test_extra_stopwords_applied(self):
        """Verifies caller-supplied extra stop-words are excluded."""
        result = preprocess_job_title("Cloud Architect Intern", extra_stopwords={"intern"})
        assert "intern" not in result
        assert "cloud" in result

    def test_returns_list_type(self):
        """Verifies return type is always a list."""
        assert isinstance(preprocess_job_title("Data Engineer"), list)

    def test_title_with_hyphens_preserves_compound_terms(self):
        """Verifies hyphenated compound words survive while standalone dashes are removed."""
        result = preprocess_job_title("Senior Full-Stack Developer - Azure Cloud")
        assert "full-stack" in result
        assert "-" not in result
        assert "developer" in result
        assert "azure" in result
        assert "cloud" in result

    def test_title_with_numbers_filters_seniority_levels(self):
        """Verifies numeric-only seniority levels (1, 2, etc.) are excluded."""
        result = preprocess_job_title("Software Engineer 2")
        assert "2" not in result
        assert result == ["software", "engineer"]

    def test_title_with_numbers_preserves_technical_acronyms(self):
        """Verifies alphanumeric technical terms (e.g. M365) retain their digits."""
        result = preprocess_job_title("Senior Software Engineer - M365 Platform")
        assert "m365" in result
        assert "platform" in result
        assert "software" in result
        assert "engineer" in result

    def test_title_with_numbers_preserves_meaningful_studio_names(self):
        """Verifies non-level numbers in proper names (e.g. Turn 10) are retained."""
        result = preprocess_job_title("Senior Data Engineer - Turn 10 Studios")
        assert "10" in result
        assert "turn" in result
        assert "studio" in result

    def test_title_containing_csharp(self):
        """Verifies C# in a job title does not become 'c' and retains '#'. """
        result = preprocess_job_title("Senior Software Engineer (C# or Python)")
        assert "c#" in result
        assert "c" not in result
        assert "python" in result
        assert "software" in result
        assert "engineer" in result

    def test_title_containing_cplusplus(self):
        """Verifies C++ in a job title retains its plus signs and does not become 'c'."""
        result = preprocess_job_title("C++ Systems Software Engineer")
        assert "c++" in result
        assert "c" not in result
        assert "system" in result
        assert "software" in result
        assert "engineer" in result

    def test_title_containing_sql_and_python(self):
        """Verifies SQL and Python are preserved and standalone symbols (&, -) filtered."""
        result = preprocess_job_title("Data Engineer - Python & SQL")
        assert "python" in result
        assert "sql" in result
        assert "data" in result
        assert "engineer" in result
        assert "&" not in result
        assert "-" not in result

    def test_title_containing_unicode_fullwidth_characters(self):
        """Verifies fullwidth punctuation and non-ASCII dashes do not corrupt tokens."""
        result = preprocess_job_title("Support Engineer（Data & AI - SQL VM+MI）")
        assert "support" in result
        assert "engineer" in result
        assert "data" in result
        assert "ai" in result
        assert "sql" in result
        assert "vm+mi" in result
        assert "（" not in str(result)
        assert "）" not in str(result)


# ---------------------------------------------------------------------------
# deserialize_skill_list
# ---------------------------------------------------------------------------

class TestDeserializeSkillList:
    """Tests for deserialize_skill_list()."""

    def test_valid_serialized_list_parsed_correctly(self):
        """Verifies a Sprint 2-style serialized list string is correctly parsed."""
        result = deserialize_skill_list("['python', 'azure', 'sql']")
        assert result == ["python", "azure", "sql"]

    def test_null_input_returns_empty_list(self):
        """Verifies NaN returns an empty list."""
        assert deserialize_skill_list(float("nan")) == []

    def test_none_input_returns_empty_list(self):
        """Verifies None returns an empty list."""
        assert deserialize_skill_list(None) == []

    def test_empty_string_returns_empty_list(self):
        """Verifies empty string returns an empty list."""
        assert deserialize_skill_list("") == []

    def test_explicit_empty_list_string_returns_empty_list(self):
        """Verifies literal '[]' string returns an empty list."""
        assert deserialize_skill_list("[]") == []

    def test_malformed_string_returns_empty_list(self):
        """Verifies unparseable strings return an empty list without raising."""
        assert deserialize_skill_list("NOT_A_VALID_LIST") == []

    def test_return_type_is_list(self):
        """Verifies return type is always a Python list."""
        assert isinstance(deserialize_skill_list("['python']"), list)


# ---------------------------------------------------------------------------
# normalize_skill_token
# ---------------------------------------------------------------------------

class TestNormalizeSkillToken:
    """Tests for normalize_skill_token()."""

    def test_lowercases_skill(self):
        """Verifies skill tokens are lowercased."""
        assert normalize_skill_token("Azure") == "azure"

    def test_strips_whitespace(self):
        """Verifies surrounding whitespace is stripped."""
        assert normalize_skill_token("  power bi  ") == "power bi"

    def test_preserves_plus_signs(self):
        """Verifies '+' is retained (e.g. 'c++')."""
        result = normalize_skill_token("C++")
        assert "+" in result

    def test_preserves_dots(self):
        """Verifies dots are retained (e.g. 'node.js')."""
        result = normalize_skill_token("Node.js")
        assert "." in result

    def test_preserves_hyphens(self):
        """Verifies hyphens are retained (e.g. multi-word skill names)."""
        result = normalize_skill_token("real-time")
        assert "-" in result

    def test_empty_string_returns_empty(self):
        """Verifies empty string input returns empty string."""
        assert normalize_skill_token("") == ""

    def test_multi_word_skill_normalized(self):
        """Verifies multi-word skills with extra spaces are collapsed."""
        result = normalize_skill_token("  Power   BI  ")
        assert "  " not in result

    def test_csharp_regression_preserves_hash_sign(self):
        """Regression test: Proves C# retains '#' and does NOT become 'c'."""
        assert normalize_skill_token("C#") == "c#"
        assert normalize_skill_token("c#") == "c#"
        assert normalize_skill_token("  C#  ") == "c#"
        assert normalize_skill_token("C#") != "c"

    def test_cplusplus_regression_preserves_plus_signs(self):
        """Regression test: Proves C++ retains '++' and does NOT become 'c'."""
        assert normalize_skill_token("C++") == "c++"
        assert normalize_skill_token("c++") == "c++"
        assert normalize_skill_token("  C++  ") == "c++"
        assert normalize_skill_token("C++") != "c"

    def test_distinct_c_family_languages(self):
        """Verifies C, C#, and C++ normalize to three distinct, non-overlapping tokens."""
        c = normalize_skill_token("C")
        csharp = normalize_skill_token("C#")
        cpp = normalize_skill_token("C++")
        assert c == "c"
        assert csharp == "c#"
        assert cpp == "c++"
        assert len({c, csharp, cpp}) == 3

    def test_canonical_alias_mappings(self):
        """Verifies documented canonical alias mappings normalize to standard forms."""
        assert normalize_skill_token("golang") == "go"
        assert normalize_skill_token("mongo") == "mongodb"
        assert normalize_skill_token("postgres") == "postgresql"
        assert normalize_skill_token("k8s") == "kubernetes"
        assert normalize_skill_token("csharp") == "c#"
        assert normalize_skill_token("c sharp") == "c#"
        assert normalize_skill_token("cpp") == "c++"
        assert normalize_skill_token("sklearn") == "scikit-learn"
        assert normalize_skill_token("nodejs") == "node.js"
        assert normalize_skill_token("reactjs") == "react"


# ---------------------------------------------------------------------------
# normalize_skills_list (job-level deduplication)
# ---------------------------------------------------------------------------

class TestNormalizeSkillsList:
    """Tests for normalize_skills_list() — order preservation and deduplication."""

    def test_deduplicates_identical_skills_preserving_order(self):
        """Verifies duplicate skill names are removed while keeping original order."""
        result = normalize_skills_list(["python", "azure", "python"])
        assert result == ["python", "azure"]

    def test_deduplicates_aliases_within_job(self):
        """Verifies canonical aliases that resolve to the same name are deduplicated."""
        result = normalize_skills_list(["go", "golang"])
        assert result == ["go"]

    def test_preserves_distinct_c_and_csharp(self):
        """Verifies C, C#, and C++ all survive together without colliding."""
        result = normalize_skills_list(["c", "c#", "c++", "c#"])
        assert result == ["c", "c#", "c++"]

    def test_empty_input_returns_empty_list(self):
        """Verifies empty or None list returns an empty list."""
        assert normalize_skills_list([]) == []
        assert normalize_skills_list(None) == []

    def test_case_insensitive_deduplication(self):
        """Verifies case variations of the same skill collapse to a single token."""
        result = normalize_skills_list(["Azure", "azure", "AZURE"])
        assert result == ["azure"]


# ---------------------------------------------------------------------------
# build_nlp_features
# ---------------------------------------------------------------------------

class TestBuildNlpFeatures:
    """Tests for build_nlp_features() — DataFrame-level feature builder."""

    def test_adds_job_title_tokens_column(self, sample_nlp_df):
        """Verifies 'job_title_tokens' column is created."""
        result = build_nlp_features(sample_nlp_df)
        assert "job_title_tokens" in result.columns

    def test_adds_job_skills_list_column(self, sample_nlp_df):
        """Verifies 'job_skills_list' column is created."""
        result = build_nlp_features(sample_nlp_df)
        assert "job_skills_list" in result.columns

    def test_adds_job_skills_normalized_column(self, sample_nlp_df):
        """Verifies 'job_skills_normalized' column is created."""
        result = build_nlp_features(sample_nlp_df)
        assert "job_skills_normalized" in result.columns

    def test_no_null_values_in_new_columns(self, sample_nlp_df):
        """Verifies none of the three new NLP columns contain null values."""
        result = build_nlp_features(sample_nlp_df)
        assert result["job_title_tokens"].isnull().sum() == 0
        assert result["job_skills_list"].isnull().sum() == 0
        assert result["job_skills_normalized"].isnull().sum() == 0

    def test_sprint2_columns_not_modified(self, sample_nlp_df):
        """Verifies Sprint 2 columns are identical before and after NLP processing."""
        original_titles = sample_nlp_df["job_title"].tolist()
        original_dates = sample_nlp_df["job_posted_date"].tolist()
        original_companies = sample_nlp_df["company_name"].tolist()
        original_skills_count = sample_nlp_df["job_skills_count"].tolist()

        result = build_nlp_features(sample_nlp_df)

        assert result["job_title"].tolist() == original_titles
        assert result["job_posted_date"].tolist() == original_dates
        assert result["company_name"].tolist() == original_companies
        assert result["job_skills_count"].tolist() == original_skills_count

    def test_row_count_unchanged(self, sample_nlp_df):
        """Verifies the number of rows is unchanged after NLP processing."""
        result = build_nlp_features(sample_nlp_df)
        assert len(result) == len(sample_nlp_df)

    def test_null_skills_produce_empty_list_representation(self, sample_nlp_df):
        """Verifies that rows with null job_skills_parsed produce '[]' in new columns."""
        result = build_nlp_features(sample_nlp_df)
        # Row index 2 has None in job_skills_parsed
        assert result.loc[2, "job_skills_list"] == str([])

    def test_missing_required_column_raises_key_error(self):
        """Verifies KeyError is raised when required columns are absent."""
        bad_df = pd.DataFrame({"job_title": ["Engineer"]})
        with pytest.raises(KeyError, match="job_skills_parsed"):
            build_nlp_features(bad_df)

    def test_token_column_is_deserializable(self, sample_nlp_df):
        """Verifies 'job_title_tokens' strings can be parsed back to lists."""
        result = build_nlp_features(sample_nlp_df)
        for val in result["job_title_tokens"]:
            parsed = ast.literal_eval(val)
            assert isinstance(parsed, list)

    def test_skills_list_column_is_deserializable(self, sample_nlp_df):
        """Verifies 'job_skills_list' strings can be parsed back to lists."""
        result = build_nlp_features(sample_nlp_df)
        for val in result["job_skills_list"]:
            parsed = ast.literal_eval(val)
            assert isinstance(parsed, list)

    def test_job_skills_normalized_has_no_duplicates_within_job(self):
        """Verifies that job_skills_normalized never contains duplicate skills in any row."""
        df_dupes = pd.DataFrame(
            {
                "job_title": ["Senior C# Developer", "Cloud Engineer"],
                "job_posted_date": ["2023-01-01", "2023-01-02"],
                "company_name": ["Microsoft", "Microsoft"],
                "job_skills_parsed": [
                    "['c#', 'c#', 'python', 'python', 'c']",
                    "['go', 'golang', 'azure']",
                ],
            }
        )
        result = build_nlp_features(df_dupes)
        for val in result["job_skills_normalized"]:
            parsed = ast.literal_eval(val)
            assert len(parsed) == len(set(parsed)), f"Duplicates found in {parsed}"

        # First row must contain distinct c# and c
        row0_skills = ast.literal_eval(result.loc[0, "job_skills_normalized"])
        assert row0_skills == ["c#", "python", "c"]
        # Second row must collapse go and golang to single go
        row1_skills = ast.literal_eval(result.loc[1, "job_skills_normalized"])
        assert row1_skills == ["go", "azure"]


# ---------------------------------------------------------------------------
# validate_nlp_output
# ---------------------------------------------------------------------------

class TestValidateNlpOutput:
    """Tests for validate_nlp_output()."""

    def test_valid_output_passes_and_returns_dict(self, sample_nlp_df):
        """Verifies validation passes on a correctly built NLP DataFrame."""
        enriched = build_nlp_features(sample_nlp_df)
        metrics = validate_nlp_output(enriched)
        assert isinstance(metrics, dict)
        assert metrics["total_records"] == len(sample_nlp_df)
        assert metrics["nlp_columns_present"] is True
        assert metrics["sprint2_columns_preserved"] is True

    def test_empty_dataframe_raises_value_error(self):
        """Verifies ValueError is raised for an empty DataFrame."""
        with pytest.raises(ValueError, match="empty"):
            validate_nlp_output(pd.DataFrame())

    def test_missing_nlp_column_raises_value_error(self, sample_nlp_df):
        """Verifies ValueError is raised when a required NLP column is missing."""
        enriched = build_nlp_features(sample_nlp_df)
        enriched = enriched.drop(columns=["job_title_tokens"])
        with pytest.raises(ValueError, match="job_title_tokens"):
            validate_nlp_output(enriched)

    def test_null_in_nlp_column_raises_value_error(self, sample_nlp_df):
        """Verifies ValueError is raised when an NLP column contains null values."""
        enriched = build_nlp_features(sample_nlp_df)
        enriched.loc[0, "job_title_tokens"] = None
        with pytest.raises(ValueError, match="Null values"):
            validate_nlp_output(enriched)
