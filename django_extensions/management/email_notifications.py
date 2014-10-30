from optparse import make_option

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class EmailNotificationCommand(BaseCommand):
    """A BaseCommand subclass which adds sending email fuctionality.

    Subclasses will have an extra command line option ``--email-notification``
    and will be able to send emails by calling ``send_email_notification()``
    if SMTP host and port are specified in settings. The handling of the
    command line option is left to the management command implementation.

    """
    option_list = BaseCommand.option_list + (
        make_option('--email-notifications',
                    action='store_true',
                    dest='email_notification',
                    help='Send email notifications for command.'),
    )

    def run_from_argv(self, argv):
        """Overriden in order to access the command line arguments."""
        self.argv_string = ' '.join(argv)
        super(EmailNotificationCommand, self).run_from_argv(argv)

    def send_email_notification(self, notification_id=None,
                                trb=None, verbosity=1):
        """Send email notifications.

        Reads settings from settings.EMAIL_NOTIFICATIONS dict, if available,
        using ``notification_id`` as a key or else provides reasonable
        defaults.

        """
        # Load email notification settings if available.
        if notification_id is not None:
            try:
                email_settings = settings.EMAIL_NOTIFICATIONS.get(
                    notification_id, {})
            except AttributeError:
                email_settings = {}
        else:
            email_settings = {}

        # Exit if no traceback found and not in 'notify always' mode.
        if trb is None and not email_settings.get('notification_level', 0):
            print(self.style.ERROR("Exiting, not in 'notify always' mode."))
            return

        # Set email fields.
        subject = email_settings.get('subject',
                                     "Django extensions email notification.")
        body = email_settings.get(
            'body',
            "Reporting execution of command: '%s'" % self.argv_string)
        # Include traceback.
        if (trb is not None and
            not email_settings.get('no_traceback', False)):
            body += "\n\nTraceback:\n\n%s\n" % trb
        # Set from address.
        from_email = email_settings.get('from_email',
                                        settings.DEFAULT_FROM_EMAIL)
        # Calculate recipients.
        recipients = list(email_settings.get('recipients', []))

        if not email_settings.get('no_admins', False):
            recipients.extend([a[1] for a in settings.ADMINS])

        if not recipients:
            if verbosity > 0:
                print (self.style.ERROR("No email recipients available."))
            return

        # Send email...
        send_mail(subject, body, from_email, recipients,
                  fail_silently=email_settings.get('fail_silently', True))
