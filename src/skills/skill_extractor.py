"""Deterministic Skill Extraction and Normalization Module.

Stage 4: spaCy PhraseMatcher- and Matcher-based extraction of technical, data,
cloud, engineering, and analytical skills with category traceability and alias normalization.
"""

import logging
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import spacy
from spacy.language import Language
from spacy.matcher import Matcher, PhraseMatcher
from spacy.tokens import Doc, Span
from spacy.util import filter_spans

from src.skills.ner_extractor import DEFAULT_SPACY_MODEL, load_spacy_model

# Console encoding safety for Windows
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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Transparent Skill Taxonomy by Category
# ---------------------------------------------------------------------------

SKILL_TAXONOMY: Dict[str, List[str]] = {
    "Programming Languages": [
        "Python",
        "Java",
        "C++",
        "C#",
        "C",
        "JavaScript",
        "TypeScript",
        "SQL",
        "R",
        "Scala",
        "Go",
    ],
    "Data Analysis": [
        "Pandas",
        "NumPy",
        "Matplotlib",
        "Seaborn",
        "Excel",
        "Power BI",
        "Tableau",
        "Power Query",
        "DAX",
    ],
    "Machine Learning": [
        "Scikit-learn",
        "TensorFlow",
        "PyTorch",
        "Keras",
        "XGBoost",
        "LightGBM",
        "CatBoost",
        "Machine Learning",
    ],
    "Data Engineering": [
        "Apache Spark",
        "PySpark",
        "Hadoop",
        "Kafka",
        "Airflow",
        "ETL",
        "ELT",
        "Data Warehousing",
        "Snowflake",
        "Databricks",
        "BigQuery",
        "dbt",
    ],
    "Databases": [
        "MySQL",
        "PostgreSQL",
        "MongoDB",
        "SQLite",
        "Microsoft SQL Server",
        "Oracle",
        "Redis",
        "Cassandra",
        "NoSQL",
    ],
    "Cloud": [
        "AWS",
        "Microsoft Azure",
        "Google Cloud Platform",
        "Azure Data Factory",
        "Amazon S3",
        "Azure Synapse",
        "Azure DevOps",
    ],
    "Development & Tools": [
        "Git",
        "GitHub",
        "Docker",
        "Kubernetes",
        "REST API",
        "FastAPI",
        "Flask",
        "Linux",
        "CI/CD",
        "Jenkins",
    ],
    "Other Relevant Skills": [
        "Data Modeling",
        "Data Cleaning",
        "Data Visualization",
        "Statistics",
        "NLP",
        "Deep Learning",
        "Artificial Intelligence",
        "Business Intelligence",
    ],
}

