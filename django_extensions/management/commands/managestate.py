import json
from logging import getLogger
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone

logger = getLogger(__name__)

DEFAULT_FILENAME = 'managestate.json'
DEFAULT_STATE = 'default'


class Command(BaseCommand):
    help = 'Manage database state depending on branch.'
    conn = file = None

    def add_arguments(self, parser):
        parser.add_argument(
            'action', choices=('dump', 'load'),
            help='An action to do. Dump action saves result to the file. Load action vice versa.',
        )
        parser.add_argument(
            '-d', '--database', default=DEFAULT_DB_ALIAS,
            help='An alias of a database to use.',
        )
        parser.add_argument(
            '-f', '--filename', default=DEFAULT_FILENAME,
            help=f'A file to write to. Defaults to "{DEFAULT_FILENAME}"',
        )
        parser.add_argument(
            '-s', '--state', default=DEFAULT_STATE,
            help='A name of a state. May be a name of a git branch.',
        )

    def handle(self, action, database, filename, state, *args, **options):
        self.conn = connections[database]
        self.file = filename
        getattr(self, action)(state)

    def dump(self, state: str):
        """Save applied migrations to the file"""
        applied_migrations = MigrationRecorder(self.conn).applied_migrations()
        data = {state: dict(applied_migrations.keys())}
        self.write(data)

    def load(self, state: str):
        """Apply migrations from the file"""
        self.read()

    def read(self) -> dict:
        """Get saved state from the file."""
        path = Path(self.file)
        if not path.exists() and not path.is_file():
            raise CommandError(f'No such file: {self.file}')

        with open(self.file) as file:
            data = json.load(file)

        data.pop('saved_at')
        return data

    def write(self, data: dict):
        """Write new data to the file using existent one."""
        try:
            saved = self.read()
        except CommandError:
            saved = {}

        saved.update(data, saved_at=str(timezone.now()))
        with open(self.file, 'w') as file:
            json.dump(saved, file, indent=2, sort_keys=True)
