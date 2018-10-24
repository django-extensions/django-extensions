# -*- coding: utf-8 -*-
import sys
import six

from django.core.management import call_command
from django.test import TestCase


class RunJobTests(TestCase):

    def setUp(self):
        sys.stdout = six.StringIO()
        sys.stderr = six.StringIO()

    def test_runs(self):
        # lame test...does it run?
        call_command('runjob', 'cache_cleanup', verbosity=2)
        self.assertIn("Executing job: cache_cleanup (app: None)", sys.stdout.getvalue())

    def test_sample_job(self):
        call_command('runjob', 'sample_job', verbosity=2)
        self.assertIn("Executing job: sample_job (app: None)", sys.stdout.getvalue())
        self.assertIn("executing empty sample job", sys.stdout.getvalue())

    def test_list_jobs(self):
        call_command('runjob', '-l', verbosity=2)
        self.assertRegexpMatches(sys.stdout.getvalue(), "tests.testapp +- sample_job +- +- My sample job.\n")

    def test_list_jobs_appconfig(self):
        with self.modify_settings(INSTALLED_APPS={
            'append': 'tests.testapp.apps.TestAppConfig',
            'remove': 'tests.testapp',
        }):
            call_command('runjob', '-l', verbosity=2)
            self.assertRegexpMatches(sys.stdout.getvalue(), "tests.testapp +- sample_job +- +- My sample job.\n")

    def test_runs_appconfig(self):
        with self.modify_settings(INSTALLED_APPS={
            'append': 'tests.testapp.apps.TestAppConfig',
            'remove': 'tests.testapp',
        }):
            call_command('runjob', 'sample_job', verbosity=2)
            self.assertIn("Executing job: sample_job (app: None)", sys.stdout.getvalue())
            self.assertIn("executing empty sample job", sys.stdout.getvalue())
