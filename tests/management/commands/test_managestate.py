# -*- coding: utf-8 -*-
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from django.core.management import CommandError, call_command
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

from django_extensions.management.commands.managestate import (
    DEFAULT_FILENAME,
    DEFAULT_STATE,
    Command,
)

pytestmark = [pytest.mark.django_db]

COMMAND = "managestate"
DEFAULT_FILE = Path(DEFAULT_FILENAME)


@pytest.fixture
def make_dump(request):
    request.addfinalizer(DEFAULT_FILE.unlink)
    return call_command(COMMAND, "dump", "-v", 0)


@pytest.fixture
def cmd_data():
    cmd = Command()
    cmd.verbosity = 0
    cmd.conn = connection
    data = cmd.get_migrated_apps()
    data.update(cmd.get_applied_migrations())
    return data


class TestManageStateExceptions:
    """Tests for managestate management command exceptions."""

    def test_bad_action(self):
        with pytest.raises(CommandError):
            call_command(COMMAND, "bad_action")

    def test_no_such_file(self):
        with pytest.raises(CommandError):
            call_command(COMMAND, "load", "-f", "non_existent_file")

    def test_not_a_file(self):
        with pytest.raises(CommandError), TemporaryDirectory() as tmp_dir:
            call_command(COMMAND, "load", "-f", tmp_dir)

    @pytest.mark.usefixtures("make_dump")
    def test_no_such_state(self):
        with pytest.raises(CommandError):
            call_command(COMMAND, "load", "non_existent_state")


class TestManageState:
    """Tests managestate management command"""

    def test_dump(self, request, capsys):
        request.addfinalizer(DEFAULT_FILE.unlink)
        call_command(COMMAND, "dump", "-v", 0)
        stdout, _ = capsys.readouterr()
        assert DEFAULT_FILE.exists()
        assert "successfully saved" in stdout

    @pytest.mark.parametrize("filename", [DEFAULT_FILENAME, "custom_f1l3n4m3.json"])
    def test_dump_files(self, request, filename):
        path = Path(filename)
        request.addfinalizer(path.unlink)
        call_command(COMMAND, "dump", "-f", filename)
        assert path.exists()

    @pytest.mark.parametrize("state", [DEFAULT_STATE, "custom_state"])
    def test_dump_states(self, request, state):
        request.addfinalizer(DEFAULT_FILE.unlink)
        call_command(COMMAND, "dump", state)
        with open(DEFAULT_FILE) as file:
            data = json.load(file)
        assert isinstance(data, dict)
        assert data.get(state) is not None

    @pytest.mark.usefixtures("make_dump")
    def test_load(self, capsys):
        call_command(COMMAND, "load", "-v", 0)
        stdout, _ = capsys.readouterr()
        assert "successfully applied" in stdout

    @pytest.mark.parametrize("filename", [DEFAULT_FILENAME, "custom_f1l3n4m3.json"])
    def test_load_files(self, request, capsys, filename):
        request.addfinalizer(Path(filename).unlink)
        call_command(COMMAND, "dump", "-f", filename)
        call_command(COMMAND, "load", "-f", filename)
        stdout, _ = capsys.readouterr()
        assert "successfully applied" in stdout

    @pytest.mark.parametrize("state", [DEFAULT_STATE, "custom_state"])
    def test_load_states(self, request, capsys, state):
        request.addfinalizer(DEFAULT_FILE.unlink)
        call_command(COMMAND, "dump", state)
        call_command(COMMAND, "load", state)
        stdout, _ = capsys.readouterr()
        assert "successfully applied" in stdout

    def test_migration_is_last_applied(self, cmd_data):
        migrations = MigrationRecorder(connection).applied_migrations()
        for app, migration in cmd_data.items():
            last_migration = sorted(filter(lambda x: x[0] == app, migrations))[-1][1]
            assert migration == last_migration
