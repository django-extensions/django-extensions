import os
from django.core.management.base import NoArgsCommand
from django_extensions.management.shells import import_objects
from optparse import make_option
import time


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--ipython', action='store_true', dest='ipython',
            help='Tells Django to use IPython, not BPython.'),
        make_option('--notebook', action='store_true', dest='notebook',
            help='Tells Django to use IPython Notebook.'),
        make_option('--plain', action='store_true', dest='plain',
            help='Tells Django to use plain Python, not BPython nor IPython.'),
        make_option('--no-pythonrc', action='store_true', dest='no_pythonrc',
            help='Tells Django to use plain Python, not IPython.'),
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
        use_notebook = options.get('notebook', False)
        use_ipython = options.get('ipython', use_notebook)
        use_plain = options.get('plain', False)
        use_pythonrc = not options.get('no_pythonrc', True)

        if options.get("print_sql", False):
            # Code from http://gist.github.com/118990
            from django.db.backends import util
            try:
                import sqlparse
            except ImportError:
                sqlparse = None

            class PrintQueryWrapper(util.CursorDebugWrapper):
                def execute(self, sql, params=()):
                    starttime = time.time()
                    try:
                        return self.cursor.execute(sql, params)
                    finally:
                        raw_sql = self.db.ops.last_executed_query(self.cursor, sql, params)
                        execution_time = time.time() - starttime
                        if sqlparse:
                            print sqlparse.format(raw_sql, reindent=True)
                        else:
                            print raw_sql
                        print
                        print 'Execution time: %.6fs [Database: %s]' % (execution_time, self.db.alias)
                        print

            util.CursorDebugWrapper = PrintQueryWrapper

        # Set up a dictionary to serve as the environment for the shell, so
        # that tab completion works on objects that are imported at runtime.
        # See ticket 5082.
        try:
            if use_plain:
                # Don't bother loading B/IPython, because the user wants plain Python.
                raise ImportError
            try:
                if use_ipython:
                    # User wants IPython
                    raise ImportError
                from bpython import embed
                imported_objects = import_objects(options, self.style)
                embed(imported_objects)
            except ImportError:
                try:
                    if use_notebook:
                        from django.conf import settings
                        from IPython.frontend.html.notebook import notebookapp
                        app = notebookapp.NotebookApp.instance()
                        ipython_arguments = getattr(
                            settings,
                            'IPYTHON_ARGUMENTS',
                            ['--ext',
                             'django_extensions.management.notebook_extension'])
                        app.initialize(ipython_arguments)
                        app.start()
                    else:
                        from IPython import embed
                        imported_objects = import_objects(options, self.style)
                        embed(user_ns=imported_objects)
                except ImportError:
                    # IPython < 0.11
                    # Explicitly pass an empty list as arguments, because otherwise
                    # IPython would use sys.argv from this script.
                    # Notebook not supported for IPython < 0.11.
                    try:
                        from IPython.Shell import IPShell
                        imported_objects = import_objects(options, self.style)
                        shell = IPShell(argv=[], user_ns=imported_objects)
                        shell.mainloop()
                    except ImportError:
                        # IPython not found at all, raise ImportError
                        raise
        except ImportError:
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
                    try:
                        execfile(pythonrc)
                    except NameError:
                        pass
                # This will import .pythonrc.py as a side-effect
                import user
            code.interact(local=imported_objects)
