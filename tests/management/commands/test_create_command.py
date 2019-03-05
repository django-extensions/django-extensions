# -*- coding: utf-8 -*-
import os
import shutil

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from six import StringIO

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


class CreateCommandTests(TestCase):
    """Tests for create_command command."""

    def setUp(self):  # noqa
        self.management_command_path = os.path.join(
            settings.BASE_DIR, 'tests/testapp/management')
        self.command_template_path = os.path.join(
            settings.BASE_DIR, 'django_extensions/conf/command_template')

        self.files = ['__init__.py', 'commands/__init__.py',
                      'commands/sample.py']

    def tearDown(self):  # noqa
        shutil.rmtree(self.management_command_path,
                      ignore_errors=True)
        shutil.rmtree(os.path.join(self.command_template_path, '.hidden'),
                      ignore_errors=True)
        test_pyc_path = os.path.join(self.command_template_path, 'test.pyc')
        if os.path.isfile(test_pyc_path):
            os.remove(test_pyc_path)

    def _create_management_command_with_empty_files(self):
        os.mkdir(self.management_command_path)
        os.mkdir(os.path.join(self.management_command_path, 'commands'))
        for f in self.files:
            os.mknod(os.path.join(self.management_command_path, f))

    def _create__pycache__in_command_template_directory(self):
        os.mknod(os.path.join(self.command_template_path, 'test.pyc'))

    def _create_hidden_directory_in_command_template_directory(self):
        os.mkdir(os.path.join(self.command_template_path, '.hidden'))

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_management_command_files_only_on_dry_run(self, m_stdout):  # noqa
        call_command('create_command', 'testapp', '--dry-run', verbosity=2)

        for f in self.files:
            filepath = os.path.join(self.management_command_path, f)
            self.assertIn(filepath, m_stdout.getvalue())
            self.assertFalse(os.path.isfile(filepath))

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_create_management_command_files_and_print_filepaths(self, m_stdout):  # noqa
        call_command('create_command', 'testapp', verbosity=2)

        for f in self.files:
            filepath = os.path.join(self.management_command_path, f)
            self.assertIn(filepath, m_stdout.getvalue())
            self.assertTrue(os.path.isfile(filepath))

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_that_filepaths_already_exists(self, m_stdout):  # noqa
        self._create_management_command_with_empty_files()

        call_command('create_command', 'testapp', verbosity=2)

        for f in self.files:
            filepath = os.path.join(self.management_command_path, f)
            self.assertIn(
                '{} already exists'.format(filepath), m_stdout.getvalue())
            self.assertTrue(os.path.isfile(filepath))
            self.assertEqual(os.path.getsize(filepath), 0)

    @patch('sys.stderr', new_callable=StringIO)
    @patch('django_extensions.management.commands.create_command._make_writeable')  # noqa
    def test_should_print_error_on_OSError_exception(self, m__make_writeable, m_stderr):  # noqa
        m__make_writeable.side_effect = OSError
        self._create__pycache__in_command_template_directory()
        self._create_hidden_directory_in_command_template_directory()

        call_command('create_command', 'testapp')
        for f in self.files:
            filepath = os.path.join(self.management_command_path, f)
            self.assertIn("Notice: Couldn't set permission bits on {}. You're probably using an uncommon filesystem setup. No problem.\n".format(filepath),  # noqa
                          m_stderr.getvalue())
