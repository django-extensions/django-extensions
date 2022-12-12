# -*- coding: utf-8 -*-
import importlib
import os
import subprocess
import sys

import pip
import pkg_resources
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

        self.assertTrue(value.endswith('repo is not frozen\n'), value)

    def test_pipchecker_with_outdated_requirement_on_pip20_1(self):
        def _install_pip(version):
            subprocess.call([sys.executable, '-m', 'pip', 'install', '-U', f'pip=={version}'])
            importlib.reload(pip)

        current_pip_version = pip.__version__

        try:
            _install_pip("20.1")

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
        finally:
            _install_pip(current_pip_version)

    def test_pipchecker_with_long_up_to_date_requirements(self):
        requirements_path = './requirements.txt'
        out = StringIO()

        f = open(requirements_path, 'wt')
        f.write('appdirs')
        f.write('asgiref')
        f.write('attrs')
        f.write('black')
        f.write('certifi')
        f.write('chardet')
        f.write('click')
        f.write('distlib')
        f.write('Django')
        f.write('django-cors-headers')
        f.write('django-debug-toolbar')
        f.write('djangorestframework')
        f.write('filelock')
        f.write('idna')
        f.write('iniconfig')
        f.write('mypy-extensions')
        f.write('packaging')
        f.write('pathspec')
        f.write('Pillow')
        f.write('pluggy')
        f.write('psycopg2-binary')
        f.write('py')
        f.write('pyparsing')
        f.write('pytest')
        f.write('pytz')
        f.write('regex')
        f.write('requests')
        f.write('sentry-sdk')
        f.write('shortuuid')
        f.write('six')
        f.write('sqlparse')
        f.write('toml')
        f.write('typed-ast')
        f.write('typing-extensions')
        f.write('urllib3')
        f.write('whitenoise')
        f.write('zipp')

        subprocess.call([sys.executable, '-m', 'pip', 'install', '-r', requirements_path])
        pip._vendor.pkg_resources = importlib.reload(pip._vendor.pkg_resources)
        call_command('pipchecker', '-r', requirements_path, stdout=out)

        value = out.getvalue()

        subprocess.call([sys.executable, '-m', 'pip', 'uninstall', '--yes', '-r', requirements_path])
        os.remove(requirements_path)

        self.assertTrue(value.endswith("Retrying in 60 seconds!") or value == '')
