shell_plus
==========

:synopsis: Django shell with autoloading of the apps database models and subclasses of user-defined classes.


Interactive Python Shells
-------------------------

There is support for three different types of interactive python shells.

IPython::

  $ ./manage.py shell_plus --ipython


bpython::

  $ ./manage.py shell_plus --bpython


ptpython::

  $ ./manage.py shell_plus --ptpython


Python::

  $ ./manage.py shell_plus --plain

It is possible to directly add command line arguments to the underlying Python shell using `--`::

  $ ./manage.py shell_plus --ipython -- --profile=foo


The default resolution order is: ptpython, bpython, ipython, python.

You can also set the configuration option SHELL_PLUS to explicitly specify which version you want.

::

  # Always use IPython for shell_plus
  SHELL_PLUS = "ipython"


It is also possible to use `IPython Notebook`_, an interactive Python shell which
uses a web browser as its user interface, as an alternative shell::

    $ ./manage.py shell_plus --notebook

In addition to being savable, IPython Notebooks can be updated (while running) to reflect changes in a Django application's code with the menu command `Kernel > Restart`.


Configuration
-------------

Sometimes, models from your own apps and other people's apps have colliding names,
or you may want to completely skip loading an app's models. Here are some examples of how to do that.

Note: These settings are only used inside shell_plus and will not affect your environment.

::

  # Rename the automatic loaded module Messages in the app blog to blog_messages.
  SHELL_PLUS_MODEL_ALIASES = {'blog': {'Messages': 'blog_messages'},}

::

  # Prefix all automatically loaded models in the app blog with myblog.
  SHELL_PLUS_APP_PREFIXES = {'blog': 'myblog',}

::

  # Dont load the 'sites' app, and skip the model 'pictures' in the app 'blog'
  SHELL_PLUS_DONT_LOAD = ['sites', 'blog.pictures']


::

  # Dont load any models
  SHELL_PLUS_DONT_LOAD = ['*']

You can also combine model_aliases and dont_load.
When referencing nested modules, e.g. `somepackage.someapp.models.somemodel`, omit the
package name and the reference to `models`. For example:

::

    SHELL_PLUS_DONT_LOAD = ['someapp.somemodel', ]  # This works
    SHELL_PLUS_DONT_LOAD = ['somepackage.someapp.models.somemodel', ]  # This does NOT work

It is possible to ignore autoloaded modules when using manage.py, like::

  $ ./manage.py shell_plus --dont-load app1 --dont-load app2.module1

Command line parameters and settings in the configuration file are merged, so you can
safely append modules to ignore from the commandline for one-time usage.

Other configuration options include:

::

  # Always use IPython for shell_plus
  SHELL_PLUS = "ipython"


::

  SHELL_PLUS_PRINT_SQL = True

  # Truncate sql queries to this number of characters
  SHELL_PLUS_PRINT_SQL_TRUNCATE = 1000

  # Specify sqlparse configuration options when printing sql queries to the console
  SHELL_PLUS_SQLPARSE_FORMAT_KWARGS = dict(
    reindent_aligned=True,
    truncate_strings=500,
  )

  # Specify Pygments formatter and configuration options when printing sql queries to the console
  import pygments.formatters
  SHELL_PLUS_PYGMENTS_FORMATTER = pygments.formatters.TerminalFormatter
  SHELL_PLUS_PYGMENTS_FORMATTER_KWARGS = {}


::

  # Additional IPython arguments to use
  IPYTHON_ARGUMENTS = []

  IPYTHON_KERNEL_DISPLAY_NAME = "Django Shell-Plus"

  # Additional Notebook arguments to use
  NOTEBOOK_ARGUMENTS = []
  NOTEBOOK_KERNEL_SPEC_NAMES = ["python3", "python"]



Collision resolvers
-------------------
You don't have to worry about inaccessibility of models with conflicting names.

If you have conflicting model names, all conflicts can be resolved automatically.
All models will be available under shell_plus, some of them with intuitive aliases.

This mechanism is highly configurable and you must only set ``SHELL_PLUS_MODEL_IMPORTS_RESOLVER``.
You should set full path to collision resolver class.

All predefined collision resolvers are in ``django_extensions.collision_resolvers`` module. Example::

    SHELL_PLUS_MODEL_IMPORTS_RESOLVER = 'django_extensions.collision_resolvers.FullPathCR'

All collision resolvers searches for models with the same name.

