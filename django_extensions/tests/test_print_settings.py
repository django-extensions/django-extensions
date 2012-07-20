try:
    import simplejson as json
except ImportError:
    import json

import subprocess
import sys
from django.utils import unittest


class PrintSettingsTests(unittest.TestCase):

    def _exec_manage_py(self, argv):
        python = sys.executable
        argv = [python, 'example_project/manage.py'] + argv
        return subprocess.Popen(argv, stdout=subprocess.PIPE).communicate()[0]

    def assertIn(self, needle, haystack):
        self.assertTrue(needle in haystack)

    def test_manage_py_print_settings_help(self):
        output = self._exec_manage_py(['print_settings', '--help'])
        # output = subprocess.check_output(['python', 'example_project/manage.py', 'print_settings', '--help'])
        self.assertIn('print_settings [options]', output)
        self.assertIn('--format=FORMAT', output)
        self.assertIn('--indent=INDENT', output)

    def test_manage_py_print_settings_no_args(self):
        output = self._exec_manage_py(['print_settings'])
        self.assertIn('America/Los_Angeles', output)

    def test_manage_py_print_settings_json(self):
        output = self._exec_manage_py(['print_settings', '--format=json'])
        self.assertIn('America/Los_Angeles', output)
        settings_dict = json.loads(output)
        self.assertEquals(len(settings_dict['AUTHENTICATION_BACKENDS']), 1)
        self.assertEquals(
            settings_dict['AUTHENTICATION_BACKENDS'][0],
            'django.contrib.auth.backends.ModelBackend'
        )

    def test_manage_py_print_settings_yaml(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("`yaml` module not available; install `PyYAML` to test --format=yaml")

        output = self._exec_manage_py(['print_settings', '--format=yaml'])
        self.assertIn('America/Los_Angeles', output)
        settings_dict = yaml.load(output)
        self.assertEquals(settings_dict['TIME_ZONE'], 'America/Los_Angeles')
        self.assertEquals(len(settings_dict['AUTHENTICATION_BACKENDS']), 1)
        self.assertEquals(
            settings_dict['AUTHENTICATION_BACKENDS'][0],
            'django.contrib.auth.backends.ModelBackend'
        )

