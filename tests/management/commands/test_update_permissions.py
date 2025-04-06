# -*- coding: utf-8 -*-
import sys
from io import StringIO

import django
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.db import models
from django.test import TestCase


if django.VERSION >= (5, 0):
    DJANGO_EXTENSIONS_NAME = "Django Extensions"
    TESTAPP_NAME = "Testapp"
else:
    DJANGO_EXTENSIONS_NAME = "django_extensions"
    TESTAPP_NAME = "testapp"


class UpdatePermissionsTests(TestCase):
    def setUp(self):
        class PermModel(models.Model):
            class Meta:
                app_label = "django_extensions"
                permissions = (("test_permission", "test_permission"),)

        class TestModel(models.Model):
            class Meta:
                app_label = "testapp"
                permissions = (("testapp_permission", "testapp_permission"),)

    def test_works(self):
        original_stdout = sys.stdout
        out = sys.stdout = StringIO()
        call_command("update_permissions", stdout=out, verbosity=3)
        sys.stdout = original_stdout
        self.assertIn("Can change perm model", out.getvalue())

    def test_should_reload_permission_only_for_specified_apps(self):
        original_stdout = sys.stdout
        out = sys.stdout = StringIO()

        call_command("update_permissions", "--apps=testapp", stdout=out, verbosity=3)

        sys.stdout = original_stdout
        self.assertNotIn(
            f"{DJANGO_EXTENSIONS_NAME} | perm model | Can add perm model",
            out.getvalue(),
        )
        self.assertIn(
            f"{TESTAPP_NAME} | test model | Can add test model", out.getvalue()
        )

    def test_should_reload_permission_only_for_all_apps(self):
        original_stdout = sys.stdout
        out = sys.stdout = StringIO()

        call_command("update_permissions", verbosity=3)

        sys.stdout = original_stdout
        self.assertIn(
            f"{DJANGO_EXTENSIONS_NAME} | perm model | Can add perm model",
            out.getvalue(),
        )
        self.assertIn(
            f"{TESTAPP_NAME} | test model | Can add test model", out.getvalue()
        )

    def test_should_update_permission_if_name_changed(self):
        original_stdout = sys.stdout
        out = sys.stdout = StringIO()

        call_command("update_permissions", verbosity=3, create_only=True)
        self.assertIn(
            f"{TESTAPP_NAME} | test model | testapp_permission", out.getvalue()
        )

        testapp_permission = Permission.objects.get(name="testapp_permission")
        testapp_permission.name = "testapp_permission_wrong"
        testapp_permission.save()

        call_command("update_permissions", verbosity=3, update_only=True)

        sys.stdout = original_stdout
        self.assertIn(
            f"'{TESTAPP_NAME} | test model | testapp_permission_wrong' to '{TESTAPP_NAME} | test model | testapp_permission'",
            out.getvalue(),
        )
