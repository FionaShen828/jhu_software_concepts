import sys
import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models import Base, Applicant
import load_data


# ---------------------------------------------------------
# Basic database tests using an isolated SQLite database
# ---------------------------------------------------------

@pytest.fixture
def test_session():
    """Create an isolated in-memory database for testing."""

    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    TestSession = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with TestSession() as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.mark.db
def test_table_starts_empty(test_session):
    """The test applicants table should start empty."""

    applicants = test_session.scalars(
        select(Applicant)
    ).all()

    assert applicants == []


@pytest.mark.db
def test_insert_applicant(test_session):
    """A new applicant should be inserted successfully."""

    applicant = Applicant(
        university="Johns Hopkins University",
        program="Computer Science",
        url="https://example.com/test-1",
        status="Accepted",
        term="Fall 2026",
        degree="Masters",
    )

    test_session.add(applicant)
    test_session.commit()

    saved = test_session.scalar(
        select(Applicant).where(
            Applicant.url == "https://example.com/test-1"
        )
    )

    assert saved is not None
    assert saved.university == "Johns Hopkins University"
    assert saved.program == "Computer Science"
    assert saved.status == "Accepted"
    assert saved.term == "Fall 2026"


@pytest.mark.db
def test_required_fields_not_null_after_insert(test_session):
    """Inserted test data should contain the required fields."""

    applicant = Applicant(
        university="Stanford University",
        program="Computer Science",
        url="https://example.com/test-2",
        status="Accepted",
        term="Fall 2026",
        degree="PhD",
    )

    test_session.add(applicant)
    test_session.commit()

    saved = test_session.scalar(
        select(Applicant).where(
            Applicant.url == "https://example.com/test-2"
        )
    )

    assert saved.university is not None
    assert saved.program is not None
    assert saved.url is not None
    assert saved.status is not None
    assert saved.term is not None
    assert saved.degree is not None


@pytest.mark.db
def test_duplicate_url_does_not_create_duplicate(test_session):
    """The same applicant URL should not produce duplicate rows."""

    url = "https://example.com/duplicate"

    applicant = Applicant(
        university="MIT",
        program="Computer Science",
        url=url,
        status="Accepted",
        term="Fall 2026",
        degree="PhD",
    )

    test_session.add(applicant)
    test_session.commit()

    existing = test_session.scalar(
        select(Applicant).where(Applicant.url == url)
    )

    if existing is None:
        test_session.add(applicant)

    test_session.commit()

    matches = test_session.scalars(
        select(Applicant).where(Applicant.url == url)
    ).all()

    assert len(matches) == 1


@pytest.mark.db
def test_simple_query_returns_expected_keys(test_session):
    """A simple database query should return Module 3 style keys."""

    applicant = Applicant(
        university="Carnegie Mellon University",
        program="Computer Science",
        url="https://example.com/test-3",
        status="Accepted",
        term="Fall 2026",
        degree="PhD",
    )

    test_session.add(applicant)
    test_session.commit()

    saved = test_session.scalar(
        select(Applicant).where(
            Applicant.url == "https://example.com/test-3"
        )
    )

    result = {
        "university": saved.university,
        "program": saved.program,
        "status": saved.status,
        "term": saved.term,
        "degree": saved.degree,
    }

    expected_keys = {
        "university",
        "program",
        "status",
        "term",
        "degree",
    }

    assert expected_keys.issubset(result.keys())


# ---------------------------------------------------------
# Tests for load_data.py
# ---------------------------------------------------------

@pytest.mark.db
def test_parse_date():
    """Valid dates should be parsed and invalid dates should return None."""

    assert str(load_data.parse_date("Sep 24, 2026")) == "2026-09-24"
    assert str(load_data.parse_date("  Sep 24, 2026  ")) == "2026-09-24"

    assert load_data.parse_date(None) is None
    assert load_data.parse_date("") is None
    assert load_data.parse_date("not a date") is None
    assert load_data.parse_date(123) is None


