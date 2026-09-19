# Module 3 - GradCafe Database Analysis

**Name:** Fiona Shen\
**JHED ID:** \[Add JHED ID\]

## Project Overview

This project continues the GradCafe work from Module 2 by moving the
cleaned applicant data into a PostgreSQL database. I use raw SQL and
SQLAlchemy to answer questions about the admissions data, and the Flask
page displays the analysis results from the database.

The project also keeps the Module 2 scraping and local LLM cleaning
workflow so that newly available GradCafe entries can be pulled,
cleaned, and added to the database without replacing the records that
are already there.

## Main Files

-   `load_data.py` - Creates the applicants table when needed and loads
    the cleaned JSON data into PostgreSQL.
-   `query_data.py` - Answers Questions 1-9 and my two original
    questions using raw SQL.
-   `models.py` - Defines the SQLAlchemy `Applicant` model and database
    session.
-   `orm_queries.py` - Repeats the required analyses using SQLAlchemy.
-   `app.py` - Runs the Flask application.
-   `refresh_data.py` - Checks the newest GradCafe pages for records
    that are not already stored.
-   `scrape.py` - Module 2 scraping and parsing code reused by the
    refresh process.
-   `clean.py` - Runs the provided local LLM standardization workflow.
-   `templates/index.html` - HTML template for the analysis page.
-   `static/style.css` - Styling for the Flask page.
-   `query_results.pdf` - Results, SQL queries, and explanations for all
    11 analysis questions.
-   `limitations.pdf` - Reflection on limitations of the GradCafe data.
-   `requirements.txt` - Python packages used by the project.

## Data and Cleaning

The original data comes from public GradCafe applicant-result listings.
The scraper collects fields such as university, program, degree,
admission status, term, applicant type, GPA, GRE scores, comments, and
the listing URL.

Because university and program names are not always written
consistently, I use the local LLM package provided for the assignment to
create standardized program and university fields. The original values
are still kept in the data. This is important because some of the Module
3 questions specifically compare the original downloaded fields with the
LLM-generated fields.

The cleaned file used for database loading is
`llm_extend_applicant_data.json`.

## PostgreSQL Setup

This project uses a PostgreSQL database named `gradcafe`. PostgreSQL
should be running before the scripts are used.

The database password is not stored in the repository. I provide it
through the `DB_PASSWORD` environment variable in the Terminal session:

``` bash
export DB_PASSWORD="your_postgresql_password"
```

After the database has been created, load the cleaned data with:

``` bash
python load_data.py
```

`load_data.py` creates the `applicants` table if needed and inserts the
cleaned records. The listing URL is treated as unique, so running the
loader again does not keep inserting the same applicant records.

## Running the SQL Analysis

To run the raw SQL questions:

``` bash
python query_data.py
```

This prints the answers for Questions 1-9 and the two original
questions. The same questions, results, SQL statements, and short
explanations are included in `query_results.pdf`.

## Running the SQLAlchemy Analysis

To run the required questions through SQLAlchemy:

``` bash
python orm_queries.py
```

`models.py` maps the existing PostgreSQL `applicants` table to the
`Applicant` Python class. The ORM analysis uses the same database and
table as the raw SQL analysis rather than making a separate copy of the
data.

## Raw SQL and SQLAlchemy Comparison

For Question 1, my raw SQL version uses `SELECT COUNT(*)` with
`WHERE term = 'Fall 2026'`. The SQLAlchemy version expresses the same
idea with Python objects such as `select()`, `func.count()`, and
`Applicant.term`. I found the ORM version useful when working with the
Flask application because the database logic stays in Python and works
naturally with the `Applicant` model. On the other hand, the raw SQL
version is shorter for this question and makes the exact database
operation very easy to see, so direct SQL can be more convenient for a
simple query.

## Flask Application

Start the webpage with:

``` bash
python app.py
```

Then open the local address shown in the Terminal, normally:

``` text
http://127.0.0.1:8080
```

The page reads the analysis results from PostgreSQL through SQLAlchemy.
`Update Analysis` queries the current database again and refreshes the
displayed results.

`Pull Data` starts the data-refresh process in the background. It checks
the newest GradCafe pages for records that are not already stored, runs
the cleaning step for new data, and then loads usable new records into
PostgreSQL. The application prevents another Pull Data process from
starting while one is already running. After the refresh finishes,
`Update Analysis` can be used to show the newest database results.

## Module 2 Scraping Notes

Before the original scraping work, I checked GradCafe's `robots.txt` and
saved a screenshot as `screenshot.jpg`. A direct `urllib.request`
request returned HTTP 403, so I did not try to bypass that response. The
Module 2 scraper instead uses browser-rendered public result pages and
includes delays and checkpoint/resume behavior.

For Module 3, `refresh_data.py` reuses the parsing functions from the
Module 2 scraper but only checks the newest pages for newly available
records. Existing URLs are used to avoid adding duplicate records.

## Installation

Python 3.10 or later is recommended. Create and activate a virtual
environment, then install the required packages:

``` bash
pip install -r requirements.txt
```

Do not store PostgreSQL passwords, `.env` credentials, virtual
environments, or other secrets in the repository.
