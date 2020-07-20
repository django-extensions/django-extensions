# -*- coding: utf-8 -*-
import fnmatch
import os

from io import StringIO
from django.core.management import call_command
from django.test import TestCase


class CompilePycTests(TestCase):
    def setUp(self):
        self.project_root = os.path.join('tests', 'testapp')
        self._settings = os.environ.get('DJANGO_SETTINGS_MODULE')
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_extensions.settings'

    def tearDown(self):
        if self._settings:
            os.environ['DJANGO_SETTINGS_MODULE'] = self._settings

    def _find_pyc(self, path, mask='*.pyc'):
        pyc_glob = []
        for root, dirs, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, mask):
                pyc_glob.append(os.path.join(root, filename))
        return pyc_glob

    def test_compiles_pyc_files(self):
        with self.settings(BASE_DIR=self.project_root):
            call_command('clean_pyc')
        pyc_glob = self._find_pyc(self.project_root)
        self.assertEqual(len(pyc_glob), 0)
        with self.settings(BASE_DIR=self.project_root):
            call_command('compile_pyc')
        pyc_glob = self._find_pyc(self.project_root)
        self.assertTrue(len(pyc_glob) > 0)
        with self.settings(BASE_DIR=self.project_root):
            call_command('clean_pyc')

    def test_takes_path(self):
        out = StringIO()
        with self.settings(BASE_DIR=""):
            call_command('clean_pyc', path=self.project_root)
        pyc_glob = self._find_pyc(self.project_root)
        self.assertEqual(len(pyc_glob), 0)
        with self.settings(BASE_DIR=""):
            call_command('compile_pyc', verbosity=2, path=self.project_root, stdout=out)
        expected = ['Compiling %s...' % fn for fn in sorted(self._find_pyc(self.project_root, mask='*.py'))]
        output = out.getvalue().splitlines()
        self.assertEqual(expected, sorted(output))
        with self.settings(BASE_DIR=""):
            call_command('clean_pyc', path=self.project_root)
