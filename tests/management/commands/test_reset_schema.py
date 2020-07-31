# -*- coding: utf-8 -*-
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings

from unittest import mock


class ResetSchemaExceptionsTests(TestCase):
    """Tests if reset_schema command raises exceptions."""

    def test_should_raise_CommandError_when_database_does_not_exist(self):
        with self.assertRaisesRegex(CommandError, 'Unknown database non-existing_database'):
            call_command('reset_schema', '--database=non-existing_database')

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.mysql',
        },
    })
    def test_should_raise_CommandError_when_database_ENGINE_different_thant_postgresql(self):
        with self.assertRaisesRegex(CommandError, 'This command can be used only with PostgreSQL databases.'):
            call_command('reset_schema')


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'test',
        'USER': 'test',
        'PASSWORD': 'test',
        'HOST': 'localhost',
    },
})
class ResetSchemaTests(TestCase):
    """Tests for reset_chema command."""

    def test_should_drop_schema_and_create_new_one(self):
        m_cursor = mock.Mock()
        m_router = mock.Mock()
        m_router.cursor.return_value = mock.Mock(
            __enter__=mock.Mock(return_value=m_cursor),
            __exit__=mock.Mock(return_value=False),
        )
        expected_calls = [
            mock.call('DROP SCHEMA test_public CASCADE'),
            mock.call('CREATE SCHEMA test_public'),
        ]

        with mock.patch('django_extensions.management.commands.reset_schema.connections', {'default': m_router}):
            call_command('reset_schema', '--noinput', '--schema=test_public')

        m_cursor.execute.assert_has_calls(expected_calls, any_order=False)

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('django_extensions.management.commands.reset_schema.input')
    def test_should_cancel_reset_schema_and_print_info_if_input_is_different_than_yes(self, m_input, m_stdout):
        m_input.return_value = 'no'

        call_command('reset_schema')

        self.assertEqual("Reset cancelled.\n", m_stdout.getvalue())
