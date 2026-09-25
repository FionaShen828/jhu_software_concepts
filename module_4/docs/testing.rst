Testing Guide
=============

The Module 4 test suite uses pytest to test the Flask application,
database operations, analysis formatting, button behavior, and
end-to-end application flows.

Test Organization
-----------------

All test code is stored in the ``tests`` directory. Tests are separated
from the application code in ``src`` so that the project structure keeps
testing and application responsibilities separate.

Pytest Markers
--------------

Tests use the following markers:

``web``
    Tests Flask routes and page behavior.

``buttons``
    Tests the Pull Data and Update Analysis buttons.

``analysis``
    Tests analysis output and formatting.

``db``
    Tests database operations, inserts, and queries.

``integration``
    Tests workflows that involve multiple parts of the application.

The required marked tests can be run with::

    python3 -m pytest -m "web or buttons or analysis or db or integration"

Stable Selectors
----------------

The Flask page uses stable ``data-testid`` attributes so tests can identify
important controls without depending on presentation or styling.

The main selectors are:

* ``data-testid="pull-data-btn"``
* ``data-testid="update-analysis-btn"``

Test Doubles
------------

The tests use monkeypatching and test doubles to replace external
dependencies when appropriate. This keeps the automated tests independent
from live internet access and long-running GradCafe scraping.

Fake applicant records are used to test the data pipeline without making
live requests to GradCafe.

Database Testing
----------------

Database integration tests use a separate PostgreSQL test database. The
``DATABASE_URL`` environment variable can be overridden so tests do not
modify the normal GradCafe database.

The database tests verify behaviors such as inserting applicant records,
preventing duplicate URLs, and retrieving expected data.

Integration Testing
-------------------

Integration tests check the flow between multiple parts of the
application. This includes pulling fake applicant data, loading the data
into PostgreSQL, updating the analysis, and checking the Flask analysis
page.

The tests also verify that overlapping data pulls are handled correctly.

Coverage
--------

pytest-cov is used to measure code coverage. The project is configured to
require 100% coverage for the application source code.

Coverage can be checked with::

    python3 -m pytest -q -o addopts="--cov=src --cov-report=term-missing"

The current test suite contains 94 passing tests and reaches 100% coverage
across the ``src`` directory.

The saved coverage output is available in ``coverage_summary.txt``.