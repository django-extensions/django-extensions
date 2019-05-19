# -*- coding: utf-8 -*-
import six
import pytest
from django.conf import settings
from django.apps import apps
from django.test import TestCase

# from django.core.management import call_command
from django_extensions.management.commands.sqldiff import SqliteSQLDiff, Command


class SqlDiffTests(TestCase):
    def _include_proxy_models_testing(self, should_include_proxy_models):  # type: (bool) -> ()
        parser = Command().create_parser("test", "sqldiff")
        args = ["-a"]
        if should_include_proxy_models:
            args.append("--include-proxy-models")
        options = parser.parse_args(args=args)
        tmp_out = six.StringIO()
        tmp_err = six.StringIO()
        instance = SqliteSQLDiff(
            apps.get_models(include_auto_created=True),
            vars(options),
            stdout=tmp_out,
            stderr=tmp_err,
        )
        instance.find_differences()
        checked_models = {"%s.%s" % (app_label, model_name) for app_label, model_name, _ in instance.differences}
        self.assertEqual(should_include_proxy_models, "testapp.PostWithTitleOrdering" in checked_models)

    @pytest.mark.skipif(settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3', reason="Test can only run on sqlite3")
    def test_sql_diff_without_proxy_models(self):
        self._include_proxy_models_testing(False)

    @pytest.mark.skipif(settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3', reason="Test can only run on sqlite3")
    def test_sql_diff_with_proxy_models(self):
        self._include_proxy_models_testing(True)

    # def test_sql_diff_run(self):
    #     tmp_out = six.StringIO()
    #     call_command("sqldiff", all_applications=True, migrate_for_tests=True, stdout=tmp_out)
    #     self.assertEqual('-- No differences', tmp_out.getvalue())
    #     tmp_out.close()
