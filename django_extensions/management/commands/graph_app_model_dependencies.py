from __future__ import annotations

import json
import os
import sys
import tempfile

from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
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


Edge = tuple[str, str]


class Command(BaseCommand):
    """
    Creates an app-level dependency graph based on model relations.

    Nodes are Django app labels. There is a directed edge A -> B if any model
    in app A has a relation (FK/O2O/M2M) to a model in app B.
    """

    help = (
        "Creates an app-level dependency graph based on model relations. "
        "Nodes are apps; edges represent cross-app model relations."
    )

    can_import_settings = True

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "app_label",
            nargs="*",
            help=(
                "App labels to include. If omitted, use --all-applications to "
                "include all installed apps."
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
                "Output graph data as raw DOT (graph description language) "
                "text data."
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
                '"in" (incoming relations first), "out" (outgoing relations first). '
                "Default is None."
            ),
        )

    @signalcommand
    def handle(self, *args, **options):
        # Determine which apps to include
        app_labels: list[str] = options["app_label"]
        if not app_labels and not options["all_applications"]:
            msg = "need one or more arguments for appname or use --all-applications"
            raise CommandError(msg)

        if options["all_applications"]:
            selected_apps: set[str] = {
                cfg.label for cfg in apps.get_app_configs()}
        else:
            selected_apps = set(app_labels)

        # Determine output format (same logic style as graph_models)
        outputfile = options.get("outputfile") or ""
        _, outputfile_ext = os.path.splitext(outputfile)
        outputfile_ext = outputfile_ext.lower()
        output_opts_names = ["pydot", "pygraphviz", "json", "dot"]
        output_opts = {k: v for k,
                       v in options.items() if k in output_opts_names}
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
            msg = "Neither pygraphviz nor pydotplus could "
            "be found to generate the image. "
            "To generate text output, use the --json or --dot options.",
            raise CommandError(msg)

        if options.get("rankdir") != "TB" and output not in ["pydot",
                                                             "pygraphviz", "dot"]:
            msg = "--rankdir is not supported for the chosen output format"
            raise CommandError(msg)

        if options.get("ordering") and output not in ["pydot",
                                                      "pygraphviz", "dot"]:
            msg = "--ordering is not supported for the chosen output format"
            raise CommandError(msg)

        if output in ["pydot", "pygraphviz"] and not outputfile:
            msg = "An output file (--output) must be specified when --pydot or "
            "--pygraphviz are set.",
            raise CommandError(msg)

        edges, app_nodes = self._collect_app_edges(selected_apps)

        graph_data = self._build_graph_data(app_nodes, edges)

        if output == "json":
            return self.render_output_json(graph_data, outputfile)

        dotdata = self._build_dot(
            app_nodes,
            edges,
            rankdir=options.get("rankdir") or "TB",
            ordering=options.get("ordering"),
        )

        if output == "pygraphviz":
            return self.render_output_pygraphviz(dotdata, **options)
        if output == "pydot":
            return self.render_output_pydot(dotdata, **options)

        # Ensure file output ends with a newline, mirroring graph_models tests.
        if outputfile and not dotdata.endswith("\n"):
            dotdata = dotdata + "\n"

        self.print_output(dotdata, outputfile)

    def _collect_app_edges(
        self,
        selected_apps: set[str],
    ) -> tuple[set[Edge], set[str]]:
        """
        Collect app-level edges based on model relations.

        Returns:
            edges: {(src_app, tgt_app), ...}
            app_labels: {app_label, ...}
        """
        if not selected_apps:
            app_labels: set[str] = {
                cfg.label for cfg in apps.get_app_configs()}
        else:
            app_labels = selected_apps

        edges: set[Edge] = set()

        for model in apps.get_models():
            src_app = model._meta.app_label
            if src_app not in app_labels:
                continue

            for field in model._meta.get_fields():
                # Skip non-relations and auto-created reverse relations
                if not getattr(field, "is_relation", False) or getattr(field,
                                                                       "auto_created",
                                                                       False):
                    continue

                remote = getattr(field, "remote_field", None)
                if not remote:
                    continue

                rel_model = remote.model
                if not hasattr(rel_model, "_meta"):
                    continue

                tgt_app = rel_model._meta.app_label
                if tgt_app not in app_labels:
                    continue

                if src_app != tgt_app:
                    edges.add((src_app, tgt_app))

        return edges, app_labels

    def _build_graph_data(
        self,
        app_labels: set[str],
        edges: set[Edge],
    ) -> dict:
        """
        Simple JSON-serializable structure for app graph.

        Example:
        {
            "apps": ["app_a", "app_b"],
            "edges": [{"from": "app_a", "to": "app_b"}],
        }
        """
        return {
            "apps": sorted(app_labels),
            "edges": [
                {"from": src, "to": tgt}
                for src, tgt in sorted(edges)
            ],
        }

    def _build_dot(
        self,
        app_labels: set[str],
        edges: set[Edge],
        rankdir: str = "TB",
        ordering: str | None = None,
    ) -> str:
        lines: list[str] = ["digraph app_dependencies {"]
        lines.append(f"  rankdir={rankdir};")

        if ordering:
            lines.append(f'  graph [ordering="{ordering}"];')

        # Nodes
        for app in sorted(app_labels):
            lines.append(f'  "{app}";')

        # Edges
        for src, tgt in sorted(edges):
            lines.append(f'  "{src}" -> "{tgt}";')

        lines.append("}")
        return "\n".join(lines)

    def print_output(self, dotdata, output_file=None):
        """Write model data to file or stdout in DOT (text) format."""
        if isinstance(dotdata, bytes):
            dotdata = dotdata.decode()

        if output_file:
            with open(output_file, "wt") as dot_output_f:
                dot_output_f.write(dotdata)
        else:
            self.stdout.write(dotdata)

    def render_output_json(self, graph_data, output_file=None):
        """Write model data to file or stdout in JSON format."""
        if output_file:
            with open(output_file, "wt") as json_output_f:
                json.dump(graph_data, json_output_f)
        else:
            self.stdout.write(json.dumps(graph_data))

    def render_output_pygraphviz(self, dotdata, **kwargs):
        """Render model data as image using pygraphviz."""
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
        """Render model data as image using pydot."""
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
        ext = output_file[output_file.rfind(".") + 1:]
        format_ = ext if ext in formats else "raw"
        graph.write(output_file, format=format_)
