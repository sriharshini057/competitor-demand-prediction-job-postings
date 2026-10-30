# CadetX Sprint 3 Deliverable Report: NLP Preprocessing Pipeline

**Project**: Competitor Demand Prediction Using Job Postings  
**Target Subject**: Microsoft (`company_name == "Microsoft"`)  
**Sprint**: Sprint 3 (Stage 3: NLP Preprocessing)  
**Date**: October 29, 2026  
**Status**: COMPLETE — Ready for Review and Submission

---

## 1. Executive Summary & Objective

Sprint 3 implements the NLP text preprocessing pipeline (`src/preprocessing/nlp_pipeline.py`) that transforms raw string fields from the Sprint 2 cleaned dataset (`data/processed/microsoft_jobs_cleaned.csv`, 498 × 32) into analytically usable token-level representations, producing a new enriched artifact (`data/processed/microsoft_jobs_nlp.csv`, 498 × 35).

Sprint 2 stored parsed skill lists and category dicts as Python string representations for CSV persistence (via `str()`). Sprint 3 provides the downstream deserialization and normalization utilities required by Sprints 4–6. All Sprint 1 and Sprint 2 columns are preserved exactly — no existing column is modified.

Primary objectives of Sprint 3:

1. **Text Normalization**: Lower-case, strip punctuation (preserving hyphens), and collapse whitespace from raw `job_title` strings.
2. **Tokenization**: Split normalized text into word-level tokens.
3. **Stop-word Removal**: Filter English stop-words (NLTK) plus a domain-specific set (`"senior"`, `"junior"`, `"microsoft"`, etc.) using a graceful fallback if NLTK corpora are absent.
4. **Lemmatization**: Reduce plural and inflected tokens to base noun forms using NLTK `WordNetLemmatizer`, with graceful fallback.
5. **Skill List Deserialization**: Reverse the CSV string serialization applied by Sprint 2, recovering Python lists from `job_skills_parsed`.
6. **Skill Token Normalization**: Apply consistent lowercasing and punctuation handling to individual skill strings, preserving technically significant characters (`+`, `.`, `-`).
7. **Validation**: Assert zero null values in all new columns and verify Sprint 2 primary identifiers remain intact.

---

## 2. Input and Output File Specifications

| Attribute | Input File | Output File |
| :--- | :--- | :--- |
| **Path** | `data/processed/microsoft_jobs_cleaned.csv` | `data/processed/microsoft_jobs_nlp.csv` |
| **Origin** | Sprint 2 Cleaning (`src/preprocessing/cleaner.py`) | Sprint 3 NLP (`src/preprocessing/nlp_pipeline.py`) |
| **Record Count** | 498 | 498 |
| **Total Columns** | 32 | 35 (3 newly added NLP features) |
| **File Size** | 231,514 bytes (226.09 KB) | 291,906 bytes (285.06 KB) |
| **Git Status** | Ignored by Git (`data/processed/*`) | Ignored by Git (`data/processed/*`) |
| **Target Filter** | `company_name == 'Microsoft'` | `company_name == 'Microsoft'` (100% verified) |

---

## 3. New Columns Added

| Column | dtype (in CSV) | Description |
| :--- | :--- | :--- |
| `job_title_tokens` | str (serialized `List[str]`) | Lemmatized, stop-word-filtered token list from `job_title` |
| `job_skills_list` | str (serialized `List[str]`) | Deserialized Python list recovered from the CSV-stringified `job_skills_parsed` |
| `job_skills_normalized` | str (serialized `List[str]`) | Punctuation-normalized, deduplicated skill list recovered from `job_skills_list` |

> All three columns are stored as string-serialized lists (same pattern as Sprint 2) for CSV compatibility, and can be recovered with `ast.literal_eval()`.

---

## 4. Methodology & Transformation Pipeline

### 4.1 Text Normalization (`normalize_text`)
Accepts a raw job title string and applies:
- Cast to `str`, strip surrounding whitespace
- NFKC Unicode normalization (normalizes fullwidth characters, spaces)
- Normalize various Unicode dashes (en-dash, em-dash, minus) to ASCII hyphen
- Replace hyphens and slashes used as separators (surrounded by whitespace or multiple dashes `--`) with spaces while preserving internal compound hyphens
- Lowercase all characters
- Replace non-technical punctuation with spaces, while strictly preserving technical symbols: hyphens (`-`), forward slashes (`/`), plus signs (`+`), and hash signs (`#`)
- Collapse multiple consecutive whitespace characters to a single space

