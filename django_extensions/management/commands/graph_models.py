from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django_extensions.management.modelviz import generate_dot


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
    option_list = BaseCommand.option_list + (
        make_option('--pygraphviz', action='store_true', dest='pygraphviz',
                    help='Use PyGraphViz to generate the image.'),
        make_option('--pydot', action='store_true', dest='pydot',
                    help='Use PyDot to generate the image.'),
        make_option('--disable-fields', '-d', action='store_true', dest='disable_fields',
                    help='Do not show the class member fields'),
        make_option('--group-models', '-g', action='store_true', dest='group_models',
                    help='Group models together respective to their application'),
        make_option('--all-applications', '-a', action='store_true', dest='all_applications',
                    help='Automatically include all applications from INSTALLED_APPS'),
        make_option('--output', '-o', action='store', dest='outputfile',
                    help='Render output file. Type of output dependend on file extensions. Use png or jpg to render graph to image.'),
        make_option('--layout', '-l', action='store', dest='layout', default='dot',
                    help='Layout to be used by GraphViz for visualization. Layouts: circo dot fdp neato nop nop1 nop2 twopi'),
        make_option('--verbose-names', '-n', action='store_true', dest='verbose_names',
                    help='Use verbose_name of models and fields'),
        make_option('--language', '-L', action='store', dest='language',
                    help='Specify language used for verbose_name localization'),
        make_option('--exclude-columns', '-x', action='store', dest='exclude_columns',
                    help='Exclude specific column(s) from the graph. Can also load exclude list from file.'),
        make_option('--exclude-models', '-X', action='store', dest='exclude_models',
                    help='Exclude specific model(s) from the graph. Can also load exclude list from file.'),
        make_option('--inheritance', '-e', action='store_true', dest='inheritance',
                    help='Include inheritance arrows'),
    )

    help = ("Creates a GraphViz dot file for the specified app names.  You can pass multiple app names and they will all be combined into a single model.  Output is usually directed to a dot file.")
    args = "[appname]"
    label = 'application name'

    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        if len(args) < 1 and not options['all_applications']:
            raise CommandError("need one or more arguments for appname")

        use_pygraphviz = options.get('pygraphviz', False)
        use_pydot = options.get('pydot', False)
        dotdata = generate_dot(args, **options)
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

    def print_output(self, dotdata):
        print(dotdata.encode('utf-8'))

    def render_output_pygraphviz(self, dotdata, **kwargs):
        """Renders the image using pygraphviz"""
        if not HAS_PYGRAPHVIZ:
            raise CommandError("You need to install pygraphviz python module")

        vizdata = ' '.join(dotdata.split("\n")).strip().encode('utf-8')
        version = pygraphviz.__version__.rstrip("-svn")
        try:
            if tuple(int(v) for v in version.split('.')) < (0, 36):
                # HACK around old/broken AGraph before version 0.36 (ubuntu ships with this old version)
                import tempfile
                tmpfile = tempfile.NamedTemporaryFile()
                tmpfile.write(vizdata)
                tmpfile.seek(0)
                vizdata = tmpfile.name
        except ValueError:
            pass

        graph = pygraphviz.AGraph(vizdata)
        graph.layout(prog=kwargs['layout'])
        graph.draw(kwargs['outputfile'])

    def render_output_pydot(self, dotdata, **kwargs):
        """Renders the image using pydot"""
        if not HAS_PYDOT:
            raise CommandError("You need to install pydot python module")

        vizdata = ' '.join(dotdata.split("\n")).strip().encode('utf-8')
        graph = pydot.graph_from_dot_data(vizdata)
        output_file = kwargs['outputfile']
        formats = ['bmp', 'canon', 'cmap', 'cmapx', 'cmapx_np', 'dot', 'dia', 'emf',
                   'em', 'fplus', 'eps', 'fig', 'gd', 'gd2', 'gif', 'gv', 'imap',
                   'imap_np', 'ismap', 'jpe', 'jpeg', 'jpg', 'metafile', 'pdf',
                   'pic', 'plain', 'plain-ext', 'png', 'pov', 'ps', 'ps2', 'svg',
                   'svgz', 'tif', 'tiff', 'tk', 'vml', 'vmlz', 'vrml', 'wbmp', 'xdot']
        ext = output_file[output_file.rfind('.') + 1:]
        format = ext if ext in formats else 'raw'
        graph.write(output_file, format=format)
