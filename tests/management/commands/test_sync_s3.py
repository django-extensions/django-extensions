import os
import shutil
import unittest
from io import StringIO
from unittest.mock import Mock, patch

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings

from django_extensions.management.commands.sync_s3 import Command


class SyncS3TestsMixin:
    def setUp(self):
        self.mocked_boto = Mock()
        self.boto_patch = patch(
            "django_extensions.management.commands.sync_s3.boto3",
            create=True,
            boto=self.mocked_boto,
        )
        self.boto_patch.start()

    def tearDown(self):
        super().tearDown()
        self.boto_patch.stop()


@patch("django_extensions.management.commands.sync_s3.HAS_BOTO", True)
class SyncS3ExceptionsTests(SyncS3TestsMixin, TestCase):
    def test_should_raise_ImportError_if_boto_is_not_installed(self):
        with patch("django_extensions.management.commands.sync_s3.HAS_BOTO", False):
            with self.assertRaisesRegex(
                CommandError,
                r"Please install the 'boto3' Python library. \(\$ pip install boto3\)",
            ):
                call_command("sync_s3")

    @override_settings(AWS_ACCESS_KEY_ID=None)
    def test_should_raise_CommandError_if_AWS_ACCESS_KEY_ID_is_not_set_or_is_set_to_None(
        self,
    ):
        with self.assertRaisesRegex(
            CommandError,
            "Missing AWS_S3_ACCESS_KEY_ID and/or AWS_S3_SECRET_ACCESS_KEY in your settings file",
        ):
            call_command("sync_s3")

    @override_settings(AWS_SECRET_ACCESS_KEY=None)
    def test_should_raise_CommandError_if_AWS_SECRET_ACCESS_KEY_is_not_set_or_is_set_to_None(
        self,
    ):
        with self.assertRaisesRegex(
            CommandError,
            "Missing AWS_S3_ACCESS_KEY_ID and/or AWS_S3_SECRET_ACCESS_KEY in your settings file",
        ):
            call_command("sync_s3")

    @override_settings(
        AWS_S3_ACCESS_KEY_ID="access_key_id",
        AWS_S3_SECRET_ACCESS_KEY="secret_access_key",
        AWS_STORAGE_BUCKET_NAME="",
    )
    def test_should_raise_CommandError_if_AWS_STORAGE_BUCKET_NAME_is_set_to_None(self):
        with self.assertRaisesRegex(
            CommandError,
            "Missing AWS_STORAGE_BUCKET_NAME in your settings file"
        ):
            call_command("sync_s3")

    @override_settings(
        AWS_S3_ACCESS_KEY_ID="access_key_id",
        AWS_S3_SECRET_ACCESS_KEY="secret_access_key",
    )
    def test_should_raise_CommandError_if_AWS_STORAGE_BUCKET_NAME_does_not_have_AWS_STORAGE_BUCKET_NAME_attr(
        self,
    ):
        del settings.AWS_STORAGE_BUCKET_NAME

        with self.assertRaisesRegex(
            CommandError,
            "Missing AWS_STORAGE_BUCKET_NAME in your settings file",
        ):
            call_command("sync_s3")

    @override_settings(
        AWS_S3_ACCESS_KEY_ID="access_key_id",
        AWS_S3_SECRET_ACCESS_KEY="secret_access_key",
        AWS_STORAGE_BUCKET_NAME="bucket_name",
        MEDIA_ROOT=None,
    )
    def test_should_raise_CommandError_if_MEDIA_ROOT_is_None(self):
        with self.assertRaisesRegex(
            CommandError, "MEDIA_ROOT should be set in your settings file"
        ):
            call_command("sync_s3")

    @override_settings(
        AWS_S3_ACCESS_KEY_ID="access_key_id",
        AWS_S3_SECRET_ACCESS_KEY="secret_access_key",
        AWS_STORAGE_BUCKET_NAME="bucket_name"
    )
    def test_should_raise_CommandError_if_settings_does_not_have_MEDIA_ROOT_attr(self):
        del settings.MEDIA_ROOT

        with self.assertRaisesRegex(
            CommandError, "MEDIA_ROOT should be set in your settings file"
        ):
            call_command("sync_s3")

    @override_settings(
        AWS_S3_ACCESS_KEY_ID="access_key_id",
        AWS_S3_SECRET_ACCESS_KEY="secret_access_key",
        AWS_STORAGE_BUCKET_NAME="bucket_name",
    )
    def test_should_raise_CommandError_when_media_only_and_static_only_options_together(
        self,
    ):
        with self.assertRaisesRegex(
            CommandError,
            "--static-only and --media-only options cannot be used together",
        ):
            call_command("sync_s3", "--media-only", "--static-only")

    @override_settings(
        AWS_S3_ACCESS_KEY_ID="access_key_id",
        AWS_S3_SECRET_ACCESS_KEY="secret_access_key",
        AWS_STORAGE_BUCKET_NAME="bucket_name",
    )
    def test_should_raise_CommandError_when_media_only_and_cloudfront_invalidate_options_together(self):
        del settings.AWS_CLOUDFRONT_DISTRIBUTION

        self.mocked_boto.Session.return_value.client.return_value = Mock()
        self.mocked_boto.Session.return_value.resource.return_value = Mock()
        self.mocked_boto.Session.return_value.resource.return_value.Bucket.return_value = Mock()

        # self.mocked_boto.connect_s3.return_value.get_bucket.return_value = Mock()
        # self.mocked_boto.s3.key.Key.return_value = "bucket_key"

        with self.assertRaisesRegex(
            CommandError,
            "An object invalidation was requested but AWS_CLOUDFRONT_DISTRIBUTION is not present in your settings"
        ):
            call_command("sync_s3", "--media-only", "--invalidate")


