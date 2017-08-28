# -*- coding: utf-8 -*-
import sys
import json

import six
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

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
        """Allow defaults for arguments to be set in settings.GRAPH_MODELS.

        Each argument in self.arguments is a dict where the key is the
        space-separated args and the value is our kwarg dict.

        The default from settings is keyed as the long arg name with '--'
        removed and any '-' replaced by '_'.
        """
        self.arguments = {
            '--pygraphviz': {
                'action': 'store_true', 'dest': 'pygraphviz',
                'help': 'Use PyGraphViz to generate the image.'},

            '--pydot': {'action': 'store_true', 'dest': 'pydot',
                        'help': 'Use PyDot(Plus) to generate the image.'},

            '--disable-fields -d': {
                'action': 'store_true', 'dest': 'disable_fields',
                'help': 'Do not show the class member fields'},

            '--group-models -g': {
                'action': 'store_true', 'dest': 'group_models',
                'help': 'Group models together respective to their '
                'application'},

            '--all-applications -a': {
                'action': 'store_true', 'dest': 'all_applications',
                'help': 'Automatically include all applications from '
                'INSTALLED_APPS'},

            '--output -o': {
                'action': 'store', 'dest': 'outputfile',
                'help': 'Render output file. Type of output dependend on file '
                'extensions. Use png or jpg to render graph to image.'},

            '--layout -l': {
                'action': 'store', 'dest': 'layout', 'default': 'dot',
                'help': 'Layout to be used by GraphViz for visualization. '
                'Layouts: circo dot fdp neato nop nop1 nop2 twopi'},

            '--verbose-names -n': {
                'action': 'store_true', 'dest': 'verbose_names',
                'help': 'Use verbose_name of models and fields'},

            '--language -L': {
                'action': 'store', 'dest': 'language',
                'help': 'Specify language used for verbose_name localization'},

            '--exclude-columns -x': {
                'action': 'store', 'dest': 'exclude_columns',
                'help': 'Exclude specific column(s) from the graph. '
                'Can also load exclude list from file.'},

            '--exclude-models -X': {
                'action': 'store', 'dest': 'exclude_models',
                'help': 'Exclude specific model(s) from the graph. Can also '
                'load exclude list from file. Wildcards (*) are allowed.'},

            '--include-models -I': {
                'action': 'store', 'dest': 'include_models',
                'help': 'Restrict the graph to specified models. Wildcards '
                '(*) are allowed.'},

            '--inheritance -e': {
                'action': 'store_true', 'dest': 'inheritance', 'default': True,
                'help': 'Include inheritance arrows (default)'},

            '--no-inheritance -E': {
                'action': 'store_false', 'dest': 'inheritance',
                'help': 'Do not include inheritance arrows'},

            '--hide-relations-from-fields -R': {
                'action': 'store_false', 'dest': 'relations_as_fields',
                'default': True,
                'help': 'Do not show relations as fields in the graph.'},

            '--disable-sort-fields -S': {
                'action': 'store_false', 'dest': 'sort_fields',
                'default': True, 'help': 'Do not sort fields'},

            '--json': {'action': 'store_true', 'dest': 'json',
                       'help': 'Output graph data as JSON'}
        }

        defaults = getattr(settings, 'GRAPH_MODELS', None)

        if defaults:
            for argument in self.arguments:
                arg_split = argument.split(' ')
                setting_opt = arg_split[0].lstrip('-').replace('-', '_')
                if setting_opt in defaults:
                    self.arguments[argument]['default'] = defaults[setting_opt]

        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        """Unpack self.arguments for parser.add_arguments."""
        parser.add_argument('app_label', nargs='*')
        for argument in self.arguments:
            parser.add_argument(*argument.split(' '),
                                **self.arguments[argument])

    @signalcommand
    def handle(self, *args, **options):
        args = options['app_label']
        if len(args) < 1 and not options['all_applications']:
            raise CommandError("need one or more arguments for appname")

        use_pygraphviz = options.get('pygraphviz', False)
        use_pydot = options.get('pydot', False)
        use_json = options.get('json', False)
        if use_json and (use_pydot or use_pygraphviz):
            raise CommandError("Cannot specify --json with --pydot or --pygraphviz")

        cli_options = ' '.join(sys.argv[2:])
        graph_models = ModelGraph(args, cli_options=cli_options, **options)
        graph_models.generate_graph_data()
        graph_data = graph_models.get_graph_data(as_json=use_json)
        if use_json:
            self.render_output_json(graph_data, **options)
            return

        dotdata = generate_dot(graph_data)
        if not six.PY3:
            dotdata = dotdata.encode('utf-8')
        if options['outputfile']:
            if not use_pygraphviz and not use_pydot:
                if HAS_PYGRAPHVIZ:
                    use_pygraphviz = True
                elif HAS_PYDOT:
                    use_pydot = True
            if use_pygraphviz:
                self.render_output_pygraphviz(dotdata, **options)
            elif use_pydot:
                self.render_output_pydot(dotdata, **options)
            else:
                raise CommandError("Neither pygraphviz nor pydotplus could be found to generate the image")
        else:
            self.print_output(dotdata)

    def print_output(self, dotdata):
        if six.PY3 and isinstance(dotdata, six.binary_type):
            dotdata = dotdata.decode()

        print(dotdata)

    def render_output_json(self, graph_data, **kwargs):
        output_file = kwargs.get('outputfile')
        if output_file:
            with open(output_file, 'wt') as json_output_f:
                json.dump(graph_data, json_output_f)
        else:
            print(json.dumps(graph_data))

    def render_output_pygraphviz(self, dotdata, **kwargs):
        """Renders the image using pygraphviz"""
        if not HAS_PYGRAPHVIZ:
            raise CommandError("You need to install pygraphviz python module")

        version = pygraphviz.__version__.rstrip("-svn")
        try:
            if tuple(int(v) for v in version.split('.')) < (0, 36):
                # HACK around old/broken AGraph before version 0.36 (ubuntu ships with this old version)
                import tempfile
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
        """Renders the image using pydot"""
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
        formats = ['bmp', 'canon', 'cmap', 'cmapx', 'cmapx_np', 'dot', 'dia', 'emf',
                   'em', 'fplus', 'eps', 'fig', 'gd', 'gd2', 'gif', 'gv', 'imap',
                   'imap_np', 'ismap', 'jpe', 'jpeg', 'jpg', 'metafile', 'pdf',
                   'pic', 'plain', 'plain-ext', 'png', 'pov', 'ps', 'ps2', 'svg',
                   'svgz', 'tif', 'tiff', 'tk', 'vml', 'vmlz', 'vrml', 'wbmp', 'xdot']
        ext = output_file[output_file.rfind('.') + 1:]
        format = ext if ext in formats else 'raw'
        graph.write(output_file, format=format)
