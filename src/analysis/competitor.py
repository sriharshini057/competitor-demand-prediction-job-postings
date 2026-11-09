
"""
Sprint 8: Competitor Comparison and Demand Benchmarking.

Compares job-posting demand across selected technology companies.
Uses the original 2023 job postings dataset and structured job_skills.
"""

import ast
from collections import Counter
from pathlib import Path

import pandas as pd

from src.skills.skill_extractor import (
    CANONICAL_SKILL_ALIASES,
    SKILL_TO_CATEGORY,
)


# ---------------------------------------------------------
# PROJECT CONFIGURATION
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_FILE = PROJECT_ROOT / "data" / "raw" / "data_jobs.csv"

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "sprint_08"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COMPANIES = [
    "Microsoft",
    "Amazon",
    "IBM",
    "Accenture",
    "Deloitte",
]

CHUNK_SIZE = 50000

# ---------------------------------------------------------
# SPRINT 8 SKILL EXTENSIONS
# ---------------------------------------------------------

ADDITIONAL_SKILLS = {
    "ibm cloud": ("IBM Cloud", "Cloud"),
    "sas": ("SAS", "Data Analysis & BI"),
    "redshift": ("Amazon Redshift", "Data Engineering"),
    "qlik": ("Qlik", "Data Analysis & BI"),
    "matlab": ("MATLAB", "Programming"),
    "jira": ("Jira", "Development & Tools"),
    "sap": ("SAP", "Enterprise Tools"),
    "powerpoint": ("PowerPoint", "Business Tools"),
    "shell": ("Shell", "Operating Systems & Scripting"),
    "unix": ("Unix", "Operating Systems & Scripting"),
    "spss": ("SPSS", "Data Analysis & BI"),
    "vba": ("VBA", "Programming"),
    "cognos": ("IBM Cognos", "Data Analysis & BI"),
    "perl": ("Perl", "Programming"),
    "ssis": ("SSIS", "Data Engineering"),
    "jupyter": ("Jupyter", "Development & Tools"),
    "terraform": ("Terraform", "Cloud & DevOps"),
    "confluence": ("Confluence", "Development & Tools"),
    "dynamodb": ("Amazon DynamoDB", "Databases"),
    "watson": ("IBM Watson", "Artificial Intelligence"),
    "elasticsearch": ("Elasticsearch", "Databases"),
    "react": ("React", "Development & Tools"),
    "alteryx": ("Alteryx", "Data Analysis & BI"),
    "db2": ("IBM Db2", "Databases"),
    "visio": ("Visio", "Business Tools"),
    "mxnet": ("Apache MXNet", "Machine Learning"),
    "microstrategy": ("MicroStrategy", "Data Analysis & BI"),
    "ruby": ("Ruby", "Programming"),
    "t-sql": ("T-SQL", "Databases"),
    "css": ("CSS", "Development & Tools"),
    "outlook": ("Outlook", "Business Tools"),
    "bash": ("Bash", "Operating Systems & Scripting"),
    "html": ("HTML", "Development & Tools"),
    "sharepoint": ("SharePoint", "Business Tools"),
    "powershell": ("PowerShell", "Operating Systems & Scripting"),
    "windows": ("Windows", "Operating Systems & Scripting"),
    "express": ("Express.js", "Development & Tools"),
    "word": ("Microsoft Word", "Business Tools"),
    "colocation": ("Colocation", "Cloud Infrastructure"),
}

# Terms that are too ambiguous to count as technical skills.
EXCLUDED_SKILLS = {
    "flow",
}

# Case-insensitive lookup for the original taxonomy.
BASE_SKILL_LOOKUP = {
    skill.lower(): (skill, category)
    for skill, category in SKILL_TO_CATEGORY.items()
}


# ---------------------------------------------------------
# SKILL NORMALIZATION
# ---------------------------------------------------------

def parse_skill_list(value):
    """Convert a structured job_skills value into a Python list."""

    if isinstance(value, list):
        return value

    if pd.isna(value):
        return []

    try:
        parsed = ast.literal_eval(value)
        return parsed if isinstance(parsed, list) else []
    except (ValueError, SyntaxError):
        return []


def normalize_skill(skill):
    """Normalize a raw skill and return its canonical name and category."""

    if not isinstance(skill, str):
        return None, None

    raw_skill = skill.strip().lower()

    if not raw_skill or raw_skill in EXCLUDED_SKILLS:
        return None, None

    # Sprint 8-specific extensions.
    if raw_skill in ADDITIONAL_SKILLS:
        return ADDITIONAL_SKILLS[raw_skill]

    # Existing canonical aliases.
    canonical = CANONICAL_SKILL_ALIASES.get(raw_skill)

    if canonical:
        category = SKILL_TO_CATEGORY.get(canonical)

        if category:
            return canonical, category

    # Existing taxonomy, ignoring capitalization.
    if raw_skill in BASE_SKILL_LOOKUP:
        return BASE_SKILL_LOOKUP[raw_skill]

    # Preserve valid but currently uncategorized skills.
    return raw_skill.title(), "Other / Unclassified"


