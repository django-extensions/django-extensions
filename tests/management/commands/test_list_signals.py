# -*- coding: utf-8 -*-
import re
from io import StringIO

from django.db.models.signals import post_delete
from django.test import TestCase
from django.core.management import call_command

from tests.testapp.models import AbstractInheritanceTestModelParent


def delete_dummy_handler(sender, instance, **kwargs):
    pass


class ListSignalsTests(TestCase):
    """Tests for list_signals command."""

    def setUp(self):
        self.out = StringIO()

        post_delete.connect(delete_dummy_handler, sender=AbstractInheritanceTestModelParent)

    def test_should_print_all_signals(self):
        expected_result = """django.contrib.sites.models.Site (site)
    pre_delete
        django.contrib.sites.models.clear_site_cache #
    pre_save
        django.contrib.sites.models.clear_site_cache #
tests.testapp.models.AbstractInheritanceTestModelParent (abstract inheritance test model parent)
    post_delete
        tests.management.commands.test_list_signals.delete_dummy_handler #
tests.testapp.models.HasOwnerModel (has owner model)
    pre_save
        tests.testapp.models.dummy_handler #
"""

        call_command('list_signals', stdout=self.out)

        # Strip line numbers to make the test less brittle
        out = re.sub(r'(?<=#)\d+', '', self.out.getvalue(), re.M)
        self.assertIn(expected_result, out)
