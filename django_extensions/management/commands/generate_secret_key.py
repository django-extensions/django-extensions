# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Generates a new SECRET_KEY that can be used in a project settings file."

    requires_system_checks = False

    @signalcommand
    def handle(self, *args, **options):
        return get_random_secret_key()
