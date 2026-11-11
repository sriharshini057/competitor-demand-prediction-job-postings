
"""Interactive Streamlit Dashboard for Competitor Demand Prediction."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"

st.set_page_config(
    page_title="Competitor Demand Intelligence",
    page_icon="📊",
    layout="wide",
)

COMPANIES = ["Accenture", "Amazon", "Deloitte", "IBM", "Microsoft"]


# --------------------------------------------------
# Data Loading
# --------------------------------------------------

@st.cache_data
def load_csv(relative_path):
    """Load a CSV file from the project output directory."""
    path = OUTPUT_DIR / relative_path

    if not path.exists():
        return None

    return pd.read_csv(path)


def show_missing(message):
    st.warning(message)


def metric_card(label, value, help_text=None):
    st.metric(label=label, value=value, help=help_text)


def bar_chart(data, x, y, title, xlabel="", ylabel=""):
    """Create a Matplotlib bar chart."""
    if data is None or data.empty:
        show_missing(f"No data available for {title}.")
        return

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(data[x].astype(str), data[y])
    ax.set_title(title)
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# --------------------------------------------------
# Load Sprint Outputs
# --------------------------------------------------

employment = load_csv("sprint_07/employment_type_analysis.csv")
work_arrangement = load_csv("sprint_07/work_arrangement_analysis.csv")
roles = load_csv("sprint_07/job_role_demand.csv")
skills = load_csv("sprint_07/skill_demand_analysis.csv")
geography = load_csv("sprint_07/geographic_demand.csv")

company_summary = load_csv("sprint_08/company_summary.csv")
company_skills = load_csv("sprint_08/skill_demand_by_company.csv")
company_roles = load_csv("sprint_08/role_demand_by_company.csv")
india_summary = load_csv("sprint_08/india_company_summary.csv")

forecast = load_csv("sprint_09/future_demand_forecast.csv")
model_comparison = load_csv("sprint_09/model_comparison.csv")

similarity = load_csv("sprint_10/company_similarity_matrix.csv")
overlap = load_csv("sprint_10/company_skill_overlap.csv")
clusters = load_csv("sprint_10/company_clusters.csv")


# --------------------------------------------------
# Sidebar Navigation
# --------------------------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Dashboard Section",
    [
        "Project Overview",
        "Competitor Benchmarking",
        "Demand Forecasting",
        "Company Similarity",
    ],
)

st.sidebar.divider()
st.sidebar.caption("CadetX | Competitor Demand Prediction")
st.sidebar.caption("Data source: Luke Barousse Data Jobs dataset")


# --------------------------------------------------
# Dashboard Header
# --------------------------------------------------

st.title("Competitor Demand Intelligence Dashboard")

st.markdown(
    "Analyze hiring demand, compare competitor skill requirements, "
    "explore future demand forecasts, and measure company similarity."
)

st.divider()


# ==================================================
# PAGE 1: PROJECT OVERVIEW
# ==================================================

if page == "Project Overview":

    st.header("Project Overview")

    # Derive Microsoft total from employment categories.
    microsoft_total = (
        pd.to_numeric(employment["Posting Count"], errors="coerce").sum()
        if employment is not None
        else 0
    )

    competitor_total = (
        pd.to_numeric(company_summary["total_postings"], errors="coerce").sum()
        if company_summary is not None
        else 0
    )

    company_count = (
        company_summary["company_name"].nunique()
        if company_summary is not None
        else 0
    )

    skill_count = 0
    skill_matrix = load_csv("sprint_10/company_skill_matrix.csv")

    if skill_matrix is not None:
        skill_count = max(0, len(skill_matrix.columns) - 1)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("Microsoft postings", f"{int(microsoft_total):,}")

    with col2:
        metric_card("Competitor postings", f"{int(competitor_total):,}")

    with col3:
        metric_card("Companies analysed", company_count)

    with col4:
        metric_card("Skills analysed", skill_count)

    st.caption(
        "Microsoft postings are calculated from employment-type counts. "
        "Competitor postings are summed from the Sprint 8 company summary."
    )

    st.subheader("Job Role Demand")

    if roles is not None:
        bar_chart(
            roles.head(10),
            "Job Role",
            "Posting Count",
            "Top Job Roles",
            "Job Role",
            "Number of Postings",
        )

    st.subheader("Top In-Demand Skills")

    if skills is not None:
        bar_chart(
            skills.head(10),
            "Skill",
            "Posting Count",
            "Top Technical Skills",
            "Skill",
            "Number of Postings",
        )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Geographical Demand")

        if geography is not None:
            bar_chart(
                geography.head(10),
                "Country",
                "Posting Count",
                "Job Postings by Country",
            )

    with col2:
        st.subheader("Employment Type")

        if employment is not None:
            bar_chart(
                employment,
                "Employment Type",
                "Posting Count",
                "Employment Distribution",
            )

    st.subheader("Work Arrangement")

    if work_arrangement is not None:
        st.dataframe(work_arrangement, hide_index=True, use_container_width=True)


# ==================================================
# PAGE 2: COMPETITOR BENCHMARKING
# ==================================================

elif page == "Competitor Benchmarking":

    st.header("Competitor Benchmarking")

    if company_summary is not None:

        st.subheader("Company Overview")

        st.dataframe(
            company_summary,
            hide_index=True,
            use_container_width=True,
        )

        bar_chart(
            company_summary,
            "company_name",
            "total_postings",
            "Total Job Postings by Company",
            "Company",
            "Total Postings",
        )

    st.divider()

    st.subheader("Skill Demand Comparison")

    if company_skills is not None:

        selected_company = st.selectbox(
            "Select Company",
            COMPANIES,
        )

        selected_skills = company_skills[
            company_skills["company_name"] == selected_company
        ].copy()

        if not selected_skills.empty:

            selected_skills["skill_demand_pct"] = pd.to_numeric(
                selected_skills["skill_demand_pct"],
                errors="coerce",
            )

            selected_skills = selected_skills.sort_values(
                "skill_demand_pct",
                ascending=False,
            ).head(10)

            bar_chart(
                selected_skills,
                "skill",
                "skill_demand_pct",
                f"Top Skills Required by {selected_company}",
                "Skill",
                "Demand Percentage",
            )

            st.dataframe(
                selected_skills,
                hide_index=True,
                use_container_width=True,
            )
        else:
            show_missing("No skill records found for this company.")

    st.divider()

    st.subheader("Job Role Comparison")

    if company_roles is not None:

        selected_role_company = st.selectbox(
            "Select Company for Role Analysis",
            COMPANIES,
            key="role_company",
        )

        selected_roles = company_roles[
            company_roles["company_name"] == selected_role_company
        ].copy()

        if not selected_roles.empty:

            selected_roles["posting_count"] = pd.to_numeric(
                selected_roles["posting_count"],
                errors="coerce",
            )

            selected_roles = selected_roles.sort_values(
                "posting_count",
                ascending=False,
            ).head(10)

            bar_chart(
                selected_roles,
                "job_title_short",
                "posting_count",
                f"Job Roles at {selected_role_company}",
                "Job Role",
                "Number of Postings",
            )

    st.divider()

    st.subheader("India-Focused Comparison")

    if india_summary is not None:
        st.dataframe(
            india_summary,
            hide_index=True,
            use_container_width=True,
        )

        bar_chart(
            india_summary,
            "company_name",
            "total_postings",
            "Competitor Postings in India",
            "Company",
            "Postings",
        )


# ==================================================
# PAGE 3: DEMAND FORECASTING
# ==================================================

elif page == "Demand Forecasting":

    st.header("Weekly Demand Forecasting")

    if model_comparison is not None:

        st.subheader("Model Performance Comparison")

        st.dataframe(
            model_comparison,
            hide_index=True,
            use_container_width=True,
        )

        model_comparison["MAE"] = pd.to_numeric(
            model_comparison["MAE"],
            errors="coerce",
        )

        best_model = model_comparison.loc[
            model_comparison["MAE"].idxmin()
        ]

        st.success(
            f"Best model based on MAE: {best_model['Model']} "
            f"(MAE: {best_model['MAE']:.3f})"
        )

        bar_chart(
            model_comparison,
            "Model",
            "MAE",
            "Model Comparison - Mean Absolute Error",
            "Model",
            "MAE",
        )

    st.divider()

    st.subheader("Future Demand Forecast")

    if forecast is not None:

        forecast["predicted_posting_count"] = pd.to_numeric(
            forecast["predicted_posting_count"],
            errors="coerce",
        )

        available_models = forecast["Model"].unique().tolist()

        selected_model = st.selectbox(
            "Choose Forecast Model",
            available_models,
            index=(
                available_models.index("Moving Average")
                if "Moving Average" in available_models
                else 0
            ),
        )

        selected_forecast = forecast[
            forecast["Model"] == selected_model
        ].copy()

        selected_forecast["forecast_week"] = pd.to_datetime(
            selected_forecast["forecast_week"],
            errors="coerce",
        )

        selected_forecast = selected_forecast.sort_values("forecast_week")

        if not selected_forecast.empty:

            fig, ax = plt.subplots(figsize=(10, 4))

            ax.plot(
                selected_forecast["forecast_week"],
                selected_forecast["predicted_posting_count"],
                marker="o",
            )

            ax.set_title(f"Weekly Forecast - {selected_model}")
            ax.set_xlabel("Forecast Week")
            ax.set_ylabel("Predicted Job Postings")
            fig.autofmt_xdate()
            fig.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

            st.dataframe(
                selected_forecast,
                hide_index=True,
                use_container_width=True,
            )

    else:
        show_missing("Forecast data is not available.")


# ==================================================
# PAGE 4: COMPANY SIMILARITY
# ==================================================

elif page == "Company Similarity":

    st.header("Company Similarity Analysis")

    st.write(
        "This section compares companies using their skill-demand "
        "patterns. Similarity values range from 0 to 1."
    )

    if similarity is not None:

        st.subheader("Company Similarity Heatmap")

        matrix = similarity.set_index("company_name")
        matrix = matrix.apply(pd.to_numeric, errors="coerce")

        fig, ax = plt.subplots(figsize=(9, 6))

        image = ax.imshow(
            matrix.values,
            cmap="Blues",
            vmin=0,
            vmax=1,
        )

        ax.set_xticks(range(len(matrix.columns)))
        ax.set_xticklabels(matrix.columns, rotation=35, ha="right")
        ax.set_yticks(range(len(matrix.index)))
        ax.set_yticklabels(matrix.index)

        for i in range(len(matrix.index)):
            for j in range(len(matrix.columns)):
                ax.text(
                    j,
                    i,
                    f"{matrix.iloc[i, j]:.2f}",
                    ha="center",
                    va="center",
                )

        ax.set_title("Cosine Similarity Between Companies")
        fig.colorbar(image, ax=ax, label="Similarity")
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Similarity Matrix")

        st.dataframe(
            matrix.style.format("{:.3f}"),
            use_container_width=True,
        )

    st.divider()

    st.subheader("Shared Skills Between Companies")

    if overlap is not None:
        st.dataframe(
            overlap.sort_values(
                "jaccard_similarity",
                ascending=False,
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()

    st.subheader("Company Clusters")

    if clusters is not None:
        st.dataframe(
            clusters,
            hide_index=True,
            use_container_width=True,
        )

    dendrogram_path = OUTPUT_DIR / "sprint_10/company_dendrogram.png"

    if dendrogram_path.exists():
        st.subheader("Hierarchical Clustering Dendrogram")
        st.image(str(dendrogram_path), use_container_width=True)


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption(
    "CadetX | Competitor Demand Prediction Using Job Postings | "
    "Sprint 11 Dashboard"
)
