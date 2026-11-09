
"""Visualization module for Sprint 8 competitor comparison."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def create_comparison_chart(
    df,
    category_column,
    value_column,
    title,
    filename,
    output_dir,
    top_n=8,
):
    """Create a five-company comparison chart."""

    companies = [
        "Microsoft", "Amazon", "IBM", "Accenture", "Deloitte"
    ]

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    axes = axes.flatten()

    for index, company in enumerate(companies):
        company_data = df[
            df["company_name"] == company
        ].nlargest(top_n, value_column)

        company_data = company_data.sort_values(value_column)

        axes[index].barh(
            company_data[category_column].astype(str),
            company_data[value_column],
        )

        axes[index].set_title(company)
        axes[index].set_xlabel(value_column.replace("_", " ").title())
        axes[index].grid(axis="x", alpha=0.3)

    axes[5].axis("off")

    fig.suptitle(title, fontsize=16, fontweight="bold")
    plt.tight_layout()

    output_path = Path(output_dir) / filename
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")


def generate_competitor_visualizations(output_dir):
    """Generate all Sprint 8 comparison charts."""

    output_dir = Path(output_dir)

    charts = [
        (
            "skill_demand_by_company.csv",
            "skill",
            "skill_demand_pct",
            "Global Skill Demand by Company",
            "global_skill_demand.png",
        ),
        (
            "role_demand_by_company.csv",
            "job_title_short",
            "role_demand_pct",
            "Global Job Role Demand by Company",
            "global_role_demand.png",
        ),
        (
            "country_demand_by_company.csv",
            "job_country",
            "country_demand_pct",
            "Global Country Distribution by Company",
            "country_distribution.png",
        ),
        (
            "india_skill_demand_by_company.csv",
            "skill",
            "skill_demand_pct",
            "India Skill Demand by Company",
            "india_skill_demand.png",
        ),
        (
            "india_role_demand_by_company.csv",
            "job_title_short",
            "role_demand_pct",
            "India Job Role Demand by Company",
            "india_role_demand.png",
        ),
    ]

    for csv_file, category, value, title, filename in charts:

        df = pd.read_csv(output_dir / csv_file)

        create_comparison_chart(
            df=df,
            category_column=category,
            value_column=value,
            title=title,
            filename=filename,
            output_dir=output_dir,
        )


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "outputs" / "sprint_08"

    generate_competitor_visualizations(output_dir)
