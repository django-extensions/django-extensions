# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Generates a new password that can be used for a user password."

    requires_system_checks = False

    def add_arguments(self, parser):
        default_length = 10
        parser.add_argument(
            '--length', nargs='?', type=int, default=default_length,
            help='Password length (default: %d).' % (default_length, ))

    @signalcommand
    def handle(self, *args, **options):
        length = options['length']

        # This does not have "I" or "0" or letters and digits that look similar
        # to avoid confusion.
        allowed_chars = ('abcdefghjkmnpqrstuvwxyz'
                         'ABCDEFGHJKLMNPQRSTUVWXYZ'
                         '23456789')
        return get_random_string(length, allowed_chars)
