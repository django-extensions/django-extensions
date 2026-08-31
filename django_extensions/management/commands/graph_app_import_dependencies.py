from __future__ import annotations

import json
import os
import sys
import tempfile

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from django_extensions.management.app_import_graph import build_app_dependency_graph
from django_extensions.management.utils import signalcommand

try:
    import pygraphviz

    HAS_PYGRAPHVIZ = True
except ImportError:
    HAS_PYGRAPHVIZ = False

try:
    try:
        import pydotplus as pydot
    except ImportError:
        import pydot
    HAS_PYDOT = True
except ImportError:
    HAS_PYDOT = False


class Command(BaseCommand):
    """
    Creates an app-level dependency graph based on cross-app Python imports.

    Nodes are Django app labels. There is a directed edge A -> B if any
    module in app A imports something owned by app B, found by parsing
    every installed app's source with ``ast`` (no import side effects).
    This catches architectural coupling that a model-relation graph never
    shows, such as service calls, task imports, or admin imports across
    apps. It can also detect and highlight cycles -- strongly connected
    components of mutually-dependent apps -- and the specific edges that
    close each cycle.
    """

    help = (
        "Creates an app-level dependency graph based on cross-app Python "
        "imports. Nodes are apps; edges represent one app importing "
        "another. Can detect and highlight import cycles between apps."
    )

    can_import_settings = True

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "app_label",
            nargs="*",
            help=(
                "App labels to include (and edges between them only). If "
                "omitted, use --all-applications to include all installed "
                "apps."
            ),
        )
        parser.add_argument(
            "--all-applications",
            "-a",
            action="store_true",
            default=False,
            dest="all_applications",
            help="Automatically include all applications from INSTALLED_APPS.",
        )
        parser.add_argument(
            "--exclude",
            action="store",
            dest="exclude",
            help="Comma-separated app labels to drop from the graph (applied "
            "after --all-applications/app labels and --exclude-external).",
        )
        parser.add_argument(
            "--exclude-external",
            action="store_true",
            default=False,
            dest="exclude_external",
            help="Drop every app installed into site-packages/dist-packages "
            "(i.e. Django itself and ordinary third-party apps), keeping "
            "only apps that live in your project (including editable "
            "installs).",
        )
        parser.add_argument(
            "--exclude-name-prefix",
            action="store",
            dest="exclude_name_prefix",
            help="Comma-separated dotted app-name prefixes to drop, subtree "
            "included -- e.g. myproject.reporting.exporters drops every "
            "nested app label under it, not just one label.",
        )
        parser.add_argument(
            "--exclude-file-pattern",
            action="store",
            dest="exclude_file_pattern",
            help="Comma-separated fnmatch-style glob patterns for files to "
            "skip when scanning for imports, matched against both the bare "
            "filename and the path relative to the app (e.g. "
            "'test*.py,migrations/*.py'). Nothing is excluded by default, "
            "and no particular test-file convention is assumed -- pass "
            "'test*.py' yourself to drop test-only imports (fixtures, "
            "factories, mocks pulled in from other apps), which is a "
            "different kind of coupling than production code importing "
            "production code.",
        )
        parser.add_argument(
            "--highlight-cycles",
            action="store_true",
            default=False,
            dest="highlight_cycles",
            help="Box each group of mutually-dependent apps (strongly "
            "connected component) in its own color and mark the specific "
            "edges that close each cycle in red. For --json output, add "
            "'cycle_groups' and 'feedback_edges' keys instead. Off by "
            "default -- output is identical to the plain graph otherwise.",
        )
        parser.add_argument(
            "--pygraphviz",
            action="store_true",
            default=False,
            dest="pygraphviz",
            help="Output graph data as image using PyGraphViz.",
        )
        parser.add_argument(
            "--pydot",
            action="store_true",
            default=False,
            dest="pydot",
            help="Output graph data as image using PyDot(Plus).",
        )
        parser.add_argument(
            "--dot",
            action="store_true",
            default=False,
            dest="dot",
            help=(
                "Output graph data as raw DOT (graph description language) text data."
            ),
        )
        parser.add_argument(
            "--json",
            action="store_true",
            default=False,
            dest="json",
            help="Output graph data as JSON.",
        )
        parser.add_argument(
            "--output",
            "-o",
            action="store",
            dest="outputfile",
            help=(
                "Render output file. Type of output depends on file extension. "
                "Use png or jpg to render graph to image (via pygraphviz/pydot)."
            ),
        )
        parser.add_argument(
            "--layout",
            "-l",
            action="store",
            dest="layout",
            default="dot",
            help=(
                "Layout to be used by GraphViz for visualization. Layouts: "
                "circo dot fdp neato nop nop1 nop2 twopi"
            ),
        )
        parser.add_argument(
            "--rankdir",
            action="store",
            default="TB",
            dest="rankdir",
            choices=["TB", "BT", "LR", "RL"],
            help=(
                "Set direction of graph layout. Supported directions: TB, LR, "
                "BT and RL. Default is TB."
            ),
        )
        parser.add_argument(
            "--ordering",
            action="store",
            default=None,
            dest="ordering",
            choices=["in", "out"],
            help=(
                "Controls how the edges are arranged. Supported orderings: "
                '"in" (incoming relations first), "out" (outgoing relations '
                "first). Default is None."
            ),
        )

    @signalcommand
    def handle(self, *args, **options):
        app_label: list[str] = options["app_label"]
        if not app_label and not options["all_applications"]:
            msg = "need one or more arguments for appname or use --all-applications"
            raise CommandError(msg)

        if options["all_applications"]:
            only = None
        else:
            only = frozenset(app_label)

        exclude = (
            frozenset(options["exclude"].split(","))
            if options["exclude"]
            else frozenset()
        )
        exclude_name_prefixes = (
            frozenset(options["exclude_name_prefix"].split(","))
            if options["exclude_name_prefix"]
            else frozenset()
        )
        exclude_file_patterns = (
            frozenset(options["exclude_file_pattern"].split(","))
            if options["exclude_file_pattern"]
            else frozenset()
        )

        # Determine output format (same logic style as graph_models /
        # graph_app_model_dependencies).
        outputfile = options.get("outputfile") or ""
        _, outputfile_ext = os.path.splitext(outputfile)
        outputfile_ext = outputfile_ext.lower()
        output_opts_names = ["pydot", "pygraphviz", "json", "dot"]
        output_opts = {k: v for k, v in options.items() if k in output_opts_names}
        output_opts_count = sum(output_opts.values())
        if output_opts_count > 1:
            msg = "Only one of %s can be set." % ", ".join(
                ["--%s" % opt for opt in output_opts_names]
            )
            raise CommandError(msg)
        if output_opts_count == 1:
            output = next(key for key, val in output_opts.items() if val)
        elif not outputfile:
            # Default to printing DOT to stdout if nothing else is set.
            output = "dot"
        elif outputfile_ext == ".dot":
            output = "dot"
        elif outputfile_ext == ".json":
            output = "json"
        elif HAS_PYGRAPHVIZ:
            output = "pygraphviz"
        elif HAS_PYDOT:
            output = "pydot"
        else:
            msg = (
                "Neither pygraphviz nor pydotplus could be found to generate "
                "the image. To generate text output, use the --json or "
                "--dot options."
            )
            raise CommandError(msg)

        if options.get("rankdir") != "TB" and output not in [
            "pydot",
            "pygraphviz",
            "dot",
        ]:
            msg = "--rankdir is not supported for the chosen output format"
            raise CommandError(msg)

        if options.get("ordering") and output not in ["pydot", "pygraphviz", "dot"]:
            msg = "--ordering is not supported for the chosen output format"
            raise CommandError(msg)

        if output in ["pydot", "pygraphviz"] and not outputfile:
            msg = (
                "An output file (--output) must be specified when --pydot or "
                "--pygraphviz are set."
            )
            raise CommandError(msg)

        try:
            graph = build_app_dependency_graph(
                only=only,
                exclude=exclude,
                exclude_external=options["exclude_external"],
                exclude_name_prefixes=exclude_name_prefixes,
                exclude_file_patterns=exclude_file_patterns,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        highlight_cycles = options["highlight_cycles"]

        if output == "json":
            graph_data = self._build_graph_data(
                graph, highlight_cycles=highlight_cycles
            )
            return self.render_output_json(graph_data, outputfile)

        dotdata = graph.to_dot(
            rankdir=options.get("rankdir") or "TB",
            ordering=options.get("ordering"),
            highlight_cycles=highlight_cycles,
        )

        if output == "pygraphviz":
            return self.render_output_pygraphviz(dotdata, **options)
        if output == "pydot":
            return self.render_output_pydot(dotdata, **options)

        self.print_output(dotdata, outputfile)

    def _build_graph_data(self, graph, *, highlight_cycles: bool) -> dict:
        """
        Simple JSON-serializable structure for the app import graph.

        Example::

            {
                "apps": ["app_a", "app_b"],
                "edges": [{"from": "app_a", "to": "app_b"}],
            }

        With --highlight-cycles, also includes "cycle_groups" (each a list
        of app labels forming one strongly connected component) and
        "feedback_edges" (the edges that close each cycle).
        """
        data = {
            "apps": list(graph.app_labels),
            "edges": [{"from": src, "to": tgt} for src, tgt in sorted(graph.edges)],
        }
        if highlight_cycles:
            data["cycle_groups"] = [sorted(group) for group in graph.cycle_groups()]
            data["feedback_edges"] = [
                {"from": src, "to": tgt} for src, tgt in sorted(graph.feedback_edges())
            ]
        return data

    def print_output(self, dotdata, output_file=None):
        """Write graph data to file or stdout in DOT (text) format."""
        if isinstance(dotdata, bytes):
            dotdata = dotdata.decode()

        if output_file:
            with open(output_file, "wt") as dot_output_f:
                dot_output_f.write(dotdata)
        else:
            self.stdout.write(dotdata)

    def render_output_json(self, graph_data, output_file=None):
        """Write graph data to file or stdout in JSON format."""
        if output_file:
            with open(output_file, "wt") as json_output_f:
                json.dump(graph_data, json_output_f)
        else:
            self.stdout.write(json.dumps(graph_data))

    def render_output_pygraphviz(self, dotdata, **kwargs):
        """Render graph data as image using pygraphviz."""
        if not HAS_PYGRAPHVIZ:
            raise CommandError("You need to install pygraphviz python module")

        version = pygraphviz.__version__.rstrip("-svn")
        try:
            if tuple(int(v) for v in version.split(".")) < (0, 36):
                # HACK around old/broken AGraph before version 0.36
                #   (ubuntu ships with this old version)
                tmpfile = tempfile.NamedTemporaryFile()
                tmpfile.write(dotdata)
                tmpfile.seek(0)
                dotdata = tmpfile.name
        except ValueError:
            pass

        graph = pygraphviz.AGraph(dotdata)
        graph.layout(prog=kwargs["layout"])
        graph.draw(kwargs["outputfile"])

    def render_output_pydot(self, dotdata, **kwargs):
        """Render graph data as image using pydot."""
        if not HAS_PYDOT:
            raise CommandError("You need to install pydot python module")

        graph = pydot.graph_from_dot_data(dotdata)
        if not graph:
            raise CommandError("pydot returned an error")
        if isinstance(graph, (list, tuple)):
            if len(graph) > 1:
                sys.stderr.write(
                    "Found more then one graph, rendering only the first one.\n"
                )
            graph = graph[0]

        output_file = kwargs["outputfile"]
        formats = [
            "bmp",
            "canon",
            "cmap",
            "cmapx",
            "cmapx_np",
            "dot",
            "dia",
            "emf",
            "em",
            "fplus",
            "eps",
            "fig",
            "gd",
            "gd2",
            "gif",
            "gv",
            "imap",
            "imap_np",
            "ismap",
            "jpe",
            "jpeg",
            "jpg",
            "metafile",
            "pdf",
            "pic",
            "plain",
            "plain-ext",
            "png",
            "pov",
            "ps",
            "ps2",
            "svg",
            "svgz",
            "tif",
            "tiff",
            "tk",
            "vml",
            "vmlz",
            "vrml",
            "wbmp",
            "webp",
            "xdot",
        ]
        ext = output_file[output_file.rfind(".") + 1 :]
        format_ = ext if ext in formats else "raw"
        graph.write(output_file, format=format_)
