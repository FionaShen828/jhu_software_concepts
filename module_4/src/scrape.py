import json
import time
from urllib.parse import urljoin, urlencode

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://www.thegradcafe.com/"
RESULTS_URL = "https://www.thegradcafe.com/survey/"


def build_page_url(page_number):
    query = urlencode({"page": page_number})
    return f"{RESULTS_URL}?{query}"


def get_rendered_page(driver, url):
    driver.get(url)

    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script(
            "return document.readyState"
        ) == "complete"
    )

    WebDriverWait(driver, 15).until(
        lambda d: len(
            d.find_elements(By.TAG_NAME, "tr")
        ) > 1
    )

    return driver.page_source


def parse_page(html):
    return BeautifulSoup(
        html,
        "html.parser"
    )


def extract_rows(soup):
    return soup.find_all("tr")


def group_applicant_rows(rows):
    applicants = []

    for i in range(len(rows) - 1):
        main_row = rows[i]

        # Detail and comment rows use this class.
        if "tw-border-none" in main_row.get(
            "class",
            []
        ):
            continue

        detail_row = rows[i + 1]

        if "tw-border-none" not in detail_row.get(
            "class",
            []
        ):
            continue

        comment_row = None

        # Comments appear in the row after
        # the applicant detail row.
        if "Total comments" in main_row.get_text(
            " ",
            strip=True
        ):
            if i + 2 < len(rows):
                possible_comment = rows[i + 2]

                if (
                    "tw-border-none"
                    in possible_comment.get(
                        "class",
                        []
                    )
                ):
                    comment_row = possible_comment

        applicants.append(
            (
                main_row,
                detail_row,
                comment_row
            )
        )

    return applicants


def extract_university(main_row):
    cells = main_row.find_all("td")

    if not cells:
        return None

    return cells[0].get_text(
        " ",
        strip=True
    )


def extract_program_and_degree(main_row):
    cells = main_row.find_all("td")

    if len(cells) < 2:
        return None, None

    spans = cells[1].find_all("span")

    program = (
        spans[0].get_text(
            " ",
            strip=True
        )
        if len(spans) > 0
        else None
    )

    degree = (
        spans[1].get_text(
            " ",
            strip=True
        )
        if len(spans) > 1
        else None
    )

    return program, degree


def extract_date_and_decision(main_row):
    cells = main_row.find_all("td")

    if len(cells) < 4:
        return None, None

    date_added = cells[2].get_text(
        " ",
        strip=True
    )

    decision = cells[3].get_text(
        " ",
        strip=True
    )

    return date_added, decision


def extract_status_and_decision_date(
    decision
):
    if not decision:
        return None, None

    if " on " in decision:
        status, decision_date = (
            decision.split(
                " on ",
                1
            )
        )

        return (
            status.strip(),
            decision_date.strip()
        )

    return decision.strip(), None


def extract_detail_url(main_row):
    link = main_row.find(
        "a",
        href=lambda href: (
            href
            and href.startswith(
                "/result/"
            )
        )
    )

    if link is None:
        return None

    return urljoin(
        BASE_URL,
        link["href"]
    )


def extract_term(detail_row):
    text = detail_row.get_text(
        " ",
        strip=True
    )

    parts = text.split()

    for season in [
        "Spring",
        "Summer",
        "Fall",
        "Winter"
    ]:
        for i, part in enumerate(parts):
            if (
                part == season
                and i + 1 < len(parts)
            ):
                return (
                    f"{season} "
                    f"{parts[i + 1]}"
                )

    return None


def extract_semester_and_year(term):
    if not term:
        return None, None

    parts = term.split()

    if len(parts) < 2:
        return None, None

    semester = parts[0]
    start_year = parts[1]

    return semester, start_year


def extract_applicant_type(detail_row):
    text = detail_row.get_text(
        " ",
        strip=True
    )

    if "International" in text:
        return "International"

    if "American" in text:
        return "American"

    return None


