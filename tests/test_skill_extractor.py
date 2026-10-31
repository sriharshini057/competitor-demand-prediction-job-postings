"""Unit tests for Stage 4 Skill Extraction and Normalization module.

Tests cover:
- Single skill extraction
- Multiple skills extraction
- Case-insensitive matching (e.g. PYTHON, python, PyThOn)
- Multiword skill matching (e.g. Apache Spark, Microsoft Azure, Power BI, Data Warehousing)
- Alias normalization:
    - sklearn -> Scikit-learn
    - PyTorch -> PyTorch
    - Postgres -> PostgreSQL
    - MS SQL Server -> Microsoft SQL Server
    - k8s -> Kubernetes
- Duplicate prevention within single posting
- Partial-word false positive prevention:
    - 'go' in 'going to the store'
    - 'excel' in 'must excel in communication'
    - 'R' in 'program'
- Empty string input
- None input
- Text with no technical skills (unknown skills)
- Multiple skill categories properly grouped
"""

import pytest

from src.skills.skill_extractor import (
    CANONICAL_SKILL_ALIASES,
    SKILL_TAXONOMY,
    SKILL_TO_CATEGORY,
    SkillExtractor,
)


@pytest.fixture(scope="module")
def shared_skill_extractor():
    """Module-level fixture to share single SkillExtractor instance across tests."""
    return SkillExtractor()


