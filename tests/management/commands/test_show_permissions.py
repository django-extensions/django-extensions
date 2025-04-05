# -*- coding: utf-8 -*-
import sys
from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase


class ShowPermissionsTests(TestCase):
    def _run_command(self, *args, **kwargs):
        """
        Utility to run the command and return captured output.
        """
        out = StringIO()
        sys_stdout = sys.stdout
        sys.stdout = out
        try:
            call_command("show_permissions", *args, **kwargs)
        finally:
            sys.stdout = sys_stdout
        return out.getvalue()

    def test_should_list_permissions_for_all_apps_excluding_defaults(self):
        output = self._run_command(verbosity=3)
        auth_verbose = apps.get_app_config("auth").verbose_name
        self.assertNotIn(f"Permissions for {auth_verbose}", output)
        self.assertNotIn("auth.add_user", output)

    def test_should_include_all_apps_with_flag(self):
        output = self._run_command("--all", verbosity=3)
        auth_verbose = apps.get_app_config("auth").verbose_name
        self.assertIn(f"Permissions for {auth_verbose}", output)
        self.assertIn("auth.add_user", output)

        admin_config = apps.get_app_config("admin")
        self.assertIn(f"Permissions for {admin_config.verbose_name}", output)

    def test_should_filter_by_app_label(self):
        output = self._run_command("--app-label", "auth", verbosity=3)
        auth_verbose = apps.get_app_config("auth").verbose_name
        self.assertIn(f"Permissions for {auth_verbose}", output)
        self.assertIn("auth.change_user", output)

    def test_should_filter_by_app_and_model(self):
        output = self._run_command("auth.user", verbosity=3)
        auth_verbose = apps.get_app_config("auth").verbose_name
        user_model_verbose = apps.get_model("auth", "user")._meta.verbose_name
        expected_header = (
            f"Permissions for {auth_verbose} | {user_model_verbose}"
        )
        self.assertIn(expected_header, output)
        self.assertIn("auth.change_user", output)

    def test_should_raise_error_for_invalid_model(self):
        with self.assertRaisesMessage(
            Exception, "Content type not found for 'fakeapp.nosuchmodel'"
        ):
            self._run_command("fakeapp.nosuchmodel", verbosity=3)

    def test_should_return_permissions_for_test_model(self):
        if apps.is_installed("tests"):
            output = self._run_command("tests.samplemodel", verbosity=3)
            self.assertIn("tests.samplemodel", output.lower())
            self.assertIn("can add", output.lower())

    def test_should_raise_error_for_invalid_app_label(self):
        with self.assertRaisesMessage(
            Exception,
            'No content types found for app label "noapp".'
        ):
            self._run_command("--app-label", "noapp", verbosity=3)
