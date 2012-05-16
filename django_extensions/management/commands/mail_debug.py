from django.core.management.base import BaseCommand, CommandError
import sys
import smtpd
import asyncore
from optparse import make_option


# Modified from http://stackoverflow.com/a/616686/4281
class Tee(object):
    """ Intercept sys.stdout and redirect to a file, and stdout."""
    def __init__(self, name, mode='w', tee=True):
        self.tee = tee
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self

    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        """Intercept output and write to file, real stdout."""
        self.file.write(data)
        if self.tee:
            self.stdout.write(data)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--output', dest='output_file', default=None,
            help='Specifies an output file to send all messages.'),
        make_option('--tee', dest='tee', action='store_true', default=False,
            help='Send output to file and stdout (requires --output).'),
        make_option('--use-settings', dest='use_settings',
            action='store_true', default=False,
            help='Uses EMAIL_HOST and HOST_PORT from Django settings.'),

    )
    help = "Starts a test mail server for development."
    args = '[optional port number or ippaddr:port]'

    requires_model_validation = False

    def handle(self, addrport='', *args, **options):
        if args:
            raise CommandError('Usage is runserver %s' % self.args)
        if not addrport:
            if options.get('use_settings', False):
                from django.conf import settings
                addr = settings.EMAIL_HOST
                port = settings.EMAIL_PORT
            else:
                addr = ''
                port = '1025'
        else:
            try:
                addr, port = addrport.split(':')
            except ValueError:
                addr, port = '', addrport
        if not addr:
            addr = '127.0.0.1'

        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)
        else:
            port = int(port)

        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        def inner_run():
            print "Now accepting mail at %s:%s" % (addr, port)
            # Set up output redirection after the above info message.
            if options.get('output_file', None):
                self.tee = Tee(options.get('output_file', None),
                        tee=options.get('tee', False))

            server = smtpd.DebuggingServer((addr, port), None)
            asyncore.loop()

        try:
            inner_run()
        except KeyboardInterrupt:
            pass
