# -*- coding: utf-8 -*-
import logging
from cStringIO import StringIO

from django.core.management import call_command
from django.test import TestCase


class MockLoggingHandler(logging.Handler):
    """ Mock logging handler to check for expected logs. """

    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }


class CommandTest(TestCase):
    def test_error_logging(self):
        # Ensure command errors are properly logged and reraised
        from django_extensions.management.base import logger
        logger.addHandler(MockLoggingHandler())
        from django.conf import settings
        org_apps = None
        apps = list(settings.INSTALLED_APPS)
        if not 'django_extensions.tests' in apps:
            apps.append('django_extensions.tests')
        self.assertRaises(Exception, call_command, 'error_raising_command')
        handler = logger.handlers[0]
        self.assertEqual(len(handler.messages['error']), 1)
        if org_apps:
            settings.INSTALLED_APPS = org_apps


class ShowTemplateTagsTests(TestCase):
    def test_some_output(self):
        out = StringIO()
        call_command('show_templatetags', stdout=out)
        output = out.getvalue()
        # Once django_extension is installed during tests it should appear with
        # its templatetags
        self.assertIn('django_extensions', output)
        # let's check at least one
        self.assertIn('truncate_letters', output)
