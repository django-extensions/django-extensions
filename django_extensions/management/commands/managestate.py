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
    help = 'Manage database state in the convenient way.'
    migrate_args = migrate_options = None
    database = filename = None

    def add_arguments(self, parser):
        parser.add_argument(
            'action', choices=('dump', 'load'),
            help='An action to do. '
                 'Dump action saves applied migrations to a file. '
                 'Load action applies migrations specified in a file.',
        )
        parser.add_argument(
            '-d', '--database', default=DEFAULT_DB_ALIAS,
            help=f'Nominates a database to synchronize. Defaults to the "{DEFAULT_DB_ALIAS}" database.',
        )
        parser.add_argument(
            '-f', '--filename', default=DEFAULT_FILENAME,
            help=f'A file to write to. Defaults to "{DEFAULT_FILENAME}"',
        )
        parser.add_argument(
            '-s', '--state', default=DEFAULT_STATE,
            help=f'A name of a state. Usually a name of a git branch. Defaults to "{DEFAULT_STATE}"',
        )

        # migrate command arguments
        parser.add_argument(
            '--noinput', '--no-input', action='store_false', dest='interactive',
            help='The argument for "migrate" command. '
                 'Tells Django to NOT prompt the user for input of any kind.',
        )
        parser.add_argument(
            '--fake', action='store_true',
            help='The argument for "migrate" command. '
                 'Mark migrations as run without actually running them.',
        )
        parser.add_argument(
            '--fake-initial', action='store_true',
            help='The argument for "migrate" command. '
                 'Detect if tables already exist and fake-apply initial migrations if so. Make sure '
                 'that the current database schema matches your initial migration before using this '
                 'flag. Django will only check for an existing table name.',
        )
        parser.add_argument(
            '--plan', action='store_true',
            help='The argument for "migrate" command. '
                 'Shows a list of the migration actions that will be performed.',
        )
        parser.add_argument(
            '--run-syncdb', action='store_true',
            help='The argument for "migrate" command. '
                 'Creates tables for apps without migrations.',
        )
        parser.add_argument(
            '--check', action='store_true', dest='check_unapplied',
            help='The argument for "migrate" command. '
                 'Exits with a non-zero status if unapplied migrations exist.',
        )

    def handle(self, action, database, filename, state, *args, **options):
        self.migrate_args = args
        self.migrate_options = options
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
        if migrations is None:
            raise CommandError(f'No such state saved: {state}')

        for app, migration in migrations.items():
            args = (app, migration, *self.migrate_args)
            kwargs = {**self.migrate_options, 'database': self.database}
            call_command('migrate', *args, **kwargs)

    def read(self) -> dict:
        """Get saved state from the file."""
        path = Path(self.filename)
        if not path.exists() and not path.is_file():
            raise CommandError(f'No such file: {self.filename}')

        with open(self.filename) as file:
            data = json.load(file)

        data.pop('updated_at')
        return data

    def write(self, data: dict):
        """Write new data to the file using existent one."""
        try:
            saved = self.read()
        except CommandError:
            saved = {}

        saved.update(data, updated_at=str(timezone.now()))
        with open(self.filename, 'w') as file:
            json.dump(saved, file, indent=2, sort_keys=True)
