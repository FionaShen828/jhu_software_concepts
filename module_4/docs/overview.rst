Overview and Setup
==================

Overview
--------

GradCafe Analysis is a Flask application that works with applicant data
collected from GradCafe. The project includes data collection, data
cleaning, PostgreSQL storage, SQLAlchemy queries, and a web page for
viewing analysis results.

Module 4 extends the previous application by adding automated testing,
100% test coverage, and Sphinx documentation.

Project Structure
-----------------

The main project structure is::

    module_4/
    ├── src/
    ├── tests/
    ├── docs/
    ├── pytest.ini
    ├── requirements.txt
    └── coverage_summary.txt

The ``src`` directory contains the application code. The ``tests``
directory contains the pytest test suite, and the ``docs`` directory
contains the Sphinx documentation.

Environment Variables
---------------------

The application uses the following environment variables:

``DB_PASSWORD``
    Password used to connect to the local PostgreSQL database.

``DATABASE_URL``
    PostgreSQL connection URL. This can also be overridden during testing
    so that tests use a separate test database.

Do not store database passwords directly in the source code.

Install Dependencies
--------------------

From the ``module_4`` directory, install the project dependencies with::

    python3 -m pip install -r requirements.txt

Run the Application
-------------------

From the ``module_4`` directory, run the Flask application with::

    python3 src/app.py

The application runs locally and provides the GradCafe analysis page.

Run the Tests
-------------

Run the required marked tests with::

    python3 -m pytest -m "web or buttons or analysis or db or integration"

The project uses pytest-cov to measure test coverage. The complete test
suite currently reaches 100% coverage across the application source code.