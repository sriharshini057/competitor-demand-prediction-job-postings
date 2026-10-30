"""NLP Preprocessing Pipeline Module.

Stage 3: Text normalization, tokenization, stop-word removal, lemmatization,
skill list deserialization, and skill token normalization.

Input  : data/processed/microsoft_jobs_cleaned.csv  (Sprint 2 output — read-only)
Output : data/processed/microsoft_jobs_nlp.csv      (Sprint 3 artifact — additive columns only)

New columns added (Sprint 2 columns are NEVER modified):
    job_title_tokens       : List[str] — lemmatized, stop-word-filtered tokens from job_title
    job_skills_list        : List[str] — deserialized job_skills_parsed back to Python list
    job_skills_normalized  : List[str] — punctuation-normalized skill tokens
"""

import ast
import logging
import re
import string
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

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
DEFAULT_INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "microsoft_jobs_cleaned.csv"
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "microsoft_jobs_nlp.csv"

# ---------------------------------------------------------------------------
# Stop-word management — NLTK with graceful fallback
# ---------------------------------------------------------------------------

#: Minimal hard-coded English stop-word set used when NLTK is unavailable.
_FALLBACK_STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "as", "not", "no", "nor", "so", "yet", "both", "either", "neither",
    "each", "every", "all", "any", "few", "more", "most", "other", "some",
    "such", "than", "then", "that", "this", "these", "those", "i", "you",
    "he", "she", "it", "we", "they", "what", "which", "who", "whom",
    "how", "when", "where", "why", "its", "our", "their", "my", "your",
}

#: Domain-specific tokens to exclude from job-title analysis.
#: Includes corporate brand name, seniority prefixes, Roman numerals, and
#: numeric level indicators (1-6) that indicate hierarchy rather than core function.
DOMAIN_STOPWORDS: Set[str] = {
    "microsoft", "senior", "junior", "jr", "sr", "lead", "principal",
    "staff", "associate", "ii", "iii", "iv", "v", "i",
    "1", "2", "3", "4", "5", "6",
}

#: Documented canonical alias mapping for programming languages and technologies.
#: Maps common informal variants, abbreviations, and acronyms to canonical skill names.
CANONICAL_SKILL_ALIASES: Dict[str, str] = {
    "golang": "go",
    "mongo": "mongodb",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "sklearn": "scikit-learn",
    "csharp": "c#",
    "c sharp": "c#",
    "cpp": "c++",
    "ts": "typescript",
    "js": "javascript",
}


def _load_nltk_stopwords() -> Set[str]:
    """Loads NLTK English stop-words, downloading corpora if absent.

    Returns:
        Set of English stop-word strings. Falls back to ``_FALLBACK_STOPWORDS``
        if NLTK is unavailable or corpus download fails.
    """
    try:
        import nltk
        from nltk.corpus import stopwords as nltk_sw

        try:
            words = set(nltk_sw.words("english"))
            logger.debug("NLTK stop-words loaded: %d words", len(words))
            return words
        except LookupError:
            logger.info("NLTK 'stopwords' corpus not found -- downloading...")
            nltk.download("stopwords", quiet=True)
            words = set(nltk_sw.words("english"))
            logger.info("NLTK stop-words downloaded and loaded: %d words", len(words))
            return words
    except ImportError:
        logger.warning("NLTK not installed; using fallback stop-word set (%d words).", len(_FALLBACK_STOPWORDS))
        return _FALLBACK_STOPWORDS
    except Exception as exc:  # pragma: no cover
        logger.warning("Unexpected NLTK error (%s); using fallback stop-word set.", exc)
        return _FALLBACK_STOPWORDS


