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


class NonExistentScriptsTests(RunScriptTests):
    def test_prints_error_on_nonexistent_script(self):
        call_command('runscript', 'non_existent_script', verbosity=2)
        self.assertIn("No (valid) module for script 'non_existent_script' found", sys.stdout.getvalue())

    def test_prints_nothing_for_nonexistent_script_when_silent(self):
        call_command('runscript', 'non_existent_script', silent=True)
        self.assertEqual("", sys.stdout.getvalue())

    def test_doesnt_print_exception_for_nonexistent_script_when_no_traceback(self):
        call_command('runscript', 'non_existent_script', no_traceback=True)
        self.assertEqual("", sys.stderr.getvalue())


class InvalidImportScriptsTests(RunScriptTests):
    def test_prints_additional_info_on_nonexistent_script_by_default(self):
        call_command('runscript', 'non_existent_script')
        self.assertIn("No (valid) module for script 'non_existent_script' found", sys.stdout.getvalue())
        self.assertIn("Try running with a higher verbosity level like: -v2 or -v3", sys.stdout.getvalue())

    def test_prints_import_error_on_script_with_invalid_imports_by_default(self):
        call_command('runscript', 'invalid_import_script')
        self.assertIn("Cannot import module 'tests.testapp.scripts.invalid_import_script'", sys.stdout.getvalue())
        self.assertRegexpMatches(sys.stdout.getvalue(), 'No module named (\')?(invalidpackage)\1?')


class InvalidScriptsTests(RunScriptTests):
    def test_raises_error_message_on_invalid_script_by_default(self):
        with self.assertRaises(Exception):
            call_command('runscript', 'error_script')
        self.assertIn("Exception while running run() in", sys.stdout.getvalue())

    def test_prints_nothing_for_invalid_script_when_silent(self):
        call_command('runscript', 'error_script', silent=True)
        self.assertEqual("", sys.stdout.getvalue())

    def test_doesnt_print_exception_for_nonexistent_script_when_no_traceback(self):
        call_command('runscript', 'error_script', no_traceback=True)
        self.assertEqual("", sys.stderr.getvalue())
        self.assertIn("Exception while running run() in", sys.stdout.getvalue())


class RunFunctionTests(RunScriptTests):
    def test_prints_error_message_for_script_without_run(self):
        call_command('runscript', 'script_no_run_function')
        self.assertIn("No (valid) module for script 'script_no_run_function' found", sys.stdout.getvalue())
        self.assertIn("Try running with a higher verbosity level like: -v2 or -v3", sys.stdout.getvalue())

    def test_prints_additional_info_for_script__run_extra_verbosity(self):
        call_command('runscript', 'script_no_run_function', verbosity=2)
        self.assertIn("No (valid) module for script 'script_no_run_function' found", sys.stdout.getvalue())
        self.assertIn("Found script", sys.stdout.getvalue())

    def test_prints_nothing_for_script_without_run(self):
        call_command('runscript', 'script_no_run_function', silent=True)
        self.assertEqual("", sys.stdout.getvalue())