If conflict is detected they decides, which model to choose.
Some of them are creating aliases for all conflicting models.

**Example**

Suppose that we have two apps:

- programming(with models Language and Framework)

- workers(with models Language and Worker)

'workers' app is last in alphabetical order, but suppose that 'programming' app is occurs firstly in ``INSTALLED_APPS``.

Collision resolvers won't change aliases for models Framework and Worker, because their names are unique.
There are several types of collision resolvers:

**LegacyCR**

Default collision resolver. Model from last application in alphabetical order is selected::

    from workers import Language

**InstalledAppsOrderCR**

Collision resolver which selects first model from INSTALLED_APPS.
You can set your own app priorities list subclassing him and overwriting ``APP_PRIORITIES`` field.

This collision resolver will select model from first app on this list.
If both app's are absent on this list, resolver will choose model from first app in alphabetical order::

    from programming import Language

**FullPathCR**

Collision resolver which transform full model name to alias by changing dots to underscores.
He also removes 'models' part of alias, because all models are in models.py files.

Model from last application in alphabetical order is selected::

    from programming import Language (as programming_Language)
    from workers import Language, Language (as workers_Language)

**AppNamePrefixCR**

Collision resolver which transform pair (app name, model_name) to alias ``{app_name}_{model_name}``.
Model from last application in alphabetical order is selected.

Result is different than FullPathCR, when model has app_label other than current app::

    from programming import Language (as programming_Language)
    from workers import Language, Language (as workers_Language)

**AppNameSuffixCR**

Collision resolver which transform pair (app name, model_name) to alias ``{model_name}_{app_name}``

Model from last application in alphabetical order is selected::

    from programming import Language (as Language_programming)
    from workers import Language, Language (as Language_workers)

**AppNamePrefixCustomOrderCR**

Collision resolver which is mixin of AppNamePrefixCR and InstalledAppsOrderCR.

In case of collisions he sets aliases like AppNamePrefixCR, but sets default model using InstalledAppsOrderCR::

    from programming import Language, Language (as programming_Language)
    from workers import Language (as workers_Language)

**AppNameSuffixCustomOrderCR**

Collision resolver which is mixin of AppNameSuffixCR and InstalledAppsOrderCR.

In case of collisions he sets aliases like AppNameSuffixCR, but sets default model using InstalledAppsOrderCR::

    from programming import Language, Language (as Language_programming)
    from workers import Language (as Language_workers)

**FullPathCustomOrderCR**

Collision resolver which is mixin of FullPathCR and InstalledAppsOrderCR.

In case of collisions he sets aliases like FullPathCR, but sets default model using InstalledAppsOrderCR::

    from programming import Language, Language (as programming_Language)
    from workers import Language (as workers_Language)

**AppLabelPrefixCR**

Collision resolver which transform pair (app_label, model_name) to alias ``{app_label}_{model_name}``

