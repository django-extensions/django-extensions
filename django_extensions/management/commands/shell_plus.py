import os
from django.core.management.base import NoArgsCommand
from optparse import make_option


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--ipython', action='store_true', dest='ipython',
            help='Tells Django to use IPython, not BPython.'),
        make_option('--plain', action='store_true', dest='plain',
            help='Tells Django to use plain Python, not BPython nor IPython.'),
        make_option('--no-pythonrc', action='store_true', dest='no_pythonrc',
            help='Tells Django to use plain Python, not IPython.'),
        make_option('--print-sql', action='store_true', default=False,
            help="Print SQL queries as they're executed"),
    )
    help = "Like the 'shell' command but autoloads the models of all installed Django apps."

    requires_model_validation = True

    def handle_noargs(self, **options):
        # XXX: (Temporary) workaround for ticket #1796: force early loading of all
        # models from installed apps. (this is fixed by now, but leaving it here
        # for people using 0.96 or older trunk (pre [5919]) versions.
        from django.db.models.loading import get_models, get_apps
        loaded_models = get_models()

        use_ipython = options.get('ipython', False)
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
                    try:
                        return self.cursor.execute(sql, params)
                    finally:
                        raw_sql = self.db.ops.last_executed_query(self.cursor, sql, params)
                        if sqlparse:
                            print sqlparse.format(raw_sql, reindent=True)
                        else:
                            print raw_sql
                        print

            util.CursorDebugWrapper = PrintQueryWrapper

        # Set up a dictionary to serve as the environment for the shell, so
        # that tab completion works on objects that are imported at runtime.
        # See ticket 5082.
        from django.conf import settings
        imported_objects = {'settings': settings}
        for app_mod in get_apps():
            app_models = get_models(app_mod)
            if not app_models:
                continue
            model_labels = ", ".join([model.__name__ for model in app_models])
            print self.style.SQL_COLTYPE("From '%s' autoload: %s" % (app_mod.__name__.split('.')[-2], model_labels))
            for model in app_models:
                try:
                    imported_objects[model.__name__] = getattr(__import__(app_mod.__name__, {}, {}, model.__name__), model.__name__)
                except AttributeError, e:
                    print self.style.ERROR("Failed to import '%s' from '%s' reason: %s" % (model.__name__, app_mod.__name__.split('.')[-2], str(e)))
                    continue
        try:
            if use_plain:
                # Don't bother loading B/IPython, because the user wants plain Python.
                raise ImportError
            try:
                if use_ipython:
                    # User wants IPython
                    raise ImportError
                from bpython import embed
                embed(imported_objects)
            except ImportError:
                # Explicitly pass an empty list as arguments, because otherwise IPython
                # would use sys.argv from this script.
                try:
                    from IPython.frontend.terminal.embed import TerminalInteractiveShell
                    shell = TerminalInteractiveShell(user_ns=imported_objects)
                    shell.mainloop()
                except ImportError:
                    try:
                        from IPython.core.iplib import InteractiveShell
                        shell = InteractiveShell(user_ns=imported_objects)
                    except ImportError:
                        import IPython
                        shell = IPython.Shell.IPShell(argv=[], user_ns=imported_objects)
                    shell.mainloop()
        except ImportError:
            # Using normal Python shell
            import code
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
