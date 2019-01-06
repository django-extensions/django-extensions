# -*- coding: utf-8 -*-
import importlib
import os
import subprocess
import sys

import pip
from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO
from pip._internal.exceptions import InstallationError


class PipCheckerTests(TestCase):

    def test_pipchecker_when_requirements_file_does_not_exist(self):
        with self.assertRaises(InstallationError):
            call_command('pipchecker', '-r', 'not_exist.txt')

    def test_pipchecker_with_not_installed_requirement(self):
        requirements_path = './requirements.txt'
        out = StringIO()

        f = open(requirements_path, 'wt')
        f.write('not-installed==1.0.0')
        f.close()

        call_command('pipchecker', '-r', requirements_path, stdout=out)

        value = out.getvalue()

        subprocess.call([sys.executable, '-m', 'pip', 'uninstall', '--yes', '-r', requirements_path])
        os.remove(requirements_path)

        self.assertTrue(value.endswith('not installed\n'))

    def test_pipchecker_with_outdated_requirement(self):
        requirements_path = './requirements.txt'
        out = StringIO()

        f = open(requirements_path, 'wt')
        f.write('django-extensions==1.0.0')
        f.close()

        subprocess.call([sys.executable, '-m', 'pip', 'install', '-r', requirements_path])
        pip._vendor.pkg_resources = importlib.reload(pip._vendor.pkg_resources)
        call_command('pipchecker', '-r', requirements_path, stdout=out)

        value = out.getvalue()

        subprocess.call([sys.executable, '-m', 'pip', 'uninstall', '--yes', '-r', requirements_path])
        os.remove(requirements_path)

        self.assertTrue(value.endswith('available\n'))

    def test_pipchecker_with_up_to_date_requirement(self):
        requirements_path = './requirements.txt'
        out = StringIO()

        f = open(requirements_path, 'wt')
        f.write('django-extensions')
        f.close()

        subprocess.call([sys.executable, '-m', 'pip', 'install', '-r', requirements_path])
        pip._vendor.pkg_resources = importlib.reload(pip._vendor.pkg_resources)
        call_command('pipchecker', '-r', requirements_path, stdout=out)

        value = out.getvalue()

        subprocess.call([sys.executable, '-m', 'pip', 'uninstall', '--yes', '-r', requirements_path])
        os.remove(requirements_path)

        self.assertEqual(value, '')

    def test_pipchecker_with_github_url_requirement(self):
        requirements_path = './requirements.txt'
        out = StringIO()

        f = open(requirements_path, 'wt')
        f.write('git+https://github.com/jmrivas86/django-json-widget')
        f.close()

        subprocess.call([sys.executable, '-m', 'pip', 'install', 'django-json-widget'])
        pip._vendor.pkg_resources = importlib.reload(pip._vendor.pkg_resources)
        call_command('pipchecker', '-r', requirements_path, stdout=out)

        value = out.getvalue()

        subprocess.call([sys.executable, '-m', 'pip', 'uninstall', '--yes', '-r', requirements_path])
        os.remove(requirements_path)

        self.assertTrue(value.endswith('repo is not frozen\n'))
