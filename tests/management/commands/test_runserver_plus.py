import os

import pytest
from django.core.management import call_command
from django.test.utils import override_settings

from unittest import mock


class FakeDebuggedApplication:
    def __init__(self, app, evalex):
        self.app = app
        self.evalex = evalex
        self.pin = "123-456-789"
        self.trusted_hosts = [".localhost", "127.0.0.1"]


@pytest.mark.django_db
def test_initialize_runserver_plus():
    with mock.patch(
        "django_extensions.management.commands.runserver_plus.run_simple"
    ) as run_simple:
        call_command("runserver_plus")
        assert run_simple.called, "werkzeug.run_simple was not called"


@pytest.mark.django_db
def test_runserver_plus_shows_startup_messages_without_reloader(monkeypatch, capsys):
    monkeypatch.delenv("RUNSERVER_PLUS_SHOW_MESSAGES", raising=False)
    monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)

    with (
        mock.patch(
            "django_extensions.management.commands.runserver_plus.DebuggedApplication",
            FakeDebuggedApplication,
        ),
        mock.patch(
            "django_extensions.management.commands.runserver_plus.run_simple"
        ),
        mock.patch("django_extensions.management.commands.runserver_plus._log"),
    ):
        call_command("runserver_plus", use_reloader=False)

    output = capsys.readouterr().out
    assert "Using the Werkzeug debugger (https://werkzeug.palletsprojects.com/)" in output


@pytest.mark.django_db
@override_settings(RUNSERVER_PLUS_TRUSTED_HOSTS=["debug.example"])
def test_runserver_plus_wraps_debugger_without_reloader(monkeypatch):
    monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)
    monkeypatch.delenv("WERKZEUG_DEBUG_PIN", raising=False)

    with (
        mock.patch(
            "django_extensions.management.commands.runserver_plus.DebuggedApplication",
            FakeDebuggedApplication,
        ),
        mock.patch(
            "django_extensions.management.commands.runserver_plus.run_simple"
        ) as run_simple,
        mock.patch("django_extensions.management.commands.runserver_plus._log") as log,
    ):
        call_command("runserver_plus", use_reloader=False, startup_messages="never")

    app = run_simple.call_args.args[2]
    assert isinstance(app, FakeDebuggedApplication)
    assert "WERKZEUG_RUN_MAIN" not in os.environ
    assert run_simple.call_args.kwargs["use_debugger"] is False
    assert app.trusted_hosts == ["debug.example", "127.0.0.1"]
    log.assert_any_call("warning", " * Debugger is active!")
    log.assert_any_call("info", " * Debugger PIN: %s", "123-456-789")


@pytest.mark.django_db
def test_runserver_plus_sets_nopin_before_reloader_parent(monkeypatch):
    monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)
    monkeypatch.delenv("WERKZEUG_DEBUG_PIN", raising=False)

    with (
        mock.patch(
            "django_extensions.management.commands.runserver_plus.DebuggedApplication"
        ) as debugged_application,
        mock.patch(
            "django_extensions.management.commands.runserver_plus.run_simple"
        ) as run_simple,
    ):
        call_command(
            "runserver_plus",
            use_reloader=True,
            nopin=True,
            startup_messages="never",
        )

    debugged_application.assert_not_called()
    assert os.environ["WERKZEUG_DEBUG_PIN"] == "off"
    assert run_simple.call_args.kwargs["use_debugger"] is False


@pytest.mark.django_db
@override_settings(RUNSERVER_PLUS_TRUSTED_HOSTS=["debug.example"])
def test_runserver_plus_wraps_debugger_in_reloader_child(monkeypatch):
    monkeypatch.setenv("WERKZEUG_RUN_MAIN", "true")
    monkeypatch.delenv("WERKZEUG_DEBUG_PIN", raising=False)

    with (
        mock.patch(
            "django_extensions.management.commands.runserver_plus.DebuggedApplication",
            FakeDebuggedApplication,
        ),
        mock.patch(
            "django_extensions.management.commands.runserver_plus.run_simple"
        ) as run_simple,
        mock.patch("django_extensions.management.commands.runserver_plus._log") as log,
    ):
        call_command(
            "runserver_plus",
            use_reloader=True,
            startup_messages="never",
        )

    app = run_simple.call_args.args[2]
    assert isinstance(app, FakeDebuggedApplication)
    assert run_simple.call_args.kwargs["use_debugger"] is False
    assert app.trusted_hosts == ["debug.example", "127.0.0.1"]
    log.assert_not_called()
