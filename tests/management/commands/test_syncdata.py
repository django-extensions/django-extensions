from __future__ import unicode_literals
import os

from django.contrib.auth.models import User
from django.db.models import Q
from django.core.management import CommandError, call_command
from django.test import TransactionTestCase, TestCase
from django.test.utils import override_settings
from ...testapp.models import Secret

from django.utils.six import StringIO
import unittest

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


@override_settings(
    FIXTURE_DIRS=[os.path.join(os.path.dirname(__file__), 'fixtures')])
class SyncDataTests(TestCase):
    """Tests for syncdata command."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_No_fixtures_found_if_fixture_labels_not_provided(self, m_stdout):  # noqa
        call_command('syncdata', verbosity=2)

        self.assertEqual('No fixtures found.\n', m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_No_fixtures_found_if_fixtures_not_found(self, m_stdout):  # noqa
        call_command('syncdata', 'foo', verbosity=2)

        self.assertIn('No fixtures found.\n', m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_delete_old_objects_and_load_data_from_json_fixture(self, m_stdout):  # noqa
        for username in ['foo', 'bar']:
            User.objects.create(username=username)

        call_command('syncdata', 'users.json', verbosity=2)

        self.assertTrue(User.objects.filter(username='jdoe').exists())
        self.assertEqual(User.objects.count(), 1)
        self.assertIn(
            'Installed 1 object from 1 fixture', m_stdout.getvalue())

    def test_should_keep_old_objects_and_load_data_from_json_fixture(self):
        User.objects.create(username='foo')

        call_command('syncdata', '--skip-remove', 'users', verbosity=2)

        self.assertTrue(User.objects.filter(username='jdoe').exists())
        self.assertTrue(User.objects.filter(username='foo').exists())
        self.assertEqual(User.objects.count(), 2)

