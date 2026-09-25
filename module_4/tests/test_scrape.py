import json
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import scrape


def make_soup(html):
    return BeautifulSoup(html, "html.parser")


@pytest.mark.web
def test_build_page_url():
    assert scrape.build_page_url(3) == (
        "https://www.thegradcafe.com/survey/?page=3"
    )


@pytest.mark.web
def test_get_rendered_page(monkeypatch):
    class FakeDriver:
        page_source = "<html>ready</html>"

        def __init__(self):
            self.url = None

        def get(self, url):
            self.url = url

        def execute_script(self, script):
            return "complete"

        def find_elements(self, by, value):
            return [1, 2]

    class FakeWait:
        def __init__(self, driver, timeout):
            self.driver = driver

        def until(self, condition):
            assert condition(self.driver)

    monkeypatch.setattr(
        scrape,
        "WebDriverWait",
        FakeWait,
    )

    driver = FakeDriver()

    result = scrape.get_rendered_page(
        driver,
        "https://example.com",
    )

    assert driver.url == "https://example.com"
    assert result == "<html>ready</html>"


@pytest.mark.web
def test_parse_page_and_extract_rows():
    html = """
    <table>
        <tr><td>One</td></tr>
        <tr><td>Two</td></tr>
    </table>
    """

    soup = scrape.parse_page(html)
    rows = scrape.extract_rows(soup)

    assert len(rows) == 2
    assert rows[0].get_text(strip=True) == "One"


@pytest.mark.web
def test_group_applicant_rows():
    html = """
    <table>
        <tr>
            <td>University</td>
            <td>Total comments</td>
        </tr>
        <tr class="tw-border-none">
            <td>Fall 2026</td>
        </tr>
        <tr class="tw-border-none">
            <td>Great program</td>
        </tr>

        <tr>
            <td>Second University</td>
        </tr>
        <tr class="tw-border-none">
            <td>Spring 2027</td>
        </tr>

        <tr>
            <td>No detail row</td>
        </tr>
        <tr>
            <td>Another normal row</td>
        </tr>
    </table>
    """

    rows = make_soup(html).find_all("tr")

    result = scrape.group_applicant_rows(rows)

    assert len(result) == 2
    assert result[0][2] is not None
    assert result[1][2] is None


@pytest.mark.analysis
def test_extract_university():
    row = make_soup(
        "<tr><td>Johns Hopkins University</td></tr>"
    ).tr

    assert (
        scrape.extract_university(row)
        == "Johns Hopkins University"
    )

    empty = make_soup("<tr></tr>").tr
    assert scrape.extract_university(empty) is None


@pytest.mark.analysis
def test_extract_program_and_degree():
    row = make_soup(
        """
        <tr>
            <td>University</td>
            <td>
                <span>Computer Science</span>
                <span>PhD</span>
            </td>
        </tr>
        """
    ).tr

    assert scrape.extract_program_and_degree(row) == (
        "Computer Science",
        "PhD",
    )

    one_span = make_soup(
        """
        <tr>
            <td>University</td>
            <td><span>Data Science</span></td>
        </tr>
        """
    ).tr

    assert scrape.extract_program_and_degree(
        one_span
    ) == ("Data Science", None)

    short_row = make_soup(
        "<tr><td>Only one</td></tr>"
    ).tr

    assert scrape.extract_program_and_degree(
        short_row
    ) == (None, None)


@pytest.mark.analysis
def test_extract_date_and_decision():
    row = make_soup(
        """
        <tr>
            <td>University</td>
            <td>Program</td>
            <td>Sep 20, 2026</td>
            <td>Accepted on Sep 19, 2026</td>
        </tr>
        """
    ).tr

    assert scrape.extract_date_and_decision(row) == (
        "Sep 20, 2026",
        "Accepted on Sep 19, 2026",
    )

    short_row = make_soup(
        "<tr><td>Only one</td></tr>"
    ).tr

    assert scrape.extract_date_and_decision(
        short_row
    ) == (None, None)


@pytest.mark.analysis
def test_extract_status_and_decision_date():
    assert scrape.extract_status_and_decision_date(
        None
    ) == (None, None)

    assert scrape.extract_status_and_decision_date(
        "Accepted on Sep 19, 2026"
    ) == (
        "Accepted",
        "Sep 19, 2026",
    )

    assert scrape.extract_status_and_decision_date(
        "Rejected"
    ) == (
        "Rejected",
        None,
    )


