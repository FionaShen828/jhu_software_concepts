import sys
from pathlib import Path

import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


import refresh_data
import scrape


class FakeDriver:
    """Fake Selenium driver for coverage tests."""

    def __init__(self, quit_error=False):
        self.quit_called = False
        self.quit_error = quit_error

    def quit(self):
        self.quit_called = True

        if self.quit_error:
            raise RuntimeError("quit failed")


@pytest.mark.integration
def test_scrape_restarts_driver_after_25_pages(monkeypatch):
    """The scraper should restart Chrome after 25 pages."""

    first_driver = FakeDriver()
    second_driver = FakeDriver()

    drivers = [
        first_driver,
        second_driver,
    ]

    monkeypatch.setattr(
        scrape,
        "load_checkpoint",
        lambda: (
            [],
            "https://example.com/page1",
            1,
        ),
    )

    def fake_create_driver():
        if drivers:
            return drivers.pop(0)

        return FakeDriver()

    monkeypatch.setattr(
        scrape,
        "create_driver",
        fake_create_driver,
    )

    monkeypatch.setattr(
        scrape,
        "get_rendered_page",
        lambda driver, url: "<html></html>",
    )

    monkeypatch.setattr(
        scrape,
        "parse_page",
        lambda html: "fake-soup",
    )

    monkeypatch.setattr(
        scrape,
        "extract_rows",
        lambda soup: [],
    )

    monkeypatch.setattr(
        scrape,
        "group_applicant_rows",
        lambda rows: [],
    )

    page_counter = {"page": 1}

    def fake_next_page(soup):
        page_counter["page"] += 1

        if page_counter["page"] <= 26:
            return (
                "https://example.com/page"
                f"{page_counter['page']}"
            )

        return None

    monkeypatch.setattr(
        scrape,
        "get_next_page_url",
        fake_next_page,
    )

    monkeypatch.setattr(
        scrape,
        "save_checkpoint",
        lambda *args: None,
    )

    monkeypatch.setattr(
        scrape.time,
        "sleep",
        lambda seconds: None,
    )

    result = scrape.scrape_data(
        target_count=1,
    )

    assert result == []
    assert first_driver.quit_called is True


@pytest.mark.integration
def test_scrape_restart_handles_quit_error(monkeypatch):
    """A quit error during the 25-page restart should be ignored."""

    first_driver = FakeDriver(
        quit_error=True,
    )
    second_driver = FakeDriver()

    drivers = [
        first_driver,
        second_driver,
    ]

    monkeypatch.setattr(
        scrape,
        "load_checkpoint",
        lambda: (
            [],
            "https://example.com/page1",
            1,
        ),
    )

    def fake_create_driver():
        if drivers:
            return drivers.pop(0)

        return FakeDriver()

    monkeypatch.setattr(
        scrape,
        "create_driver",
        fake_create_driver,
    )

    monkeypatch.setattr(
        scrape,
        "get_rendered_page",
        lambda driver, url: "<html></html>",
    )

    monkeypatch.setattr(
        scrape,
        "parse_page",
        lambda html: "fake-soup",
    )

    monkeypatch.setattr(
        scrape,
        "extract_rows",
        lambda soup: [],
    )

    monkeypatch.setattr(
        scrape,
        "group_applicant_rows",
        lambda rows: [],
    )

    page_counter = {"page": 1}

    def fake_next_page(soup):
        page_counter["page"] += 1

        if page_counter["page"] <= 26:
            return (
                "https://example.com/page"
                f"{page_counter['page']}"
            )

        return None

    monkeypatch.setattr(
        scrape,
        "get_next_page_url",
        fake_next_page,
    )

    monkeypatch.setattr(
        scrape,
        "save_checkpoint",
        lambda *args: None,
    )

    monkeypatch.setattr(
        scrape.time,
        "sleep",
        lambda seconds: None,
    )

    result = scrape.scrape_data(
        target_count=1,
    )

    assert result == []
    assert first_driver.quit_called is True


@pytest.mark.integration
def test_scrape_final_quit_error_is_ignored(monkeypatch):
    """A quit error in the final cleanup should not crash."""

    driver = FakeDriver(
        quit_error=True,
    )

    monkeypatch.setattr(
        scrape,
        "load_checkpoint",
        lambda: (
            [],
            "https://example.com/page1",
            1,
        ),
    )

    monkeypatch.setattr(
        scrape,
        "create_driver",
        lambda: driver,
    )

    monkeypatch.setattr(
        scrape,
        "get_rendered_page",
        lambda driver, url: "<html></html>",
    )

    monkeypatch.setattr(
        scrape,
        "parse_page",
        lambda html: "fake-soup",
    )

    monkeypatch.setattr(
        scrape,
        "extract_rows",
        lambda soup: [],
    )

    monkeypatch.setattr(
        scrape,
        "group_applicant_rows",
        lambda rows: [],
    )

    monkeypatch.setattr(
        scrape,
        "get_next_page_url",
        lambda soup: None,
    )

    monkeypatch.setattr(
        scrape,
        "save_checkpoint",
        lambda *args: None,
    )

    monkeypatch.setattr(
        scrape.time,
        "sleep",
        lambda seconds: None,
    )

    result = scrape.scrape_data(
        target_count=1,
    )

    assert result == []
    assert driver.quit_called is True

@pytest.mark.web
def test_create_app_with_test_config():
    """create_app should apply a provided test configuration."""

    from app import create_app

    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
        }
    )

    assert test_app.config["TESTING"] is True
    assert test_app.config["SECRET_KEY"] == "test-secret"

@pytest.mark.integration
def test_refresh_continues_to_next_page(monkeypatch):
    """Refresh should move to the next page after finding a new record."""

    driver = FakeDriver()
    page_count = {"value": 0}

    monkeypatch.setattr(
        refresh_data,
        "create_driver",
        lambda: driver,
    )

    monkeypatch.setattr(
        refresh_data,
        "load_raw_data",
        lambda: [],
    )

    monkeypatch.setattr(
        refresh_data,
        "load_existing_urls",
        lambda: set(),
    )

    def fake_render(driver, url):
        page_count["value"] += 1
        return "<html></html>"

    monkeypatch.setattr(
        refresh_data,
        "get_rendered_page",
        fake_render,
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

    def fake_group(rows):
        if page_count["value"] == 1:
            return [
                (
                    "main-row",
                    "detail-row",
                    "comment-row",
                )
            ]

        return []

    monkeypatch.setattr(
        refresh_data,
        "group_applicant_rows",
        fake_group,
    )

    monkeypatch.setattr(
        refresh_data,
        "parse_applicant",
        lambda main, detail, comment: {
            "url": "https://example.com/new-applicant"
        },
    )

    monkeypatch.setattr(
        refresh_data,
        "get_next_page_url",
        lambda soup: "https://example.com/page2",
    )

    monkeypatch.setattr(
        refresh_data,
        "save_raw_data",
        lambda data: None,
    )

    result = refresh_data.refresh_data()

    assert result == 1
    assert page_count["value"] == 2
    assert driver.quit_called is True