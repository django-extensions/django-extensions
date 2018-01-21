# -*- coding: utf-8 -*-
import os
import fnmatch

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import color_style
from django.template.loader import get_template

from django_extensions.compat import get_template_setting
from django_extensions.management.utils import signalcommand


#
# TODO: Render the template with fake request object ?
#


class Command(BaseCommand):
    args = ''
    help = "Validate templates on syntax and compile errors"
    ignores = set([
        ".DS_Store",
        "*.swp",
        "*~",
    ])

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--no-apps', action='store_true', dest='no_apps',
            default=False, help="Do not automatically include apps.")
        parser.add_argument(
            '--break', '-b', action='store_true', dest='break',
            default=False, help="Break on first error.")
        parser.add_argument(
            '--include', '-i', action='append', dest='includes',
            default=[], help="Append these paths to TEMPLATE DIRS")
        parser.add_argument(
            '--ignore-app', action='append', dest='ignore_apps',
            default=[], help="Ignore these apps")

    def ignore_filename(self, filename):
        filename = os.path.basename(filename)
        for ignore_pattern in self.ignores:
            if fnmatch.fnmatch(filename, ignore_pattern):
                return True
        return False

    @signalcommand
    def handle(self, *args, **options):
        if hasattr(settings, 'VALIDATE_TEMPLATES_IGNORES'):
            self.ignores = getattr(settings, 'VALIDATE_TEMPLATES_IGNORES')

        style = color_style()
        template_dirs = set(get_template_setting('DIRS'))
        template_dirs |= set(options.get('includes', []))
        template_dirs |= set(getattr(settings, 'VALIDATE_TEMPLATES_EXTRA_TEMPLATE_DIRS', []))

        if not options['no_apps']:
            ignore_apps = options['ignore_apps']
            if not ignore_apps and hasattr(settings, 'VALIDATE_TEMPLATES_IGNORE_APPS'):
                ignore_apps = getattr(settings, 'VALIDATE_TEMPLATES_IGNORE_APPS')
            for app in apps.get_app_configs():
                if app.name in ignore_apps:
                    continue
                app_template_dir = os.path.join(app.path, 'templates')
                if os.path.isdir(app_template_dir):
                    template_dirs.add(app_template_dir)

        # This is unsafe:
        # https://docs.djangoproject.com/en/1.10/topics/settings/#altering-settings-at-runtime
        if hasattr(settings, 'TEMPLATES'):
            settings.TEMPLATES[0]['DIRS'] = list(template_dirs)
        else:
            settings.TEMPLATE_DIRS = list(template_dirs)
        settings.TEMPLATE_DEBUG = True
        verbosity = int(options.get('verbosity', 1))
        errors = 0

        for template_dir in template_dirs:
            for root, dirs, filenames in os.walk(template_dir):
                for filename in filenames:
                    if self.ignore_filename(filename):
                        continue

                    filepath = os.path.join(root, filename)
                    if verbosity > 1:
                        self.stdout.write(filepath)
                    try:
                        get_template(filepath)
                    except Exception as e:
                        errors += 1
                        self.stdout.write("%s: %s" % (filepath, style.ERROR("%s %s" % (e.__class__.__name__, str(e)))))
                    if errors and options.get('break', False):
                        raise CommandError("Errors found")

        if errors:
            raise CommandError("%s errors found" % errors)
        self.stdout.write("%s errors found" % errors)
