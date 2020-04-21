# -*- coding: utf-8 -*-
import sys
import traceback

from django.conf import settings
from django.core.mail import send_mail
from django.core.management import BaseCommand


class EmailNotificationCommand(BaseCommand):
    """
    A BaseCommand subclass which adds sending email fuctionality.

    Subclasses will have an extra command line option ``--email-notification``
    and will be able to send emails by calling ``send_email_notification()``
    if SMTP host and port are specified in settings. The handling of the
    command line option is left to the management command implementation.
    Configuration is done in settings.EMAIL_NOTIFICATIONS dict.

    Configuration example::

        EMAIL_NOTIFICATIONS = {
            'scripts.my_script': {
                'subject': 'my_script subject',
                'body': 'my_script body',
                'from_email': 'from_email@example.com',
                'recipients': ('recipient0@example.com',),
                'no_admins': False,
                'no_traceback': False,
                'notification_level': 0,
                'fail_silently': False
            },
            'scripts.another_script': {
                ...
            },
            ...
        }

    Configuration explained:
        subject:            Email subject.
        body:               Email body.
        from_email:         Email from address.
        recipients:         Sequence of email recipient addresses.
        no_admins:          When True do not include ADMINS to recipients.
        no_traceback:       When True do not include traceback to email body.
        notification_level: 0: send email on fail, 1: send email always.
        fail_silently:      Parameter passed to django's send_mail().
    """

    def add_arguments(self, parser):
        parser.add_argument('--email-notifications',
                            action='store_true',
                            default=False,
                            dest='email_notifications',
                            help='Send email notifications for command.')
        parser.add_argument('--email-exception',
                            action='store_true',
                            default=False,
                            dest='email_exception',
                            help='Send email for command exceptions.')

    def run_from_argv(self, argv):
        """Overriden in order to access the command line arguments."""
        self.argv_string = ' '.join(argv)
        super().run_from_argv(argv)

    def execute(self, *args, **options):
        """
        Overriden in order to send emails on unhandled exception.

        If an unhandled exception in ``def handle(self, *args, **options)``
        occurs and `--email-exception` is set or `self.email_exception` is
        set to True send an email to ADMINS with the traceback and then
        reraise the exception.
        """
        try:
            super().execute(*args, **options)
        except Exception:
            if options['email_exception'] or getattr(self, 'email_exception', False):
                self.send_email_notification(include_traceback=True)
            raise

    def send_email_notification(self, notification_id=None, include_traceback=False, verbosity=1):
        """
        Send email notifications.

        Reads settings from settings.EMAIL_NOTIFICATIONS dict, if available,
        using ``notification_id`` as a key or else provides reasonable
        defaults.
        """
        # Load email notification settings if available
        if notification_id is not None:
            try:
                email_settings = settings.EMAIL_NOTIFICATIONS.get(notification_id, {})
            except AttributeError:
                email_settings = {}
        else:
            email_settings = {}

        # Exit if no traceback found and not in 'notify always' mode
        if not include_traceback and not email_settings.get('notification_level', 0):
            print(self.style.ERROR("Exiting, not in 'notify always' mode."))
            return

        # Set email fields.
        subject = email_settings.get('subject', "Django extensions email notification.")

        command_name = self.__module__.split('.')[-1]

        body = email_settings.get(
            'body',
            "Reporting execution of command: '%s'" % command_name
        )

        # Include traceback
        if include_traceback and not email_settings.get('no_traceback', False):
            try:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                trb = ''.join(traceback.format_tb(exc_traceback))
                body += "\n\nTraceback:\n\n%s\n" % trb
            finally:
                del exc_traceback

        # Set from address
        from_email = email_settings.get('from_email', settings.DEFAULT_FROM_EMAIL)

        # Calculate recipients
        recipients = list(email_settings.get('recipients', []))

        if not email_settings.get('no_admins', False):
            recipients.extend(settings.ADMINS)

        if not recipients:
            if verbosity > 0:
                print(self.style.ERROR("No email recipients available."))
            return

        # Send email...
        send_mail(subject, body, from_email, recipients,
                  fail_silently=email_settings.get('fail_silently', True))
