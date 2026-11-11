
"""Company similarity scoring module.

Sprint 10: Calculate competitor similarity matrices,
skill overlap, and hierarchical clustering.
"""

from itertools import combinations

import numpy as np
import pandas as pd

from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity


REQUIRED_COLUMNS = {
    "company_name",
    "skill",
    "skill_demand_pct",
}


def build_company_skill_matrix(skill_data):
    """Build a company-by-skill matrix using skill demand percentages."""

    missing = REQUIRED_COLUMNS - set(skill_data.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if skill_data.empty:
        raise ValueError("Skill demand dataset is empty.")

    data = skill_data.copy()

    data["company_name"] = data["company_name"].astype("string").str.strip()
    data["skill"] = data["skill"].astype("string").str.strip()

    data = data.dropna(subset=["company_name", "skill"])

    data = data[
        data["company_name"].ne("")
        & data["skill"].ne("")
    ]

    if data.empty:
        raise ValueError("No valid company-skill records found.")

    data["skill_demand_pct"] = pd.to_numeric(
        data["skill_demand_pct"],
        errors="raise",
    )

    if not np.isfinite(data["skill_demand_pct"]).all():
        raise ValueError("Skill demand percentages must be finite.")

    if (data["skill_demand_pct"] < 0).any():
        raise ValueError("Skill demand percentages cannot be negative.")

    # Average duplicate company-skill records if present.
    matrix = data.pivot_table(
        index="company_name",
        columns="skill",
        values="skill_demand_pct",
        aggfunc="mean",
        fill_value=0,
    )

    matrix = matrix.sort_index().sort_index(axis=1)

    if matrix.empty or (matrix.sum(axis=1) == 0).any():
        raise ValueError("Every company must have at least one skill.")

    matrix.index.name = "company_name"
    matrix.columns.name = "skill"

    return matrix



def calculate_similarity_matrix(skill_matrix):
    """Calculate pairwise cosine similarity between companies."""

    if skill_matrix.empty:
        raise ValueError("Skill matrix cannot be empty.")

    scores = cosine_similarity(skill_matrix.to_numpy())

    # Explicitly set diagonal on a writable NumPy array.
    scores = np.array(scores, copy=True)
    np.fill_diagonal(scores, 1.0)

    return pd.DataFrame(
        scores,
        index=skill_matrix.index,
        columns=skill_matrix.index,
    )




def calculate_distance_matrix(similarity_matrix):
    """Convert cosine similarity into cosine distance."""

    if similarity_matrix.empty:
        raise ValueError("Similarity matrix cannot be empty.")

    distances = 1.0 - similarity_matrix.to_numpy(copy=True)
    distances = np.clip(distances, 0.0, 1.0)

    np.fill_diagonal(distances, 0.0)

    return pd.DataFrame(
        distances,
        index=similarity_matrix.index,
        columns=similarity_matrix.columns,
    )



def calculate_skill_overlap(skill_matrix):
    """Calculate shared skills and Jaccard similarity for company pairs."""

    if skill_matrix.empty:
        raise ValueError("Skill matrix cannot be empty.")

    binary_matrix = skill_matrix.gt(0).astype(int)

    records = []

    for company_a, company_b in combinations(binary_matrix.index, 2):

        skills_a = set(
            binary_matrix.columns[binary_matrix.loc[company_a].astype(bool)]
        )

        skills_b = set(
            binary_matrix.columns[binary_matrix.loc[company_b].astype(bool)]
        )

        shared = skills_a & skills_b
        union = skills_a | skills_b

        jaccard = len(shared) / len(union) if union else 0.0

        records.append({
            "company_1": company_a,
            "company_2": company_b,
            "shared_skill_count": len(shared),
            "union_skill_count": len(union),
            "jaccard_similarity": round(jaccard, 4),
        })

    return pd.DataFrame(records)


def cluster_companies(distance_matrix, n_clusters=2):
    """Group companies using hierarchical clustering and cosine distance."""

    if distance_matrix.empty:
        raise ValueError("Distance matrix cannot be empty.")

    distances = distance_matrix.to_numpy(dtype=float)

    if not np.isfinite(distances).all():
        raise ValueError("Distance matrix contains invalid values.")

    if not np.allclose(distances, distances.T):
        raise ValueError("Distance matrix must be symmetric.")

    if not np.allclose(np.diag(distances), 0):
        raise ValueError("Distance matrix diagonal must be zero.")

    if not 2 <= n_clusters < len(distance_matrix):
        raise ValueError(
            "n_clusters must be at least 2 and smaller "
            "than the number of companies."
        )

    model = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric="precomputed",
        linkage="average",
    )

    labels = model.fit_predict(distances)

    return pd.DataFrame({
        "company_name": distance_matrix.index,
        "cluster": labels + 1,
    })
