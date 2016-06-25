# -*- coding: utf-8 -*-
import os

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

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--break', '-b', action='store_true', dest='break',
            default=False, help="Break on first error.")
        parser.add_argument(
            '--include', '-i', action='append', dest='includes',
            default=[], help="Append these paths to TEMPLATE DIRS")

    @signalcommand
    def handle(self, *args, **options):
        from django.conf import settings
        style = color_style()
        template_dirs = set(get_template_setting('DIRS'))
        template_dirs |= set(options.get('includes', []))
        template_dirs |= set(getattr(settings, 'VALIDATE_TEMPLATES_EXTRA_TEMPLATE_DIRS', []))

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
                    if filename.endswith(".swp"):
                        continue
                    if filename.endswith("~"):
                        continue
                    filepath = os.path.join(root, filename)
                    if verbosity > 1:
                        print(filepath)
                    try:
                        get_template(filepath)
                    except Exception as e:
                        errors += 1
                        print("%s: %s" % (filepath, style.ERROR("%s %s" % (e.__class__.__name__, str(e)))))
                    if errors and options.get('break', False):
                        raise CommandError("Errors found")

        if errors:
            raise CommandError("%s errors found" % errors)
        print("%s errors found" % errors)
