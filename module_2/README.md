# Module 2 - GradCafe Web Scraping and Data Cleaning

**Name:** Fiona Shen  
**JHED ID:** [Add JHED ID]  
**Due Date:** [Add Due Date]

## Project Overview

This project collects graduate admissions data from GradCafe and stores the results in a structured JSON format. The scraper collects applicant information such as university, program, degree, admission status, dates, term, applicant type, GPA, GRE scores, comments, and the original listing text.

The project also uses the provided local LLM package to standardize program and university names while preserving the original scraped values.

## Project Structure

- `scrape.py` - Scrapes and parses GradCafe applicant data.
- `clean.py` - Prepares the scraped data and runs the provided local LLM standardizer.
- `applicant_data.json` - Scraped applicant records.
- `llm_extend_applicant_data.json` - Final data with LLM-generated standardized program and university names.
- `screenshot.jpg` - Screenshot of the GradCafe robots.txt file.
- `requirements.txt` - Python packages required for scraping.
- `llm_hosting/` - Local LLM package provided with the assignment.

## Responsible Scraping

Before scraping, I checked GradCafe's `robots.txt`. A screenshot is included as `screenshot.jpg`.

The general `User-agent: *` section displayed `Allow: /`. I used only publicly available applicant result pages and did not attempt to bypass logins, CAPTCHAs, rate limits, or other access restrictions.

A direct request using `urllib.request` returned HTTP 403, so I stopped using direct urllib requests rather than attempting to bypass the restriction. `urllib.parse` is used for URL construction and management. The scraper uses browser-rendered public pages for retrieving the applicant listings.

The scraper includes delays between pages and checkpoint/resume functionality so that an interrupted collection does not need to restart from the beginning.

## Scraping Approach

The scraper:

1. Builds and manages GradCafe URLs using `urllib.parse`.
2. Loads public applicant result pages.
3. Parses the rendered HTML using BeautifulSoup.
4. Follows GradCafe pagination using the Next-page cursor.
5. Extracts applicant information when available.
6. Preserves the original listing text in `raw_listing_text`.
7. Saves progress using a checkpoint.
8. Stores the final results in `applicant_data.json`.

Missing information is stored as `null` in JSON.

## Data Cleaning

GradCafe program and university names can contain inconsistent spelling, abbreviations, and formatting. I used the local LLM package provided with the assignment to standardize these values.

Before sending a row to the provided standardizer, `clean.py` temporarily combines the program and university values into the input expected by the LLM. The original scraped values are preserved and restored afterward.

The final output keeps the original:

- `program`
- `university`

and adds:

- `llm-generated-program`
- `llm-generated-university`

The cleaned data is saved as `llm_extend_applicant_data.json`.

## Setup

Python 3.10 or later is required.

Create and activate a virtual environment, then install the scraping dependencies:

```bash
pip install -r requirements.txt