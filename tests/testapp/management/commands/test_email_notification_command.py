# -*- coding: utf-8 -*-
from django_extensions.management.email_notifications import EmailNotificationCommand


class Command(EmailNotificationCommand):
    help = 'Just for email_notifications testing purpose'

    def handle(self, *args, **kwargs):
        raise Exception()
