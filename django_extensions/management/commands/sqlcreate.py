# -*- coding: utf-8 -*-
import socket
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = """Generates the SQL to create your database for you, as specified in settings.py
The envisioned use case is something like this:

    ./manage.py sqlcreate [--router=<routername>] | mysql -u <db_administrator> -p
    ./manage.py sqlcreate [--router=<routername>] | psql -U <db_administrator> -W"""

    requires_system_checks = False
    can_import_settings = True

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '-R', '--router', action='store', dest='router', default='default',
            help='Use this router-database other then defined in settings.py'
        )
        parser.add_argument(
            '-D', '--drop', action='store_true', dest='drop', default=False,
            help='If given, includes commands to drop any existing user and database.'
        )

    @signalcommand
    def handle(self, *args, **options):
        router = options['router']
        dbinfo = settings.DATABASES.get(router)
        if dbinfo is None:
            raise CommandError("Unknown database router %s" % router)

        engine = dbinfo.get('ENGINE').split('.')[-1]
        dbuser = dbinfo.get('USER')
        dbpass = dbinfo.get('PASSWORD')
        dbname = dbinfo.get('NAME')
        dbhost = dbinfo.get('HOST')
        dbclient = socket.gethostname()

        # django settings file tells you that localhost should be specified by leaving
        # the DATABASE_HOST blank
        if not dbhost:
            dbhost = 'localhost'

        if engine == 'mysql':
            sys.stderr.write("""-- WARNING!: https://docs.djangoproject.com/en/dev/ref/databases/#collation-settings
-- Please read this carefully! Collation will be set to utf8_bin to have case-sensitive data.
""")
            print("CREATE DATABASE %s CHARACTER SET utf8 COLLATE utf8_bin;" % dbname)
            print("GRANT ALL PRIVILEGES ON %s.* to '%s'@'%s' identified by '%s';" % (
                dbname, dbuser, dbclient, dbpass
            ))

        elif engine in ('postgresql', 'postgresql_psycopg2'):
            if options['drop']:
                print("DROP DATABASE IF EXISTS %s;" % (dbname,))
                print("DROP USER IF EXISTS %s;" % (dbuser,))

            print("CREATE USER %s WITH ENCRYPTED PASSWORD '%s' CREATEDB;" % (dbuser, dbpass))
            print("CREATE DATABASE %s WITH ENCODING 'UTF-8' OWNER \"%s\";" % (dbname, dbuser))
            print("GRANT ALL PRIVILEGES ON DATABASE %s TO %s;" % (dbname, dbuser))

        elif engine == 'sqlite3':
            sys.stderr.write("-- manage.py syncdb will automatically create a sqlite3 database file.\n")

        else:
            # CREATE DATABASE is not SQL standard, but seems to be supported by most.
            sys.stderr.write("-- Don't know how to handle '%s' falling back to SQL.\n" % engine)
            print("CREATE DATABASE %s;" % dbname)
            print("GRANT ALL PRIVILEGES ON DATABASE %s to %s;" % (dbname, dbuser))
