# -*- coding: utf-8 -*-
import re
from io import StringIO

from django.test import TestCase
from django.core.management import call_command


class ListSignalsTests(TestCase):
    """Tests for list_signals command."""

    def setUp(self):
        self.out = StringIO()

    def test_should_print_all_signals(self):
        expected_result = '''django.contrib.sites.models.Site (site)
    pre_delete
        django.contrib.sites.models.clear_site_cache #
    pre_save
        django.contrib.sites.models.clear_site_cache #
tests.testapp.models.HasOwnerModel (has owner model)
    pre_save
        tests.testapp.models.dummy_handler #
'''

        call_command('list_signals', stdout=self.out)

        # Strip line numbers to make the test less brittle
        out = re.sub(r'(?<=#)\d+', '', self.out.getvalue(), re.M)
        self.assertIn(expected_result, out)
