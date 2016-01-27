# coding=utf-8
import logging

from django.conf import settings
from django.core.management.base import CommandError
from six.moves import input

from django_extensions.management.mysql import parse_mysql_cnf
from django_extensions.management.utils import signalcommand
from django_extensions.compat import CompatibilityBaseCommand as BaseCommand

try:
    from django.db.backends.base.creation import TEST_DATABASE_PREFIX
except ImportError:
    # Django < 1.7
    from django.db.backends.creation import TEST_DATABASE_PREFIX


class Command(BaseCommand):
    help = "Drops test database for this project."

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', action='store_false', dest='interactive',
            default=True, help='Tells Django to NOT prompt the user for '
            'input of any kind.')
        parser.add_argument(
            '-U', '--user', action='store', dest='user', default=None,
            help='Use another user for the database then defined in '
            'settings.py')
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

    @signalcommand
    def handle(self, *args, **options):
        """
        Drop test database for this project.
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

        try:
            database_name = dbinfo['TEST']['NAME']
        except KeyError:
            database_name = None

        if database_name is None:
            database_name = TEST_DATABASE_PREFIX + (options.get('dbname') or dbinfo.get('NAME'))

        if database_name is None or database_name == '':
            raise CommandError("You need to specify DATABASE_NAME in your Django settings file.")

        database_host = dbinfo.get('HOST') or database_host
        database_port = dbinfo.get('PORT') or database_port

        verbosity = int(options.get('verbosity', 1))
        if options.get('interactive'):
            confirm = input("""
You have requested to drop the test database.
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
                if os.path.isfile(database_name):
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
            logging.info('Executing: "' + drop_query + '"')
            connection.query(drop_query)
        elif engine in ('postgresql', 'postgresql_psycopg2', 'postgis'):
            if engine == 'postgresql':
                import psycopg as Database  # NOQA
            elif engine in ('postgresql_psycopg2', 'postgis'):
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
            drop_query = "DROP DATABASE IF EXISTS \"%s\";" % database_name
            logging.info('Executing: "' + drop_query + '"')

            try:
                cursor.execute(drop_query)
            except Database.ProgrammingError as e:
                logging.exception("Error: %s" % str(e))
        else:
            raise CommandError("Unknown database engine %s" % engine)

        if verbosity >= 2 or options.get('interactive'):
            print("Reset successful.")
