# -*- coding: utf-8 -*-
import os
from distutils.version import LooseVersion

import pytest
from django import get_version
from django.contrib.auth.models import User
from django.core.management import call_command, CommandError
from django.test import TestCase
from django.test.utils import override_settings
from io import StringIO

from unittest.mock import patch


TEST_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@override_settings(FIXTURE_DIRS=[TEST_FIXTURE_DIR])
class SyncDataExceptionsTests(TestCase):
    """Tests for SyncData command exceptions."""

    def test_should_return_SyncDataError_when_unknown_fixture_format(self):
        with pytest.raises(CommandError, match="Problem installing fixture 'foo': jpeg is not a known serialization format."):
            call_command('syncdata', 'foo.jpeg', verbosity=2)

    def test_should_return_SyncDataError_when_file_not_contains_valid_fixture_data(self):
        with pytest.raises(CommandError, match=r"No fixture data found for 'invalid_fixture'. \(File format may be invalid.\)"):
            call_command('syncdata', 'invalid_fixture.xml', verbosity=2)

    def test_should_return_SyncDataError_when_file_has_non_existent_field_in_fixture_data(self):
        with pytest.raises(CommandError, match=r"Problem installing fixture '.+fixture_with_nonexistent_field.json'"):
            call_command('syncdata', 'fixture_with_nonexistent_field.json', verbosity=1)
        with pytest.raises(CommandError, match="django.core.exceptions.FieldDoesNotExist: User has no field named 'non_existent_field'"):
            call_command('syncdata', 'fixture_with_nonexistent_field.json', verbosity=1)

    @pytest.mark.skipif(
        LooseVersion(get_version()) < LooseVersion('2.0.0'),
        reason="This test works only on Django greater than 2.x",
    )
    def test_should_return_SyncDataError_when_multiple_fixtures(self):
        with pytest.raises(CommandError, match="Multiple fixtures named 'users' in '{}'. Aborting.".format(TEST_FIXTURE_DIR)):
            call_command('syncdata', 'users', verbosity=2)


@override_settings(FIXTURE_DIRS=[TEST_FIXTURE_DIR])
class SyncDataTests(TestCase):
    """Tests for syncdata command."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_No_fixtures_found_if_fixture_labels_not_provided(self, m_stdout):
        call_command('syncdata', verbosity=2)

        self.assertEqual('No fixtures found.\n', m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_No_fixtures_found_if_fixtures_not_found(self, m_stdout):
        call_command('syncdata', 'foo', verbosity=2)

        self.assertIn('No fixtures found.\n', m_stdout.getvalue())

    def test_should_keep_old_objects_and_load_data_from_json_fixture(self):
        User.objects.all().delete()
        User.objects.create(username='foo')

        call_command('syncdata', '--skip-remove', os.path.join(TEST_FIXTURE_DIR, 'users.json'), verbosity=2)

        self.assertTrue(User.objects.filter(username='jdoe').exists())
        self.assertTrue(User.objects.filter(username='foo').exists())

    @pytest.mark.skipif(
        LooseVersion(get_version()) < LooseVersion('2.0.0'),
        reason="This test works only on Django greater than 2.x",
    )
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_delete_old_objects_and_load_data_from_json_fixture(self, m_stdout):
        User.objects.all().delete()
        User.objects.create(username='foo')

        call_command('syncdata', 'users.json', verbosity=2)

        self.assertTrue(User.objects.filter(username='jdoe').exists())
        self.assertEqual(User.objects.count(), 1)
        self.assertIn('Installed 1 object from 1 fixture', m_stdout.getvalue())
