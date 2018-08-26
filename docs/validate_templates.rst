validate_templates
==================

:synopsis: Checks templates on syntax or compile errors.

Options
-------

verbosity
~~~~~~~~~
A higher verbosity level will print out all the files that are processed
instead of only the ones that contain errors.

break
~~~~~
Do not continue scanning other templates after the first failure.

ignore_app
~~~~~~~~~~
Ignore this app (can be used multiple times).

includes
~~~~~~~~
Use -i (can be used multiple times) to add directories to the TEMPLATE DIRS.

no_apps
~~~~~~~
Do not automatically include app template directories.


Settings
--------

VALIDATE_TEMPLATES_IGNORE_APPS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ignore the following apps


VALIDATE_TEMPLATES_IGNORES
~~~~~~~~~~~~~~~~~~~~~~~~~~

Ignore file names which matches these patterns.
Matching is done via `fnmatch`.


VALIDATE_TEMPLATES_EXTRA_TEMPLATE_DIRS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use `VALIDATE_TEMPLATES_EXTRA_TEMPLATE_DIRS` to include a number of template
dirs by default directly from the settings file. This can be useful for situations
where TEMPLATE DIRS is dynamically generated or switched in middleware, or when you
have other template dirs for external applications like celery, and you want to
check those as well.

Usage Example
-------------

 ./manage.py validate_templates
