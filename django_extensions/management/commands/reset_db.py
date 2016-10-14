# -*- coding: utf-8 -*-
"""
originally from http://www.djangosnippets.org/snippets/828/ by dnordberg
"""
import logging

import django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from six.moves import input

from django_extensions.management.mysql import parse_mysql_cnf
from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Resets the database for this project."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--noinput', action='store_false',
            dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.')
        parser.add_argument(
            '--no-utf8', action='store_true', dest='no_utf8_support',
            default=False,
            help='Tells Django to not create a UTF-8 charset database')
        parser.add_argument(
            '-U', '--user', action='store', dest='user', default=None,
            help='Use another user for the database then defined in '
            'settings.py')
        parser.add_argument(
            '-O', '--owner', action='store', dest='owner', default=None,
            help='Use another owner for creating the database then the '
            'user defined in settings or via --user')
        parser.add_argument(
            '-P', '--password', action='store', dest='password', default=None,
            help='Use another password for the database then defined in '
            'settings.py')
        parser.add_argument(
            '-D', '--dbname', action='store', dest='dbname', default=None,
            help='Use another database name then defined in settings.py')
        parser.add_argument(
            '-R', '--router', action='store', dest='router', default='default',
            help='Use this router-database other then defined in settings.py')
        parser.add_argument(
            '-c', '--close-sessions', action='store_true', dest='close_sessions', default=False,
            help='Close database connections before dropping database (PostgreSQL only)')

    @signalcommand
    def handle(self, *args, **options):
        """
        Resets the database for this project.

        Note: Transaction wrappers are in reverse as a work around for
        autocommit, anybody know how to do this the right way?
        """

        if args:
            raise CommandError("reset_db takes no arguments")

        router = options.get('router')
        dbinfo = settings.DATABASES.get(router)
        if dbinfo is None:
            raise CommandError("Unknown database router %s" % router)

        engine = dbinfo.get('ENGINE').split('.')[-1]

        user = password = database_name = database_host = database_port = ''
        if engine == 'mysql':
            (user, password, database_name, database_host, database_port) = parse_mysql_cnf(dbinfo)

        user = options.get('user') or dbinfo.get('USER') or user
        password = options.get('password') or dbinfo.get('PASSWORD') or password
        owner = options.get('owner') or user

        database_name = options.get('dbname') or dbinfo.get('NAME') or database_name
        if database_name == '':
            raise CommandError("You need to specify DATABASE_NAME in your Django settings file.")

        database_host = dbinfo.get('HOST') or database_host
        database_port = dbinfo.get('PORT') or database_port

        verbosity = int(options.get('verbosity', 1))
        if options.get('interactive'):
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

        if engine in ('sqlite3', 'spatialite'):
            import os
            try:
                logging.info("Unlinking %s database" % engine)
                os.unlink(database_name)
            except OSError:
                pass

        elif engine in ('mysql',):
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
            utf8_support = options.get('no_utf8_support', False) and '' or 'CHARACTER SET utf8'
            create_query = 'CREATE DATABASE `%s` %s' % (database_name, utf8_support)
            logging.info('Executing... "' + drop_query + '"')
            connection.query(drop_query)
            logging.info('Executing... "' + create_query + '"')
            connection.query(create_query)

        elif engine in ('postgresql', 'postgresql_psycopg2', 'postgis'):
            if engine == 'postgresql' and django.VERSION < (1, 9):
                import psycopg as Database  # NOQA
            elif engine in ('postgresql', 'postgresql_psycopg2', 'postgis'):
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

            if options.get('close_sessions'):
                close_sessions_query = """
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '%s';
                """ % database_name
                logging.info('Executing... "' + close_sessions_query.strip() + '"')
                try:
                    cursor.execute(close_sessions_query)
                except Database.ProgrammingError as e:
                    logging.exception("Error: %s" % str(e))

            drop_query = "DROP DATABASE \"%s\";" % database_name
            logging.info('Executing... "' + drop_query + '"')
            try:
                cursor.execute(drop_query)
            except Database.ProgrammingError as e:
                logging.exception("Error: %s" % str(e))

            create_query = "CREATE DATABASE \"%s\"" % database_name
            if owner:
                create_query += " WITH OWNER = \"%s\" " % owner
            create_query += " ENCODING = 'UTF8'"

            if engine == 'postgis' and django.VERSION < (1, 9):
                # For PostGIS 1.5, fetch template name if it exists
                from django.contrib.gis.db.backends.postgis.base import DatabaseWrapper
                postgis_template = DatabaseWrapper(dbinfo).template_postgis
                if postgis_template is not None:
                    create_query += ' TEMPLATE = %s' % postgis_template

            if settings.DEFAULT_TABLESPACE:
                create_query += ' TABLESPACE = %s;' % settings.DEFAULT_TABLESPACE
            else:
                create_query += ';'

            logging.info('Executing... "' + create_query + '"')
            cursor.execute(create_query)

        else:
            raise CommandError("Unknown database engine %s" % engine)

        if verbosity >= 2 or options.get('interactive'):
            print("Reset successful.")
