# -*- coding: utf-8 -*-
from io import StringIO

from django.core.management import call_command
from django.db import models
from django.test import TestCase


class AdminGeneratorTests(TestCase):
    """Tests for admin_generator management command."""

    def setUp(self):
        self.out = StringIO()

    def test_command(self):
        call_command('admin_generator', 'django_extensions', stdout=self.out)
        output = self.out.getvalue()
        self.assertIn("@admin.register(Secret)", output)
        self.assertIn("class SecretAdmin(admin.ModelAdmin):", output)
        self.assertIn("list_display = ('id', 'name', 'text')", output)
        self.assertIn("search_fields = ('name',)", output)

    def test_should_print_warning_if_given_app_is_not_installed(self):
        expected_output = '''This command requires an existing app name as argument
Available apps:
    admin'''
        call_command('admin_generator', 'invalid_app', stderr=self.out)

        for expected_line in expected_output.splitlines():
            self.assertIn(expected_line, self.out.getvalue())

    def test_should_print_admin_class_for_User_model_only(self):
        call_command('admin_generator', 'auth', 'Group', stdout=self.out)

        self.assertIn('from .models import Group', self.out.getvalue())

    def test_should_print_admin_class_with_date_hierarchy(self):
        class TestAdminModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            title = models.CharField(max_length=50)

            class Meta:
                app_label = 'testapp'

        call_command('admin_generator', 'testapp', 'TestAdminModel',
                     stdout=self.out)

        self.assertIn("date_hierarchy = 'created_at'", self.out.getvalue())
