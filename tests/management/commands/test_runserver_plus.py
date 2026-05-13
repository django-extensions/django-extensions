import pytest
from django.core.management import call_command

from unittest import mock

from werkzeug.serving import WSGIRequestHandler

from django_extensions.management.commands import runserver_plus


@pytest.mark.django_db
def test_initialize_runserver_plus():
    with mock.patch(
        "django_extensions.management.commands.runserver_plus.run_simple"
    ) as run_simple:
        call_command("runserver_plus")
        assert run_simple.called, "werkzeug.run_simple was not called"


def test_werk_log_fallback_passes_self_to_orig_log():
    orig_log = mock.Mock(name="orig_log")
    saved = WSGIRequestHandler.log
    WSGIRequestHandler.log = orig_log
    try:
        runserver_plus.set_werkzeug_log_color()
        werk_log = WSGIRequestHandler.log

        class FakeHandler:
            pass

        handler = FakeHandler()
        werk_log(handler, "error", "boom %s", "x")

        orig_log.assert_called_once_with(handler, "error", "boom %s", "x")
    finally:
        WSGIRequestHandler.log = saved
