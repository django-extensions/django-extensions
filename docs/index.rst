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

The easiest way to figure out what Django Extensions are all about is to watch the `excellent screencast by Eric Holscher`__ (`Direct Vimeo link`__). In a couple minutes Eric walks you through a half a dozen command extensions.

Getting it
==========

You can get Django Extensions by using pip::

 $ pip install django-extensions

If you want to install it from source, grab the git repository and run setup.py::

 $ git clone git://github.com/django-extensions/django-extensions.git
 $ cd django-extensions
 $ python setup.py install

Then you will need to add the *django_extensions* application to the
``INSTALLED_APPS`` setting of your Django project *settings.py* file.

For more detailed instructions check out our :doc:`installation_instructions`. Enjoy.

Compatibility with versions of Python and Django
=================================================

We follow the Django guidelines for supported Python and Django versions. See more at `Django Supported Versions <https://docs.djangoproject.com/en/dev/internals/release-process/#supported-versions>`_

This might mean the django-extensions may work with older or unsupported versions but we do not guarantee it and most likely will not fix bugs related to incompatibilities with older versions.

Contents
========

.. toctree::
   :maxdepth: 2

   installation_instructions
   admin_extensions
   command_extensions
   command_signals
   debugger_tags
   field_extensions
   jobs_scheduling
   model_extensions
   permissions
   utilities
   validators


Indices and tables
==================

* :ref:`search`

__ https://ericholscher.com/blog/2008/sep/12/screencast-django-command-extensions/
__ https://vimeo.com/1720508
