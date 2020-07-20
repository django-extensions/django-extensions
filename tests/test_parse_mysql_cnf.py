# -*- coding: utf-8 -*-
import os
import shutil
from tempfile import mkdtemp

from django.test import TestCase

from django_extensions.management.mysql import parse_mysql_cnf


class ParseMysqlCnfTests(TestCase):
    """Tests for parse_mysql_cnf."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def test_should_return_empty_strings_if_read_default_file_option_is_missing(self):
        dbinfo = {}

        result = parse_mysql_cnf(dbinfo)

        self.assertEqual(result, ('', '', '', '', ''))

    def test_should_parse_my_cnf_and_retun_connection_settings(self):
        my_cnf_path = os.path.join(self.tmpdir, 'my.cnf')
        with open(my_cnf_path, 'w') as f:
            f.write("""[client]
database = test_name
user = test_user
password = test_password
host = localhost
port = 3306
socket = /var/lib/mysqld/mysql.sock
""")

        dbinfo = {
            'ENGINE': 'django.db.backends.mysql',
            'OPTIONS': {
                'read_default_file': my_cnf_path,
            }
        }

        result = parse_mysql_cnf(dbinfo)

        self.assertEqual(result,
                         ('test_user', 'test_password', 'test_name',
                          '/var/lib/mysqld/mysql.sock', '3306'))

    def test_should_return_empty_strings_if_NoSectionError_exception_occured(self):
        my_cnf_path = os.path.join(self.tmpdir, 'my.cnf')
        with open(my_cnf_path, 'w') as f:
            f.write("")

        dbinfo = {
            'ENGINE': 'django.db.backends.mysql',
            'OPTIONS': {
                'read_default_file': my_cnf_path,
            }
        }
        result = parse_mysql_cnf(dbinfo)

        self.assertEqual(result, ('', '', '', '', ''))
