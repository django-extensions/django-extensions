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

POSTGRESQL_PSYCOPG2_DATABASE_SETTINGS = {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'database',
    'USER': 'foo',
    'PASSWORD': 'bar',
    'HOST': 'localhost',
    'PORT': '5432',
}

POSTGIS_DATABASE_SETTINGS = {
    'ENGINE': 'django.db.backends.postgis',
    'NAME': 'database',
    'USER': 'foo',
    'PASSWORD': 'bar',
    'HOST': 'localhost',
}

POSTGIS_WITH_PORT_DATABASE_SETTINGS = {
    'ENGINE': 'django.db.backends.postgis',
    'NAME': 'database',
    'USER': 'foo',
    'PASSWORD': 'bar',
    'HOST': 'localhost',
    'PORT': 5432
}


class SqlDsnExceptionsTests(TestCase):
    """Tests for sqldsn management command exceptions."""

    @override_settings(DATABASES={})
    def test_should_raise_CommandError_if_unknown_database_does_not_exist(self):
        with self.assertRaisesRegex(CommandError, "Unknown database unknown"):
            call_command('sqldsn', '--database=unknown')


class SqlDsnTests(TestCase):
    """Tests for sqldsn management command."""
    maxDiff = None

    @override_settings(DATABASES={'default': SQLITE3_DATABASE_SETTINGS})
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info_for_default_sqlite3_database(self, m_stdout):
        expected_result = """DSN for database 'default' with engine 'sqlite3':
db.sqlite3
"""
        call_command('sqldsn')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={'default': MYSQL_DATABASE_SETTINGS})
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_quiet_info_for_mysql_database(self, m_stdout):
        expected_result = """host="127.0.0.1", db="dbatabase", user="foo", passwd="bar", port="3306"
"""
        call_command('sqldsn', '-q')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={'default': POSTGRESQL_DATABASE_SETTINGS})
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_all_info_for_postgresql_database(self, m_stdout):
        expected_result = """DSN for database 'default' with engine 'postgresql':
host='localhost' dbname='database' user='foo' password='bar' port='5432'
"""

        call_command('sqldsn', '-a')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={'default': POSTGRESQL_PSYCOPG2_DATABASE_SETTINGS})
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info__with_kwargs_style_for_postgresql_psycopg2_database(self, m_stdout):
        expected_result = """DSN for database 'default' with engine 'postgresql_psycopg2':
host='localhost', database='database', user='foo', password='bar', port='5432'
"""

        call_command('sqldsn', '--style=kwargs')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={'default': POSTGIS_WITH_PORT_DATABASE_SETTINGS})
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info__with_uri_style_for_postgis_database(self, m_stdout):
        expected_result = """DSN for database 'default' with engine 'postgis':
postgresql://foo:bar@localhost:5432/database
"""

        call_command('sqldsn', '--style=uri')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={'default': POSTGIS_DATABASE_SETTINGS})
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info__with_uri_style_without_port_for_postgis_database(self, m_stdout):
        expected_result = """DSN for database 'default' with engine 'postgis':
postgresql://foo:bar@localhost/database
"""

        call_command('sqldsn', '--style=uri')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={'default': POSTGRESQL_DATABASE_SETTINGS})
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info_with_pgpass_style_and_quiet_option_for_postgresql_database(self, m_stdout):
        expected_result = "localhost:5432:database:foo:bar\n"

        call_command('sqldsn', '--style=pgpass', '-q')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': POSTGRESQL_DATABASE_SETTINGS,
        'slave': MYSQL_DATABASE_SETTINGS,
        'test': SQLITE3_DATABASE_SETTINGS,
        'unknown': {
            'ENGINE': 'django.db.backends.unknown',
        }
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info_for_all_databases(self, m_stdout):
        default_postgresql = """DSN for database 'default' with engine 'postgresql':
host='localhost' dbname='database' user='foo' password='bar' port='5432'"""
        slave_mysql = '''DSN for database 'slave' with engine 'mysql':
host="127.0.0.1", db="dbatabase", user="foo", passwd="bar", port="3306"'''
        test_sqlite3 = """DSN for database 'test' with engine 'sqlite3':
db.sqlite3"""
        unknown = """DSN for database 'unknown' with engine 'unknown':
Unknown database, cant generate DSN"""

        call_command('sqldsn', '--all')

        self.assertIn(default_postgresql, m_stdout.getvalue())
        self.assertIn(slave_mysql, m_stdout.getvalue())
        self.assertIn(test_sqlite3, m_stdout.getvalue())
        self.assertIn(unknown, m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': POSTGRESQL_DATABASE_SETTINGS,
        'slave': MYSQL_DATABASE_SETTINGS,
        'test': SQLITE3_DATABASE_SETTINGS,
        'unknown': {
            'ENGINE': 'django.db.backends.unknown',
        }
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info_with_all_style_for_all_databases(self, m_stdout):
        default_postgresql = """DSN for database 'default' with engine 'postgresql':
host='localhost' dbname='database' user='foo' password='bar' port='5432'
host='localhost', database='database', user='foo', password='bar', port='5432'
postgresql://foo:bar@localhost:5432/database
localhost:5432:database:foo:bar"""
        slave_mysql = '''DSN for database 'slave' with engine 'mysql':
host="127.0.0.1", db="dbatabase", user="foo", passwd="bar", port="3306"'''
        test_sqlite3 = """DSN for database 'test' with engine 'sqlite3':
db.sqlite3"""
        unknown = """DSN for database 'unknown' with engine 'unknown':
Unknown database, cant generate DSN"""

        call_command('sqldsn', '--all', '--style=all')

        self.assertIn(default_postgresql, m_stdout.getvalue())
        self.assertIn(slave_mysql, m_stdout.getvalue())
        self.assertIn(test_sqlite3, m_stdout.getvalue())
        self.assertIn(unknown, m_stdout.getvalue())
