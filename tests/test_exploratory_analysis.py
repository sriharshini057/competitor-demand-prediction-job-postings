
import pandas as pd
import matplotlib
matplotlib.use("Agg")

from src.analysis.exploratory_analysis import (
    generate_basic_summary,
    analyze_job_roles,
    analyze_weekly_skill_trends,
)


def test_generate_basic_summary(capsys):
    """Test basic dataset summary calculations."""

    df = pd.DataFrame({
       "job_title_short": ["Data Engineer", "Data Analyst"],
       "job_country": ["India", "USA"],
       "job_work_from_home": [True, False],
       "salary_year_avg": [80000, None],
       "has_salary_data": [True, False],
       "has_skills_specified": [True, False],
       "job_skills": ["Python, SQL", None],
})

    generate_basic_summary(df)

    output = capsys.readouterr().out

    assert "total_job_postings" in output
    assert "2" in output


def test_analyze_job_roles(tmp_path, monkeypatch):
    """Test job role demand analysis."""

    from src.analysis import exploratory_analysis as analysis

    monkeypatch.setattr(analysis, "OUTPUT_DIR", tmp_path)

    df = pd.DataFrame({
        "job_title_short": [
            "Data Engineer",
            "Data Engineer",
            "Data Analyst",
        ]
    })

    analysis.analyze_job_roles(df)

    result = pd.read_csv(tmp_path / "job_role_demand.csv")

    assert result.iloc[0]["Job Role"] == "Data Engineer"
    assert result.iloc[0]["Posting Count"] == 2


def test_weekly_skill_trends_complete():
    """Test that weekly skill trends include all skill-week combinations."""

    result = analyze_weekly_skill_trends()

    assert len(result) == 260
    assert result["skill"].nunique() == 5
    assert result["week_start"].nunique() == 52
    assert result["skill_posting_count"].ge(0).all()
