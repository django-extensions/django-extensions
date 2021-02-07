# -*- coding: utf-8 -*-
import asyncore
import sys
from logging import getLogger
from smtpd import SMTPServer

from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.utils import setup_logger, signalcommand

logger = getLogger(__name__)


class ExtensionDebuggingServer(SMTPServer):
    """Duplication of smtpd.DebuggingServer, but using logging instead of print."""

    # Do something with the gathered message
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        """Output will be sent to the module logger at INFO level."""
        inheaders = 1
        lines = data.split('\n')
        logger.info('---------- MESSAGE FOLLOWS ----------')
        for line in lines:
            # headers first
            if inheaders and not line:
                logger.info('X-Peer: %s' % peer[0])
                inheaders = 0
            logger.info(line)
        logger.info('------------ END MESSAGE ------------')


class Command(BaseCommand):
    help = "Starts a test mail server for development."
    args = '[optional port number or ippaddr:port]'

    requires_system_checks = False

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('addrport', nargs='?')
        parser.add_argument(
            '--output', dest='output_file', default=None,
            help='Specifies an output file to send a copy of all messages (not flushed immediately).'
        )
        parser.add_argument(
            '--use-settings', dest='use_settings',
            action='store_true', default=False,
            help='Uses EMAIL_HOST and HOST_PORT from Django settings.'
        )

    @signalcommand
    def handle(self, addrport='', *args, **options):
        if not addrport:
            if options['use_settings']:
                from django.conf import settings
                addr = getattr(settings, 'EMAIL_HOST', '')
                port = str(getattr(settings, 'EMAIL_PORT', '1025'))
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

        # Add console handler
        setup_logger(logger, stream=self.stdout, filename=options['output_file'])

        def inner_run():
            quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'
            print("Now accepting mail at %s:%s -- use %s to quit" % (addr, port, quit_command))
            ExtensionDebuggingServer((addr, port), None, decode_data=True)
            asyncore.loop()

        try:
            inner_run()
        except KeyboardInterrupt:
            pass
