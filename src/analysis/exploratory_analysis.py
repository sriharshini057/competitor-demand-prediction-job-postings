
"""
Sprint 7: Exploratory Analysis and Demand Insights

Analyzes Microsoft job postings and generates summary statistics.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


# Project directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Input dataset
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "microsoft_jobs_skills.csv"

# Output directory
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "sprint_07"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load the Microsoft job postings dataset."""

    df = pd.read_csv(DATA_FILE)

    print("Dataset loaded successfully!")
    print("Total job postings:", len(df))
    print("Total columns:", len(df.columns))

    return df


def generate_basic_summary(df):
    """Generate basic statistics about job postings."""

    summary = {
        "total_job_postings": len(df),
        "unique_job_titles": df["job_title_short"].nunique(),
        "unique_countries": df["job_country"].nunique(),
        "work_from_home_jobs": int(df["job_work_from_home"].sum()),
        "jobs_with_salary_data": int(df["has_salary_data"].sum()),
        "jobs_with_skills": int(df["has_skills_specified"].sum()),
    }

    summary_df = pd.DataFrame(
        list(summary.items()),
        columns=["Metric", "Value"]
    )

    summary_df.to_csv(
        OUTPUT_DIR / "basic_summary.csv",
        index=False
    )

    print("\nBasic Job Market Summary")
    print(summary_df.to_string(index=False))

    return summary_df


def analyze_job_roles(df):
    """Analyze the most frequently posted job roles."""

    role_counts = (
        df["job_title_short"]
        .dropna()
        .value_counts()
        .reset_index()
    )

    role_counts.columns = ["Job Role", "Posting Count"]

    # Save role analysis
    role_counts.to_csv(
        OUTPUT_DIR / "job_role_demand.csv",
        index=False
    )

    # Create visualization
    plt.figure(figsize=(12, 6))

    sns.barplot(
        data=role_counts,
        x="Posting Count",
        y="Job Role"
    )

    plt.title("Microsoft Job Postings by Job Role")
    plt.xlabel("Number of Job Postings")
    plt.ylabel("Job Role")
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "job_role_demand.png",
        dpi=300
    )

    plt.close()

    print("\nTop 10 Most Demanded Job Roles")
    print(role_counts.head(10).to_string(index=False))

    return role_counts

def analyze_geographic_demand(df):
    """Analyze Microsoft job postings by country."""

    country_counts = (
        df["job_country"]
        .dropna()
        .value_counts()
        .head(10)
        .reset_index()
    )

    country_counts.columns = [
        "Country",
        "Posting Count"
    ]

    country_counts.to_csv(
        OUTPUT_DIR / "geographic_demand.csv",
        index=False
    )

    plt.figure(figsize=(12, 6))

    sns.barplot(
        data=country_counts,
        x="Posting Count",
        y="Country"
    )

    plt.title("Top 10 Countries by Microsoft Job Postings")
    plt.xlabel("Number of Job Postings")
    plt.ylabel("Country")
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "geographic_demand.png",
        dpi=300
    )

    plt.close()

    print("\nTop 10 Countries by Job Postings")
    print(country_counts.to_string(index=False))

    return country_counts


def analyze_work_arrangements(df):
    """Analyze remote and non-remote job postings."""

    work_counts = (
        df["job_work_from_home"]
        .fillna(False)
        .map({True: "Work From Home", False: "Not Work From Home"})
        .value_counts()
        .reset_index()
    )

    work_counts.columns = [
        "Work Arrangement",
        "Posting Count"
    ]

    work_counts["Percentage"] = (
        work_counts["Posting Count"] / len(df) * 100
    ).round(2)

    work_counts.to_csv(
        OUTPUT_DIR / "work_arrangement_analysis.csv",
        index=False
    )

    plt.figure(figsize=(8, 6))

    plt.pie(
        work_counts["Posting Count"],
        labels=work_counts["Work Arrangement"],
        autopct="%1.1f%%",
        startangle=90
    )

    plt.title("Microsoft Job Work Arrangement Distribution")
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "work_arrangement_distribution.png",
        dpi=300
    )

    plt.close()

    print("\nWork Arrangement Analysis")
    print(work_counts.to_string(index=False))

    return work_counts

def analyze_employment_types(df):
    """Analyze job postings by employment schedule type."""

    schedule_counts = (
        df["job_schedule_type"]
        .dropna()
        .str.split(",")
        .explode()
        .str.strip()
        .value_counts()
        .reset_index()
    )

    schedule_counts.columns = [
        "Employment Type",
        "Posting Count"
    ]

    schedule_counts.to_csv(
        OUTPUT_DIR / "employment_type_analysis.csv",
        index=False
    )

    plt.figure(figsize=(11, 6))

    sns.barplot(
        data=schedule_counts.head(10),
        x="Posting Count",
        y="Employment Type"
    )

    plt.title("Microsoft Job Postings by Employment Type")
    plt.xlabel("Number of Job Postings")
    plt.ylabel("Employment Type")
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "employment_type_distribution.png",
        dpi=300
    )

    plt.close()

    print("\nEmployment Schedule Type Analysis")
    print(schedule_counts.head(10).to_string(index=False))

    return schedule_counts

