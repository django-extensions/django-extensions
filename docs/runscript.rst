RunScript
=============

:synopsis: Runs a script in the django context.


Introduction
------------

The runscript command lets you run any arbritrary set of python commands within
the django context. It offers the same usability and functionality as running a
set of command in shell accessed by::

  $ python manage.py shell


Getting Started
---------------

To get started create a scripts directory in your project root, next to
manage.py::

  $ mkdir scripts
  $ touch scripts/__init__.py

Note: The *__init__.py* file is necessary so that the folder is picked up as a
python package.

Next, create a python file with the name of the script you want to run within
the scripts directory::

  $ touch scripts/delete_all_polls.py

This file must implement a *run()* function. This is what gets called when you
run the script. You can import any models or other parts of your django project
to use in these scripts.

For example::

  # scripts/delete_all_polls.py

  from Polls.models import Poll

  def run():
      # Get all polls
      all_polls = Poll.objects.all()
      # Delete polls
      all_polls.delete()

Note: You can put a script inside a *scripts* folder in any of your apps too.

Using
-----

To run any script you use the command *runscript* with the name of the script
that you want to run.

For example::

  $ python manage.py runscript delete_all_polls

Note: The command first checks for scripts in your apps i.e. *app_name/scripts*
folder and runs them before checking for and running scripts in the
*project_root/scripts* folder. You can have multiple scripts with the same name
and they will all be run sequentially.
