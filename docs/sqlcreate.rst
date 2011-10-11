sqlcreate
==========

:synopsis: Helps you setup your database(s) more easily


Introduction
-------------

Stop creating databases by hand.  Your settings.py file already contains the correct
information, so DRY.

Usage
-------------

  $ python manage.py sqlcreate [--router=<routername>] | <my_database_shell_command>
  
It will spit out SQL which you can review (if you want) but ultimately you want to
pipe it into the database shell command of your choice.

If there was a good way to ensure that the user in the database settings had the
proper permissions, we could submit the commands straight to the database.
But due to the nature of this portion of the project setup, that will never happen.