@pytest.mark.web
def test_extract_detail_url():
    row = make_soup(
        """
        <tr>
            <td>
                <a href="/result/12345">
                    Result
                </a>
            </td>
        </tr>
        """
    ).tr

    assert scrape.extract_detail_url(row) == (
        "https://www.thegradcafe.com/result/12345"
    )

    no_link = make_soup(
        "<tr><td>No link</td></tr>"
    ).tr

    assert scrape.extract_detail_url(no_link) is None


@pytest.mark.analysis
def test_extract_term():
    row = make_soup(
        """
        <tr>
            <td>
                International Fall 2026 GPA 3.8
            </td>
        </tr>
        """
    ).tr

    assert scrape.extract_term(row) == "Fall 2026"

    no_term = make_soup(
        "<tr><td>International GPA 3.8</td></tr>"
    ).tr

    assert scrape.extract_term(no_term) is None


@pytest.mark.analysis
def test_extract_semester_and_year():
    assert scrape.extract_semester_and_year(
        "Fall 2026"
    ) == (
        "Fall",
        "2026",
    )

    assert scrape.extract_semester_and_year(
        None
    ) == (None, None)

    assert scrape.extract_semester_and_year(
        "Fall"
    ) == (None, None)


@pytest.mark.analysis
def test_extract_applicant_type():
    international = make_soup(
        "<tr><td>International applicant</td></tr>"
    ).tr

    american = make_soup(
        "<tr><td>American applicant</td></tr>"
    ).tr

    unknown = make_soup(
        "<tr><td>Applicant</td></tr>"
    ).tr

    assert (
        scrape.extract_applicant_type(international)
        == "International"
    )

    assert (
        scrape.extract_applicant_type(american)
        == "American"
    )

    assert scrape.extract_applicant_type(
        unknown
    ) is None


@pytest.mark.analysis
def test_extract_scores():
    row = make_soup(
        """
        <tr>
            <td>
                GPA 3.90
                GRE 325
                GRE V 165
                GRE AW 4.5
            </td>
        </tr>
        """
    ).tr

    assert scrape.extract_scores(row) == (
        "3.90",
        "325",
        "165",
        "4.5",
    )

    empty = make_soup(
        "<tr><td>No scores</td></tr>"
    ).tr

    assert scrape.extract_scores(empty) == (
        None,
        None,
        None,
        None,
    )


@pytest.mark.integration
def test_parse_applicant():
    html = """
    <table>
        <tr id="main">
            <td>
                Johns Hopkins University
                <a href="/result/12345">
                    Result
                </a>
            </td>
            <td>
                <span>Computer Science</span>
                <span>PhD</span>
            </td>
            <td>Sep 20, 2026</td>
            <td>Accepted on Sep 19, 2026</td>
        </tr>

        <tr id="detail" class="tw-border-none">
            <td>
                International Fall 2026
                GPA 3.90 GRE 325
                GRE V 165 GRE AW 4.5
            </td>
        </tr>

        <tr id="comment" class="tw-border-none">
            <td>Great program</td>
        </tr>
    </table>
    """

    soup = make_soup(html)

    applicant = scrape.parse_applicant(
        soup.find(id="main"),
        soup.find(id="detail"),
        soup.find(id="comment"),
    )

    assert (
        applicant["university"]
        == "Johns Hopkins University Result"
    )
    assert applicant["program"] == "Computer Science"
    assert applicant["degree"] == "PhD"
    assert applicant["status"] == "Accepted"
    assert applicant["decision_date"] == "Sep 19, 2026"
    assert applicant["term"] == "Fall 2026"
    assert applicant["semester"] == "Fall"
    assert applicant["start_year"] == "2026"
    assert applicant["applicant_type"] == "International"
    assert applicant["gpa"] == "3.90"
    assert applicant["gre"] == "325"
    assert applicant["gre_v"] == "165"
    assert applicant["gre_aw"] == "4.5"
    assert applicant["comments"] == "Great program"
    assert "Great program" in applicant["raw_listing_text"]


@pytest.mark.integration
def test_parse_applicant_without_comment():
    html = """
    <table>
        <tr id="main">
            <td>MIT</td>
            <td>
                <span>Data Science</span>
            </td>
            <td>Sep 20, 2026</td>
            <td>Rejected</td>
        </tr>

        <tr id="detail">
            <td>American Spring 2027</td>
        </tr>
    </table>
    """

    soup = make_soup(html)

    applicant = scrape.parse_applicant(
        soup.find(id="main"),
        soup.find(id="detail"),
    )

    assert applicant["comments"] is None
    assert applicant["status"] == "Rejected"
    assert applicant["decision_date"] is None
    assert applicant["applicant_type"] == "American"