# ---------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------

def load_competitor_data():
    """Read the original dataset in chunks and retain selected companies."""

    if not RAW_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Raw dataset not found: {RAW_DATA_FILE}"
        )

    required_columns = [
        "company_name",
        "job_title_short",
        "job_posted_date",
        "job_country",
        "job_skills",
    ]

    selected_frames = []

    for chunk in pd.read_csv(
        RAW_DATA_FILE,
        usecols=required_columns,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    ):
        filtered = chunk[
            chunk["company_name"].isin(COMPANIES)
        ].copy()

        if not filtered.empty:
            selected_frames.append(filtered)

    if not selected_frames:
        raise ValueError("No selected company records were found.")

    df = pd.concat(selected_frames, ignore_index=True)

    df["skill_list"] = df["job_skills"].apply(parse_skill_list)
    df["skill_data_available"] = df["job_skills"].notna()

    return df


# ---------------------------------------------------------
# COMPANY SUMMARY
# ---------------------------------------------------------

def generate_company_summary(df):
    """Calculate posting volume, skill coverage, and company diversity."""

    summary = (
        df.groupby("company_name")
        .agg(
            total_postings=("company_name", "size"),
            skill_data_available=("skill_data_available", "sum"),
            unique_job_roles=("job_title_short", "nunique"),
            unique_countries=("job_country", "nunique"),
        )
        .reset_index()
    )

    summary["skill_coverage_pct"] = (
        summary["skill_data_available"]
        / summary["total_postings"]
        * 100
    ).round(2)

    summary.to_csv(
        OUTPUT_DIR / "company_summary.csv",
        index=False,
    )

    return summary
def generate_country_comparison(df):
    """Compare job-posting distribution across countries."""

    country_df = df.copy()

    country_df["job_country"] = (
        country_df["job_country"]
        .astype("string")
        .str.strip()
    )

    country_df = country_df[
        country_df["job_country"].notna()
        & country_df["job_country"].ne("")
    ]

    country_counts = (
        country_df
        .groupby(["company_name", "job_country"])
        .size()
        .reset_index(name="posting_count")
    )

    company_totals = (
        df.groupby("company_name")
        .size()
        .to_dict()
    )

    country_counts["company_total_postings"] = (
        country_counts["company_name"].map(company_totals)
    )

    country_counts["country_demand_pct"] = (
        country_counts["posting_count"]
        / country_counts["company_total_postings"]
        * 100
    ).round(2)

    country_counts = country_counts.sort_values(
        ["company_name", "posting_count"],
        ascending=[True, False],
    )

    country_counts.to_csv(
        OUTPUT_DIR / "country_demand_by_company.csv",
        index=False,
    )

    return country_counts
def generate_india_comparison(df):
    """Compare job roles and skill demand for India postings."""

    india_df = df[
        df["job_country"].astype("string").str.strip().eq("India")
    ].copy()

    # India company summary
    summary = (
        india_df.groupby("company_name")
        .agg(
            total_postings=("company_name", "size"),
            skill_data_available=("skill_data_available", "sum"),
        )
        .reset_index()
    )

    summary["skill_coverage_pct"] = (
        summary["skill_data_available"]
        / summary["total_postings"] * 100
    ).round(2)

    summary.to_csv(
        OUTPUT_DIR / "india_company_summary.csv",
        index=False,
    )

    # India role demand
    roles = (
        india_df.groupby(["company_name", "job_title_short"])
        .size()
        .reset_index(name="posting_count")
    )

    role_totals = india_df.groupby("company_name").size().to_dict()

    roles["company_total_postings"] = (
        roles["company_name"].map(role_totals)
    )

    roles["role_demand_pct"] = (
        roles["posting_count"]
        / roles["company_total_postings"] * 100
    ).round(2)

    roles = roles.sort_values(
        ["company_name", "posting_count"],
        ascending=[True, False],
    )

    roles.to_csv(
        OUTPUT_DIR / "india_role_demand_by_company.csv",
        index=False,
    )

    # India skill demand
    skill_counts = Counter()
    available_counts = Counter()
    skill_categories = {}

    for row in india_df.itertuples(index=False):

        if not row.skill_data_available:
            continue

        company = row.company_name
        available_counts[company] += 1

        normalized_skills = {}

        for raw_skill in row.skill_list:
            skill, category = normalize_skill(raw_skill)

            if skill is not None:
                normalized_skills[skill] = category

        for skill, category in normalized_skills.items():
            skill_counts[(company, skill)] += 1
            skill_categories[skill] = category

    records = []

    for (company, skill), count in skill_counts.items():

        available = available_counts[company]

        records.append({
            "company_name": company,
            "skill": skill,
            "skill_category": skill_categories[skill],
            "posting_count": count,
            "skill_data_available": available,
            "skill_demand_pct": round(
                count / available * 100, 2
            ),
        })

    skills = pd.DataFrame(records)

    if not skills.empty:
        skills = skills.sort_values(
            ["company_name", "skill_demand_pct"],
            ascending=[True, False],
        )

    skills.to_csv(
        OUTPUT_DIR / "india_skill_demand_by_company.csv",
        index=False,
    )

    return summary, roles, skills

