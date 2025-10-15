import os
import pytest
from django.core.management import call_command

from unittest import mock


@pytest.mark.django_db
def test_initialize_runserver_plus():
    with mock.patch(
        "django_extensions.management.commands.runserver_plus.run_simple"
    ) as run_simple:
        call_command("runserver_plus")
        assert run_simple.called, "werkzeug.run_simple was not called"


@pytest.mark.django_db
def test_initialize_runserver_plus_with_addrport_via_env_var():
    with mock.patch(
        "django_extensions.management.commands.runserver_plus.run_simple"
    ) as run_simple:
        os.environ["RUNSERVERPLUS_SERVER_ADDRESS_PORT"] = "1.1.1.1:8001"
        call_command("runserver_plus")
        assert run_simple.called, "werkzeug.run_simple was not called"
        assert run_simple.call_args[0][0] == "1.1.1.1"
        assert run_simple.call_args[0][1] == 8001