### 4.2 Tokenization (`tokenize`)
Splits normalized text into individual word tokens, trims boundary punctuation (leading/trailing hyphens, slashes, periods), and filters out standalone punctuation tokens that lack alphanumeric characters. Meaningful acronyms and symbols (`c#`, `c++`, `full-stack`, `m365`) remain intact.

### 4.3 Stop-word Removal (`remove_stopwords`)
Loads the NLTK English stop-word corpus at runtime with a download guard. Falls back to a hard-coded 60-word set if NLTK is unavailable. Accepts an optional caller-supplied extra stop-word set.

Domain stop-words applied in addition to NLTK defaults:

```python
{"microsoft", "senior", "junior", "jr", "sr", "lead", "principal",
 "staff", "associate", "ii", "iii", "iv", "v", "i",
 "1", "2", "3", "4", "5", "6"}
```
Numeric level indicators (`1` through `6`) are filtered as seniority stop-words (matching Roman numerals `i` through `vi`), while alphanumeric acronyms (`m365`) and studio numbers (`Turn 10`) are preserved.

### 4.4 Lemmatization (`lemmatize_tokens`)
Applies NLTK `WordNetLemmatizer` with noun POS tag (`"n"`) to reduce plural and inflected forms (e.g., `"engineers"` → `"engineer"`, `"scientists"` → `"scientist"`). The WordNet corpus is downloaded automatically if absent. Lemmatization gracefully degrades (tokens returned unchanged) if NLTK is unavailable.

### 4.5 Job Title Pipeline (`preprocess_job_title`)
Composes steps 4.1–4.4 into a single function:
`normalize_text` → `tokenize` → `remove_stopwords` → `lemmatize_tokens`

Returns a clean `List[str]` of meaningful role tokens for each job title.

### 4.6 Skill List Deserialization (`deserialize_skill_list`)
Reverses Sprint 2's `str()` serialization using `ast.literal_eval`. Handles edge cases:
- `NaN` / `None` → `[]`
- Empty string → `[]`
- Literal `"[]"` → `[]`
- Malformed string → `[]` (logs debug warning, no exception raised)

### 4.7 Skill Token Normalization & Canonical Aliases (`normalize_skill_token`)
Normalizes individual skill strings for consistent downstream matching:
- Lowercase, strip whitespace
- Remove punctuation except: hyphens (`-`), dots (`.`), plus signs (`+`), hash signs (`#`), and word characters (`c#` and `c++` are preserved; `c#` does not become `c`)
- Collapse internal whitespace
- Apply documented canonical alias mappings:
  - `"golang"` → `"go"`
  - `"mongo"` → `"mongodb"`
  - `"postgres"` → `"postgresql"`
  - `"k8s"` → `"kubernetes"`
  - `"reactjs"` / `"react.js"` → `"react"`
  - `"nodejs"` / `"node"` → `"node.js"`
  - `"sklearn"` → `"scikit-learn"`
  - `"csharp"` / `"c sharp"` → `"c#"`
  - `"cpp"` → `"c++"`

Note: Lemmatization is intentionally **not** applied to skill tokens, which are branded/proper-noun terms (e.g., `"databricks"`, `"pytorch"`, `"power bi"`).

### 4.8 Skill Deduplication per Job (`normalize_skills_list`)
Applies `normalize_skill_token` to each skill in a job posting, discards empty tokens, and eliminates duplicate normalized skills within the posting while strictly preserving original insertion order.

### 4.9 DataFrame Feature Builder (`build_nlp_features`)
Applies all transformations column-wise to the input DataFrame. Raises `KeyError` if required columns (`job_title`, `job_skills_parsed`) are absent. Returns a `.copy()` — the input DataFrame is never mutated.

### 4.10 Windows Console & Execution Robustness
Configures UTF-8 console stream handlers on Windows with fallback error replacement. Uses ASCII log markers (`->`, `...`, `--`, `x`) to prevent `UnicodeEncodeError` across Windows terminals. Provides an explicit `main()` entry point returning exit code `0` on success and `1` on failure with real error reporting.

### 4.11 Orchestrator (`run_nlp_pipeline`)
End-to-end pipeline: load → build → validate → save. Raises `FileNotFoundError` if input does not exist; raises `ValueError` if validation fails.

---

## 5. Observed Metrics from Actual Dataset

### 5.1 `job_title_tokens`

| Metric | Value |
| :--- | :--- |
| Rows with ≥ 1 token | 498 / 498 (100%) |
| Total tokens across all titles | 1,490 |
| Unique tokens | 174 |
| Mean tokens per title | 2.99 |

**Top 12 tokens** (after stop-word removal and lemmatization):

| Token | Count | Token | Count |
|-------|-------|-------|-------|
| data | 283 | applied | 69 |
| engineer | 253 | engineering | 24 |
| scientist | 172 | support | 21 |
| software | 165 | manager | 21 |
| science | 17 | center | 16 |
| analyst | 14 | ai | 14 |

