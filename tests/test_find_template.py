# -*- coding: utf-8 -*-
from django.core.management import call_command
from django.test import TestCase
from io import StringIO

from unittest.mock import patch


class FindTemplateTests(TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    def test_finding_template(self, m_stdout):
        call_command('find_template', 'admin/change_form.html')

        self.assertIn('admin/change_form.html', m_stdout.getvalue())

    @patch('sys.stderr', new_callable=StringIO)
    def test_should_print_error_when_template_not_found(self, m_stderr):
        call_command('find_template', 'not_found_template.html')

        self.assertIn('No template found', m_stderr.getvalue())