This is very similar to ``AppNamePrefixCR`` but this may generate shorter names in case of apps nested
into several namespace (like Django's auth app)::

    # with AppNamePrefixCR
    from django.contrib.auth.models import Group (as django_contrib_auth_Group)

    # with AppLabelPrefixCR
    from django.contrib.auth.models import Group (as auth_Group)

**AppLabelSuffixCR**

Collision resolver which transform pair (app_label, model_name) to alias ``{model_name}_{app_label}``

Similar idea as the above, but based on ``AppNameSuffixCR``::

    # with AppNamePrefixCR
    from django.contrib.auth.models import Group (as Group_django_contrib_auth)

    # with AppLabelSuffixCR
    from django.contrib.auth.models import Group (as Group_auth)


Writing your custom collision resolver
--------------------------------------

You can customize models import behaviour by subclassing one of the abstract collision resolvers:


**PathBasedCR**

Abstract resolver which transforms full model name into alias.
To use him you need to overwrite transform_import function
which should have one parameter.

It will be full model name. It should return valid alias as str instance.

**AppNameCR**

Abstract collision resolver which transform pair (app name, model_name) to alias by changing dots to underscores.

You must define ``MODIFICATION_STRING`` which should be string to format with two keyword arguments:
app_name and model_name. For example: ``{app_name}_{model_name}``.

Model from last application in alphabetical order is selected.

You can mix PathBasedCR or AppNameCR with InstalledAppsOrderCR, but InstalledAppsOrderCR should be second base class.

**BaseCR**

Abstract base collision resolver. All collision resolvers needs to inherit from this class.

To write custom collision resolver you need to overwrite resolve_collisions function.
It receives ``Dict[str, List[str]]`` where key is model name and values are full model names
(full model name means: module + model_name).

You should return ``Dict[str, str]``, where key is model name and value is full model name.

Import Subclasses
-------------------
If you want to load automatically all project subclasses of some base class,
you can achieve this by setting ``SHELL_PLUS_SUBCLASSES_IMPORT`` option.

It must be list of either classes or strings containing paths to this classes.

For example if you want to load all your custom managers than you should provide::

    from django.db.models import Manager
    SHELL_PLUS_SUBCLASSES_IMPORT = [Manager]

Than shell_plus will load all your custom managers::

    # Shell Plus Subclasses Imports
    from utils.managers import AbstractManager
    from myapp.managers import MyCustomManager
    from somewhere.else import MyOtherManager
    # django.db.models.Manager is not loaded because only project classes are.

By default all subclasses of your base class from all projects module will be loaded.

You can exclude some modules and all their submodules by passing ``SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST`` option::

    SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST = ['utils', 'somewhere.else']

Elements of this list must be strings containing full modules paths.
If these modules are excluded only ``MyCustomManager`` from ``myapp.managers`` will be loaded.

If you are using ``SHELL_PLUS_SUBCLASSES_IMPORT`` shell_plus loads all project modules for finding subclasses.

Sometimes it can lead to some errors(for example when we have old unused module which contains syntax errors).

Excluding these modules can help avoid shell_plus crashes in some situations.
It is recommended to exclude all ``setup.py`` files.

IPython Notebook
----------------
There are two settings that you can use to pass your custom options to the IPython
Notebook in your Django settings.

The first one is ``NOTEBOOK_ARGUMENTS`` that can be used to hold those options that available via::

    $ ipython notebook -h

For example::

    NOTEBOOK_ARGUMENTS = [
        '--ip', 'x.x.x.x',
        '--port', 'xx',
    ]

Another one is ``IPYTHON_ARGUMENTS`` that for those options that available via::

    $ ipython -h

The Django settings module and database models are auto-loaded into the
interactive shell's global namespace also for IPython Notebook.

Auto-loading is done by a custom IPython extension which is activated by
default by passing the
``--ext django_extensions.management.notebook_extension``
argument to the Notebook.  If you need to pass custom options to the IPython
Notebook, you can override the default options in your Django settings using
the ``IPYTHON_ARGUMENTS`` setting.  For example::

    IPYTHON_ARGUMENTS = [
        '--ext', 'django_extensions.management.notebook_extension',
        '--ext', 'myproject.notebook_extension',
        '--debug',
    ]

To activate auto-loading, remember to either include the django-extensions' default
notebook extension or copy its auto-loading code into your own extension.

Note that the IPython Notebook feature doesn't currently honor the
``--dont-load`` option.

.. _`IPython Notebook`: http://ipython.org/ipython-doc/dev/interactive/htmlnotebook.html



Additional Imports
------------------

In addition to importing the models you can specify other items to import by default.
These are specified in SHELL_PLUS_PRE_IMPORTS and SHELL_PLUS_POST_IMPORTS. The former is imported
before any other imports (such as the default models import) and the latter is imported after any
other imports. Both have similar syntax. So in your settings.py file:

::

    SHELL_PLUS_PRE_IMPORTS = [
        ('module.submodule1', ('class1', 'function2')),
        ('module.submodule2', 'function3'),
        ('module.submodule3', '*'),
        'module.submodule4'
    ]

The above example would directly translate to the following python code which would be executed before
the automatic imports:

::

    from module.submodule1 import class1, function2
    from module.submodule2 import function3
    from module.submodule3 import *
    import module.submodule4

These symbols will be available as soon as the shell starts.


Database application signature
------------------------------

If using PostgreSQL the ``application_name`` is set by default to
``django_shell`` to help  identify queries made under shell_plus.


SQL queries
-------------------------

If the configuration option DEBUG is set to True, it is possible to print SQL queries as they're executed in shell_plus like::

  $ ./manage.py shell_plus --print-sql

You can also set the configuration option SHELL_PLUS_PRINT_SQL to omit the above command line option.

::

  # print SQL queries in shell_plus
  SHELL_PLUS_PRINT_SQL = True
