migrationstate
==============

:synopsis: Dumps/Restores the current migration state of all installed apps.


Why?
----

If you, for instance, want to re-import data taken out of an existing
database with the `dumpdata` command into a fresh one, you need to ensure
the database tables of all apps are migrated to the state they were when
the `dumpdata` command was run.

To achieve this, you'd need to run::

  $ ./manage.py showmigrations

and manually apply all migrations that were applied before on the
new system, which is annoying and susceptible to mistakes.

That's why the `migrationstate` command was written. It automates this
task for you by storing the current migration state in machine-readable
JSON.


How?
----

To dump the migration state of all apps installed in your project::

  $ ./manage.py migrationstate dump > migrationstate.json

To dump the migration state of just a single app `appname`::

  $ ./manage.py migrationstate appname > migrationstate.json

To apply the migration state stored in `migrationstate.json`::

  $ ./manage.py migrationstate load < migrationstate.json

A full usage scenario could look like this::

  # We dump the state of the auth app...
  $ ./manage.py dumpscript auth > auth_dump.py
  $ ./manage.py migrationstate dump auth > auth_migrationstate.json

  # And then restore it elsewhere...
  $ ./manage.py reset_db
  $ ./manage.py migrationstate load < auth_migrationstate.json
  $ ./manage.py runscript auth_dump.py

Have a look at::

  $ ./manage.py migrationstate --help
  $ ./manage.py migrationstate dump --help
  $ ./manage.py migrationstate load --help

for the full list of options.


Caveats
-------

Consistency of Migrations
~~~~~~~~~~~~~~~~~~~~~~~~~

It should be clear, but I'm mentioning it anyway. To be able to reproduce
a previously dumped migration state, all migration files up to that
state still need to be present when restoring. Never delete or change
migrations that have already been deployed. You may of course squash
existing migrations, but leave the original ones in place so that people
can upgrade smoothly.
