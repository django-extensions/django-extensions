===================
 Django Extensions
===================

.. image:: https://secure.travis-ci.org/django-extensions/django-extensions.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/django-extensions/django-extensions

Django Extensions is a collection of custom extensions for the Django Framework.


Getting Started
===============

The easiest way to figure out what Django Extensions are all about is to watch the `excellent screencast by Eric Holscher`__. In a couple minutes Eric walks you through a half a dozen command extensions.


Requirements
============

Django Extensions requires Django 1.4 or later.


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

To enable `django_extensions` in your project you need to add it to `INSTALLED_APPS` in your projects `settings.py` file::

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


Getting Involved
================

Open Source projects can always use more help. Fixing a problem, documenting a feature, adding translation in your language. If you have some time to spare and like to help us, here are the places to do so:

- GitHub: https://github.com/django-extensions/django-extensions
- Mailing list: http://groups.google.com/group/django-extensions
- Translations: https://www.transifex.net/projects/p/django-extensions/


Documentation
=============

You can view documentation online at:

- http://django-extensions.readthedocs.org

Or you can look at the docs/ directory in the repository.


__ http://ericholscher.com/blog/2008/sep/12/screencast-django-command-extensions/
