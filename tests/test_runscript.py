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

    def test_prints_error_on_nonexistent_script(self):
        call_command('runscript', 'non_existent_script', verbosity=2)
        self.assertIn("No (valid) module for script 'non_existent_script' found", sys.stdout.getvalue())

    def test_prints_additional_info_on_nonexistent_script_and_low_verbosity(self):
        call_command('runscript', 'non_existent_script', verbosity=1)
        self.assertIn("No (valid) module for script 'non_existent_script' found", sys.stdout.getvalue())
        self.assertIn("Try running with a higher verbosity level like: -v2 or -v3", sys.stdout.getvalue())

    def test_prints_import_error_on_script_with_invalid_imports(self):
        call_command('runscript', 'invalid_import_script', verbosity=2)
        self.assertIn("Cannot import module 'tests.testapp.scripts.invalid_import_script'", sys.stdout.getvalue())
        self.assertRegexpMatches(sys.stdout.getvalue(), 'No module named (\')?(invalidpackage)\1?')
