# coding=utf-8
import six
from django.test import TestCase

from django_extensions.templatetags.widont import widont, widont_html


# TODO: these tests are far from having decent test coverage
class TemplateTagsTests(TestCase):
    def test_widont(self):
        self.assertEqual(widont('Test Value'), 'Test&nbsp;Value')
        self.assertEqual(widont(six.u('Test Value')), u'Test&nbsp;Value')

    def test_widont_html(self):
        self.assertEqual(widont_html('Test Value'), 'Test&nbsp;Value')
        self.assertEqual(widont_html(six.u('Test Value')), u'Test&nbsp;Value')
