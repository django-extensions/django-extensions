# -*- coding: utf-8 -*-
from io import StringIO

from django.test import TestCase
from django.db import models
from django.core.management import CommandError, call_command


class DescribeFormExceptionsTests(TestCase):
    """Tests for describe_form command exceptions."""

    def test_should_raise_CommandError_if_invalid_arg(self):
        with self.assertRaisesRegex(CommandError, "Need application and model name in the form: appname.model"):
            call_command('describe_form', 'testapp')


class DescribeFormTests(TestCase):
    """Tests for describe_form command."""

    def setUp(self):
        self.out = StringIO()

        class BaseModel(models.Model):
            title = models.CharField(max_length=50)
            body = models.TextField()

            class Meta:
                app_label = 'testapp'

        class NonEditableModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            title = models.CharField(max_length=50)

            class Meta:
                app_label = 'testapp'

    def test_should_print_form_definition_for_TestModel(self):
        expected_result = '''from django import forms
from testapp.models import BaseModel

class BaseModelForm(forms.Form):
    title = forms.CharField(label='Title', max_length=50)
    body = forms.CharField(label='Body')'''

        call_command('describe_form', 'testapp.BaseModel', stdout=self.out)

        self.assertIn(expected_result, self.out.getvalue())

    def test_should_print_form_definition_for_TestModel_with_non_editable_field(self):
        expected_result = '''from django import forms
from testapp.models import NonEditableModel

class NonEditableModelForm(forms.Form):
    title = forms.CharField(label='Title', max_length=50)'''

        call_command('describe_form', 'testapp.NonEditableModel', stdout=self.out)

        self.assertIn(expected_result, self.out.getvalue())

    def test_should_print_form_with_fields_for_TestModel(self):
        not_expected = '''body = forms.CharField(label='Body')'''

        call_command('describe_form', 'testapp.BaseModel', '--fields=title', stdout=self.out)

        self.assertNotIn(not_expected, self.out.getvalue())
