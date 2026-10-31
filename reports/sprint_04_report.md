# CadetX Sprint 4 Deliverable Report: Named Entity Recognition (NER) & Skill Extraction Pipeline

- **Project**: Competitor Demand Prediction Using Job Postings
- **Target Subject**: Microsoft (`company_name == "Microsoft"`)
- **Sprint**: Sprint 4 (Stage 4: spaCy-Based NER and Skill Extraction)
- **Date**: October 31, 2026
- **Status**: COMPLETE — Ready for Review and Submission
---

## 1. Executive Summary & Objective

Sprint 4 implements an end-to-end Named Entity Recognition (NER) and deterministic skill extraction pipeline for Microsoft job postings. Building directly on the Sprint 3 NLP-preprocessed dataset (`data/processed/microsoft_jobs_nlp.csv`, 498 rows × 35 columns), Sprint 4 enriches each job posting with structured entity annotations and standardized skill taxonomy metadata, producing the new additive artifact (`data/processed/microsoft_jobs_skills.csv`, 498 rows × 40 columns).

All 35 columns from Sprints 1, 2, and 3 are strictly preserved without modification. Five new analytical features are introduced to enable downstream relational storage (Sprint 5) and time-lagged feature engineering (Sprint 6).

### Primary Objectives Delivered:
1. **Named Entity Recognition (NER)**: Integrated `spaCy` using the `en_core_web_sm` model to extract named entities (organizations, locations, nationalities, products, and persons) with explicit handling of missing model states.
2. **Deterministic Skill Extraction**: Implemented phrase-level extraction via spaCy's `PhraseMatcher` and token-level `Matcher`, ensuring exact token boundary enforcement and eliminating substring false positives.
3. **Skill Taxonomy & Category Traceability**: Defined an 8-category skill dictionary spanning Programming Languages, Data Analysis, Machine Learning, Data Engineering, Databases, Cloud, Development & Tools, and Other Relevant Skills.
4. **Canonical Alias Normalization**: Formulated explicit, testable mapping rules to resolve abbreviations and informal variants (e.g., `sklearn` → `Scikit-learn`, `postgres` → `PostgreSQL`, `ms sql server` → `Microsoft SQL Server`, `k8s` → `Kubernetes`).
5. **Deduplication & Multiword Phrase Preservation**: Preserved multiword technical phrases (e.g., `Apache Spark`, `Microsoft Azure`, `Power BI`) and prevented duplicate skills and entities within each posting.
6. **Robust Text Handling & Composite Representation**: Dynamically handled missing free-text descriptions in the primary Luke Barousse dataset via structured composite text formatting, while supporting arbitrary free-text descriptions.
7. **Quality Assurance & Verification**: Executed 127 automated tests (87 existing Sprint 1–3 regression tests + 40 new Sprint 4 tests), achieving a 100% pass rate.

---

## 2. Tools & Libraries

The Sprint 4 pipeline relies exclusively on free, open-source, and reproducible tools:

| Tool / Library | Version | Role in Sprint 4 |
| :--- | :--- | :--- |
| **Python** | 3.13.5 | Core execution runtime |
| **spaCy** | 3.8.18 | Natural language processing, tokenization, phrase matching, and entity recognition |
| **en_core_web_sm** | 3.8.0 | Pretrained English statistical NLP pipeline (tagger, parser, NER) |
| **Pandas** | 3.0.3 | Tabular data manipulation, CSV I/O, column-wise feature building |
| **pytest** | 9.1.1 | Unit, regression, and integration testing framework |
| **json** | Standard Library | Structured CSV column serialization (`json.dumps` / `json.loads`) |

---

## 3. NER Implementation

### 3.1 Architecture & Model Loading (`src/skills/ner_extractor.py`)
Named Entity Recognition is isolated in `src.skills.ner_extractor.NamedEntityExtractor`. The module uses spaCy's `en_core_web_sm` pipeline.