@patch("django_extensions.management.commands.sync_s3.HAS_BOTO", Mock(side_effect=True))
class SyncS3Tests(TestCase):
    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        media_root = os.path.join(current_dir, "media")
        if os.path.isdir(media_root):
            shutil.rmtree(media_root)
        os.mkdir(media_root)
        test_dirs = [
            os.path.join(media_root, "testdir1"),
            os.path.join(media_root, "testdir2"),
            os.path.join(media_root, "testdir3"),
            os.path.join(media_root, "testdir4"),
            os.path.join(media_root, "testsamenamedir"),
        ]
        for dir_ in test_dirs:
            os.mkdir(dir_)

        test_sub_dir = os.path.join(media_root, "testdir2", "testsubdir1")
        os.mkdir(test_sub_dir)

        test_sub_dir_base = os.path.join(media_root, "testdir1")
        test_sub_dirs = [
            os.path.join(test_sub_dir_base, "testsubdir1"),
            os.path.join(test_sub_dir_base, "testsubdir2"),
            os.path.join(test_sub_dir_base, "testsubdir3"),
            os.path.join(test_sub_dir_base, "testsubdir4"),
        ]

        for dir_ in test_sub_dirs:
            os.mkdir(dir_)

        test_sub_dir_base2 = os.path.join(media_root, "testdir3")
        test_sub_dirs_2 = [
            os.path.join(test_sub_dir_base2, "testsubdir1"),
            os.path.join(test_sub_dir_base2, "testsubdir2"),
            os.path.join(test_sub_dir_base2, "testsubdir3"),
            os.path.join(test_sub_dir_base2, "testsubdir4"),
            os.path.join(test_sub_dir_base2, "testsamenamedir"),
        ]

        for dir_ in test_sub_dirs_2:
            os.mkdir(dir_)

    def tearDown(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        media_root = os.path.join(current_dir, "media")
        shutil.rmtree(media_root)

    @override_settings(
        MEDIA_ROOT=os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "media")
    )
    @override_settings(
        STATIC_ROOT=os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "static")
    )
    @override_settings(AWS_S3_ACCESS_KEY_ID="FAKE_KEY")
    @override_settings(AWS_S3_SECRET_ACCESS_KEY="FAKE_SECRET_KEY")
    @override_settings(AWS_STORAGE_BUCKET_NAME="FAKE_BUCKET_NAME")
    def test_sync_s3_dir_exclusions(self):
        sync_s3_command = Command()
        try:
            call_command(
                "sync_s3",
                "--acl=authenticated-read",
                "--filter-list=testsamenamedir,testdir1",
            )
        except Exception:
            # Exception is expected, we're not actually attempting to connect to S3
            self.assertEqual(0, 0)

        for directory in sync_s3_command.directories:
            for root, dirs, files in os.walk(directory):
                sync_s3_command._handle_upload(
                    root,
                    dirs,
                    files
                )
                dir_name = os.path.basename(root)
                if dir_name == "testdir1":
                    self.assertEqual(len(dirs), 0)
                elif dir_name == "testdir2":
                    self.assertEqual(len(dirs), 1)
                elif dir_name == "testdir3":
                    self.assertEqual(len(dirs), 5)


@patch("django_extensions.management.commands.sync_s3.HAS_BOTO", Mock(side_effect=True))
class SyncS3CommandTests(SyncS3TestsMixin, TestCase):
    @override_settings(
        AWS_S3_ACCESS_KEY_ID="access_key_id",
        AWS_S3_SECRET_ACCESS_KEY="secret_access_key",
        AWS_STORAGE_BUCKET_NAME="bucket_name",
    )
    @patch("sys.stdout", new_callable=StringIO)
    def test_should_raise_CommandError_when_media_folder_has_no_files(self, m_stdout):
        self.mocked_boto.Session.return_value.client.return_value = Mock()
        self.mocked_boto.Session.return_value.resource.return_value = Mock()
        self.mocked_boto.Session.return_value.resource.return_value.Bucket.return_value = Mock()

        # self.mocked_boto.connect_s3.return_value.get_bucket.return_value = Mock()
        # self.mocked_boto.s3.key.Key.return_value = "bucket_key"

        call_command("sync_s3", "--media-only")

        self.assertIn("0 files uploaded.", m_stdout.getvalue())
        self.assertIn("0 files skipped.", m_stdout.getvalue())
