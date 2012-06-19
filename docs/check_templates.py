check_templates
===============

:synopsis: Checks templates on syntax or compile errors.

Options
=======

verbosity; A higher verbosity level will print out all the files that are processed not just the onces that contain errors.

break: Do not continue scanning other templates after the first failure.

includes: Use -i (can be used multiple times) to add directories to the TEMPLATE_DIRS.

How
===

 ./manage.py check_templates

