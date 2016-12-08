.. django-extensions documentation master file, created by
   sphinx-quickstart on Wed Apr  1 20:39:40 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the django-extensions documentation!
===============================================

Django Extensions is a collection of custom extensions for the Django Framework.

These include management commands, additional database fields, admin extensions and
much more.

`这篇文档当然还有中文版 <https://django-extensions-zh.readthedocs.io/zh_CN/latest/>`_

Getting Started
===============

The easiest way to figure out what Django Extensions are all about is to watch the `excellent screencast by Eric Holscher`__. In a couple minutes Eric walks you through a half a dozen command extensions.

Getting it
==========

You can get Django Extensions by using pip or easy_install::

 $ pip install django-extensions
 or
 $ easy_install django-extensions

If you want to install it from source, grab the git repository and run setup.py::

 $ git clone git://github.com/django-extensions/django-extensions.git
 $ cd django-extensions
 $ python setup.py install

For more detailed instructions check out our :doc:`installation_instructions`. Enjoy.

Compatibility with versions of Python and Django
=================================================

We follow the Django guidelines for supported Python and Django versions. See more at `Django Supported Versions <https://docs.djangoproject.com/en/dev/internals/release-process/#supported-versions>`_

This might mean the django-extensions may work with older or unsupported versions but we do not guarantee it and most likely will not fix bugs related to incompatibilities with older versions.

At this time we test on and thrive to support valid combinations of Python 2.7, 3.4, 3.5, pypy and pypy3 with Django versions 1.8 and 1.9.

Contents
========

.. toctree::
   :maxdepth: 3

   installation_instructions
   command_extensions
   command_extension_ideas
   command_signals
   admin_extensions
   shell_plus
   create_app
   delete_squashed_migrations
   dumpscript
   runscript
   export_emails
   field_extensions
   graph_models
   jobs_scheduling
   model_extensions
   namespace_proposal
   print_settings
   runprofileserver
   runserver_plus
   sync_s3
   sqldiff
   sqlcreate
   sqldsn
   validate_templates


Indices and tables
==================

* :ref:`search`

__ http://ericholscher.com/blog/2008/sep/12/screencast-django-command-extensions/
