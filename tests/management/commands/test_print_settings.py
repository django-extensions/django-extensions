# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_extensions.management.commands.print_settings import Command


def test_without_args(capsys):
    print_settings = Command()
    print_settings.run_from_argv(['manage.py', 'print_settings'])

    out, err = capsys.readouterr()
    assert 'DEBUG' in out
    assert 'INSTALLED_APPS' in out


def test_with_setting_args(capsys):
    print_settings = Command()
    print_settings.run_from_argv(['manage.py', 'print_settings', 'DEBUG'])

    out, err = capsys.readouterr()
    assert 'DEBUG' in out
    assert 'INSTALLED_APPS' not in out


def test_with_multiple_setting_args(capsys):
    print_settings = Command()
    print_settings.run_from_argv([
        'manage.py',
        'print_settings',
        'SECRET_KEY',
        'DATABASES',
        'INSTALLED_APPS',
    ])

    out, err = capsys.readouterr()
    assert 'DEBUG' not in out
    assert 'SECRET_KEY' in out
    assert 'DATABASES' in out
    assert 'INSTALLED_APPS' in out


def test_format(capsys):
    print_settings = Command()
    print_settings.run_from_argv([
        'manage.py',
        'print_settings',
        'DEBUG',
        '--format=text',
    ])

    out, err = capsys.readouterr()
    expected = 'DEBUG = False\n'
    assert expected == out


def test_format_json_without_indent(capsys):
    print_settings = Command()
    print_settings.run_from_argv([
        'manage.py',
        'print_settings',
        'DEBUG',
        '--format=json',
        '--indent=0',
    ])

    expected = '{\n"DEBUG": false\n}\n'
    out, err = capsys.readouterr()
    assert expected == out
