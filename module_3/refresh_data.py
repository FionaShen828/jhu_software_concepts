import json
from pathlib import Path

from sqlalchemy import select

from models import Applicant, SessionLocal
from scrape import (
    RESULTS_URL,
    create_driver,
    get_rendered_page,
    parse_page,
    extract_rows,
    group_applicant_rows,
    parse_applicant,
    get_next_page_url,
)


BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_FILE = BASE_DIR / "applicant_data.json"

# Safety limit so Pull Data does not accidentally start
# a very long scraping session.
MAX_PAGES = 5


def load_existing_urls():
    """Load URLs already stored in PostgreSQL."""
    with SessionLocal() as session:
        urls = session.scalars(
            select(Applicant.url).where(
                Applicant.url.is_not(None)
            )
        ).all()

    return set(urls)


def load_raw_data():
    """Load the existing raw applicant JSON file."""
    if not RAW_DATA_FILE.exists():
        return []

    with open(
        RAW_DATA_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_raw_data(data):
    """Save updated raw applicant data."""
    with open(
        RAW_DATA_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def refresh_data():
    """
    Check the newest GradCafe pages and append only
    records that are not already in PostgreSQL.
    """

    existing_urls = load_existing_urls()
    raw_data = load_raw_data()

    # Also protect against duplicates already present
    # in the JSON file.
    raw_urls = {
        applicant.get("url")
        for applicant in raw_data
        if applicant.get("url")
    }

    known_urls = existing_urls | raw_urls

    print(
        f"Existing database URLs: {len(existing_urls)}"
    )

    print(
        f"Existing raw records: {len(raw_data)}"
    )

    driver = create_driver()

    current_url = RESULTS_URL
    new_applicants = []

    try:
        for page_number in range(1, MAX_PAGES + 1):

            print(
                f"Checking latest GradCafe page "
                f"{page_number}..."
            )

            html = get_rendered_page(
                driver,
                current_url,
            )

            soup = parse_page(html)
            rows = extract_rows(soup)

            applicant_rows = group_applicant_rows(
                rows
            )

            page_new_records = 0

            for (
                main_row,
                detail_row,
                comment_row,
            ) in applicant_rows:

                applicant = parse_applicant(
                    main_row,
                    detail_row,
                    comment_row,
                )

                applicant_url = applicant.get(
                    "url"
                )

                if not applicant_url:
                    continue

                if applicant_url in known_urls:
                    continue

                known_urls.add(applicant_url)
                new_applicants.append(applicant)

                page_new_records += 1

            print(
                f"New records on this page: "
                f"{page_new_records}"
            )

            # GradCafe is ordered newest first.
            # Once a full page contains no new URLs,
            # older pages should already be represented
            # in our existing dataset.
            if page_new_records == 0:
                print(
                    "Reached records already stored "
                    "in the database."
                )
                break

            next_url = get_next_page_url(soup)

            if next_url is None:
                print(
                    "No next page found."
                )
                break

            current_url = next_url

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    if not new_applicants:
        print()
        print("No new GradCafe records found.")
        return 0

    raw_data.extend(new_applicants)
    save_raw_data(raw_data)

    print()
    print(
        f"New records found: "
        f"{len(new_applicants)}"
    )

    print(
        f"Updated raw record total: "
        f"{len(raw_data)}"
    )

    print(
        "Updated applicant_data.json"
    )

    return len(new_applicants)


if __name__ == "__main__":
    refresh_data()