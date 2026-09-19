import subprocess
import sys
import threading

from flask import Flask, render_template, redirect, url_for, flash
from sqlalchemy import select, func, and_, or_

from models import Applicant, SessionLocal


app = Flask(__name__)
app.secret_key = "module3-gradcafe-app"

scrape_lock = threading.Lock()
scrape_running = False


def format_number(value):
    """Format averages to two decimal places."""
    return "N/A" if value is None else f"{value:.2f}"


def format_percent(value):
    """Format percentages to two decimal places."""
    return "N/A" if value is None else f"{value:.2f}%"


def get_analysis():
    """Retrieve analysis results from PostgreSQL using SQLAlchemy."""

    results = {}

    with SessionLocal() as session:

        # Question 1
        q1 = select(func.count(Applicant.p_id)).where(
            Applicant.term == "Fall 2026"
        )
        results["q1"] = session.scalar(q1)

        # Question 2
        international = session.scalar(
            select(func.count(Applicant.p_id)).where(
                Applicant.us_or_international == "International"
            )
        )

        usable_nationality = session.scalar(
            select(func.count(Applicant.p_id)).where(
                Applicant.us_or_international.in_(
                    ["American", "International"]
                )
            )
        )

        if usable_nationality:
            q2_result = (
                international / usable_nationality
            ) * 100
        else:
            q2_result = None

        results["q2"] = format_percent(q2_result)

        # Question 3
        q3_gpa = select(
            func.avg(Applicant.gpa)
        ).where(
            Applicant.gpa.is_not(None)
        )

        q3_gre = select(
            func.avg(Applicant.gre)
        ).where(
            Applicant.gre.is_not(None)
        )

        q3_gre_v = select(
            func.avg(Applicant.gre_v)
        ).where(
            Applicant.gre_v.is_not(None)
        )

        q3_gre_aw = select(
            func.avg(Applicant.gre_aw)
        ).where(
            Applicant.gre_aw.is_not(None)
        )

        results["q3_gpa"] = format_number(
            session.scalar(q3_gpa)
        )

        results["q3_gre"] = format_number(
            session.scalar(q3_gre)
        )

        results["q3_gre_v"] = format_number(
            session.scalar(q3_gre_v)
        )

        results["q3_gre_aw"] = format_number(
            session.scalar(q3_gre_aw)
        )

        # Question 4
        q4 = select(
            func.avg(Applicant.gpa)
        ).where(
            and_(
                Applicant.term == "Fall 2026",
                Applicant.us_or_international == "American",
                Applicant.gpa.is_not(None),
            )
        )

        results["q4"] = format_number(
            session.scalar(q4)
        )

        # Question 5
        fall_2025_total = session.scalar(
            select(func.count(Applicant.p_id)).where(
                Applicant.term == "Fall 2025"
            )
        )

        fall_2025_accepted = session.scalar(
            select(func.count(Applicant.p_id)).where(
                and_(
                    Applicant.term == "Fall 2025",
                    Applicant.status == "Accepted",
                )
            )
        )

        if fall_2025_total:
            q5_result = (
                fall_2025_accepted / fall_2025_total
            ) * 100
        else:
            q5_result = None

        results["q5"] = format_percent(q5_result)

        # Question 6
        q6 = select(
            func.avg(Applicant.gpa)
        ).where(
            and_(
                Applicant.term == "Fall 2026",
                Applicant.status == "Accepted",
                Applicant.gpa.is_not(None),
            )
        )

        results["q6"] = format_number(
            session.scalar(q6)
        )

        # Question 7
        q7 = select(
            func.count(Applicant.p_id)
        ).where(
            and_(
                Applicant.degree == "Masters",
                func.lower(
                    Applicant.program
                ).like("%computer science%"),
                or_(
                    func.lower(
                        Applicant.university
                    ).like("%johns hopkins university%"),
                    func.lower(
                        Applicant.university
                    ) == "jhu",
                ),
            )
        )

        results["q7"] = session.scalar(q7)

        # Question 8
        q8 = select(
            func.count(Applicant.p_id)
        ).where(
            and_(
                Applicant.term == "Fall 2026",
                Applicant.status == "Accepted",
                Applicant.degree == "PhD",
                func.lower(
                    Applicant.program
                ).like("%computer science%"),
                or_(
                    func.lower(
                        Applicant.university
                    ).like("%georgetown university%"),
                    func.lower(
                        Applicant.university
                    ).like(
                        "%massachusetts institute of technology%"
                    ),
                    func.lower(
                        Applicant.university
                    ) == "mit",
                    func.lower(
                        Applicant.university
                    ).like("%stanford university%"),
                    func.lower(
                        Applicant.university
                    ).like("%carnegie mellon university%"),
                ),
            )
        )

        q8_result = session.scalar(q8)
        results["q8"] = q8_result

        # Question 9
        q9 = select(
            func.count(Applicant.p_id)
        ).where(
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

        results["q9"] = q9_result
        results["q9_difference"] = (
            f"{q9_result - q8_result:+d}"
        )

        # Original Question 1
        fall_2026_total = session.scalar(
            select(func.count(Applicant.p_id)).where(
                Applicant.term == "Fall 2026"
            )
        )

        fall_2026_accepted = session.scalar(
            select(func.count(Applicant.p_id)).where(
                and_(
                    Applicant.term == "Fall 2026",
                    Applicant.status == "Accepted",
                )
            )
        )

        if fall_2026_total:
            original_1 = (
                fall_2026_accepted / fall_2026_total
            ) * 100
        else:
            original_1 = None

        results["original_1"] = format_percent(
            original_1
        )

        # Original Question 2
        original_2 = select(
            func.avg(Applicant.gpa)
        ).where(
            and_(
                Applicant.us_or_international
                == "International",
                Applicant.gpa.is_not(None),
            )
        )

        results["original_2"] = format_number(
            session.scalar(original_2)
        )

    return results


@app.route("/")
def index():
    results = get_analysis()

    return render_template(
        "index.html",
        results=results,
        scrape_running=scrape_running,
    )


@app.route("/update-analysis", methods=["POST"])
def update_analysis():

    if scrape_running:
        flash(
            "New data is currently being retrieved. "
            "The analysis shown uses the current database."
        )
    else:
        flash(
            "Analysis updated using the latest data "
            "currently stored in PostgreSQL."
        )

    return redirect(url_for("index"))


def run_data_refresh():
    """
    Pull new GradCafe data, clean it,
    and load it into PostgreSQL.
    """
    global scrape_running

    try:
        subprocess.run(
            [sys.executable, "refresh_data.py"],
            check=True,
        )

        subprocess.run(
            [sys.executable, "clean.py"],
            check=True,
        )

        subprocess.run(
            [sys.executable, "load_data.py"],
            check=True,
        )

    except subprocess.CalledProcessError as error:
        print(f"Data refresh failed: {error}")

    finally:
        scrape_running = False
        scrape_lock.release()


@app.route("/pull-data", methods=["POST"])
def pull_data():
    global scrape_running

    if not scrape_lock.acquire(blocking=False):
        flash(
            "Pull Data is already running. "
            "Please wait for the current data "
            "retrieval to finish."
        )

        return redirect(url_for("index"))

    scrape_running = True

    thread = threading.Thread(
        target=run_data_refresh,
        daemon=True,
    )

    thread.start()

    flash(
        "Pull Data started. New GradCafe entries "
        "are being retrieved in the background. "
        "Use Update Analysis after the process finishes."
    )

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(
        debug=True,
        port=8080,
    )