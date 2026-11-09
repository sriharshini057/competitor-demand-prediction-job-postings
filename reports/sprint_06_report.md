# Sprint 6 Report – Feature Engineering

## 1. Objective

The objective of Sprint 6 was to transform the cleaned Microsoft job-posting data into structured weekly demand features and weekly skill-demand data for future demand analysis and forecasting.

## 2. Input Dataset

- File: `data/processed/microsoft_jobs_skills.csv`
- Company: Microsoft
- Total job postings: 498
- Time period: 2023
- Weekly coverage: 52 weeks

## 3. Feature Engineering Implementation

Implemented in `src/features/feature_builder.py`.

### 3.1 Weekly Demand Features

Created `data/processed/weekly_demand_features.csv` containing:

- Weekly job posting count
- Year and week information
- Month and quarter
- Week of year
- Demand lag features (1, 2 and 4 weeks)
- Four-week rolling mean
- Four-week rolling standard deviation

Missing weeks were included with zero job postings to maintain continuous weekly observations.

Rolling statistics use previous weeks' demand to avoid future-data leakage.

### 3.2 Weekly Skill Demand

Created `data/processed/weekly_skill_demand.csv` containing:

- Week start date
- Year-week identifier
- Skill name
- Weekly skill posting count
- Total weekly job postings
- Skill demand share

Each skill is counted at most once per job posting.

## 4. Output Dataset Validation

| Metric | Result |
|---|---:|
| Weekly demand dataset rows | 52 |
| Weekly demand dataset columns | 12 |
| Total job postings | 498 |
| Weekly skill-demand rows | 801 |
| Unique skills | 47 |
| Missing week dates | 0 |
| Missing skill names | 0 |
| Duplicate weeks | 0 |
| Duplicate week-skill pairs | 0 |

All validation checks passed.

## 5. Automated Testing

Created `tests/test_feature_builder.py` with 11 tests covering:

- JSON and Python-format skill-list parsing
- Empty skill-list handling
- Weekly demand aggregation
- Lag feature calculation
- Rolling mean calculation
- Weekly skill-demand calculation
- Skill-count validation
- Missing-column validation
- Invalid-date validation

Complete project test suite:

- Total tests: 180
- Passed: 180
- Failed: 0

## 6. Technologies Used

- Python
- Pandas
- NumPy
- Pytest
- CSV

## 7. Limitations

- The dataset contains Microsoft job postings only.
- The dataset covers 52 weekly observations from 2023.
- The available history is limited for reliable long-term forecasting.
- The engineered features are prepared for future modeling; no forecasting model was developed in this sprint.

## 8. Conclusion

Sprint 6 successfully generated weekly demand features and weekly skill-demand datasets from the processed Microsoft job postings.

Both output datasets passed validation, and all 180 project tests passed. The engineered datasets are ready for subsequent analysis and modeling.
