sqlcreate
==========

:synopsis: Helps you setup your database(s) more easily


Introduction
-------------

Stop creating databases by hand.  Your settings.py file already contains the correct
information, so DRY.

Usage
-------------

  $ python manage.py sqlcreate [--database=<databasename>] | <my_database_shell_command>

It will spit out SQL which you can review (if you want). Ultimately you want to
pipe it into the database shell command of your choice.

If there were a good way to ensure that the user in the database settings had the
proper permissions, we could submit the commands straight to the database.
However, due to the nature of this portion of the project setup, that will never happen.

Example
-------------

PostgreSQL
~~~~~~~~~~
  $ ./manage.py sqlcreate [--database=<databasename>] | psql -U <db_administrator> -W

.. note::
    If `USER` or `PASSWORD` are empty string or None, the `sqlcreate` assumes that unix domain
    socket connection mode is being used, and because of that the SQL clauses `CREATE USER` and
    privilege grants to the database and database user are not generated.


MySQL
~~~~~
  $ ./manage.py sqlcreate [--database=<databasename>] | mysql -u <db_administrator> -p


Known Issues
------------

 * CREATE DATABASE is not SQL standard so might not work everywhere.
 * When using fallback user is not created and password is not set.
   But it does try to do a GRANT to the database user.
 * Missing options for tablespaces, etc.
