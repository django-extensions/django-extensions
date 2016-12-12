# -*- coding: utf-8 -*-
import os
import six
import sys
import time
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.backends import utils
from django.utils.six import PY3

from django_extensions.management.shells import import_objects
from django_extensions.management.utils import signalcommand


def use_vi_mode():
    editor = os.environ.get('EDITOR')
    if not editor:
        return False
    editor = os.path.basename(editor)
    return editor.startswith('vi') or editor.endswith('vim')


class Command(BaseCommand):
    help = "Like the 'shell' command but autoloads the models of all installed Django apps."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--plain', action='store_true', dest='plain',
            help='Tells Django to use plain Python, not BPython nor IPython.')
        parser.add_argument(
            '--bpython', action='store_true', dest='bpython',
            help='Tells Django to use BPython, not IPython.')
        parser.add_argument(
            '--ptpython', action='store_true', dest='ptpython',
            help='Tells Django to use PTPython, not IPython.')
        parser.add_argument(
            '--ptipython', action='store_true', dest='ptipython',
            help='Tells Django to use PT-IPython, not IPython.')
        parser.add_argument(
            '--ipython', action='store_true', dest='ipython',
            help='Tells Django to use IPython, not BPython.')
        parser.add_argument(
            '--notebook', action='store_true', dest='notebook',
            help='Tells Django to use IPython Notebook.')
        parser.add_argument(
            '--kernel', action='store_true', dest='kernel',
            help='Tells Django to start an IPython Kernel.')
        parser.add_argument('--connection-file', action='store', dest='connection_file',
            help='Specifies the connection file to use if using the --kernel option'),
        parser.add_argument(
            '--use-pythonrc', action='store_true', dest='use_pythonrc',
            help='Tells Django to execute PYTHONSTARTUP file '
            '(BE CAREFULL WITH THIS!)')
        parser.add_argument(
            '--print-sql', action='store_true', default=False,
            help="Print SQL queries as they're executed")
        parser.add_argument(
            '--dont-load', action='append', dest='dont_load', default=[],
            help='Ignore autoloading of some apps/models. Can be used '
            'several times.')
        parser.add_argument(
            '--quiet-load', action='store_true', default=False,
            dest='quiet_load', help='Do not display loaded models messages')
        parser.add_argument(
            '--vi', action='store_true', default=use_vi_mode(), dest='vi_mode',
            help='Load Vi key bindings (for --ptpython and --ptipython)')
        parser.add_argument(
            '--no-browser', action='store_true', default=False,
            dest='no_browser',
            help='Don\'t open the notebook in a browser after startup.')

    def get_ipython_arguments(self, options):
        return getattr(settings, 'IPYTHON_ARGUMENTS', [])

    def get_notebook_arguments(self, options):
        notebook_args = 'NOTEBOOK_ARGUMENTS'
        arguments = getattr(settings, notebook_args, [])
        if not arguments:
            arguments = os.environ.get(notebook_args, '').split()
        return arguments

    @signalcommand
    def handle(self, *args, **options):
        use_kernel = options.get('kernel', False)
        use_notebook = options.get('notebook', False)
        use_ipython = options.get('ipython', False)
        use_bpython = options.get('bpython', False)
        use_plain = options.get('plain', False)
        use_ptpython = options.get('ptpython', False)
        use_ptipython = options.get('ptipython', False)
        use_pythonrc = options.get('use_pythonrc', True)
        no_browser = options.get('no_browser', False)
        verbosity = int(options.get('verbosity', 1))
        print_sql = getattr(settings, 'SHELL_PLUS_PRINT_SQL', False)

        if options.get("print_sql", False) or print_sql:

            # Code from http://gist.github.com/118990
            sqlparse = None
            try:
                import sqlparse
            except ImportError:
                pass

            class PrintQueryWrapper(utils.CursorDebugWrapper):
                def execute(self, sql, params=()):
                    starttime = time.time()
                    try:
                        return self.cursor.execute(sql, params)
                    finally:
                        execution_time = time.time() - starttime
                        raw_sql = self.db.ops.last_executed_query(self.cursor, sql, params)
                        if sqlparse:
                            print(sqlparse.format(raw_sql, reindent=True))
                        else:
                            print(raw_sql)
                        print("")
                        print('Execution time: %.6fs [Database: %s]' % (execution_time, self.db.alias))
                        print("")

            utils.CursorDebugWrapper = PrintQueryWrapper

        def get_kernel():
            try:
                from IPython import release
                if release.version_info[0] < 2:
                    print(self.style.ERROR("--kernel requires at least IPython version 2.0"))
                    return
                from IPython import start_kernel
            except ImportError:
                return traceback.format_exc()

            def run_kernel():
                imported_objects = import_objects(options, self.style)
                kwargs = dict(
                    argv=[],
                    user_ns=imported_objects,
                )
                connection_file = options.get('connection_file')
                if connection_file:
                    kwargs['connection_file'] = connection_file
                start_kernel(**kwargs)
            return run_kernel

        def get_notebook():
            from IPython import release
            try:
                from notebook.notebookapp import NotebookApp
            except ImportError:
                try:
                    from IPython.html.notebookapp import NotebookApp
                except ImportError:
                    if release.version_info[0] >= 3:
                        raise
                    try:
                        from IPython.frontend.html.notebook import notebookapp
                        NotebookApp = notebookapp.NotebookApp
                    except ImportError:
                        return traceback.format_exc()

            def install_kernel_spec(app, display_name, ipython_arguments):
                """install an IPython >= 3.0 kernelspec that loads django extensions"""
                ksm = app.kernel_spec_manager
                try_spec_names = getattr(settings, 'NOTEBOOK_KERNEL_SPEC_NAMES', [
                    'python3' if PY3 else 'python2',
                    'python',
                ])
                if isinstance(try_spec_names, six.string_types):
                    try_spec_names = [try_spec_names]
                ks = None
                for spec_name in try_spec_names:
                    try:
                        ks = ksm.get_kernel_spec(spec_name)
                        break
                    except:
                        continue
                if not ks:
                    raise CommandError("No notebook (Python) kernel specs found")
                ks.argv.extend(ipython_arguments)
                ks.display_name = display_name

                manage_py_dir, manage_py = os.path.split(os.path.realpath(sys.argv[0]))

                if manage_py == 'manage.py' and os.path.isdir(manage_py_dir) and manage_py_dir != os.getcwd():
                    pythonpath = ks.env.get('PYTHONPATH', os.environ.get('PYTHONPATH', ''))
                    pythonpath = pythonpath.split(':')
                    if manage_py_dir not in pythonpath:
                        pythonpath.append(manage_py_dir)

                    ks.env['PYTHONPATH'] = ':'.join(filter(None, pythonpath))

                kernel_dir = os.path.join(ksm.user_kernel_dir, 'django_extensions')
                if not os.path.exists(kernel_dir):
                    os.makedirs(kernel_dir)
                with open(os.path.join(kernel_dir, 'kernel.json'), 'w') as f:
                    f.write(ks.to_json())

            def run_notebook():
                app = NotebookApp.instance()

                # Treat IPYTHON_ARGUMENTS from settings
                ipython_arguments = self.get_ipython_arguments(options)
                if 'django_extensions.management.notebook_extension' not in ipython_arguments:
                    ipython_arguments.extend(['--ext', 'django_extensions.management.notebook_extension'])

                # Treat NOTEBOOK_ARGUMENTS from settings
                notebook_arguments = self.get_notebook_arguments(options)
                if no_browser and '--no-browser' not in notebook_arguments:
                    notebook_arguments.append('--no-browser')
                if '--notebook-dir' not in notebook_arguments:
                    notebook_arguments.extend(['--notebook-dir', '.'])

                # IPython < 3 passes through kernel args from notebook CLI
                if release.version_info[0] < 3:
                    notebook_arguments.extend(ipython_arguments)

                app.initialize(notebook_arguments)

                # IPython >= 3 uses kernelspecs to specify kernel CLI args
                if release.version_info[0] >= 3:
                    display_name = getattr(settings, 'IPYTHON_KERNEL_DISPLAY_NAME', "Django Shell-Plus")
                    install_kernel_spec(app, display_name, ipython_arguments)

                app.start()
            return run_notebook

        def get_plain():
            # Using normal Python shell
            import code
            imported_objects = import_objects(options, self.style)
            try:
                # Try activating rlcompleter, because it's handy.
                import readline
            except ImportError:
                pass
            else:
                # We don't have to wrap the following import in a 'try', because
                # we already know 'readline' was imported successfully.
                import rlcompleter
                readline.set_completer(rlcompleter.Completer(imported_objects).complete)
                readline.parse_and_bind("tab:complete")

            # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
            # conventions and get $PYTHONSTARTUP first then import user.
            if use_pythonrc:
                pythonrc = os.environ.get("PYTHONSTARTUP")
                if pythonrc and os.path.isfile(pythonrc):
                    global_ns = {}
                    with open(pythonrc) as rcfile:
                        try:
                            six.exec_(compile(rcfile.read(), pythonrc, 'exec'), global_ns)
                            imported_objects.update(global_ns)
                        except NameError:
                            pass
                # This will import .pythonrc.py as a side-effect
                try:
                    import user  # NOQA
                except ImportError:
                    pass

            def run_plain():
                code.interact(local=imported_objects)
            return run_plain

        def get_bpython():
            try:
                from bpython import embed
            except ImportError:
                return traceback.format_exc()

            def run_bpython():
                imported_objects = import_objects(options, self.style)
                embed(imported_objects)
            return run_bpython

        def get_ipython():
            try:
                from IPython import start_ipython

                def run_ipython():
                    imported_objects = import_objects(options, self.style)
                    ipython_arguments = self.get_ipython_arguments(options)
                    start_ipython(argv=ipython_arguments, user_ns=imported_objects)
                return run_ipython
            except ImportError:
                str_exc = traceback.format_exc()
                # IPython < 0.11
                # Explicitly pass an empty list as arguments, because otherwise
                # IPython would use sys.argv from this script.
                # Notebook not supported for IPython < 0.11.
                try:
                    from IPython.Shell import IPShell
                except ImportError:
                    return str_exc + "\n" + traceback.format_exc()

                def run_ipython():
                    imported_objects = import_objects(options, self.style)
                    shell = IPShell(argv=[], user_ns=imported_objects)
                    shell.mainloop()
                return run_ipython

        def get_ptpython():
            try:
                from ptpython.repl import embed, run_config
            except ImportError:
                tb = traceback.format_exc()
                try:  # prompt_toolkit < v0.27
                    from prompt_toolkit.contrib.repl import embed, run_config
                except ImportError:
                    return tb

            def run_ptpython():
                imported_objects = import_objects(options, self.style)
                history_filename = os.path.expanduser('~/.ptpython_history')
                embed(globals=imported_objects, history_filename=history_filename,
                      vi_mode=options.get('vi_mode', False), configure=run_config)
            return run_ptpython

        def get_ptipython():
            try:
                from ptpython.repl import run_config
                from ptpython.ipython import embed
            except ImportError:
                tb = traceback.format_exc()
                try:  # prompt_toolkit < v0.27
                    from prompt_toolkit.contrib.repl import run_config
                    from prompt_toolkit.contrib.ipython import embed
                except ImportError:
                    return tb

            def run_ptipython():
                imported_objects = import_objects(options, self.style)
                history_filename = os.path.expanduser('~/.ptpython_history')
                embed(user_ns=imported_objects, history_filename=history_filename,
                      vi_mode=options.get('vi_mode', False), configure=run_config)
            return run_ptipython

        def set_application_name():
            """Set the application_name on PostgreSQL connection

            Use the fallback_application_name to let the user override
            it with PGAPPNAME env variable

            http://www.postgresql.org/docs/9.4/static/libpq-connect.html#LIBPQ-PARAMKEYWORDS  # noqa
            """
            supported_backends = ['django.db.backends.postgresql_psycopg2']
            opt_name = 'fallback_application_name'
            default_app_name = 'django_shell'
            app_name = default_app_name
            dbs = getattr(settings, 'DATABASES', [])

            # lookup over all the databases entry
            for db in dbs.keys():
                if dbs[db]['ENGINE'] in supported_backends:
                    try:
                        options = dbs[db]['OPTIONS']
                    except KeyError:
                        options = {}

                    # dot not override a defined value
                    if opt_name in options.keys():
                        app_name = dbs[db]['OPTIONS'][opt_name]
                    else:
                        dbs[db].setdefault('OPTIONS', {}).update({opt_name: default_app_name})
                        app_name = default_app_name

            return app_name

        shells = (
            ('ptipython', get_ptipython),
            ('ptpython', get_ptpython),
            ('bpython', get_bpython),
            ('ipython', get_ipython),
            ('plain', get_plain),
        )
        SETTINGS_SHELL_PLUS = getattr(settings, 'SHELL_PLUS', None)

        shell = None
        shell_name = "any"
        set_application_name()
        if use_kernel:
            shell = get_kernel()
            shell_name = "IPython Kernel"
        elif use_notebook:
            shell = get_notebook()
            shell_name = "IPython Notebook"
        elif use_plain:
            shell = get_plain()
            shell_name = "plain"
        elif use_ipython:
            shell = get_ipython()
            shell_name = "IPython"
        elif use_bpython:
            shell = get_bpython()
            shell_name = "BPython"
        elif use_ptpython:
            shell = get_ptpython()
            shell_name = "ptpython"
        elif use_ptipython:
            shell = get_ptipython()
            shell_name = "ptipython"
        elif SETTINGS_SHELL_PLUS:
            shell_name = SETTINGS_SHELL_PLUS
            shell = dict(shells)[shell_name]()
        else:
            for shell_name, func in shells:
                shell = func()
                if callable(shell):
                    if verbosity > 1:
                        print(self.style.NOTICE("Using shell %s." % shell_name))
                    break

        if not callable(shell):
            if shell:
                print(shell)
            print(self.style.ERROR("Could not load %s interactive Python environment." % shell_name))
            return

        shell()
