# -*- coding: utf-8 -*-
import os
from distutils.version import LooseVersion

import pytest
from unittest.mock import patch

from django import get_version
from django.core.management import CommandError, call_command
from django.db import models
from django.test import TestCase, override_settings
from tests import testapp_with_appconfig

MIGRATIONS_DIR = os.path.join(testapp_with_appconfig.__path__[0], 'migrations')


@override_settings(MIGRATION_MODULES={'testapp_with_appconfig': 'tests.testapp_with_appconfig.migrations'})
class BaseDeleteSquashedMigrationsTestCase(TestCase):
    def migration_exists(self, filename):
        return os.path.exists(os.path.join(MIGRATIONS_DIR, filename))

    def setUp(self):
        class TitleModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            title = models.CharField(max_length=50)

            class Meta:
                app_label = 'testapp_with_appconfig'

        call_command('makemigrations')

    def tearDown(self):
        for root, dirs, files in os.walk(MIGRATIONS_DIR):
            for filename in files:
                if filename.startswith('000'):
                    os.remove(os.path.join(root, filename))


@pytest.mark.xfail
@pytest.mark.skipif(
    LooseVersion(get_version()) <= LooseVersion('2.0.0'),
    reason="This test works only on Django greater than 2.0.0",
)
class DeleteSquashedMigrationsExceptionsTests(BaseDeleteSquashedMigrationsTestCase):
    """Tests for delete_squashed_migrations command exceptions."""

    def test_should_raise_CommandError_if_app_does_not_have_migrations(self):
        with self.assertRaisesRegex(
                CommandError,
                r"App 'testapp_with_no_models_file' does not have migrations \(so delete_squashed_migrations on it makes no sense\)"):

            call_command('delete_squashed_migrations', 'testapp_with_no_models_file')

    def test_should_raise_CommandEror_if_migration_is_not_squashed(self):
        with self.assertRaisesRegex(
                CommandError,
                "The migration testapp_with_appconfig 0001_initial is not a squashed migration."):

            call_command('delete_squashed_migrations', 'testapp_with_appconfig',
                         '0001')

    def test_should_raise_CommandEror_if_more_than_one_migration_matches_to_given_arg(self):
        class NameModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            name = models.CharField(max_length=50)

            class Meta:
                app_label = 'testapp_with_appconfig'

        call_command('makemigrations', 'testapp_with_appconfig')
        call_command('squashmigrations', 'testapp_with_appconfig', '0002', '--noinput')

        with self.assertRaisesRegex(
                CommandError,
                "More than one migration matches '0001' in app 'testapp_with_appconfig'. Please be more specific."):

            call_command('delete_squashed_migrations', 'testapp_with_appconfig', '0001')

    def test_should_raise_CommandEror_if_squashed_migration_not_found(self):
        class NameModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            name = models.CharField(max_length=50)

            class Meta:
                app_label = 'testapp_with_appconfig'

        call_command('makemigrations', 'testapp_with_appconfig')

        with self.assertRaisesRegex(
                CommandError,
                "Cannot find a squashed migration in app 'testapp_with_appconfig'."):

            call_command('delete_squashed_migrations', 'testapp_with_appconfig')

    def test_should_raise_CommandEror_if_squashed_migration_not_foundee(self):
        with self.assertRaisesRegex(
                CommandError,
                "Cannot find a migration matching '0002' from app 'testapp_with_appconfig'."):

            call_command('delete_squashed_migrations', 'testapp_with_appconfig',
                         '0002')

    def test_should_raise_CommandError_when_database_does_not_exist(self):
        with self.assertRaisesRegex(CommandError, 'Unknown database non-existing_database'):
            call_command('delete_squashed_migrations', '--database=non-existing_database')


@pytest.mark.xfail
@pytest.mark.skipif(
    LooseVersion(get_version()) <= LooseVersion('2.0.0'),
    reason="This test works only on Django greater than 2.0.0",
)
class DeleteSquashedMigrationsTests(BaseDeleteSquashedMigrationsTestCase):
    """Tests for delete_squashed_migrations command."""

    @patch('django_extensions.management.commands.delete_squashed_migrations.six.moves.input')
    def test_should_delete_squashed_migrations(self, m_input):
        m_input.return_value = 'y'

        class NameModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            name = models.CharField(max_length=50)

            class Meta:
                app_label = 'testapp_with_appconfig'

        call_command('makemigrations', 'testapp_with_appconfig')
        call_command('squashmigrations', 'testapp_with_appconfig', '0002', '--noinput')
        call_command('delete_squashed_migrations', 'testapp_with_appconfig')

        self.assertFalse(self.migration_exists('0001_initial.py'))
        self.assertFalse(self.migration_exists('0002_namemodel.py'))
        self.assertTrue(self.migration_exists('0001_squashed_0002_namemodel.py'))

    def test_should_delete_squashed_migrations_if_interactive_mode_is_set_to_False(self):
        class NameModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            name = models.CharField(max_length=50)

            class Meta:
                app_label = 'testapp_with_appconfig'

        call_command('makemigrations', 'testapp_with_appconfig')
        call_command('squashmigrations', 'testapp_with_appconfig', '0002', '--noinput')
        call_command('delete_squashed_migrations', 'testapp_with_appconfig', interactive=False)

        self.assertFalse(self.migration_exists('0001_initial.py'))
        self.assertFalse(self.migration_exists('0002_namemodel.py'))
        self.assertTrue(self.migration_exists('0001_squashed_0002_namemodel.py'))

    @patch('django_extensions.management.commands.delete_squashed_migrations.six.moves.input')
    def test_should_not_delete_anything(self, m_input):
        m_input.return_value = None

        class NameModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            name = models.CharField(max_length=50)

            class Meta:
                app_label = 'testapp_with_appconfig'

        call_command('makemigrations', 'testapp_with_appconfig')
        call_command('squashmigrations', 'testapp_with_appconfig', '0002', '--noinput')
        call_command('delete_squashed_migrations', 'testapp_with_appconfig')

        self.assertTrue(self.migration_exists('0001_initial.py'))
        self.assertTrue(self.migration_exists('0002_namemodel.py'))
        self.assertTrue(self.migration_exists('0001_squashed_0002_namemodel.py'))

    def test_should_not_delete_files_for_given_squashed_migration(self):
        class NameModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            name = models.CharField(max_length=50)

            class Meta:
                app_label = 'testapp_with_appconfig'

        call_command('makemigrations', 'testapp_with_appconfig')
        call_command('squashmigrations', 'testapp_with_appconfig', '0002', '--noinput')

        class FooModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            name = models.CharField(max_length=50)

            class Meta:
                app_label = 'testapp_with_appconfig'

        call_command('makemigrations', 'testapp_with_appconfig')
        call_command('delete_squashed_migrations', 'testapp_with_appconfig',
                     '0001_squashed_0002_namemodel', interactive=False)

        self.assertFalse(self.migration_exists('0001_initial.py'))
        self.assertFalse(self.migration_exists('0002_namemodel.py'))
        self.assertTrue(self.migration_exists('0001_squashed_0002_namemodel.py'))
        self.assertTrue(self.migration_exists('0002_foomodel.py'))
