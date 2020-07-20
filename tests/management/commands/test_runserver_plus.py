# -*- coding: utf-8 -*-
import pytest
from django.core.management import call_command

from unittest import mock


@pytest.mark.django_db
def test_initialize_runserver_plus():
    with mock.patch('werkzeug.run_simple') as run_simple:
        call_command('runserver_plus')
        assert run_simple.called, 'werkzeug.run_simple was not called'