- **Non-Silent Dependency Guard**: Rather than silently assuming the language model exists or fabricating synthetic fallback entities, `load_spacy_model()` raises a descriptive `ModelNotFoundError` with exact shell installation instructions (`python -m spacy download en_core_web_sm`).
- **Targeted Entity Labels**: Extraction captures entity classes relevant to corporate competitive intelligence:
  - `ORG`: Organizations, corporations, and agencies (e.g., `Microsoft`, `Google`, `OpenAI`).
  - `GPE`: Geopolitical entities, including cities, states, and countries (e.g., `Redmond`, `Dublin`, `Washington`, `India`).
  - `LOC`: Non-GPE geographical locations and regions.
  - `PERSON`: Spans the model labels as persons; this label does not verify that a span is a real person's name.
  - `PRODUCT`: Branded technological systems or products.
  - `NORP`: Nationalities and geopolitical groups.
- **Entity Deduplication**: Entities within a single job posting are deduplicated based on `(text.lower(), label)`, preserving original casing on first appearance.
- **Pretrained NER Scope Disclaimer**: Pretrained general-domain NER models are trained on OntoNotes 5.0 and news corpora; they are **not** specialized technical skill extractors. For instance, pretrained NER may mislabel informal tech acronyms (e.g., labeling `k8s` as `PERSON` or `PyTorch` as `ORG`). Technical competencies are therefore handled independently by the deterministic `SkillExtractor`.
- **Entity Interpretation Caveat**: These are model-detected labels and may include false positives; `PERSON` spans are not independently verified as real people. The composite text includes `Company: Microsoft`, so Microsoft appearing as `ORG` in 498 / 498 rows is only a consistency check and is not evidence of NER accuracy.

---

## 4. Skill Extraction Methodology

### 4.1 spaCy PhraseMatcher & Matcher (`src/skills/skill_extractor.py`)
Deterministic phrase matching is implemented via `src.skills.skill_extractor.SkillExtractor`.

1. **PhraseMatcher with `attr="LOWER"`**: Enables case-insensitive matching across single-word and multi-word terms while strictly respecting token boundaries. Substring false positives (such as matching `go` inside `going` or `r` inside `program`) are structurally prevented.
2. **Specialized Token-level `Matcher` Patterns**:
   - Symbols and punctuation (`C#`, `C++`, `CI/CD`): Custom token patterns capture terms with non-alphanumeric symbols that general word tokenizers split.
   - Single-letter skills (`R`, `C`): `R` is restricted to uppercase standalone tokens or sentence-boundary tokens (`R.`). `C` is restricted to explicit language contexts (`C/C++`, `C and C++`, `C language`).
3. **Longest-Span Resolution (`spacy.util.filter_spans`)**: When multi-word phrases overlap with nested sub-phrases (e.g., `Microsoft Azure` vs. `Azure`, or `Microsoft SQL Server` vs. `SQL`), `filter_spans` preserves the longest specific phrase.
4. **Context & Part-of-Speech Validation**: Polysemous words that double as common English verbs (e.g., `go` as a verb vs. `Go` language, or `excel` as a verb in "must excel in communication" vs. Microsoft `Excel`) are checked against spaCy's POS tagger. When tagged as `VERB`, the match is rejected.

---

## 5. Skill Taxonomy & Canonical Normalization Rules

The skill dictionary groups competencies across 8 transparent categories:

```text
A. Programming Languages : Python, Java, C++, C#, C, JavaScript, TypeScript, SQL, R, Scala, Go
B. Data Analysis         : Pandas, NumPy, Matplotlib, Seaborn, Excel, Power BI, Tableau, Power Query, DAX
C. Machine Learning      : Scikit-learn, TensorFlow, PyTorch, Keras, XGBoost, LightGBM, CatBoost
D. Data Engineering      : Apache Spark, PySpark, Hadoop, Kafka, Airflow, ETL, ELT, Data Warehousing, Snowflake, Databricks, BigQuery, dbt
E. Databases             : MySQL, PostgreSQL, MongoDB, SQLite, Microsoft SQL Server, Oracle, Redis, Cassandra, NoSQL
F. Cloud                 : AWS, Microsoft Azure, Google Cloud Platform, Azure Data Factory, Amazon S3, Azure Synapse, Azure DevOps
G. Development & Tools   : Git, GitHub, Docker, Kubernetes, REST API, FastAPI, Flask, Linux, CI/CD, Jenkins
H. Other Relevant Skills : Data Modeling, Data Cleaning, Data Visualization, Statistics, NLP, Deep Learning, Artificial Intelligence, Business Intelligence
```

