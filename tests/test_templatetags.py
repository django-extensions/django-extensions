# -*- coding: utf-8 -*-
from django.template import engines
from django.test import TestCase

from django_extensions.templatetags.widont import widont, widont_html

from unittest.mock import MagicMock


# TODO: these tests are far from having decent test coverage
class TemplateTagsTests(TestCase):
    def test_widont(self):
        self.assertEqual(widont('Test Value'), 'Test&nbsp;Value')
        self.assertEqual(widont(str('Test Value')), str('Test&nbsp;Value'))

    def test_widont_html(self):
        self.assertEqual(widont_html('Test Value'), 'Test&nbsp;Value')
        self.assertEqual(widont_html(str('Test Value')), str('Test&nbsp;Value'))


class DebuggerTagsTests(TestCase):

    """Test class for DebuggerTags."""

    def setUp(self):
        self.engine = engines['django']

    def test_pdb_filter(self):
        """Test for pdb filter."""
        import pdb
        pdb.set_trace = MagicMock(return_value=None)
        template = self.engine.from_string(
            '''
            {% load debugger_tags %}

            {{ test_object|pdb }}
            '''
        )
        template.render({'test_object': 'test_value'})
        self.assertTrue(pdb.set_trace.called)
