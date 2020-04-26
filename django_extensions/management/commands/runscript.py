# -*- coding: utf-8 -*-
import importlib
import inspect
import os
import traceback

from argparse import ArgumentTypeError

from django.apps import apps
from django.core.management.base import CommandError

from django_extensions.management.email_notifications import EmailNotificationCommand
from django_extensions.management.utils import signalcommand


class DirPolicyChoices:
    NONE = 'none'
    EACH = 'each'
    ROOT = 'root'


def check_is_directory(value):
    if value is None or not os.path.isdir(value):
        raise ArgumentTypeError("%s is not a directory!" % value)
    return value


class BadCustomDirectoryException(Exception):
    def __init__(self, value):
        self.message = value + ' If --dir-policy is custom than you must set correct directory in ' \
                               '--dir option or in settings.RUNSCRIPT_CHDIR'

    def __str__(self):
        return self.message


class Command(EmailNotificationCommand):
    help = 'Runs a script in django context.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_directory = os.getcwd()

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('script', nargs='+')
        parser.add_argument(
            '--fixtures', action='store_true', dest='infixtures', default=False,
            help='Also look in app.fixtures subdir',
        )
        parser.add_argument(
            '--noscripts', action='store_true', dest='noscripts', default=False,
            help='Do not look in app.scripts subdir',
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
        parser.add_argument(
            '--dir-policy', type=str,
            choices=[DirPolicyChoices.NONE, DirPolicyChoices.EACH, DirPolicyChoices.ROOT],
            help='Policy of selecting scripts execution directory: '
                 'none - start all scripts in current directory '
                 'each - start all scripts in their directories '
                 'root - start all scripts in BASE_DIR directory ',
        )
        parser.add_argument(
            '--chdir', type=check_is_directory,
            help='If dir-policy option is set to custom, than this option determines script execution directory.',
        )

    @signalcommand
    def handle(self, *args, **options):
        from django.conf import settings

        NOTICE = self.style.SQL_TABLE
        NOTICE2 = self.style.SQL_FIELD
        ERROR = self.style.ERROR
        ERROR2 = self.style.NOTICE

        subdirs = []
        scripts = options['script']

        if not options['noscripts']:
            subdirs.append(getattr(settings, 'RUNSCRIPT_SCRIPT_DIR', 'scripts'))
        if options['infixtures']:
            subdirs.append('fixtures')
        verbosity = options["verbosity"]
        show_traceback = options['traceback']
        no_traceback = options['no_traceback']
        if no_traceback:
            show_traceback = False
        else:
            show_traceback = True
        silent = options['silent']
        if silent:
            verbosity = 0
        email_notifications = options['email_notifications']

        if len(subdirs) < 1:
            print(NOTICE("No subdirs to run left."))
            return

        if len(scripts) < 1:
            print(ERROR("Script name required."))
            return

        def get_directory_from_chdir():
            directory = options['chdir'] or getattr(settings, 'RUNSCRIPT_CHDIR', None)
            try:
                check_is_directory(directory)
            except ArgumentTypeError as e:
                raise BadCustomDirectoryException(str(e))
            return directory

        def get_directory_basing_on_policy(script_module):
            policy = options['dir_policy'] or getattr(settings, 'RUNSCRIPT_CHDIR_POLICY', DirPolicyChoices.NONE)
            if policy == DirPolicyChoices.ROOT:
                return settings.BASE_DIR
            elif policy == DirPolicyChoices.EACH:
                return os.path.dirname(inspect.getfile(script_module))
            else:
                return self.current_directory

        def set_directory(script_module):
            if options['chdir']:
                directory = get_directory_from_chdir()
            elif options['dir_policy']:
                directory = get_directory_basing_on_policy(script_module)
            elif getattr(settings, 'RUNSCRIPT_CHDIR', None):
                directory = get_directory_from_chdir()
            else:
                directory = get_directory_basing_on_policy(script_module)
            os.chdir(os.path.abspath(directory))

        def run_script(mod, *script_args):
            try:
                set_directory(mod)
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

        def my_import(parent_package, module_name):
            full_module_path = "%s.%s" % (parent_package, module_name)
            if verbosity > 1:
                print(NOTICE("Check for %s" % full_module_path))
            # Try importing the parent package first
            try:
                importlib.import_module(parent_package)
            except ImportError as e:
                if str(e).startswith('No module named'):
                    # No need to proceed if the parent package doesn't exist
                    return False

            try:
                t = importlib.import_module(full_module_path)
            except ImportError as e:
                # The parent package exists, but the module doesn't
                try:
                    if importlib.util.find_spec(full_module_path) is None:
                        return False
                except Exception:
                    module_file = os.path.join(settings.BASE_DIR, *full_module_path.split('.')) + '.py'
                    if not os.path.isfile(module_file):
                        return False

                if silent:
                    return False
                if show_traceback:
                    traceback.print_exc()
                if verbosity > 0:
                    print(ERROR("Cannot import module '%s': %s." % (full_module_path, e)))

                return False

            if hasattr(t, "run"):
                if verbosity > 1:
                    print(NOTICE2("Found script '%s' ..." % full_module_path))
                return t
            else:
                if verbosity > 1:
                    print(ERROR2("Found script '%s' but no run() function found." % full_module_path))

        def find_modules_for_script(script):
            """ Find script module which contains 'run' attribute """
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

        if options['script_args']:
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
