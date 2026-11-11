
# Sprint 10 Report: Company Similarity Scoring

## 1. Sprint Overview

Sprint 10 focuses on comparing competitor companies based on their technical skill-demand patterns.

The objective is to identify companies with similar skill requirements using cosine similarity, skill overlap analysis, and hierarchical clustering.

## 2. Dataset

**Input file:** `outputs/sprint_08/skill_demand_by_company.csv`

The analysis includes five companies:

- Accenture
- Amazon
- Deloitte
- IBM
- Microsoft

The input dataset contains 613 company-skill records.

After transforming the data, the company-skill matrix contains:

- 5 companies
- 180 unique skills
- Skill demand percentages as feature values

## 3. Methodology

### 3.1 Company-Skill Matrix

A company-by-skill matrix was created using skill demand percentages.

Rows represent companies, and columns represent technical skills.

Missing company-skill combinations were filled with zero.

### 3.2 Cosine Similarity

Cosine similarity was used to measure how closely companies' skill-demand patterns match.

A score closer to 1 indicates more similar skill-demand patterns.

### 3.3 Cosine Distance

Cosine distance was calculated as:

Distance = 1 - Cosine Similarity

A lower distance indicates greater similarity.

### 3.4 Skill Overlap

Shared skills were identified for every company pair.

Jaccard similarity was calculated using:

Jaccard Similarity = Shared Skills / Union of Skills

### 3.5 Hierarchical Clustering

Agglomerative hierarchical clustering was applied using:

- Distance metric: Precomputed cosine distance
- Linkage method: Average linkage
- Number of clusters: 2

## 4. Results

### 4.1 Cosine Similarity Results

| Company Pair | Similarity |
|---|---:|
| Accenture – Deloitte | 0.9584 |
| Amazon – Deloitte | 0.8242 |
| Accenture – Amazon | 0.8201 |
| Accenture – Microsoft | 0.7988 |
| Deloitte – Microsoft | 0.7757 |
| Accenture – IBM | 0.7175 |
| Deloitte – IBM | 0.7177 |
| IBM – Microsoft | 0.6273 |
| Amazon – IBM | 0.6200 |
| Amazon – Microsoft | 0.5744 |

Accenture and Deloitte have the highest cosine similarity, approximately 0.9584.

Amazon and Microsoft have the lowest cosine similarity, approximately 0.5744.

### 4.2 Skill Overlap

The analysis produced 10 company-pair comparisons.

The highest Jaccard similarity was between Accenture and Deloitte:

- Shared skills: 124
- Union of skills: 159
- Jaccard similarity: 0.7799

### 4.3 Clustering Results

| Company | Cluster |
|---|---:|
| Accenture | 1 |
| Amazon | 1 |
| Deloitte | 1 |
| IBM | 2 |
| Microsoft | 1 |

The selected two-cluster configuration placed IBM in Cluster 2 and the other four companies in Cluster 1.

## 5. Visualisations

Two visualisations were generated:

1. `similarity_heatmap.png` – displays pairwise cosine similarity between companies.
2. `company_dendrogram.png` – displays hierarchical relationships between companies based on cosine distance.

## 6. Generated Deliverables

All Sprint 10 outputs are stored in `outputs/sprint_10/`.

| File | Description |
|---|---|
| company_skill_matrix.csv | Company-by-skill percentage matrix |
| company_similarity_matrix.csv | Pairwise cosine similarity |
| company_distance_matrix.csv | Pairwise cosine distance |
| company_skill_overlap.csv | Shared skills and Jaccard similarity |
| company_clusters.csv | Hierarchical clustering assignments |
| similarity_heatmap.png | Similarity heatmap |
| company_dendrogram.png | Hierarchical clustering dendrogram |

Implementation files:

- `src/modeling/similarity.py`
- `src/modeling/run_similarity_analysis.py`
- `tests/test_similarity.py`

## 7. Testing and Validation

Sprint 10 unit tests: 11 passed.

Complete project test suite: 210 passed.

The generated matrices were checked for their dimensions and similarity values.

No test failures were reported.

## 8. Limitations

- The analysis depends on the available job-posting dataset.
- Skill extraction and normalization may affect the accuracy of comparisons.
- Similarity reflects technical skill-demand patterns, not overall business competition.
- The clustering output depends on the selected number of clusters and linkage method.
- Results should not be interpreted as market share or company performance.

## 9. Conclusion

Sprint 10 successfully implemented company similarity scoring using cosine similarity, cosine distance, Jaccard skill overlap, and hierarchical clustering.

The analysis identified Accenture and Deloitte as the most similar pair based on their skill-demand profiles.

All seven expected output files were generated, and all 210 project tests passed.

Sprint 10 completed successfully.
