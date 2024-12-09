# -*- coding: utf-8 -*-
from typing import List

from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Generates a new password that can be used for a user password. This uses Django `get_random_string`."

    requires_system_checks: List[str] = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--length', nargs='?', type=int,
            help='Password length.', default=10)

    @signalcommand
    def handle(self, *args, **options):
        length = options['length']
        return get_random_string(length)
