from django.core.management.base import NoArgsCommand
from django_extensions.management.utils import get_project_root
from random import choice
from optparse import make_option
from os.path import join as _j
import py_compile 
import os

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        #make_option('--optimize', '-o', '-O', action='store_true', dest='optimize', 
        #    help='Compile optimized python bytecode files'),
        make_option('--verbose', '-v', action='store_true', dest='verbose', 
            help='Verbose operation'),
    )
    help = "Compile python bytecode files for the project."
    
    requires_model_validation = False
    
    def handle_noargs(self, **options):
        project_root = get_project_root()
	verbose = options.get("verbose", False)
	for root, dirs, files in os.walk(project_root):
	    for file in files:
		ext = os.path.splitext(file)[1]
		if ext==".py":
		    full_path = _j(root, file)
		    if verbose:
			print "%sc" % full_path
		    py_compile.compile(full_path)
		    