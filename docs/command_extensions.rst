Current Command Extensions
==========================

:synopsis: Current Command Extensions

* :doc:`shell_plus` - An enhanced version of the Django shell.  It will autoload
  all your models making it easy to work with the ORM right away.

* *admin_generator* - Generate automatic Django Admin classes by providing an app name. Outputs
  source code at STDOUT.
  
* *clean_pyc* - Remove all python bytecode compiled files from the project

* `create_app`_ - Creates an application directory structure for the specified
  app name.  This command allows you to specify the --template option where you
  can indicate a template directory structure to use as your default.

* *create_command* - Creates a command extension directory structure within the
  specified application.  This makes it easy to get started with adding a
  command extension to your application.

* *create_template_tags* - Creates a template tag directory structure within the
  specified application.

* *create_jobs* - Creates a Django jobs command directory structure for the
  given app name in the current directory.  This is part of the impressive jobs
  system.

* *clear_cache* - Clear django cache, useful when testing or deploying.

* *compile_pyc* - Compile python bytecode files for the project.

* *describe_form* - Used to display a form definition for a model. Copy and
  paste the contents into your forms.py and you're ready to go.

* :doc:`delete_squashed_migrations` - Deletes leftover migrations after
  squashing and converts squashed migration to a normal one.

* :doc:`dumpscript <dumpscript>` - Generates a Python script that will
  repopulate the database using objects. The advantage of this approach is that
  it is easy to understand, and more flexible than directly populating the
  database, or using XML.

* `export_emails`_ - export the email addresses for your
  users in one of many formats.  Currently supports Address, Google, Outlook,
  LinkedIn, and VCard formats.
  
* *find_template* - Finds the location of the given template by resolving its path

* *generate_secret_key* - Creates a new secret key that you can put in your
  settings.py module.

* `graph_models`_ - Creates a GraphViz_ dot file.  You need
  to send this output to a file yourself.  Great for graphing your models. Pass
  multiple application names to combine all the models into a single dot file.

* *mail_debug* - Starts a mail server which echos out the contents of the email
  instead of sending it.
  
* *notes* - Show all annotations like TODO, FIXME, BUG, HACK, WARNING, NOTE or XXX in your py and HTML files.

* *passwd* - Makes it easy to reset a user's password.

* *pipchecker* - Scan pip requirement file(s)s for out-of-date packages. Similar to
  ``pip list -o`` which used installed packages (in virtualenv) instead of requirements file(s).

* `print_settings`_ - Similar to ``diffsettings`` but shows *selected*
  active Django settings or *all* if no args passed.

* *print_user_for_session* - Print the user information for the provided
  session key. this is very helpful when trying to track down the person who
  experienced a site crash.
  It seems this works only if setting ``SESSION_ENGINE`` is
  ``'django.contrib.sessions.backends.db'`` (default value).

* *drop_test_database* - Drops the test database. Usefull when running Django
  test via some automated system (BuildBot, Jenkins, etc) and making sure that
  the test database is always dropped at the end.

* *reset_db* - Resets a database (currently sqlite3, mysql, postgres). Uses "DROP DATABASE" and "CREATE DATABASE".

* *runjob* - Run a single maintenance job.  Part of the jobs system.

* *runjobs* - Runs scheduled maintenance jobs. Specify hourly, daily, weekly,
  monthly.  Part of the jobs system.

* :doc:`runprofileserver <runprofileserver>` - Starts *runserver* with hotshot/profiling tools enabled.
  I haven't had a chance to check this one out, but it looks really cool.

* `runscript`_ - Runs a script in the django context.

* `runserver_plus`_ - The standard runserver stuff but with
  the Werkzeug debugger baked in. Requires Werkzeug_. This one kicks ass.

* *set_fake_emails* - Give all users a new email based on their account data ("%(username)s@example.com" by default). Possible parameters are: username, first_name, last_name. *DEBUG only*

* *set_fake_passwords* -  Sets all user passwords to a common value (*password* by default). *DEBUG only*.

* *show_template_tags* - Displays template tags and filters available in the current project.

* *show_urls* - Displays the url routes that are defined in your project. Very
  crude at this point.

* :doc:`sqldiff` - Prints the (approximated) difference between an app's models and
  what is in the database.  This is very nice, but also very experimental at
  the moment.  It can not catch everything but it's a great sanity check.

* :doc:`sqlcreate` - Generates the SQL to create your database for you, as specified
  in settings.py.

* :doc:`sqldsn` - Reads the Django settings and extracts the parameters needed
  to connect to databases using other programs.

* `sync_s3`_ - Copies files found in settings.MEDIA_ROOT to S3.
  Optionally can also gzip CSS and Javascript files and set the
  Content-Encoding header, and also set a far future expires header for browser
  caching.
  
* *syncdata* - Makes the current database have the same data as the fixture(s), no more, no less.

* *unreferenced_files* - Prints a list of all files in MEDIA_ROOT that are not referenced in the database.

* *update_permissions* - Reloads permissions for specified apps, or all apps if no args are specified.

* *validate_templates* - Validate templates on syntax and compile errors.

* *set_default_site* - Set parameters of the default `django.contrib.sites` Site using `name` and `domain` or `system-fqdn`.


.. _`create_app`: create_app.html
.. _`export_emails`: export_emails.html
.. _`graph_models`: graph_models.html
.. _`print_settings`: print_settings.html
.. _`runscript`: runscript.html
.. _`runserver_plus`: runserver_plus.html
.. _`sync_s3`: sync_s3.html
.. _GraphViz: http://www.graphviz.org/
.. _Werkzeug: http://werkzeug.pocoo.org/
