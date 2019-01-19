from __future__ import print_function, unicode_literals

import os
import pytest
from django import get_version
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.utils.six import StringIO
from distutils.version import StrictVersion


try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


@override_settings(
    FIXTURE_DIRS=[os.path.join(os.path.dirname(__file__), 'fixtures')])
class SyncDataExceptionsTests(TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_return_SyncDataError_when_unknown_fixture_format(self, m_stdout):  # noqa
        call_command('syncdata', 'foo.jpeg', verbosity=2)
        self.assertEqual(
            "Problem installing fixture 'foo': jpeg is not a known serialization format.\n",  # noqa
            m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_return_SyncDataError_when_file_not_contains_valid_fixture_data(self, m_stdout):  # noqa
        call_command('syncdata', 'invalid_fixture.xml', verbosity=2)
        self.assertIn(
            "No fixture data found for 'invalid_fixture'. (File format may be invalid.)\n",  # noqa
            m_stdout.getvalue())

    def test_WIP(self):  # noqa
        call_command('syncdata', 'users', verbosity=2)


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

    def test_should_keep_old_objects_and_load_data_from_json_fixture(self):
        User.objects.create(username='foo')

        call_command('syncdata', '--skip-remove', 'users.json', verbosity=2)

        self.assertTrue(User.objects.filter(username='jdoe').exists())
        self.assertTrue(User.objects.filter(username='foo').exists())

    @patch('sys.stdout', new_callable=StringIO)
    @pytest.mark.skipif(StrictVersion(get_version()) < StrictVersion('2.0.0'),  # noqa
                        reason="This test works only on Django 2.x")
    def test_should_delete_old_objects_and_load_data_from_json_fixture(self, m_stdout):  # noqa
        User.objects.create(username='foo')

        call_command('syncdata', 'users.json', verbosity=2)

        self.assertTrue(User.objects.filter(username='jdoe').exists())
        self.assertEqual(User.objects.count(), 1)
        self.assertIn(
            'Installed 1 object from 1 fixture', m_stdout.getvalue())
