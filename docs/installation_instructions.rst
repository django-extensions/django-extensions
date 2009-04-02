Installation instructions
=========================

:synopsis: Installing django-command-extensions


Download and installation
-------------------------

Download
^^^^^^^^

Download the latest packaged version from
http://code.google.com/p/django-command-extensions/ and unpack it. Inside is a
script called setup.py. Enter this command::

  python setup.py install

...and the package will install automatically.

Installation
^^^^^^^^^^^^

You will need to add the *django_extensions* application to the INSTALLED_APPS
setting of your Django project *settings.py* file.::

  INSTALLED_APPS = (
      ...
      'django_extensions',
  )

This will make sure that Django finds the additional management commands
provided by *django-extensions*.

The next time you invoke *./manage.py help* you should be able to see all the
newly available commands.

Some command's or option's require additional applications or python libraries,
for example:

  * 'export_emails' will require the *python vobject* module to create vcard
    files.
  * 'graph_models' requires *pygraphviz* to render directly to image file.

If the given application or python library is not installed on your system (or
not in the python path) the executed command will raise an exception and inform
you of the missing dependency.

Version Control (Subversion and Mercurial)
------------------------------------------

Alternatively, source code can be accessed by performing a Subversion checkout
or a Mercurial clone.

Tracking the development version of *django command extensions* should be
pretty stable and will keep you up-to-date with the latests fixes.

The following command will check the application's source code out to a
directory called *django-command-extensions*:

Subversion::

  svn checkout http://django-command-extensions.googlecode.com/svn/trunk/ django-command-extensions

Mercurial::

  hg clone http://hgsvn.trbs.net/django-command-extensions

*For more information about Mercurial see MercurialGateway wiki page*

You should either install the resulting project with *python setup.py install*
or put it the *extensions* directory into your PYTHONPATH. The most common way
is to symlink (junction, if you're on Windows) the extensions directory inside
a directory which is on your PYTHONPATH, such as your Python installation's
site-packages directory.

::

  ln -sf /full/path/to/django-command-extensions/django_extensions /usr/lib/python2.5/site-packages/django_extensions

You can verify that the application is available on your PYTHONPATH by opening a Python interpreter and entering the following commands:

::

  >>> import django_extensions
  >>> django_extensions.VERSION
  (0, 2, 'pre')

Keep in mind that the current code in SVN trunk may be different from the
packaged release, and may contain bugs and backwards-incompatible changes, as
well as new goodies to play with.