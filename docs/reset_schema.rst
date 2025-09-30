reset_schema
========

:synopsis: Fully resets your database by running DROP SCHEMA and CREATE SCHEMA

Django command that resets your Django database, removing all data from all
tables. This allows you to run all migrations again.

By default the command will prompt you to confirm that all data will be
deleted. This can be turned off with the ``--noinput``-argument.

Supported engines
-----------------
The command supports only Postgres database.

Example Usage
-------------

::

  # Reset the public schema so that database contains no data and migrations can be run again
  $ ./manage.py reset_schema

::

  # Don't ask for a confirmation before doing the reset
  $ ./manage.py reset_schema --noinput

::

  # Use a specific database router
  $ ./manage.py reset_schema --router my_router

::

  # Run command for a specific database
  $ ./manage.py reset_schema --database secondary_db

::

  # Drop a different schema instead of "public"
  $ ./manage.py reset_schema --schema custom_schema

::

  # Run with increased verbosity level
  $ ./manage.py reset_schema --verbosity 2

::

  # Use a specific settings module
  $ ./manage.py reset_schema --settings myproject.settings.local

::

  # Add a directory to Python path
  $ ./manage.py reset_schema --pythonpath "/home/djangoprojects/myproject"

::

  # Show full traceback on errors
  $ ./manage.py reset_schema --traceback

::

  # Run without colored output
  $ ./manage.py reset_schema --no-color

::

  # Force colored output
  $ ./manage.py reset_schema --force-color

::

  # Skip system checks
  $ ./manage.py reset_schema --skip-checks
