list_model_info
===============

:synopsis: Lists out all the fields and methods for models in installed apps.

Introduction
------------

When working with large projects or when returning to a code base after some time away, it can be challenging to remember all of the
fields and methods associated with your models. This command makes it easy to see:

 * what fields are available
 * how they are refered to in queries
 * each field's class
 * each field's representation in the database
 * what methods are available
 * method signatures


Commandline arguments
^^^^^^^^^^^^^^^^^^^^^
You can configure the output in a number of ways.

::

  # Show each field's class
  $ ./manage.py list_model_info --field-class

::

  # Show each field's database type representation
  $ ./manage.py list_model_info --db-type


.. tip::
   Only the field class or the db type can be displayed in the output. If you have selected both options, the field type will be displayed.
   This applies to any combinations of the associated commandline arguments and settings.


::

  # Show each method's signature
  $ ./manage.py list_model_info --signature

::

  # Show all model methods, including private methods and django's default methods
  $ ./manage.py list_model_info --all-methods

::

  # Output only information for a single model, specifying the app and model using dot notation
  $ ./manage.py list_model_info --model users.User


You can combine arguments. for instance, to list all methods and show the method signatures for the User model within the users app::

  $ ./manage.py list_model_info --all --signature --model users.User



Settings Configuration
^^^^^^^^^^^^^^^^^^^^^^

You can specify default values in your settings.py to simplify running this command.


.. tip::
   Commandline arguments override the following settings, allowing you to change options on the fly.


To show each field's class::

    MODEL_INFO_FIELD_CLASS = True

To show each field's database type representation::

    MODEL_INFO_DB_TYPE = True

To show each method's signature::

    MODEL_INFO_SIGNATURE = True

To show all model methods, including private methods and django's default methods::

    MODEL_INFO_ALL_METHODS = True

To output only information for a single model, specify the app and model using dot notation::

    MODEL_INFO_MODEL = 'users.User'
