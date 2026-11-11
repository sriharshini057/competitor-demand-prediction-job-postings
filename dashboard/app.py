"""CadetX - Competitor Demand Intelligence Dashboard."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"

st.set_page_config(
    page_title="CadetX | Demand Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

COMPANIES = ["Accenture", "Amazon", "Deloitte", "IBM", "Microsoft"]

COLORS = {
    "background": "#0B1120",
    "surface": "#111C30",
    "surface_light": "#172640",
    "blue": "#3B82F6",
    "cyan": "#22D3EE",
    "green": "#34D399",
    "text": "#F1F5F9",
    "muted": "#94A3B8",
}


# ============================================================
# CUSTOM STYLING
# ============================================================


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    :root {
    --bg: #090D24;
    --panel: rgba(32, 35, 75, 0.88);
    --border: rgba(139, 92, 246, 0.45);
    --cyan: #22F0FF;
    --blue: #4385FF;
    --purple: #A855F7;
    --pink: #FF4FD8;
    --teal: #2DE2B6;
    --text: #FFFFFF;
    --muted: #C1C8E8;
}

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Deep-space background */
    .stApp {
    background:
        radial-gradient(ellipse at 8% 12%, rgba(255, 79, 216, 0.28), transparent 32%),
        radial-gradient(ellipse at 90% 15%, rgba(67, 133, 255, 0.30), transparent 32%),
        radial-gradient(ellipse at 50% 95%, rgba(45, 226, 182, 0.20), transparent 38%),
        linear-gradient(135deg, #090D24, #17103B 50%, #071D36);
    color: var(--text);
}

    /* Perspective grid layer */
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        opacity: 0.18;
        background-image:
            linear-gradient(rgba(34, 211, 238, 0.13) 1px, transparent 1px),
            linear-gradient(90deg, rgba(34, 211, 238, 0.13) 1px, transparent 1px);
        background-size: 55px 55px;
        transform: perspective(700px) rotateX(58deg) scale(1.8);
        transform-origin: center bottom;
        mask-image: linear-gradient(to bottom, transparent 8%, black 100%);
    }

    /* Keep dashboard content above background */
    [data-testid="stAppViewContainer"] {
        position: relative;
        z-index: 1;
        background: transparent;
    }

    [data-testid="stHeader"] {
        background: rgba(5, 11, 24, 0.55);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #101E35 0%, #091426 100%);
        border-right: 1px solid var(--border);
        box-shadow: 8px 0 35px rgba(0, 0, 0, 0.28);
    }

    [data-testid="stSidebar"] .stRadio label {
        font-weight: 600;
        padding: 7px 0;
    }

    /* Brand */
    .brand-title {
        font-size: 31px;
        font-weight: 900;
        letter-spacing: 1.5px;
        color: var(--text);
        margin-bottom: 0;
        text-shadow: 0 0 22px rgba(34, 211, 238, 0.25);
    }

    .brand-highlight {
        background: linear-gradient(90deg, #22F0FF, #A855F7, #FF4FD8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
}

    .brand-subtitle {
        color: var(--muted);
        font-size: 12px;
        margin-top: 5px;
        margin-bottom: 24px;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }

    /* Page headings */
    .main-heading {
        font-size: 34px;
        font-weight: 900;
        color: var(--text);
        margin-bottom: 5px;
        text-shadow: 0 0 28px rgba(34, 211, 238, 0.17);
    }

    .main-description {
        color: var(--muted);
        font-size: 14px;
        margin-bottom: 24px;
    }

    .section-heading {
        font-size: 19px;
        font-weight: 800;
        color: #E2F6FF;
        margin-top: 20px;
        margin-bottom: 14px;
    }

    /* Glassmorphism KPI cards */
    .kpi-card {
    background: linear-gradient(
        135deg,
        rgba(91, 55, 170, 0.85),
        rgba(25, 62, 112, 0.88),
        rgba(12, 103, 119, 0.78)
    );
    border: 1px solid rgba(34, 240, 255, 0.55);
    border-radius: 18px;
    padding: 21px 19px;
    min-height: 120px;
    box-shadow:
        0 12px 35px rgba(0, 0, 0, 0.30),
        0 0 22px rgba(168, 85, 247, 0.22),
        inset 0 1px 0 rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(16px);
    transition: all 0.3s ease;
}

    .kpi-card:hover {
        transform: translateY(-7px) scale(1.02);
        box-shadow: 0 15px 35px rgba(34, 240, 255, 0.25);
}



    .kpi-label {
        color: #A8BCD3;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.1px;
    }

    .kpi-value {
        color: #F8FAFC;
        font-size: 30px;
        font-weight: 900;
        margin-top: 9px;
        text-shadow: 0 0 18px rgba(34, 211, 238, 0.18);
    }

    .kpi-accent {
        color: var(--cyan);
    }

    /* Insight panels */
    .insight-card {
    background: linear-gradient(
        110deg,
        rgba(91, 55, 170, 0.35),
        rgba(20, 100, 145, 0.35)
    );
    border: 1px solid rgba(34, 240, 255, 0.35);
    border-left: 5px solid #FF4FD8;
    border-radius: 14px;
    padding: 17px 19px;
    margin: 14px 0;
    color: #F1F5FF;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.22);
    backdrop-filter: blur(14px);
}

    /* Streamlit metric containers */
    div[data-testid="stMetric"] {
        background: rgba(17, 34, 59, 0.78);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.20);
        backdrop-filter: blur(12px);
    }

    div[data-testid="stMetric"] label {
        color: #A8BCD3 !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #F1F5F9;
    }

    /* Tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
    }

    /* Input controls */
    .stSelectbox label,
    .stMultiSelect label {
        color: #CBD5E1 !important;
        font-weight: 600;
    }

    [data-baseweb="select"] > div {
        background: rgba(17, 34, 59, 0.85);
        border-color: var(--border);
    }

    /* Dividers and footer */
    hr {
        border-color: rgba(56, 189, 248, 0.20);
    }

    .footer {
        color: #7186A3;
        text-align: center;
        font-size: 12px;
        padding: 22px 0 10px 0;
        letter-spacing: 0.4px;
    }

    /* Subtle scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #07101F;
    }

    ::-webkit-scrollbar-thumb {
        background: #1E4965;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_csv(relative_path):
    """Load a CSV file from the project output directory."""
    path = OUTPUT_DIR / relative_path

    if not path.exists():
        return None

    try:
        return pd.read_csv(path)
    except (pd.errors.ParserError, UnicodeDecodeError, OSError):
        return None


def show_missing(message):
    st.warning(message)


def section_heading(title, description=None):
    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True,
    )

    if description:
        st.caption(description)


def show_kpi(label, value, accent=False):
    value_class = "kpi-value kpi-accent" if accent else "kpi-value"

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="{value_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def prepare_plot(fig, height=390):
    """Apply a consistent dark theme to Plotly charts."""
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, sans-serif",
            color="#CBD5E1",
            size=12,
        ),
        margin=dict(l=20, r=20, t=55, b=35),
        title_font=dict(size=16, color="#F1F5F9"),
        legend_title_text="",
        hoverlabel=dict(
            bgcolor="#172640",
            font_color="#F1F5F9",
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#263B5B",
    )

    fig.update_yaxes(
        gridcolor="#263B5B",
        zeroline=False,
    )

    return fig


def bar_chart(data, x, y, title, xlabel=None, ylabel=None):
    """Display an interactive Plotly bar chart."""
    if data is None or data.empty:
        show_missing(f"No data available for {title}.")
        return

    if x not in data.columns or y not in data.columns:
        show_missing(f"Required columns are missing for {title}.")
        return

    chart_data = data.copy()
    chart_data[y] = pd.to_numeric(chart_data[y], errors="coerce")
    chart_data = chart_data.dropna(subset=[x, y])

    if chart_data.empty:
        show_missing(f"No valid records available for {title}.")
        return


    fig = px.bar(
    chart_data,
    x=x,
    y=y,
    title=title,
    text_auto=".2s",
    color=x,
    color_discrete_sequence=[
        "#22F0FF",
        "#A855F7",
        "#FF4FD8",
        "#4385FF",
        "#2DE2B6",
        "#FBBF24",
        "#FB7185",
    ],
)

    fig.update_traces(
    marker_line_width=0,
    textfont=dict(color="#FFFFFF", size=11),
)

    fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(12,18,42,0.35)",
    font=dict(color="#EAF2FF", family="Inter"),
    title_font=dict(color="#FFFFFF", size=18),
    xaxis=dict(
        title_font=dict(color="#CBD5E1"),
        tickfont=dict(color="#CBD5E1"),
        gridcolor="rgba(148,163,184,0.12)",
    ),
    yaxis=dict(
        title_font=dict(color="#CBD5E1"),
        tickfont=dict(color="#CBD5E1"),
        gridcolor="rgba(148,163,184,0.15)",
    ),
    legend=dict(font=dict(color="#EAF2FF")),
    margin=dict(l=15, r=15, t=55, b=15),
)


    fig.update_traces(
        marker_line_width=0,
        hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
    )

    fig.update_layout(
        xaxis_title=xlabel or x,
        yaxis_title=ylabel or y,
    )

    prepare_plot(fig)
    st.plotly_chart(fig, use_container_width=True)


def show_table(data, height=350):
    if data is not None and not data.empty:
        st.dataframe(
            data,
            hide_index=True,
            use_container_width=True,
            height=height,
        )
    else:
        show_missing("No records available.")


# ============================================================
# LOAD SPRINT OUTPUTS
# ============================================================

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


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="brand-title">CADET<span class="brand-highlight">X</span></div>
        <div class="brand-subtitle">TALENT DEMAND INTELLIGENCE PLATFORM</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Navigation")

    page = st.radio(
        "Select a section",
        [
            "Project Overview",
            "Competitor Benchmarking",
            "Demand Forecasting",
            "Company Similarity",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("**PROJECT INFORMATION**")
    st.caption("Project: Competitor Demand Prediction")
    st.caption("Primary company: Microsoft")
    st.caption("Competitor analysis: 5 companies")
    st.caption("Dataset: Luke Barousse Data Jobs")

    st.divider()

    st.caption("CadetX | Final Dashboard")


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<div class="main-heading">Demand Intelligence</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-description">'
    'Explore hiring patterns, competitor skill requirements, '
    'forecasted demand and company skill similarity.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# PAGE 1: PROJECT OVERVIEW
# ============================================================

if page == "Project Overview":

    section_heading(
        "Project Overview",
        "A consolidated view of job posting demand and hiring patterns.",
    )

    microsoft_total = (
        pd.to_numeric(employment["Posting Count"], errors="coerce").sum()
        if employment is not None and "Posting Count" in employment.columns
        else 0
    )

    competitor_total = (
        pd.to_numeric(company_summary["total_postings"], errors="coerce").sum()
        if company_summary is not None and "total_postings" in company_summary.columns
        else 0
    )

    company_count = (
        company_summary["company_name"].nunique()
        if company_summary is not None and "company_name" in company_summary.columns
        else 0
    )

    skill_matrix = load_csv("sprint_10/company_skill_matrix.csv")
    skill_count = (
        max(0, len(skill_matrix.columns) - 1)
        if skill_matrix is not None
        else 0
    )

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        show_kpi("Microsoft postings", f"{int(microsoft_total):,}", True)

    with kpi2:
        show_kpi("Competitor postings", f"{int(competitor_total):,}")

    with kpi3:
        show_kpi("Companies analysed", f"{company_count:,}")

    with kpi4:
        show_kpi("Skills analysed", f"{skill_count:,}")

    st.caption(
        "Microsoft postings are calculated from employment-type counts. "
        "Competitor postings are summed from the Sprint 8 company summary."
    )

    st.divider()

    left, right = st.columns(2)

    with left:
        section_heading("Top Job Roles")
        if roles is not None:
            bar_chart(
                roles.head(10),
                "Job Role",
                "Posting Count",
                "Most Frequently Posted Roles",
                "Job Role",
                "Number of Postings",
            )
        else:
            show_missing("Job role data is not available.")

    with right:
        section_heading("Top In-Demand Skills")
        if skills is not None:
            bar_chart(
                skills.head(10),
                "Skill",
                "Posting Count",
                "Most Frequently Required Skills",
                "Skill",
                "Number of Postings",
            )
        else:
            show_missing("Skill demand data is not available.")

    st.divider()

    left, right = st.columns(2)

    with left:
        section_heading("Geographical Demand")
        if geography is not None:
            bar_chart(
                geography.head(10),
                "Country",
                "Posting Count",
                "Job Postings by Country",
            )
        else:
            show_missing("Geographical data is not available.")

    with right:
        section_heading("Employment Distribution")
        if employment is not None:
            bar_chart(
                employment,
                "Employment Type",
                "Posting Count",
                "Employment Type Breakdown",
            )
        else:
            show_missing("Employment data is not available.")

    st.divider()

    section_heading("Work Arrangement")
    show_table(work_arrangement)


# ============================================================
# PAGE 2: COMPETITOR BENCHMARKING
# ============================================================

elif page == "Competitor Benchmarking":

    section_heading(
        "Competitor Benchmarking",
        "Compare posting volumes, technical skills and job roles "
        "across the five analysed companies.",
    )

    if company_summary is not None:

        section_heading("Company Overview")

        if "total_postings" in company_summary.columns:
            total_posts = pd.to_numeric(
                company_summary["total_postings"],
                errors="coerce",
            ).sum()
        else:
            total_posts = 0

        summary_cols = st.columns(3)

        with summary_cols[0]:
            show_kpi("Companies compared", company_summary["company_name"].nunique())

        with summary_cols[1]:
            show_kpi("Total competitor postings", f"{int(total_posts):,}", True)

        with summary_cols[2]:
            show_kpi("Analysis scope", "Multi-company")

        bar_chart(
            company_summary,
            "company_name",
            "total_postings",
            "Total Job Postings by Company",
            "Company",
            "Total Postings",
        )

        with st.expander("View company summary data"):
            show_table(company_summary)

    else:
        show_missing("Company summary data is not available.")

    st.divider()

    section_heading("Skill Demand Comparison")

    if company_skills is not None:

        available_companies = (
            sorted(company_skills["company_name"].dropna().unique().tolist())
            if "company_name" in company_skills.columns
            else COMPANIES
        )

        selected_company = st.selectbox(
            "Select company for skill analysis",
            available_companies,
            key="skill_company",
        )

        selected_skills = company_skills[
            company_skills["company_name"] == selected_company
        ].copy()

        if not selected_skills.empty:

            selected_skills["skill_demand_pct"] = pd.to_numeric(
                selected_skills["skill_demand_pct"],
                errors="coerce",
            )

            selected_skills = selected_skills.dropna(
                subset=["skill_demand_pct"]
            ).sort_values(
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

            with st.expander("View detailed skill demand"):
                show_table(selected_skills)

        else:
            show_missing("No skill records found for this company.")

    else:
        show_missing("Company skill data is not available.")

    st.divider()

    section_heading("Job Role Comparison")

    if company_roles is not None:

        available_role_companies = (
            sorted(company_roles["company_name"].dropna().unique().tolist())
            if "company_name" in company_roles.columns
            else COMPANIES
        )

        selected_role_company = st.selectbox(
            "Select company for role analysis",
            available_role_companies,
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

            selected_roles = selected_roles.dropna(
                subset=["posting_count"]
            ).sort_values(
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

        else:
            show_missing("No job role records found for this company.")

    else:
        show_missing("Company role data is not available.")

    st.divider()

    section_heading("India-Focused Comparison")

    if india_summary is not None:

        bar_chart(
            india_summary,
            "company_name",
            "total_postings",
            "Competitor Postings in India",
            "Company",
            "Postings",
        )

        with st.expander("View India company summary"):
            show_table(india_summary)

    else:
        show_missing("India comparison data is not available.")


# ============================================================
# PAGE 3: DEMAND FORECASTING
# ============================================================

elif page == "Demand Forecasting":

    section_heading(
        "Weekly Demand Forecasting",
        "Review historical model performance and explore forecasted "
        "Microsoft job posting demand.",
    )

    if model_comparison is not None:

        section_heading("Model Performance Comparison")

        comparison = model_comparison.copy()

        if "MAE" in comparison.columns:
            comparison["MAE"] = pd.to_numeric(
                comparison["MAE"],
                errors="coerce",
            )

        if "RMSE" in comparison.columns:
            comparison["RMSE"] = pd.to_numeric(
                comparison["RMSE"],
                errors="coerce",
            )

        if "MAE" in comparison.columns and comparison["MAE"].notna().any():

            best_model = comparison.loc[comparison["MAE"].idxmin()]

            st.markdown(
                f"""
                <div class="insight-card">
                    <strong>Best model based on MAE:</strong>
                    {best_model['Model']}
                    &nbsp; | &nbsp;
                    <strong>MAE:</strong> {best_model['MAE']:.3f}
                </div>
                """,
                unsafe_allow_html=True,
            )

        if "Model" in comparison.columns and "MAE" in comparison.columns:
            bar_chart(
                comparison,
                "Model",
                "MAE",
                "Model Comparison - Mean Absolute Error",
                "Model",
                "MAE",
            )

        with st.expander("View complete model comparison"):
            show_table(comparison)

    else:
        show_missing("Model comparison data is not available.")

    st.divider()

    section_heading("Future Demand Forecast")

    if forecast is not None:

        forecast_data = forecast.copy()

        forecast_data["predicted_posting_count"] = pd.to_numeric(
            forecast_data["predicted_posting_count"],
            errors="coerce",
        )

        forecast_data["forecast_week"] = pd.to_datetime(
            forecast_data["forecast_week"],
            errors="coerce",
        )

        available_models = (
            forecast_data["Model"].dropna().unique().tolist()
            if "Model" in forecast_data.columns
            else []
        )

        if available_models:

            default_index = (
                available_models.index("Moving Average")
                if "Moving Average" in available_models
                else 0
            )

            selected_model = st.selectbox(
                "Choose forecast model",
                available_models,
                index=default_index,
            )

            selected_forecast = forecast_data[
                forecast_data["Model"] == selected_model
            ].copy()

            selected_forecast = selected_forecast.dropna(
                subset=["forecast_week", "predicted_posting_count"]
            ).sort_values("forecast_week")

            if not selected_forecast.empty:

                forecast_total = selected_forecast[
                    "predicted_posting_count"
                ].sum()

                forecast_average = selected_forecast[
                    "predicted_posting_count"
                ].mean()

                forecast_peak = selected_forecast[
                    "predicted_posting_count"
                ].max()

                c1, c2, c3 = st.columns(3)

                with c1:
                    show_kpi("Forecast periods", len(selected_forecast))

                with c2:
                    show_kpi("Average predicted postings", f"{forecast_average:.2f}", True)

                with c3:
                    show_kpi("Peak predicted postings", f"{forecast_peak:.2f}")

                fig = px.line(
                    selected_forecast,
                    x="forecast_week",
                    y="predicted_posting_count",
                    markers=True,
                    title=f"Weekly Demand Forecast - {selected_model}",
                    color_discrete_sequence=["#22D3EE"],
                )


                fig.update_traces(
    line=dict(
        color="#22F0FF",
        width=4,
        shape="spline",
    ),
    marker=dict(
        size=10,
        color="#FF4FD8",
        line=dict(
            color="#FFFFFF",
            width=1.5,
        ),
    ),
    hovertemplate=(
        "Week: %{x|%d %b %Y}<br>"
        "Predicted postings: %{y:.2f}"
        "<extra></extra>"
    ),
)

                fig.update_layout(
    xaxis_title="Forecast Week",
    yaxis_title="Predicted Job Postings",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(12,18,42,0.35)",
    font=dict(color="#EAF2FF", family="Inter"),
    title_font=dict(color="#FFFFFF", size=20),
    xaxis=dict(
        title_font=dict(color="#22F0FF"),
        tickfont=dict(color="#CBD5E1"),
        gridcolor="rgba(148,163,184,0.13)",
    ),
    yaxis=dict(
        title_font=dict(color="#22F0FF"),
        tickfont=dict(color="#CBD5E1"),
        gridcolor="rgba(148,163,184,0.15)",
    ),
    hoverlabel=dict(
        bgcolor="#201B48",
        bordercolor="#22F0FF",
        font=dict(color="#FFFFFF"),
    ),
    margin=dict(l=15, r=15, t=55, b=15),
)




                prepare_plot(fig, height=420)
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("View forecast data"):
                    show_table(selected_forecast)

                st.caption(
                    f"Total predicted postings across the displayed "
                    f"forecast periods: {forecast_total:.2f}"
                )

            else:
                show_missing("No forecast records found for the selected model.")

        else:
            show_missing("No forecast models are available.")

    else:
        show_missing("Forecast data is not available.")

    st.info(
        "Forecasts are historical-data-based estimates. They should not "
        "be interpreted as confirmed current or future hiring vacancies."
    )


# ============================================================
# PAGE 4: COMPANY SIMILARITY
# ============================================================

elif page == "Company Similarity":

    section_heading(
        "Company Similarity Analysis",
        "Compare companies based on their skill-demand patterns. "
        "Similarity values range from 0 to 1.",
    )

    if similarity is not None:

        section_heading("Company Similarity Heatmap")

        matrix = similarity.set_index("company_name")
        matrix = matrix.apply(pd.to_numeric, errors="coerce")

        fig = go.Figure(
            data=go.Heatmap(
                z=matrix.values,
                x=matrix.columns.tolist(),
                y=matrix.index.tolist(),
                colorscale=[
                    [0, "#172640"],
                    [0.5, "#2563EB"],
                    [1, "#22D3EE"],
                ],
                zmin=0,
                zmax=1,
                text=matrix.round(2).values,
                texttemplate="%{text}",
                hovertemplate=(
                    "Company 1: %{y}<br>"
                    "Company 2: %{x}<br>"
                    "Similarity: %{z:.3f}"
                    "<extra></extra>"
                ),
                colorbar=dict(title="Similarity"),
            )
        )

        fig.update_layout(
            title="Cosine Similarity Between Companies",
            xaxis_title="Company",
            yaxis_title="Company",
        )

        prepare_plot(fig, height=480)
        st.plotly_chart(fig, use_container_width=True)

        section_heading("Similarity Matrix")

        with st.expander("View numerical similarity values"):
            st.dataframe(
                matrix.style.format("{:.3f}"),
                use_container_width=True,
            )

    else:
        show_missing("Company similarity data is not available.")

    st.divider()

    section_heading("Shared Skills Between Companies")

    if overlap is not None:

        if "jaccard_similarity" in overlap.columns:
            sorted_overlap = overlap.sort_values(
                "jaccard_similarity",
                ascending=False,
            )
        else:
            sorted_overlap = overlap

        show_table(sorted_overlap)

    else:
        show_missing("Company skill overlap data is not available.")

    st.divider()

    section_heading("Company Clusters")

    if clusters is not None:
        show_table(clusters)
    else:
        show_missing("Company cluster data is not available.")

    dendrogram_path = OUTPUT_DIR / "sprint_10/company_dendrogram.png"

    if dendrogram_path.exists():

        st.divider()
        section_heading(
            "Hierarchical Clustering Dendrogram",
            "Visual representation of company groupings based on skill similarity.",
        )

        st.image(
            str(dendrogram_path),
            use_container_width=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        <strong>CADETX</strong> &nbsp;|&nbsp;
        Competitor Demand Prediction Using Job Postings
        <br>
        Data source: Luke Barousse Data Jobs Dataset
        <br>
        Sprint 12 - Integrated Analytics Dashboard
    </div>
    """,
    unsafe_allow_html=True,
)
