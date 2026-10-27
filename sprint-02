# Competitor Demand Prediction Using Job Postings

**CadetX Virtual Internship Project**

## 1. Project Overview

Competitor Demand Prediction Using Job Postings is a data engineering and analytics project that analyzes job postings to understand hiring demand, job requirements, and skill trends.

The project uses job-posting data from the [Luke Barousse Data Jobs dataset](https://github.com/lukebarousse/data_jobs). The initial analysis focuses exclusively on job postings where the company name matches **Microsoft**.

The project follows a structured data pipeline covering data collection, data cleaning, feature engineering, exploratory data analysis, and future demand analysis.

## 2. Objectives

- Collect and validate job-posting data.
- Filter records for Microsoft using the company name.
- Clean missing, inconsistent, and duplicate data.
- Normalize posting dates and derive time-based features.
- Standardize salary information and job locations where data permits.
- Extract and analyze skills mentioned in job postings.
- Identify hiring patterns and in-demand technical skills.
- Develop a reproducible and testable data pipeline.

## 3. Dataset

**Source:** [Luke Barousse — Data Jobs](https://github.com/lukebarousse/data_jobs)

**Original dataset:** `data_jobs.csv`

The project uses the company-name filter:

`company_name == "Microsoft"`

The initial collection stage produced a filtered dataset containing **498 rows and 17 columns**, according to the project's Sprint 1 validation report.

The cleaned dataset contains **498 rows and 32 columns**, according to the Sprint 2 implementation results.

These figures describe the current project outputs and may change if the source dataset or pipeline is updated.

> **Data privacy and repository size:** Raw and processed CSV files are excluded from Git. They must be obtained or generated locally by running the pipeline. Do not upload the original dataset or generated CSV files to this public repository.

## 4. Technology Stack

### Implemented

- **Python** — pipeline implementation
- **Pandas** — data manipulation and cleaning
- **NumPy** — numerical and data operations
- **pytest** — automated testing
- **Git and GitHub** — version control

### Planned for later sprints

- **scikit-learn** — predictive modelling
- **NLTK or spaCy** — text and skill analysis
- **Matplotlib** — data visualization
- **SQLite and SQL** — structured storage and querying
- **Streamlit** — interactive dashboard, if included in the final implementation

Planned technologies will be added as the corresponding project stages are implemented.

## 5. Project Structure

```text
Competitor-Demand-Prediction-Using-Job-Postings/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── collection/
│   │   └── collector.py
│   └── preprocessing/
│       └── cleaner.py
│
├── tests/
│   ├── test_collector.py
│   └── test_cleaner.py
│
├── reports/
│   ├── dataset_validation_report.md
│   └── sprint_02_report.md
│
├── .gitignore
├── requirements.txt
└── README.md
```

The `data/` directories hold local data files and may contain `.gitkeep` files so that the directory structure can be maintained in Git. Raw and processed datasets should remain untracked.

## 6. Sprint Progress

### Sprint 1 — Data Collection and Validation

**Status: Completed**

Implemented components:

- Data collection and filtering logic in `src/collection/collector.py`.
- Automated tests in `tests/test_collector.py`.
- Dataset validation documentation in `reports/dataset_validation_report.md`.
- Microsoft-only filtering using the company-name field.

The Sprint 1 validation report documents the collection results and dataset checks.

### Sprint 2 — Data Cleaning, Imputation, and Date Normalization

**Status: Implemented locally; verify repository submission status**

Implemented components:

- Cleaning pipeline in `src/preprocessing/cleaner.py`.
- Automated cleaning tests in `tests/test_cleaner.py`.
- Sprint documentation in `reports/sprint_02_report.md`.

The cleaning pipeline covers:

- Handling missing values.
- Standardizing company names and locations.
- Normalizing posting dates.
- Creating time-based features.
- Annualizing salary information when the available data supports it.
- Parsing skill data.
- Removing duplicate records.
- Validating the cleaned dataset schema.

The current cleaning implementation produces a dataset reported as 498 rows and 32 columns.

### Remaining planned sprints

The following stages are proposed roadmap items, not claims of completed work.

| Sprint | Planned deliverable |
|---|---|
| 3 | Feature engineering and data quality improvements |
| 4 | Exploratory data analysis |
| 5 | Job role and location analysis |
| 6 | Skill extraction and normalization |
| 7 | SQL database integration |
| 8 | Demand trend analysis |
| 9 | Predictive modelling |
| 10 | Model evaluation and validation |
| 11 | Dashboard or reporting layer |
| 12 | Final integration, testing, and documentation |

The roadmap may be refined as internship requirements and implementation progress become clearer.

## 7. Setup and Installation

### Prerequisites

- Python installed on your system.
- Git installed on your system.
- Access to the source dataset.

### Step 1: Clone the repository

Replace the placeholder below with your actual GitHub repository URL.

```bash
git clone <YOUR_EXISTING_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER>
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

For Windows Command Prompt:

```cmd
venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Prepare the source dataset

Download `data_jobs.csv` from the official dataset repository and place it in the location expected by `src/collection/collector.py`.

Check the collector's configuration and command-line instructions before running it, because the exact input path and invocation depend on the implemented code.

### Step 5: Run the collection pipeline

Run the collector using the command or entry point defined in `src/collection/collector.py`.

### Step 6: Run the cleaning pipeline

Run the cleaning script using the input and output paths defined in `src/preprocessing/cleaner.py`.

The expected cleaned output is:

`data/processed/microsoft_jobs_cleaned.csv`

The raw and processed datasets are generated locally and are not committed to Git.

## 8. Testing

Run the automated tests from the repository root:

```bash
python -m pytest -v
```

The combined Sprint 1 and Sprint 2 test suite previously passed **13 tests**: five collector tests and eight cleaner tests.

Run the command again after any code changes to verify the current state.

## 9. Data Quality and Reproducibility

The project uses automated tests and validation reports to help verify pipeline behavior.

Important considerations:

- The Microsoft filter uses the company-name field. It does not independently establish corporate ownership or resolve subsidiaries and aliases.
- Missing values and salary fields are handled according to the available source data and cleaning rules.
- Derived date and salary features depend on the source fields being available and interpretable.
- Results may change when the source dataset is updated.
- Raw data, processed data, credentials, and other private files must not be committed to the public repository.

## 10. Expected Outcomes

The completed project aims to provide:

- A reproducible job-posting data pipeline.
- A validated and cleaned Microsoft job-posting dataset.
- Structured features for subsequent analysis.
- Insights into job roles, technical skills, locations, and hiring trends.
- A foundation for future demand analysis and predictive modelling.

These are project objectives; final analytical findings will be documented after the relevant stages are implemented.

## 11. Author and Internship Context

**Project:** Competitor Demand Prediction Using Job Postings  
**Program:** CadetX Virtual Internship  
**Focus areas:** Data Engineering, Data Cleaning, Feature Engineering, and Job Market Analytics

This repository documents the implementation and progress of the project sprint by sprint.

## 12. Acknowledgements

Thanks to [Luke Barousse](https://github.com/lukebarousse/data_jobs) for providing the public Data Jobs dataset used as the project's data source.

---

*Last updated: October 2026*
