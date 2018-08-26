# -*- coding: utf-8 -*-
import django_extensions.management.commands.sync_s3
import os
import shutil

from django.test import TestCase
from django.test.utils import override_settings
from django_extensions.management.commands.sync_s3 import Command


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
