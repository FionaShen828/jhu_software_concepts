from sqlalchemy import select, func, and_, or_
from models import Applicant, SessionLocal


def format_number(value):
    """Format averages to two decimal places."""
    return "N/A" if value is None else f"{value:.2f}"


def format_percent(value):
    """Format percentages to two decimal places."""
    return "N/A" if value is None else f"{value:.2f}%"


def main():
    with SessionLocal() as session:

        # ---------------------------------------------------------
        # Question 1
        # How many entries applied for Fall 2026?
        # ---------------------------------------------------------
        q1 = select(func.count(Applicant.p_id)).where(
            Applicant.term == "Fall 2026"
        )

        q1_result = session.scalar(q1)

        print("\nQuestion 1")
        print(f"Fall 2026 applicant count: {q1_result}")


        # ---------------------------------------------------------
        # Question 4
        # Average GPA of American applicants who applied
        # for Fall 2026.
        # ---------------------------------------------------------
        q4 = select(func.avg(Applicant.gpa)).where(
            and_(
                Applicant.term == "Fall 2026",
                Applicant.us_or_international == "American",
                Applicant.gpa.is_not(None),
            )
        )

        q4_result = session.scalar(q4)

        print("\nQuestion 4")
        print(
            "Average GPA of American Fall 2026 applicants: "
            f"{format_number(q4_result)}"
        )


        # ---------------------------------------------------------
        # Question 5
        # Percentage of Fall 2025 entries that are acceptances.
        # ---------------------------------------------------------
        q5_total = select(func.count(Applicant.p_id)).where(
            Applicant.term == "Fall 2025"
        )

        q5_accepted = select(func.count(Applicant.p_id)).where(
            and_(
                Applicant.term == "Fall 2025",
                Applicant.status == "Accepted",
            )
        )

        total_fall_2025 = session.scalar(q5_total)
        accepted_fall_2025 = session.scalar(q5_accepted)

        if total_fall_2025:
            q5_result = (
                accepted_fall_2025 / total_fall_2025
            ) * 100
        else:
            q5_result = None

        print("\nQuestion 5")
        print(
            "Fall 2025 acceptance percentage: "
            f"{format_percent(q5_result)}"
        )


        # ---------------------------------------------------------
        # Question 8
        # Fall 2026 accepted PhD Computer Science applicants
        # at Georgetown, MIT, Stanford, or Carnegie Mellon,
        # using original downloaded university/program fields.
        # ---------------------------------------------------------
        q8 = select(func.count(Applicant.p_id)).where(
            and_(
                Applicant.term == "Fall 2026",
                Applicant.status == "Accepted",
                Applicant.degree == "PhD",
                func.lower(Applicant.program).like(
                    "%computer science%"
                ),
                or_(
                    func.lower(Applicant.university).like(
                        "%georgetown university%"
                    ),
                    func.lower(Applicant.university).like(
                        "%massachusetts institute of technology%"
                    ),
                    func.lower(Applicant.university) == "mit",
                    func.lower(Applicant.university).like(
                        "%stanford university%"
                    ),
                    func.lower(Applicant.university).like(
                        "%carnegie mellon university%"
                    ),
                ),
            )
        )

        q8_result = session.scalar(q8)

        print("\nQuestion 8")
        print(f"Original-field count: {q8_result}")


        # ---------------------------------------------------------
        # Question 9
        # Repeat Question 8 using LLM-generated program
        # and university fields.
        # ---------------------------------------------------------
        q9 = select(func.count(Applicant.p_id)).where(
            and_(
                Applicant.term == "Fall 2026",
                Applicant.status == "Accepted",
                Applicant.degree == "PhD",
                func.lower(
                    Applicant.llm_generated_program
                ).like("%computer science%"),
                or_(
                    func.lower(
                        Applicant.llm_generated_university
                    ).like("%georgetown university%"),
                    func.lower(
                        Applicant.llm_generated_university
                    ).like(
                        "%massachusetts institute of technology%"
                    ),
                    func.lower(
                        Applicant.llm_generated_university
                    ) == "mit",
                    func.lower(
                        Applicant.llm_generated_university
                    ).like("%stanford university%"),
                    func.lower(
                        Applicant.llm_generated_university
                    ).like("%carnegie mellon university%"),
                ),
            )
        )

        q9_result = session.scalar(q9)
        difference = q9_result - q8_result

        print("\nQuestion 9")
        print(f"Original-field count: {q8_result}")
        print(f"LLM-field count: {q9_result}")
        print(f"Difference: {difference:+d}")


        # ---------------------------------------------------------
        # Original Question
        # What percentage of Fall 2026 entries are acceptances?
        # ---------------------------------------------------------
        original_total = select(
            func.count(Applicant.p_id)
        ).where(
            Applicant.term == "Fall 2026"
        )

        original_accepted = select(
            func.count(Applicant.p_id)
        ).where(
            and_(
                Applicant.term == "Fall 2026",
                Applicant.status == "Accepted",
            )
        )

        total_fall_2026 = session.scalar(original_total)
        accepted_fall_2026 = session.scalar(original_accepted)

        if total_fall_2026:
            original_result = (
                accepted_fall_2026 / total_fall_2026
            ) * 100
        else:
            original_result = None

        print("\nOriginal Question")
        print(
            "What percentage of Fall 2026 entries are acceptances?"
        )
        print(
            "Fall 2026 acceptance percentage: "
            f"{format_percent(original_result)}"
        )


if __name__ == "__main__":  # pragma: no cover
    main()