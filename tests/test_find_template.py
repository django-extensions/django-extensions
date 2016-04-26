# coding=utf-8
import os

from django.core.management import call_command
from django.test import TestCase


class FindTemplateTests(TestCase):
    def setUp(self):
        self.project_root = os.path.join('tests', 'testapp')
        self._settings = os.environ.get('DJANGO_SETTINGS_MODULE')
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_extensions.settings'

    def tearDown(self):
        if self._settings:
            os.environ['DJANGO_SETTINGS_MODULE'] = self._settings

    def test_finding_template(self):
        call_command('find_template', 'admin/change_form.html')
