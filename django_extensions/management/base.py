# -*- coding: utf-8 -*-
import sys
from typing import List, Tuple, Union

from django.core.checks import Tags
from django.core.management import BaseCommand
from logging import getLogger

logger = getLogger('django.commands')


class _BaseDjangoExtensionsCommand(BaseCommand):
    """
    This is an internally used command.
    It is used for defining suitable defaults for all subclasses that require to inherit from _BaseDjangoExtensionsCommand.
    All instances of potential BaseCommad usage should inherit from this."""
    # Django4: bool is provided for backward compatability. Remove bool after django4 is released
    requires_system_checks: Union[bool, Tuple[Tags, ...], List[Tags], str]


class LoggingBaseCommand(_BaseDjangoExtensionsCommand):
    """
    A subclass of BaseCommand that logs run time errors to `django.commands`.
    To use this, create a management command subclassing LoggingBaseCommand:

        from django_extensions.management.base import LoggingBaseCommand

        class Command(LoggingBaseCommand):
            help = 'Test error'

            def handle(self, *args, **options):
                raise Exception


    And then define a logging handler in settings.py:

        LOGGING = {
            ... # Other stuff here

            'handlers': {
                'mail_admins': {
                    'level': 'ERROR',
                    'filters': ['require_debug_false'],
                    'class': 'django.utils.log.AdminEmailHandler'
                },
            },
            'loggers': {
                'django.commands': {
                    'handlers': ['mail_admins'],
                    'level': 'ERROR',
                    'propagate': False,
                },
            }

        }

    """

    def execute(self, *args, **options):
        try:
            super().execute(*args, **options)
        except Exception as e:
            logger.error(e, exc_info=sys.exc_info(), extra={'status_code': 500})
            raise
