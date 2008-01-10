from django.core.management.base import NoArgsCommand
from optparse import make_option

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
        make_option('--plain', action='store_true', dest='plain',
            help='Tells Django to use plain Python, not IPython.'),
    )
    help = "Like the 'shell' command but autoloads the models of all installed Django apps."
    
    requires_model_validation = True
    
    def handle_noargs(self, **options):
        from django.core.management import call_command
        from django.db.models.loading import get_models
        
        verbosity = int(options.get('verbosity', 1))
        use_plain = options.get('plain', False)
        
        for m in get_models():
            try:
                exec "from %s import %s" % (m.__module__, m.__name__)
            except ImportError:
                pass
        call_command('shell', **{'use_plain': use_plain})
