Graph app import dependencies
==============================

:synopsis: Graphs which apps import which other apps, and can highlight import cycles between them.

Creates a GraphViz_ dot file (or JSON, or a rendered image) showing app-level
import dependencies: a directed edge *A -> B* means some module in app *A*
imports something owned by app *B*. Edges are found by parsing every
installed app's source with Python's ``ast`` module -- nothing is actually
imported, so there are no import side effects and no risk of triggering a
real circular import while graphing one.

This is a different, complementary view to :doc:`graph_models`: that command
graphs *model relations* (foreign keys, many-to-many, one-to-one).
``graph_app_import_dependencies`` graphs *Python imports* instead, so it also
catches coupling that never shows up as a model relation -- one app calling
another's service layer, importing its Celery tasks, registering its admin
classes, and so on.

It can additionally detect **import cycles**: groups of apps that
mutually depend on each other (technically, non-trivial strongly connected
components of the import graph, found with Tarjan's algorithm), and the
specific *feedback edges* -- the minimal set of edges that, if removed,
would break every cycle. Pass ``--highlight-cycles`` to see them.


Selecting apps
---------------

Like :doc:`graph_models`, pass one or more app labels as positional
arguments to graph just those apps (and only the edges between them), or
``--all-applications``/``-a`` to include every installed app::

  $ ./manage.py graph_app_import_dependencies -a

Further narrow the selection with:

- ``--exclude`` -- comma-separated app labels to drop.
- ``--exclude-external`` -- drop every app installed into
  site-packages/dist-packages (Django itself, ordinary third-party apps),
  keeping only apps that live in your project (this also recognizes apps
  installed with ``pip install -e .``).
- ``--exclude-name-prefix`` -- comma-separated dotted app-name prefixes to
  drop, subtree included. Useful for nested apps that share a dotted-name
  prefix but not a label prefix, e.g. ``myproject.reporting.exporters``
  drops every app nested under it.
- ``--exclude-file-pattern`` -- comma-separated fnmatch-style glob patterns
  for files to skip when scanning for imports, matched against both the
  bare filename and the path relative to the app (e.g.
  ``migrations/*.py``). Nothing is excluded by default, and no particular
  test-file convention is assumed -- pass ``test*.py`` yourself (the same
  default ``manage.py test --pattern`` uses) to drop test-only imports
  (fixtures, factories, mocks pulled in from other apps), which is a
  different kind of coupling than production code importing production
  code. Since cycles are computed from whatever edges remain, this also
  keeps that noise out of cycle detection.


Selecting a library
---------------------

As with :doc:`graph_models`, pass ``--pygraphviz`` or ``--pydot`` to render
directly to an image via those libraries, ``--dot`` for raw DOT text, or
``--json`` for a JSON structure. With no output-format option and no
``--output``, DOT is printed to stdout.


Example Usage
---------------

Print the import graph for every installed app as DOT::

  $ ./manage.py graph_app_import_dependencies -a

Render a PNG for just a few apps::

  $ ./manage.py graph_app_import_dependencies billing shipping catalog --pydot -o deps.png

Get JSON instead::

  $ ./manage.py graph_app_import_dependencies -a --json

::

  {"apps": ["billing", "catalog", "shipping"],
   "edges": [{"from": "billing", "to": "catalog"}, {"from": "shipping", "to": "billing"}]}

Only look at your own apps, ignoring Django and third-party dependencies::

  $ ./manage.py graph_app_import_dependencies -a --exclude-external

Ignore test-only imports, so cross-app test fixtures/factories don't get
counted as real coupling::

  $ ./manage.py graph_app_import_dependencies -a --exclude-file-pattern "test*.py"


Highlighting cycles
---------------------

Pass ``--highlight-cycles`` to make import cycles visible instead of having
to spot them by eye. With a DOT/image output, each cycle group is drawn as
its own colored cluster, and the specific edge(s) that close each cycle are
drawn in red::

  $ ./manage.py graph_app_import_dependencies catalog billing shipping --highlight-cycles --dot

Given ``billing`` and ``shipping`` importing each other (billing needs a
shipping cost estimate; shipping won't ship an order until payment
clears) -- a real, if easy-to-miss, circular dependency -- the DOT output
looks like::

  digraph app_import_dependencies {
    rankdir=TB;
    subgraph cluster_0 {
      label="cycle group 1";
      style=filled; color="lightpink";
      "billing";
      "shipping";
    }
    "catalog";
    "billing" -> "catalog";
    "billing" -> "shipping";
    "shipping" -> "billing" [color=red, penwidth=2];
  }

Pass ``--pydot``/``--pygraphviz`` with ``--output`` instead of ``--dot`` to
render this as an actual image rather than raw DOT text.

With ``--json``, the same information is added as two extra keys instead of
being drawn::

  $ ./manage.py graph_app_import_dependencies catalog billing shipping --highlight-cycles --json

::

  {"apps": ["billing", "catalog", "shipping"],
   "edges": [{"from": "billing", "to": "catalog"},
             {"from": "billing", "to": "shipping"},
             {"from": "shipping", "to": "billing"}],
   "cycle_groups": [["billing", "shipping"]],
   "feedback_edges": [{"from": "shipping", "to": "billing"}]}

``cycle_groups`` lists every strongly connected component of two or more
apps (or a single app that imports itself); ``feedback_edges`` lists the
specific edge(s) closing each of those cycles -- the actionable "cut these
imports" set, not just "these apps are entangled".

Without ``--highlight-cycles``, output is identical to today's plain graph.


.. _GraphViz: https://www.graphviz.org/
