create_template_tags
====================

:synopsis: Creates a template tag directory structure within the specified application.

Usage
-----

Create templatetags directory for *foobar* app::

   $ python manage.py create_template_tags foobar

it will create directory structure::

   foobar/
      __init__.py
      models.py
      templatetags/
         __init__.py
         foobar_tags.py

you can pass custom tags filename by providing ``--name`` argument::

   $ python manage.py create_template_tags foobar --name custom_tags