### 5.1 Documented Normalization Rules
Informal abbreviations, framework shorthands, and legacy names are normalized to official industry standards:

| Raw / Informal Mention | Canonical Form | Primary Category |
| :--- | :--- | :--- |
| `sklearn`, `scikitlearn`, `scikit-learn` | **Scikit-learn** | Machine Learning |
| `pytorch`, `torch` | **PyTorch** | Machine Learning |
| `postgres`, `postgresql` | **PostgreSQL** | Databases |
| `ms sql server`, `mssql`, `sql server` | **Microsoft SQL Server** | Databases |
| `azure`, `ms azure`, `microsoft azure` | **Microsoft Azure** | Cloud |
| `gcp`, `google cloud`, `google cloud platform` | **Google Cloud Platform** | Cloud |
| `aws`, `amazon web services` | **AWS** | Cloud |
| `adf`, `azure data factory` | **Azure Data Factory** | Cloud |
| `spark`, `apache spark` | **Apache Spark** | Data Engineering |
| `pyspark` | **PySpark** | Data Engineering |
| `hadoop`, `apache hadoop` | **Hadoop** | Data Engineering |
| `kafka`, `apache kafka` | **Kafka** | Data Engineering |
| `k8s`, `kubernetes` | **Kubernetes** | Development & Tools |
| `csharp`, `c sharp`, `c#` | **C#** | Programming Languages |
| `cpp`, `c++` | **C++** | Programming Languages |
| `golang`, `go` | **Go** | Programming Languages |
| `js`, `javascript` | **JavaScript** | Programming Languages |
| `ts`, `typescript` | **TypeScript** | Programming Languages |
| `powerbi`, `power bi` | **Power BI** | Data Analysis |
| `rest`, `rest api`, `restful`, `restful api` | **REST API** | Development & Tools |
| `dwh`, `data warehouse`, `data warehousing` | **Data Warehousing** | Data Engineering |
| `dl`, `deep learning` | **Deep Learning** | Other Relevant Skills |
| `nlp`, `natural language processing` | **NLP** | Other Relevant Skills |
| `ml`, `machine learning` | **Machine Learning** | Machine Learning |

---

## 6. Input & Output Dataset Specifications

| Attribute | Input File (Sprint 3) | Output File (Sprint 4) |
| :--- | :--- | :--- |
| **Path** | `data/processed/microsoft_jobs_nlp.csv` | `data/processed/microsoft_jobs_skills.csv` |
| **Origin** | Sprint 3 NLP Pipeline (`nlp_pipeline.py`) | Sprint 4 NER & Skills (`src/skills/extractor.py`) |
| **Record Count** | 498 records | 498 records (100% row count preserved) |
| **Total Columns** | 35 columns | 40 columns (35 Sprint 3 + 5 new Sprint 4) |
| **File Size** | 291,906 bytes (285.06 KB) | 465,928 bytes (455.01 KB) |
| **Target Filter** | `company_name == 'Microsoft'` | `company_name == 'Microsoft'` (100% verified) |
| **Git Status** | Not ignored; explicitly allowed by `.gitignore` | Not ignored; explicitly allowed by `.gitignore` |

### 6.1 Description of Newly Added Columns

| Column | dtype (in CSV) | Content Description |
| :--- | :--- | :--- |
| `extracted_entities` | str (JSON) | Serialized `List[Dict[str, str]]` with deduplicated entity mentions (`text` and `label`) |
| `extracted_skills` | str (JSON) | Serialized `List[str]` of deduplicated canonical skill names |
| `skill_categories` | str (JSON) | Serialized `Dict[str, List[str]]` mapping skill categories to matched skills |
| `skill_count` | int | Non-negative integer count of unique skills extracted from the posting |
| `entity_count` | int | Non-negative integer count of unique named entities extracted |

> All structured columns are serialized as standard JSON strings via `json.dumps(..., ensure_ascii=False)`. They can be deserialized directly using `json.loads` or `pd.read_csv`.

---

## 7. Observed Extraction Statistics from Actual Dataset

