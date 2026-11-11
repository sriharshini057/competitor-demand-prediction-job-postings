
"""Run Sprint 10 company similarity analysis and save outputs."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

from src.modeling.similarity import (
    build_company_skill_matrix,
    calculate_similarity_matrix,
    calculate_distance_matrix,
    calculate_skill_overlap,
    cluster_companies,
)


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT / "outputs" / "sprint_08" / "skill_demand_by_company.csv"
OUTPUT_DIR = ROOT / "outputs" / "sprint_10"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading Sprint 8 skill demand data...", flush=True)
    data = pd.read_csv(INPUT_FILE)

    print("Building company-skill matrix...", flush=True)
    skill_matrix = build_company_skill_matrix(data)

    print("Calculating similarity and distance...", flush=True)
    similarity = calculate_similarity_matrix(skill_matrix)
    distance = calculate_distance_matrix(similarity)

    print("Calculating skill overlap...", flush=True)
    overlap = calculate_skill_overlap(skill_matrix)

    print("Clustering companies...", flush=True)
    clusters = cluster_companies(distance, n_clusters=2)

    print("Saving CSV files...", flush=True)
    skill_matrix.to_csv(OUTPUT_DIR / "company_skill_matrix.csv")
    similarity.to_csv(OUTPUT_DIR / "company_similarity_matrix.csv")
    distance.to_csv(OUTPUT_DIR / "company_distance_matrix.csv")
    overlap.to_csv(OUTPUT_DIR / "company_skill_overlap.csv", index=False)
    clusters.to_csv(OUTPUT_DIR / "company_clusters.csv", index=False)

    print("Generating similarity heatmap...", flush=True)
    fig, ax = plt.subplots(figsize=(9, 7))

    image = ax.imshow(similarity.values, cmap="Blues", vmin=0, vmax=1)

    ax.set_xticks(range(len(similarity.columns)))
    ax.set_yticks(range(len(similarity.index)))
    ax.set_xticklabels(similarity.columns, rotation=35, ha="right")
    ax.set_yticklabels(similarity.index)

    for row in range(len(similarity.index)):
        for col in range(len(similarity.columns)):
            ax.text(
                col,
                row,
                f"{similarity.iloc[row, col]:.2f}",
                ha="center",
                va="center",
            )

    ax.set_title("Company Skill-Demand Similarity")
    ax.set_xlabel("Company")
    ax.set_ylabel("Company")
    fig.colorbar(image, ax=ax, label="Cosine Similarity")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "similarity_heatmap.png", dpi=300)
    plt.close(fig)

    print("Generating hierarchical clustering dendrogram...", flush=True)
    condensed_distance = squareform(distance.values, checks=True)
    linkage_matrix = linkage(condensed_distance, method="average")

    fig, ax = plt.subplots(figsize=(10, 6))

    dendrogram(
        linkage_matrix,
        labels=distance.index.tolist(),
        ax=ax,
        leaf_rotation=30,
    )

    ax.set_title("Company Hierarchical Clustering")
    ax.set_xlabel("Company")
    ax.set_ylabel("Cosine Distance")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "company_dendrogram.png", dpi=300)
    plt.close(fig)

    print("\nSPRINT 10 OUTPUTS GENERATED", flush=True)
    print("Output directory:", OUTPUT_DIR)
    print("Company-skill matrix:", skill_matrix.shape)
    print("Similarity matrix:", similarity.shape)
    print("Skill overlap pairs:", len(overlap))

    print("\nClusters:")
    print(clusters.to_string(index=False))

    print("\nGenerated files:")
    for file in sorted(OUTPUT_DIR.iterdir()):
        print(f"- {file.name}")


if __name__ == "__main__":
    main()