@pytest.mark.web
def test_get_next_page_url():
    soup = make_soup(
        """
        <a href="/survey/?cursor=abc">
            Next
        </a>
        """
    )

    assert scrape.get_next_page_url(soup) == (
        "https://www.thegradcafe.com/"
        "survey/?cursor=abc"
    )

    no_next = make_soup(
        '<a href="/survey/">Previous</a>'
    )

    assert scrape.get_next_page_url(no_next) is None


@pytest.mark.db
def test_save_data(tmp_path):
    file_path = tmp_path / "data.json"

    data = [{"url": "https://example.com/1"}]

    scrape.save_data(data, file_path)

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        saved = json.load(file)

    assert saved == data


@pytest.mark.db
def test_save_checkpoint(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    applicants = [
        {"url": "https://example.com/1"}
    ]

    scrape.save_checkpoint(
        applicants,
        "https://example.com/page2",
        2,
    )

    checkpoint_file = (
        tmp_path / "applicant_data_checkpoint.json"
    )

    assert checkpoint_file.exists()

    with open(
        checkpoint_file,
        "r",
        encoding="utf-8",
    ) as file:
        checkpoint = json.load(file)

    assert checkpoint["applicants"] == applicants
    assert checkpoint["next_url"] == (
        "https://example.com/page2"
    )
    assert checkpoint["page_number"] == 2


@pytest.mark.db
def test_load_checkpoint_missing(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    applicants, url, page_number = (
        scrape.load_checkpoint()
    )

    assert applicants == []
    assert url == scrape.build_page_url(1)
    assert page_number == 1


@pytest.mark.db
def test_load_checkpoint_old_format(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    applicants = [
        {"url": "https://example.com/1"}
    ]

    with open(
        "applicant_data_checkpoint.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(applicants, file)

    result, url, page_number = (
        scrape.load_checkpoint()
    )

    assert result == applicants
    assert url == scrape.build_page_url(1)
    assert page_number == 1


@pytest.mark.db
def test_load_checkpoint_new_format(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    checkpoint = {
        "applicants": [
            {"url": "https://example.com/1"}
        ],
        "next_url": "https://example.com/page2",
        "page_number": 2,
    }

    with open(
        "applicant_data_checkpoint.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(checkpoint, file)

    applicants, url, page_number = (
        scrape.load_checkpoint()
    )

    assert applicants == checkpoint["applicants"]
    assert url == "https://example.com/page2"
    assert page_number == 2


@pytest.mark.web
def test_create_driver(monkeypatch):
    fake_driver = object()

    monkeypatch.setattr(
        scrape.webdriver,
        "Chrome",
        lambda: fake_driver,
    )

    assert scrape.create_driver() is fake_driver


class FakeDriver:
    def __init__(self, quit_error=False):
        self.quit_called = False
        self.quit_error = quit_error

    def quit(self):
        self.quit_called = True

        if self.quit_error:
            raise RuntimeError("quit failed")


def configure_scrape(
    monkeypatch,
    applicants,
    next_urls,
    existing=None,
    first_render_error=False,
    quit_error=False,
):
    if existing is None:
        existing = []

    driver_one = FakeDriver(
        quit_error=quit_error
    )
    driver_two = FakeDriver()

    drivers = [driver_one, driver_two]

    monkeypatch.setattr(
        scrape,
        "load_checkpoint",
        lambda: (
            list(existing),
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

    render_calls = {"count": 0}

    def fake_render(driver, url):
        render_calls["count"] += 1

        if (
            first_render_error
            and render_calls["count"] == 1
        ):
            raise RuntimeError(
                "Chrome disconnected"
            )

        return "<html></html>"

    monkeypatch.setattr(
        scrape,
        "get_rendered_page",
        fake_render,
    )

    monkeypatch.setattr(
        scrape,
        "parse_page",
        lambda html: "fake-soup",
    )

    monkeypatch.setattr(
        scrape,
        "extract_rows",
        lambda soup: ["row"],
    )

    monkeypatch.setattr(
        scrape,
        "group_applicant_rows",
        lambda rows: [
            ("main", "detail", None)
            for _ in applicants
        ],
    )

    applicant_iterator = iter(applicants)

    monkeypatch.setattr(
        scrape,
        "parse_applicant",
        lambda main, detail, comment: next(
            applicant_iterator
        ),
    )

    next_iterator = iter(next_urls)

    def fake_next(soup):
        try:
            return next(next_iterator)
        except StopIteration:
            return None

    monkeypatch.setattr(
        scrape,
        "get_next_page_url",
        fake_next,
    )

    monkeypatch.setattr(
        scrape.time,
        "sleep",
        lambda seconds: None,
    )

    monkeypatch.setattr(
        scrape,
        "save_checkpoint",
        lambda *args: None,
    )

    return driver_one, render_calls


@pytest.mark.integration
def test_scrape_data_reaches_target(
    monkeypatch,
):
    applicants = [
        {
            "url": "https://example.com/1",
            "program": "Computer Science",
        },
        {
            "url": "https://example.com/2",
            "program": "Data Science",
        },
    ]

    driver, _ = configure_scrape(
        monkeypatch,
        applicants,
        next_urls=[],
    )

    result = scrape.scrape_data(
        target_count=2
    )

    assert len(result) == 2
    assert driver.quit_called is True


@pytest.mark.integration
def test_scrape_data_skips_duplicate_url(
    monkeypatch,
    capsys,
):
    existing = [
        {
            "url": "https://example.com/1",
            "program": "Existing",
        }
    ]

    applicants = [
        {
            "url": "https://example.com/1",
            "program": "Duplicate",
        },
        {
            "url": None,
            "program": "No URL",
        },
    ]

    configure_scrape(
        monkeypatch,
        applicants,
        next_urls=[None],
        existing=existing,
    )

    result = scrape.scrape_data(
        target_count=10
    )

    output = capsys.readouterr().out

    assert len(result) == 2
    assert result[0]["program"] == "Existing"
    assert result[1]["program"] == "No URL"
    assert "No Next page found." in output


@pytest.mark.integration
def test_scrape_data_restarts_after_render_error(
    monkeypatch,
    capsys,
):
    applicants = [
        {
            "url": "https://example.com/1",
            "program": "Computer Science",
        }
    ]

    driver, render_calls = configure_scrape(
        monkeypatch,
        applicants,
        next_urls=[],
        first_render_error=True,
        quit_error=True,
    )

    result = scrape.scrape_data(
        target_count=1
    )

    output = capsys.readouterr().out

    assert len(result) == 1
    assert render_calls["count"] == 2
    assert driver.quit_called is True
    assert "Chrome session disconnected." in output
    assert "Restarting Chrome once..." in output


@pytest.mark.integration
def test_scrape_data_repeated_page(
    monkeypatch,
    capsys,
):
    driver = FakeDriver()

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
        lambda soup: "https://example.com/page1",
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
        target_count=1
    )

    output = capsys.readouterr().out

    assert result == []
    assert "Repeated page detected." in output


@pytest.mark.integration
def test_scrape_data_keyboard_interrupt(
    monkeypatch,
    capsys,
):
    driver = FakeDriver()

    saved = {}

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

    def interrupt(driver, url):
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        scrape,
        "get_rendered_page",
        interrupt,
    )

    def fake_save(applicants, url, page):
        saved["values"] = (
            applicants,
            url,
            page,
        )

    monkeypatch.setattr(
        scrape,
        "save_checkpoint",
        fake_save,
    )

    result = scrape.scrape_data(
        target_count=1
    )

    output = capsys.readouterr().out

    assert result == []
    assert "Progress saved." in output
    assert "values" in saved
    assert driver.quit_called is True


@pytest.mark.integration
def test_scrape_data_general_error(
    monkeypatch,
    capsys,
):
    driver_one = FakeDriver()
    driver_two = FakeDriver()

    drivers = [driver_one, driver_two]

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
        lambda: drivers.pop(0),
    )

    monkeypatch.setattr(
        scrape,
        "get_rendered_page",
        lambda driver, url: (
            (_ for _ in ()).throw(
                RuntimeError("scrape failed")
            )
        ),
    )

    monkeypatch.setattr(
        scrape.time,
        "sleep",
        lambda seconds: None,
    )

    saved = {}

    def fake_save(applicants, url, page):
        saved["called"] = True

    monkeypatch.setattr(
        scrape,
        "save_checkpoint",
        fake_save,
    )

    with pytest.raises(
        RuntimeError,
        match="scrape failed",
    ):
        scrape.scrape_data(
            target_count=1
        )

    output = capsys.readouterr().out

    assert saved["called"] is True
    assert "Scraping stopped because of an error:" in output
    assert "Progress saved." in output