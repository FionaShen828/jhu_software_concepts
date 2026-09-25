API Reference
=============

This section documents the main Python modules used by the GradCafe
Analysis application. The documentation is generated from the source
code using Sphinx autodoc.

Flask Application
-----------------

The Flask application provides the web interface and routes for displaying
analysis results, pulling new data, and updating the analysis.

.. automodule:: app
   :members:
   :undoc-members:
   :show-inheritance:

Scraping
--------

The scraping module collects and parses applicant records from GradCafe.

.. automodule:: scrape
   :members:
   :undoc-members:
   :show-inheritance:

Data Refresh
------------

The refresh module checks for new applicant records and updates the raw
dataset.

.. automodule:: refresh_data
   :members:
   :undoc-members:
   :show-inheritance:

Data Cleaning
-------------

The cleaning module standardizes program and university information before
the records are loaded into the database.

.. automodule:: clean
   :members:
   :undoc-members:
   :show-inheritance:

Database Loading
----------------

The database loader creates the applicant table when needed and inserts
processed applicant records into PostgreSQL.

.. automodule:: load_data
   :members:
   :undoc-members:
   :show-inheritance:



Data Queries
------------

The query module contains database queries used to generate applicant
analysis results.

.. automodule:: query_data
   :members:
   :undoc-members:
   :show-inheritance:

SQLAlchemy Queries
------------------

The ORM query module performs applicant analysis using SQLAlchemy.

.. automodule:: models
   :members:
   :exclude-members: metadata
   :undoc-members:
   :show-inheritance: