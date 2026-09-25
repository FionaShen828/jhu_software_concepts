import subprocess
import sys
import threading
from pathlib import Path

from flask import Flask, render_template, redirect, url_for, flash, jsonify
from sqlalchemy import select, func, and_, or_

from models import Applicant, SessionLocal


# ---------------------------------------------------------
# Flask setup
# ---------------------------------------------------------

def create_app(test_config=None):
    """Create and configure the Flask application."""
    flask_app = Flask(__name__)

    flask_app.config.from_mapping(
        SECRET_KEY="module4-gradcafe-app"
    )

    if test_config is not None:
        flask_app.config.update(test_config)

    return flask_app


app = create_app()

scrape_lock = threading.Lock()
scrape_running = False

BASE_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------

def format_number(value):
    """Format averages to two decimal places."""
    return "N/A" if value is None else f"{value:.2f}"


def format_percent(value):
    """Format percentages to two decimal places."""
    return "N/A" if value is None else f"{value:.2f}%"


# ---------------------------------------------------------
# Analysis
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Flask routes
# ---------------------------------------------------------

@app.route("/")
@app.route("/analysis")
def index():
    """Render the GradCafe analysis page."""

    results = get_analysis()

    return render_template(
        "index.html",
        results=results,
        scrape_running=scrape_running,
    )


@app.route("/update-analysis", methods=["POST"])
def update_analysis():
    """Refresh analysis using the current PostgreSQL data."""

    if scrape_running:
        return jsonify({
            "ok": False,
            "busy": True
        }), 409

    # Run the query again so the current database is checked.
    get_analysis()

    return jsonify({
        "ok": True,
        "busy": False
    }), 200


# ---------------------------------------------------------
# Pull Data
# ---------------------------------------------------------

def run_data_refresh():
    """
    Pull new GradCafe data, clean it,
    and load it into PostgreSQL.
    """

    global scrape_running

    try:
        subprocess.run(
            [sys.executable, str(BASE_DIR / "refresh_data.py")],
            check=True,
            cwd=BASE_DIR,
        )

        subprocess.run(
            [sys.executable, str(BASE_DIR / "clean.py")],
            check=True,
            cwd=BASE_DIR,
        )

        subprocess.run(
            [sys.executable, str(BASE_DIR / "load_data.py")],
            check=True,
            cwd=BASE_DIR,
        )

    except subprocess.CalledProcessError as error:
        print(f"Data refresh failed: {error}")

    finally:
        scrape_running = False

        if scrape_lock.locked():
            scrape_lock.release()


@app.route("/pull-data", methods=["POST"])
def pull_data():
    """Start the GradCafe data refresh process."""

    global scrape_running

    if not scrape_lock.acquire(blocking=False):
        return jsonify({
            "ok": False,
            "busy": True
        }), 409

    scrape_running = True

    # Module 4 tests can provide a safe fake refresh function.
    test_refresh = app.config.get("TEST_REFRESH_FUNCTION")

    if test_refresh is not None:
        try:
            test_refresh()
        finally:
            scrape_running = False

            if scrape_lock.locked():
                scrape_lock.release()

        return jsonify({
            "ok": True,
            "busy": False
        }), 202

    thread = threading.Thread(
        target=run_data_refresh,
        daemon=True,
    )

    thread.start()

    return jsonify({
        "ok": True,
        "busy": False
    }), 202


# ---------------------------------------------------------
# Run application
# ---------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    app.run(  # pragma: no cover
        debug=True,
        port=8080,
    )