@pytest.mark.db
def test_safe_float():
    """Numeric values should become floats and invalid values should be None."""

    assert load_data.safe_float("3.75") == 3.75
    assert load_data.safe_float(165) == 165.0

    assert load_data.safe_float(None) is None
    assert load_data.safe_float("") is None
    assert load_data.safe_float("unknown") is None
    assert load_data.safe_float([]) is None


@pytest.mark.db
def test_get_connection(monkeypatch):
    """get_connection should use the configured PostgreSQL settings."""

    monkeypatch.delenv("DATABASE_URL", raising=False)

    captured = {}

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return "fake-connection"

    monkeypatch.setattr(
        load_data.psycopg,
        "connect",
        fake_connect,
    )

    monkeypatch.setenv(
        "DB_PASSWORD",
        "test-password",
    )

    connection = load_data.get_connection()

    assert connection == "fake-connection"
    assert captured["dbname"] == "gradcafe"
    assert captured["user"] == "postgres"
    assert captured["password"] == "test-password"
    assert captured["host"] == "localhost"
    assert captured["port"] == "5432"


class FakeCursor:
    """Fake PostgreSQL cursor for load_data tests."""

    def __init__(self):
        self.commands = []
        self.rowcount = 0
        self.insert_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.commands.append((query, params))

        if "INSERT INTO applicants" in query:
            self.insert_count += 1

            # First row is inserted.
            # Second row represents a duplicate URL.
            if self.insert_count == 1:
                self.rowcount = 1
            else:
                self.rowcount = 0


class FakeConnection:
    """Fake PostgreSQL connection for load_data tests."""

    def __init__(self):
        self.cursor_object = FakeCursor()
        self.commit_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.cursor_object

    def commit(self):
        self.commit_count += 1


@pytest.mark.db
def test_create_table():
    """create_table should create and update the applicants table."""

    connection = FakeConnection()

    load_data.create_table(connection)

    assert len(connection.cursor_object.commands) == 2

    first_query = connection.cursor_object.commands[0][0]
    second_query = connection.cursor_object.commands[1][0]

    assert "CREATE TABLE IF NOT EXISTS applicants" in first_query
    assert "url TEXT UNIQUE" in first_query
    assert "ADD COLUMN IF NOT EXISTS university" in second_query

    assert connection.commit_count == 1


@pytest.mark.db
def test_load_data(monkeypatch, tmp_path, capsys):
    """load_data should read applicants and insert only new URLs."""

    fake_applicants = [
        {
            "university": "Johns Hopkins University",
            "program": "Computer Science",
            "comments": "Test applicant",
            "date_added": "Sep 24, 2026",
            "url": "https://example.com/applicant-1",
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
            "university": "Johns Hopkins University",
            "program": "Computer Science",
            "comments": "Duplicate applicant",
            "date_added": "Sep 24, 2026",
            "url": "https://example.com/applicant-1",
            "status": "Accepted",
            "term": "Fall 2026",
            "applicant_type": "International",
            "gpa": "",
            "gre": None,
            "gre_v": None,
            "gre_aw": None,
            "degree": "Masters",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "Johns Hopkins University",
        },
    ]

    fake_file = tmp_path / "applicants.json"

    with open(fake_file, "w", encoding="utf-8") as file:
        json.dump(fake_applicants, file)

    connection = FakeConnection()

    monkeypatch.setattr(
        load_data,
        "DATA_FILE",
        fake_file,
    )

    monkeypatch.setattr(
        load_data,
        "get_connection",
        lambda: connection,
    )

    load_data.load_data()

    output = capsys.readouterr().out

    assert "Applicants found: 2" in output
    assert "New applicants inserted: 1" in output
    assert "Database load complete." in output

    insert_commands = [
        command
        for command in connection.cursor_object.commands
        if "INSERT INTO applicants" in command[0]
    ]

    assert len(insert_commands) == 2

    first_params = insert_commands[0][1]

    assert first_params[0] == "Johns Hopkins University"
    assert first_params[1] == "Computer Science"
    assert first_params[4] == "https://example.com/applicant-1"
    assert first_params[8] == 3.80
    assert first_params[9] == 165.0
    assert first_params[10] == 160.0
    assert first_params[11] == 4.5

    assert connection.commit_count >= 2