# ---------------------------------------------------------------------------
# Documented Canonical Alias & Normalization Mapping
# ---------------------------------------------------------------------------
# Maps variants, informal acronyms, abbreviations, and lowercase aliases
# to the canonical skill name.
CANONICAL_SKILL_ALIASES: Dict[str, str] = {
    # Machine Learning & AI
    "sklearn": "Scikit-learn",
    "scikitlearn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "keras": "Keras",
    "xgboost": "XGBoost",
    "xgb": "XGBoost",
    "lightgbm": "LightGBM",
    "catboost": "CatBoost",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "artificial intelligence": "Artificial Intelligence",
    "ai": "Artificial Intelligence",
    "nlp": "NLP",
    "natural language processing": "NLP",

    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "ms sql server": "Microsoft SQL Server",
    "mssql": "Microsoft SQL Server",
    "sql server": "Microsoft SQL Server",
    "microsoft sql server": "Microsoft SQL Server",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "oracle": "Oracle",
    "redis": "Redis",
    "cassandra": "Cassandra",
    "nosql": "NoSQL",

    # Cloud
    "azure": "Microsoft Azure",
    "microsoft azure": "Microsoft Azure",
    "ms azure": "Microsoft Azure",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "Google Cloud Platform",
    "google cloud": "Google Cloud Platform",
    "google cloud platform": "Google Cloud Platform",
    "adf": "Azure Data Factory",
    "azure data factory": "Azure Data Factory",
    "s3": "Amazon S3",
    "amazon s3": "Amazon S3",
    "azure synapse": "Azure Synapse",
    "azure devops": "Azure DevOps",

    # Data Engineering
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "pyspark": "PySpark",
    "hadoop": "Hadoop",
    "apache hadoop": "Hadoop",
    "kafka": "Kafka",
    "apache kafka": "Kafka",
    "airflow": "Airflow",
    "apache airflow": "Airflow",
    "etl": "ETL",
    "elt": "ELT",
    "data warehouse": "Data Warehousing",
    "data warehousing": "Data Warehousing",
    "dwh": "Data Warehousing",
    "snowflake": "Snowflake",
    "databricks": "Databricks",
    "bigquery": "BigQuery",
    "dbt": "dbt",

    # Programming Languages
    "python": "Python",
    "python3": "Python",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "c sharp": "C#",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "golang": "Go",
    "go": "Go",
    "scala": "Scala",
    "sql": "SQL",
    "r": "R",
    "r.": "R",
    "rstudio": "R",
    "c": "C",

    # Data Analysis & BI
    "pandas": "Pandas",
    "numpy": "NumPy",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "excel": "Excel",
    "ms excel": "Excel",
    "microsoft excel": "Excel",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "tableau": "Tableau",
    "power query": "Power Query",
    "dax": "DAX",
    "business intelligence": "Business Intelligence",
    "bi": "Business Intelligence",

    # Development & Tools
    "git": "Git",
    "github": "GitHub",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "rest": "REST API",
    "rest api": "REST API",
    "rest apis": "REST API",
    "restful": "REST API",
    "restful api": "REST API",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "linux": "Linux",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "jenkins": "Jenkins",

    # Other Skills
    "data modeling": "Data Modeling",
    "data modelling": "Data Modeling",
    "data cleaning": "Data Cleaning",
    "data cleansing": "Data Cleaning",
    "data visualization": "Data Visualization",
    "data visualisation": "Data Visualization",
    "dataviz": "Data Visualization",
    "statistics": "Statistics",
    "statistical analysis": "Statistics",
}

# Reverse mapping: Canonical skill name -> Primary category
SKILL_TO_CATEGORY: Dict[str, str] = {}
for category, skills in SKILL_TAXONOMY.items():
    for skill in skills:
        SKILL_TO_CATEGORY[skill] = category


