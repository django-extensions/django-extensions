# coding=utf-8
import sys
from optparse import NO_DEFAULT

import six
from django.conf import settings
from django.core.management.base import CommandError

from django_extensions.compat import CompatibilityBaseCommand as BaseCommand
from django_extensions.management.modelviz import generate_dot
from django_extensions.management.utils import signalcommand

try:
    import pygraphviz
    HAS_PYGRAPHVIZ = True
except ImportError:
    HAS_PYGRAPHVIZ = False

try:
    import pydot
    HAS_PYDOT = True
except ImportError:
    HAS_PYDOT = False


class Command(BaseCommand):
    help = "Creates a GraphViz dot file for the specified app names.  You can pass multiple app names and they will all be combined into a single model.  Output is usually directed to a dot file."
    args = "[appname]"
    label = 'application name'

    can_import_settings = True

    def add_arguments(self, parser):
        parser.add_argument(
            '--pygraphviz', action='store_true', dest='pygraphviz',
            help='Use PyGraphViz to generate the image.')
        parser.add_argument(
            '--pydot', action='store_true', dest='pydot',
            help='Use PyDot to generate the image.')
        parser.add_argument(
            '--disable-fields', '-d', action='store_true',
            dest='disable_fields', help='Do not show the class member fields')
        parser.add_argument(
            '--group-models', '-g', action='store_true', dest='group_models',
            help='Group models together respective to their application')
        parser.add_argument(
            '--all-applications', '-a', action='store_true',
            dest='all_applications',
            help='Automatically include all applications from INSTALLED_APPS')
        parser.add_argument(
            '--output', '-o', action='store', dest='outputfile',
            help='Render output file. Type of output dependend on file '
            'extensions. Use png or jpg to render graph to image.')
        parser.add_argument(
            '--layout', '-l', action='store', dest='layout', default='dot',
            help='Layout to be used by GraphViz for visualization. '
            'Layouts: circo dot fdp neato nop nop1 nop2 twopi')
        parser.add_argument(
            '--verbose-names', '-n', action='store_true', dest='verbose_names',
            help='Use verbose_name of models and fields')
        parser.add_argument(
            '--language', '-L', action='store', dest='language',
            help='Specify language used for verbose_name localization')
        parser.add_argument(
            '--exclude-columns', '-x', action='store', dest='exclude_columns',
            help='Exclude specific column(s) from the graph. '
            'Can also load exclude list from file.')
        parser.add_argument(
            '--exclude-models', '-X', action='store', dest='exclude_models',
            help='Exclude specific model(s) from the graph. '
            'Can also load exclude list from file.')
        parser.add_argument(
            '--include-models', '-I', action='store', dest='include_models',
            help='Restrict the graph to specified models.')
        parser.add_argument(
            '--inheritance', '-e', action='store_true', dest='inheritance',
            default=True, help='Include inheritance arrows (default)')
        parser.add_argument(
            '--no-inheritance', '-E', action='store_false', dest='inheritance',
            help='Do not include inheritance arrows')
        parser.add_argument(
            '--hide-relations-from-fields', '-R', action='store_false',
            dest="relations_as_fields",
            default=True, help="Do not show relations as fields in the graph.")
        parser.add_argument(
            '--disable-sort-fields', '-S', action="store_false",
            dest="sort_fields", default=True, help="Do not sort fields")

    @signalcommand
    def handle(self, *args, **options):
        self.options_from_settings(options)

        if len(args) < 1 and not options['all_applications']:
            raise CommandError("need one or more arguments for appname")

        use_pygraphviz = options.get('pygraphviz', False)
        use_pydot = options.get('pydot', False)
        cli_options = ' '.join(sys.argv[2:])
        dotdata = generate_dot(args, cli_options=cli_options, **options)
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
                raise CommandError("Neither pygraphviz nor pydot could be found to generate the image")
        else:
            self.print_output(dotdata)

    def options_from_settings(self, options):
        defaults = getattr(settings, 'GRAPH_MODELS', None)
        if defaults:
            for option in self.graph_models_options:
                long_opt = option._long_opts[0]
                if long_opt:
                    long_opt = long_opt.lstrip("-").replace("-", "_")
                    if long_opt in defaults:
                        default_value = None
                        if not option.default == NO_DEFAULT:
                            default_value = option.default
                        if options[option.dest] == default_value:
                            options[option.dest] = defaults[long_opt]

    def print_output(self, dotdata):
        if six.PY3 and isinstance(dotdata, six.binary_type):
            dotdata = dotdata.decode()

        print(dotdata)

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
        output_file = kwargs['outputfile']
        formats = ['bmp', 'canon', 'cmap', 'cmapx', 'cmapx_np', 'dot', 'dia', 'emf',
                   'em', 'fplus', 'eps', 'fig', 'gd', 'gd2', 'gif', 'gv', 'imap',
                   'imap_np', 'ismap', 'jpe', 'jpeg', 'jpg', 'metafile', 'pdf',
                   'pic', 'plain', 'plain-ext', 'png', 'pov', 'ps', 'ps2', 'svg',
                   'svgz', 'tif', 'tiff', 'tk', 'vml', 'vmlz', 'vrml', 'wbmp', 'xdot']
        ext = output_file[output_file.rfind('.') + 1:]
        format = ext if ext in formats else 'raw'
        graph.write(output_file, format=format)
