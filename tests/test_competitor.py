
import pandas as pd

from src.analysis.competitor import (
    normalize_skill,
    parse_skill_list,
    generate_company_summary,
    generate_skill_demand,
    generate_role_comparison,
)
from src.analysis.competitor import (
    normalize_skill,
    parse_skill_list,
    generate_company_summary,
    generate_skill_demand,
    generate_role_comparison,
    generate_country_comparison,
    generate_india_comparison,
)


def test_parse_skill_list():
    result = parse_skill_list("['python', 'sql']")

    assert result == ["python", "sql"]


def test_parse_invalid_skill_list():
    assert parse_skill_list("INVALID") == []


def test_normalize_existing_skill():
    name, category = normalize_skill("python")

    assert name == "Python"
    assert category is not None


def test_normalize_additional_skill():
    name, category = normalize_skill("ibm cloud")

    assert name == "IBM Cloud"
    assert category == "Cloud"

def test_additional_skill_categories():
    assert normalize_skill("redshift") == (
        "Amazon Redshift",
        "Data Engineering",
    )

    assert normalize_skill("express") == (
        "Express.js",
        "Development & Tools",
    )


def test_exclude_ambiguous_skill():
    name, category = normalize_skill("flow")

    assert name is None
    assert category is None


def test_generate_company_summary(tmp_path, monkeypatch):
    from src.analysis import competitor

    monkeypatch.setattr(competitor, "OUTPUT_DIR", tmp_path)

    df = pd.DataFrame({
        "company_name": ["Microsoft", "Microsoft", "Amazon"],
        "job_title_short": [
            "Data Engineer",
            "Data Analyst",
            "Data Engineer",
        ],
        "job_country": ["India", "USA", "USA"],
        "skill_data_available": [True, False, True],
    })

    result = generate_company_summary(df)

    microsoft = result[
        result["company_name"] == "Microsoft"
    ].iloc[0]

    assert microsoft["total_postings"] == 2
    assert microsoft["skill_data_available"] == 1
    assert microsoft["skill_coverage_pct"] == 50.0


def test_skill_demand_uses_available_postings(
    tmp_path, monkeypatch
):
    from src.analysis import competitor

    monkeypatch.setattr(competitor, "OUTPUT_DIR", tmp_path)

    df = pd.DataFrame({
        "company_name": ["Microsoft", "Microsoft", "Microsoft"],
        "skill_data_available": [True, True, False],
        "skill_list": [
            ["python", "sql"],
            ["python"],
            [],
        ],
    })

    result = generate_skill_demand(df)

    python = result[result["skill"] == "Python"].iloc[0]

    assert python["posting_count"] == 2
    assert python["skill_data_available"] == 2
    assert python["skill_demand_pct"] == 100.0


def test_role_comparison(tmp_path, monkeypatch):
    from src.analysis import competitor

    monkeypatch.setattr(competitor, "OUTPUT_DIR", tmp_path)

    df = pd.DataFrame({
        "company_name": [
            "Microsoft",
            "Microsoft",
            "Microsoft",
            "Amazon",
        ],
        "job_title_short": [
            "Data Engineer",
            "Data Engineer",
            "Data Analyst",
            "Data Engineer",
        ],
    })

    result = generate_role_comparison(df)

    microsoft = result[
        (result["company_name"] == "Microsoft")
        & (result["job_title_short"] == "Data Engineer")
    ].iloc[0]

    assert microsoft["posting_count"] == 2
    assert microsoft["role_demand_pct"] == 66.67

def test_country_comparison(tmp_path, monkeypatch):
    from src.analysis import competitor

    monkeypatch.setattr(competitor, "OUTPUT_DIR", tmp_path)

    df = pd.DataFrame({
        "company_name": [
            "Microsoft",
            "Microsoft",
            "Amazon",
        ],
        "job_country": [
            "India",
            "USA",
            "India",
        ],
    })

    result = generate_country_comparison(df)

    microsoft_india = result[
        (result["company_name"] == "Microsoft")
        & (result["job_country"] == "India")
    ].iloc[0]

    assert microsoft_india["posting_count"] == 1
    assert microsoft_india["company_total_postings"] == 2
    assert microsoft_india["country_demand_pct"] == 50.0

    assert (tmp_path / "country_demand_by_company.csv").exists()


def test_india_comparison(tmp_path, monkeypatch):
    from src.analysis import competitor

    monkeypatch.setattr(competitor, "OUTPUT_DIR", tmp_path)

    df = pd.DataFrame({
        "company_name": [
            "Microsoft",
            "Microsoft",
            "Microsoft",
            "Amazon",
        ],
        "job_country": [
            "India",
            "India",
            "USA",
            "India",
        ],
        "job_title_short": [
            "Data Engineer",
            "Data Scientist",
            "Data Engineer",
            "Data Analyst",
        ],
        "skill_data_available": [
            True,
            True,
            True,
            False,
        ],
        "skill_list": [
            ["python", "sql"],
            ["python"],
            ["java"],
            [],
        ],
    })

    summary, roles, skills = generate_india_comparison(df)

    microsoft = summary[
        summary["company_name"] == "Microsoft"
    ].iloc[0]

    assert microsoft["total_postings"] == 2
    assert microsoft["skill_data_available"] == 2
    assert microsoft["skill_coverage_pct"] == 100.0

    microsoft_python = skills[
        (skills["company_name"] == "Microsoft")
        & (skills["skill"] == "Python")
    ].iloc[0]

    assert microsoft_python["posting_count"] == 2
    assert microsoft_python["skill_demand_pct"] == 100.0

    microsoft_engineer = roles[
        (roles["company_name"] == "Microsoft")
        & (roles["job_title_short"] == "Data Engineer")
    ].iloc[0]

    assert microsoft_engineer["posting_count"] == 1
    assert microsoft_engineer["role_demand_pct"] == 50.0

    assert (tmp_path / "india_company_summary.csv").exists()
    assert (tmp_path / "india_role_demand_by_company.csv").exists()
    assert (tmp_path / "india_skill_demand_by_company.csv").exists()
