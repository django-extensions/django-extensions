shell_plus
=============

:synopsis: Django shell with autoloading of the apps database models


Configuration
------------

Sometimes, models from your own apps and other peoples apps have colliding names,
or you may want to completly skip loading an apps models. Here are some examples of how to do that.

Note: This settings are just used inside shell_plus and will not affect your envirnoment.

::

  # Rename the automatic loaded module Messages in the app blog to blog_messages.
  SHELL_PLUS = {
    'model_aliases': {'blog': {'Messages': 'blog_messages'}},
  }

::

  # Dont load the 'sites' app, and skip the model 'pictures' in the app 'blog'
  SHELL_PLUS = {
    'dont_load': ['sites', 'blog.pictures'],
  }


You can also combine model_aliases and dont_load.