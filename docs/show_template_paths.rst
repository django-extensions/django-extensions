Show Template Paths
===================

:synopsis: Show all file system paths searched by the template loader.

Introduction
------------

The ``show_template_paths`` management command lists all file system paths that are searched by the template loader when loading a template, in the order they are searched in.

Usage
-----

.. code-block:: bash

    python manage.py show_template_paths

This will output the list of absolute file system paths searched by the template loader.