### 5.2 `job_skills_list` (deserialized)

| Metric | Value |
| :--- | :--- |
| Rows with ≥ 1 skill | 393 / 498 (78.9%) |
| Rows with 0 skills | 105 / 498 (21.1%) — matches Sprint 2 `has_skills_specified` |

### 5.3 `job_skills_normalized`

| Metric | Value |
| :--- | :--- |
| Total normalized skill tokens | 2,101 (27 within-job duplicates eliminated) |
| Unique normalized skills | 91 (canonical aliases merged) |

**Top 15 normalized skills:**

| Skill | Count | Skill | Count |
|-------|-------|-------|-------|
| azure | 241 | windows | 58 |
| python | 175 | power bi | 57 |
| sql | 147 | r | 52 |
| c# | 141 | databricks | 51 |
| java | 104 | javascript | 40 |
| spark | 101 | aws | 33 |
| c++ | 77 | mongodb | 33 |
| hadoop | 61 | c | 30 |

> `c#` (141), `c++` (77), and `c` (30) are cleanly separated and distinct. `golang` (6) mapped to `go` (total 22). `mongo` (3) mapped to `mongodb` (total 33).

---

## 6. Validation Results

| Check | Requirement | Result | Status |
| :--- | :--- | :--- | :--- |
| **Output File Presence** | File at `data/processed/microsoft_jobs_nlp.csv` | 285.06 KB generated | **PASS** |
| **Record Count** | Exactly 498 records | 498 records | **PASS** |
| **Column Count** | 35 (32 Sprint 2 + 3 new) | 35 columns | **PASS** |
| **Null `job_title_tokens`** | 0 null values | 0 nulls | **PASS** |
| **Null `job_skills_list`** | 0 null values | 0 nulls | **PASS** |
| **Null `job_skills_normalized`** | 0 null values | 0 nulls | **PASS** |
| **Skill Deduplication** | 0 duplicate skills within any job | 0 duplicates across all 498 rows | **PASS** |
| **C# / C++ Preservation** | Preserve technical names without corruption | C# (141), C++ (77), C (30) verified | **PASS** |
| **Sprint 2 columns preserved** | `job_title`, `job_posted_date`, `company_name` intact | 0 nulls; 100% Microsoft | **PASS** |
| **Non-Microsoft records** | 0 non-Microsoft rows | 0 | **PASS** |
| **Sprint 2 dataset untouched** | `microsoft_jobs_cleaned.csv` unchanged | SHA-256 verified identical | **PASS** |
| **Pipeline Exit Code** | Successful run returns exit code 0 | Exit code 0 verified | **PASS** |
| **Pipeline Error Exit Code** | Failed run returns nonzero exit code | Exit code 1 on missing file verified | **PASS** |

---

## 7. Tests Actually Executed

Automated unit tests were executed using `pytest 9.1.1` on Python 3.13.5 (Windows):

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.7.0
rootdir: Competitor Demand Prediction Using Job Postings
collected 87 items

tests/test_cleaner.py ........                                           [  9%]
tests/test_collector.py .....                                            [ 14%]
tests/test_nlp_pipeline.py ............................................. [ 66%]
.............................                                            [100%]

============================= 87 passed in 3.77s ==============================
```

**Total**: 87 tests — 13 Sprint 1 & 2 (unchanged) + 74 Sprint 3 (new & regression). All passed.

---

## 8. Known Limitations & Downstream Recommendations

1. **No raw job description text in primary dataset**: The `data_jobs.csv` dataset contains structured fields (titles, locations, skill arrays) only — no free-text descriptions. NLP preprocessing targets `job_title` in Sprint 3. For full text-mining analysis, the secondary benchmark corpus (`data/raw/fake_job_postings.csv`, EMSCAD) contains `description` fields and may be leveraged in Sprint 4 for NER benchmarking.

2. **NLTK dependency on corpora download**: The pipeline downloads `stopwords` and `wordnet` corpora on first run if absent. In offline or restricted-network environments, the fallback stop-word set activates automatically. Pre-downloading corpora (`python -m nltk.downloader stopwords wordnet omw-1.4`) is recommended as part of environment setup.

3. **`job_type_skills_parsed` not processed in Sprint 3**: The category-to-skills dict column (`job_type_skills_parsed`) is deserialized in Sprint 3 only for the flat `job_skills_list` (via `job_skills_parsed`). Category-level skill analysis (e.g., `cloud` → `[azure, aws]`) is deferred to Sprint 4 (Skill Extraction) and Sprint 6 (Feature Engineering).
