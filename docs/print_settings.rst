print_settings
==============

:synopsis: Django management command similar to ``diffsettings`` but shows *selected* active Django settings or *all* if no args passed.


Introduction
------------

Django comes with a ``diffsettings`` command that shows how your project's
settings differ from the Django defaults.  Sometimes it is useful to just see
the settings that are in effect for your project. This is particularly
true if you have a more complex system for settings than just a single
:file:`settings.py` file. For example, you might have settings files that
import other settings file, such as dev, test, and production settings files
that source a base settings file.

This command also supports dumping the data in a few different formats.

More Info
---------------

The simplest way to run it is with no arguments::

    $ python manage.py print_settings

Some variations::

    $ python manage.py print_settings --format=json
    $ python manage.py print_settings --format=yaml    # Requires PyYAML
    $ python manage.py print_settings --format=pprint
    $ python manage.py print_settings --format=text
    $ python manage.py print_settings --format=value

Show just selected settings::

    $ python manage.py print_settings DEBUG INSTALLED_APPS
    $ python manage.py print_settings DEBUG INSTALLED_APPS --format=pprint
    $ python manage.py print_settings INSTALLED_APPS --format=value

It is also possible to use shell-style wildcards::

    $ python manage.py print_settings TIME*
    $ python manage.py print_settings *_DIRS STATIC*
    $ python manage.py print_settings INSTALLED_????

By default, secrets are masked. To show secrets, use the --show-secrets flag::

    $ python manage.py print_settings --show-secrets

Yielding an error when a settings does not exist::

    $ ./manage.py print_settings -f INSTALLED_APPZ
    CommandError: INSTALLED_APPZ not found in settings.

For more info, take a look at the built-in help::

    $ python manage.py print_settings --help
    usage: manage.py print_settings [-h] [-f] [--format FORMAT] [--indent INDENT] [--version] [-v {0,1,2,3}]
                                    [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                                    [--force-color] [--skip-checks]
                                    [setting [setting ...]]

    Print the active Django settings.

    positional arguments:
      setting               Specifies setting to be printed.

    optional arguments:
      -h, --help            show this help message and exit
      -f, --fail            Fail if invalid setting name is given.
      --format FORMAT       Specifies output format.
      --indent INDENT       Specifies indent level for JSON and YAML
      --version             show program's version number and exit
      -v {0,1,2,3}, --verbosity {0,1,2,3}
                            Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
      --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided,
                            the DJANGO_SETTINGS_MODULE environment variable will be used.
      --pythonpath PYTHONPATH
                            A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
      --traceback           Raise on CommandError exceptions
      --no-color            Don't colorize the command output.
      --force-color         Force colorization of the command output.
      --skip-checks         Skip system checks.
      --show-secrets        Show secrets in the output without masking.
