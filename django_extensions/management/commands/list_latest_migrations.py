from django.core.management.commands import showmigrations
from django.db import DEFAULT_DB_ALIAS
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder


class Command(showmigrations.Command):
    help = "Shows the most recently applied migration for each app."

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            nargs="*",
            help="App labels of applications to limit the output to.",
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to synchronize. Defaults to the "default" database.',
        )

    def handle(self, *args, **options):
        options["format"] = "plan"
        super().handle(*args, **options)

    def show_plan(self, connection, app_names=None):
        """
        Show the most recently applied migration for each app.
        """
        migrations = self.get_latest_migrations(connection, app_names)

        # Print all
        for m in migrations:
            self.stdout.write(f"{m[0]} {m[1]}")

    @staticmethod
    def get_latest_migrations(connection, app_names=None):
        """
        Get the most recently applied migration for each app.
        """

        # Get app names
        loader = MigrationLoader(connection)

        if not app_names:
            app_names = sorted(loader.migrated_apps)
        else:
            app_names = [name for name in app_names if name in loader.migrated_apps]

        # Get Migration model
        Migration = MigrationRecorder(connection).Migration

        # Get latest migration for each app
        migrations = []
        for app_name in app_names:
            app_migrations = Migration.objects.filter(app=app_name)

            if app_migrations.count() > 0:
                migration_name = app_migrations.latest("applied").name
            else:
                migration_name = "zero"

            migrations.append((app_name, migration_name))

        return migrations
