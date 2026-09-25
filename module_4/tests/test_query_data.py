import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import query_data


@pytest.mark.db
def test_get_connection(monkeypatch):
    captured = {}

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return "fake-connection"

    monkeypatch.setattr(
        query_data.psycopg,
        "connect",
        fake_connect,
    )

    monkeypatch.setenv(
        "DB_PASSWORD",
        "test-password",
    )

    connection = query_data.get_connection()

    assert connection == "fake-connection"
    assert captured["dbname"] == "gradcafe"
    assert captured["user"] == "postgres"
    assert captured["password"] == "test-password"
    assert captured["host"] == "localhost"
    assert captured["port"] == "5432"


class FetchCursor:
    def __init__(self, row):
        self.row = row
        self.commands = []

    def execute(self, query, params=None):
        self.commands.append((query, params))

    def fetchone(self):
        return self.row


@pytest.mark.db
def test_fetch_one_without_params():
    cursor = FetchCursor((25,))

    result = query_data.fetch_one(
        cursor,
        "SELECT COUNT(*) FROM applicants",
    )

    assert result == 25
    assert cursor.commands[0][1] is None


@pytest.mark.db
def test_fetch_one_with_params():
    cursor = FetchCursor((10,))

    result = query_data.fetch_one(
        cursor,
        "SELECT COUNT(*) FROM applicants WHERE term = %s",
        ("Fall 2026",),
    )

    assert result == 10
    assert cursor.commands[0][1] == ("Fall 2026",)


@pytest.mark.db
def test_fetch_one_empty_result():
    cursor = FetchCursor(None)

    result = query_data.fetch_one(
        cursor,
        "SELECT COUNT(*) FROM applicants",
    )

    assert result is None


@pytest.mark.analysis
def test_format_number():
    assert query_data.format_number(3.756) == "3.76"
    assert query_data.format_number(4) == "4.00"
    assert query_data.format_number(None) == "N/A"


@pytest.mark.analysis
def test_format_percent():
    assert query_data.format_percent(49.014) == "49.01%"
    assert query_data.format_percent(50) == "50.00%"
    assert query_data.format_percent(None) == "N/A"


class FakeMainCursor:
    def __init__(self, values, q3_values):
        self.values = iter(values)
        self.q3_values = q3_values
        self.last_query = ""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.last_query = query

    def fetchone(self):
        if "AVG(gpa)," in self.last_query:
            return self.q3_values

        return (next(self.values),)


class FakeConnection:
    def __init__(self, values, q3_values):
        self.cursor_object = FakeMainCursor(
            values,
            q3_values,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.cursor_object


@pytest.mark.db
@pytest.mark.analysis
def test_main_with_data(monkeypatch, capsys):
    values = [
        100,    # q1
        49.01,  # q2
        3.756,  # q4
        54.43,  # q5
        3.75,   # q6
        6,      # q7
        6,      # q8
        8,      # q9
        40.40,  # original q1
        3.81,   # original q2
    ]

    q3_values = (
        3.75,
        165.57,
        159.94,
        4.52,
    )

    monkeypatch.setattr(
        query_data,
        "get_connection",
        lambda: FakeConnection(
            values,
            q3_values,
        ),
    )

    query_data.main()

    output = capsys.readouterr().out

    assert "Fall 2026 applicant count: 100" in output
    assert "Percent international: 49.01%" in output

    assert "Average GPA: 3.75" in output
    assert "Average GRE Quantitative: 165.57" in output
    assert "Average GRE Verbal: 159.94" in output
    assert "Average GRE Analytical Writing: 4.52" in output

    assert (
        "Average GPA of American Fall 2026 applicants: 3.76"
        in output
    )

    assert (
        "Fall 2025 acceptance percentage: 54.43%"
        in output
    )

    assert (
        "Average GPA of accepted Fall 2026 applicants: 3.75"
        in output
    )

    assert (
        "JHU Computer Science master's applicant count: 6"
        in output
    )

    assert "Original-field count: 6" in output
    assert "LLM-field count: 8" in output
    assert "Difference: +2" in output

    assert (
        "Fall 2026 acceptance percentage: 40.40%"
        in output
    )

    assert (
        "Average GPA of international applicants: 3.81"
        in output
    )


@pytest.mark.db
@pytest.mark.analysis
def test_main_with_missing_values(monkeypatch, capsys):
    values = [
        0,     # q1
        None,  # q2
        None,  # q4
        None,  # q5
        None,  # q6
        0,     # q7
        0,     # q8
        0,     # q9
        None,  # original q1
        None,  # original q2
    ]

    q3_values = (
        None,
        None,
        None,
        None,
    )

    monkeypatch.setattr(
        query_data,
        "get_connection",
        lambda: FakeConnection(
            values,
            q3_values,
        ),
    )

    query_data.main()

    output = capsys.readouterr().out

    assert "Fall 2026 applicant count: 0" in output
    assert "Percent international: N/A" in output

    assert "Average GPA: N/A" in output
    assert "Average GRE Quantitative: N/A" in output
    assert "Average GRE Verbal: N/A" in output
    assert "Average GRE Analytical Writing: N/A" in output

    assert (
        "Average GPA of American Fall 2026 applicants: N/A"
        in output
    )

    assert (
        "Fall 2025 acceptance percentage: N/A"
        in output
    )

    assert (
        "Average GPA of accepted Fall 2026 applicants: N/A"
        in output
    )

    assert (
        "JHU Computer Science master's applicant count: 0"
        in output
    )

    assert "Original-field count: 0" in output
    assert "LLM-field count: 0" in output
    assert "Difference: +0" in output

    assert (
        "Fall 2026 acceptance percentage: N/A"
        in output
    )

    assert (
        "Average GPA of international applicants: N/A"
        in output
    )