sqldsn
======

:synopsis: Prints Data Source Name connection string on stdout



Supported Databases
-------------------

Currently the following databases are supported:

* PostgreSQL
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

  # Print the DSN for database named 'slave'
  $ ./manage.py sqldsn --router=slave
