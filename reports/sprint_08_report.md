# Sprint 8 – Competitor Comparison and Demand Benchmarking

## 1. Objective

The objective of Sprint 8 is to compare job-posting demand across five selected technology companies: Microsoft, Amazon, IBM, Accenture, and Deloitte. The analysis identifies differences in skill requirements, job roles, and geographical hiring patterns.

## 2. Dataset

- **Source:** Luke Barousse – `data_jobs.csv`
- **Dataset size:** 785,741 job postings
- **Selected companies:** Microsoft, Amazon, IBM, Accenture, Deloitte
- **Selected postings:** 6,450
- **Dataset period:** January 2023 – December 2023

Microsoft is used as the baseline company because it was the focus of the earlier project sprints.

## 3. Methodology

The following steps were performed:

1. Loaded the original job-postings dataset in chunks.
2. Filtered postings for the five selected companies.
3. Parsed structured skill lists using Python's `ast.literal_eval`.
4. Normalized skill names and added Sprint 8-specific skill mappings without modifying the original Sprint 4 taxonomy.
5. Calculated company-level posting summaries and skill-data coverage.
6. Compared skill demand and job-role distributions.
7. Analyzed country-wise posting distributions.
8. Performed a separate India-focused comparison.
9. Generated CSV outputs and visualizations using Pandas and Matplotlib.

## 4. Company Summary

| Company | Job Postings | Skill Data Available | Skill Coverage |
|---|---:|---:|---:|
| Accenture | 1,699 | 1,016 | 59.80% |
| Amazon | 1,270 | 1,097 | 86.38% |
| Deloitte | 1,694 | 1,558 | 91.97% |
| IBM | 1,289 | 1,247 | 96.74% |
| Microsoft | 498 | 393 | 78.92% |

A total of 6,450 postings were selected for comparison.

## 5. Global Analysis

### Skill Demand

- Python and SQL appear frequently across the selected companies.
- AWS is particularly prominent in Amazon postings.
- Microsoft Azure is prominent in Microsoft postings.
- IBM Cloud is the most frequently identified skill in IBM postings.
- Deloitte has substantial demand for Python, SQL, AWS, and R.

### Job Role Demand

- Data Engineer is the leading role for Amazon, IBM, and Accenture.
- Data Scientist is the leading role for Deloitte.
- Software Engineer is the leading role for Microsoft.

### Country Distribution

- Deloitte has the largest number of selected postings in the United States.
- IBM and Microsoft have substantial posting counts in India.
- Accenture has a geographically distributed posting pattern.

## 6. India-Focused Analysis

The India analysis contains 816 postings across the five companies.

| Company | India Postings | Skill Data Available | Skill Coverage |
|---|---:|---:|---:|
| Accenture | 68 | 46 | 67.65% |
| Amazon | 122 | 114 | 93.44% |
| Deloitte | 153 | 143 | 93.46% |
| IBM | 358 | 344 | 96.09% |
| Microsoft | 115 | 84 | 73.04% |

### Key Findings

- IBM has the highest number of selected India postings, with 358.
- Data Engineer is the leading role in IBM, Amazon, and Deloitte India postings.
- Data Scientist is the leading role in Accenture and Microsoft India postings.
- Python and SQL are important skills across multiple companies.
- IBM Cloud has particularly high demand in IBM postings.
- Microsoft Azure is prominent in Microsoft's India postings.

## 7. Generated Outputs

### CSV Files

- `company_summary.csv`
- `skill_demand_by_company.csv`
- `role_demand_by_company.csv`
- `country_demand_by_company.csv`
- `india_company_summary.csv`
- `india_role_demand_by_company.csv`
- `india_skill_demand_by_company.csv`

### Visualizations

- `global_skill_demand.png`
- `global_role_demand.png`
- `country_distribution.png`
- `india_skill_demand.png`
- `india_role_demand.png`

All outputs are stored in `outputs/sprint_08/`.

## 8. Testing and Validation

- Added 11 automated tests in `tests/test_competitor.py`.
- Tested skill parsing and normalization.
- Tested additional skill mappings and ambiguous skill exclusion.
- Tested company summaries and skill-demand calculations.
- Tested role and country comparisons.
- Tested India-specific analysis.
- Full project test suite: **194 tests passed**.

## 9. Limitations

- The analysis uses 2023 job-posting data and does not represent current hiring demand.
- Job-posting counts are not the same as actual employee hiring numbers.
- Skill-demand percentages use only postings with available skill data as their denominator.
- Skill coverage varies between companies and should be considered when comparing skill percentages.
- The five companies are selected for benchmarking; they are not necessarily direct competitors in every business area.
- The India analysis is a subset of the global dataset.

## 10. Conclusion

Sprint 8 successfully compares job-posting demand across five selected companies. The analysis identifies differences in technical skills, job roles, and geographical distributions, with additional insights for India.

The generated datasets and visualizations provide a foundation for understanding competitor demand patterns and comparing the skills requested by different employers.