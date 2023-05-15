sqldsn
======

:synopsis: Prints Data Source Name connection string on stdout



Supported Databases
-------------------

Currently the following databases are supported:

* PostgreSQL (psycopg2, psycopg3, or postgis)
* Sqlite3
* MySQL

Patches to support other databases are welcome! :-)


Supported Styles
----------------

Currently the following databases are supported:

+----------+------------+-------+---------+---------------------------+
| Style    | PostgreSQL | MySQL | Sqlite3 | Description               |
+==========+============+=======+=========+===========================+
| args     |            |   Y   |         | command-line arguments    |
+----------+------------+-------+---------+---------------------------+
| filename |            |       |    Y    | filename                  |
+----------+------------+-------+---------+---------------------------+
| keyvalue |      Y     |   Y   |         | key-value pairs (legacy)  |
+----------+------------+-------+---------+---------------------------+
| kwargs   |      Y     |       |         | Python keyword arguments  |
+----------+------------+-------+---------+---------------------------+
| pgpass   |      Y     |       |         | ``.pgpass`` format        |
+----------+------------+-------+---------+---------------------------+
| uri      |      Y     |   Y   |    Y    | (See ``dj-database-url``) |
+----------+------------+-------+---------+---------------------------+


Exit Codes
----------

Exit status is 0 unless invalid options were given.


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
  $ ./manage.py sqldsn --database=slave

::

  # Print all DSN styles available for the default database
  $ ./manage.py sqldsn --style=all

::

  # Print the URI for the default database
  $ ./manage.py sqldsn -q --style=uri

::

  # Create .pgpass file for default database by using the quiet option
  $ ./manage.py sqldsn -q --style=pgpass > .pgpass
