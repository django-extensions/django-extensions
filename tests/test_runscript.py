# -*- coding: utf-8 -*-
import os
import sys
import importlib

from io import StringIO
from django.core.management import call_command
from django.test import TestCase, override_settings

from django_extensions.management.commands.runscript import BadCustomDirectoryException, DirPolicyChoices


class RunScriptTests(TestCase):

    def setUp(self):
        sys.stdout = StringIO()
        sys.stderr = StringIO()

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
        self.assertRegex(sys.stdout.getvalue(), 'No module named (\')?(invalidpackage)\1?')

    def test_prints_import_error_on_script_with_invalid_imports_reliably(self):
        if hasattr(importlib, 'util') and hasattr(importlib.util, 'find_spec'):
            with self.settings(BASE_DIR=os.path.dirname(os.path.abspath(__file__))):
                call_command('runscript', 'invalid_import_script')
                self.assertIn("Cannot import module 'tests.testapp.scripts.invalid_import_script'", sys.stdout.getvalue())
                self.assertRegex(sys.stdout.getvalue(), 'No module named (\')?(invalidpackage)\1?')


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


project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class ChangingDirectoryTests(RunScriptTests):
    def setUp(self):
        super().setUp()
        self.curwd = os.getcwd()
        os.chdir(project_path)

    def tearDown(self):
        super().setUp()
        os.chdir(self.curwd)

    def _execute_script_with_chdir(self, dir_policy, start_path, expected_path, chdir=None):
        os.chdir(os.path.join(project_path, *start_path))
        expected_path = os.path.join(project_path, *expected_path)
        call_command('runscript', 'directory_checker_script', dir_policy=dir_policy, chdir=chdir)
        output = sys.stdout.getvalue().split('Script called from: ')[1]
        self.assertEqual(output, expected_path + '\n')

    def test_none_policy_command_run(self):
        self._execute_script_with_chdir(DirPolicyChoices.NONE, [], [])

    def test_none_policy_command_run_with_chdir(self):
        self._execute_script_with_chdir(DirPolicyChoices.NONE, ['tests'], ['tests'])

    def test_none_policy_freezing_start_directory(self):
        self._execute_script_with_chdir(DirPolicyChoices.NONE, ['tests'], ['tests'])
        self._execute_script_with_chdir(DirPolicyChoices.NONE, ['tests'], ['tests'])

    def test_root_policy_command_run(self):
        self._execute_script_with_chdir(DirPolicyChoices.ROOT, ['tests'], [])

    def test_each_policy_command_run(self):
        os.chdir(os.path.join(project_path, 'tests'))
        call_command('runscript', 'directory_checker_script', 'other_directory_checker_script',
                     dir_policy=DirPolicyChoices.EACH)
        output = sys.stdout.getvalue()
        first_output = output.split('Script called from: ')[1].split('Cannot import module ')[0]
        self.assertEqual(first_output, os.path.join(project_path, 'tests', 'testapp', 'scripts') + '\n')
        second_output = output.split('Script called from: ')[2].split('Cannot import module ')[0]
        self.assertEqual(second_output,
                         os.path.join(project_path, 'tests', 'testapp_with_no_models_file', 'scripts') + '\n')

    def test_chdir_specified(self):
        execution_path = os.path.join(project_path, 'django_extensions', 'management')
        self._execute_script_with_chdir(DirPolicyChoices.ROOT, ['tests'], ['django_extensions', 'management'],
                                        chdir=execution_path)

    @override_settings(RUNSCRIPT_CHDIR=os.path.join(project_path, 'tests'))
    def test_policy_from_cli_and_chdir_from_settings(self):
        self._execute_script_with_chdir(DirPolicyChoices.ROOT, ['tests'], [])

    @override_settings(
        RUNSCRIPT_CHDIR=os.path.join(project_path, 'django_extensions', 'management'),
        RUNSCRIPT_CHDIR_POLICY=DirPolicyChoices.ROOT,
    )
    def test_chdir_from_settings_and_policy_from_settings(self):
        self._execute_script_with_chdir(None, ['tests'], ['django_extensions', 'management'])

    @override_settings(RUNSCRIPT_CHDIR_POLICY=DirPolicyChoices.EACH)
    def test_policy_from_settings(self):
        self._execute_script_with_chdir(None, ['tests'], ['tests', 'testapp', 'scripts'])

    @override_settings(RUNSCRIPT_CHDIR=os.path.join(project_path, 'tests'))
    def test_chdir_django_settings(self):
        self._execute_script_with_chdir(None, [], ['tests'])

    @override_settings(RUNSCRIPT_CHDIR='bad path')
    def test_custom_policy_django_settings_bad_path(self):
        with self.assertRaisesRegex(
            BadCustomDirectoryException,
            'bad path is not a directory! If --dir-policy is custom than you must set '
            'correct directory in --dir option or in settings.RUNSCRIPT_CHDIR'
        ):
            self._execute_script_with_chdir(None, [], ['tests'])

    def test_skip_printing_modules_which_does_not_exist(self):
        call_command('runscript', 'directory_checker_script')
        self.assertNotIn('No module named', sys.stdout.getvalue())
        self.assertNotIn('No module named', sys.stderr.getvalue())
