# -*- coding: utf-8 -*-
"""
Recreates the public schema for current database (PostgreSQL only).
Useful for Docker environments where you need to reset database
schema while there are active connections.
"""

import warnings

from django.core.management import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.db import connections
from django.conf import settings

from django_extensions.settings import POSTGRESQL_ENGINES
from django_extensions.utils.deprecation import RemovedInNextVersionWarning


class Command(BaseCommand):
    """`reset_schema` command implementation."""

    help = "Recreates the public schema for this project."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            default=True,
            help="Tells Django to NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "-R",
            "--router",
            action="store",
            dest="router",
            default=DEFAULT_DB_ALIAS,
            help="Use this router-database instead of the one defined in settings.py",
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to run command for. Defaults to the "%s".'
            % DEFAULT_DB_ALIAS,
        )
        parser.add_argument(
            "-S",
            "--schema",
            action="store",
            dest="schema",
            default="public",
            help='Drop this schema instead of "public"',
        )

    def handle(self, *args, **options):
        database = options["database"]
        if options["router"] != DEFAULT_DB_ALIAS:
            warnings.warn(
                "--router is deprecated. You should use --database.",
                RemovedInNextVersionWarning,
                stacklevel=2,
            )
            database = options["router"]

        dbinfo = settings.DATABASES.get(database)
        if dbinfo is None:
            raise CommandError("Unknown database %s" % database)

        engine = dbinfo.get("ENGINE")
        if engine not in POSTGRESQL_ENGINES:
            raise CommandError(
                "This command can be used only with PostgreSQL databases."
            )

        database_name = dbinfo["NAME"]

        schema = options["schema"]

        if options["interactive"]:
            confirm = input(
                """
You have requested a database schema reset.
This will IRREVERSIBLY DESTROY ALL data
in the "{}" schema of database "{}".
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """.format(schema, database_name)
            )
        else:
            confirm = "yes"

        if confirm != "yes":
            print("Reset cancelled.")
            return

        with connections[database].cursor() as cursor:
            cursor.execute("DROP SCHEMA {} CASCADE".format(schema))
            cursor.execute("CREATE SCHEMA {}".format(schema))
