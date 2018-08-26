generate_password
=================

:synopsis: Generates a new password that can be used for a user password.

Introduction
-------------

This is a handy command to generate a new password which can be used for a user password. This uses Django core's default password generator ``django.contrib.auth.base_user.BaseUserManager.make_random_password()`` to generate a password.

You can specify the length of password with the option ``--length``. If you don't specify ``--length``, the default value of ``make_random_password()`` is applied.

Usage
-------------

Run ::

    $ python manage.py generate_password  [--length=<length>]
