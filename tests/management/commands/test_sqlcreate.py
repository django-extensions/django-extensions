# -*- coding: utf-8 -*-
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings

from unittest.mock import patch


MYSQL_DATABASE_SETTINGS = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'dbatabase',
    'USER': 'foo',
    'PASSWORD': 'bar',
    'HOST': '127.0.0.1',
    'PORT': '3306',
}

SQLITE3_DATABASE_SETTINGS = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'db.sqlite3',
}

POSTGRESQL_DATABASE_SETTINGS = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'database',
    'USER': 'foo',
    'PASSWORD': 'bar',
    'HOST': 'localhost',
    'PORT': '5432',
}


class SqlcreateExceptionsTests(TestCase):
    """Test for sqlcreate exception."""

    def test_should_raise_CommandError_if_database_is_unknown(self):
        with self.assertRaisesRegex(CommandError, "Unknown database unknown"):
            call_command('sqlcreate', '--database=unknown')


class SqlCreateTests(TestCase):
    """Tests for sqlcreate command."""

    @override_settings(DATABASES={'default': MYSQL_DATABASE_SETTINGS})
    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    @patch('django_extensions.management.commands.sqlcreate.socket')
    def test_should_print_SQL_create_database_statement_for_mysql(self, m_socket, m_stdout, m_stderr):
        m_socket.gethostname.return_value = 'tumbleweed'
        expected_error = """-- WARNING!: https://docs.djangoproject.com/en/dev/ref/databases/#collation-settings
-- Please read this carefully! Collation will be set to utf8_bin to have case-sensitive data.
"""
        expected_statement = """CREATE DATABASE dbatabase CHARACTER SET utf8 COLLATE utf8_bin;
GRANT ALL PRIVILEGES ON dbatabase.* to 'foo'@'tumbleweed' identified by 'bar';
"""

        call_command('sqlcreate')

        self.assertEqual(expected_statement, m_stdout.getvalue())
        self.assertEqual(expected_error, m_stderr.getvalue())

    @override_settings(DATABASES={'default': POSTGRESQL_DATABASE_SETTINGS})
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_SQL_create_database_statement_for_postgresql(self, m_stdout):
        expected_statement = """CREATE USER foo WITH ENCRYPTED PASSWORD 'bar' CREATEDB;
CREATE DATABASE database WITH ENCODING 'UTF-8' OWNER "foo";
GRANT ALL PRIVILEGES ON DATABASE database TO foo;
"""

        call_command('sqlcreate')

        self.assertEqual(expected_statement, m_stdout.getvalue())

    @override_settings(DATABASES={'default': POSTGRESQL_DATABASE_SETTINGS})
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_SQL_drop_and_create_database_statement_for_postgresql(self, m_stdout):
        expected_statement = """DROP DATABASE IF EXISTS database;
DROP USER IF EXISTS foo;
CREATE USER foo WITH ENCRYPTED PASSWORD 'bar' CREATEDB;
CREATE DATABASE database WITH ENCODING 'UTF-8' OWNER "foo";
GRANT ALL PRIVILEGES ON DATABASE database TO foo;
"""

        call_command('sqlcreate', '--drop')

        self.assertEqual(expected_statement, m_stdout.getvalue())

    @override_settings(DATABASES={'default': SQLITE3_DATABASE_SETTINGS})
    @patch('sys.stderr', new_callable=StringIO)
    def test_should_print_stderr_for_sqlite3(self, m_stderr):
        expected_error = "-- manage.py syncdb will automatically create a sqlite3 database file.\n"

        call_command('sqlcreate')

        self.assertEqual(expected_error, m_stderr.getvalue())

    @override_settings(DATABASES={
        'unknown': {
            'ENGINE': 'django.db.backends.unknown',
            'NAME': 'database',
            'USER': 'foo',
        }
    })
    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_stderr_and_standard_create_database_statement_for_unsupported_engine(self, m_stdout, m_stderr):
        expected_error = "-- Don't know how to handle 'unknown' falling back to SQL.\n"
        expected_statement = """CREATE DATABASE database;
GRANT ALL PRIVILEGES ON DATABASE database to foo;
"""

        call_command('sqlcreate', '--database=unknown')

        self.assertEqual(expected_error, m_stderr.getvalue())
        self.assertEqual(expected_statement, m_stdout.getvalue())
