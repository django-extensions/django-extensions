import os
import six
import time
import traceback
from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.conf import settings

from django_extensions.management.shells import import_objects


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--plain', action='store_true', dest='plain',
                    help='Tells Django to use plain Python, not BPython nor IPython.'),
        make_option('--bpython', action='store_true', dest='bpython',
                    help='Tells Django to use BPython, not IPython.'),
        make_option('--ipython', action='store_true', dest='ipython',
                    help='Tells Django to use IPython, not BPython.'),
        make_option('--notebook', action='store_true', dest='notebook',
                    help='Tells Django to use IPython Notebook.'),
        make_option('--kernel', action='store_true', dest='kernel',
                    help='Tells Django to start an IPython Kernel.'),
        make_option('--use-pythonrc', action='store_true', dest='use_pythonrc',
                    help='Tells Django to execute PYTHONSTARTUP file (BE CAREFULL WITH THIS!)'),
        make_option('--print-sql', action='store_true', default=False,
                    help="Print SQL queries as they're executed"),
        make_option('--dont-load', action='append', dest='dont_load', default=[],
                    help='Ignore autoloading of some apps/models. Can be used several times.'),
        make_option('--quiet-load', action='store_true', default=False, dest='quiet_load',
                    help='Do not display loaded models messages'),
    )
    help = "Like the 'shell' command but autoloads the models of all installed Django apps."

    requires_model_validation = True

    def handle_noargs(self, **options):
        use_kernel = options.get('kernel', False)
        use_notebook = options.get('notebook', False)
        use_ipython = options.get('ipython', False)
        use_bpython = options.get('bpython', False)
        use_plain = options.get('plain', False)
        use_pythonrc = options.get('use_pythonrc', True)

        if options.get("print_sql", False):
            # Code from http://gist.github.com/118990
            try:
                # Django 1.7 onwards
                from django.db.backends import utils
            except ImportError:
                # Django 1.6 and below
                from django.db.backends import util as utils

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
                from IPython import embed_kernel
            except ImportError:
                return traceback.format_exc()

            def run_kernel():
                imported_objects = import_objects(options, self.style)
                embed_kernel(local_ns=imported_objects)
            return run_kernel

        def get_notebook():
            from django.conf import settings
            try:
                from IPython.html.notebookapp import NotebookApp
            except ImportError:
                try:
                    from IPython.frontend.html.notebook import notebookapp
                    NotebookApp = notebookapp.NotebookApp
                except ImportError:
                    return traceback.format_exc()

            def run_notebook():
                app = NotebookApp.instance()
                ipython_arguments = getattr(settings, 'IPYTHON_ARGUMENTS', ['--ext', 'django_extensions.management.notebook_extension'])
                app.initialize(ipython_arguments)
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
                from IPython import embed
                def run_ipython():
                    imported_objects = import_objects(options, self.style)
                    embed(user_ns=imported_objects)
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

        shells = (
            ('bpython', get_bpython),
            ('ipython', get_ipython),
            ('plain', get_plain),
        )
        SETTINGS_SHELL_PLUS = getattr(settings, 'SHELL_PLUS', None)

        shell = None
        shell_name = "any"
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
        elif SETTINGS_SHELL_PLUS:
            shell_name = SETTINGS_SHELL_PLUS
            shell = dict(shells)[shell_name]()
        else:
            for shell_name, func in shells:
                shell = func()
                if shell:
                    break

        if not callable(shell):
            if shell:
                print shell
            print(self.style.ERROR("Could not load %s interactive Python environment." % shell_name))
            return

        shell()
