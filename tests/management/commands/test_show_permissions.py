# -*- coding: utf-8 -*-
import sys
from io import StringIO

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

        # Should not include default apps like 'auth' unless explicitly allowed
        self.assertNotIn("Permissions for Authentication and Authorization", output)
        self.assertNotIn("auth.add_user", output)

    def test_should_include_all_apps_with_flag(self):
        output = self._run_command("--all", verbosity=3)

        # Should include default apps like 'auth' and 'admin'
        self.assertIn("Permissions for Authentication and Authorization", output)
        self.assertIn("auth.add_user", output)
        self.assertIn("admin", output)

    def test_should_filter_by_app_label(self):
        output = self._run_command("--app-label", "auth", verbosity=3)

        self.assertIn("Permissions for Authentication and Authorization", output)
        self.assertIn("auth.change_user", output)

    def test_should_filter_by_app_and_model(self):
        output = self._run_command("auth.user", verbosity=3)

        self.assertIn("Permissions for Authentication and Authorization | user", output)
        self.assertIn("auth.change_user", output)

    def test_should_raise_error_for_invalid_model(self):
        with self.assertRaisesMessage(
            Exception, "Content type not found for 'fakeapp.nosuchmodel'"
        ):
            self._run_command("fakeapp.nosuchmodel", verbosity=3)