def extract_scores(detail_row):
    text = detail_row.get_text(
        " ",
        strip=True
    )

    parts = text.split()

    gpa = None
    gre = None
    gre_v = None
    gre_aw = None

    for i, part in enumerate(parts):

        if (
            part == "GPA"
            and i + 1 < len(parts)
        ):
            gpa = parts[i + 1]

        elif (
            part == "GRE"
            and i + 2 < len(parts)
            and parts[i + 1] == "V"
        ):
            gre_v = parts[i + 2]

        elif (
            part == "GRE"
            and i + 2 < len(parts)
            and parts[i + 1] == "AW"
        ):
            gre_aw = parts[i + 2]

        elif (
            part == "GRE"
            and i + 1 < len(parts)
        ):
            gre = parts[i + 1]

    return (
        gpa,
        gre,
        gre_v,
        gre_aw
    )


def parse_applicant(
    main_row,
    detail_row,
    comment_row=None
):
    university = extract_university(
        main_row
    )

    program, degree = (
        extract_program_and_degree(
            main_row
        )
    )

    date_added, decision = (
        extract_date_and_decision(
            main_row
        )
    )

    status, decision_date = (
        extract_status_and_decision_date(
            decision
        )
    )

    url = extract_detail_url(
        main_row
    )

    term = extract_term(
        detail_row
    )

    semester, start_year = (
        extract_semester_and_year(
            term
        )
    )

    applicant_type = (
        extract_applicant_type(
            detail_row
        )
    )

    (
        gpa,
        gre,
        gre_v,
        gre_aw
    ) = extract_scores(
        detail_row
    )

    comments = None

    if comment_row is not None:
        comments = comment_row.get_text(
            " ",
            strip=True
        )

    raw_listing_text = (
        main_row.get_text(
            " ",
            strip=True
        )
        + " "
        + detail_row.get_text(
            " ",
            strip=True
        )
    )

    if comment_row is not None:
        raw_listing_text += (
            " "
            + comment_row.get_text(
                " ",
                strip=True
            )
        )

    applicant = {
        "university": university,
        "program": program,
        "degree": degree,
        "date_added": date_added,
        "status": status,
        "decision": decision,
        "decision_date": decision_date,
        "url": url,
        "term": term,
        "semester": semester,
        "start_year": start_year,
        "applicant_type": applicant_type,
        "gpa": gpa,
        "gre": gre,
        "gre_v": gre_v,
        "gre_aw": gre_aw,
        "comments": comments,
        "raw_listing_text": (
            raw_listing_text
        ),
    }

    return applicant


def get_next_page_url(soup):
    for link in soup.find_all(
        "a",
        href=True
    ):
        text = link.get_text(
            " ",
            strip=True
        )

        href = link["href"]

        if (
            text == "Next"
            and "cursor=" in href
        ):
            return urljoin(
                BASE_URL,
                href
            )

    return None


def save_data(data, filename):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


def save_checkpoint(applicants, next_url, page_number):
    checkpoint = {
        "applicants": applicants,
        "next_url": next_url,
        "page_number": page_number
    }

    with open(
        "applicant_data_checkpoint.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            checkpoint,
            file,
            ensure_ascii=False,
            indent=2
        )


def load_checkpoint():
    try:
        with open(
            "applicant_data_checkpoint.json",
            "r",
            encoding="utf-8"
        ) as file:
            checkpoint = json.load(file)

    except FileNotFoundError:
        return [], build_page_url(1), 1

    # Supports the older checkpoint format
    # that only contained a list of applicants.
    if isinstance(checkpoint, list):
        print(
            f"Found old checkpoint with "
            f"{len(checkpoint)} applicants."
        )

        return (
            checkpoint,
            build_page_url(1),
            1
        )

    applicants = checkpoint.get(
        "applicants",
        []
    )

    next_url = checkpoint.get(
        "next_url",
        build_page_url(1)
    )

    page_number = checkpoint.get(
        "page_number",
        1
    )

    print(
        f"Resuming checkpoint: "
        f"{len(applicants)} applicants."
    )

    return (
        applicants,
        next_url,
        page_number
    )