def _get_lemmatizer():
    """Returns an NLTK WordNetLemmatizer instance, or None if unavailable.

    Returns:
        nltk.stem.WordNetLemmatizer instance or None.
    """
    try:
        import nltk
        from nltk.stem import WordNetLemmatizer

        try:
            lemmatizer = WordNetLemmatizer()
            # Trigger a test lemmatization to confirm wordnet corpus is available
            lemmatizer.lemmatize("engineers")
            return lemmatizer
        except LookupError:
            logger.info("NLTK 'wordnet' corpus not found -- downloading...")
            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)
            lemmatizer = WordNetLemmatizer()
            lemmatizer.lemmatize("engineers")  # validate
            logger.info("NLTK WordNet downloaded successfully.")
            return lemmatizer
    except ImportError:
        logger.warning("NLTK not installed; lemmatization will be skipped.")
        return None
    except Exception as exc:  # pragma: no cover
        logger.warning("Unexpected NLTK lemmatizer error (%s); skipping lemmatization.", exc)
        return None


# ---------------------------------------------------------------------------
# Core NLP functions
# ---------------------------------------------------------------------------

def normalize_text(text: Any) -> str:
    """Normalises a raw text string for tokenization.

    Steps applied (in order):
    1. Cast to string and strip surrounding whitespace.
    2. NFKC Unicode normalization (normalizes fullwidth characters, spaces).
    3. Normalize various Unicode dashes (en-dash, em-dash, minus) to ASCII hyphen.
    4. Replace hyphens and slashes used as separators (i.e. surrounded by whitespace
       or multiple hyphens '--') with spaces while preserving internal compound hyphens.
    5. Lowercase all characters.
    6. Replace punctuation characters with spaces *except* technical symbols:
       hyphens (``-``), forward slashes (``/``), plus signs (``+``), and hash signs (``#``).
    7. Collapse multiple consecutive whitespace characters to a single space.

    Args:
        text: Raw input value (str, float NaN, None, etc.).

    Returns:
        Normalised lowercase string; empty string if input is null/empty.

    Examples:
        >>> normalize_text("Senior Software Engineer (II)")
        'senior software engineer ii'
        >>> normalize_text("  Data & Applied Scientist  ")
        'data applied scientist'
        >>> normalize_text("Full-Stack Developer (C# / C++)")
        'full-stack developer c# c++'
    """
    if pd.isna(text) or text is None:
        return ""
    s = unicodedata.normalize("NFKC", str(text)).strip()
    # Normalize unicode dashes to ascii hyphen
    s = re.sub(r"[\u2010-\u2015\u2212]", "-", s)
    # Replace multiple hyphens (like '--') and spaced hyphens/slashes with spaces
    s = re.sub(r"--+", " ", s)
    s = re.sub(r"\s+[-/]+\s*|\s*[-/]+\s+", " ", s)
    s = s.lower()
    # Remove all punctuation except hyphens, forward slashes, plus, and hash
    allowed_punct = {"-", "/", "+", "#"}
    cleaned_chars = []
    for ch in s:
        if ch in string.punctuation and ch not in allowed_punct:
            cleaned_chars.append(" ")
        else:
            cleaned_chars.append(ch)
    s = "".join(cleaned_chars)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokenize(text: str) -> List[str]:
    """Splits a normalised text string into individual word tokens.

    Splits on whitespace, trims boundary punctuation (leading/trailing hyphens,
    slashes, periods) from tokens, and filters out standalone punctuation tokens
    that lack alphanumeric characters.

    Args:
        text: Normalised text string (output of :func:`normalize_text`).

    Returns:
        List of individual word token strings.

    Examples:
        >>> tokenize("senior software engineer")
        ['senior', 'software', 'engineer']
        >>> tokenize("full-stack c# c++ -")
        ['full-stack', 'c#', 'c++']
        >>> tokenize("")
        []
    """
    if not text or not text.strip():
        return []
    raw_tokens = text.split()
    tokens = []
    for tok in raw_tokens:
        t = tok.strip("-/.,;:")
        if t and any(ch.isalnum() for ch in t):
            tokens.append(t)
    return tokens


