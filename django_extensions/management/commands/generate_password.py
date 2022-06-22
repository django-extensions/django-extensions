# -*- coding: utf-8 -*-
from typing import List

try:
    from django.contrib.auth.base_user import BaseUserManager
except ImportError:
    from django.contrib.auth.models import BaseUserManager
from django.core.management.base import BaseCommand
from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Generates a new password that can be used for a user password. This uses Django core's default password generator `BaseUserManager.make_random_password()`."

    requires_system_checks: List[str] = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--length', nargs='?', type=int,
            help='Password length.')

    @signalcommand
    def handle(self, *args, **options):
        length = options['length']
        manager = BaseUserManager()

        if length:
            return manager.make_random_password(length)
        else:
            return manager.make_random_password()
