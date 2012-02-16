Graph models
============

:synopsis: Renders a graphical overview of your project or specified apps.

Creates a GraphViz_ dot file for the specified app names.  You can pass
multiple app names and they will all be combined into a single model.  Output
is usually directed to a dot file.

With the latest revisions it's also possible to specify an output file if
pygraphviz_ is installed and render directly to an image or other supported
filetype.


Example Usage
-------------

With *django-command-extensions* installed you can create a dot-file or an
image by using the *graph_models* command. Like used in the following examples::

  # Create a dot file
  $ ./manage.py graph_models -a > my_project.dot

::

  # Create a PNG image file called my_project_visualized.png with application grouping
  $ ./manage.py graph_models -a -g -o my_project_visualized.png

::

  # Create a dot file for only the 'foo' and 'bar' applications of your project
  $ ./manage.py graph_models foo bar > my_project.dot


.. _GraphViz: http://www.graphviz.org/
.. _pygraphviz: https://networkx.lanl.gov/wiki/pygraphviz
