# -*- coding: utf-8 -*-

from django.core.management import CommandError, call_command

from django.test import TestCase
from django.test.utils import override_settings
from django.utils.six import StringIO
import pytest
try:
    from unittest.mock import MagicMock, Mock, patch
except ImportError:
    from mock import MagicMock, Mock, patch

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


@pytest.mark.WIP
class SqlDsnExceptionsTests(TestCase):
    """Tests for sqldsn management command exceptions."""

    @override_settings(DATABASES={})
    def test_should_raise_CommandError_if_unknown_router_does_not_exist(self):  # noqa
        with self.assertRaisesRegex(
                CommandError, "Unknown database router unknown"):
            call_command('sqldsn', '--router=unknown')


@pytest.mark.WIP
class SqlDsnTests(TestCase):
    """Tests for sqldsn management command."""
    maxDiff = None

    @override_settings(DATABASES={
        'default': SQLITE3_DATABASE_SETTINGS
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info_for_default_sqlite3_router(self, m_stdout):  # noqa
        expected_result = """DSN for router 'default' with engine 'sqlite3':
db.sqlite3
"""
        call_command('sqldsn')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': MYSQL_DATABASE_SETTINGS
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_quiet_info_for_mysql_router(self, m_stdout):  # noqa
        expected_result = '''host="127.0.0.1", db="dbatabase", user="foo", passwd="bar", port="3306"
'''  # noqa
        call_command('sqldsn', '-q')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': POSTGRESQL_DATABASE_SETTINGS
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_all_info_for_postgresql_router(self, m_stdout):  # noqa
        expected_result = """DSN for router 'default' with engine 'postgresql':
host='localhost' dbname='database' user='foo' password='bar' port='5432'
"""

        call_command('sqldsn', '-a')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': POSTGRESQL_PSYCOPG2_DATABASE_SETTINGS
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info__with_kwargs_style_for_postgresql_psycopg2_router(self, m_stdout):  # noqa
        expected_result = """DSN for router 'default' with engine 'postgresql_psycopg2':
host='localhost', database='database', user='foo', password='bar', port='5432'
"""  # noqa

        call_command('sqldsn', '--style=kwargs')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': POSTGIS_WITH_PORT_DATABASE_SETTINGS
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info__with_uri_style_for_postgis_router(self, m_stdout):  # noqa
        expected_result = """DSN for router 'default' with engine 'postgis':
postgresql://foo:bar@localhost:5432/database
"""  # noqa

        call_command('sqldsn', '--style=uri')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': POSTGIS_DATABASE_SETTINGS
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info__with_uri_style_without_port_for_postgis_router(self, m_stdout):  # noqa
        expected_result = """DSN for router 'default' with engine 'postgis':
postgresql://foo:bar@localhost/database
"""  # noqa

        call_command('sqldsn', '--style=uri')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': POSTGRESQL_DATABASE_SETTINGS
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info_with_pgpass_style_and_quiet_option_for_postgresql_router(self, m_stdout):  # noqa
        expected_result = "localhost:5432:database:foo:bar\n"

        call_command('sqldsn', '--style=pgpass', '-q')

        self.assertEqual(expected_result, m_stdout.getvalue())

    @override_settings(DATABASES={
        'default': POSTGRESQL_DATABASE_SETTINGS,
        'slave': MYSQL_DATABASE_SETTINGS,
        'test': SQLITE3_DATABASE_SETTINGS,
        'unknown': {
            'ENGINE': 'django.db.backends.unknown'
        }
    })
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_info_for_all_routers(self, m_stdout):  # noqa
        expected_result = """DSN for router 'default' with engine 'postgresql':
host='localhost' dbname='database' user='foo' password='bar' port='5432'

DSN for router 'slave' with engine 'mysql':
host="127.0.0.1", db="dbatabase", user="foo", passwd="bar", port="3306"

DSN for router 'test' with engine 'sqlite3':
db.sqlite3

DSN for router 'unknown' with engine 'unknown':
Unknown database, cant generate DSN
"""

        call_command('sqldsn', '--all')

        self.assertEqual(expected_result, m_stdout.getvalue())
