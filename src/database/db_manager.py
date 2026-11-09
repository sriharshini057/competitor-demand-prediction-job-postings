
"""SQLite database manager for the Competitor Demand Prediction project.

Sprint 5:
- Database connection and schema initialization
- DataFrame ingestion
- Normalized skill and entity storage
- SQL query execution
"""

import ast
import json
import sqlite3
from collections import Counter
from pathlib import Path
from contextlib import closing

import pandas as pd


class DatabaseManager:
    """Manage SQLite storage for processed job-posting data."""

    def __init__(
        self,
        db_path="data/database/competitor_demand.db",
        schema_path="sql/schema.sql",
    ):
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)

    def connect(self):
        """Create a SQLite connection with foreign keys enabled."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        return conn

    def initialize_database(self):
        """Create database tables and indexes from schema.sql."""
        if not self.schema_path.exists():
           raise FileNotFoundError(
              f"Schema file not found: {self.schema_path}"
        )

        schema = self.schema_path.read_text(encoding="utf-8-sig")

        with closing(self.connect()) as conn:
             conn.executescript(schema)

        return True

    @staticmethod
    def _clean_value(value):
        """Convert Pandas values into SQLite-compatible values."""
        if value is None:
            return None

        missing = pd.isna(value)
        if bool(missing):
            return None

        if isinstance(value, bool) or type(value).__name__ == "bool_":
            return int(value)

        if hasattr(value, "item"):
            return value.item()

        return value

    @staticmethod
    def _parse_structured_value(value, expected_type):
        """Parse JSON or Python-style serialized lists/dictionaries."""
        if value is None:
            return expected_type()

        if not isinstance(value, str):
            return value if isinstance(value, expected_type) else expected_type()

        value = value.strip()

        if not value:
            return expected_type()

        for parser in (json.loads, ast.literal_eval):
            try:
                result = parser(value)
                if isinstance(result, expected_type):
                    return result
            except (ValueError, SyntaxError, TypeError):
                continue

        return expected_type()

    def load_dataframe(self, df):
        """Load job postings and normalized skills/entities.

        A database containing existing job postings is not overwritten.
        """
        if df.empty:
            raise ValueError("Cannot load an empty DataFrame.")

        if df.columns.duplicated().any():
            raise ValueError("DataFrame contains duplicate column names.")

        stats = {
            "jobs_loaded": 0,
            "companies_loaded": 0,
            "skills_loaded": 0,
            "job_skill_links": 0,
            "categories_loaded": 0,
            "entities_loaded": 0,
            "job_entity_links": 0,
        }

        with closing(self.connect()) as conn:
            with conn:
                existing = conn.execute(
                    "SELECT COUNT(*) FROM job_postings"
                ).fetchone()[0]

                if existing:
                    raise ValueError(
                        "Database already contains job postings. "
                        "Use a fresh database or explicitly manage "
                        "the existing data before loading again."
                    )

                table_info = conn.execute(
                    "PRAGMA table_info(job_postings)"
                ).fetchall()

                dataset_columns = [
                    row["name"]
                    for row in table_info
                    if row["name"] not in {
                        "job_id",
                        "source_row_number",
                        "company_id",
                    }
                ]

                missing = set(dataset_columns) - set(df.columns)

                if missing:
                    raise ValueError(
                        f"Missing required dataset columns: {sorted(missing)}"
                    )

                insert_columns = [
                    "source_row_number",
                    "company_id",
                    *dataset_columns,
                ]

                placeholders = ", ".join(
                    ["?"] * len(insert_columns)
                )

                insert_sql = (
                    f"INSERT INTO job_postings "
                    f"({', '.join(insert_columns)}) "
                    f"VALUES ({placeholders})"
                )

                company_cache = {}
                skill_cache = {}
                category_cache = {}
                entity_cache = {}

                for row_number, record in enumerate(
                    df.to_dict(orient="records"), start=1
                ):
                    company_name = str(record["company_name"]).strip()

                    if not company_name:
                        raise ValueError(
                            f"Missing company name at source row {row_number}"
                        )

                    if company_name not in company_cache:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO companies (company_name)
                            VALUES (?)
                            """,
                            (company_name,),
                        )

                        company_id = conn.execute(
                            """
                            SELECT company_id FROM companies
                            WHERE company_name = ?
                            """,
                            (company_name,),
                        ).fetchone()["company_id"]

                        company_cache[company_name] = company_id

                    company_id = company_cache[company_name]

                    values = [
                        row_number,
                        company_id,
                        *[
                            self._clean_value(record[column])
                            for column in dataset_columns
                        ],
                    ]

                    cursor = conn.execute(insert_sql, values)
                    job_id = cursor.lastrowid
                    stats["jobs_loaded"] += 1

                    # Parse extracted skills.
                    skills = self._parse_structured_value(
                        record.get("extracted_skills"),
                        list,
                    )

                    skill_ids = set()

                    for skill in skills:
                        if not isinstance(skill, str) or not skill.strip():
                            continue

                        skill_name = skill.strip()

                        if skill_name not in skill_cache:
                            conn.execute(
                                """
                                INSERT OR IGNORE INTO skills (skill_name)
                                VALUES (?)
                                """,
                                (skill_name,),
                            )

                            skill_id = conn.execute(
                                """
                                SELECT skill_id FROM skills
                                WHERE skill_name = ?
                                """,
                                (skill_name,),
                            ).fetchone()["skill_id"]

                            skill_cache[skill_name] = skill_id

                        skill_id = skill_cache[skill_name]
                        skill_ids.add(skill_id)

                        conn.execute(
                            """
                            INSERT INTO job_skill_map (job_id, skill_id)
                            VALUES (?, ?)
                            """,
                            (job_id, skill_id),
                        )

                        stats["job_skill_links"] += 1

                    # Parse skill categories.
                    categories = self._parse_structured_value(
                        record.get("skill_categories"),
                        dict,
                    )

                    for category_name, category_skills in categories.items():
                        if not isinstance(category_name, str):
                            continue

                        category_name = category_name.strip()

                        if not category_name:
                            continue

                        if category_name not in category_cache:
                            conn.execute(
                                """
                                INSERT OR IGNORE INTO skill_categories
                                (category_name) VALUES (?)
                                """,
                                (category_name,),
                            )

                            category_id = conn.execute(
                                """
                                SELECT category_id FROM skill_categories
                                WHERE category_name = ?
                                """,
                                (category_name,),
                            ).fetchone()["category_id"]

                            category_cache[category_name] = category_id

                        category_id = category_cache[category_name]

                        if not isinstance(category_skills, list):
                            continue

                        for skill in category_skills:
                            if not isinstance(skill, str) or not skill.strip():
                                continue

                            skill_name = skill.strip()

                            if skill_name not in skill_cache:
                                conn.execute(
                                    """
                                    INSERT OR IGNORE INTO skills (skill_name)
                                    VALUES (?)
                                    """,
                                    (skill_name,),
                                )

                                skill_id = conn.execute(
                                    """
                                    SELECT skill_id FROM skills
                                    WHERE skill_name = ?
                                    """,
                                    (skill_name,),
                                ).fetchone()["skill_id"]

                                skill_cache[skill_name] = skill_id

                            skill_id = skill_cache[skill_name]

                            conn.execute(
                                """
                                INSERT OR IGNORE INTO skill_category_map
                                (skill_id, category_id)
                                VALUES (?, ?)
                                """,
                                (skill_id, category_id),
                            )

                    # Parse named entities and count repeated mentions.
                    entities = self._parse_structured_value(
                        record.get("extracted_entities"),
                        list,
                    )

                    entity_counts = Counter(
                        (
                            entity["text"].strip(),
                            entity["label"].strip(),
                        )
                        for entity in entities
                        if isinstance(entity, dict)
                        and isinstance(entity.get("text"), str)
                        and entity["text"].strip()
                        and isinstance(entity.get("label"), str)
                        and entity["label"].strip()
                    )

                    for (entity_text, entity_label), count in (
                        entity_counts.items()
                    ):
                        entity_key = (entity_text, entity_label)

                        if entity_key not in entity_cache:
                            conn.execute(
                                """
                                INSERT OR IGNORE INTO entities
                                (entity_text, entity_label)
                                VALUES (?, ?)
                                """,
                                entity_key,
                            )

                            entity_id = conn.execute(
                                """
                                SELECT entity_id FROM entities
                                WHERE entity_text = ? AND entity_label = ?
                                """,
                                entity_key,
                            ).fetchone()["entity_id"]

                            entity_cache[entity_key] = entity_id

                        entity_id = entity_cache[entity_key]

                        conn.execute(
                            """
                            INSERT INTO job_entities
                            (job_id, entity_id, mention_count)
                            VALUES (?, ?, ?)
                            """,
                            (job_id, entity_id, count),
                        )

                        stats["job_entity_links"] += 1

                stats["companies_loaded"] = conn.execute(
                    "SELECT COUNT(*) FROM companies"
                ).fetchone()[0]

                stats["skills_loaded"] = conn.execute(
                    "SELECT COUNT(*) FROM skills"
                ).fetchone()[0]

                stats["categories_loaded"] = conn.execute(
                    "SELECT COUNT(*) FROM skill_categories"
                ).fetchone()[0]

                stats["entities_loaded"] = conn.execute(
                    "SELECT COUNT(*) FROM entities"
                ).fetchone()[0]

        return stats

    def execute_query(self, query, params=()):
         """Execute a read-only SQL query and return dictionary rows."""
         with closing(self.connect()) as conn:
             conn.execute("PRAGMA query_only = ON")

             if not query.lstrip().upper().startswith(
                 ("SELECT", "PRAGMA", "WITH", "EXPLAIN")
        ):
                  raise ValueError("Only read-only SQL queries are supported.")

             return [
                 dict(row)
                 for row in conn.execute(query, params).fetchall()
        ]

    def get_table_counts(self):
        """Return row counts for all project tables."""
        tables = [
            "companies",
            "job_postings",
            "skills",
            "job_skill_map",
            "skill_categories",
            "skill_category_map",
            "entities",
            "job_entities",
        ]

        with closing(self.connect()) as conn:
            return {
                table: conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
                for table in tables
            }
