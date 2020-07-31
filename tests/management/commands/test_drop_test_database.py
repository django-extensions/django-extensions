# -*- coding: utf-8 -*-
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings

from unittest.mock import MagicMock, Mock, patch


class DropTestDatabaseExceptionsTests(TestCase):
    """Test for drop_test_database command."""

    def test_should_raise_CommandError_if_database_is_unknown(self):
        with self.assertRaisesRegex(CommandError, "Unknown database unknown"):
            call_command('drop_test_database', '--database=unknown')

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.unknown',
            'NAME': 'unknown',
        }
    })
    @patch('django_extensions.management.commands.drop_test_database.input')
    def test_should_raise_CommandError_if_unknown_database_engine(self, m_input):
        m_input.return_value = 'yes'
        with self.assertRaisesRegex(CommandError, "Unknown database engine unknown"):
            call_command('drop_test_database')

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'test',
            'TEST': {
                'NAME': '',
            }
        }
    })
    def test_shoul_raise_CommandError_if_test_database_name_is_empty(self):
        with self.assertRaisesRegex(CommandError, "You need to specify DATABASE_NAME in your Django settings file."):
            call_command('drop_test_database')


class DropTestDatabaseTests(TestCase):
    """Test for drop_test_database command."""

    @patch('sys.stdout', new_callable=StringIO)
    @patch('django_extensions.management.commands.drop_test_database.input')
    def test_should_raise_CommandError_if_database_is_unknown(self, m_input, m_stdout):
        m_input.return_value = 'no'

        call_command('drop_test_database')

        self.assertEqual("Reset cancelled.\n", m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }
    })
    @patch('sys.stdout', new_callable=StringIO)
    @patch('os.path.isfile')
    @patch('os.unlink')
    def test_sqlite3_should_unlink_database(self, m_unlink, m_isfile, m_stdout):
        m_isfile.return_value = True
        call_command('drop_test_database', '--noinput', verbosity=2)

        m_unlink.assert_called_once_with('test_db.sqlite3')
        self.assertIn("Reset successful.", m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }
    })
    @patch('sys.stdout', new_callable=StringIO)
    @patch('os.path.isfile')
    @patch('os.unlink')
    def test_sqlite3_should_not_print_Reset_successful_when_OSError_exception(self, m_unlink, m_isfile, m_stdout):
        m_isfile.return_value = True
        m_unlink.side_effect = OSError
        call_command('drop_test_database', '--noinput', verbosity=2)

        self.assertNotIn("Reset successful.", m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'test',
            'USER': 'test',
            'PASSWORD': 'test',
            'HOST': 'localhost',
            'PORT': '3306',
        },
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_mysql_should_drop_datatabase_with_host_and_port(self, m_stdout):
        m_database = MagicMock()
        m_connection = Mock()
        m_database.connect.return_value = m_connection

        with patch.dict("sys.modules", MySQLdb=m_database):
            call_command('drop_test_database', '--noinput', verbosity=2)

        m_connection.query.assert_called_with(
            'DROP DATABASE IF EXISTS `test_test`')

        self.assertIn("Reset successful.", m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'test',
            'USER': 'test',
            'PASSWORD': 'test',
            'HOST': '/var/run/mysqld/mysql.sock',
        },
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_mysql_should_drop_datatabase_with_unix_socket(self, m_stdout):
        m_database = MagicMock()
        m_connection = Mock()
        m_database.connect.return_value = m_connection

        with patch.dict("sys.modules", MySQLdb=m_database):
            call_command('drop_test_database', '--noinput', verbosity=2)

        m_connection.query.assert_called_with(
            'DROP DATABASE IF EXISTS `test_test`')

        self.assertIn("Reset successful.", m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'test',
            'USER': 'test',
            'PASSWORD': 'test',
            'PORT': '5432',
            'HOST': 'localhost',
        },
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_postgresql_should_drop_database(self, m_stdout):
        m_database = MagicMock()
        m_cursor = Mock()
        m_database.connect.return_value.cursor.return_value = m_cursor

        with patch.dict("sys.modules", psycopg2=m_database):
            call_command('drop_test_database', '--noinput', verbosity=2)

        m_cursor.execute.assert_called_once_with(
            'DROP DATABASE IF EXISTS "test_test";')
        self.assertIn("Reset successful.", m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'test',
            'USER': 'test',
            'PASSWORD': 'test',
            'PORT': '5432',
            'HOST': 'localhost',
        },
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_postgresql_should_not_print_Reset_successful_when_exception_occured(self, m_stdout):
        m_database = MagicMock()
        m_database.ProgrammingError = Exception
        m_cursor = Mock()
        m_cursor.execute.side_effect = m_database.ProgrammingError
        m_database.connect.return_value.cursor.return_value = m_cursor

        with patch.dict("sys.modules", psycopg2=m_database):
            call_command('drop_test_database', '--noinput', verbosity=2)

        self.assertNotIn("Reset successful.", m_stdout.getvalue())
