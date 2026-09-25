import sys
from pathlib import Path

import pytest


# Allow tests to import files from module_4/src
SRC_DIR = Path(__file__).resolve().parents[1] / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import app as flask_app


@pytest.fixture
def client(monkeypatch):
    """Create a Flask test client without using the real database."""

    fake_results = {
        "q1": 100,
        "q2": "49.01%",
        "q3_gpa": "3.75",
        "q3_gre": "253.57",
        "q3_gre_v": "159.94",
        "q3_gre_aw": "7.52",
        "q4": "3.76",
        "q5": "54.43%",
        "q6": "3.75",
        "q7": 6,
        "q8": 1,
        "q9": 1,
        "q9_difference": "+0",
        "original_1": "40.40%",
        "original_2": "3.76",
    }

    monkeypatch.setattr(
        flask_app,
        "get_analysis",
        lambda: fake_results,
    )

    flask_app.app.config.update(
        TESTING=True
    )

    return flask_app.app.test_client()


@pytest.mark.web
def test_app_config_and_routes():
    """Test that the Flask app is testable and required routes exist."""

    assert flask_app.app.config is not None

    routes = {
        rule.rule
        for rule in flask_app.app.url_map.iter_rules()
    }

    assert "/analysis" in routes
    assert "/pull-data" in routes
    assert "/update-analysis" in routes


@pytest.mark.web
def test_analysis_page_loads(client):
    """Test the Analysis page and its required content."""

    response = client.get("/analysis")

    assert response.status_code == 200

    page = response.get_data(as_text=True)

    assert "Analysis" in page
    assert "Pull Data" in page
    assert "Update Analysis" in page
    assert "Answer:" in page