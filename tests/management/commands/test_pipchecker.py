# -*- coding: utf-8 -*-
import importlib
import os
import subprocess
import sys

import pip
import pkg_resources
import pytest
from django.core.management import call_command
from django.test import TestCase
from io import StringIO
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
        f.write('djangorestframework==3.0.0')
        f.close()

        subprocess.call([sys.executable, '-m', 'pip', 'install', '-r', requirements_path])
        pip._vendor.pkg_resources = importlib.reload(pip._vendor.pkg_resources)
        call_command('pipchecker', '-r', requirements_path, stdout=out)

        value = out.getvalue()

        subprocess.call([sys.executable, '-m', 'pip', 'uninstall', '--yes', '-r', requirements_path])
        os.remove(requirements_path)

        self.assertTrue(value.endswith('available\n'))

    @pytest.mark.skipif(sys.version_info < (3, 6), reason="requires python3.6 or higher")
    def test_pipchecker_with_up_to_date_requirement(self):
        requirements_path = './requirements.txt'
        out = StringIO()

        f = open(requirements_path, 'wt')
        f.write('djangorestframework')
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

    def test_pipchecker_with_outdated_requirement_on_pip20_1(self):
        subprocess.call([sys.executable, '-m', 'pip', 'install', '-U', 'pip==20.1'])
        importlib.reload(pip)

        requirements_path = './requirements.txt'
        out = StringIO()

        f = open(requirements_path, 'wt')
        f.write('djangorestframework==3.0.0')
        f.close()

        subprocess.call([sys.executable, '-m', 'pip', 'install', '-r', requirements_path])
        importlib.reload(pkg_resources)
        call_command('pipchecker', '-r', requirements_path, stdout=out)

        value = out.getvalue()

        subprocess.call([sys.executable, '-m', 'pip', 'uninstall', '--yes', '-r', requirements_path])
        os.remove(requirements_path)

        self.assertTrue(value.endswith('available\n'))
