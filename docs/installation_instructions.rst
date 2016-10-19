Installation instructions
=========================

:synopsis: Installing django-extensions


Installation
------------

For usage
^^^^^^^^^

You can use pip to install django-extensions for usage::

  $ pip install django-extensions

For development
^^^^^^^^^^^^^^^

Django-extensions is hosted on github::

 https://github.com/django-extensions/django-extensions

Source code can be accessed by performing a Git clone.

Tracking the development version of *django command extensions* should be
pretty stable and will keep you up-to-date with the latests fixes.

  $ pip install -e git+https://github.com/django-extensions/django-extensions.git#egg=django-extensions
  
You find the sources in src/django-extensions now.

You can verify that the application is available on your PYTHONPATH by opening a python interpreter and entering the following commands:

::

  >>> import django_extensions
  >>> django_extensions.VERSION
  (0, 8)

Keep in mind that the current code in the git repository may be different from the
packaged release. It may contain bugs and backwards-incompatible changes but most
likely also new goodies to play with.


Configuration
^^^^^^^^^^^^^

You will need to add the *django_extensions* application to the INSTALLED_APPS
setting of your Django project *settings.py* file.::

  INSTALLED_APPS = (
      ...
      'django_extensions',
  )

This will make sure that Django finds the additional management commands
provided by *django-extensions*.

The next time you invoke *./manage.py help* you should be able to see all the
newly available commands.

Some commands or options require additional applications or python libraries,
for example:

  * 'export_emails' will require the *python vobject* module to create vcard
    files.
  * 'graph_models' requires *pygraphviz* to render directly to image file.

If the given application or python library is not installed on your system (or
not in the python path) the executed command will raise an exception and inform
you of the missing dependency.

