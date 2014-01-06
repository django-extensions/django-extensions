Jobs scheduling
===============

:synopsis: Documentation on creating/using jobs in Django-extensions


JobsScheduling
--------------


This page is very much a  Work In Progress
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Creating jobs works much like management commands work in Django.
Use create_jobs to make a 'jobs' directory inside of an application.
After that create one python file per job.

Some simple examples are provided by the django_extensions.jobs package.

A job is a python script with a mandatory Job class which extends from
HourlyJob, DailyJob, WeeklyJob or MonthlyJob. It has one method that must be
implemented called 'execute', which is called when the job is run.

The following commands are related to jobs:

* create_jobs, create the directory structure for jobs
* runjob, run a single job
* runjobs, run all hourly/daily/weekly/monthly jobs

Use "runjob(s) -l" to list all jobs recognized.

Jobs do not run automatically !

You must either run a job manually specifying  the exact time on
which the command is to be run, or use crontab: ::

@hourly /path/to/my/project/manage.py runjobs hourly

::

@daily /path/to/my/project/manage.py runjobs daily

::

@weekly /path/to/my/project/manage.py runjobs weekly

::

@monthly /path/to/my/project/manage.py runjobs monthly
