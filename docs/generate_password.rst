generate_password
=================

:synopsis: Generates a new password that can be used for a user password.

Introduction
-------------

Generate password is a handy command to generate a new password which can be used for a user password.
This uses Python's secret module `Recipes and best practices`_ to generate a password.

There are two options.

You can specify the length of password with the option ``--length``. If you don't specify ``--length``, a default value of 16 is applied.
Using ``--complex`` will add punctuation to the aphabet of characters which the password will be generated from.


Usage
-----

Run ::

    $ python manage.py generate_password [--length=<length>] [--complex]


.. _Recipes and best practices: https://docs.python.org/3/library/secrets.html#recipes-and-best-practices
