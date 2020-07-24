# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import call_command


def test_without_args(capsys):
    call_command("print_settings")

    out, err = capsys.readouterr()
    assert "DEBUG" in out
    assert "INSTALLED_APPS" in out
    assert "DATABASE_ENGINE" not in out


def test_with_setting_args(capsys):
    call_command("print_settings", "DEBUG")

    out, err = capsys.readouterr()
    assert "DEBUG" in out
    assert "INSTALLED_APPS" not in out


def test_with_multiple_setting_args(capsys):
    call_command(
        "print_settings",
        "SECRET_KEY",
        "DATABASES",
        "INSTALLED_APPS",
        "--show-secrets=True",
    )

    out, err = capsys.readouterr()
    assert "DEBUG" not in out
    assert "SECRET_KEY" in out
    assert "DATABASES" in out
    assert "INSTALLED_APPS" in out


def test_with_not_show_secrets(capsys):
    call_command(
        "print_settings", "SECRET_KEY",
    )

    out, err = capsys.readouterr()

    assert "*******" in out


def test_format(capsys):
    call_command(
        "print_settings", "DEBUG", "--format=text",
    )

    out, err = capsys.readouterr()
    expected = "DEBUG = False\n"
    assert expected == out


def test_format_json_without_indent(capsys):
    call_command(
        "print_settings", "DEBUG", "--format=json", "--indent=0",
    )

    expected = '{\n"DEBUG": false\n}\n'
    out, err = capsys.readouterr()
    assert expected == out


def test_show_database_option(capsys):
    call_command(
        "print_settings", "--database",
    )

    out, err = capsys.readouterr()
    assert "DATABASE_ENGINE" in out
