# -*- coding: utf-8 -*-
import logging
import os
import sys

from django.core.management import (
    call_command, find_commands, load_command_class,
)
from django.test import TestCase

from django_extensions.compat import StringIO, importlib
from django_extensions.management.modelviz import use_model


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
    """Try to load every management command to catch exceptions."""
    def test_load_commands(self):
        try:
            management_dir = os.path.join('django_extensions', 'management')
            commands = find_commands(management_dir)
            for command in commands:
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
