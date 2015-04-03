import fnmatch
import os
import py_compile
from optparse import make_option
from os.path import join as _j

from django.conf import settings
from django.core.management.base import CommandError, NoArgsCommand

from django_extensions.management.utils import signalcommand


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--path', '-p', action='store', dest='path',
                    help='Specify path to recurse into'),
    )
    help = "Compile python bytecode files for the project."

    requires_system_checks = False

    @signalcommand
    def handle_noargs(self, **options):
        project_root = options.get("path", None)
        if not project_root:
            project_root = getattr(settings, 'BASE_DIR', None)

        verbosity = int(options.get("verbosity"))
        if not project_root:
            raise CommandError("No --path specified and settings.py does not contain BASE_DIR")

        for root, dirs, filenames in os.walk(project_root):
            for filename in fnmatch.filter(filenames, '*.py'):
                full_path = _j(root, filename)
                if verbosity > 1:
                    self.stdout.write("Compiling %s...\n" % full_path)
                py_compile.compile(full_path)
