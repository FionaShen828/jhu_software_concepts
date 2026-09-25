import os

import psycopg


def get_connection():
    """Connect to the PostgreSQL gradcafe database."""
    return psycopg.connect(
        dbname="gradcafe",
        user="postgres",
        password=os.environ.get("DB_PASSWORD"),
        host="localhost",
        port="5432",
    )


def fetch_one(cur, query, params=None):
    """Run a query and return the first value."""
    if params is None:
        cur.execute(query)
    else:
        cur.execute(query, params)

    row = cur.fetchone()
    return row[0] if row else None


def format_number(value):
    """Format averages to two decimal places."""
    return "N/A" if value is None else f"{value:.2f}"


def format_percent(value):
    """Format percentages to two decimal places."""
    return "N/A" if value is None else f"{value:.2f}%"


def main():
    with get_connection() as conn:
        with conn.cursor() as cur:

            # ---------------------------------------------------------
            # Question 1
            # How many entries applied for Fall 2026?
            # ---------------------------------------------------------
            q1 = """
                SELECT COUNT(*)
                FROM applicants
                WHERE term = 'Fall 2026';
            """
            q1_result = fetch_one(cur, q1)

            print("\nQuestion 1")
            print(f"Fall 2026 applicant count: {q1_result}")


            # ---------------------------------------------------------
            # Question 2
            # Among entries with usable nationality classification,
            # what percentage are international?
            # ---------------------------------------------------------
            q2 = """
                SELECT
                    100.0 * COUNT(*) FILTER (
                        WHERE us_or_international = 'International'
                    ) / NULLIF(
                        COUNT(*) FILTER (
                            WHERE us_or_international IN (
                                'American',
                                'International'
                            )
                        ),
                        0
                    )
                FROM applicants;
            """
            q2_result = fetch_one(cur, q2)

            print("\nQuestion 2")
            print(
                "Percent international: "
                f"{format_percent(q2_result)}"
            )


            # ---------------------------------------------------------
            # Question 3
            # Average GPA, GRE Quantitative, GRE Verbal,
            # and GRE Analytical Writing.
            # Each metric is averaged independently.
            # ---------------------------------------------------------
            q3 = """
                SELECT
                    AVG(gpa),
                    AVG(gre),
                    AVG(gre_v),
                    AVG(gre_aw)
                FROM applicants;
            """
            cur.execute(q3)
            q3_result = cur.fetchone()

            print("\nQuestion 3")
            print(f"Average GPA: {format_number(q3_result[0])}")
            print(
                "Average GRE Quantitative: "
                f"{format_number(q3_result[1])}"
            )
            print(
                "Average GRE Verbal: "
                f"{format_number(q3_result[2])}"
            )
            print(
                "Average GRE Analytical Writing: "
                f"{format_number(q3_result[3])}"
            )


            # ---------------------------------------------------------
            # Question 4
            # Average GPA of American applicants who applied
            # for Fall 2026.
            # ---------------------------------------------------------
            q4 = """
                SELECT AVG(gpa)
                FROM applicants
                WHERE term = 'Fall 2026'
                  AND us_or_international = 'American'
                  AND gpa IS NOT NULL;
            """
            q4_result = fetch_one(cur, q4)

            print("\nQuestion 4")
            print(
                "Average GPA of American Fall 2026 applicants: "
                f"{format_number(q4_result)}"
            )


            # ---------------------------------------------------------
            # Question 5
            # Percentage of Fall 2025 entries that are acceptances.
            # ---------------------------------------------------------
            q5 = """
                SELECT
                    100.0 * COUNT(*) FILTER (
                        WHERE status = 'Accepted'
                    ) / NULLIF(COUNT(*), 0)
                FROM applicants
                WHERE term = 'Fall 2025';
            """
            q5_result = fetch_one(cur, q5)

            print("\nQuestion 5")
            print(
                "Fall 2025 acceptance percentage: "
                f"{format_percent(q5_result)}"
            )


            # ---------------------------------------------------------
            # Question 6
            # Average GPA of accepted Fall 2026 applicants.
            # ---------------------------------------------------------
            q6 = """
                SELECT AVG(gpa)
                FROM applicants
                WHERE term = 'Fall 2026'
                  AND status = 'Accepted'
                  AND gpa IS NOT NULL;
            """
            q6_result = fetch_one(cur, q6)

            print("\nQuestion 6")
            print(
                "Average GPA of accepted Fall 2026 applicants: "
                f"{format_number(q6_result)}"
            )


            # ---------------------------------------------------------
            # Question 7
            # Count applicants to Johns Hopkins University for a
            # master's degree in Computer Science using original data.
            # ---------------------------------------------------------
            q7 = """
                SELECT COUNT(*)
                FROM applicants
                WHERE degree = 'Masters'
                  AND LOWER(program) LIKE '%computer science%'
                  AND (
                        LOWER(university) LIKE '%johns hopkins university%'
                        OR LOWER(university) = 'jhu'
                      );
            """
            q7_result = fetch_one(cur, q7)

            print("\nQuestion 7")
            print(
                "JHU Computer Science master's applicant count: "
                f"{q7_result}"
            )


            # ---------------------------------------------------------
            # Question 8
            # Count Fall 2026 accepted PhD Computer Science applicants
            # at Georgetown, MIT, Stanford, or Carnegie Mellon using
            # original downloaded program/university fields.
            # ---------------------------------------------------------
            q8 = """
                SELECT COUNT(*)
                FROM applicants
                WHERE term = 'Fall 2026'
                  AND status = 'Accepted'
                  AND degree = 'PhD'
                  AND LOWER(program) LIKE '%computer science%'
                  AND (
                        LOWER(university) LIKE '%georgetown university%'
                        OR LOWER(university) LIKE
                           '%massachusetts institute of technology%'
                        OR LOWER(university) = 'mit'
                        OR LOWER(university) LIKE '%stanford university%'
                        OR LOWER(university) LIKE
                           '%carnegie mellon university%'
                      );
            """
            q8_result = fetch_one(cur, q8)

            print("\nQuestion 8")
            print(f"Original-field count: {q8_result}")


            # ---------------------------------------------------------
            # Question 9
            # Repeat Question 8 using LLM-generated program and
            # university fields while keeping original term,
            # degree, and status fields.
            # ---------------------------------------------------------
            q9 = """
                SELECT COUNT(*)
                FROM applicants
                WHERE term = 'Fall 2026'
                  AND status = 'Accepted'
                  AND degree = 'PhD'
                  AND LOWER(llm_generated_program)
                      LIKE '%computer science%'
                  AND (
                        LOWER(llm_generated_university)
                            LIKE '%georgetown university%'
                        OR LOWER(llm_generated_university)
                            LIKE '%massachusetts institute of technology%'
                        OR LOWER(llm_generated_university) = 'mit'
                        OR LOWER(llm_generated_university)
                            LIKE '%stanford university%'
                        OR LOWER(llm_generated_university)
                            LIKE '%carnegie mellon university%'
                      );
            """
            q9_result = fetch_one(cur, q9)
            difference = q9_result - q8_result

            print("\nQuestion 9")
            print(f"Original-field count: {q8_result}")
            print(f"LLM-field count: {q9_result}")
            print(f"Difference: {difference:+d}")


            # ---------------------------------------------------------
            # Original Question 1
            # What percentage of Fall 2026 entries are acceptances?
            # ---------------------------------------------------------
            original_q1 = """
                SELECT
                    100.0 * COUNT(*) FILTER (
                        WHERE status = 'Accepted'
                    ) / NULLIF(COUNT(*), 0)
                FROM applicants
                WHERE term = 'Fall 2026';
            """
            original_q1_result = fetch_one(cur, original_q1)

            print("\nOriginal Question 1")
            print(
                "What percentage of Fall 2026 entries are acceptances?"
            )
            print(
                "Fall 2026 acceptance percentage: "
                f"{format_percent(original_q1_result)}"
            )


            # ---------------------------------------------------------
            # Original Question 2
            # What is the average GPA of international applicants?
            # ---------------------------------------------------------
            original_q2 = """
                SELECT AVG(gpa)
                FROM applicants
                WHERE us_or_international = 'International'
                  AND gpa IS NOT NULL;
            """
            original_q2_result = fetch_one(cur, original_q2)

            print("\nOriginal Question 2")
            print(
                "What is the average GPA of international applicants?"
            )
            print(
                "Average GPA of international applicants: "
                f"{format_number(original_q2_result)}"
            )


if __name__ == "__main__":  # pragma: no cover
    main()