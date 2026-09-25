Architecture
============

The GradCafe Analysis project is organized into separate layers for the
web application, data processing, database access, and analysis. This
structure keeps the responsibilities of each part of the application
separate and easier to test.

Web Layer
---------

The Flask web application is implemented in ``app.py``. It displays the
analysis page and provides routes for updating the analysis and pulling
new applicant data.

The main routes include:

* ``/analysis`` - displays the analysis page.
* ``/pull-data`` - starts the data refresh process.
* ``/update-analysis`` - updates the analysis results.

The application also exposes a ``create_app()`` factory so Flask
configuration can be changed during testing.

ETL and Data Processing Layer
-----------------------------

The project uses several modules to collect and process applicant data.

``scrape.py``
    Collects applicant records from GradCafe and extracts the required
    applicant information.

``refresh_data.py``
    Checks for newer GradCafe records and updates the local raw dataset.

``clean.py``
    Standardizes program and university names using the local LLM
    cleaning workflow.

``load_data.py``
    Loads the processed applicant records into PostgreSQL while preventing
    duplicate URLs.

Database Layer
--------------

PostgreSQL is used to store applicant records. Database connection
information is provided through environment variables rather than
hard-coded credentials.

``models.py``
    Defines the SQLAlchemy applicant model and database configuration.

``load_data.py``
    Creates the applicant table when necessary and inserts applicant
    records into the database.

Analysis Layer
--------------

``query_data.py`` and ``orm_queries.py`` contain the database queries used
to analyze applicant data.

The analysis results are used by the Flask application and displayed on
the analysis page. Results include formatted values such as percentages
and other applicant statistics.

Application Flow
----------------

The general application flow is::

    GradCafe
       |
       v
    scrape.py / refresh_data.py
       |
       v
    applicant_data.json
       |
       v
    clean.py
       |
       v
    load_data.py
       |
       v
    PostgreSQL
       |
       v
    query_data.py / orm_queries.py
       |
       v
    Flask application
       |
       v
    Analysis page

This separation also allows the test suite to replace external
dependencies with test doubles so tests do not depend on live internet
requests or long-running scraping.