def create_driver():
    return webdriver.Chrome()


def scrape_data(target_count=30000):
    (
        all_applicants,
        url,
        page_number
    ) = load_checkpoint()

    seen_urls = {
        applicant["url"]
        for applicant in all_applicants
        if applicant.get("url")
    }

    seen_page_urls = set()

    driver = create_driver()

    pages_this_session = 0

    try:
        while (
            len(all_applicants)
            < target_count
        ):

            if url in seen_page_urls:
                print(
                    "Repeated page detected. "
                    "Stopping."
                )
                break

            seen_page_urls.add(url)

            print(
                f"Scraping page "
                f"{page_number} | "
                f"Applicants: "
                f"{len(all_applicants)}"
            )

            # Try the page once.
            # If Chrome itself disconnects,
            # restart the browser and try
            # the same page one more time.
            try:
                html = get_rendered_page(
                    driver,
                    url
                )

            except Exception as first_error:
                print(
                    "Chrome session disconnected."
                )

                print(
                    "Restarting Chrome once..."
                )

                try:
                    driver.quit()
                except Exception:
                    pass

                time.sleep(5)

                driver = create_driver()

                html = get_rendered_page(
                    driver,
                    url
                )

            soup = parse_page(html)

            rows = extract_rows(soup)

            applicant_rows = (
                group_applicant_rows(
                    rows
                )
            )

            new_records = 0

            for (
                main_row,
                detail_row,
                comment_row
            ) in applicant_rows:

                applicant = parse_applicant(
                    main_row,
                    detail_row,
                    comment_row
                )

                applicant_url = (
                    applicant["url"]
                )

                if (
                    applicant_url
                    and applicant_url
                    in seen_urls
                ):
                    continue

                if applicant_url:
                    seen_urls.add(
                        applicant_url
                    )

                all_applicants.append(
                    applicant
                )

                new_records += 1

            print(
                f"Added "
                f"{new_records} "
                f"new applicants."
            )

            if (
                len(all_applicants)
                >= target_count
            ):
                break

            next_url = get_next_page_url(
                soup
            )

            if next_url is None:
                print(
                    "No Next page found. "
                    "Stopping."
                )
                break

            page_number += 1
            pages_this_session += 1

            # Save exact resume position
            # after every page.
            save_checkpoint(
                all_applicants,
                next_url,
                page_number
            )

            url = next_url

            # Polite delay between pages.
            time.sleep(2)

            # Restart Chrome periodically
            # to avoid long-session crashes.
            if pages_this_session >= 25:
                print(
                    "Restarting Chrome "
                    "for stability..."
                )

                try:
                    driver.quit()
                except Exception:
                    pass

                time.sleep(3)

                driver = create_driver()

                pages_this_session = 0

    except KeyboardInterrupt:
        print(
            "\nScraping stopped by user."
        )

        save_checkpoint(
            all_applicants,
            url,
            page_number
        )

        print(
            "Progress saved."
        )

    except Exception as error:
        print(
            "Scraping stopped because "
            "of an error:"
        )

        print(error)

        save_checkpoint(
            all_applicants,
            url,
            page_number
        )

        print(
            "Progress saved."
        )

        raise

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    return all_applicants


if __name__ == "__main__":  # pragma: no cover
    applicants = scrape_data(
        target_count=30000
    )

    save_data(
        applicants,
        "applicant_data.json"
    )

    print()
    print("Finished.")

    print(
        "Total applicants:",
        len(applicants)
    )

    print(
        "Unique URLs:",
        len(
            {
                applicant["url"]
                for applicant
                in applicants
                if applicant["url"]
            }
        )
    )

    print(
        "Saved to "
        "applicant_data.json"
    )