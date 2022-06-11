reset_db
========

:synopsis: Fully resets your database by running DROP DATABASE and CREATE DATABASE

Django command that resets your Django database, removing all data from all
tables. This allows you to run all migrations again.

By default the command will prompt you to confirm that all data will be
deleted. This can be turned off with the ``--noinput``-argument.

Supported engines
-----------------
The command detects whether you're using a SQLite, MySQL, or Postgres database
by looking up your Django database engine in the following lists.

::

  DEFAULT_SQLITE_ENGINES = (
      'django.db.backends.sqlite3',
      'django.db.backends.spatialite',
  )
  DEFAULT_MYSQL_ENGINES = (
      'django.db.backends.mysql',
      'django.contrib.gis.db.backends.mysql',
      'mysql.connector.django',
  )
  DEFAULT_POSTGRESQL_ENGINES = (
      'django.db.backends.postgresql',
      'django.db.backends.postgresql_psycopg2',
      'django.db.backends.postgis',
      'django.contrib.gis.db.backends.postgis',
      'psqlextra.backend',
      'django_zero_downtime_migrations.backends.postgres',
      'django_zero_downtime_migrations.backends.postgis',
  )

If the engine you're using is not listed above, check the optional settings
section below.


Example Usage
-------------

::

  # Reset the DB so that it contains no data and migrations can be run again
  $ ./manage.py reset_db mybucket

::

  # Don't ask for a confirmation before doing the reset
  $ ./manage.py reset_db --noinput

::

  # Use a different user and password than the one from settings.py
  $ ./manage.py reset_db --user db_root --password H4rd2Guess

Optional settings
-----------------

It is possible to use a Django DB engine not in the lists above -- to do that add
the approriate setting as shown below to your Django settings file::

  # settings.py
  DJANGO_EXTENSIONS_RESET_DB_SQLITE_ENGINES = ['your_custom_sqlite_engine']
  DJANGO_EXTENSIONS_RESET_DB_MYSQL_ENGINES = ['your_custom_mysql_engine']
  DJANGO_EXTENSIONS_RESET_DB_POSTGRESQL_ENGINES = ['your_custom_postgres_engine']
