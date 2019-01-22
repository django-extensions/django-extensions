# -*- coding: utf-8 -*-
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.six import StringIO

try:
    from unittest.mock import Mock, call, patch
except ImportError:
    from mock import Mock, call, patch


class ResetSchemaExceptionsTests(TestCase):
    """Tests if reset_schema command raises exceptions."""

    def test_should_raise_CommandError_when_router_does_not_exist(self):  # noqa
        with self.assertRaisesRegexp(
                CommandError, 'Unknown database router non-existing_router'):
            call_command('reset_schema', '--router=non-existing_router')

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.mysql',
        },
    })
    def test_should_raise_CommandError_when_database_ENGINE_different_thant_postgresql(self):  # noqa
        with self.assertRaisesRegexp(
                CommandError,
                'This command can be used only with PostgreSQL databases.'):
            call_command('reset_schema')


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'test',
        'USER': 'test',
        'PASSWORD': 'test',
        'HOST': 'localhost'
    },
})
class ResetSchemaTests(TestCase):
    """Tests for reset_chema command."""

    def test_should_drop_schema_and_create_new_one(self):  # noqa
        m_cursor = Mock()
        m_router = Mock()
        m_router.cursor.return_value = Mock(
            __enter__=Mock(return_value=m_cursor),
            __exit__=Mock(return_value=False))
        expected_calls = [
            call('DROP SCHEMA test_public CASCADE'),
            call('CREATE SCHEMA test_public')
        ]

        with patch('django_extensions.management.commands.reset_schema.connections',
                   {'default': m_router}):
            call_command('reset_schema', '--noinput', '--schema=test_public')

        m_cursor.execute.assert_has_calls(expected_calls, any_order=False)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('django_extensions.management.commands.reset_schema.input')
    def test_should_cancel_reset_schema_and_print_info_if_input_is_different_than_yes(self, m_input, m_stdout):  # noqa
        m_input.return_value = 'no'

        call_command('reset_schema')

        self.assertEqual("Reset cancelled.\n", m_stdout.getvalue())
