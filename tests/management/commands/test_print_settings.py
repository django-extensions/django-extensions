# -*- coding: utf-8 -*-

import pytest
from django.core.management import CommandError, call_command


def test_without_args(capsys):
    call_command('print_settings')

    out, err = capsys.readouterr()
    assert 'DEBUG' in out
    assert 'INSTALLED_APPS' in out


def test_with_setting_args(capsys):
    call_command('print_settings', 'DEBUG')

    out, err = capsys.readouterr()
    assert 'DEBUG' in out
    assert 'INSTALLED_APPS' not in out


def test_with_setting_wildcard(capsys):
    call_command('print_settings', '*_DIRS')

    out, err = capsys.readouterr()
    assert 'FIXTURE_DIRS' in out
    assert 'STATICFILES_DIRS' in out
    assert 'INSTALLED_APPS' not in out


def test_with_setting_fail(capsys):
    with pytest.raises(CommandError, match='INSTALLED_APPZ not found in settings.'):
        call_command('print_settings', '-f', 'INSTALLED_APPZ')


def test_with_multiple_setting_args(capsys):
    call_command(
        'print_settings',
        'SECRET_KEY',
        'DATABASES',
        'INSTALLED_APPS',
    )

    out, err = capsys.readouterr()
    assert 'DEBUG' not in out
    assert 'SECRET_KEY' in out
    assert 'DATABASES' in out
    assert 'INSTALLED_APPS' in out


def test_format(capsys):
    call_command(
        'print_settings',
        'DEBUG',
        '--format=text',
    )

    out, err = capsys.readouterr()
    expected = 'DEBUG = False\n'
    assert expected == out


def test_format_json_without_indent(capsys):
    call_command(
        'print_settings',
        'DEBUG',
        '--format=json',
        '--indent=0',
    )

    expected = '{\n"DEBUG": false\n}\n'
    out, err = capsys.readouterr()
    assert expected == out
