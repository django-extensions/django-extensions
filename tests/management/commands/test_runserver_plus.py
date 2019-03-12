# -*- coding: utf-8 -*-
import pytest
from django_extensions.management.commands import runserver_plus

try:
    from unittest import mock
except ImportError:
    import mock


@pytest.mark.django_db
def test_initialize_runserver_plus():
    with mock.patch('werkzeug.run_simple') as run_simple:
        command = runserver_plus.Command()
        command.run_from_argv(['manage.py', 'runserver_plus'])
        assert run_simple.called, 'werkzeug.run_simple was not called'
