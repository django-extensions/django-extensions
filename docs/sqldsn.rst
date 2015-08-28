sqldsn
======

:synopsis: Prints Data Source Name connection string on stdout



Supported Databases
-------------------

Currently the following databases are supported:

* PostgreSQL (psycopg2 or postgis)
* Sqlite3
* MySQL

Patches to support other databases are welcome! :-)

Exit Codes
----------

Exit status is 0


Example Usage
-------------

::

  # Prints the DSN for the default database
  $ ./manage.py sqldsn

::

  # Prints the DSN for all databases
  $ ./manage.py sqldsn --all

::

  # Print the DSN for database named 'slave'
  $ ./manage.py sqldsn --router=slave

::

  # Print all DSN styles available for the default database
  $ ./manage.py sqldsn --style=all

::

  # Create .pgpass file for default database by using the quiet option
  $ ./manage.py sqldsn -q --style=pgpass > .pgpass

