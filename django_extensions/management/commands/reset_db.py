# -*- coding: utf-8 -*-
"""
reset_db command

originally from http://www.djangosnippets.org/snippets/828/ by dnordberg
"""
import os
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from six.moves import input

from django_extensions.settings import SQLITE_ENGINES, POSTGRESQL_ENGINES, MYSQL_ENGINES
from django_extensions.management.mysql import parse_mysql_cnf
from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Resets the database for this project."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--noinput', action='store_false',
            dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'
        )
        parser.add_argument(
            '--no-utf8', action='store_true', dest='no_utf8_support',
            default=False,
            help='Tells Django to not create a UTF-8 charset database'
        )
        parser.add_argument(
            '-U', '--user', action='store', dest='user', default=None,
            help='Use another user for the database than defined in settings.py'
        )
        parser.add_argument(
            '-O', '--owner', action='store', dest='owner', default=None,
            help='Use another owner for creating the database than the user defined in settings or via --user'
        )
        parser.add_argument(
            '-P', '--password', action='store', dest='password', default=None,
            help='Use another password for the database than defined in settings.py'
        )
        parser.add_argument(
            '-D', '--dbname', action='store', dest='dbname', default=None,
            help='Use another database name than defined in settings.py'
        )
        parser.add_argument(
            '-R', '--router', action='store', dest='router', default='default',
            help='Use this router-database other than defined in settings.py'
        )
        parser.add_argument(
            '-c', '--close-sessions', action='store_true', dest='close_sessions', default=False,
            help='Close database connections before dropping database (PostgreSQL only)'
        )

    @signalcommand
    def handle(self, *args, **options):
        """
        Reset the database for this project.

        Note: Transaction wrappers are in reverse as a work around for
        autocommit, anybody know how to do this the right way?
        """
        router = options['router']
        dbinfo = settings.DATABASES.get(router)
        if dbinfo is None:
            raise CommandError("Unknown database router %s" % router)

        engine = dbinfo.get('ENGINE')

        user = password = database_name = database_host = database_port = ''
        if engine == 'mysql':
            (user, password, database_name, database_host, database_port) = parse_mysql_cnf(dbinfo)

        user = options['user'] or dbinfo.get('USER') or user
        password = options['password'] or dbinfo.get('PASSWORD') or password
        owner = options['owner'] or user

        database_name = options['dbname'] or dbinfo.get('NAME') or database_name
        if database_name == '':
            raise CommandError("You need to specify DATABASE_NAME in your Django settings file.")

        database_host = dbinfo.get('HOST') or database_host
        database_port = dbinfo.get('PORT') or database_port

        verbosity = options["verbosity"]
        if options['interactive']:
            confirm = input("""
You have requested a database reset.
This will IRREVERSIBLY DESTROY
ALL data in the database "%s".
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """ % (database_name,))
        else:
            confirm = 'yes'

        if confirm != 'yes':
            print("Reset cancelled.")
            return

        if engine in SQLITE_ENGINES:
            try:
                logging.info("Unlinking %s database", engine)
                os.unlink(database_name)
            except OSError:
                pass

        elif engine in MYSQL_ENGINES:
            import MySQLdb as Database
            kwargs = {
                'user': user,
                'passwd': password,
            }
            if database_host.startswith('/'):
                kwargs['unix_socket'] = database_host
            else:
                kwargs['host'] = database_host

            if database_port:
                kwargs['port'] = int(database_port)

            connection = Database.connect(**kwargs)
            drop_query = 'DROP DATABASE IF EXISTS `%s`' % database_name
            utf8_support = '' if options['no_utf8_support'] else 'CHARACTER SET utf8'
            create_query = 'CREATE DATABASE `%s` %s' % (database_name, utf8_support)
            logging.info('Executing... "%s"', drop_query)
            connection.query(drop_query)
            logging.info('Executing... "%s"', create_query)
            connection.query(create_query.strip())

        elif engine in POSTGRESQL_ENGINES:
            import psycopg2 as Database  # NOQA

            conn_params = {'database': 'template1'}
            if user:
                conn_params['user'] = user
            if password:
                conn_params['password'] = password
            if database_host:
                conn_params['host'] = database_host
            if database_port:
                conn_params['port'] = database_port

            connection = Database.connect(**conn_params)
            connection.set_isolation_level(0)  # autocommit false
            cursor = connection.cursor()

            if options['close_sessions']:
                close_sessions_query = """
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '%s';
                """ % database_name
                logging.info('Executing... "%s"', close_sessions_query.strip())
                try:
                    cursor.execute(close_sessions_query)
                except Database.ProgrammingError as e:
                    logging.exception("Error: %s", str(e))

            drop_query = "DROP DATABASE \"%s\";" % database_name
            logging.info('Executing... "%s"', drop_query)
            try:
                cursor.execute(drop_query)
            except Database.ProgrammingError as e:
                logging.exception("Error: %s", str(e))

            create_query = "CREATE DATABASE \"%s\"" % database_name
            if owner:
                create_query += " WITH OWNER = \"%s\" " % owner
            create_query += " ENCODING = 'UTF8'"

            if settings.DEFAULT_TABLESPACE:
                create_query += ' TABLESPACE = %s;' % settings.DEFAULT_TABLESPACE
            else:
                create_query += ';'

            logging.info('Executing... "%s"', create_query)
            cursor.execute(create_query)

        else:
            raise CommandError("Unknown database engine %s" % engine)

        if verbosity >= 2 or options['interactive']:
            print("Reset successful.")
