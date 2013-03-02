validate_templates
==================

:synopsis: Checks templates on syntax or compile errors.

Options
-------

verbosity
~~~~~~~~~
A higher verbosity level will print out all the files that are processed not just the onces that contain errors.

break
~~~~~
Do not continue scanning other templates after the first failure.

includes
~~~~~~~~
Use -i (can be used multiple times) to add directories to the TEMPLATE_DIRS.

Settings
--------

VALIDATE_TEMPLATES_EXTRA_TEMPLATE_DIRS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use `VALIDATE_TEMPLATES_EXTRA_TEMPLATE_DIRS` to include a number of template dirs per default directly from the settings file.
This can be usefull for situations where TEMPLATE_DIRS is dynamically generated or switched in middleware or you have other template
dirs for external applications like celery you want to check as well.

Usage Example
-------------

 ./manage.py validate_templates

