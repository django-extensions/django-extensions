# -*- coding: utf-8 -*-
import os
import six
import sys
import time
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.backends import utils
from django.utils.datastructures import OrderedSet
from six import PY3

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
    extra_args = None
    tests_mode = False

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--plain', action='store_true', dest='plain',
            default=False,
            help='Tells Django to use plain Python, not BPython nor IPython.'
        )
        parser.add_argument(
            '--bpython', action='store_true', dest='bpython',
            default=False,
            help='Tells Django to use BPython, not IPython.'
        )
        parser.add_argument(
            '--ptpython', action='store_true', dest='ptpython',
            default=False,
            help='Tells Django to use PTPython, not IPython.'
        )
        parser.add_argument(
            '--ptipython', action='store_true', dest='ptipython',
            default=False,
            help='Tells Django to use PT-IPython, not IPython.'
        )
        parser.add_argument(
            '--ipython', action='store_true', dest='ipython',
            default=False,
            help='Tells Django to use IPython, not BPython.'
        )
        parser.add_argument(
            '--notebook', action='store_true', dest='notebook',
            default=False,
            help='Tells Django to use IPython Notebook.'
        )
        parser.add_argument(
            '--kernel', action='store_true', dest='kernel',
            default=False,
            help='Tells Django to start an IPython Kernel.'
        )
        parser.add_argument(
            '--connection-file', action='store', dest='connection_file',
            help='Specifies the connection file to use if using the --kernel option'
        )
        parser.add_argument(
            '--no-startup', action='store_true', dest='no_startup',
            default=False,
            help='When using plain Python, ignore the PYTHONSTARTUP environment variable and ~/.pythonrc.py script.'
        )
        parser.add_argument(
            '--use-pythonrc', action='store_true', dest='use_pythonrc',
            default=False,
            help='When using plain Python, load the PYTHONSTARTUP environment variable and ~/.pythonrc.py script.'
        )
        parser.add_argument(
            '--print-sql', action='store_true',
            default=False,
            help="Print SQL queries as they're executed"
        )
        parser.add_argument(
            '--dont-load', action='append', dest='dont_load', default=[],
            help='Ignore autoloading of some apps/models. Can be used several times.'
        )
        parser.add_argument(
            '--quiet-load', action='store_true',
            default=False,
            dest='quiet_load', help='Do not display loaded models messages'
        )
        parser.add_argument(
            '--vi', action='store_true', default=use_vi_mode(), dest='vi_mode',
            help='Load Vi key bindings (for --ptpython and --ptipython)'
        )
        parser.add_argument(
            '--no-browser', action='store_true',
            default=False,
            dest='no_browser',
            help='Don\'t open the notebook in a browser after startup.'
        )

    def run_from_argv(self, argv):
        if '--' in argv[2:]:
            idx = argv.index('--')
            self.extra_args = argv[idx + 1:]
            argv = argv[:idx]
        return super(Command, self).run_from_argv(argv)

    def get_ipython_arguments(self, options):
        if self.extra_args:
            return self.extra_args
        ipython_args = 'IPYTHON_ARGUMENTS'
        arguments = getattr(settings, ipython_args, [])
        if not arguments:
            arguments = os.environ.get(ipython_args, '').split()
        return arguments

    def get_notebook_arguments(self, options):
        if self.extra_args:
            return self.extra_args
        notebook_args = 'NOTEBOOK_ARGUMENTS'
        arguments = getattr(settings, notebook_args, [])
        if not arguments:
            arguments = os.environ.get(notebook_args, '').split()
        return arguments

    def get_imported_objects(self, options):
        imported_objects = import_objects(options, self.style)
        if self.tests_mode:
            # save imported objects so we can run tests against it later
            self.tests_imported_objects = imported_objects
        return imported_objects

    def get_kernel(self, options):
        try:
            from IPython import release
            if release.version_info[0] < 2:
                print(self.style.ERROR("--kernel requires at least IPython version 2.0"))
                return
            from IPython import start_kernel
        except ImportError:
            return traceback.format_exc()

        def run_kernel():
            imported_objects = self.get_imported_objects(options)
            kwargs = dict(
                argv=[],
                user_ns=imported_objects,
            )
            connection_file = options['connection_file']
            if connection_file:
                kwargs['connection_file'] = connection_file
            start_kernel(**kwargs)
        return run_kernel

    def get_notebook(self, options):
        from IPython import release
        try:
            from notebook.notebookapp import NotebookApp
        except ImportError:
            if release.version_info[0] >= 7:
                raise
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

        no_browser = options['no_browser']

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
                except Exception:
                    continue
            if not ks:
                raise CommandError("No notebook (Python) kernel specs found")
            ks.argv.extend(ipython_arguments)
            ks.display_name = display_name

            manage_py_dir, manage_py = os.path.split(os.path.realpath(sys.argv[0]))

            if manage_py == 'manage.py' and os.path.isdir(manage_py_dir) and manage_py_dir != os.getcwd():
                pythonpath = ks.env.get('PYTHONPATH', os.environ.get('PYTHONPATH', ''))
                pythonpath = pythonpath.split(os.pathsep)
                if manage_py_dir not in pythonpath:
                    pythonpath.append(manage_py_dir)

                ks.env['PYTHONPATH'] = os.pathsep.join(filter(None, pythonpath))

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
            if '--notebook-dir' not in notebook_arguments and not any(e.startswith('--notebook-dir=') for e in notebook_arguments):
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

    def get_plain(self, options):
        # Using normal Python shell
        import code
        imported_objects = self.get_imported_objects(options)
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
            # Enable tab completion on systems using libedit (e.g. macOS).
            # These lines are copied from Lib/site.py on Python 3.4.
            readline_doc = getattr(readline, '__doc__', '')
            if readline_doc is not None and 'libedit' in readline_doc:
                readline.parse_and_bind("bind ^I rl_complete")
            else:
                readline.parse_and_bind("tab:complete")

        use_pythonrc = options['use_pythonrc']
        no_startup = options['no_startup']

        # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
        # conventions and get $PYTHONSTARTUP first then .pythonrc.py.
        if use_pythonrc or not no_startup:
            for pythonrc in OrderedSet([os.environ.get("PYTHONSTARTUP"), os.path.expanduser('~/.pythonrc.py')]):
                if not pythonrc:
                    continue
                if not os.path.isfile(pythonrc):
                    continue
                with open(pythonrc) as handle:
                    pythonrc_code = handle.read()
                # Match the behavior of the cpython shell where an error in
                # PYTHONSTARTUP prints an exception and continues.
                try:
                    exec(compile(pythonrc_code, pythonrc, 'exec'), imported_objects)
                except Exception:
                    traceback.print_exc()
                    if self.tests_mode:
                        raise

        def run_plain():
            code.interact(local=imported_objects)
        return run_plain

    def get_bpython(self, options):
        try:
            from bpython import embed
        except ImportError:
            return traceback.format_exc()

        def run_bpython():
            imported_objects = self.get_imported_objects(options)
            kwargs = {}
            if self.extra_args:
                kwargs['args'] = self.extra_args
            embed(imported_objects, **kwargs)
        return run_bpython

    def get_ipython(self, options):
        try:
            from IPython import start_ipython

            def run_ipython():
                imported_objects = self.get_imported_objects(options)
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
                imported_objects = self.get_imported_objects(options)
                shell = IPShell(argv=[], user_ns=imported_objects)
                shell.mainloop()
            return run_ipython

    def get_ptpython(self, options):
        try:
            from ptpython.repl import embed, run_config
        except ImportError:
            tb = traceback.format_exc()
            try:  # prompt_toolkit < v0.27
                from prompt_toolkit.contrib.repl import embed, run_config
            except ImportError:
                return tb

        def run_ptpython():
            imported_objects = self.get_imported_objects(options)
            history_filename = os.path.expanduser('~/.ptpython_history')
            embed(globals=imported_objects, history_filename=history_filename,
                  vi_mode=options['vi_mode'], configure=run_config)
        return run_ptpython

    def get_ptipython(self, options):
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
            imported_objects = self.get_imported_objects(options)
            history_filename = os.path.expanduser('~/.ptpython_history')
            embed(user_ns=imported_objects, history_filename=history_filename,
                  vi_mode=options['vi_mode'], configure=run_config)
        return run_ptipython

    def set_application_name(self, options):
        """Set the application_name on PostgreSQL connection

        Use the fallback_application_name to let the user override
        it with PGAPPNAME env variable

        http://www.postgresql.org/docs/9.4/static/libpq-connect.html#LIBPQ-PARAMKEYWORDS  # noqa
        """
        supported_backends = ['django.db.backends.postgresql',
                              'django.db.backends.postgresql_psycopg2']
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

    @signalcommand
    def handle(self, *args, **options):
        use_kernel = options['kernel']
        use_notebook = options['notebook']
        use_ipython = options['ipython']
        use_bpython = options['bpython']
        use_plain = options['plain']
        use_ptpython = options['ptpython']
        use_ptipython = options['ptipython']
        verbosity = options["verbosity"]
        print_sql = getattr(settings, 'SHELL_PLUS_PRINT_SQL', False)
        truncate = getattr(settings, 'SHELL_PLUS_PRINT_SQL_TRUNCATE', 1000)

        if options["print_sql"] or print_sql:

            # Code from http://gist.github.com/118990
            try:
                import sqlparse

                sqlparse_format_kwargs_defaults = dict(
                    reindent_aligned=True,
                    truncate_strings=500,
                )
                sqlparse_format_kwargs = getattr(settings, 'SHELL_PLUS_SQLPARSE_FORMAT_KWARGS', sqlparse_format_kwargs_defaults)
            except ImportError:
                sqlparse = None

            try:
                import pygments.lexers
                import pygments.formatters

                pygments_formatter = getattr(settings, 'SHELL_PLUS_PYGMENTS_FORMATTER', pygments.formatters.TerminalFormatter)
                pygments_formatter_kwargs = getattr(settings, 'SHELL_PLUS_PYGMENTS_FORMATTER_KWARGS', {})
            except ImportError:
                pygments = None

            class PrintQueryWrapper(utils.CursorDebugWrapper):
                def execute(self, sql, params=()):
                    starttime = time.time()
                    try:
                        return utils.CursorWrapper.execute(self, sql, params)
                    finally:
                        execution_time = time.time() - starttime
                        raw_sql = self.db.ops.last_executed_query(self.cursor, sql, params)

                        if sqlparse:
                            raw_sql = raw_sql[:truncate]
                            raw_sql = sqlparse.format(raw_sql, **sqlparse_format_kwargs)

                        if pygments:
                            raw_sql = pygments.highlight(
                                raw_sql,
                                pygments.lexers.get_lexer_by_name("sql"),
                                pygments_formatter(**pygments_formatter_kwargs),
                            )

                        print(raw_sql)
                        print("")
                        print('Execution time: %.6fs [Database: %s]' % (execution_time, self.db.alias))
                        print("")

            utils.CursorDebugWrapper = PrintQueryWrapper

        shells = (
            ('ptipython', self.get_ptipython),
            ('ptpython', self.get_ptpython),
            ('bpython', self.get_bpython),
            ('ipython', self.get_ipython),
            ('plain', self.get_plain),
        )
        SETTINGS_SHELL_PLUS = getattr(settings, 'SHELL_PLUS', None)

        shell = None
        shell_name = "any"
        self.set_application_name(options)
        if use_kernel:
            shell = self.get_kernel(options)
            shell_name = "IPython Kernel"
        elif use_notebook:
            shell = self.get_notebook(options)
            shell_name = "IPython Notebook"
        elif use_plain:
            shell = self.get_plain(options)
            shell_name = "plain"
        elif use_ipython:
            shell = self.get_ipython(options)
            shell_name = "IPython"
        elif use_bpython:
            shell = self.get_bpython(options)
            shell_name = "BPython"
        elif use_ptpython:
            shell = self.get_ptpython(options)
            shell_name = "ptpython"
        elif use_ptipython:
            shell = self.get_ptipython(options)
            shell_name = "ptipython"
        elif SETTINGS_SHELL_PLUS:
            shell_name = SETTINGS_SHELL_PLUS
            shell = dict(shells)[shell_name](options)
        else:
            for shell_name, func in shells:
                if verbosity > 2:
                    print(self.style.NOTICE("Trying shell: %s" % shell_name))
                shell = func(options)
                if callable(shell):
                    if verbosity > 1:
                        print(self.style.NOTICE("Using shell: %s" % shell_name))
                    break

        if not callable(shell):
            if shell:
                print(shell)
            print(self.style.ERROR("Could not load %s interactive Python environment." % shell_name))
            return

        if self.tests_mode:
            return 130

        shell()