The pipeline was executed against all 498 Microsoft job postings. The following metrics were derived directly from the generated artifact:

### 7.1 Global Overview
- **Total Postings Processed**: 498
- **Postings with ≥ 1 Skill**: 358 / 498 (71.89%)
- **Total Skills Extracted**: 1,686 mentions
- **Unique Canonical Skills**: 47 distinct skills
- **Average Skills per Posting**: 3.39
- **Total Entities Extracted**: 2,056 mentions
- **Average Entities per Posting**: 4.13
- **Microsoft ORG Consistency Check**: Microsoft appears as `ORG` in 498 / 498 postings (100.0%); the composite text includes `Company: Microsoft`, so this is not independent evidence of NER accuracy.

### 7.2 Top 15 Extracted Skills at Microsoft (2023)

| Rank | Canonical Skill | Category | Frequency | % of Postings (N=498) |
| :---: | :--- | :--- | :---: | :---: |
| 1 | **Microsoft Azure** | Cloud | 243 | 48.80% |
| 2 | **Python** | Programming Languages | 175 | 35.14% |
| 3 | **SQL** | Programming Languages | 148 | 29.72% |
| 4 | **C#** | Programming Languages | 141 | 28.31% |
| 5 | **Java** | Programming Languages | 104 | 20.88% |
| 6 | **Apache Spark** | Data Engineering | 101 | 20.28% |
| 7 | **C++** | Programming Languages | 77 | 15.46% |
| 8 | **Hadoop** | Data Engineering | 61 | 12.25% |
| 9 | **Power BI** | Data Analysis | 57 | 11.45% |
| 10 | **Databricks** | Data Engineering | 51 | 10.24% |
| 11 | **JavaScript** | Programming Languages | 40 | 8.03% |
| 12 | **AWS** | Cloud | 33 | 6.63% |
| 13 | **PyTorch** | Machine Learning | 31 | 6.22% |
| 14 | **Kubernetes** | Development & Tools | 28 | 5.62% |
| 15 | **TensorFlow** | Machine Learning | 27 | 5.42% |

### 7.3 Skill Distribution by Category

| Category | Total Skills Extracted | Share of Skill Footprint |
| :--- | :---: | :---: |
| **Programming Languages** | 712 | 42.23% |
| **Cloud** | 294 | 17.44% |
| **Data Engineering** | 259 | 15.36% |
| **Data Analysis** | 126 | 7.47% |
| **Databases** | 109 | 6.47% |
| **Development & Tools** | 85 | 5.04% |
| **Machine Learning** | 80 | 4.75% |
| **Other Relevant Skills** | 21 | 1.25% |
| **Total** | **1,686** | **100.00%** |

### 7.4 Named Entity Breakdown

| Entity Label | Meaning | Frequency | Top Examples |
| :--- | :--- | :---: | :--- |
| **GPE** | Geopolitical Entities (Countries, Cities) | 804 | India (107), Telangana (56), China (46), Dublin (30), Ireland (30), Washington (25) |
| **ORG** | Organizations & Companies | 680 | Microsoft (498), GCP (18), GA (10), Pandas (9) |
| **PERSON** | Model-detected PERSON spans (may include false positives; not verified people) | 563 | Examples are model outputs and are not confirmed real people |
| **PRODUCT** | Commercial Products | 5 | Software platforms |
| **NORP** | Nationalities / Political Groups | 4 | Regional classifications |

---

## 8. Validation Results

| Validation Check | Requirement | Result | Status |
| :--- | :--- | :--- | :--- |
| **Output File Exists** | `data/processed/microsoft_jobs_skills.csv` | 455.01 KB generated on disk | **PASS** |
| **Record Count** | Exactly 498 records | 498 records | **PASS** |
| **Column Count** | Exactly 40 columns (35 Sprint 3 + 5 new) | 40 columns | **PASS** |
| **Original Columns Preserved** | 100% of Sprint 3 columns intact | All 35 columns present and identical | **PASS** |
| **Null Values in New Features** | 0 nulls across all 5 new columns | 0 nulls verified | **PASS** |
| **JSON Serializability** | Parseable via `json.loads` without error | 100% valid JSON strings across all rows | **PASS** |
| **Strict Competitor Scope** | 100% Microsoft postings | 0 non-Microsoft records | **PASS** |
| **Sprint 3 Output Untouched** | `microsoft_jobs_nlp.csv` unmodified | Read-only input verified | **PASS** |
| **CLI Exit Code** | Exit code 0 on successful pipeline completion | Exit code 0 verified | **PASS** |