class TestSkillExtractor:
    """Test suite for SkillExtractor class."""

    def test_single_skill(self, shared_skill_extractor):
        """Extracts a single technical skill accurately."""
        text = "Looking for an engineer proficient in Python."
        result = shared_skill_extractor.extract_skills(text)

        assert result["skills"] == ["Python"]
        assert result["skill_count"] == 1
        assert "Programming Languages" in result["categories"]
        assert result["categories"]["Programming Languages"] == ["Python"]

    def test_multiple_skills(self, shared_skill_extractor):
        """Extracts multiple distinct technical skills across categories."""
        text = "Requirements: Python, Docker, PostgreSQL, and AWS."
        result = shared_skill_extractor.extract_skills(text)

        expected = ["Python", "Docker", "PostgreSQL", "AWS"]
        assert result["skills"] == expected
        assert result["skill_count"] == 4

        assert "Programming Languages" in result["categories"]
        assert "Development & Tools" in result["categories"]
        assert "Databases" in result["categories"]
        assert "Cloud" in result["categories"]

    def test_case_insensitive_matching(self, shared_skill_extractor):
        """Skill extraction matches regardless of character casing."""
        text1 = "Knowledge of PYTHON and PANDAS."
        text2 = "Knowledge of python and pandas."
        text3 = "Knowledge of PyThOn and PaNdAs."

        res1 = shared_skill_extractor.extract_skills(text1)["skills"]
        res2 = shared_skill_extractor.extract_skills(text2)["skills"]
        res3 = shared_skill_extractor.extract_skills(text3)["skills"]

        assert res1 == ["Python", "Pandas"]
        assert res2 == ["Python", "Pandas"]
        assert res3 == ["Python", "Pandas"]

    def test_multiword_skill_matching(self, shared_skill_extractor):
        """Extracts multiword skills preserving full phrase boundaries."""
        text = (
            "Must have experience with Apache Spark, Microsoft Azure, "
            "Power BI, and Data Warehousing."
        )
        result = shared_skill_extractor.extract_skills(text)

        skills = result["skills"]
        assert "Apache Spark" in skills
        assert "Microsoft Azure" in skills
        assert "Power BI" in skills
        assert "Data Warehousing" in skills

    def test_alias_normalization_sklearn(self, shared_skill_extractor):
        """Normalizes 'sklearn' alias to canonical 'Scikit-learn'."""
        text = "Experience with sklearn for building predictive models."
        result = shared_skill_extractor.extract_skills(text)
        assert "Scikit-learn" in result["skills"]
        assert "sklearn" not in result["skills"]

    def test_alias_normalization_pytorch(self, shared_skill_extractor):
        """Normalizes 'pytorch' and casing to canonical 'PyTorch'."""
        text = "Deep learning frameworks: pytorch and tensorflow."
        result = shared_skill_extractor.extract_skills(text)
        assert "PyTorch" in result["skills"]
        assert "TensorFlow" in result["skills"]

    def test_alias_normalization_postgres(self, shared_skill_extractor):
        """Normalizes 'Postgres' alias to canonical 'PostgreSQL'."""
        text = "Database experience with Postgres and MySQL required."
        result = shared_skill_extractor.extract_skills(text)
        assert "PostgreSQL" in result["skills"]
        assert "MySQL" in result["skills"]
        assert "Postgres" not in result["skills"]

    def test_alias_normalization_ms_sql_server(self, shared_skill_extractor):
        """Normalizes 'MS SQL Server' and 'mssql' to 'Microsoft SQL Server'."""
        text1 = "Proficient with MS SQL Server."
        text2 = "Proficient with mssql."
        result1 = shared_skill_extractor.extract_skills(text1)
        result2 = shared_skill_extractor.extract_skills(text2)

        assert "Microsoft SQL Server" in result1["skills"]
        assert "Microsoft SQL Server" in result2["skills"]

    def test_alias_normalization_k8s(self, shared_skill_extractor):
        """Normalizes 'k8s' abbreviation to canonical 'Kubernetes'."""
        text = "Container orchestration using k8s and Docker."
        result = shared_skill_extractor.extract_skills(text)
        assert "Kubernetes" in result["skills"]
        assert "Docker" in result["skills"]

    def test_duplicate_prevention(self, shared_skill_extractor):
        """Repeated mentions of a skill produce a single deduplicated entry."""
        text = "Python developer needed. Must know Python, advanced python, and Python 3."
        result = shared_skill_extractor.extract_skills(text)
        assert result["skills"] == ["Python"]
        assert result["skill_count"] == 1

    def test_partial_word_false_positives_go(self, shared_skill_extractor):
        """English verb 'go' in sentences does not trigger false positive Go match."""
        text = "Candidates must go to the headquarters. We also use Python."
        result = shared_skill_extractor.extract_skills(text)
        assert "Go" not in result["skills"]
        assert result["skills"] == ["Python"]

    def test_partial_word_false_positives_excel(self, shared_skill_extractor):
        """English verb 'excel' in phrases like 'excel at' does not trigger Excel tool."""
        text = "The candidate should excel in communication and problem solving."
        result = shared_skill_extractor.extract_skills(text)
        assert "Excel" not in result["skills"]
        assert result["skills"] == []

    def test_actual_excel_tool_matched(self, shared_skill_extractor):
        """Capitalized or qualified Excel as spreadsheet tool is correctly matched."""
        text = "Advanced proficiency in Microsoft Excel and Excel spreadsheets."
        result = shared_skill_extractor.extract_skills(text)
        assert "Excel" in result["skills"]

    def test_excel_verb_at_sentence_start_is_not_matched(self, shared_skill_extractor):
        """Sentence-initial capitalization does not turn the verb into the tool."""
        text = "Excel in communication and leadership."
        result = shared_skill_extractor.extract_skills(text)
        assert "Excel" not in result["skills"]

    def test_partial_word_false_positives_r(self, shared_skill_extractor):
        """Letter 'r' inside regular words does not trigger R programming language."""
        text = "Regular programming with standard procedures."
        result = shared_skill_extractor.extract_skills(text)
        assert "R" not in result["skills"]

    @pytest.mark.parametrize(
        "text",
        [
            "I received an R on the assignment.",
            "The R is listed in the document.",
            "R is the next letter in the sequence.",
        ],
    )
    def test_ordinary_standalone_r_is_not_matched(self, shared_skill_extractor, text):
        """Standalone uppercase R needs programming or statistical context."""
        assert "R" not in shared_skill_extractor.extract_skills(text)["skills"]

    def test_actual_r_language_matched(self, shared_skill_extractor):
        """R in a data-analysis context is correctly matched."""
        text = "Data analysis using R and Python."
        result = shared_skill_extractor.extract_skills(text)
        assert "R" in result["skills"]
        assert "Python" in result["skills"]

    @pytest.mark.parametrize(
        "text",
        [
            "R programming experience is required.",
            "Knowledge of the R language.",
            "Experience with RStudio for statistical analysis.",
        ],
    )
    def test_explicit_r_language_contexts_are_matched(
        self, shared_skill_extractor, text
    ):
        """Programming, language, and RStudio mentions map to canonical R."""
        assert "R" in shared_skill_extractor.extract_skills(text)["skills"]

    @pytest.mark.parametrize(
        "text",
        [
            "The C section is near the end of the document.",
            "I received a C on the assignment.",
            "C is the next letter in the sequence.",
        ],
    )
    def test_ordinary_standalone_c_is_not_matched(self, shared_skill_extractor, text):
        """A standalone C outside explicit language context is not a skill."""
        assert "C" not in shared_skill_extractor.extract_skills(text)["skills"]

    @pytest.mark.parametrize(
        "text",
        [
            "C programming experience is required.",
            "Knowledge of the C language.",
        ],
    )
    def test_explicit_c_language_contexts_are_matched(
        self, shared_skill_extractor, text
    ):
        """Explicit C programming and language phrases are extracted."""
        assert "C" in shared_skill_extractor.extract_skills(text)["skills"]

    @pytest.mark.parametrize(
        "text",
        [
            "Candidates should go as instructed.",
            "Go to the next section of the document.",
            "Please go to the next section.",
            "Employees can go home after work.",
            "We can go home after the meeting.",
            "The word Go appears in the instructions.",
        ],
    )
    def test_ordinary_go_is_not_matched(self, shared_skill_extractor, text):
        """Ordinary verbs and mentions of the word Go are not programming skills."""
        assert "Go" not in shared_skill_extractor.extract_skills(text)["skills"]

    @pytest.mark.parametrize(
        "text",
        [
            "Using Go for backend development.",
            "Experience with Go programming.",
            "Go programming experience is required.",
            "Knowledge of the Go language.",
            "Experience with Golang.",
            "Golang development experience.",
        ],
    )
    def test_go_programming_contexts_are_matched(self, shared_skill_extractor, text):
        """Explicit Go programming, language, and Golang mentions are extracted."""
        assert "Go" in shared_skill_extractor.extract_skills(text)["skills"]

    def test_technical_symbols_csharp_cpp(self, shared_skill_extractor):
        """Special characters in C# and C++ are extracted cleanly."""
        text = "Experience with C# and C++ development."
        result = shared_skill_extractor.extract_skills(text)
        assert "C#" in result["skills"]
        assert "C++" in result["skills"]

    def test_empty_text(self, shared_skill_extractor):
        """Empty string returns empty lists and 0 count."""
        result = shared_skill_extractor.extract_skills("")
        assert result["skills"] == []
        assert result["categories"] == {}
        assert result["skill_count"] == 0

    def test_none_input(self, shared_skill_extractor):
        """None input returns empty lists and 0 count without error."""
        result = shared_skill_extractor.extract_skills(None)
        assert result["skills"] == []
        assert result["categories"] == {}
        assert result["skill_count"] == 0

    def test_unknown_skills(self, shared_skill_extractor):
        """Text without any known skills produces empty skills list."""
        text = "Managing client expectations, coordinating meetings, and budget oversight."
        result = shared_skill_extractor.extract_skills(text)
        assert result["skills"] == []
        assert result["skill_count"] == 0

    def test_multiple_skill_categories(self, shared_skill_extractor):
        """Extracts skills spanning multiple categories and groups them accurately."""
        text = (
            "Tech stack: Python, Pandas, PyTorch, Apache Spark, "
            "PostgreSQL, Microsoft Azure, Docker, and Data Modeling."
        )
        result = shared_skill_extractor.extract_skills(text)

        categories = result["categories"]
        assert "Programming Languages" in categories
        assert "Data Analysis" in categories
        assert "Machine Learning" in categories
        assert "Data Engineering" in categories
        assert "Databases" in categories
        assert "Cloud" in categories
        assert "Development & Tools" in categories
        assert "Other Relevant Skills" in categories

        assert "Python" in categories["Programming Languages"]
        assert "Pandas" in categories["Data Analysis"]
        assert "PyTorch" in categories["Machine Learning"]
        assert "Apache Spark" in categories["Data Engineering"]
        assert "PostgreSQL" in categories["Databases"]
        assert "Microsoft Azure" in categories["Cloud"]
        assert "Docker" in categories["Development & Tools"]
        assert "Data Modeling" in categories["Other Relevant Skills"]

    def test_normalize_skill_fallback(self, shared_skill_extractor):
        """normalize_skill handles unknown and edge-case strings gracefully."""
        assert shared_skill_extractor.normalize_skill("unknown_skill") == "unknown_skill"
        assert shared_skill_extractor.normalize_skill("") == ""
