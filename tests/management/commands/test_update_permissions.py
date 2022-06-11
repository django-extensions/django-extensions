# -*- coding: utf-8 -*-
import sys
from io import StringIO

from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.db import models
from django.test import TestCase


class UpdatePermissionsTests(TestCase):

    def setUp(self):
        class PermModel(models.Model):
            class Meta:
                app_label = 'django_extensions'
                permissions = (('test_permission', 'test_permission'),)

        class TestModel(models.Model):
            class Meta:
                app_label = 'testapp'
                permissions = (('testapp_permission', 'testapp_permission'),)

    def test_works(self):
        original_stdout = sys.stdout
        out = sys.stdout = StringIO()
        call_command('update_permissions', stdout=out, verbosity=3)
        sys.stdout = original_stdout
        self.assertIn("Can change perm model", out.getvalue())

    def test_should_reload_permission_only_for_specified_apps(self):
        original_stdout = sys.stdout
        out = sys.stdout = StringIO()

        call_command('update_permissions', '--apps=testapp',
                     stdout=out, verbosity=3)

        sys.stdout = original_stdout
        self.assertNotIn('django_extensions | perm model | Can add perm model', out.getvalue())
        self.assertIn('testapp | test model | Can add test model', out.getvalue())

    def test_should_reload_permission_only_for_all_apps(self):
        original_stdout = sys.stdout
        out = sys.stdout = StringIO()

        call_command('update_permissions', verbosity=3)

        sys.stdout = original_stdout
        self.assertIn('django_extensions | perm model | Can add perm model', out.getvalue())
        self.assertIn('testapp | test model | Can add test model', out.getvalue())

    def test_should_update_permission_if_name_changed(self):
        original_stdout = sys.stdout
        out = sys.stdout = StringIO()

        call_command('update_permissions', verbosity=3, create_only=True)
        self.assertIn('testapp | test model | testapp_permission', out.getvalue())

        testapp_permission = Permission.objects.get(name="testapp_permission")
        testapp_permission.name = "testapp_permission_wrong"
        testapp_permission.save()

        call_command('update_permissions', verbosity=3, update_only=True)

        sys.stdout = original_stdout
        self.assertIn("'testapp | test model | testapp_permission_wrong' to 'testapp | test model | testapp_permission'", out.getvalue())