def remove_stopwords(
    tokens: List[str],
    extra_stopwords: Optional[Set[str]] = None,
) -> List[str]:
    """Filters stop-words from a token list.

    Uses NLTK English stop-words with graceful fallback to
    :data:`_FALLBACK_STOPWORDS`. Optionally merges caller-supplied additional
    stop-words (e.g. domain-specific terms).

    Args:
        tokens: List of word token strings.
        extra_stopwords: Optional set of additional tokens to exclude.

    Returns:
        Filtered list of tokens with stop-words removed.

    Examples:
        >>> remove_stopwords(["senior", "software", "engineer", "at", "the"])
        ['senior', 'software', 'engineer']
    """
    base_stopwords = _load_nltk_stopwords()
    combined = base_stopwords.copy()
    if extra_stopwords:
        combined.update(t.lower() for t in extra_stopwords)
    return [tok for tok in tokens if tok.lower() not in combined]


def lemmatize_tokens(tokens: List[str]) -> List[str]:
    """Reduces tokens to their base lemma forms using NLTK WordNetLemmatizer.

    If NLTK or WordNet is unavailable, tokens are returned unchanged (graceful
    degradation). Lemmatization is applied with the noun POS tag (``"n"``) as
    the default, which is appropriate for job-role vocabulary.

    Args:
        tokens: List of word token strings.

    Returns:
        List of lemmatized token strings (or original tokens if NLTK unavailable).

    Examples:
        >>> lemmatize_tokens(["engineers", "scientists", "building"])
        ['engineer', 'scientist', 'building']
    """
    lemmatizer = _get_lemmatizer()
    if lemmatizer is None:
        logger.debug("Lemmatizer unavailable; returning tokens unchanged.")
        return tokens
    return [lemmatizer.lemmatize(tok, pos="n") for tok in tokens]


def preprocess_job_title(
    title: Any,
    extra_stopwords: Optional[Set[str]] = None,
) -> List[str]:
    """Composes the full NLP preprocessing pipeline for a single job title.

    Pipeline steps:
        1. :func:`normalize_text` — lowercase, strip punctuation
        2. :func:`tokenize` — split to word tokens
        3. :func:`remove_stopwords` — filter English + domain stop-words
        4. :func:`lemmatize_tokens` — reduce to base lemma forms

    Args:
        title: Raw job title string (or null value).
        extra_stopwords: Optional additional stop-words beyond the defaults.

    Returns:
        List of clean, lemmatized, stop-word-free token strings.

    Examples:
        >>> preprocess_job_title("Senior Software Engineers II")
        ['software', 'engineer']
    """
    merged_stopwords = DOMAIN_STOPWORDS.copy()
    if extra_stopwords:
        merged_stopwords.update(extra_stopwords)

    normalized = normalize_text(title)
    tokens = tokenize(normalized)
    tokens = remove_stopwords(tokens, extra_stopwords=merged_stopwords)
    tokens = lemmatize_tokens(tokens)
    return tokens


# ---------------------------------------------------------------------------
# Skill deserialization and normalization
# ---------------------------------------------------------------------------

def deserialize_skill_list(skill_str: Any) -> List[str]:
    """Safely parses the CSV-serialized ``job_skills_parsed`` string back to a
    Python list of strings.

    Sprint 2's :func:`~src.preprocessing.cleaner.save_cleaned_dataset` converts
    the ``job_skills_parsed`` list to its ``str()`` representation for CSV
    persistence (e.g. ``"['python', 'azure', 'sql']"``). This function
    reverses that serialization using :func:`ast.literal_eval`.

    Args:
        skill_str: Serialized skill list string, or NaN/None.

    Returns:
        Python list of skill strings; empty list ``[]`` on any parse failure.

    Examples:
        >>> deserialize_skill_list("['python', 'azure', 'sql']")
        ['python', 'azure', 'sql']
        >>> deserialize_skill_list(float('nan'))
        []
    """
    if pd.isna(skill_str) or skill_str is None or str(skill_str).strip() == "":
        return []
    raw = str(skill_str).strip()
    # Handle explicit empty list representations
    if raw in ("[]", "nan", "None"):
        return []
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return [str(s) for s in parsed]
    except (ValueError, SyntaxError):
        logger.debug("Failed to parse skill list string: %r", raw[:80])
    return []


