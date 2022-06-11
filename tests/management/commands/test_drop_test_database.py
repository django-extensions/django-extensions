# -*- coding: utf-8 -*-
from io import StringIO
from unittest.mock import MagicMock, Mock, PropertyMock, call, patch

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings


# Database testing configurations

UNKOWN_ENGINE = {
    'default': {
        'ENGINE': 'django.db.backends.unknown',
        'NAME': 'unknown',
    }
}

NO_TEST_NAME = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test',
        'TEST': {
            'NAME': '',
        }
    }
}

SQLITE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

MYSQL_HOST_PORT = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test',
        'USER': 'test',
        'PASSWORD': 'test',
        'HOST': 'localhost',
        'PORT': '3306',
    },
}

MYSQL_SOCKET = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test',
        'USER': 'test',
        'PASSWORD': 'test',
        'HOST': '/var/run/mysqld/mysql.sock',
    },
}

POSTGRES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'test',
        'USER': 'test',
        'PASSWORD': 'test',
        'PORT': '5432',
        'HOST': 'localhost',
    },
}


class DropTestDatabaseExceptionsTests(TestCase):
    """Test for drop_test_database command."""

    def test_should_raise_CommandError_if_database_is_unknown(self):
        with self.assertRaisesRegex(CommandError, "Unknown database unknown"):
            call_command('drop_test_database', '--database=unknown')

    @override_settings(DATABASES=UNKOWN_ENGINE)
    @patch('django_extensions.management.commands.drop_test_database.input')
    def test_should_raise_CommandError_if_unknown_database_engine(self, m_input):
        m_input.return_value = 'yes'
        with self.assertRaisesRegex(CommandError, "Unknown database engine django.db.backends.unknown"):
            call_command('drop_test_database')

    @override_settings(DATABASES=NO_TEST_NAME)
    def test_should_raise_CommandError_if_test_database_name_is_empty(self):
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

    @override_settings(DATABASES=SQLITE)
    @patch('sys.stdout', new_callable=StringIO)
    @patch('os.path.isfile')
    @patch('os.unlink')
    def test_sqlite3_should_unlink_primary_test_database(self, m_unlink, m_isfile, m_stdout):
        # Indicate that no clone databases exist
        m_isfile.side_effect = (True, False)
        call_command('drop_test_database', '--noinput', verbosity=2)

        with self.subTest('Should check for test database names until failure'):
            self.assertListEqual(
                m_isfile.call_args_list,
                # See production code comments regarding double dots
                [call('test_db.sqlite3'), call('test_db_1..sqlite3')],
            )

        with self.subTest('Should unlink only primary test database'):
            self.assertListEqual(
                m_unlink.call_args_list,
                [call('test_db.sqlite3')],
            )

        with self.subTest('Should report successful message'):
            self.assertIn("Reset successful.", m_stdout.getvalue())

    @override_settings(DATABASES=SQLITE)
    @patch('os.path.isfile')
    @patch('os.unlink')
    def test_sqlite3_should_unlink_all_existing_clone_databases(self, m_unlink, m_isfile):
        """Test cloned test databases created via 'manage.py test --parallel'."""
        # Indicate that clone databases exist up to test_db_2.sqlite3
        m_isfile.side_effect = (True, True, True, False)
        call_command('drop_test_database', '--noinput')

        with self.subTest('Should check for test database names until failure'):
            self.assertListEqual(
                m_isfile.call_args_list,
                [
                    call('test_db.sqlite3'),
                    # See production code comments regarding double dots
                    call('test_db_1..sqlite3'),
                    call('test_db_2..sqlite3'),
                    call('test_db_3..sqlite3'),
                ],
            )

        with self.subTest('Should unlink all existing test databases'):
            self.assertListEqual(
                m_unlink.call_args_list,
                [
                    call('test_db.sqlite3'),
                    # See production code comments regarding double dots
                    call('test_db_1..sqlite3'),
                    call('test_db_2..sqlite3'),
                ],
            )

    @override_settings(DATABASES=SQLITE)
    @patch('sys.stdout', new_callable=StringIO)
    @patch('os.path.isfile')
    @patch('os.unlink')
    def test_sqlite3_should_not_print_Reset_successful_when_OSError_exception(self, m_unlink, m_isfile, m_stdout):
        m_isfile.return_value = True
        m_unlink.side_effect = OSError
        call_command('drop_test_database', '--noinput', verbosity=2)

        self.assertNotIn("Reset successful.", m_stdout.getvalue())

    @override_settings(DATABASES=MYSQL_HOST_PORT)
    @patch('sys.stdout', new_callable=StringIO)
    def test_mysql_should_drop_database_with_host_and_port(self, m_stdout):
        m_database = MagicMock()
        # Indicate that no clone databases exist
        # DROP queries return None while SELECT queries return a row count
        m_database.connect.return_value.cursor.return_value.execute.side_effect = (1, None, 0)

        with patch.dict("sys.modules", MySQLdb=m_database):
            call_command('drop_test_database', '--noinput', verbosity=2)

        with self.subTest('Should check for and remove test database names until failure'):
            exists_query = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME="
            self.assertListEqual(
                m_database.connect.return_value.cursor.return_value.execute.call_args_list,
                [
                    call(exists_query + "'test_test';"),
                    call('DROP DATABASE IF EXISTS `test_test`'),
                    call(exists_query + "'test_test_1';"),
                ],
            )

        with self.subTest('Should report successful message'):
            self.assertIn("Reset successful.", m_stdout.getvalue())

    @override_settings(DATABASES=MYSQL_SOCKET)
    @patch('sys.stdout', new_callable=StringIO)
    def test_mysql_should_drop_database_with_unix_socket(self, m_stdout):
        m_database = MagicMock()
        # Indicate that no clone databases exist
        # DROP queries return None while SELECT queries return a row count
        m_database.connect.return_value.cursor.return_value.execute.side_effect = (1, None, 0)

        with patch.dict("sys.modules", MySQLdb=m_database):
            call_command('drop_test_database', '--noinput', verbosity=2)

        with self.subTest('Should check for and remove test database names until failure'):
            exists_query = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME="
            self.assertListEqual(
                m_database.connect.return_value.cursor.return_value.execute.call_args_list,
                [
                    call(exists_query + "'test_test';"),
                    call('DROP DATABASE IF EXISTS `test_test`'),
                    call(exists_query + "'test_test_1';"),
                ],
            )

        with self.subTest('Should report successful message'):
            self.assertIn("Reset successful.", m_stdout.getvalue())

    @override_settings(DATABASES=MYSQL_HOST_PORT)
    def test_mysql_should_drop_all_existing_clone_databases(self):
        """Test cloned test databases created via 'manage.py test --parallel'."""
        m_database = MagicMock()
        # Indicate that clone databases exist up to test_test_2
        # DROP queries return None while SELECT queries return a row count
        m_database.connect.return_value.cursor.return_value.execute.side_effect = \
            (1, None, 1, None, 1, None, 0)

        with patch.dict("sys.modules", MySQLdb=m_database):
            call_command('drop_test_database', '--noinput')

        exists_query = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME="
        self.assertListEqual(
            m_database.connect.return_value.cursor.return_value.execute.call_args_list,
            [
                call(exists_query + "'test_test';"),
                call('DROP DATABASE IF EXISTS `test_test`'),
                call(exists_query + "'test_test_1';"),
                call('DROP DATABASE IF EXISTS `test_test_1`'),
                call(exists_query + "'test_test_2';"),
                call('DROP DATABASE IF EXISTS `test_test_2`'),
                call(exists_query + "'test_test_3';"),
            ],
        )

    @override_settings(DATABASES=POSTGRES)
    @patch('sys.stdout', new_callable=StringIO)
    def test_postgresql_should_drop_database(self, m_stdout):
        m_database = MagicMock()
        m_cursor = Mock()
        m_database.connect.return_value.cursor.return_value = m_cursor
        # Indicate that no clone databases exist
        type(m_cursor).rowcount = PropertyMock(side_effect=(1, 0))

        with patch.dict("sys.modules", psycopg2=m_database):
            call_command('drop_test_database', '--noinput', verbosity=2)

        with self.subTest('Should check for and remove test database names until failure'):
            exists_query = "SELECT datname FROM pg_catalog.pg_database WHERE datname="
            self.assertListEqual(
                m_cursor.execute.call_args_list,
                [
                    call(exists_query + "'test_test';"),
                    call('DROP DATABASE IF EXISTS "test_test";'),
                    call(exists_query + "'test_test_1';"),
                ],
            )

        with self.subTest('Should report successful message'):
            self.assertIn("Reset successful.", m_stdout.getvalue())

    @override_settings(DATABASES=POSTGRES)
    def test_postgresql_should_drop_all_existing_cloned_databases(self):
        """Test cloned test databases created via 'manage.py test --parallel'."""
        m_database = MagicMock()
        m_cursor = Mock()
        m_database.connect.return_value.cursor.return_value = m_cursor
        # Indicate that clone databases exist up to test_test_2
        type(m_cursor).rowcount = PropertyMock(side_effect=(1, 1, 1, 0))

        with patch.dict("sys.modules", psycopg2=m_database):
            call_command('drop_test_database', '--noinput')

        exists_query = "SELECT datname FROM pg_catalog.pg_database WHERE datname="
        self.assertListEqual(
            m_cursor.execute.call_args_list,
            [
                call(exists_query + "'test_test';"),
                call('DROP DATABASE IF EXISTS "test_test";'),
                call(exists_query + "'test_test_1';"),
                call('DROP DATABASE IF EXISTS "test_test_1";'),
                call(exists_query + "'test_test_2';"),
                call('DROP DATABASE IF EXISTS "test_test_2";'),
                call(exists_query + "'test_test_3';"),
            ],
        )

    @override_settings(DATABASES=POSTGRES)
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
