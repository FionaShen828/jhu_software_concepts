import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import orm_queries


@pytest.mark.analysis
def test_format_number():
    assert orm_queries.format_number(3.756) == "3.76"
    assert orm_queries.format_number(4) == "4.00"
    assert orm_queries.format_number(None) == "N/A"


@pytest.mark.analysis
def test_format_percent():
    assert orm_queries.format_percent(49.014) == "49.01%"
    assert orm_queries.format_percent(50) == "50.00%"
    assert orm_queries.format_percent(None) == "N/A"


class FakeSession:
    def __init__(self, values):
        self.values = iter(values)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def scalar(self, query):
        return next(self.values)


@pytest.mark.analysis
def test_main_with_data(monkeypatch, capsys):
    values = [
        100,    # q1
        3.756,  # q4
        200,    # q5 total
        100,    # q5 accepted
        6,      # q8
        8,      # q9
        100,    # original total
        40,     # original accepted
    ]

    monkeypatch.setattr(
        orm_queries,
        "SessionLocal",
        lambda: FakeSession(values),
    )

    orm_queries.main()

    output = capsys.readouterr().out

    assert "Fall 2026 applicant count: 100" in output
    assert "Average GPA of American Fall 2026 applicants: 3.76" in output
    assert "Fall 2025 acceptance percentage: 50.00%" in output
    assert "Original-field count: 6" in output
    assert "LLM-field count: 8" in output
    assert "Difference: +2" in output
    assert "Fall 2026 acceptance percentage: 40.00%" in output


@pytest.mark.analysis
def test_main_with_empty_data(monkeypatch, capsys):
    values = [
        0,     # q1
        None,  # q4
        0,     # q5 total
        0,     # q5 accepted
        0,     # q8
        0,     # q9
        0,     # original total
        0,     # original accepted
    ]

    monkeypatch.setattr(
        orm_queries,
        "SessionLocal",
        lambda: FakeSession(values),
    )

    orm_queries.main()

    output = capsys.readouterr().out

    assert "Fall 2026 applicant count: 0" in output
    assert "Average GPA of American Fall 2026 applicants: N/A" in output
    assert "Fall 2025 acceptance percentage: N/A" in output
    assert "Original-field count: 0" in output
    assert "LLM-field count: 0" in output
    assert "Difference: +0" in output
    assert "Fall 2026 acceptance percentage: N/A" in output