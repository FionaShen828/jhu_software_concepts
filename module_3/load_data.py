import json
import os
from datetime import datetime
from pathlib import Path

import psycopg


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "llm_extend_applicant_data.json"


def get_connection():
    """Connect to the PostgreSQL gradcafe database."""
    return psycopg.connect(
        dbname="gradcafe",
        user="postgres",
        password=os.environ.get("DB_PASSWORD"),
        host="localhost",
        port="5432",
    )


def parse_date(value):
    """Convert GradCafe date strings into Python date objects."""
    if not value:
        return None

    try:
        return datetime.strptime(value.strip(), "%b %d, %Y").date()
    except (ValueError, AttributeError):
        return None


def safe_float(value):
    """Convert numeric values to floats while allowing missing data."""
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def create_table(conn):
    """Create the applicants table if it does not already exist."""
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS applicants (
                p_id SERIAL PRIMARY KEY,
                university TEXT,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT UNIQUE,
                status TEXT,
                term TEXT,
                us_or_international TEXT,
                gpa FLOAT,
                gre FLOAT,
                gre_v FLOAT,
                gre_aw FLOAT,
                degree TEXT,
                llm_generated_program TEXT,
                llm_generated_university TEXT
            );
            """
        )

        # Add university if the table was created by an older version
        # of this script that did not include the column.
        cur.execute(
            """
            ALTER TABLE applicants
            ADD COLUMN IF NOT EXISTS university TEXT;
            """
        )

    conn.commit()


def load_data():
    print("Loading cleaned applicant data...")

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        applicants = json.load(file)

    print(f"Applicants found: {len(applicants):,}")

    inserted = 0

    with get_connection() as conn:
        create_table(conn)

        with conn.cursor() as cur:
            for applicant in applicants:
                cur.execute(
                    """
                    INSERT INTO applicants (
                        university,
                        program,
                        comments,
                        date_added,
                        url,
                        status,
                        term,
                        us_or_international,
                        gpa,
                        gre,
                        gre_v,
                        gre_aw,
                        degree,
                        llm_generated_program,
                        llm_generated_university
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (url) DO NOTHING;
                    """,
                    (
                        applicant.get("university"),
                        applicant.get("program"),
                        applicant.get("comments"),
                        parse_date(applicant.get("date_added")),
                        applicant.get("url"),
                        applicant.get("status"),
                        applicant.get("term"),
                        applicant.get("applicant_type"),
                        safe_float(applicant.get("gpa")),
                        safe_float(applicant.get("gre")),
                        safe_float(applicant.get("gre_v")),
                        safe_float(applicant.get("gre_aw")),
                        applicant.get("degree"),
                        applicant.get("llm-generated-program"),
                        applicant.get("llm-generated-university"),
                    ),
                )

                if cur.rowcount == 1:
                    inserted += 1

        conn.commit()

    print(f"New applicants inserted: {inserted:,}")
    print("Database load complete.")


if __name__ == "__main__":
    load_data()