# -*- coding: utf-8 -*-
import os
import pathlib
import pytest
from django.core.management import call_command
from django_extensions.management.commands import runserver_plus

from unittest import mock


@pytest.mark.django_db
def test_initialize_runserver_plus():
    with mock.patch('django_extensions.management.commands.runserver_plus.run_simple') as run_simple:
        call_command('runserver_plus')
        assert run_simple.called, 'werkzeug.run_simple was not called'


def test_get_directory_expands_vars():
    assert "/user/home" == runserver_plus.Command._get_directory("/user/home/file.txt")
    assert os.path.split(os.getcwd())[0] == runserver_plus.Command._get_directory("$PWD")


def test_get_directory_expands_vars():
    assert "/user/home" == runserver_plus.Command._get_directory("/user/home/file.txt")
    assert os.path.split(os.getcwd())[0] == runserver_plus.Command._get_directory("$PWD")
    assert os.path.split(pathlib.Path.home())[0] == runserver_plus.Command._get_directory("~")

