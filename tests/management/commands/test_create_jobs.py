# -*- coding: utf-8 -*-
import os
import shutil

from django.core.management import call_command
from django.test import TestCase
from io import StringIO
from tests import testapp_with_no_models_file

from unittest.mock import patch


JOBS_DIR = os.path.join(testapp_with_no_models_file.__path__[0], 'jobs')
TIME_PERIODS = ['hourly', 'daily', 'weekly', 'monthly', 'yearly']


class CreateJobsTestsMixin:

    def tearDown(self):
        super().tearDown()
        try:
            shutil.rmtree(JOBS_DIR)
        except OSError:
            pass


class CreateJobsExceptionsTests(CreateJobsTestsMixin, TestCase):

    @patch('sys.stderr', new_callable=StringIO)
    @patch('django_extensions.management.commands.create_jobs._make_writeable', side_effect=OSError)
    def test_should_print_error_notice_on_OSError(self, m__make_writeable, m_stderr):
        call_command('create_jobs', 'testapp_with_no_models_file')

        self.assertRegex(
            m_stderr.getvalue(),
            r"Notice: Couldn't set permission bits on \S+ You're probably using an uncommon filesystem setup. No problem.",
        )


class CreateJobsTests(CreateJobsTestsMixin, TestCase):

    def test_should_create_jobs_directory_structure_silently(self):
        call_command('create_jobs', 'testapp_with_no_models_file')

        self.assertTrue(os.path.exists(JOBS_DIR))

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_create_jobs_directory_structure_and_print_SUCCESS_message(self, m_stdout):
        call_command('create_jobs', 'testapp_with_no_models_file', verbosity=2)

        self.assertTrue(os.path.exists(JOBS_DIR))
        for time_period in TIME_PERIODS:
            self.assertIn(
                'testapp_with_no_models_file/jobs/{}/__init__.py'.format(time_period),
                m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_not_override_already_created_jobs_directory_structure_and_print_that_already_exists(self, m_stdout):
        call_command('create_jobs', 'testapp_with_no_models_file')
        sample_file_path = os.path.join(JOBS_DIR, 'sample.py')
        TEST_COMMENT = '# test'
        with open(sample_file_path, 'a') as f:
            f.write(TEST_COMMENT)

        call_command('create_jobs', 'testapp_with_no_models_file', verbosity=2)

        self.assertTrue(os.path.exists(JOBS_DIR))
        self.assertIn(TEST_COMMENT, open(sample_file_path).read())
        for time_period in TIME_PERIODS:
            self.assertIn(
                'testapp_with_no_models_file/jobs/{}/__init__.py already exists'.format(time_period),
                m_stdout.getvalue())