def analyze_salary_distribution(df):
    """Analyze available annual salary information."""

    salary_df = df[
        df["salary_annual_standardized"].notna()
        & (df["salary_annual_standardized"] > 0)
    ].copy()

    if salary_df.empty:
        print("\nNo valid salary information available.")
        return pd.DataFrame()

    salary_summary = salary_df[
        "salary_annual_standardized"
    ].describe().to_frame().reset_index()

    salary_summary.columns = ["Statistic", "Annual Salary"]

    salary_summary["Annual Salary"] = (
        salary_summary["Annual Salary"].round(2)
    )

    salary_summary.to_csv(
        OUTPUT_DIR / "salary_summary.csv",
        index=False
    )

    plt.figure(figsize=(10, 6))

    sns.histplot(
        data=salary_df,
        x="salary_annual_standardized",
        bins=10,
        kde=True
    )

    plt.title("Distribution of Available Microsoft Annual Salaries")
    plt.xlabel("Annual Salary")
    plt.ylabel("Number of Job Postings")
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "salary_distribution.png",
        dpi=300
    )

    plt.close()

    print("\nSalary Distribution Analysis")
    print("Postings with valid salary data:", len(salary_df))
    print(salary_summary.to_string(index=False))

    return salary_summary

def analyze_skill_demand():
    """Analyze the most demanded skills across job postings."""

    skill_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "weekly_skill_demand.csv"
    )

    skill_df = pd.read_csv(skill_file)

    # Aggregate weekly skill demand across all weeks
    skill_counts = (
        skill_df.groupby("skill")["skill_posting_count"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    skill_counts.columns = [
        "Skill",
        "Posting Count"
    ]

    # Calculate percentage of total job postings
    skill_counts["Demand Percentage"] = (
        skill_counts["Posting Count"] / 498 * 100
    ).round(2)

    # Save complete skill analysis
    skill_counts.to_csv(
        OUTPUT_DIR / "skill_demand_analysis.csv",
        index=False
    )

    # Select top 10 skills for visualization
    top_skills = skill_counts.head(10)

    plt.figure(figsize=(12, 7))

    sns.barplot(
        data=top_skills,
        x="Posting Count",
        y="Skill"
    )

    plt.title("Top 10 Most Demanded Skills at Microsoft")
    plt.xlabel("Number of Job Postings")
    plt.ylabel("Skills")
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "top_10_skills.png",
        dpi=300
    )

    plt.close()

    print("\nTop 10 Most Demanded Skills")
    print(top_skills.to_string(index=False))

    return skill_counts

def analyze_weekly_skill_trends():
    """Visualize weekly demand trends for the top five skills."""

    skill_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "weekly_skill_demand.csv"
    )

    skill_df = pd.read_csv(skill_file)
    skill_df["week_start"] = pd.to_datetime(skill_df["week_start"])

    # Identify the top five skills
    top_5_skills = (
        skill_df.groupby("skill")["skill_posting_count"]
        .sum()
        .nlargest(5)
        .index.tolist()
    )

    # Get all available weeks
    all_weeks = pd.DatetimeIndex(
        sorted(skill_df["week_start"].unique())
    )

    # Create every skill-week combination
    complete_index = pd.MultiIndex.from_product(
        [all_weeks, top_5_skills],
        names=["week_start", "skill"]
    )

    # Aggregate existing weekly counts
    trend_df = (
        skill_df[
            skill_df["skill"].isin(top_5_skills)
        ]
        .groupby(["week_start", "skill"])["skill_posting_count"]
        .sum()
        .reindex(complete_index, fill_value=0)
        .reset_index()
    )

    # Save complete weekly trend data
    trend_df.to_csv(
        OUTPUT_DIR / "weekly_top_skill_trends.csv",
        index=False
    )

    # Generate line chart
    plt.figure(figsize=(14, 7))

    sns.lineplot(
        data=trend_df,
        x="week_start",
        y="skill_posting_count",
        hue="skill",
        marker="o"
    )

    plt.title("Weekly Demand Trends for Top 5 Skills")
    plt.xlabel("Week")
    plt.ylabel("Number of Job Postings")
    plt.xticks(rotation=45)
    plt.legend(title="Skills")
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "weekly_skill_trends.png",
        dpi=300
    )

    plt.close()

    print("\nWeekly Skill Trend Analysis")
    print("Skills analyzed:", top_5_skills)
    print("Weekly records analyzed:", len(trend_df))
    print("Expected records:", len(all_weeks) * len(top_5_skills))

    return trend_df



def main():
    """Run the exploratory analysis."""

    df = load_data()

    generate_basic_summary(df)

    analyze_job_roles(df)

    analyze_geographic_demand(df)

    analyze_work_arrangements(df)

    analyze_employment_types(df)

    analyze_salary_distribution(df)

    analyze_skill_demand()

    analyze_weekly_skill_trends()


if __name__ == "__main__":
    main()
