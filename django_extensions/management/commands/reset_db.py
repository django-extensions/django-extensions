"""
originally from http://www.djangosnippets.org/snippets/828/ by dnordberg
"""

from django.conf import settings
from django.core.management.base import CommandError, BaseCommand
from django.core.management import sql
from django.db.models import get_apps
import django
import logging
import re
from optparse import make_option


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noinput', action='store_false',
            dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--no-utf8', action='store_true',
            dest='no_utf8_support', default=False,
            help='Tells Django to not create a UTF-8 charset database'),
        make_option('-U', '--user', action='store',
            dest='user', default=None,
            help='Use another user for the database then defined in \
            settings.py'),
        make_option('-P', '--password', action='store',
            dest='password', default=None,
            help='Use another password for the database then defined in \
            settings.py'),
        make_option('-D', '--dbname', action='store',
            dest='dbname', default=None,
            help='Use another database name then defined in settings.py'),
        make_option('-R', '--router', action='store',
            dest='router', default=None,
            help='Use this router-database other then defined in settings.py'),
        make_option('-J', '--django-only', action='store',
            dest='django_only', default=True,
            help='Only reset tables associate with django'),
    )
    help = "Resets the database for this project."

    def clean_options(self, options):
        """
        If an option was not given and doesn't have a default, I don't want
        to know about it. This allows me to use options.get(key,default)
        instead of cludgy if value is None statements
        """
        for k, v in options.items():
            if v == None:
                del options[k]
        return options

    def getConnection(self, *args, **options):
        from django.db.utils import ConnectionHandler, DEFAULT_DB_ALIAS
        if not settings.DATABASES:
            if settings.DATABASE_ENGINE:
                import warnings
                warnings.warn(
                    "settings.DATABASE_* is deprecated; use \
                        settings.DATABASES instead.",
                    DeprecationWarning
                )

            settings.DATABASES[DEFAULT_DB_ALIAS] = {
                'ENGINE': settings.DATABASE_ENGINE,
                'HOST': settings.DATABASE_HOST,
                'NAME': settings.DATABASE_NAME,
                'OPTIONS': settings.DATABASE_OPTIONS,
                'PASSWORD': settings.DATABASE_PASSWORD,
                'PORT': settings.DATABASE_PORT,
                'USER': settings.DATABASE_USER,
                'TEST_CHARSET': settings.TEST_DATABASE_CHARSET,
                'TEST_COLLATION': settings.TEST_DATABASE_COLLATION,
                'TEST_NAME': settings.TEST_DATABASE_NAME,
            }
        router = options.get('router', DEFAULT_DB_ALIAS)

        connections = ConnectionHandler(settings.DATABASES)
        connection = connections[router]
        if 'user'  in options:
            connection.settings_dict['USER'] = options['user']
        if 'password' in options:
            connection.settings_dict['PASSWORD'] = options['password']
        if 'dbname' in options:
            connection.settings_dict['NAME'] = options['dbname']
        return connection

    def handle(self, *args, **options):
        options = self.clean_options(options)
        verbosity = int(options.get('verbosity', 1))
        if options.get('interactive'):
            confirm = raw_input("""
You have requested a database reset.
This will IRREVERSIBLY DESTROY
ALL data in the database "%s".
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """ % (settings.DATABASE_NAME,))
        else:
            confirm = 'yes'

        if confirm != 'yes':
            print "Reset cancelled."
            return

        if django.get_version() >= "1.2":
            self.handle_gt_12(*args, **options)
        else:
            self.handle_lg_12(*args, **options)
        if verbosity >= 2 or options.get('interactive'):
            print "Reset successful."

    def handle_gt_12(self, *args, **options):
        connection = self.getConnection(*args, **options)
        d_only = options['django_only']
        drop_commands = sql.sql_flush(
            self.style,
            connection,
            only_django=d_only
        )
        create_commands = []
        apps = get_apps()
        for app in apps:
            create_commands.extend(
                sql.sql_create(app, self.style, connection)
            )
        connection.cursor().executemany(drop_commands, [])
        connection.cursor().executemany(create_commands, [])

    def handle_lt_12(self, *args, **options):
        """
        Resets the database for this project.

        Note: Transaction wrappers are in reverse as a work around for
        autocommit, anybody know how to do this the right way?
        """

        postgis = re.compile('.*postgis')
        engine = settings.DATABASE_ENGINE
        user = options.get('user', settings.DATABASE_USER)
        db_name = options.get('dbname', settings.DATABASE_NAME)
        password = options.get('password', settings.DATABASE_PASSWORD)
        if db_name == '':
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured("You need to specify DATABASE_NAME in \
            your Django settings file or as the option --dbname")
        if engine == 'sqlite3':
            import os
            try:
                logging.info("Unlinking sqlite3 database")
                os.unlink(settings.DATABASE_NAME)
            except OSError:
                pass
        elif engine == 'mysql':
            import MySQLdb as Database
            kwargs = {
                'user': user,
                'passwd': password,
            }
            if settings.DATABASE_HOST.startswith('/'):
                kwargs['unix_socket'] = settings.DATABASE_HOST
            else:
                kwargs['host'] = settings.DATABASE_HOST
            if settings.DATABASE_PORT:
                kwargs['port'] = int(settings.DATABASE_PORT)

            connection = Database.connect(**kwargs)
            drop_query = 'DROP DATABASE IF EXISTS %s' % db_name
            utf8_support = options.get('no_utf8_support', False) and '' or \
            'CHARACTER SET utf8'
            create_query = 'CREATE DATABASE %s %s' % (db_name, utf8_support)
            logging.info('Executing... "' + drop_query + '"')
            connection.query(drop_query)
            logging.info('Executing... "' + create_query + '"')
            connection.query(create_query)

        elif engine == 'postgresql' or engine == 'postgresql_psycopg2' or \
            postgis.match(engine):
            if engine == 'postgresql':
                import psycopg as Database
            else:
                import psycopg2 as Database
            # Postgres won't let you drop the currently open database.
            # On some webhosts you wont have priveledge to drop a databas
            # TODO this should cycle through all the installed apps,
            # gather the the drop statements, and call those
            conn_string = "dbname=%s" % 'template1'
            if user:
                conn_string += " user=%s" % user
            if password:
                conn_string += " password='%s'" % password
            if settings.DATABASE_HOST:
                conn_string += " host=%s" % settings.DATABASE_HOST
            if settings.DATABASE_PORT:
                conn_string += " port=%s" % settings.DATABASE_PORT

            connection = Database.connect(conn_string)
            connection.set_isolation_level(0)  # autocommit false
            cursor = connection.cursor()
            drop_query = 'DROP DATABASE %s' % db_name
            logging.info('Executing... "' + drop_query + '"')

            try:
                cursor.execute(drop_query)
            except Database.ProgrammingError, e:
                logging.info("Error: %s" % str(e))

            # Encoding should be SQL_ASCII (7-bit postgres default) or
            # prefered UTF8 (8-bit)
            create_query = "CREATE DATABASE %s WITH OWNER = %s ENCODING = \
            'UTF8' " % (db_name, user)

            if postgis.match(engine):
                create_query += 'TEMPLATE = template_postgis '
            if settings.DEFAULT_TABLESPACE:
                create_query += 'TABLESPACE = %s;' % (
                    settings.DEFAULT_TABLESPACE
                )
            else:
                create_query += ';'
            logging.info('Executing... "' + create_query + '"')
            cursor.execute(create_query)

        else:
            raise CommandError("Unknown database engine %s" % engine)
