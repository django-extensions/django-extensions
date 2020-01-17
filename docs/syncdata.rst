syncdata
========

:synopsis: Makes the current database have the same data as the fixture(s), no more, no less.


Introduction
-------------

Django command similar to 'loaddata' but also deletes.
After 'syncdata' has run, the database will have the same data as the fixture - anything
missing will of been added, anything different will of been updated,
and anything extra will of been deleted.

Usage
-----

.. tip::
   Command will loop over *fixtures* inside installed apps and pathes defined in ``FIXTURE_DIRS``.

Assuming that you've got sample.json under *fixtures* directory in one of your ``INSTALLED_APPS``::

  $ python manage.py syncdata sample.json

If you want to keep old records use ``--skip-remove`` option::

   $ python manage syncdata sample.xml --skip-remove

You can provide full path to your fixtures file like::

   $ python manage syncdata /var/fixtures/sample.json
