# -*- coding: utf-8 -*-
import os
from distutils.version import LooseVersion

import pytest
from django import get_version
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from six import StringIO

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

TEST_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@override_settings(FIXTURE_DIRS=[TEST_FIXTURE_DIR])
class SyncDataExceptionsTests(TestCase):
    """Tests for SyncData command exceptions."""

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

    @pytest.mark.skipif(
        LooseVersion(get_version()) < LooseVersion('2.0.0'),
        reason="This test works only on Django greater than 2.x")
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_return_SyncDataError_when_multiple_fixtures(self, m_stdout):  # noqa
        call_command('syncdata', 'users', verbosity=2)
        self.assertIn(
            "Multiple fixtures named 'users' in '{}'. Aborting.\n".format(
                TEST_FIXTURE_DIR), m_stdout.getvalue())


@override_settings(FIXTURE_DIRS=[TEST_FIXTURE_DIR])
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

    def test_should_keep_old_objects_and_load_data_from_json_fixture(self):  # noqa
        User.objects.create(username='foo')

        call_command('syncdata', '--skip-remove',
                     os.path.join(TEST_FIXTURE_DIR, 'users.json'), verbosity=2)

        self.assertTrue(User.objects.filter(username='jdoe').exists())
        self.assertTrue(User.objects.filter(username='foo').exists())

    @pytest.mark.skipif(
        LooseVersion(get_version()) < LooseVersion('2.0.0'),
        reason="This test works only on Django greater than 2.x")
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_delete_old_objects_and_load_data_from_json_fixture(self, m_stdout):  # noqa
        User.objects.create(username='foo')

        call_command('syncdata', 'users.json', verbosity=2)

        self.assertTrue(User.objects.filter(username='jdoe').exists())
        self.assertEqual(User.objects.count(), 1)
        self.assertIn(
            'Installed 1 object from 1 fixture', m_stdout.getvalue())
