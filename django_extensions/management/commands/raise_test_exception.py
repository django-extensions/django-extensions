# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from django_extensions.management.utils import signalcommand


class DjangoExtensionsTestException(Exception):
    pass


class Command(BaseCommand):
    help = (
        "Raises a test Exception named DjangoExtensionsTestException. "
        "Useful for debugging integration with error reporters like Sentry."
    )

    @signalcommand
    def handle(self, *args, **options):
        message = (
            "This is a test exception via the "
            "django-extensions raise_test_exception management command."
        )
        raise DjangoExtensionsTestException(message)
