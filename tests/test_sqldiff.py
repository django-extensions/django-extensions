# -*- coding: utf-8 -*-
from django.apps import apps
from django.test import TestCase

from django_extensions.management.commands.sqldiff import SqliteSQLDiff


class SqlDiffTests(TestCase):
    def _include_proxy_models_testing(self, should_include_proxy_models):  # type: (bool) -> ()
        instance = SqliteSQLDiff(
            apps.get_models(include_auto_created=True),
            {'all_applications': True, 'include_proxy_models': should_include_proxy_models}
        )
        instance.find_differences()
        checked_models = {"%s.%s" % (app_label, model_name) for app_label, model_name, _ in instance.differences}
        self.assertEqual(should_include_proxy_models, "testapp.PostWithTitleOrdering" in checked_models)

    def test_sql_diff_without_proxy_models(self):
        self._include_proxy_models_testing(False)

    def test_sql_diff_with_proxy_models(self):
        self._include_proxy_models_testing(True)
