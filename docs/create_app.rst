create_app
==========

:synopsis: Creates an application directory structure for the specified application name.

This command allows you to specify the --template option where you can indicate
a template directory structure to use as your default.

The --diagram option generates the models.py and admin.py from a .dia file.


Example Usage
-------------

All examples assume your current directory is the project directory and
settings.py is under it.

::

  # Get command help
  ./manage.py create_app --help

::

  # Generate models.py and admin.py from [APP_NAME].dia file. This file should
  # be placed in the settings.py directory.
  ./manage.py create_app -d APP_NAME


Example generated from sample.dia
---------------------------------

::

  ./manage.py create_app --diagram=sample.dia webdata

-d switch or --diagram option use dia2django_ to generate models.py and is
better documented in `django wiki`_.

.. _dia2django: https://svn.devnull.li/main/pythonware/dia2django/trunk/doc/
.. _`django wiki`: http://code.djangoproject.com/wiki/Dia2Django
