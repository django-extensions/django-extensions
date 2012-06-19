.. django-extensions documentation master file, created by
   sphinx-quickstart on Wed Apr  1 20:39:40 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-extensions's documentation!
=============================================

Django Extensions is a collection of custom extensions for the Django Framework.

These include management commands, additional database field, admin extensions and
much more.

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

Contents
========

.. toctree::
   :maxdepth: 3

   admin_extensions
   command_extension_ideas
   command_extensions
   shell_plus
   create_app
   dumpscript
   export_emails
   field_extensions
   graph_models
   installation_instructions
   jobs_scheduling
   model_extensions
   namespace_proposal
   runprofileserver
   runserver_plus
   sync_media_s3
   sqldiff
   sqlcreate
   validate_templates


Indices and tables
==================

* :ref:`search`

__ http://ericholscher.com/blog/2008/sep/12/screencast-django-command-extensions/
