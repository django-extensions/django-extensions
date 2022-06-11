# -*- coding: utf-8 -*-
import logging
import sys
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from unittest.mock import patch


class RunJobTests(TestCase):

    def setUp(self):
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        # Remove old loggers, since utils.setup_logger does not clean up after itself
        logger = logging.getLogger("django_extensions.management.commands.runjob")
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

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
        self.assertRegex(sys.stdout.getvalue(), "tests.testapp +- sample_job +- +- My sample job.\n")

    def test_list_jobs_appconfig(self):
        with self.modify_settings(INSTALLED_APPS={
            'append': 'tests.testapp.apps.TestAppConfig',
            'remove': 'tests.testapp',
        }):
            call_command('runjob', '-l', verbosity=2)
            self.assertRegex(sys.stdout.getvalue(), "tests.testapp +- sample_job +- +- My sample job.\n")

    def test_runs_appconfig(self):
        with self.modify_settings(INSTALLED_APPS={
            'append': 'tests.testapp.apps.TestAppConfig',
            'remove': 'tests.testapp',
        }):
            call_command('runjob', 'sample_job', verbosity=2)
            self.assertIn("Executing job: sample_job (app: None)", sys.stdout.getvalue())
            self.assertIn("executing empty sample job", sys.stdout.getvalue())

    def test_should_print_that_job_not_found(self):
        call_command('runjob', 'test_job', verbosity=2)

        self.assertIn("Error: Job test_job not found", sys.stdout.getvalue())

    def test_should_print_that_applabel_not_found(self):
        call_command('runjob', 'test_job', 'test_app', verbosity=2)

        self.assertIn("Error: Job test_app for applabel test_job not found", sys.stdout.getvalue())

    def test_should_always_print_list_option_usage_if_job_or_applabel_not_found(self):
        call_command('runjob', 'test_job', verbosity=2)

        self.assertIn("Use -l option to view all the available jobs", sys.stdout.getvalue())

    @patch('django_extensions.management.commands.runjob.get_job')
    def test_should_print_traceback(self, m_get_job):
        m_get_job.return_value.return_value.execute.side_effect = Exception

        call_command('runjob', 'test_job', 'test_app')

        self.assertIn("ERROR OCCURED IN JOB: test_app (APP: test_job)", sys.stdout.getvalue())
        self.assertIn("Traceback (most recent call last):", sys.stdout.getvalue())
