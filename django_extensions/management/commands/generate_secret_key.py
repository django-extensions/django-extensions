# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django_extensions.management.utils import signalcommand

try:
    from django.core.management.utils import get_random_secret_key
except ImportError:
    from django.utils.crypto import get_random_string

    def get_random_secret_key():
        """
        Return a 50 character random string usable as a SECRET_KEY setting value.
        """
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        return get_random_string(50, chars)


class Command(BaseCommand):
    help = "Generates a new SECRET_KEY that can be used in a project settings file."

    requires_system_checks = False

    @signalcommand
    def handle(self, *args, **options):
        return get_random_secret_key()
