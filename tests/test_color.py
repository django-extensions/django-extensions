# -*- coding: utf-8 -*-
from django.test import SimpleTestCase
from django_extensions.management import color
from . import force_color_support


class ColorTest(SimpleTestCase):
    def test_no_style(self):
        with force_color_support:
            style = color.no_style().MODULE_NAME
            text = 'csv'
            styled_text = style(text)
            self.assertEqual(text, styled_text)

    def test_color_style(self):
        with force_color_support:
            style = color.color_style().MODULE_NAME
            text = 'antigravity'
            styled_text = style(text)
            self.assertIn(text, styled_text)
            self.assertNotEqual(text, styled_text)
