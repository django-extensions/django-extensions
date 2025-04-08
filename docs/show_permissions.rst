Show Permissions
================

:synopsis: Show all permissions for Django models

Introduction
------------

The ``show_permissions`` management command lists all permissions for the models in your Django project.
By default, it excludes built-in Django apps such as ``admin``, ``auth``, ``contenttypes``, and ``sessions``.

This command is useful to quickly inspect the permissions assigned to models, especially when customizing permission logic or managing role-based access.

Basic Usage
-----------

.. code-block:: bash

    python manage.py show_permissions

This will output the list of permissions for models in all installed apps **excluding** built-in Django apps.

Examples
--------

Show permissions for specific apps and models:

.. code-block:: bash

    python manage.py show_permissions blog
    python manage.py show_permissions blog.Post

Show permissions including built-in Django apps:

.. code-block:: bash

    python manage.py show_permissions --all

Show permissions for only a specific app using the `--app-label` option:

.. code-block:: bash

    python manage.py show_permissions --app-label blog

Options
-------

* ``--all``
  Include permissions for Django’s built-in apps (``admin``, ``auth``, ``contenttypes``, ``sessions``).

* ``--app-label <label>``
  Only show permissions for the specified app label.

* ``app_label.model`` (positional argument)
  Restrict output to specific model(s), optionally prefixed by app label.

* ``--verbosity {0,1,2,3}``
  Set verbosity level (default: 1).

* ``--settings <path>``
  Set a specific Django settings module.

* ``--pythonpath <path>``
  Add a path to the Python module search path.

* ``--traceback``
  Show full traceback on error.

* ``--no-color`` / ``--force-color``
  Toggle colored output.

* ``--skip-checks``
  Skip Django’s system checks.

Conclusion
----------

The ``show_permissions`` command is a handy tool for developers and administrators to audit or debug permission settings within their Django project.
