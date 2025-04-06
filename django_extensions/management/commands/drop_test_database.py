# -*- coding: utf-8 -*-
import importlib.util
from itertools import count
import os
import logging
import warnings

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.db.backends.base.creation import TEST_DATABASE_PREFIX

from django_extensions.settings import SQLITE_ENGINES, POSTGRESQL_ENGINES, MYSQL_ENGINES
from django_extensions.management.mysql import parse_mysql_cnf
from django_extensions.management.utils import signalcommand
from django_extensions.utils.deprecation import RemovedInNextVersionWarning


class Command(BaseCommand):
    help = "Drops test database for this project."

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
            "-U",
            "--user",
            action="store",
            dest="user",
            default=None,
            help="Use another user for the database then defined in settings.py",
        )
        parser.add_argument(
            "-P",
            "--password",
            action="store",
            dest="password",
            default=None,
            help="Use another password for the database then defined in settings.py",
        )
        parser.add_argument(
            "-D",
            "--dbname",
            action="store",
            dest="dbname",
            default=None,
            help="Use another database name then defined in settings.py",
        )
        parser.add_argument(
            "-R",
            "--router",
            action="store",
            dest="router",
            default=DEFAULT_DB_ALIAS,
            help="Use this router-database other then defined in settings.py",
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help=(
                "Nominates a database to run command for. "
                'Defaults to the "%s" database.'
            )
            % DEFAULT_DB_ALIAS,
        )

    @signalcommand
    def handle(self, *args, **options):
        """Drop test database for this project."""
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

        user = password = database_name = database_host = database_port = ""
        if engine == "mysql":
            (user, password, database_name, database_host, database_port) = (
                parse_mysql_cnf(dbinfo)
            )

        user = options["user"] or dbinfo.get("USER") or user
        password = options["password"] or dbinfo.get("PASSWORD") or password

        try:
            database_name = dbinfo["TEST"]["NAME"]
        except KeyError:
            database_name = None

        if database_name is None:
            database_name = TEST_DATABASE_PREFIX + (
                options["dbname"] or dbinfo.get("NAME")
            )

        if database_name is None or database_name == "":
            raise CommandError(
                "You need to specify DATABASE_NAME in your Django settings file."
            )

        database_host = dbinfo.get("HOST") or database_host
        database_port = dbinfo.get("PORT") or database_port

        verbosity = options["verbosity"]
        if options["interactive"]:
            confirm = input(
                """
You have requested to drop all test databases.
This will IRREVERSIBLY DESTROY
ALL data in the database "{db_name}"
and all cloned test databases generated via
the "--parallel" flag (these are sequentially
named "{db_name}_1", "{db_name}_2", etc.).
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """.format(db_name=database_name)
            )
        else:
            confirm = "yes"

        if confirm != "yes":
            print("Reset cancelled.")
            return

        def get_database_names(formatter):
            """
            Return a generator of all possible test database names.
            e.g., 'test_foo', 'test_foo_1', test_foo_2', etc.

            formatter: func returning a clone db name given the primary db name
            and the clone's number, e.g., 'test_foo_1' for mysql/postgres, and
            'test_foo_1..sqlite3' for sqlite (re: double dots, see comments).
            """
            yield database_name
            yield from (formatter(database_name, n) for n in count(1))

        if engine in SQLITE_ENGINES:
            # By default all sqlite test databases are created in memory.
            # There will only be database files to delete if the developer has
            # specified a test database name, which forces files to be written
            # to disk.

            logging.info("Unlinking %s databases" % engine)

            def format_filename(name, number):
                filename, ext = os.path.splitext(name)
                # Since splitext() includes the dot in 'ext', the inclusion of
                # the dot in the format string below is incorrect and creates a
                # double dot. Django makes this mistake, so it must be
                # replicated here. If fixed in Django, this code should be
                # updated accordingly.
                # Reference: https://code.djangoproject.com/ticket/32582
                return "{}_{}.{}".format(filename, number, ext)

            try:
                for db_name in get_database_names(format_filename):
                    if not os.path.isfile(db_name):
                        break
                    logging.info('Unlinking database named "%s"' % db_name)
                    os.unlink(db_name)
            except OSError:
                return

        elif engine in MYSQL_ENGINES:
            import MySQLdb as Database

            kwargs = {
                "user": user,
                "passwd": password,
            }
            if database_host.startswith("/"):
                kwargs["unix_socket"] = database_host
            else:
                kwargs["host"] = database_host

            if database_port:
                kwargs["port"] = int(database_port)

            connection = Database.connect(**kwargs)
            cursor = connection.cursor()

            for db_name in get_database_names("{}_{}".format):
                exists_query = (
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                    "WHERE SCHEMA_NAME='%s';" % db_name
                )
                row_count = cursor.execute(exists_query)
                if row_count < 1:
                    break
                drop_query = "DROP DATABASE IF EXISTS `%s`" % db_name
                logging.info('Executing: "' + drop_query + '"')
                cursor.execute(drop_query)

        elif engine in POSTGRESQL_ENGINES:
            has_psycopg3 = importlib.util.find_spec("psycopg")
            if has_psycopg3:
                import psycopg as Database  # NOQA
            else:
                import psycopg2 as Database  # NOQA

            conn_params = {"dbname": "template1"}
            if user:
                conn_params["user"] = user
            if password:
                conn_params["password"] = password
            if database_host:
                conn_params["host"] = database_host
            if database_port:
                conn_params["port"] = database_port

            connection = Database.connect(**conn_params)
            if has_psycopg3:
                connection.autocommit = True
            else:
                connection.set_isolation_level(0)  # autocommit false
            cursor = connection.cursor()

            for db_name in get_database_names("{}_{}".format):
                exists_query = (
                    "SELECT datname FROM pg_catalog.pg_database WHERE datname='%s';"
                    % db_name
                )
                try:
                    cursor.execute(exists_query)
                    # NOTE: Unlike MySQLdb, the psycopg2 cursor does not return the row
                    # count however both cursors provide it as a property
                    if cursor.rowcount < 1:
                        break
                    drop_query = 'DROP DATABASE IF EXISTS "%s";' % db_name
                    logging.info('Executing: "' + drop_query + '"')
                    cursor.execute(drop_query)
                except Database.ProgrammingError as e:
                    logging.exception("Error: %s" % str(e))
                    return
        else:
            raise CommandError("Unknown database engine %s" % engine)

        if verbosity >= 2 or options["interactive"]:
            print("Reset successful.")
