# -*- coding: utf-8 -*-
from django.core.management import call_command
from django.test import TestCase
import six
import sys


class RunScriptTests(TestCase):

    def setUp(self):
        sys.stdout = six.StringIO()
        sys.stderr = six.StringIO()

    def test_runs(self):
        # lame test...does it run?
        call_command('runscript', 'sample_script', verbosity=2)
        self.assertIn("Found script 'tests.testapp.scripts.sample_script'", sys.stdout.getvalue())
        self.assertIn("Running script 'tests.testapp.scripts.sample_script'", sys.stdout.getvalue())

    def test_runs_appconfig(self):
        with self.modify_settings(INSTALLED_APPS={
            'append': 'tests.testapp.apps.TestAppConfig',
            'remove': 'tests.testapp',
        }):
            call_command('runscript', 'sample_script', verbosity=2)
            self.assertIn("Found script 'tests.testapp.scripts.sample_script'", sys.stdout.getvalue())
            self.assertIn("Running script 'tests.testapp.scripts.sample_script'", sys.stdout.getvalue())
