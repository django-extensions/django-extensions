RunScript
=============

:synopsis: Runs a script in the django context.


Introduction
------------

The runscript command lets you run an arbitrary set of python commands within
the django context. It offers the same usability and functionality as running a
set of commands in shell accessed by::

  $ python manage.py shell


Getting Started
---------------

This example assumes you have followed the tutorial for Django 1.8+, and
created a polls app containing a ``Question`` model. We will create a script
that deletes all of the questions from the database.

To get started create a scripts directory in your project root, next to
manage.py::

  $ mkdir scripts
  $ touch scripts/__init__.py

Note: The *__init__.py* file is necessary so that the folder is picked up as a
python package.

Next, create a python file with the name of the script you want to run within
the scripts directory::

  $ touch scripts/delete_all_questions.py

This file must implement a *run()* function. This is what gets called when you
run the script. You can import any models or other parts of your django project
to use in these scripts.

For example::

  # scripts/delete_all_questions.py

  from polls.models import Question

  def run():
      # Fetch all questions
      questions = Question.objects.all()
      # Delete questions
      questions.delete()

Note: You can put a script inside a *scripts* folder in any of your apps too.

Usage
-----

To run any script you use the command *runscript* with the name of the script
that you want to run.

For example::

  $ python manage.py runscript delete_all_questions

Note: The command first checks for scripts in your apps i.e. *app_name/scripts*
folder and runs them before checking for and running scripts in the
*project_root/scripts* folder. You can have multiple scripts with the same name
and they will all be run sequentially.

Passing arguments
-----------------

You can pass arguments from the command line to your script by passing a space separated
list of values with ``--script-args``. For example::

  $ python manage.py runscript delete_all_questions --script-args staleonly

The list of argument values gets passed as arguments to your *run()* function. For
example::

  # scripts/delete_all_questions.py
  from datetime import timedelta

  from django.utils import timezone

  from polls.models import Question

  def run(*args):
      # Get all questions
      questions = Question.objects.all()
      if 'staleonly' in args:
          # Only get questions more than 100 days old
          questions = questions.filter(pub_date__lt=timezone.now() - timedelta(days=100))
      # Delete questions
      questions.delete()

Setting execution directory
---------------------------

You can set scripts execution directory using ``--chdir`` option or ``settings.RUNSCRIPT_CHDIR``.
You can also set scripts execution directory policy using ``--dir-policy`` option or ``settings.RUNSCRIPT_CHDIR_POLICY``.

It can be one of the following:

* **none** - start all scripts in current directory.
* **each** - start all scripts in their directories.
* **root** - start all scripts in ``BASE_DIR`` directory.

Assume this simplified directory structure::

    django_project_dir/
    ├-first_app/
    │ └-scripts/
    │   ├-first_script.py
    ├-second_app/
    │ └-scripts/
    │   ├-second_script.py
    ├-manage.py
    ├-other_folder/
    │ └-some_file.py

Assume you are in ``other_folder`` directory.
You can set execution directory for both scripts using this command::

  $ python ../manage.py runscript first_script second_script --chdir /django_project_dir/second_app
  # scripts will be executed from second_app directory

You can run both scripts with ``NONE`` policy using this command::

  $ python ../manage.py runscript first_script second_script --dir-policy none
    # scripts will be executed from other_folder directory

You can run both scripts with ``EACH`` policy using this command::

  $ python ../manage.py runscript first_script second_script --dir-policy each
    # first_script will be executed from first_app and second script will be executed from second_app

You can run both scripts with ``ROOT`` policy using this command::

  $ python ../manage.py runscript first_script second_script --dir-policy root
    # scripts will be executed from django_project_dir directory

Debugging
---------

If an exception occurs you will not get a traceback by default.  To get a traceback specify ``--traceback``. For example::

  $ python manage.py runscript delete_all_questions --traceback
