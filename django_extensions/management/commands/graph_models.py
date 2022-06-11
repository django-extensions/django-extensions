# -*- coding: utf-8 -*-
import sys
import json
import os
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template import loader

from django_extensions.management.modelviz import ModelGraph, generate_dot
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
    help = "Creates a GraphViz dot file for the specified app names. You can pass multiple app names and they will all be combined into a single model. Output is usually directed to a dot file."

    can_import_settings = True

    def __init__(self, *args, **kwargs):
        """
        Allow defaults for arguments to be set in settings.GRAPH_MODELS.

        Each argument in self.arguments is a dict where the key is the
        space-separated args and the value is our kwarg dict.

        The default from settings is keyed as the long arg name with '--'
        removed and any '-' replaced by '_'. For example, the default value for
        --disable-fields can be set in settings.GRAPH_MODELS['disable_fields'].
        """
        self.arguments = {
            '--pygraphviz': {
                'action': 'store_true',
                'default': False,
                'dest': 'pygraphviz',
                'help': 'Output graph data as image using PyGraphViz.',
            },
            '--pydot': {
                'action': 'store_true',
                'default': False,
                'dest': 'pydot',
                'help': 'Output graph data as image using PyDot(Plus).',
            },
            '--dot': {
                'action': 'store_true',
                'default': False,
                'dest': 'dot',
                'help': 'Output graph data as raw DOT (graph description language) text data.',
            },
            '--json': {
                'action': 'store_true',
                'default': False,
                'dest': 'json',
                'help': 'Output graph data as JSON',
            },
            '--disable-fields -d': {
                'action': 'store_true',
                'default': False,
                'dest': 'disable_fields',
                'help': 'Do not show the class member fields',
            },
            '--disable-abstract-fields': {
                'action': 'store_true',
                'default': False,
                'dest': 'disable_abstract_fields',
                'help': 'Do not show the class member fields that were inherited',
            },
            '--group-models -g': {
                'action': 'store_true',
                'default': False,
                'dest': 'group_models',
                'help': 'Group models together respective to their application',
            },
            '--all-applications -a': {
                'action': 'store_true',
                'default': False,
                'dest': 'all_applications',
                'help': 'Automatically include all applications from INSTALLED_APPS',
            },
            '--output -o': {
                'action': 'store',
                'dest': 'outputfile',
                'help': 'Render output file. Type of output dependend on file extensions. Use png or jpg to render graph to image.',
            },
            '--layout -l': {
                'action': 'store',
                'dest': 'layout',
                'default': 'dot',
                'help': 'Layout to be used by GraphViz for visualization. Layouts: circo dot fdp neato nop nop1 nop2 twopi',
            },
            '--theme -t': {
                'action': 'store',
                'dest': 'theme',
                'default': 'django2018',
                'help': 'Theme to use. Supplied are \'original\' and \'django2018\'. You can create your own by creating dot templates in \'django_extentions/graph_models/themename/\' template directory.',
            },
            '--verbose-names -n': {
                'action': 'store_true',
                'default': False,
                'dest': 'verbose_names',
                'help': 'Use verbose_name of models and fields',
            },
            '--language -L': {
                'action': 'store',
                'dest': 'language',
                'help': 'Specify language used for verbose_name localization',
            },
            '--exclude-columns -x': {
                'action': 'store',
                'dest': 'exclude_columns',
                'help': 'Exclude specific column(s) from the graph. Can also load exclude list from file.',
            },
            '--exclude-models -X': {
                'action': 'store',
                'dest': 'exclude_models',
                'help': 'Exclude specific model(s) from the graph. Can also load exclude list from file. Wildcards (*) are allowed.',
            },
            '--include-models -I': {
                'action': 'store',
                'dest': 'include_models',
                'help': 'Restrict the graph to specified models. Wildcards (*) are allowed.',
            },
            '--inheritance -e': {
                'action': 'store_true',
                'default': True,
                'dest': 'inheritance',
                'help': 'Include inheritance arrows (default)',
            },
            '--no-inheritance -E': {
                'action': 'store_false',
                'default': False,
                'dest': 'inheritance',
                'help': 'Do not include inheritance arrows',
            },
            '--hide-relations-from-fields -R': {
                'action': 'store_false',
                'default': True,
                'dest': 'relations_as_fields',
                'help': 'Do not show relations as fields in the graph.',
            },
            '--relation-fields-only': {
                'action': 'store',
                'default': False,
                'dest': 'relation_fields_only',
                'help': 'Only display fields that are relevant for relations',
            },
            '--disable-sort-fields -S': {
                'action': 'store_false',
                'default': True,
                'dest': 'sort_fields',
                'help': 'Do not sort fields',
            },
            '--hide-edge-labels': {
                'action': 'store_true',
                'default': False,
                'dest': 'hide_edge_labels',
                'help': 'Do not show relations labels in the graph.',
            },
            '--arrow-shape': {
                'action': 'store',
                'default': 'dot',
                'dest': 'arrow_shape',
                'choices': ['box', 'crow', 'curve', 'icurve', 'diamond', 'dot', 'inv', 'none', 'normal', 'tee', 'vee'],
                'help': 'Arrow shape to use for relations. Default is dot. Available shapes: box, crow, curve, icurve, diamond, dot, inv, none, normal, tee, vee.',
            },
            '--color-code-deletions': {
                'action': 'store_true',
                'default': False,
                'dest': 'color_code_deletions',
                'help': 'Color the relations according to their on_delete setting, where it it applicable. The colors are: red (CASCADE), orange (SET_NULL), green (SET_DEFAULT), yellow (SET), blue (PROTECT), grey (DO_NOTHING) and purple (RESTRICT).',
            },
            '--rankdir': {
                'action': 'store',
                'default': 'TB',
                'dest': 'rankdir',
                'choices': ['TB', 'BT', 'LR', 'RL'],
                'help': 'Set direction of graph layout. Supported directions: "TB", "LR", "BT", "RL", corresponding to directed graphs drawn from top to bottom, from left to right, from bottom to top, and from right to left, respectively. Default is TB.'
            },
        }

        defaults = getattr(settings, 'GRAPH_MODELS', None)

        if defaults:
            for argument in self.arguments:
                arg_split = argument.split(' ')
                setting_opt = arg_split[0].lstrip('-').replace('-', '_')
                if setting_opt in defaults:
                    self.arguments[argument]['default'] = defaults[setting_opt]

        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        """Unpack self.arguments for parser.add_arguments."""
        parser.add_argument('app_label', nargs='*')
        for argument in self.arguments:
            parser.add_argument(*argument.split(' '), **self.arguments[argument])

    @signalcommand
    def handle(self, *args, **options):
        args = options['app_label']
        if not args and not options['all_applications']:
            default_app_labels = getattr(settings, 'GRAPH_MODELS', {}).get("app_labels")
            if default_app_labels:
                args = default_app_labels
            else:
                raise CommandError("need one or more arguments for appname")

        # Determine output format based on options, file extension, and library
        # availability.
        outputfile = options.get("outputfile") or ""
        _, outputfile_ext = os.path.splitext(outputfile)
        outputfile_ext = outputfile_ext.lower()
        output_opts_names = ['pydot', 'pygraphviz', 'json', 'dot']
        output_opts = {k: v for k, v in options.items() if k in output_opts_names}
        output_opts_count = sum(output_opts.values())
        if output_opts_count > 1:
            raise CommandError("Only one of %s can be set." % ", ".join(["--%s" % opt for opt in output_opts_names]))

        if output_opts_count == 1:
            output = next(key for key, val in output_opts.items() if val)
        elif not outputfile:
            # When neither outputfile nor a output format option are set,
            # default to printing .dot format to stdout. Kept for backward
            # compatibility.
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
            raise CommandError("Neither pygraphviz nor pydotplus could be found to generate the image. To generate text output, use the --json or --dot options.")

        if options.get('rankdir') != 'TB' and output not in ["pydot", "pygraphviz", "dot"]:
            raise CommandError("--rankdir is not supported for the chosen output format")

        # Consistency check: Abort if --pygraphviz or --pydot options are set
        # but no outputfile is specified. Before 2.1.4 this silently fell back
        # to printind .dot format to stdout.
        if output in ["pydot", "pygraphviz"] and not outputfile:
            raise CommandError("An output file (--output) must be specified when --pydot or --pygraphviz are set.")

        cli_options = ' '.join(sys.argv[2:])
        graph_models = ModelGraph(args, cli_options=cli_options, **options)
        graph_models.generate_graph_data()

        if output == "json":
            graph_data = graph_models.get_graph_data(as_json=True)
            return self.render_output_json(graph_data, outputfile)

        graph_data = graph_models.get_graph_data(as_json=False)

        theme = options['theme']
        template_name = os.path.join('django_extensions', 'graph_models', theme, 'digraph.dot')
        template = loader.get_template(template_name)

        dotdata = generate_dot(graph_data, template=template)

        if output == "pygraphviz":
            return self.render_output_pygraphviz(dotdata, **options)
        if output == "pydot":
            return self.render_output_pydot(dotdata, **options)
        self.print_output(dotdata, outputfile)

    def print_output(self, dotdata, output_file=None):
        """Write model data to file or stdout in DOT (text) format."""
        if isinstance(dotdata, bytes):
            dotdata = dotdata.decode()

        if output_file:
            with open(output_file, 'wt') as dot_output_f:
                dot_output_f.write(dotdata)
        else:
            self.stdout.write(dotdata)

    def render_output_json(self, graph_data, output_file=None):
        """Write model data to file or stdout in JSON format."""
        if output_file:
            with open(output_file, 'wt') as json_output_f:
                json.dump(graph_data, json_output_f)
        else:
            self.stdout.write(json.dumps(graph_data))

    def render_output_pygraphviz(self, dotdata, **kwargs):
        """Render model data as image using pygraphviz."""
        if not HAS_PYGRAPHVIZ:
            raise CommandError("You need to install pygraphviz python module")

        version = pygraphviz.__version__.rstrip("-svn")
        try:
            if tuple(int(v) for v in version.split('.')) < (0, 36):
                # HACK around old/broken AGraph before version 0.36 (ubuntu ships with this old version)
                tmpfile = tempfile.NamedTemporaryFile()
                tmpfile.write(dotdata)
                tmpfile.seek(0)
                dotdata = tmpfile.name
        except ValueError:
            pass

        graph = pygraphviz.AGraph(dotdata)
        graph.layout(prog=kwargs['layout'])
        graph.draw(kwargs['outputfile'])

    def render_output_pydot(self, dotdata, **kwargs):
        """Render model data as image using pydot."""
        if not HAS_PYDOT:
            raise CommandError("You need to install pydot python module")

        graph = pydot.graph_from_dot_data(dotdata)
        if not graph:
            raise CommandError("pydot returned an error")
        if isinstance(graph, (list, tuple)):
            if len(graph) > 1:
                sys.stderr.write("Found more then one graph, rendering only the first one.\n")
            graph = graph[0]

        output_file = kwargs['outputfile']
        formats = [
            'bmp', 'canon', 'cmap', 'cmapx', 'cmapx_np', 'dot', 'dia', 'emf',
            'em', 'fplus', 'eps', 'fig', 'gd', 'gd2', 'gif', 'gv', 'imap',
            'imap_np', 'ismap', 'jpe', 'jpeg', 'jpg', 'metafile', 'pdf',
            'pic', 'plain', 'plain-ext', 'png', 'pov', 'ps', 'ps2', 'svg',
            'svgz', 'tif', 'tiff', 'tk', 'vml', 'vmlz', 'vrml', 'wbmp', 'xdot',
        ]
        ext = output_file[output_file.rfind('.') + 1:]
        format_ = ext if ext in formats else 'raw'
        graph.write(output_file, format=format_)
