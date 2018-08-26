# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_extensions.management.commands.generate_password import Command


def test_without_args(capsys):
    generate_password = Command()
    generate_password.run_from_argv(['manage.py', 'generate_password'])

    out, err = capsys.readouterr()
    assert out


def test_with_length_args(capsys):
    length = 20
    generate_password = Command()
    generate_password.run_from_argv(['manage.py', 'generate_password',
                                     '--length', str(length)])

    out, err = capsys.readouterr()
    assert len(out.rstrip('\n')) == length
