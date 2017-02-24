===================
 Django Extensions
===================

.. image:: https://img.shields.io/pypi/l/django-extensions.svg
   :target: https://raw.githubusercontent.com/django-extensions/django-extensions/master/LICENSE

.. image:: https://secure.travis-ci.org/django-extensions/django-extensions.svg?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/django-extensions/django-extensions

.. image:: https://img.shields.io/pypi/v/django-extensions.svg
    :target: https://pypi.python.org/pypi/django-extensions/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/wheel/django-extensions.svg
    :target: https://pypi.python.org/pypi/django-extensions/
    :alt: Supports Wheel format

.. image:: https://coveralls.io/repos/django-extensions/django-extensions/badge.svg?branch=master
   :target: https://coveralls.io/r/django-extensions/django-extensions?branch=master
   :alt: Coverage

Django Extensions is a collection of custom extensions for the Django Framework.


Getting Started
===============

The easiest way to figure out what Django Extensions are all about is to watch the
`excellent screencast by Eric Holscher`__ (`watch the video on vimeo`__). In a couple
minutes Eric walks you through a half a dozen command extensions. There is also a
`short screencast on GoDjango`__ to help show you even more.


Requirements
============

Django Extensions requires Django 1.8 or later.


Getting It
==========

You can get Django Extensions by using pip or easy_install::

    $ pip install django-extensions
    or
    $ easy_install django-extensions

If you want to install it from source, grab the git repository from GitHub and run setup.py::

    $ git clone git://github.com/django-extensions/django-extensions.git
    $ cd django-extensions
    $ python setup.py install


Installing It
=============

To enable `django_extensions` in your project you need to add it to `INSTALLED_APPS` in your projects
`settings.py` file::

    INSTALLED_APPS = (
        ...
        'django_extensions',
        ...
    )


Using It
========

Generate (and view) a graphviz graph of app models::

    $ python manage.py graph_models -a -o myapp_models.png

Produce a tab-separated list of `(url_pattern, view_function, name)` tuples for a project::

    $ python manage.py show_urls

Check templates for rendering errors::

    $ python manage.py validate_templates

Run the enhanced django shell::

    $ python manage.py shell_plus

Run the enhanced django runserver, (requires Werkzeug install)::

    $ python manage.py runserver_plus


Getting Involved
================

Open Source projects can always use more help. Fixing a problem, documenting a feature, adding
translation in your language. If you have some time to spare and like to help us, here are the places to do so:

- GitHub: https://github.com/django-extensions/django-extensions
- Mailing list: http://groups.google.com/group/django-extensions
- Translations: https://www.transifex.net/projects/p/django-extensions/


Documentation
=============

You can view documentation online at:

- https://django-extensions.readthedocs.io

Or you can look at the docs/ directory in the repository.


Support
=======

Django Extensions is free and always will be. It is development and maintained by developers in an Open Source manner.
Any support is welcome. You could help by writing documentation, pull-requests, report issues and/or translations.

Please remember that nobody is payed directly to develop or maintain Django Extensions so we do have to divide our time
between putting food on the table, family, this project and the rest of life :-)


__ http://ericholscher.com/blog/2008/sep/12/screencast-django-command-extensions/
__ http://vimeo.com/1720508
__ https://godjango.com/39-be-more-productive-with-django_extensions/
