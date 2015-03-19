import sys
import traceback
from optparse import make_option

from django_extensions.compat import importlib, list_apps
from django_extensions.management.email_notifications import \
    EmailNotificationCommand
from django_extensions.management.utils import signalcommand


def vararg_callback(option, opt_str, opt_value, parser):
    parser.rargs.insert(0, opt_value)
    value = []
    for arg in parser.rargs:
        # stop on --foo like options
        if arg[:2] == "--" and len(arg) > 2:
            break
        # stop on -a like options
        if arg[:1] == "-":
            break
        value.append(arg)

    del parser.rargs[:len(value)]
    setattr(parser.values, option.dest, value)


class Command(EmailNotificationCommand):
    option_list = EmailNotificationCommand.option_list + (
        make_option('--fixtures', action='store_true', dest='infixtures', default=False,
                    help='Only look in app.fixtures subdir'),
        make_option('--noscripts', action='store_true', dest='noscripts', default=False,
                    help='Look in app.scripts subdir'),
        make_option('-s', '--silent', action='store_true', dest='silent', default=False,
                    help='Run silently, do not show errors and tracebacks'),
        make_option('--no-traceback', action='store_true', dest='no_traceback', default=False,
                    help='Do not show tracebacks'),
        make_option('--script-args', action='callback', callback=vararg_callback, type='string',
                    help='Space-separated argument list to be passed to the scripts. Note that the '
                         'same arguments will be passed to all named scripts.'),
    )
    help = 'Runs a script in django context.'
    args = "script [script ...]"

    @signalcommand
    def handle(self, *scripts, **options):
        NOTICE = self.style.SQL_TABLE
        NOTICE2 = self.style.SQL_FIELD
        ERROR = self.style.ERROR
        ERROR2 = self.style.NOTICE

        subdirs = []

        if not options.get('noscripts'):
            subdirs.append('scripts')
        if options.get('infixtures'):
            subdirs.append('fixtures')
        verbosity = int(options.get('verbosity', 1))
        show_traceback = options.get('traceback', True)
        if show_traceback is None:
            # XXX: traceback is set to None from Django ?
            show_traceback = True
        no_traceback = options.get('no_traceback', False)
        if no_traceback:
            show_traceback = False
        silent = options.get('silent', False)
        if silent:
            verbosity = 0
        email_notifications = options.get('email_notifications', False)

        if len(subdirs) < 1:
            print(NOTICE("No subdirs to run left."))
            return

        if len(scripts) < 1:
            print(ERROR("Script name required."))
            return

        def run_script(mod, *script_args):
            try:
                mod.run(*script_args)
                if email_notifications:
                    self.send_email_notification(notification_id=mod.__name__)
            except Exception:
                if silent:
                    return
                if verbosity > 0:
                    print(ERROR("Exception while running run() in '%s'" % mod.__name__))
                if email_notifications:
                    self.send_email_notification(
                        notification_id=mod.__name__, include_traceback=True)
                if show_traceback:
                    raise

        def my_import(mod):
            if verbosity > 1:
                print(NOTICE("Check for %s" % mod))
            # check if module exists before importing
            try:
                importlib.import_module(mod)
                t = __import__(mod, [], [], [" "])
            except (ImportError, AttributeError) as e:
                if str(e).startswith('No module named'):
                    try:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        try:
                            if exc_traceback.tb_next.tb_next is None:
                                return False
                        except AttributeError:
                            pass
                    finally:
                        exc_traceback = None

                if verbosity > 1:
                    if verbosity > 2:
                        traceback.print_exc()
                    print(ERROR("Cannot import module '%s': %s." % (mod, e)))

                return False

            #if verbosity > 1:
            #    print(NOTICE("Found script %s ..." % mod))
            if hasattr(t, "run"):
                if verbosity > 1:
                    print(NOTICE2("Found script '%s' ..." % mod))
                #if verbosity > 1:
                #    print(NOTICE("found run() in %s. executing..." % mod))
                return t
            else:
                if verbosity > 1:
                    print(ERROR2("Find script '%s' but no run() function found." % mod))

        def find_modules_for_script(script):
            """ find script module which contains 'run' attribute """
            modules = []
            # first look in apps
            for app in list_apps():
                for subdir in subdirs:
                    mod = my_import("%s.%s.%s" % (app, subdir, script))
                    if mod:
                        modules.append(mod)

            # try app.DIR.script import
            sa = script.split(".")
            for subdir in subdirs:
                nn = ".".join(sa[:-1] + [subdir, sa[-1]])
                mod = my_import(nn)
                if mod:
                    modules.append(mod)

            # try direct import
            if script.find(".") != -1:
                mod = my_import(script)
                if mod:
                    modules.append(mod)

            return modules

        if options.get('script_args'):
            script_args = options['script_args']
        else:
            script_args = []
        for script in scripts:
            modules = find_modules_for_script(script)
            if not modules:
                if verbosity > 0 and not silent:
                    print(ERROR("No (valid) module for script '%s' found" % script))
                    if verbosity < 2:
                        print(ERROR("Try running with a higher verbosity level like: -v2 or -v3"))
            for mod in modules:
                if verbosity > 1:
                    print(NOTICE2("Running script '%s' ..." % mod.__name__))
                run_script(mod, *script_args)
