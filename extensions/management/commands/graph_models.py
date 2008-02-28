from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from extensions.management.modelviz import generate_dot

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--disable-fields', '-d', action='store_false', dest='disable_fields', 
            help='Do not show the class member fields'),
        make_option('--all-applications', '-a', action='store_true', dest='all_applications',
    	    help='Automatically include all applications from INSTALLED_APPS'),
    )
    
    help = ("Creates a GraphViz dot file for the specified app names.  You can pass multiple app names and they will all be combined into a single model.  Output is usually directed to a dot file.")
    args = "[appname]"
    label = 'application name'
    
    requires_model_validation = True
    can_import_settings = True
    
    def handle(self, *args, **options):
        if len(args) < 1 and not options['all_applications']:
            raise CommandError("need one or more arguments for appname")
        print generate_dot(args, **options)
        
