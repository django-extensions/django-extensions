# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_extensions.management.commands.notes import Command


def test_without_args(capsys, settings):
    print_settings = Command()
    print_settings.run_from_argv(['manage.py', 'notes'])

    out, err = capsys.readouterr()
    assert 'tests/testapp/__init__.py:\n  * [  4] TODO  this is a test todo\n\n' in out


def test_empty_array_templates(capsys, settings):
    settings.TEMPLATES = []
    print_settings = Command()
    print_settings.run_from_argv(['manage.py', 'notes'])

    out, err = capsys.readouterr()
    assert 'tests/testapp/__init__.py:\n  * [  4] TODO  this is a test todo\n\n' in out
