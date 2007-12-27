from django.core.management.base import NoArgsCommand
from optparse import make_option
from django.contrib.auth.create_superuser import createsuperuser

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--username', dest='username', default=None,
            help='Specifies the username for the superuser.'),
        make_option('--email', dest='email', default=None,
            help='Specifies the email address for the superuser.'),
    )
    help = 'Used to create a superuser.'
    
    def handle_noargs(self, **options):
        username = options.get('username', None)
        email = options.get('email', None)

        createsuperuser(username=username, password=None, email=email)