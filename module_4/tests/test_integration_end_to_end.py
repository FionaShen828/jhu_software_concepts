import os
import sys
from pathlib import Path

import psycopg
import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------
# Test database configuration
# ---------------------------------------------------------

TEST_DATABASE_URL = (
    "postgresql://postgres:"
    f"{os.environ.get('DB_PASSWORD')}"
    "@localhost:5432/gradcafe_test"
)

# Set this before importing the application modules.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


import app as flask_app
import load_data


# ---------------------------------------------------------
# Fake scraper data
# ---------------------------------------------------------

FAKE_ROWS = [
    {
        "university": "Johns Hopkins University",
        "program": "Computer Science",
        "comments": "Integration test applicant.",
        "date_added": "Sep 24, 2026",
        "url": "https://example.com/integration-1",
        "status": "Accepted",
        "term": "Fall 2026",
        "applicant_type": "International",
        "gpa": "3.80",
        "gre": "165",
        "gre_v": "160",
        "gre_aw": "4.5",
        "degree": "Masters",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "Johns Hopkins University",
    },
    {
        "university": "Stanford University",
        "program": "Computer Science",
        "comments": "Second integration test applicant.",
        "date_added": "Sep 24, 2026",
        "url": "https://example.com/integration-2",
        "status": "Accepted",
        "term": "Fall 2026",
        "applicant_type": "American",
        "gpa": "3.90",
        "gre": "168",
        "gre_v": "162",
        "gre_aw": "5.0",
        "degree": "PhD",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "Stanford University",
    },
]


# ---------------------------------------------------------
# Fixtures
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_test_database():
    """
    Keep the PostgreSQL integration database isolated.

    This only clears gradcafe_test. It does not touch the
    normal gradcafe database.
    """

    with psycopg.connect(TEST_DATABASE_URL) as conn:
        load_data.create_table(conn)

        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE TABLE applicants RESTART IDENTITY;"
            )

        conn.commit()

    yield

    with psycopg.connect(TEST_DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE TABLE applicants RESTART IDENTITY;"
            )

        conn.commit()


@pytest.fixture
def client():
    """Create a Flask test client."""

    flask_app.app.config.update(
        TESTING=True,
        TEST_REFRESH_FUNCTION=None,
    )

    flask_app.scrape_running = False

    if flask_app.scrape_lock.locked():
        flask_app.scrape_lock.release()

    with flask_app.app.test_client() as test_client:
        yield test_client

    flask_app.app.config["TEST_REFRESH_FUNCTION"] = None
    flask_app.scrape_running = False

    if flask_app.scrape_lock.locked():
        flask_app.scrape_lock.release()


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def fake_refresh():
    """
    Replace the live scraper/cleaner during integration tests.

    The fake scraper rows are passed through the real
    PostgreSQL loader.
    """

    load_data.load_data(FAKE_ROWS)


def database_rows():
    """Return the applicant rows currently in PostgreSQL."""

    with psycopg.connect(TEST_DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    university,
                    program,
                    url,
                    status,
                    term,
                    degree
                FROM applicants
                ORDER BY url;
                """
            )

            return cur.fetchall()


# ---------------------------------------------------------
# End-to-end tests
# ---------------------------------------------------------

@pytest.mark.integration
def test_pull_data_loads_fake_rows_into_postgresql(client):
    """
    POST /pull-data should trigger the fake scraper data
    and load those rows through the real PostgreSQL loader.
    """

    flask_app.app.config["TEST_REFRESH_FUNCTION"] = fake_refresh

    assert database_rows() == []

    response = client.post("/pull-data")

    assert response.status_code == 202
    assert response.get_json()["ok"] is True

    rows = database_rows()

    assert len(rows) == 2

    assert rows[0][0] == "Johns Hopkins University"
    assert rows[0][1] == "Computer Science"
    assert rows[0][2] == "https://example.com/integration-1"

    assert rows[1][0] == "Stanford University"
    assert rows[1][2] == "https://example.com/integration-2"

    for row in rows:
        assert row[0] is not None
        assert row[1] is not None
        assert row[2] is not None
        assert row[3] is not None
        assert row[4] is not None
        assert row[5] is not None


@pytest.mark.integration
def test_pull_update_analysis_and_page(client):
    """
    Test the complete Module 4 flow:

    fake scraper -> POST pull -> PostgreSQL ->
    update analysis -> GET analysis page.
    """

    flask_app.app.config["TEST_REFRESH_FUNCTION"] = fake_refresh

    pull_response = client.post("/pull-data")

    assert pull_response.status_code == 202
    assert len(database_rows()) == 2

    update_response = client.post("/update-analysis")

    assert update_response.status_code == 200
    assert update_response.get_json()["ok"] is True

    page_response = client.get("/analysis")

    assert page_response.status_code == 200

    page = page_response.get_data(as_text=True)

    assert "Analysis" in page
    assert "Answer:" in page

    # Both fake records should appear in the analysis database.
    assert len(database_rows()) == 2


@pytest.mark.integration
def test_repeated_pull_keeps_urls_unique(client):
    """Repeated pulls should not create duplicate URLs."""

    flask_app.app.config["TEST_REFRESH_FUNCTION"] = fake_refresh

    first_response = client.post("/pull-data")
    second_response = client.post("/pull-data")

    assert first_response.status_code == 202
    assert second_response.status_code == 202

    rows = database_rows()

    assert len(rows) == 2

    urls = [row[2] for row in rows]

    assert len(urls) == len(set(urls))


@pytest.mark.integration
def test_overlapping_pull_is_blocked(client):
    """A second pull should return 409 while another pull is active."""

    flask_app.scrape_lock.acquire()
    flask_app.scrape_running = True

    response = client.post("/pull-data")

    assert response.status_code == 409
    assert response.get_json()["busy"] is True