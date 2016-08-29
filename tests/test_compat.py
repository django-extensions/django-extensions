# -*- coding: utf-8 -*-
from django.test import TestCase, override_settings

from django_extensions.compat import get_template_setting


class GetTemplateSettingTests(TestCase):
    @override_settings(TEMPLATES=[{'DIRS': ['asdf']}])
    def test_new_dir_template(self):
        setting = get_template_setting('DIRS')
        self.assertEqual(setting, ['asdf'])

    @override_settings(TEMPLATES=None, TEMPLATES_DIRS=['asdf'])
    def test_old_dir_template(self):
        setting = get_template_setting('DIRS')
        self.assertEqual(setting, ['asdf'])

    @override_settings(TEMPLATES=None)
    def test_old_dir_missing(self):
        setting = get_template_setting('DIRS', 'default')
        self.assertEqual(setting, 'default')

    def test_default_setting(self):
        setting = get_template_setting('ASDF', 'default')
        self.assertEqual(setting, 'default')
