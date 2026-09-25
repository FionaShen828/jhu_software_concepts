import sys
import json
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import refresh_data


class FakeScalarResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def scalars(self, query):
        return FakeScalarResult(
            [
                "https://example.com/old-1",
                "https://example.com/old-2",
            ]
        )


@pytest.mark.db
def test_load_existing_urls(monkeypatch):
    monkeypatch.setattr(
        refresh_data,
        "SessionLocal",
        lambda: FakeSession(),
    )

    result = refresh_data.load_existing_urls()

    assert result == {
        "https://example.com/old-1",
        "https://example.com/old-2",
    }


@pytest.mark.integration
def test_load_raw_data_missing_file(monkeypatch, tmp_path):
    fake_file = tmp_path / "missing.json"

    monkeypatch.setattr(
        refresh_data,
        "RAW_DATA_FILE",
        fake_file,
    )

    assert refresh_data.load_raw_data() == []


@pytest.mark.integration
def test_save_and_load_raw_data(monkeypatch, tmp_path):
    fake_file = tmp_path / "applicant_data.json"

    monkeypatch.setattr(
        refresh_data,
        "RAW_DATA_FILE",
        fake_file,
    )

    data = [
        {
            "url": "https://example.com/1",
            "program": "Computer Science",
        },
        {
            "url": "https://example.com/2",
            "program": "Data Science",
        },
    ]

    refresh_data.save_raw_data(data)

    assert fake_file.exists()

    loaded = refresh_data.load_raw_data()

    assert loaded == data


class FakeDriver:
    def __init__(self, raise_on_quit=False):
        self.quit_called = False
        self.raise_on_quit = raise_on_quit

    def quit(self):
        self.quit_called = True

        if self.raise_on_quit:
            raise RuntimeError("Fake quit error")


def configure_scraper(
    monkeypatch,
    applicants,
    existing_urls=None,
    raw_data=None,
    next_url=None,
    raise_on_quit=False,
):
    if existing_urls is None:
        existing_urls = set()

    if raw_data is None:
        raw_data = []

    driver = FakeDriver(
        raise_on_quit=raise_on_quit
    )

    monkeypatch.setattr(
        refresh_data,
        "load_existing_urls",
        lambda: existing_urls,
    )

    monkeypatch.setattr(
        refresh_data,
        "load_raw_data",
        lambda: list(raw_data),
    )

    monkeypatch.setattr(
        refresh_data,
        "create_driver",
        lambda: driver,
    )

    monkeypatch.setattr(
        refresh_data,
        "get_rendered_page",
        lambda driver, url: "<html></html>",
    )

    monkeypatch.setattr(
        refresh_data,
        "parse_page",
        lambda html: "fake-soup",
    )

    monkeypatch.setattr(
        refresh_data,
        "extract_rows",
        lambda soup: ["fake-row"],
    )

    fake_groups = [
        (
            f"main-{index}",
            f"detail-{index}",
            f"comment-{index}",
        )
        for index in range(len(applicants))
    ]

    monkeypatch.setattr(
        refresh_data,
        "group_applicant_rows",
        lambda rows: fake_groups,
    )

    applicant_iterator = iter(applicants)

    monkeypatch.setattr(
        refresh_data,
        "parse_applicant",
        lambda main, detail, comment: next(
            applicant_iterator
        ),
    )

    monkeypatch.setattr(
        refresh_data,
        "get_next_page_url",
        lambda soup: next_url,
    )

    return driver


@pytest.mark.integration
def test_refresh_data_adds_new_records(
    monkeypatch,
    capsys,
):
    applicants = [
        {
            "url": "https://example.com/new-1",
            "program": "Computer Science",
        },
        {
            "url": "https://example.com/new-2",
            "program": "Data Science",
        },
    ]

    driver = configure_scraper(
        monkeypatch,
        applicants,
        existing_urls={
            "https://example.com/old-1"
        },
        raw_data=[
            {
                "url": "https://example.com/old-2"
            }
        ],
        next_url=None,
    )

    saved = {}

    def fake_save(data):
        saved["data"] = data

    monkeypatch.setattr(
        refresh_data,
        "save_raw_data",
        fake_save,
    )

    result = refresh_data.refresh_data()

    output = capsys.readouterr().out

    assert result == 2
    assert len(saved["data"]) == 3
    assert saved["data"][1]["url"] == (
        "https://example.com/new-1"
    )
    assert saved["data"][2]["url"] == (
        "https://example.com/new-2"
    )

    assert "New records found: 2" in output
    assert "Updated raw record total: 3" in output
    assert "Updated applicant_data.json" in output
    assert driver.quit_called is True


@pytest.mark.integration
def test_refresh_data_skips_known_and_missing_urls(
    monkeypatch,
    capsys,
):
    applicants = [
        {
            "url": None,
            "program": "Unknown",
        },
        {
            "url": "https://example.com/old-1",
            "program": "Computer Science",
        },
    ]

    driver = configure_scraper(
        monkeypatch,
        applicants,
        existing_urls={
            "https://example.com/old-1"
        },
        raw_data=[],
        next_url=None,
    )

    saved = {"called": False}

    def fake_save(data):
        saved["called"] = True

    monkeypatch.setattr(
        refresh_data,
        "save_raw_data",
        fake_save,
    )

    result = refresh_data.refresh_data()

    output = capsys.readouterr().out

    assert result == 0
    assert saved["called"] is False
    assert "New records on this page: 0" in output
    assert (
        "Reached records already stored in the database."
        in output
    )
    assert "No new GradCafe records found." in output
    assert driver.quit_called is True


@pytest.mark.integration
def test_refresh_data_stops_when_no_next_page(
    monkeypatch,
    capsys,
):
    applicants = [
        {
            "url": "https://example.com/new-3",
            "program": "Computer Science",
        }
    ]

    configure_scraper(
        monkeypatch,
        applicants,
        existing_urls=set(),
        raw_data=[],
        next_url=None,
    )

    monkeypatch.setattr(
        refresh_data,
        "save_raw_data",
        lambda data: None,
    )

    result = refresh_data.refresh_data()

    output = capsys.readouterr().out

    assert result == 1
    assert "No next page found." in output


@pytest.mark.integration
def test_driver_quit_error_is_handled(
    monkeypatch,
):
    applicants = [
        {
            "url": "https://example.com/new-4",
            "program": "Computer Science",
        }
    ]

    driver = configure_scraper(
        monkeypatch,
        applicants,
        existing_urls=set(),
        raw_data=[],
        next_url=None,
        raise_on_quit=True,
    )

    monkeypatch.setattr(
        refresh_data,
        "save_raw_data",
        lambda data: None,
    )

    result = refresh_data.refresh_data()

    assert result == 1
    assert driver.quit_called is True