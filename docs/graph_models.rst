Graph models
============

:synopsis: Renders a graphical overview of your project or specified apps.

Creates a GraphViz_ dot file for the specified app names based on their models.py.
You can pass multiple app names and they will all be combined into a single model.
Output is usually directed to a dot file.

There several options available like: grouping models, including inheritance,
excluding models and columns and changing the layout when rendering to an output
image.

With the latest revisions it's also possible to specify an output file if
pygraphviz_ is installed and render directly to an image or other supported
file-type.


Selecting a library
-------------------

You need to select the library to generate the image, you can do so by passing
the --pygraphviz or --pydot parameters depending on the library you want to use.

To install pygraphviz you usually need to run this command:

::
  $ pip install pygraphviz

It is possible you can't install it because it needs some C extensions to build, you
can try other methods to install or you can use PyDot.

To install pydot you need to run this command:

::
  $ pip install pyparsing==1.5.7
  $ pip install pydot

Instalation should be fast and easy, remember to install this exact version of
pyparsing, otherwise it's possible you get this error:

    Couldn't import dot_parser, loading of dot files will not be possible.


Example Usage
-------------

With *django-extensions* installed you can create a dot-file or an
image by using the *graph_models* command. Like used in the following examples::

  # Create a dot file
  $ ./manage.py graph_models -a > my_project.dot

::

  # Create a PNG image file called my_project_visualized.png with application grouping
  $ ./manage.py graph_models --pygraphviz -a -g -o my_project_visualized.png
  # Same but using pydot instead
  $ ./manage.py graph_models --pydot -a -g -o my_project_visualized.png

::

  # Create a dot file for only the 'foo' and 'bar' applications of your project
  $ ./manage.py graph_models foo bar > my_project.dot


.. _GraphViz: http://www.graphviz.org/
.. _pygraphviz: https://networkx.lanl.gov/wiki/pygraphviz
.. _pydot: https://pypi.python.org/pypi/pydot
