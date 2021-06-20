import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from django.core.management import CommandError, call_command
from django_extensions.management.commands.managestate import DEFAULT_FILENAME, DEFAULT_STATE

pytestmark = [pytest.mark.django_db]

COMMAND = 'managestate'
DEFAULT_FILE = Path(DEFAULT_FILENAME)


@pytest.fixture
def make_dump(request):
    request.addfinalizer(DEFAULT_FILE.unlink)
    return call_command(COMMAND, 'dump', '-v', 0)


class TestManageStateExceptions:
    """Tests for managestate management command exceptions."""

    def test_bad_action(self):
        with pytest.raises(CommandError):
            call_command(COMMAND, 'bad_action')

    def test_no_such_file(self):
        with pytest.raises(CommandError):
            call_command(COMMAND, 'load', '-f', 'non_existent_file')

    def test_not_a_file(self):
        with pytest.raises(CommandError), TemporaryDirectory() as tmp_dir:
            call_command(COMMAND, 'load', '-f', tmp_dir)

    def test_no_such_state(self, make_dump):
        with pytest.raises(CommandError):
            call_command(COMMAND, 'load', 'non_existent_state')


class TestManageState:
    """Tests managestate management command"""

    def test_dump(self, request, capsys):
        request.addfinalizer(DEFAULT_FILE.unlink)
        call_command(COMMAND, 'dump', '-v', 0)
        stdout, _ = capsys.readouterr()
        assert DEFAULT_FILE.exists()
        assert 'successfully saved' in stdout

    @pytest.mark.parametrize('filename', [DEFAULT_FILENAME, 'custom_f1l3n4m3.json'])
    def test_dump_files(self, request, capsys, filename):
        path = Path(filename)
        request.addfinalizer(path.unlink)
        call_command(COMMAND, 'dump', '-f', filename)
        assert path.exists()

    @pytest.mark.parametrize('state', [DEFAULT_STATE, 'custom_state'])
    def test_dump_states(self, request, capsys, state):
        request.addfinalizer(DEFAULT_FILE.unlink)
        call_command(COMMAND, 'dump', state)
        with open(DEFAULT_FILE) as file:
            data = json.load(file)
        assert data.get(state) is not None

    def test_load(self, make_dump, capsys):
        call_command(COMMAND, 'load', '-v', 0)
        stdout, _ = capsys.readouterr()
        assert 'successfully applied' in stdout
