===================
 Django Extensions
===================

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://raw.githubusercontent.com/django-extensions/django-extensions/master/LICENSE

.. image:: https://secure.travis-ci.org/django-extensions/django-extensions.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/django-extensions/django-extensions

.. image:: https://pypip.in/v/django-extensions/badge.png
    :target: https://pypi.python.org/pypi/django-extensions/
    :alt: Latest PyPI version

.. image:: https://pypip.in/d/django-extensions/badge.png
    :target: https://pypi.python.org/pypi/django-extensions/
    :alt: Number of PyPI downloads

.. image:: https://coveralls.io/repos/django-extensions/django-extensions/badge.png?branch=master
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

- http://django-extensions.readthedocs.org

Or you can look at the docs/ directory in the repository.


Donations
=========

Django Extensions is free and always will be. From time to time people and company's have expressed the willingness
to donation to the project to help foster it's development. We prefer people to become active in the project and support
us by sending pull requests but will humbly accept donations as well.

Donations will be used to make Django Extensions better by allowing developers to spend more time on it, paying to go
to conferences, paying for infrastructure, etc. If for some reason we would receive more donations then needed they will
go towards the Django and Python foundations.

We have setup a couple of ways you can donate towards Django Extensions using the buttons below:

 - Bountysource
 - Gratipay (formerly Gittip)
 - Flattr
 - PayPal
 - Patreon `here <https://patreon.com/trbs>`_

.. image:: https://www.bountysource.com/badge/team?team_id=7470&style=bounties_posted
    :target: https://www.bountysource.com/teams/django-extensions/bounties?utm_source=django-extensions&utm_medium=shield&utm_campaign=bounties_posted
    :alt: BountySource

.. image:: https://img.shields.io/flattr/donate.png
    :target: https://flattr.com/submit/auto?user_id=Trbs&url=https%3A%2F%2Fgithub.com%2Fdjango-extensions%2Fdjango-extensions
    :alt: Flattr this

.. image:: https://img.shields.io/paypal/donate.png
    :target: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=P57EJJ9QYL232
    :alt: PayPal Donations

.. image:: https://img.shields.io/gratipay/trbs.png
    :target: https://gratipay.com/trbs/
    :alt: Gifts received


__ http://ericholscher.com/blog/2008/sep/12/screencast-django-command-extensions/
__ http://vimeo.com/1720508
__ https://godjango.com/39-be-more-productive-with-django_extensions/
