# -*- coding: utf-8 -*-
import os
import shutil

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings
from six import StringIO

import django_extensions.management.commands.sync_s3
from django_extensions.management.commands.sync_s3 import Command

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import patch


class SyncS3ExceptionsTests(TestCase):

    @patch('django_extensions.management.commands.sync_s3.HAS_BOTO', new=False)
    def test_should_raise_ImportError_if_boto_is_not_installed(self,):
        with self.assertRaisesRegexp(ImportError, "The boto Python library is not installed."):
            call_command('sync_s3')

    @override_settings(AWS_ACCESS_KEY_ID=None)
    @patch('django_extensions.management.commands.sync_s3.HAS_BOTO', new=True)
    def test_should_raise_CommandError_if_AWS_ACCESS_KEY_ID_is_not_set_or_is_set_to_None(self):
        with self.assertRaisesRegexp(CommandError, "Missing AWS keys from settings file.  Please supply both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"):
            call_command('sync_s3')

    @override_settings(AWS_SECRET_ACCESS_KEY=None)
    @patch('django_extensions.management.commands.sync_s3.HAS_BOTO', new=True)
    def test_should_raise_CommandError_if_AWS_SECRET_ACCESS_KEY_is_not_set_or_is_set_to_None(self):
        with self.assertRaisesRegexp(CommandError, "Missing AWS keys from settings file.  Please supply both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"):
            call_command('sync_s3')

    @override_settings(
        AWS_ACCESS_KEY_ID='access_key_id',
        AWS_SECRET_ACCESS_KEY='secret_access_key',
        AWS_BUCKET_NAME=''
    )
    def test_should_raise_CommandError_if_AWS_BUCKET_NAME_is_set_to_None(self):
        with self.assertRaisesRegexp(CommandError, "AWS_BUCKET_NAME cannot be empty"):
            call_command('sync_s3')

    @override_settings(
        AWS_ACCESS_KEY_ID='access_key_id',
        AWS_SECRET_ACCESS_KEY='secret_access_key',
    )
    def test_should_raise_CommandError_if_AWS_BUCKET_NAME_does_not_have_AWS_BUCKET_NAME_attr(self):
        del settings.AWS_BUCKET_NAME

        with self.assertRaisesRegexp(CommandError, "Missing bucket name from settings file. Please add the AWS_BUCKET_NAME to your settings file."):
            call_command('sync_s3')

    @override_settings(
        AWS_ACCESS_KEY_ID='access_key_id',
        AWS_SECRET_ACCESS_KEY='secret_access_key',
        AWS_BUCKET_NAME='bucket_name',
        MEDIA_ROOT=None
    )
    def test_should_raise_CommandError_if_MEDIA_ROOT_is_None(self):
        with self.assertRaisesRegexp(CommandError, "MEDIA_ROOT must be set in your settings."):
            call_command('sync_s3')

    @override_settings(
        AWS_ACCESS_KEY_ID='access_key_id',
        AWS_SECRET_ACCESS_KEY='secret_access_key',
        AWS_BUCKET_NAME='bucket_name',
    )
    def test_should_raise_CommandError_if_settings_does_not_have_MEDIA_ROOT_attr(self):
        del settings.MEDIA_ROOT

        with self.assertRaisesRegexp(CommandError, "MEDIA_ROOT must be set in your settings."):
            call_command('sync_s3')

    @override_settings(
        AWS_ACCESS_KEY_ID='access_key_id',
        AWS_SECRET_ACCESS_KEY='secret_access_key',
        AWS_BUCKET_NAME='bucket_name',
    )
    def test_should_raise_CommandError_when_media_only_and_static_only_options_together(self):
        with self.assertRaisesRegexp(CommandError, "Can't use --media-only and --static-only together. Better not use anything..."):
            call_command('sync_s3', '--media-only', '--static-only')

    @override_settings(
        AWS_ACCESS_KEY_ID='access_key_id',
        AWS_SECRET_ACCESS_KEY='secret_access_key',
        AWS_BUCKET_NAME='bucket_name',
    )
    @patch('django_extensions.management.commands.sync_s3.boto')
    def test_should_raise_CommandError_when_medi(self, m_boto):
        m_bucket = Mock()
        del settings.AWS_CLOUDFRONT_DISTRIBUTION

        m_boto.connect_s3.return_value.get_bucket.return_value = m_bucket
        m_boto.s3.key.Key.return_value = 'bucket_key'

        with self.assertRaisesRegexp(CommandError, "An object invalidation was requested but the variable AWS_CLOUDFRONT_DISTRIBUTION is not present in your settings."):
            call_command('sync_s3', '--media-only', '--invalidate')


