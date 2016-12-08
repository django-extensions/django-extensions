# -*- coding: utf-8 -*-
import os
import inspect
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.loader import AmbiguityError, MigrationLoader
from django.utils import six

REPLACES_REGEX = re.compile(r'\s+replaces\s*=\s*\[[^\]]+\]\s*')
PYC = '.pyc'


def py_from_pyc(pyc_fn):
    return pyc_fn[:-len(PYC)] + '.py'


class Command(BaseCommand):

    help = "Deletes left over migrations that have been replaced by a "
    "squashed migration and converts squashed migration into a normal "
    "migration. Modifies your source tree! Use with care!"

    def add_arguments(self, parser):
        parser.add_argument(
            'app_label',
            help='App label of the application to delete replaced migrations from.',
        )
        parser.add_argument(
            'squashed_migration_name', default=None, nargs='?',
            help='The squashed migration to replace. '
                 'If not specified defaults to the first found.'
        )
        parser.add_argument(
            '--noinput', '--no-input', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.',
        )
        parser.add_argument(
            '--dry-run', action='store_true', default=False,
            help='Do not actually delete or change any files')

    def handle(self, **options):
        self.verbosity = options['verbosity']
        self.interactive = options['interactive']
        self.dry_run = options['dry_run']
        app_label = options['app_label']
        squashed_migration_name = options['squashed_migration_name']

        # Load the current graph state, check the app and migration they asked for exists
        loader = MigrationLoader(connections[DEFAULT_DB_ALIAS])
        if app_label not in loader.migrated_apps:
            raise CommandError(
                "App '%s' does not have migrations (so delete_squashed_migrations on "
                "it makes no sense)" % app_label
            )

        squashed_migration = None
        if squashed_migration_name:
            squashed_migration = self.find_migration(loader, app_label, squashed_migration_name)
            if not squashed_migration.replaces:
                raise CommandError(
                    "The migration %s %s is not a squashed migration." %
                    (squashed_migration.app_label, squashed_migration.name)
                )
        else:
            leaf_nodes = loader.graph.leaf_nodes(app=app_label)
            migration = loader.get_migration(*leaf_nodes[0])
            previous_migrations = [
                loader.get_migration(al, mn)
                for al, mn in loader.graph.forwards_plan((migration.app_label, migration.name))
                if al == migration.app_label
            ]
            migrations = previous_migrations + [migration]
            for migration in migrations:
                if migration.replaces:
                    squashed_migration = migration
                    break

            if not squashed_migration:
                raise CommandError(
                    "Cannot find a squashed migration in app '%s'." %
                    (app_label)
                )

        files_to_delete = []
        for al, mn in squashed_migration.replaces:
            try:
                migration = loader.disk_migrations[al, mn]
            except KeyError:
                if self.verbosity > 0:
                    self.stderr.write("Couldn't find migration file for %s %s\n"
                                      % (al, mn))
            else:
                pyc_file = inspect.getfile(migration.__class__)
                files_to_delete.append(pyc_file)
                if pyc_file.endswith(PYC):
                    py_file = py_from_pyc(pyc_file)
                    files_to_delete.append(py_file)

        # Tell them what we're doing and optionally ask if we should proceed
        if self.verbosity > 0 or self.interactive:
            self.stdout.write(self.style.MIGRATE_HEADING("Will delete the following files:"))
            for fn in files_to_delete:
                self.stdout.write(" - %s" % fn)

            if not self.confirm():
                return

        for fn in files_to_delete:
            try:
                if not self.dry_run:
                    os.remove(fn)
            except OSError:
                if self.verbosity > 0:
                    self.stderr.write("Couldn't delete %s\n" % (fn,))

        # Try and delete replaces only if it's all on one line
        squashed_migration_fn = inspect.getfile(squashed_migration.__class__)
        if squashed_migration_fn.endswith(PYC):
            squashed_migration_fn = py_from_pyc(squashed_migration_fn)
        with open(squashed_migration_fn) as fp:
            squashed_migration_lines = list(fp)

        delete_lines = []
        for i, line in enumerate(squashed_migration_lines):
            if REPLACES_REGEX.match(line):
                delete_lines.append(i)
                if i > 0 and squashed_migration_lines[i - 1].strip() == '':
                    delete_lines.insert(0, i - 1)
                break
        if not delete_lines:
            raise CommandError(
                ("Couldn't find 'replaces =' line in file %s. "
                 "Please finish cleaning up manually.") % (squashed_migration_fn,)
            )

        if self.verbosity > 0 or self.interactive:
            self.stdout.write(self.style.MIGRATE_HEADING(
                "Will delete line %s%s from file %s" %
                (delete_lines[0],
                 ' and ' + str(delete_lines[1]) if len(delete_lines) > 1 else "",
                 squashed_migration_fn)))

            if not self.confirm():
                return

        for line_num in sorted(delete_lines, reverse=True):
            del squashed_migration_lines[line_num]

        with open(squashed_migration_fn, 'w') as fp:
            if not self.dry_run:
                fp.write("".join(squashed_migration_lines))

    def confirm(self):
        if self.interactive:
            answer = None
            while not answer or answer not in "yn":
                answer = six.moves.input("Do you wish to proceed? [yN] ")
                if not answer:
                    answer = "n"
                    break
                else:
                    answer = answer[0].lower()
            return answer == "y"
        return True

    def find_migration(self, loader, app_label, name):
        try:
            return loader.get_migration_by_prefix(app_label, name)
        except AmbiguityError:
            raise CommandError(
                "More than one migration matches '%s' in app '%s'. Please be "
                "more specific." % (name, app_label)
            )
        except KeyError:
            raise CommandError(
                "Cannot find a migration matching '%s' from app '%s'." %
                (name, app_label)
            )
