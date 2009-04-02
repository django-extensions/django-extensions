Jobs scheduling
===============

:synopsis: Documentation on creating/using jobs in Django-extensions


JobsScheduling
--------------


This page is very much; Work in Progress
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Creating jobs works much like management commands work in Django.
Use create_jobs to make a 'jobs' directory inside of an application.
After that create one python file per job.

Some simple examples are provided by the django_extensions.jobs package.

A job is a python script with a mandatory Job class which extends from
HourlyJob, DailyJob, WeeklyJob or MonthlyJob. It has one method that must be
implemented called 'execute', which is called when the job is ran.

The following commands are related to jobs:

* create_jobs, created the directory structure for jobs
* runjob, runs a single job
* runjobs, run all hourly/daily/weekly/monthly jobs

Use "runjob(s) -l" to list all jobs recognized.

Jobs do not run automatically !

You must either run a job by hand, with which you can specify the exact time on
which the command is ran, or put something like the following lines in your
crontab file.

@hourly /path/to/my/project/manage.py runjobs hourly

@daily /path/to/my/project/manage.py runjobs daily

@weekly /path/to/my/project/manage.py runjobs weekly

@monthly /path/to/my/project/manage.py runjobs monthly