# -*- coding: utf-8 -*-
import inspect
import os
import sys
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.datastructures import OrderedSet

from django_extensions.management.shells import import_objects
from django_extensions.management.utils import signalcommand
from django_extensions.management.debug_cursor import monkey_patch_cursordebugwrapper


def use_vi_mode():
    editor = os.environ.get('EDITOR')
    if not editor:
        return False
    editor = os.path.basename(editor)
    return editor.startswith('vi') or editor.endswith('vim')


def shell_runner(flags, name, help=None):
    """
    Decorates methods with information about the application they are starting

    :param flags: The flags used to start this runner via the ArgumentParser.
    :param name: The name of this runner for the help text for the ArgumentParser.
    :param help: The optional help for the ArgumentParser if the dynamically generated help is not sufficient.
    """

    def decorator(fn):
        fn.runner_flags = flags
        fn.runner_name = name
        fn.runner_help = help

        return fn

    return decorator


class Command(BaseCommand):
    help = "Like the 'shell' command but autoloads the models of all installed Django apps."
    extra_args = None
    tests_mode = False

    def __init__(self):
        super().__init__()
        self.runners = [member for name, member in inspect.getmembers(self)
                        if hasattr(member, 'runner_flags')]

    def add_arguments(self, parser):
        super().add_arguments(parser)

        group = parser.add_mutually_exclusive_group()
        for runner in self.runners:
            if runner.runner_help:
                help = runner.runner_help
            else:
                help = 'Tells Django to use %s.' % runner.runner_name

            group.add_argument(
                *runner.runner_flags, action='store_const', dest='runner', const=runner, help=help)

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
            '--print-sql-location', action='store_true',
            default=False,
            help="Show location in code where SQL query generated from"
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
        parser.add_argument(
            '-c', '--command',
            help='Instead of opening an interactive shell, run a command as Django and exit.',
        )

    def run_from_argv(self, argv):
        if '--' in argv[2:]:
            idx = argv.index('--')
            self.extra_args = argv[idx + 1:]
            argv = argv[:idx]
        return super().run_from_argv(argv)

    def get_ipython_arguments(self, options):
        ipython_args = 'IPYTHON_ARGUMENTS'
        arguments = getattr(settings, ipython_args, [])
        if not arguments:
            arguments = os.environ.get(ipython_args, '').split()
        return arguments

    def get_notebook_arguments(self, options):
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

    @shell_runner(flags=['--kernel'], name='IPython Kernel')
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

    def load_base_kernel_spec(self, app):
        """Finds and returns the base Python kernelspec to extend from."""
        ksm = app.kernel_spec_manager
        try_spec_names = getattr(settings, 'NOTEBOOK_KERNEL_SPEC_NAMES', [
            'python3',
            'python',
        ])

        if isinstance(try_spec_names, str):
            try_spec_names = [try_spec_names]

        ks = None
        for spec_name in try_spec_names:
            try:
                ks = ksm.get_kernel_spec(spec_name)
                break
            except Exception:
                continue
        if not ks:
            raise CommandError("No notebook (Python) kernel specs found. Tried %r" % try_spec_names)

        return ks

    def generate_kernel_specs(self, app, ipython_arguments):
        """Generate an IPython >= 3.0 kernelspec that loads django extensions"""
        ks = self.load_base_kernel_spec(app)
        ks.argv.extend(ipython_arguments)
        ks.display_name = getattr(settings, 'IPYTHON_KERNEL_DISPLAY_NAME', "Django Shell-Plus")

        manage_py_dir, manage_py = os.path.split(os.path.realpath(sys.argv[0]))
        if manage_py == 'manage.py' and os.path.isdir(manage_py_dir):
            pythonpath = ks.env.get('PYTHONPATH', os.environ.get('PYTHONPATH', ''))
            pythonpath = pythonpath.split(os.pathsep)
            if manage_py_dir not in pythonpath:
                pythonpath.append(manage_py_dir)

            ks.env['PYTHONPATH'] = os.pathsep.join(filter(None, pythonpath))

        return {'django_extensions': ks}

    def run_notebookapp(self, app, options, use_kernel_specs=True):
        no_browser = options['no_browser']

        if self.extra_args:
            # if another '--' is found split the arguments notebook, ipython
            if '--' in self.extra_args:
                idx = self.extra_args.index('--')
                notebook_arguments = self.extra_args[:idx]
                ipython_arguments = self.extra_args[idx + 1:]
            # otherwise pass the arguments to the notebook
            else:
                notebook_arguments = self.extra_args
                ipython_arguments = []
        else:
            notebook_arguments = self.get_notebook_arguments(options)
            ipython_arguments = self.get_ipython_arguments(options)

        # Treat IPYTHON_ARGUMENTS from settings
        if 'django_extensions.management.notebook_extension' not in ipython_arguments:
            ipython_arguments.extend(['--ext', 'django_extensions.management.notebook_extension'])

        # Treat NOTEBOOK_ARGUMENTS from settings
        if no_browser and '--no-browser' not in notebook_arguments:
            notebook_arguments.append('--no-browser')
        if '--notebook-dir' not in notebook_arguments and not any(e.startswith('--notebook-dir=') for e in notebook_arguments):
            notebook_arguments.extend(['--notebook-dir', '.'])

        # IPython < 3 passes through kernel args from notebook CLI
        if not use_kernel_specs:
            notebook_arguments.extend(ipython_arguments)

        app.initialize(notebook_arguments)

        # IPython >= 3 uses kernelspecs to specify kernel CLI args
        if use_kernel_specs:
            ksm = app.kernel_spec_manager
            for kid, ks in self.generate_kernel_specs(app, ipython_arguments).items():
                roots = [os.path.dirname(ks.resource_dir), ksm.user_kernel_dir]
                success = False
                for root in roots:
                    kernel_dir = os.path.join(root, kid)
                    try:
                        if not os.path.exists(kernel_dir):
                            os.makedirs(kernel_dir)

                        with open(os.path.join(kernel_dir, 'kernel.json'), 'w') as f:
                            f.write(ks.to_json())

                        success = True
                        break
                    except OSError:
                        continue

                if not success:
                    raise CommandError("Could not write kernel %r in directories %r" % (kid, roots))

        app.start()

    @shell_runner(flags=['--notebook'], name='IPython Notebook')
    def get_notebook(self, options):
        try:
            from IPython import release
        except ImportError:
            return traceback.format_exc()
        try:
            from notebook.notebookapp import NotebookApp
        except ImportError:
            if release.version_info[0] >= 7:
                return traceback.format_exc()
            try:
                from IPython.html.notebookapp import NotebookApp
            except ImportError:
                if release.version_info[0] >= 3:
                    return traceback.format_exc()
                try:
                    from IPython.frontend.html.notebook import notebookapp
                    NotebookApp = notebookapp.NotebookApp
                except ImportError:
                    return traceback.format_exc()

        use_kernel_specs = release.version_info[0] >= 3

        def run_notebook():
            app = NotebookApp.instance()
            self.run_notebookapp(app, options, use_kernel_specs)

        return run_notebook

    @shell_runner(flags=['--lab'], name='JupyterLab Notebook')
    def get_jupyterlab(self, options):
        try:
            from jupyterlab.labapp import LabApp
        except ImportError:
            return traceback.format_exc()

        def run_jupyterlab():
            app = LabApp.instance()
            self.run_notebookapp(app, options)

        return run_jupyterlab

    @shell_runner(flags=['--plain'], name='plain Python')
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

    @shell_runner(flags=['--bpython'], name='BPython')
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

    @shell_runner(flags=['--ipython'], name='IPython')
    def get_ipython(self, options):
        try:
            from IPython import start_ipython

            def run_ipython():
                imported_objects = self.get_imported_objects(options)
                ipython_arguments = self.extra_args or self.get_ipython_arguments(options)
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

    @shell_runner(flags=['--ptpython'], name='PTPython')
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

    @shell_runner(flags=['--ptipython'], name='PT-IPython')
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

    @shell_runner(flags=['--idle'], name='Idle')
    def get_idle(self, options):
        from idlelib.pyshell import main

        def run_idle():
            sys.argv = [
                sys.argv[0],
                '-c',
                """
from django_extensions.management import shells
from django.core.management.color import no_style
for k, m in shells.import_objects({}, no_style()).items():
    globals()[k] = m
""",
            ]
            main()

        return run_idle

    def set_application_name(self, options):
        """
        Set the application_name on PostgreSQL connection

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
        verbosity = options["verbosity"]
        get_runner = options['runner']
        print_sql = getattr(settings, 'SHELL_PLUS_PRINT_SQL', False)
        runner = None
        runner_name = None

        with monkey_patch_cursordebugwrapper(print_sql=options["print_sql"] or print_sql, print_sql_location=options["print_sql_location"], confprefix="SHELL_PLUS"):
            SETTINGS_SHELL_PLUS = getattr(settings, 'SHELL_PLUS', None)

            def get_runner_by_flag(flag):
                for runner in self.runners:
                    if flag in runner.runner_flags:
                        return runner
                return None

            self.set_application_name(options)

            if not get_runner and SETTINGS_SHELL_PLUS:
                get_runner = get_runner_by_flag('--%s' % SETTINGS_SHELL_PLUS)
                if not get_runner:
                    runner = None
                    runner_name = SETTINGS_SHELL_PLUS

            if get_runner:
                runner = get_runner(options)
                runner_name = get_runner.runner_name
            else:
                def try_runner(get_runner):
                    runner_name = get_runner.runner_name
                    if verbosity > 2:
                        print(self.style.NOTICE("Trying: %s" % runner_name))

                    runner = get_runner(options)
                    if callable(runner):
                        if verbosity > 1:
                            print(self.style.NOTICE("Using: %s" % runner_name))
                        return runner
                    return None

                tried_runners = set()

                # try the runners that are least unexpected (normal shell runners)
                preferred_runners = ['ptipython', 'ptpython', 'bpython', 'ipython', 'plain']
                for flag_suffix in preferred_runners:
                    get_runner = get_runner_by_flag('--%s' % flag_suffix)
                    tried_runners.add(get_runner)
                    runner = try_runner(get_runner)
                    if runner:
                        runner_name = get_runner.runner_name
                        break

                # try any remaining runners if needed
                if not runner:
                    for get_runner in self.runners:
                        if get_runner not in tried_runners:
                            runner = try_runner(get_runner)
                            if runner:
                                runner_name = get_runner.runner_name
                                break

            if not callable(runner):
                if runner:
                    print(runner)
                if not runner_name:
                    raise CommandError("No shell runner could be found.")
                raise CommandError("Could not load shell runner: '%s'." % runner_name)

            if self.tests_mode:
                return 130

            if options['command']:
                imported_objects = self.get_imported_objects(options)
                exec(options['command'], {}, imported_objects)
                return

            runner()
