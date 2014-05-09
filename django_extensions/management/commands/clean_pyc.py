import fnmatch
import os
from django.core.management.base import NoArgsCommand
from django_extensions.management.utils import get_project_root
from optparse import make_option
from os.path import join as _j


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--optimize', '-o', '-O', action='store_true',
                    dest='optimize',
                    help='Remove optimized python bytecode files'),
        make_option('--path', '-p', action='store', dest='path',
                    help='Specify path to recurse into'),
    )
    help = "Removes all python bytecode compiled files from the project."

    requires_model_validation = False

    def handle_noargs(self, **options):
        project_root = options.get("path", None)
        verbosity = int(options.get("verbosity"))
        if not project_root:
            project_root = get_project_root()
            if verbosity > 0:
                self.stdout.write(
                    "No path specified, assuming %s is the project root.\n"
                    % project_root)
        exts = options.get("optimize", False) and "*.py[co]" or "*.pyc"

        for root, dirs, filenames in os.walk(project_root):
            for filename in fnmatch.filter(filenames, exts):
                full_path = _j(root, filename)
                if verbosity > 1:
                    self.stdout.write("%s\n" % full_path)
                os.remove(full_path)
