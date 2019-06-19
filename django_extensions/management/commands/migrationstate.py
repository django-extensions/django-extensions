# -*- coding: utf-8 -*-

import json
import sys

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.loader import MigrationLoader
from django.utils import six


class Command(BaseCommand):
    help = (
        'Creates/Restores a dump of the migration targets currently reached.'
    )

    def add_arguments(self, parser):
        cmd = self

        # Custom argument parser to be used as parser_class for add_subparsers()
        class SubParser(CommandParser):
            def __init__(self, **kwargs):
                super(SubParser, self).__init__(cmd, **kwargs)

        def add_app_labels(parser):
            parser.add_argument(
                'app_label', nargs='*',
                help='App labels of applications to limit processing to.',
            )

        parser.add_argument(
            '--database', default=DEFAULT_DB_ALIAS,
            help='Nominates a database to synchronize. Defaults to the "default" database.',
        )

        subparsers = parser.add_subparsers(
            title='Action to perform',
            description='Use <sub-command> --help for more information.',
            parser_class=SubParser,
        )

        dumpparser = subparsers.add_parser(
            'dump',
            help='Dump the migration state currently reached.',
            description=(
                'Write a dump of the currently applied migration state '
                'in JSON format to stdout.'
            )
        )
        dumpparser.set_defaults(action='dump')
        add_app_labels(dumpparser)
        dumpparser.add_argument(
            '--indent', type=int,
            help='Specifies the indent level to use when pretty-printing output.',
        )

        loadparser = subparsers.add_parser(
            'load',
            help='Migrate to a previously dumped state.',
            description=(
                'Migrate to a previously dumped migration state, '
                'read from stdin.'
            )
        )
        loadparser.set_defaults(action='load')
        add_app_labels(loadparser)
        loadparser.add_argument(
            '--fake', action='store_true',
            help='Mark migrations as run without actually running them.',
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']

        # Get the database we're operating on
        self.database = options['database']
        connection = connections[self.database]

        if options['action'] == "dump":
            self.indent = options['indent']
            return self.dump_targets(connection, options['app_label'])
        else:
            self.fake = options['fake']
            return self.load_targets(connection, options['app_label'])

    def _validate_app_names(self, loader, app_names):
        has_bad_names = False
        for app_name in app_names:
            try:
                apps.get_app_config(app_name)
            except LookupError as err:
                self.stderr.write(str(err))
                has_bad_names = True
        if has_bad_names:
            raise CommandError('Invalid app name(s)')
            sys.exit(2)

    def dump_targets(self, connection, app_names=None):
        """
        Dump currently reached migration targets.
        """
        # Load migrations from disk/DB
        loader = MigrationLoader(connection)
        graph = loader.graph
        if app_names:
            self._validate_app_names(loader, app_names)
            targets = [key for key in graph.leaf_nodes() if key[0] in app_names]
        else:
            targets = graph.leaf_nodes()

        # Find latest applied migration for each target
        latest_applied = set()
        for target in targets:
            latest = None
            for migration in graph.forwards_plan(target):
                if migration not in loader.applied_migrations:
                    break
                if not app_names or migration[0] in app_names:
                    latest = migration
            if latest:
                latest_applied.add(latest)

        # Output
        serialized = json.dumps(
            sorted(list(latest_applied)),
            indent=self.indent,
        )
        self.stdout.write(serialized)

    def load_targets(self, connection, app_names=None):
        """
        Migrate up to the state represented by a dump.
        """
        # Load and validate data
        try:
            targets = json.load(sys.stdin)
            assert isinstance(targets, list), 'Need list of migration targets'
            for i, target in enumerate(targets):
                assert isinstance(target, list), 'Targets have to be lists'
                assert len(target) == 2, (
                    'Targets need to consist of 2 items - app name and '
                    'migration name'
                )
                target = tuple(target)
                assert isinstance(target[0], six.string_types) and \
                    isinstance(target[1], six.string_types), (
                        'App name and migration name need to be strings'
                )
                targets[i] = target
        except (AssertionError, ValueError) as err:
            raise CommandError('Malformed data: %s' % err)

        # Migrate to targets
        migrated = False
        for app_name, migration_name in targets:
            if app_names and app_name not in app_names:
                if self.verbosity >= 2:
                    self.stdout.write(
                        self.style.NOTICE('Skipping migration target: ') +
                        '%s from %s' % (migration_name, app_name)
                    )
                continue
            call_command(
                'migrate', app_name, migration_name,
                verbosity=self.verbosity, database=self.database,
                fake=self.fake,
            )
            migrated = True
        if not migrated and self.verbosity >= 1:
            self.stdout.write(self.style.NOTICE('No migrations to apply.'))
