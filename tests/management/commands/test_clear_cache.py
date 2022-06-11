# -*- coding: utf-8 -*-
import mock
import os
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


DefaultCacheMock = mock.Mock()
OtherCacheMock = mock.Mock()


class ClearCacheTests(TestCase):
    def setUp(self):
        self.project_root = os.path.join('tests', 'testapp')
        self._settings = os.environ.get('DJANGO_SETTINGS_MODULE')
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_extensions.settings'
        DefaultCacheMock.reset_mock()
        OtherCacheMock.reset_mock()
        self.out = StringIO()

    def tearDown(self):
        if self._settings:
            os.environ['DJANGO_SETTINGS_MODULE'] = self._settings

    def test_called_with_no_arguments(self):
        with self.settings(BASE_DIR=self.project_root):
            call_command('clear_cache')
        DefaultCacheMock.return_value.clear.assert_called()
        OtherCacheMock.return_value.clear.assert_not_called()

    def test_called_with_explicit_other(self):
        with self.settings(BASE_DIR=self.project_root):
            call_command('clear_cache', '--cache', 'other')
        DefaultCacheMock.return_value.clear.assert_not_called()
        OtherCacheMock.return_value.clear.assert_called()

    def test_called_with_all_argument(self):
        with self.settings(BASE_DIR=self.project_root):
            call_command('clear_cache', '--all')
        DefaultCacheMock.return_value.clear.assert_called()
        OtherCacheMock.return_value.clear.assert_called()

    def test_called_with_explicit_all(self):
        with self.settings(BASE_DIR=self.project_root):
            call_command('clear_cache', '--cache', 'default', '--cache', 'other',
                         stdout=self.out)
        DefaultCacheMock.return_value.clear.assert_called()
        OtherCacheMock.return_value.clear.assert_called()

        self.assertIn('Cache "default" has been cleared!', self.out.getvalue())
        self.assertIn('Cache "other" has been cleared!', self.out.getvalue())

    def test_called_with_invalid_arguments(self):
        with self.settings(BASE_DIR=self.project_root):
            with self.assertRaisesRegex(CommandError, 'Using both --all and --cache is not supported'):
                call_command('clear_cache', '--all', '--cache', 'foo')

    def test_should_print_that_cache_is_invalid_on_InvalidCacheBackendError(self):
        call_command('clear_cache', '--cache', 'invalid', stderr=self.out)

        self.assertIn('Cache "invalid" is invalid!', self.out.getvalue())
