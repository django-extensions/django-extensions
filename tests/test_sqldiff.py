# -*- coding: utf-8 -*-
import mock
import pytest
from io import StringIO

from django.conf import settings
from django.apps import apps
from django.test import TestCase

# from django.core.management import call_command
from django_extensions.management.commands.sqldiff import SqliteSQLDiff, Command, MySQLDiff, PostgresqlSQLDiff


class SqlDiffTests(TestCase):

    def setUp(self):
        self.parser = Command().create_parser("test", "sqldiff")
        self.args = ["-a"]
        self.options = self.parser.parse_args(args=self.args)
        self.tmp_out = StringIO()
        self.tmp_err = StringIO()

    def _include_proxy_models_testing(self, should_include_proxy_models):  # type: (bool) -> ()
        if should_include_proxy_models:
            self.args.append("--include-proxy-models")
        self.options = self.parser.parse_args(args=self.args)
        instance = SqliteSQLDiff(
            apps.get_models(include_auto_created=True),
            vars(self.options),
            stdout=self.tmp_out,
            stderr=self.tmp_err,
        )
        instance.load()
        instance.find_differences()
        checked_models = {"%s.%s" % (app_label, model_name) for app_label, model_name, _ in instance.differences}
        self.assertEqual(should_include_proxy_models, "testapp.PostWithTitleOrdering" in checked_models)

    @pytest.mark.skipif(settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3', reason="Test can only run on sqlite3")
    def test_sql_diff_without_proxy_models(self):
        self._include_proxy_models_testing(False)

    @pytest.mark.skipif(settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3', reason="Test can only run on sqlite3")
    def test_sql_diff_with_proxy_models(self):
        self._include_proxy_models_testing(True)

    def test_format_field_names(self):
        instance = MySQLDiff(
            apps.get_models(include_auto_created=True),
            vars(self.options),
            stdout=self.tmp_out,
            stderr=self.tmp_err,
        )
        expected_field_name = ['name', 'email', 'address']
        self.assertEqual(instance.format_field_names(['Name', 'EMAIL', 'aDDress']), expected_field_name)

    @pytest.mark.skipif(settings.DATABASES['default']['ENGINE'] != 'django.db.backends.mysql', reason="Test can only run on mysql")
    def test_mysql_to_dict(self):
        mysql_instance = MySQLDiff(
            apps.get_models(include_auto_created=True),
            vars(self.options),
            stdout=self.tmp_out,
            stderr=self.tmp_err,
        )
        mysql_dict = mysql_instance.sql_to_dict("""select 1 as "foo", 1 + 1 as "BAR";""", [])
        self.assertEqual(mysql_dict, [{'bar': 2, 'foo': 1}])

    @pytest.mark.skipif(settings.DATABASES['default']['ENGINE'] != 'django.db.backends.mysql', reason="Test can only run on mysql")
    @mock.patch('django_extensions.management.commands.sqldiff.MySQLDiff.format_field_names')
    def test_invalid_mysql_to_dict(self, format_field_names):
        format_field_names.side_effect = lambda x: x
        mysql_instance = MySQLDiff(
            apps.get_models(include_auto_created=True),
            vars(self.options),
            stdout=self.tmp_out,
            stderr=self.tmp_err,
        )
        mysql_dict = mysql_instance.sql_to_dict("""select 1 as "foo", 1 + 1 as "BAR";""", [])
        self.assertNotEquals(mysql_dict, [{'bar': 2, 'foo': 1}])

    @pytest.mark.skipif(settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3', reason="Test can only run on sqlite3")
    def test_sqlite_to_dict(self):
        sqlite_instance = SqliteSQLDiff(
            apps.get_models(include_auto_created=True),
            vars(self.options),
            stdout=self.tmp_out,
            stderr=self.tmp_err,
        )

        sqlite_dict = sqlite_instance.sql_to_dict("""select 1 as "foo", 1 + 1 as "BAR";""", [])
        self.assertEqual(sqlite_dict, [{'BAR': 2, 'foo': 1}])

    @pytest.mark.skipif(settings.DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql', reason="Test can only run on postgresql")
    def test_postgresql_to_dict(self):
        postgresql_instance = PostgresqlSQLDiff(
            apps.get_models(include_auto_created=True),
            vars(self.options),
            stdout=self.tmp_out,
            stderr=self.tmp_err,
        )

        postgresql_dict = postgresql_instance.sql_to_dict("""select 1 as "foo", 1 + 1 as "BAR";""", [])
        self.assertEqual(postgresql_dict, [{'BAR': 2, 'foo': 1}])

    # def test_sql_diff_run(self):
    #     tmp_out = StringIO()
    #     call_command("sqldiff", all_applications=True, migrate_for_tests=True, stdout=tmp_out)
    #     self.assertEqual('-- No differences', tmp_out.getvalue())
    #     tmp_out.close()
