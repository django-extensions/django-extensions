# -*- coding: utf-8 -*-
import os
import shutil
from io import StringIO
from tempfile import mkdtemp

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings


def test_validate_templates():
    out = StringIO()
    try:
        call_command('validate_templates', verbosity=3, stdout=out, stderr=out)
    except CommandError:
        print(out.getvalue())
        raise

    output = out.getvalue()
    assert "0 errors found\n" in output


class ValidateTemplatesTests(TestCase):

    def setUp(self):
        self.tempdir = mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_should_print_that_there_is_error(self):
        with override_settings(INSTALLED_APPS=settings.INSTALLED_APPS + ['tests.testapp_with_template_errors']):
            with self.assertRaisesRegex(CommandError, '1 errors found'):
                call_command('validate_templates', verbosity=3)

    def test_should_not_print_any_errors_if_template_in_VALIDATE_TEMPLATES_IGNORES(self):
        out = StringIO()

        with override_settings(
                INSTALLED_APPS=settings.INSTALLED_APPS + ['tests.testapp_with_template_errors'],
                VALIDATE_TEMPLATES_IGNORES=['template_with_error.html']):
            call_command('validate_templates', verbosity=3, stdout=out, stderr=out)

        output = out.getvalue()

        self.assertIn('0 errors found\n', output)

    def test_should_not_print_any_errors_if_app_in_VALIDATE_TEMPLATES_IGNORE_APPS(self):
        out = StringIO()

        with override_settings(
                INSTALLED_APPS=settings.INSTALLED_APPS + ['tests.testapp_with_template_errors'],
                VALIDATE_TEMPLATES_IGNORE_APPS=['tests.testapp_with_template_errors']):
            call_command('validate_templates', verbosity=3, stdout=out, stderr=out)

        output = out.getvalue()

        self.assertIn('0 errors found\n', output)

    def test_should_break_when_first_error_occur(self):
        fn = os.path.join(self.tempdir, 'template_with_error.html')
        with open(fn, 'w') as f:
            f.write("""{% invalid_tag %}""")

        with self.assertRaisesRegex(CommandError, 'Errors found'):
            call_command('validate_templates', '-i', self.tempdir, '-b', verbosity=3)