# ---------------------------------------------------------
# SKILL DEMAND COMPARISON
# ---------------------------------------------------------


def generate_skill_demand(df):
    """Calculate company-level skill demand using available skill postings."""

    skill_counts = Counter()
    company_available = Counter()
    skill_categories = {}

    for row in df.itertuples(index=False):
        company = row.company_name

        if not row.skill_data_available:
            continue

        company_available[company] += 1

        # Normalize each skill only once per posting.
        normalized_skills = {}

        for raw_skill in row.skill_list:
            skill, category = normalize_skill(raw_skill)

            if skill is not None:
                normalized_skills[skill] = category

        # Count each skill only once per posting.
        for skill, category in normalized_skills.items():
            skill_counts[(company, skill)] += 1
            skill_categories[skill] = category

    records = []

    for (company, skill), count in skill_counts.items():

        available = company_available[company]

        records.append({
            "company_name": company,
            "skill": skill,
            "skill_category": skill_categories[skill],
            "posting_count": count,
            "skill_data_available": available,
            "skill_demand_pct": round(
                count / available * 100, 2
            ),
        })

    result = pd.DataFrame(records)

    if not result.empty:
        result = result.sort_values(
            ["company_name", "skill_demand_pct"],
            ascending=[True, False],
        )

    result.to_csv(
        OUTPUT_DIR / "skill_demand_by_company.csv",
        index=False,
    )

    return result



# ---------------------------------------------------------
# JOB ROLE COMPARISON
# ---------------------------------------------------------

def generate_role_comparison(df):
    """Compare job-role demand across selected companies."""

    result = (
        df.dropna(subset=["job_title_short"])
        .groupby(["company_name", "job_title_short"])
        .size()
        .reset_index(name="posting_count")
    )

    company_totals = (
        df.groupby("company_name")
        .size()
        .to_dict()
    )

    result["company_total_postings"] = (
        result["company_name"].map(company_totals)
    )

    result["role_demand_pct"] = (
        result["posting_count"]
        / result["company_total_postings"]
        * 100
    ).round(2)

    result = result.sort_values(
        ["company_name", "posting_count"],
        ascending=[True, False],
    )

    result.to_csv(
        OUTPUT_DIR / "role_demand_by_company.csv",
        index=False,
    )

    return result


# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------

def run_competitor_analysis():
    """Run the Sprint 8 competitor benchmarking pipeline."""

    print("\nSPRINT 8: COMPETITOR COMPARISON")
    print("=" * 60)

    df = load_competitor_data()

    print("Selected company postings:", len(df))
    print("Companies:", df["company_name"].nunique())

    summary = generate_company_summary(df)
    skills = generate_skill_demand(df)
    roles = generate_role_comparison(df)
    country_comparison = generate_country_comparison(df)
    india_summary, india_roles, india_skills = (
    generate_india_comparison(df))

    print("\nCompany Summary")
    print(summary.to_string(index=False))

    print("\nTop 10 Skills by Company")

    if not skills.empty:
        top_skills = (
            skills.groupby("company_name", group_keys=False)
            .head(10)
        )
        print(top_skills.to_string(index=False))

    print("\nTop Job Roles by Company")

    if not roles.empty:
        print(
            roles.groupby("company_name", group_keys=False)
            .head(5)
            .to_string(index=False)
        )

    print("\nSprint 8 analysis completed.")
    print("Output directory:", OUTPUT_DIR)
    print("\nTop 10 Countries by Company:")
    print(
    country_comparison
    .groupby("company_name")
    .head(10)
    .to_string(index=False))
    print("\nIndia Company Summary:")
    print(india_summary.to_string(index=False))

    print("\nTop 10 India Job Roles by Company:")
    print(
    india_roles.groupby("company_name")
    .head(10)
    .to_string(index=False)
)

    print("\nTop 10 India Skills by Company:")
    print(
    india_skills.groupby("company_name")
    .head(10)
    .to_string(index=False))

    return {
        "company_summary": summary,
        "skill_demand": skills,
        "role_comparison": roles,
    }


if __name__ == "__main__":
    run_competitor_analysis()
