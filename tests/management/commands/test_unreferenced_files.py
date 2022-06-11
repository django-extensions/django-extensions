# -*- coding: utf-8 -*-
import os
import shutil
from io import StringIO
from tempfile import mkdtemp

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings

from ...testapp.models import Photo

from unittest.mock import patch


class UnreferencedFilesExceptionsTests(TestCase):

    @override_settings(MEDIA_ROOT=None)
    def test_should_raise_ComandError_if_MEDIA_ROOT_is_not_set(self):
        with self.assertRaisesRegex(CommandError, 'MEDIA_ROOT is not set, nothing to do'):
            call_command('unreferenced_files')


class UnreferencedFilesTests(TestCase):

    def setUp(self):
        self.media_root_dir = mkdtemp()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.media_root_dir)

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_not_print_any_output(self, m_stdout):
        with override_settings(MEDIA_ROOT=self.media_root_dir):
            call_command('unreferenced_files')

        self.assertIs('', m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_unreferenced_hello_txt_file(self, m_stdout):
        fn = os.path.join(self.media_root_dir, 'hello.txt')
        open(fn, 'a').close()

        with override_settings(MEDIA_ROOT=self.media_root_dir):
            call_command('unreferenced_files')

        self.assertIn(fn, m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_not_print_referenced_image_jpg_file(self, m_stdout):
        fn = os.path.join(self.media_root_dir, 'image.jpg')
        open(fn, 'a').close()

        Photo.objects.create(photo='image.jpg')

        with override_settings(MEDIA_ROOT=self.media_root_dir):
            call_command('unreferenced_files')

        self.assertNotIn(fn, m_stdout.getvalue())
