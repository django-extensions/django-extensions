Mercurial gateway
=================

:synopsis: Mercurial (hg) Repository Gateway


Introduction
------------

For people liking the Mercurial distributed version control system. I've setup
a gateway of several Django related repositories including django-extensions.
You can use these as stand alone repositories as well as in combination with
the forest extension. Which works much like an svn:external would.
(except for that extra warm and fuzzy distributed feeling :) )

Move to Git
-----------

Since we are now officially using GIT as our version control system it might
be hard to keep the Mercurial repository up-to-date as it sync of the old svn
tree at code.google.com. At some point we might have to recreate the Mercurial
repository so we can sync directly from Github.

Usage
-----

Browse the repository at:
  http://hgsvn.trbs.net/django-command-extensions/file/

Clone the repository::

  hg clone http://hgsvn.trbs.net/django-command-extensions


HG Forests
----------

About HGForest:
  http://www.selenic.com/mercurial/wiki/index.cgi/ForestExtension

About Mercurial extensions including hg forest:
  http://www.selenic.com/mercurial/wiki/index.cgi/UsingExtensions

HGForest repository:
  http://hg.akoha.org/hgforest/
