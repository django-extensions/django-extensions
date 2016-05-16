# coding=utf-8
"""
set_fake_passwords.py

    Reset all user passwords to a common value. Useful for testing in a
    development environment. As such, this command is only available when
    setting.DEBUG is True.

"""
from django.conf import settings
from django.core.management.base import CommandError

from django_extensions.management.utils import signalcommand
from django_extensions.compat import CompatibilityBaseCommand as BaseCommand

DEFAULT_FAKE_PASSWORD = 'password'


class Command(BaseCommand):
    help = 'DEBUG only: sets all user passwords to a common value ("%s" by default)' % (DEFAULT_FAKE_PASSWORD, )
    requires_model_validation = False

    def add_arguments(self, parser):
        parser.add_argument(
            '--prompt', dest='prompt_passwd', default=False,
            action='store_true',
            help='Prompts for the new password to apply to all users')
        parser.add_argument(
            '--password', dest='default_passwd', default=DEFAULT_FAKE_PASSWORD,
            help='Use this as default password.')

    @signalcommand
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Only available in debug mode')

        from django_extensions.compat import get_user_model

        if options.get('prompt_passwd', False):
            from getpass import getpass
            passwd = getpass('Password: ')
            if not passwd:
                raise CommandError('You must enter a valid password')
        else:
            passwd = options.get('default_passwd', DEFAULT_FAKE_PASSWORD)

        User = get_user_model()
        user = User()
        user.set_password(passwd)
        count = User.objects.all().update(password=user.password)

        print('Reset %d passwords' % count)