---

## 9. Testing Methodology & Actual Test Results

Automated tests were executed using `pytest 9.1.1` on Python 3.13.5 (Windows):

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.7.0
rootdir: Competitor Demand Prediction Using Job Postings
collected 127 items

tests/test_cleaner.py ........                                           [  6%]
tests/test_collector.py .....                                            [ 10%]
tests/test_ner_extractor.py .........                                    [ 17%]
tests/test_nlp_pipeline.py ............................................. [ 52%]
.............................                                            [ 75%]
tests/test_skill_extractor.py .....................                       [ 92%]
tests/test_skills_pipeline.py ..........                                  [100%]

============================ 127 passed in 27.21s =============================
```

### Breakdown of Test Suite:
- **Sprint 1 (Data Collection)**: 5 tests passed (`tests/test_collector.py`).
- **Sprint 2 (Data Cleaning & Imputation)**: 8 tests passed (`tests/test_cleaner.py`).
- **Sprint 3 (NLP Preprocessing)**: 74 tests passed (`tests/test_nlp_pipeline.py`).
- **Sprint 4 (NER Extractor)**: 9 tests passed (`tests/test_ner_extractor.py`).
- **Sprint 4 (Skill Extractor)**: 21 tests passed (`tests/test_skill_extractor.py`).
- **Sprint 4 (Pipeline Integration)**: 10 tests passed (`tests/test_skills_pipeline.py`).
- **Total**: **127 passed, 0 failed, 0 skipped**.

---

## 10. Known Limitations

1. **Absence of Unstructured Job Descriptions in Raw Data**: The primary dataset (`data_jobs.csv`) provides structured arrays rather than full-length narrative job descriptions. The pipeline bridges this by synthesizing a structured composite text representation (`Company: Microsoft. Job Title: ... Location: ... Skills: ...`). When full narrative descriptions are provided (such as in unit test fixtures or EMSCAD secondary benchmarks), the pipeline automatically prioritizes the free-text description.
2. **Ambiguous Technical Acronyms**: Terms like `Go` and `Excel` require POS-tagging guards to avoid false-positive matches with common English verbs. Highly ambiguous single letters (e.g. `C`) require language-adjacent context (`C/C++`, `C language`) to ensure precision.
3. **Pretrained General NER Noise**: As noted in Section 3, off-the-shelf general NER pipelines categorize technical terms unpredictably (e.g., labeling framework names as organizations or persons). Deterministic dictionary matching remains the authoritative extraction method for technical competencies.

---

## 11. Pipeline Execution Guide

All commands are executed from the repository root in PowerShell:

### 1. Environment Setup & Language Model Download
```powershell
# Activate project virtual environment
.\venv\Scripts\Activate.ps1

# Install requirements (including spaCy)
pip install -r requirements.txt

# Download required spaCy English model
python -m spacy download en_core_web_sm
```

### 2. Execute Sprint 4 Pipeline
```powershell
python src/skills/extractor.py
```
- **Default Input**: `data/processed/microsoft_jobs_nlp.csv`
- **Default Output**: `data/processed/microsoft_jobs_skills.csv`

### 3. Run Complete Automated Test Suite
```powershell
pytest -v
```

---

## 12. Downstream Roadmap (Sprint 5 & Beyond)

With skill extraction and entity tagging complete:
- **Sprint 5 (Database Storage)**: Design relational SQLite schema with dedicated tables for jobs, entities, and skills (`jobs`, `entities`, `skills`, `job_skills`), enabling SQL indexing and relational aggregations.
- **Sprint 6 (Feature Engineering)**: Compute skill co-occurrence matrices, temporal hiring velocity indicators, and rolling demand statistics.
- **Sprint 7 (Hiring Trend Analysis)**: Analyze quarterly demand shifts across cloud (Azure), programming languages (Python, C#, Java), and data engineering tools (Spark, Databricks).
