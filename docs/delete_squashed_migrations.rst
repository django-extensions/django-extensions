delete_squashed_migrations
==========================

:synopsis: Deletes leftover migrations after squashing and converts squashed
           migration to a normal one.

Deletes leftover migrations after squashing and converts squashed migration to
a normal one by removing the replaces attribute. This automates the clean up
procedure outlined at the end of the `Django migration squashing
documentation`__. Modifies your source tree! Use with care!

__ MigrationSquashingDocs_

Example Usage
-------------

With *django-extensions* installed you cleanup squashed migrations using the
*delete_squashed_migrations* command::

  # Delete leftover migrations from the first squashed migration found in myapp
  $ ./manage.py delete_squashed_migrations myapp

  # As above but non-interactive
  $ ./manage.py --noinput delete_squashed_migrations myapp

  # Explicitly specify the squashed migration to clean up
  $ ./manage.py delete_squashed_migrations myapp 0001_squashed


.. _MigrationSquashingDocs: https://docs.djangoproject.com/en/dev/topics/migrations/#migration-squashing
