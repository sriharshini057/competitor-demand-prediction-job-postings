"""Tests for Sprint 10 company similarity analysis."""

import numpy as np
import pandas as pd
import pytest

from src.modeling.similarity import (
    build_company_skill_matrix,
    calculate_similarity_matrix,
    calculate_distance_matrix,
    calculate_skill_overlap,
    cluster_companies,
)


@pytest.fixture
def sample_skill_data():
    return pd.DataFrame({
        "company_name": [
            "Microsoft", "Microsoft",
            "Amazon", "Amazon",
            "IBM", "IBM",
        ],
        "skill": [
            "Python", "SQL",
            "Python", "AWS",
            "Java", "SQL",
        ],
        "skill_demand_pct": [
            60, 40,
            50, 50,
            70, 30,
        ],
    })


@pytest.fixture
def sample_matrix():
    return pd.DataFrame(
        [
            [60, 40, 0],
            [50, 0, 50],
            [0, 30, 70],
        ],
        index=["Microsoft", "Amazon", "IBM"],
        columns=["Python", "SQL", "Java"],
    )


def test_build_company_skill_matrix(sample_skill_data):
    matrix = build_company_skill_matrix(sample_skill_data)

    assert matrix.shape == (3, 4)
    assert list(matrix.index) == ["Amazon", "IBM", "Microsoft"]
    assert matrix.loc["Microsoft", "Python"] == 60
    assert matrix.loc["Amazon", "AWS"] == 50


def test_build_matrix_missing_columns():
    data = pd.DataFrame({"company_name": ["Microsoft"]})

    with pytest.raises(ValueError, match="Missing required columns"):
        build_company_skill_matrix(data)


def test_build_matrix_empty_data():
    data = pd.DataFrame(
        columns=["company_name", "skill", "skill_demand_pct"]
    )

    with pytest.raises(ValueError, match="empty"):
        build_company_skill_matrix(data)


def test_build_matrix_rejects_negative_values():
    data = pd.DataFrame({
        "company_name": ["Microsoft"],
        "skill": ["Python"],
        "skill_demand_pct": [-10],
    })

    with pytest.raises(ValueError, match="negative"):
        build_company_skill_matrix(data)


def test_build_matrix_rejects_non_finite_values():
    data = pd.DataFrame({
        "company_name": ["Microsoft"],
        "skill": ["Python"],
        "skill_demand_pct": [np.inf],
    })

    with pytest.raises(ValueError, match="finite"):
        build_company_skill_matrix(data)


def test_calculate_similarity_matrix(sample_matrix):
    similarity = calculate_similarity_matrix(sample_matrix)

    assert similarity.shape == (3, 3)
    assert np.allclose(similarity.values, similarity.values.T)
    assert np.allclose(np.diag(similarity), 1.0)
    assert similarity.loc["Microsoft", "Amazon"] > 0


def test_calculate_distance_matrix(sample_matrix):
    similarity = calculate_similarity_matrix(sample_matrix)
    distance = calculate_distance_matrix(similarity)

    assert distance.shape == (3, 3)
    assert np.allclose(distance.values, distance.values.T)
    assert np.allclose(np.diag(distance), 0.0)
    assert (distance.values >= 0).all()
    assert (distance.values <= 1).all()


def test_calculate_skill_overlap(sample_matrix):
    overlap = calculate_skill_overlap(sample_matrix)

    assert len(overlap) == 3
    assert "jaccard_similarity" in overlap.columns
    assert (overlap["shared_skill_count"] >= 0).all()
    assert (overlap["jaccard_similarity"] >= 0).all()
    assert (overlap["jaccard_similarity"] <= 1).all()


def test_cluster_companies(sample_matrix):
    similarity = calculate_similarity_matrix(sample_matrix)
    distance = calculate_distance_matrix(similarity)

    clusters = cluster_companies(distance, n_clusters=2)

    assert len(clusters) == 3
    assert clusters["company_name"].nunique() == 3
    assert clusters["cluster"].nunique() == 2


def test_cluster_rejects_invalid_cluster_count(sample_matrix):
    similarity = calculate_similarity_matrix(sample_matrix)
    distance = calculate_distance_matrix(similarity)

    with pytest.raises(ValueError, match="n_clusters"):
        cluster_companies(distance, n_clusters=3)


def test_cluster_rejects_non_symmetric_distance():
    distance = pd.DataFrame(
        [[0.0, 0.2], [0.5, 0.0]],
        index=["A", "B"],
        columns=["A", "B"],
    )

    with pytest.raises(ValueError, match="symmetric"):
        cluster_companies(distance, n_clusters=2)