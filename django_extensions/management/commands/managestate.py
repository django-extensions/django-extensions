# -*- coding: utf-8 -*-
import json
from operator import itemgetter
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone

from django_extensions.management.utils import signalcommand

DEFAULT_FILENAME = "managestate.json"
DEFAULT_STATE = "default"


class Command(BaseCommand):
    help = "Manage database state in the convenient way."
    _applied_migrations = None
    migrate_args: dict
    migrate_options: dict
    filename: str
    verbosity: int
    database: str
    conn: BaseDatabaseWrapper

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=("dump", "load"),
            help="An action to do. "
            "Dump action saves applied migrations to a file. "
            "Load action applies migrations specified in a file.",
        )
        parser.add_argument(
            "state",
            nargs="?",
            default=DEFAULT_STATE,
            help="A name of a state. Usually a name of a git branch."
            f'Defaults to "{DEFAULT_STATE}"',
        )
        parser.add_argument(
            "-d",
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates a database to synchronize. "
            f'Defaults to the "{DEFAULT_DB_ALIAS}" database.',
        )
        parser.add_argument(
            "-f",
            "--filename",
            default=DEFAULT_FILENAME,
            help=f'A file to write to. Defaults to "{DEFAULT_FILENAME}"',
        )

        # migrate command arguments
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help='The argument for "migrate" command. '
            "Tells Django to NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--fake",
            action="store_true",
            help='The argument for "migrate" command. '
            "Mark migrations as run without actually running them.",
        )
        parser.add_argument(
            "--fake-initial",
            action="store_true",
            help='The argument for "migrate" command. '
            "Detect if tables already exist and fake-apply initial migrations if so. "
            "Make sure that the current database schema matches your initial migration "
            "before using this flag. "
            "Django will only check for an existing table name.",
        )
        parser.add_argument(
            "--plan",
            action="store_true",
            help='The argument for "migrate" command. '
            "Shows a list of the migration actions that will be performed.",
        )
        parser.add_argument(
            "--run-syncdb",
            action="store_true",
            help='The argument for "migrate" command. '
            "Creates tables for apps without migrations.",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            dest="check_unapplied",
            help='The argument for "migrate" command. '
            "Exits with a non-zero status if unapplied migrations exist.",
        )

    @signalcommand
    def handle(self, action, database, filename, state, *args, **options):
        self.migrate_args = args
        self.migrate_options = options
        self.verbosity = options["verbosity"]
        self.conn = connections[database]
        self.database = database
        self.filename = filename
        getattr(self, action)(state)

    def dump(self, state: str):
        """Save applied migrations to a file."""
        migrated_apps = self.get_migrated_apps()
        migrated_apps.update(self.get_applied_migrations())
        self.write({state: migrated_apps})
        self.stdout.write(
            self.style.SUCCESS(
                f'Migrations for state "{state}" have been successfully '
                f"saved to {self.filename}."
            )
        )

    def load(self, state: str):
        """Apply migrations from a file."""
        migrations = self.read().get(state)
        if migrations is None:
            raise CommandError(f"No such state saved: {state}")

        kwargs = {
            **self.migrate_options,
            "database": self.database,
            "verbosity": self.verbosity - 1 if self.verbosity > 1 else 0,
        }

        for app, migration in migrations.items():
            if self.is_applied(app, migration):
                continue

            if self.verbosity > 1:
                self.stdout.write(
                    self.style.WARNING(f'Applying migrations for "{app}"')
                )
            args = (app, migration, *self.migrate_args)
            call_command("migrate", *args, **kwargs)

        self.stdout.write(
            self.style.SUCCESS(
                f'Migrations for "{state}" have been successfully applied.'
            )
        )

    def get_migrated_apps(self) -> dict:
        """Installed apps having migrations."""
        apps = MigrationLoader(self.conn).migrated_apps
        migrated_apps = dict.fromkeys(apps, "zero")
        if self.verbosity > 1:
            self.stdout.write(
                "Apps having migrations: " + ", ".join(sorted(migrated_apps))
            )
        return migrated_apps

    def get_applied_migrations(self) -> dict:
        """Installed apps with last applied migrations."""
        if self._applied_migrations:
            return self._applied_migrations

        migrations = MigrationRecorder(self.conn).applied_migrations()
        last_applied = sorted(migrations.keys(), key=itemgetter(1))

        self._applied_migrations = dict(last_applied)
        return self._applied_migrations

    def is_applied(self, app: str, migration: str) -> bool:
        """Check whether a migration for an app is applied or not."""
        applied = self.get_applied_migrations().get(app)
        if applied == migration:
            if self.verbosity > 1:
                self.stdout.write(
                    self.style.WARNING(f'Migrations for "{app}" are already applied.')
                )
            return True
        return False

    def read(self) -> dict:
        """Get saved state from the file."""
        path = Path(self.filename)
        if not path.exists() or not path.is_file():
            raise CommandError(f"No such file: {self.filename}")

        with open(self.filename) as file:
            return json.load(file)

    def write(self, data: dict):
        """Write new data to the file using existent one."""
        try:
            saved = self.read()
        except CommandError:
            saved = {}

        saved.update(data, updated_at=str(timezone.now()))
        with open(self.filename, "w") as file:
            json.dump(saved, file, indent=2, sort_keys=True)
