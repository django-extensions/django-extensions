# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.utils import override_settings

from django_extensions.compat import get_template_setting


class CompatTests(TestCase):

    @override_settings(TEMPLATES=None)
    def test_should_return_None_by_default_if_TEMPLATES_setting_is_none(self):
        self.assertIsNone(get_template_setting('template_key'))

    @override_settings(TEMPLATES=None)
    def test_should_return_default_if_TEMPLATES_setting_is_none(self):
        self.assertEqual(get_template_setting('template_key', 'test'), 'test')

    @override_settings(TEMPLATES=[
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': ['templates'],
            'APP_DIRS': True
        }])
    def test_should_return_value_for_key(self):
        self.assertEqual(get_template_setting('BACKEND'),
                         'django.template.backends.django.DjangoTemplates')
