# -*- coding: utf-8 -*-
import os
import sys
import shutil
import logging
import importlib

import django
from django.core.management import call_command, find_commands, load_command_class
from django.test import TestCase
from django.utils.six import StringIO, PY3

from django_extensions.management.modelviz import use_model, generate_graph_data
from . import force_color_support


class MockLoggingHandler(logging.Handler):
    """ Mock logging handler to check for expected logs. """

    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }


class CommandTest(TestCase):
    def test_error_logging(self):
        # Ensure command errors are properly logged and reraised
        from django_extensions.management.base import logger
        logger.addHandler(MockLoggingHandler())
        module_path = "tests.management.commands.error_raising_command"
        module = importlib.import_module(module_path)
        error_raising_command = module.Command()
        self.assertRaises(Exception, error_raising_command.execute)
        handler = logger.handlers[0]
        self.assertEqual(len(handler.messages['error']), 1)


class ShowTemplateTagsTests(TestCase):
    def test_some_output(self):
        out = StringIO()
        call_command('show_template_tags', stdout=out)
        output = out.getvalue()
        # Once django_extension is installed during tests it should appear with
        # its templatetags
        self.assertIn('django_extensions', output)
        # let's check at least one
        self.assertIn('truncate_letters', output)


class CreateAppTests(TestCase):
    def test_command(self):
        if django.VERSION[:2] >= (1, 10):
            return

        tmpname = "testapptest"
        # TODO better temp dir handling
        tmpdir = "/tmp"
        tmppath = os.path.join(tmpdir, tmpname)
        self.assertFalse(os.path.isdir(tmppath))

        out = StringIO()
        try:
            call_command('create_app', tmpname, parent_path=tmpdir, stdout=out)
        finally:
            if os.path.isdir(tmppath):
                shutil.rmtree(tmppath)

        output = out.getvalue()
        self.assertIn("Application '%s' created." % tmpname, output)


class AdminGeneratorTests(TestCase):
    def test_command(self):
        out = StringIO()
        call_command('admin_generator', 'django_extensions', stdout=out)
        output = out.getvalue()
        self.assertIn("@admin.register(Secret)", output)
        self.assertIn("class SecretAdmin(admin.ModelAdmin):", output)
        if PY3:
            self.assertIn("list_display = ('id', 'name', 'text')", output)
            self.assertIn("search_fields = ('name',)", output)
        else:
            self.assertIn("list_display = (u'id', u'name', u'text')", output)
            self.assertIn("search_fields = (u'name',)", output)


class DescribeFormTests(TestCase):
    def test_command(self):
        out = StringIO()
        call_command('describe_form', 'django_extensions.Secret', stdout=out)
        output = out.getvalue()
        self.assertIn("class SecretForm(forms.Form):", output)
        self.assertRegexpMatches(output, "name = forms.CharField\(.*max_length=255")
        self.assertRegexpMatches(output, "name = forms.CharField\(.*required=False")
        self.assertRegexpMatches(output, "name = forms.CharField\(.*label=u?'Name'")
        self.assertRegexpMatches(output, "text = forms.CharField\(.*required=False")
        self.assertRegexpMatches(output, "text = forms.CharField\(.*label=u?'Text'")


class UpdatePermissionsTests(TestCase):
    def test_works(self):
        from django.db import models

        class PermModel(models.Model):
            class Meta:
                app_label = 'django_extensions'
                permissions = (('test_permission', 'test_permission'),)

        original_stdout = sys.stdout
        out = sys.stdout = StringIO()
        call_command('update_permissions', stdout=out, verbosity=3)
        sys.stdout = original_stdout
        self.assertIn("Can change perm model", out.getvalue())


class CommandSignalTests(TestCase):
    pre = None
    post = None

    def test_works(self):
        from django_extensions.management.signals import post_command, \
            pre_command
        from django_extensions.management.commands.show_template_tags import \
            Command

        def pre(sender, **kwargs):
            CommandSignalTests.pre = dict(**kwargs)

        def post(sender, **kwargs):
            CommandSignalTests.post = dict(**kwargs)

        pre_command.connect(pre, Command)
        post_command.connect(post, Command)

        out = StringIO()
        call_command('show_template_tags', stdout=out)

        self.assertIn('args', CommandSignalTests.pre)
        self.assertIn('kwargs', CommandSignalTests.pre)

        self.assertIn('args', CommandSignalTests.post)
        self.assertIn('kwargs', CommandSignalTests.post)
        self.assertIn('outcome', CommandSignalTests.post)