class SkillExtractor:
    """Deterministic skill extractor using spaCy PhraseMatcher and Matcher.

    Provides transparent matching of multiword skills, case-insensitivity,
    alias normalization, false-positive filtering for ambiguous tokens,
    and category traceability.
    """

    def __init__(
        self,
        nlp: Optional[Language] = None,
        model_name: str = DEFAULT_SPACY_MODEL,
        alias_mapping: Optional[Dict[str, str]] = None,
        taxonomy: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initializes the SkillExtractor with a spaCy pipeline and pattern matchers.

        Args:
            nlp: Preloaded spaCy Language pipeline. If None, loads `model_name`.
            model_name: spaCy model name to load if `nlp` is None.
            alias_mapping: Custom alias normalization dictionary.
            taxonomy: Custom category-to-skills dictionary.
        """
        if nlp is not None:
            self.nlp = nlp
        else:
            self.nlp = load_spacy_model(model_name)

        self.taxonomy = taxonomy or SKILL_TAXONOMY
        self.aliases = alias_mapping or CANONICAL_SKILL_ALIASES

        # Build skill-to-category index
        self.skill_to_category: Dict[str, str] = {}
        for category, skills in self.taxonomy.items():
            for skill in skills:
                self.skill_to_category[skill] = category

        # Polysemous/ambiguous tokens requiring context or POS validation
        self.ambiguous_tokens = {"go", "excel", "r", "c"}

        self._init_matchers()

    def _init_matchers(self) -> None:
        """Builds spaCy PhraseMatcher and Matcher patterns for skills."""
        # PhraseMatcher with lowercase attribute for case-insensitive matching
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        # Matcher for specialized token-level patterns (e.g. C++, C#, single letters)
        self.token_matcher = Matcher(self.nlp.vocab)

        # Collect all phrases to match from aliases and canonical taxonomy
        phrase_set: Set[str] = set()
        for alias in self.aliases.keys():
            # Exclude single character or special symbol tokens handled by token_matcher
            if alias.lower() not in {"c++", "c#", "r", "c", "r."}:
                phrase_set.add(alias.lower())

        for skills in self.taxonomy.values():
            for s in skills:
                if s.lower() not in {"c++", "c#", "r", "c", "r."}:
                    phrase_set.add(s.lower())

        patterns = [self.nlp.make_doc(phrase) for phrase in phrase_set if phrase.strip()]
        self.phrase_matcher.add("PHRASE_SKILL", patterns)

        # Token-level Matcher patterns for technical terms with special characters
        # C++
        self.token_matcher.add("CPP_SKILL", [
            [{"LOWER": "c++"}],
            [{"LOWER": "c"}, {"TEXT": "++"}],
        ])
        # C# (often tokenized as ['C', '#'])
        self.token_matcher.add("CSHARP_SKILL", [
            [{"LOWER": "c#"}],
            [{"LOWER": "c"}, {"TEXT": "#"}],
        ])
        # R (exact single letter token, uppercase 'R' or followed by period 'R.')
        self.token_matcher.add("R_SKILL", [
            [{"TEXT": "R"}],
            [{"TEXT": "R."}],
        ])
        # Scikit-learn (robust across mixed casing and sentence boundaries)
        self.token_matcher.add("SKLEARN_SKILL", [
            [{"LOWER": "scikit"}, {"TEXT": "-"}, {"LOWER": {"REGEX": r"^learn"}}],
        ])
        # CI/CD
        self.token_matcher.add("CICD_SKILL", [
            [{"LOWER": "ci/cd"}],
            [{"LOWER": "ci"}, {"TEXT": "/"}, {"LOWER": "cd"}],
        ])
        # C (only when followed by /C++ or in 'C and C++' or 'C programming/language')
        self.token_matcher.add("C_SKILL", [
            [{"TEXT": "C"}, {"TEXT": "/"}, {"LOWER": "c++"}],
            [{"TEXT": "C"}, {"LOWER": "and"}, {"LOWER": "c++"}],
            [{"TEXT": "C"}, {"LOWER": "or"}, {"LOWER": "c++"}],
            [{"TEXT": "C"}, {"LOWER": "language"}],
            [{"TEXT": "C"}, {"LOWER": "programming"}],
        ])

    def normalize_skill(self, raw_skill: str) -> str:
        """Maps an extracted skill phrase to its canonical normalized form.

        Args:
            raw_skill: The raw matched text string.

        Returns:
            Canonical skill string according to `self.aliases` or capitalized default.
        """
        # Strip surrounding whitespace and boundary punctuation (e.g. trailing period, comma)
        # but preserve interior symbols like '#' in C# or '++' in C++ or '-' in Scikit-learn
        cleaned = raw_skill.strip()
        cleaned = re.sub(r"^[^\w+#]+|[^\w+#]+$", "", cleaned).lower()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Direct alias lookup
        if cleaned in self.aliases:
            return self.aliases[cleaned]

        # Check if already a known canonical skill (case-insensitive)
        for canonical in self.skill_to_category.keys():
            if canonical.lower() == cleaned:
                return canonical

        # Fallback capitalization
        return raw_skill.strip()

    def _is_valid_match(self, span: Span) -> bool:
        """Validates that a matched span is not a false positive.

        Checks:
        - Rejects English verbs like 'go' in 'must go to work' (requires Go PROPN or Golang).
        - Rejects English verb 'excel' in 'excel at communication' (requires Excel tool/noun).
        - Rejects single letter false positives.

        Args:
            span: Matched spaCy Span.

        Returns:
            True if valid skill mention, False otherwise.
        """
        text_lower = span.text.strip().lower()
        left_context = [token.lower_ for token in span.doc[max(0, span.start - 3):span.start]]
        right_context = [
            token.lower_ for token in span.doc[span.end:min(len(span.doc), span.end + 3)]
        ]

        # Check 'go'
        if text_lower == "go":
            programming_terms = {
                "program",
                "programming",
                "language",
                "developer",
                "development",
            }
            technical_phrases = {
                ("experience", "with"),
                ("knowledge", "of"),
                ("proficient", "in"),
                ("proficiency", "in"),
                ("skills", "in"),
                ("working", "with"),
            }
            left_pairs = set(zip(left_context, left_context[1:]))
            has_technical_context = (
                bool(programming_terms.intersection(right_context))
                or bool(technical_phrases.intersection(left_pairs))
                or (left_context and left_context[-1] in {"use", "using"})
            )
            if not has_technical_context:
                return False

        # Check 'excel'
        if text_lower == "excel":
            # If tagged as VERB, it's 'to excel in', not Microsoft Excel
            if len(span) == 1 and span[0].pos_ == "VERB":
                return False
            # If followed by 'at' or 'in' and lowercase, likely the verb
            if span.end < len(span.doc) and span.doc[span.end].lower_ in {"at", "in"}:
                if not span[0].text.istitle():
                    return False

        # A standalone R is ambiguous; require programming/statistics context.
        if text_lower in {"r", "r."}:
            technical_terms = {
                "analysis",
                "analytics",
                "data",
                "language",
                "program",
                "programming",
                "statistical",
                "statistics",
            }
            technical_phrases = {
                ("experience", "with"),
                ("knowledge", "of"),
                ("proficient", "in"),
                ("proficiency", "in"),
                ("skills", "in"),
                ("using",),
            }
            has_technical_context = (
                bool(technical_terms.intersection(left_context + right_context))
                or any(
                    left_context[-len(phrase):] == list(phrase)
                    for phrase in technical_phrases
                    if len(left_context) >= len(phrase)
                )
            )
            if not has_technical_context:
                return False

        return True

    def extract_skills(self, text: Any) -> Dict[str, Any]:
        """Extracts and normalizes skills from an input text string.

        Performs:
        1. PhraseMatcher and token-level Matcher matching.
        2. Longest-span resolution (e.g. 'Microsoft Azure' over 'Azure').
        3. False positive filtering for polysemous words.
        4. Canonical normalization and deduplication.
        5. Category grouping.

        Args:
            text: Input string (job description, title, or combined text).

        Returns:
            Dictionary with:
                - 'skills': List[str] of deduplicated canonical skill names.
                - 'categories': Dict[str, List[str]] mapping category to matched skills.
                - 'skill_count': int total unique skills extracted.
                - 'raw_matches': List[Dict[str, Any]] containing match details.
        """
        if text is None:
            return {
                "skills": [],
                "categories": {},
                "skill_count": 0,
                "raw_matches": [],
            }

        text_str = str(text).strip()
        if not text_str:
            return {
                "skills": [],
                "categories": {},
                "skill_count": 0,
                "raw_matches": [],
            }

        doc = self.nlp(text_str)

        raw_spans: List[Span] = []

        # 1. Collect PhraseMatcher matches
        for match_id, start, end in self.phrase_matcher(doc):
            span = doc[start:end]
            if self._is_valid_match(span):
                raw_spans.append(span)

        # 2. Collect Token Matcher matches
        for match_id, start, end in self.token_matcher(doc):
            rule_name = self.nlp.vocab.strings[match_id]
            if rule_name == "C_SKILL":
                # Only take the 'C' token from 'C / C++' or 'C and C++'
                raw_spans.append(doc[start:start + 1])
            else:
                span = doc[start:end]
                if self._is_valid_match(span):
                    raw_spans.append(span)

        # 3. Filter overlapping spans (longest phrase wins)
        filtered_spans = filter_spans(raw_spans)

        # 4. Normalize and deduplicate preserving order
        extracted_skills: List[str] = []
        seen_skills: Set[str] = set()
        raw_match_records: List[Dict[str, Any]] = []

        for span in filtered_spans:
            raw_text = span.text.strip()
            canonical_name = self.normalize_skill(raw_text)

            raw_match_records.append({
                "raw_text": raw_text,
                "canonical_name": canonical_name,
                "start_char": span.start_char,
                "end_char": span.end_char,
            })

            if canonical_name and canonical_name not in seen_skills:
                seen_skills.add(canonical_name)
                extracted_skills.append(canonical_name)

        # 5. Group by category
        categories_dict: Dict[str, List[str]] = {}
        for skill in extracted_skills:
            category = self.skill_to_category.get(skill, "Other Relevant Skills")
            if category not in categories_dict:
                categories_dict[category] = []
            categories_dict[category].append(skill)

        return {
            "skills": extracted_skills,
            "categories": categories_dict,
            "skill_count": len(extracted_skills),
            "raw_matches": raw_match_records,
        }
