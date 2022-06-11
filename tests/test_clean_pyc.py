# -*- coding: utf-8 -*-
import fnmatch
import os
import shutil

from io import StringIO
from django.core.management import call_command
from django.test import TestCase


class CleanPycTests(TestCase):
    def setUp(self):
        self.project_root = os.path.join('tests', 'testapp')
        self._settings = os.environ.get('DJANGO_SETTINGS_MODULE')
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_extensions.settings'

    def tearDown(self):
        if self._settings:
            os.environ['DJANGO_SETTINGS_MODULE'] = self._settings

    def _find_pyc(self, path):
        pyc_glob = []
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, '*.pyc'):
                pyc_glob.append(os.path.join(root, filename))
        return pyc_glob

    def test_removes_pyc_files(self):
        with self.settings(BASE_DIR=self.project_root):
            call_command('compile_pyc')
        pyc_glob = self._find_pyc(self.project_root)
        self.assertTrue(len(pyc_glob) > 0)
        with self.settings(BASE_DIR=self.project_root):
            call_command('clean_pyc')
        pyc_glob = self._find_pyc(self.project_root)
        self.assertEqual(len(pyc_glob), 0)

    def test_takes_path(self):
        out = StringIO()
        project_root = os.path.join('tests', 'testapp')
        call_command('compile_pyc', path=project_root)
        pyc_glob = self._find_pyc(project_root)
        self.assertTrue(len(pyc_glob) > 0)
        call_command('clean_pyc', verbosity=2, path=project_root, stdout=out)
        output = out.getvalue().splitlines()
        self.assertEqual(sorted(pyc_glob), sorted(output))

    def test_removes_pyo_files(self):
        out = StringIO()
        project_root = os.path.join('tests', 'testapp')
        call_command('compile_pyc', path=project_root)
        pyc_glob = self._find_pyc(project_root)
        self.assertTrue(len(pyc_glob) > 0)
        # Create some fake .pyo files since we can't force them to be created.
        pyo_glob = []
        for fn in pyc_glob:
            pyo = '%s.pyo' % os.path.splitext(fn)[0]
            shutil.copyfile(fn, pyo)
            pyo_glob.append(pyo)
        call_command('clean_pyc', verbosity=2, path=project_root, optimize=True, stdout=out)
        output = out.getvalue().splitlines()
        self.assertEqual(sorted(pyc_glob + pyo_glob), sorted(output))
