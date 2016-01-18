# -*- coding: utf-8 -*-
import logging
import os

import pytest
from django.core.management import (
    call_command, find_commands, load_command_class,
)
from django.db import models

from django_extensions.compat import importlib
from django_extensions.management.base import logger

pytestmark = pytest.mark.django_db


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


def test_error_logging():
    """
    Ensure command errors are properly logged and reraised
    """
    logger.addHandler(MockLoggingHandler())
    module_path = 'tests.management.commands.error_raising_command'
    module = importlib.import_module(module_path)
    error_raising_command = module.Command()
    with pytest.raises(Exception):
        error_raising_command.execute()
    handler = logger.handlers[0]
    assert len(handler.messages['error']) == 1


def test_show_template_tags(capsys):
    call_command('show_template_tags')
    output = capsys.readouterr()[0]
    # Once django_extension is installed during tests it should appear with
    # its templatetags
    assert 'django_extensions' in output
    # let's check at least one
    assert 'truncate_letters' in output


def test_update_permissions(capsys):

    class PermModel(models.Model):

        class Meta:
            app_label = 'django_extensions'
            permissions = (('test_permission', 'test_permission'),)

    call_command('update_permissions', verbosity=3)
    assert 'Can change perm model' in capsys.readouterr()[0]


class TestCommandSignal:
    pre = None
    post = None

    def test_works(self):
        from django_extensions.management.signals import post_command, \
            pre_command
        from django_extensions.management.commands.show_template_tags import \
            Command

        def pre(sender, **kwargs):
            TestCommandSignal.pre = dict(**kwargs)

        def post(sender, **kwargs):
            TestCommandSignal.post = dict(**kwargs)

        pre_command.connect(pre, Command)
        post_command.connect(post, Command)

        call_command('show_template_tags')

        assert 'args' in TestCommandSignal.pre
        assert 'kwargs' in TestCommandSignal.pre

        assert 'args' in TestCommandSignal.post
        assert 'kwargs' in TestCommandSignal.post
        assert 'outcome' in TestCommandSignal.post


def test_load_commands():
    """Try to load every management command to catch exceptions."""
    management_dir = os.path.join('django_extensions', 'management')
    commands = find_commands(management_dir)
    for command in commands:
        load_command_class('django_extensions', command)
