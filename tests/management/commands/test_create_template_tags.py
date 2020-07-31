# -*- coding: utf-8 -*-
import os
import shutil

from django.core.management import call_command
from django.test import TestCase
from io import StringIO
from tests import testapp_with_no_models_file

from unittest.mock import Mock, patch


TEMPLATETAGS_DIR = os.path.join(testapp_with_no_models_file.__path__[0], 'templatetags')


class CreateTemplateTagsTests(TestCase):
    """Tests for create_template_tags command."""

    def tearDown(self):
        """Remove templatetags directory after each test."""
        try:
            shutil.rmtree(TEMPLATETAGS_DIR)
        except OSError:
            pass

    def test_should_create_testapp_with_no_models_file_tags_file(self):
        call_command('create_template_tags', 'testapp_with_no_models_file')
        self.assertTrue(os.path.isfile(os.path.join(TEMPLATETAGS_DIR, 'testapp_with_no_models_file_tags.py')))

    def test_should_create_custom__name_tags_file(self):
        call_command('create_template_tags', 'testapp_with_no_models_file', '--name', 'custom_name_tags')
        self.assertTrue(os.path.isfile(os.path.join(TEMPLATETAGS_DIR, 'custom_name_tags.py')))

    @patch('sys.stderr', new_callable=StringIO)
    def test_should_print_error_notice_on_OSError(self, m_stderr):
        m_shutil = Mock()
        m_shutil.copymode.side_effect = OSError
        with patch.dict('sys.modules', shutil=m_shutil):
            call_command('create_template_tags', 'testapp_with_no_models_file')

        self.assertRegex(
            m_stderr.getvalue(),
            r"Notice: Couldn't set permission bits on \S+ You're probably using an uncommon filesystem setup. No problem.",
        )
