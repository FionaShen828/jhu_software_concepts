import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import app as flask_app


@pytest.mark.analysis
def test_format_number_two_decimals():
    """Numbers should be displayed with two decimal places."""

    assert flask_app.format_number(3.756) == "3.76"
    assert flask_app.format_number(4) == "4.00"


@pytest.mark.analysis
def test_format_percent_two_decimals():
    """Percentages should be displayed with two decimal places."""

    assert flask_app.format_percent(49.014) == "49.01%"
    assert flask_app.format_percent(50) == "50.00%"


@pytest.mark.analysis
def test_format_none():
    """Missing values should be displayed as N/A."""

    assert flask_app.format_number(None) == "N/A"
    assert flask_app.format_percent(None) == "N/A"


@pytest.mark.analysis
def test_analysis_page_has_answer_label(monkeypatch):
    """The Analysis page should include the required Answer label."""

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

    flask_app.app.config.update(TESTING=True)

    with flask_app.app.test_client() as client:
        response = client.get("/analysis")

    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Answer:" in page
    assert "49.01%" in page
    assert "54.43%" in page
    assert "40.40%" in page


class FakeSession:
    """Small fake SQLAlchemy session used for analysis tests."""

    def __init__(self, values):
        self.values = iter(values)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def scalar(self, query):
        return next(self.values)


@pytest.mark.analysis
def test_get_analysis_with_data(monkeypatch):
    """get_analysis should return all expected analysis values."""

    # Values are returned in the same order that get_analysis()
    # calls session.scalar().
    values = [
        100,      # q1
        49,       # international
        100,      # usable nationality
        3.75,     # q3 GPA
        253.57,   # q3 GRE Quant
        159.94,   # q3 GRE Verbal
        7.52,     # q3 GRE AW
        3.76,     # q4
        200,      # Fall 2025 total
        100,      # Fall 2025 accepted
        3.75,     # q6
        6,        # q7
        1,        # q8
        1,        # q9
        100,      # Fall 2026 total
        40,       # Fall 2026 accepted
        3.76,     # original q2
    ]

    monkeypatch.setattr(
        flask_app,
        "SessionLocal",
        lambda: FakeSession(values),
    )

    results = flask_app.get_analysis()

    assert results["q1"] == 100
    assert results["q2"] == "49.00%"
    assert results["q3_gpa"] == "3.75"
    assert results["q3_gre"] == "253.57"
    assert results["q3_gre_v"] == "159.94"
    assert results["q3_gre_aw"] == "7.52"
    assert results["q4"] == "3.76"
    assert results["q5"] == "50.00%"
    assert results["q6"] == "3.75"
    assert results["q7"] == 6
    assert results["q8"] == 1
    assert results["q9"] == 1
    assert results["q9_difference"] == "+0"
    assert results["original_1"] == "40.00%"
    assert results["original_2"] == "3.76"


@pytest.mark.analysis
def test_get_analysis_with_empty_data(monkeypatch):
    """get_analysis should handle empty denominator values."""

    values = [
        0,       # q1
        0,       # international
        0,       # usable nationality
        None,    # q3 GPA
        None,    # q3 GRE Quant
        None,    # q3 GRE Verbal
        None,    # q3 GRE AW
        None,    # q4
        0,       # Fall 2025 total
        0,       # Fall 2025 accepted
        None,    # q6
        0,       # q7
        0,       # q8
        0,       # q9
        0,       # Fall 2026 total
        0,       # Fall 2026 accepted
        None,    # original q2
    ]

    monkeypatch.setattr(
        flask_app,
        "SessionLocal",
        lambda: FakeSession(values),
    )

    results = flask_app.get_analysis()

    assert results["q2"] == "N/A"
    assert results["q3_gpa"] == "N/A"
    assert results["q3_gre"] == "N/A"
    assert results["q3_gre_v"] == "N/A"
    assert results["q3_gre_aw"] == "N/A"
    assert results["q4"] == "N/A"
    assert results["q5"] == "N/A"
    assert results["q6"] == "N/A"
    assert results["q8"] == 0
    assert results["q9"] == 0
    assert results["q9_difference"] == "+0"
    assert results["original_1"] == "N/A"
    assert results["original_2"] == "N/A"