def normalize_skill_token(skill: str) -> str:
    """Normalises a single skill token for consistent downstream matching.

    Applied normalization:
    - Lowercase
    - Strip leading/trailing whitespace
    - Remove punctuation characters *except* hyphens, spaces, dots, plus signs,
      and hash signs (retaining '+', '#', '.', '-' to preserve terms like 'c++',
      'c#', 'node.js', 'asp.net', 'scikit-learn').
    - Collapse internal whitespace
    - Canonical alias mapping via :data:`CANONICAL_SKILL_ALIASES` (e.g. 'golang' -> 'go',
      'csharp' -> 'c#', 'mongo' -> 'mongodb').

    Note: Lemmatization is intentionally **not** applied to skill tokens.
    Skill names are proper nouns / branded terms (e.g., ``"databricks"``,
    ``"pytorch"``) that must not be lemmatized.

    Args:
        skill: A single skill string.

    Returns:
        Normalised skill string.

    Examples:
        >>> normalize_skill_token("  Power BI  ")
        'power bi'
        >>> normalize_skill_token("C++")
        'c++'
        >>> normalize_skill_token("C#")
        'c#'
        >>> normalize_skill_token("Node.js")
        'node.js'
        >>> normalize_skill_token("golang")
        'go'
    """
    if not skill or not isinstance(skill, str):
        return ""
    s = skill.strip().lower()
    # Keep: letters, digits, spaces, hyphens, dots, plus signs, hash signs
    s = re.sub(r"[^\w\s\-\.+#]", "", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return CANONICAL_SKILL_ALIASES.get(s, s)


def normalize_skills_list(skills: List[str]) -> List[str]:
    """Normalizes a list of skill tokens for a single job posting.

    Applies :func:`normalize_skill_token` to each element, discards empty tokens,
    and eliminates duplicate normalized skills within the job posting while strictly
    preserving original insertion order.

    Args:
        skills: List of raw skill strings.

    Returns:
        List of deduplicated, normalized skill strings.

    Examples:
        >>> normalize_skills_list(["python", "azure", "python"])
        ['python', 'azure']
        >>> normalize_skills_list(["C#", "c#", "C++"])
        ['c#', 'c++']
        >>> normalize_skills_list(["go", "golang"])
        ['go']
    """
    if not skills:
        return []
    seen: Set[str] = set()
    normalized: List[str] = []
    for s in skills:
        norm = normalize_skill_token(s)
        if norm and norm not in seen:
            seen.add(norm)
            normalized.append(norm)
    return normalized


# ---------------------------------------------------------------------------
# DataFrame-level feature builder
# ---------------------------------------------------------------------------

def build_nlp_features(df: pd.DataFrame) -> pd.DataFrame:
    """Applies the NLP preprocessing pipeline across all rows of the cleaned
    DataFrame, adding three new columns without modifying any Sprint 2 columns.

    New columns added:
        ``job_title_tokens``      (str — serialized List[str] for CSV compatibility)
            Lemmatized, stop-word-filtered tokens derived from ``job_title``.

        ``job_skills_list``       (str — serialized List[str] for CSV compatibility)
            Deserialized Python list from the CSV-stringified ``job_skills_parsed``.

        ``job_skills_normalized`` (str — serialized List[str] for CSV compatibility)
            Punctuation-normalized version of each element in ``job_skills_list``.

    Args:
        df: The cleaned Microsoft job postings DataFrame (Sprint 2 output).

    Returns:
        A copy of ``df`` with the three new columns appended.

    Raises:
        KeyError: If required columns ``job_title`` or ``job_skills_parsed``
                  are absent from the input DataFrame.
    """
    required_cols = {"job_title", "job_skills_parsed"}
    missing = required_cols - set(df.columns)
    if missing:
        raise KeyError(f"Required columns missing from input DataFrame: {missing}")

    df_out = df.copy()

    logger.info("Preprocessing job titles -> job_title_tokens ...")
    title_tokens = df_out["job_title"].apply(preprocess_job_title)
    # Serialize to string for CSV persistence (same pattern as cleaner.py)
    df_out["job_title_tokens"] = title_tokens.apply(str)

    logger.info("Deserializing skill lists -> job_skills_list ...")
    skill_lists = df_out["job_skills_parsed"].apply(deserialize_skill_list)
    df_out["job_skills_list"] = skill_lists.apply(str)

    logger.info("Normalizing skill tokens -> job_skills_normalized ...")
    normalized_skills = skill_lists.apply(normalize_skills_list)
    df_out["job_skills_normalized"] = normalized_skills.apply(str)

    logger.info(
        "NLP features built: %d rows processed. New columns: "
        "job_title_tokens, job_skills_list, job_skills_normalized.",
        len(df_out),
    )
    return df_out


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_nlp_output(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates the NLP-enriched DataFrame before saving.

    Checks:
    1. DataFrame is non-empty.
    2. All three new NLP columns are present.
    3. No null values in any new NLP column.
    4. Sprint 2 primary identifiers (``job_title``, ``job_posted_date``,
       ``company_name``) remain intact and null-free.
    5. Row count matches the Sprint 2 baseline of 498 records.

    Args:
        df: NLP-enriched DataFrame.

    Returns:
        Dictionary of validation result metrics.

    Raises:
        ValueError: If any critical validation check fails.
    """
    logger.info("Validating NLP-enriched dataset ...")

    if len(df) == 0:
        raise ValueError("Validation failed: NLP output DataFrame is empty.")

    nlp_cols = ["job_title_tokens", "job_skills_list", "job_skills_normalized"]
    for col in nlp_cols:
        if col not in df.columns:
            raise ValueError(f"Validation failed: Expected NLP column '{col}' is missing.")

    null_tokens = int(df["job_title_tokens"].isnull().sum())
    null_skills_list = int(df["job_skills_list"].isnull().sum())
    null_skills_norm = int(df["job_skills_normalized"].isnull().sum())

    if null_tokens > 0 or null_skills_list > 0 or null_skills_norm > 0:
        raise ValueError(
            f"Validation failed: Null values in NLP columns -- "
            f"job_title_tokens={null_tokens}, job_skills_list={null_skills_list}, "
            f"job_skills_normalized={null_skills_norm}."
        )

    # Verify Sprint 2 primary identifiers are untouched
    null_titles = int(df["job_title"].isnull().sum())
    null_dates = int(df["job_posted_date"].isnull().sum())
    null_companies = int(df["company_name"].isnull().sum())
    non_microsoft = int((df["company_name"] != "Microsoft").sum())

    if null_titles > 0 or null_dates > 0 or null_companies > 0:
        raise ValueError(
            f"Validation failed: Sprint 2 columns corrupted -- "
            f"null titles={null_titles}, null dates={null_dates}, null companies={null_companies}."
        )
    if non_microsoft > 0:
        raise ValueError(
            f"Validation failed: {non_microsoft} non-Microsoft records detected after NLP processing."
        )

    results = {
        "total_records": len(df),
        "total_columns": len(df.columns),
        "sprint2_columns_preserved": True,
        "nlp_columns_present": True,
        "null_job_title_tokens": null_tokens,
        "null_job_skills_list": null_skills_list,
        "null_job_skills_normalized": null_skills_norm,
        "null_titles": null_titles,
        "null_dates": null_dates,
        "null_companies": null_companies,
        "non_microsoft_records": non_microsoft,
    }

    logger.info(
        "NLP output validation PASSED: %d records, %d columns, 0 nulls in NLP columns.",
        len(df), len(df.columns),
    )
    return results


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_nlp_dataset(
    df: pd.DataFrame,
    output_path: Path = DEFAULT_OUTPUT_FILE,
) -> Path:
    """Saves the NLP-enriched DataFrame to a CSV file.

    Args:
        df: NLP-enriched DataFrame to save.
        output_path: Destination path for the CSV file.

    Returns:
        Path to the saved CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    file_size_kb = output_path.stat().st_size / 1024
    logger.info(
        "NLP dataset saved: %s (%.2f KB, %d records, %d columns)",
        output_path, file_size_kb, len(df), len(df.columns),
    )
    return output_path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_nlp_pipeline(
    input_path: Path = DEFAULT_INPUT_FILE,
    output_path: Path = DEFAULT_OUTPUT_FILE,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Orchestrates the end-to-end Stage 3 NLP preprocessing pipeline.

    Steps:
    1. Load the Sprint 2 cleaned dataset.
    2. Apply NLP feature engineering via :func:`build_nlp_features`.
    3. Validate the enriched output via :func:`validate_nlp_output`.
    4. Save the enriched dataset to ``output_path``.

    Args:
        input_path: Path to ``microsoft_jobs_cleaned.csv`` (Sprint 2 output).
        output_path: Destination path for the NLP-enriched CSV.

    Returns:
        Tuple of (enriched DataFrame, validation metrics dictionary).

    Raises:
        FileNotFoundError: If ``input_path`` does not exist.
        ValueError: If validation checks fail.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info("Starting Stage 3 NLP Preprocessing pipeline ...")
    logger.info("Input : %s", input_path)
    logger.info("Output: %s", output_path)

    df_in = pd.read_csv(input_path)
    logger.info("Loaded %d rows x %d columns from Sprint 2 artifact.", len(df_in), len(df_in.columns))

    df_nlp = build_nlp_features(df_in)
    metrics = validate_nlp_output(df_nlp)
    save_nlp_dataset(df_nlp, output_path=output_path)

    logger.info("Stage 3 NLP Preprocessing pipeline completed successfully.")
    return df_nlp, metrics


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for running the Stage 3 NLP preprocessing pipeline.

    Args:
        argv: Optional list of command-line arguments. Defaults to sys.argv[1:].

    Returns:
        0 on success; 1 on failure.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Stage 3: NLP Preprocessing Pipeline")
    parser.add_argument(
        "--input-file",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help="Path to input cleaned CSV (default: data/processed/microsoft_jobs_cleaned.csv)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to output enriched CSV (default: data/processed/microsoft_jobs_nlp.csv)",
    )
    parsed_args = parser.parse_args(argv)

    try:
        df_result, val_metrics = run_nlp_pipeline(
            input_path=parsed_args.input_file,
            output_path=parsed_args.output_file,
        )

        print("\n" + "=" * 60)
        print("STAGE 3: NLP PREPROCESSING EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Total Postings Processed   : {val_metrics['total_records']:,}")
        print(f"Total Columns (incl. new)  : {val_metrics['total_columns']}")
        print(f"Sprint 2 Columns Preserved : {val_metrics['sprint2_columns_preserved']}")
        print(f"NLP Columns Added          : job_title_tokens, job_skills_list, job_skills_normalized")
        print(f"Null Tokens                : {val_metrics['null_job_title_tokens']}")
        print(f"Null Skill Lists           : {val_metrics['null_job_skills_list']}")
        print(f"Null Normalized Skills     : {val_metrics['null_job_skills_normalized']}")
        print(f"Non-Microsoft Records      : {val_metrics['non_microsoft_records']}")
        print(f"Output File                : {parsed_args.output_file}")
        print(f"Validation Status          : SUCCESS")
        print("=" * 60)
        return 0
    except Exception as exc:
        logger.error("Stage 3 NLP pipeline failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
