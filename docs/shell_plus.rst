shell_plus
==========

:synopsis: Django shell with autoloading of the apps database models


Configuration
-------------

Sometimes, models from your own apps and other peoples apps have colliding names,
or you may want to completly skip loading an apps models. Here are some examples of how to do that.

Note: This settings are just used inside shell_plus and will not affect your envirnoment.

::

  # Rename the automatic loaded module Messages in the app blog to blog_messages.
  SHELL_PLUS_MODEL_ALIASES = {'blog': {'Messages': 'blog_messages'},}
  }

::

  # Dont load the 'sites' app, and skip the model 'pictures' in the app 'blog'
  SHELL_PLUS_DONT_LOAD = ['sites', 'blog.pictures']
  }


You can also combine model_aliases and dont_load.

It is also possible to ignore autoloaded modules when using manage.py, like

  $ ./manage.py shell_plus --dont-load app1 --dont-load app2.module1

And, commandline parameters and settings in the configuration file is merged, so you can
safely append modules to ignore from the commandline for one time usage.
