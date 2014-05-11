import os
import time
import fnmatch
import warnings
import py_compile
from django.core.management.base import NoArgsCommand
from django.conf import settings
from django_extensions.management.utils import get_project_root
from optparse import make_option
from os.path import join as _j


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--path', '-p', action='store', dest='path',
                    help='Specify path to recurse into'),
    )
    help = "Compile python bytecode files for the project."

    requires_model_validation = False

    def handle_noargs(self, **options):
        project_root = options.get("path", None)
        if not project_root:
            project_root = getattr(settings, 'BASE_DIR', None)

        verbosity = int(options.get("verbosity"))
        if not project_root:
            warnings.warn("settings.BASE_DIR or specifying --path will become mandatory in 1.4.0", DeprecationWarning)
            project_root = get_project_root()
            if verbosity > 0:
                self.stdout.write("""No path specified and settings.py does not contain BASE_DIR.
Assuming '%s' is the project root.

Please add BASE_DIR to your settings.py future versions 1.4.0 and higher of Django-Extensions
will require either BASE_DIR or specifying the --path option.

Waiting for 30 seconds. Press ctrl-c to abort.
""" % project_root)
                if getattr(settings, 'COMPILE_PYC_DEPRECATION_WAIT', True):
                    try:
                        time.sleep(30)
                    except KeyboardInterrupt:
                        self.stdout.write("Aborted\n")
                        return

        for root, dirs, filenames in os.walk(project_root):
            for filename in fnmatch.filter(filenames, '*.py'):
                full_path = _j(root, filename)
                if verbosity > 1:
                    self.stdout.write("Compiling %s...\n" % full_path)
                py_compile.compile(full_path)
