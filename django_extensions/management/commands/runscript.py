# -*- coding: utf-8 -*-
import sys
import importlib
import traceback

from django.apps import apps
from django.core.management.base import CommandError

from django_extensions.management.email_notifications import EmailNotificationCommand
from django_extensions.management.utils import signalcommand


class Command(EmailNotificationCommand):
    help = 'Runs a script in django context.'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('script', nargs='+')
        parser.add_argument(
            '--fixtures', action='store_true', dest='infixtures', default=False,
            help='Only look in app.fixtures subdir',
        )
        parser.add_argument(
            '--noscripts', action='store_true', dest='noscripts', default=False,
            help='Look in app.scripts subdir',
        )
        parser.add_argument(
            '-s', '--silent', action='store_true', dest='silent', default=False,
            help='Run silently, do not show errors and tracebacks',
        )
        parser.add_argument(
            '--no-traceback', action='store_true', dest='no_traceback', default=False,
            help='Do not show tracebacks',
        )
        parser.add_argument(
            '--script-args', nargs='*', type=str,
            help='Space-separated argument list to be passed to the scripts. Note that the '
                 'same arguments will be passed to all named scripts.',
        )

    @signalcommand
    def handle(self, *args, **options):
        NOTICE = self.style.SQL_TABLE
        NOTICE2 = self.style.SQL_FIELD
        ERROR = self.style.ERROR
        ERROR2 = self.style.NOTICE

        subdirs = []
        scripts = options['script']

        if not options.get('noscripts'):
            subdirs.append('scripts')
        if options.get('infixtures'):
            subdirs.append('fixtures')
        verbosity = int(options.get('verbosity', 1))
        show_traceback = options.get('traceback', False)
        no_traceback = options.get('no_traceback', False)
        if no_traceback:
            show_traceback = False
        else:
            show_traceback = True
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
            except Exception as e:
                if silent:
                    return
                if verbosity > 0:
                    print(ERROR("Exception while running run() in '%s'" % mod.__name__))
                if email_notifications:
                    self.send_email_notification(
                        notification_id=mod.__name__, include_traceback=True)
                if show_traceback:
                    if not isinstance(e, CommandError):
                        raise

        def my_import(parent_package, module):
            mod = "%s.%s" % (parent_package, module)
            if verbosity > 1:
                print(NOTICE("Check for %s" % mod))
            # Try importing the parent package first
            try:
                importlib.import_module(parent_package)
            except ImportError as e:
                if str(e).startswith('No module named'):
                    # No need to proceed if the parent package doesn't exist
                    return False

            try:
                t = importlib.import_module(mod)
            except ImportError as e:
                # The parent package exists, but the module doesn't
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

                if silent:
                    return False
                if show_traceback:
                    traceback.print_exc()
                if verbosity > 0:
                    print(ERROR("Cannot import module '%s': %s." % (mod, e)))

                return False

            if hasattr(t, "run"):
                if verbosity > 1:
                    print(NOTICE2("Found script '%s' ..." % mod))
                return t
            else:
                if verbosity > 1:
                    print(ERROR2("Found script '%s' but no run() function found." % mod))

        def find_modules_for_script(script):
            """ find script module which contains 'run' attribute """
            modules = []
            # first look in apps
            for app in apps.get_app_configs():
                for subdir in subdirs:
                    mod = my_import("%s.%s" % (app.name, subdir), script)
                    if mod:
                        modules.append(mod)

            # try direct import
            if script.find(".") != -1:
                parent, mod_name = script.rsplit(".", 1)
                mod = my_import(parent, mod_name)
                if mod:
                    modules.append(mod)
            else:
                # try app.DIR.script import
                for subdir in subdirs:
                    mod = my_import(subdir, script)
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
