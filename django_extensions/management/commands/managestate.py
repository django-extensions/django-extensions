import json
from logging import getLogger
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone

logger = getLogger(__name__)

DEFAULT_FILENAME = 'managestate.json'
DEFAULT_STATE = 'default'


class Command(BaseCommand):
    help = 'Manage database state depending on branch.'
    common_args = common_options = None
    database = filename = None

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
        self.common_args = args
        self.common_options = options
        self.database = database
        self.filename = filename
        getattr(self, action)(state)

    def dump(self, state: str):
        """Save applied migrations to the file"""
        conn = connections[self.database]
        applied_migrations = MigrationRecorder(conn).applied_migrations()
        data = {state: dict(applied_migrations.keys())}
        self.write(data)

    def load(self, state: str):
        """Apply migrations from the file"""
        migrations = self.read().get(state)
        if not migrations:
            raise CommandError(f'No such state saved: {state}')

        for app, migration in migrations.items():
            args = (app, migration, *self.common_args)
            kwargs = {
                **self.common_options,
                'database': self.database,
                'verbosity': 0,
            }
            call_command('migrate', *args, **kwargs)

    def read(self) -> dict:
        """Get saved state from the file."""
        path = Path(self.filename)
        if not path.exists() and not path.is_file():
            raise CommandError(f'No such file: {self.filename}')

        with open(self.filename) as file:
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
        with open(self.filename, 'w') as file:
            json.dump(saved, file, indent=2, sort_keys=True)