class CommandClassTests(TestCase):
    def setUp(self):
        management_dir = os.path.join('django_extensions', 'management')
        self.commands = find_commands(management_dir)

    def test_load_commands(self):
        """Try to load every management command to catch exceptions."""
        try:
            for command in self.commands:
                load_command_class('django_extensions', command)
        except Exception as e:
            self.fail("Can't load command class of {0}\n{1}".format(command, e))


class GraphModelsTests(TestCase):
    """
    Tests for the `graph_models` management command.
    """
    def test_use_model(self):
        include_models = [
            'NoWildcardInclude',
            'Wildcard*InsideInclude',
            '*WildcardPrefixInclude',
            'WildcardSuffixInclude*',
            '*WildcardBothInclude*'
        ]
        exclude_models = [
            'NoWildcardExclude',
            'Wildcard*InsideExclude',
            '*WildcardPrefixExclude',
            'WildcardSuffixExclude*',
            '*WildcardBothExclude*'
        ]
        # Any model name should be used if neither include or exclude
        # are defined.
        self.assertTrue(use_model(
            'SomeModel',
            None,
            None
        ))
        # Any model name should be allowed if `*` is in `include_models`.
        self.assertTrue(use_model(
            'SomeModel',
            ['OtherModel', '*', 'Wildcard*Model'],
            None
        ))
        # No model name should be allowed if `*` is in `exclude_models`.
        self.assertFalse(use_model(
            'SomeModel',
            None,
            ['OtherModel', '*', 'Wildcard*Model']
        ))
        # Some tests with the `include_models` defined above.
        self.assertFalse(use_model(
            'SomeModel',
            include_models,
            None
        ))
        self.assertTrue(use_model(
            'NoWildcardInclude',
            include_models,
            None
        ))
        self.assertTrue(use_model(
            'WildcardSomewhereInsideInclude',
            include_models,
            None
        ))
        self.assertTrue(use_model(
            'MyWildcardPrefixInclude',
            include_models,
            None
        ))
        self.assertTrue(use_model(
            'WildcardSuffixIncludeModel',
            include_models,
            None
        ))
        self.assertTrue(use_model(
            'MyWildcardBothIncludeModel',
            include_models,
            None
        ))
        # Some tests with the `exclude_models` defined above.
        self.assertTrue(use_model(
            'SomeModel',
            None,
            exclude_models
        ))
        self.assertFalse(use_model(
            'NoWildcardExclude',
            None,
            exclude_models
        ))
        self.assertFalse(use_model(
            'WildcardSomewhereInsideExclude',
            None,
            exclude_models
        ))
        self.assertFalse(use_model(
            'MyWildcardPrefixExclude',
            None,
            exclude_models
        ))
        self.assertFalse(use_model(
            'WildcardSuffixExcludeModel',
            None,
            exclude_models
        ))
        self.assertFalse(use_model(
            'MyWildcardBothExcludeModel',
            None,
            exclude_models
        ))

    def test_no_models_dot_py(self):
        data = generate_graph_data(['testapp_with_no_models_file'])
        self.assertEqual(len(data['graphs']), 1)

        model_name = data['graphs'][0]['models'][0]['name']
        self.assertEqual(model_name, 'TeslaCar')


class ShowUrlsTests(TestCase):
    """
    Tests for the `show_urls` management command.
    """
    def test_color(self):
        with force_color_support:
            out = StringIO()
            call_command('show_urls', stdout=out)
            self.output = out.getvalue()
            self.assertIn('\x1b', self.output)

    def test_no_color(self):
        with force_color_support:
            out = StringIO()
            call_command('show_urls', '--no-color', stdout=out)
            self.output = out.getvalue()
            self.assertNotIn('\x1b', self.output)
