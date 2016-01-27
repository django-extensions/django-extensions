# coding=utf-8
import fnmatch
import os
from os.path import join as _j

from django.conf import settings
from django.core.management.base import CommandError

from django_extensions.management.utils import signalcommand
from django_extensions.compat import CompatibilityBaseCommand as BaseCommand


class Command(BaseCommand):
    help = "Removes all python bytecode compiled files from the project."

    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument('--optimize', '-o', '-O', action='store_true',
                            dest='optimize',
                            help='Remove optimized python bytecode files')
        parser.add_argument('--path', '-p', action='store', dest='path',
                            help='Specify path to recurse into')

    @signalcommand
    def handle(self, *args, **options):
        project_root = options.get("path", getattr(settings, 'BASE_DIR', None))
        if not project_root:
            project_root = getattr(settings, 'BASE_DIR', None)

        verbosity = int(options.get("verbosity"))
        if not project_root:
            raise CommandError("No --path specified and settings.py does not contain BASE_DIR")

        exts = options.get("optimize", False) and "*.py[co]" or "*.pyc"

        for root, dirs, filenames in os.walk(project_root):
            for filename in fnmatch.filter(filenames, exts):
                full_path = _j(root, filename)
                if verbosity > 1:
                    self.stdout.write("%s\n" % full_path)
                os.remove(full_path)