class SyncS3Tests(TestCase):
    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        media_root = os.path.join(current_dir, "media")
        os.mkdir(media_root)
        test_dirs = [
            os.path.join(media_root, "testdir1"),
            os.path.join(media_root, "testdir2"),
            os.path.join(media_root, "testdir3"),
            os.path.join(media_root, "testdir4"),
            os.path.join(media_root, "testsamenamedir"),
        ]
        for dir in test_dirs:
            os.mkdir(dir)

        test_sub_dir = os.path.join(media_root, "testdir2", "testsubdir1")
        os.mkdir(test_sub_dir)

        test_sub_dir_base = os.path.join(media_root, "testdir1")
        test_sub_dirs = [
            os.path.join(test_sub_dir_base, "testsubdir1"),
            os.path.join(test_sub_dir_base, "testsubdir2"),
            os.path.join(test_sub_dir_base, "testsubdir3"),
            os.path.join(test_sub_dir_base, "testsubdir4"),
        ]

        for dir in test_sub_dirs:
            os.mkdir(dir)

        test_sub_dir_base2 = os.path.join(media_root, "testdir3")
        test_sub_dirs_2 = [
            os.path.join(test_sub_dir_base2, "testsubdir1"),
            os.path.join(test_sub_dir_base2, "testsubdir2"),
            os.path.join(test_sub_dir_base2, "testsubdir3"),
            os.path.join(test_sub_dir_base2, "testsubdir4"),
            os.path.join(test_sub_dir_base2, "testsamenamedir"),
        ]

        for dir in test_sub_dirs_2:
            os.mkdir(dir)

    def tearDown(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        media_root = os.path.join(current_dir, "media")
        shutil.rmtree(media_root)

    @override_settings(MEDIA_ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)), "media"))
    @override_settings(STATIC_ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"))
    @override_settings(AWS_ACCESS_KEY_ID="FAKE_KEY")
    @override_settings(AWS_SECRET_ACCESS_KEY="FAKE_SECRET_KEY")
    @override_settings(AWS_BUCKET_NAME="FAKE_BUCKET_NAME")
    def test_sync_s3_dir_exclusions(self):
        sync_s3_command = Command()
        django_extensions.management.commands.sync_s3.HAS_BOTO = True
        try:
            sync_s3_command.run_from_argv(
                ["manage.py", "sync_s3", "--acl=authenticated-read", "--filter-list=testsamenamedir,testdir1"]
            )
        except Exception:
            # Exception is expected, we're not actually attempting to connect to S3
            self.assertEqual(0, 0)

        for directory in sync_s3_command.DIRECTORIES:
            for root, dirs, files in os.walk(directory):
                sync_s3_command.upload_s3(("FAKE_BUCKET", "FAKE_KEY", "FAKE_BUCKET_NAME", directory), root, files, dirs)
                dir_name = os.path.basename(root)
                if dir_name == "testdir1":
                    self.assertEqual(len(dirs), 0)
                elif dir_name == "testdir2":
                    self.assertEqual(len(dirs), 1)
                elif dir_name == "testdir3":
                    self.assertEqual(len(dirs), 5)

    @override_settings(
        AWS_ACCESS_KEY_ID='access_key_id',
        AWS_SECRET_ACCESS_KEY='secret_access_key',
        AWS_BUCKET_NAME='bucket_name',
    )
    @patch('sys.stdout', new_callable=StringIO)
    @patch('django_extensions.management.commands.sync_s3.boto')
    def test_should_raise_CommandError_when_medi(self, m_boto, m_stdout):
        m_bucket = Mock()

        m_boto.connect_s3.return_value.get_bucket.return_value = m_bucket
        m_boto.s3.key.Key.return_value = 'bucket_key'

        call_command('sync_s3', '--media-only')

        self.assertIn("0 files uploaded.", m_stdout.getvalue())
        self.assertIn("0 files skipped.", m_stdout.getvalue())
