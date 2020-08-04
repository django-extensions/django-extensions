# -*- coding: utf-8 -*-
from django.core.management import call_command


def test_without_args(capsys):
    call_command('generate_password')

    out, err = capsys.readouterr()
    assert out


def test_with_length_args(capsys):
    length = 20
    call_command('generate_password', length=length)

    out, err = capsys.readouterr()
    assert len(out.rstrip('\n')) == length
