# -*- coding: utf-8 -*-
"""
Recreates the public schema for current database (PostgreSQL only).
Useful for Docker environments where you need to reset database
schema while there are active connections.
"""
from django.core.management import BaseCommand, CommandError
from django.db import connections
from django.conf import settings
from six.moves import input


class Command(BaseCommand):
    """
    `reset_schema` command implementation.
    """
    help = "Recreates the public schema for this project."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--noinput', action='store_false',
            dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'
        )
        parser.add_argument(
            '-R', '--router', action='store', dest='router', default='default',
            help='Use this router-database instead of the one defined in settings.py'
        )
        parser.add_argument(
            '-S', '--schema', action='store', dest='schema', default='public',
            help='Drop this schema instead of "public"'
        )

    def handle(self, *args, **options):
        router = options['router']
        dbinfo = settings.DATABASES.get(router)
        if dbinfo is None:
            raise CommandError("Unknown database router %s" % router)

        engine = dbinfo.get('ENGINE').split('.')[-1]
        if engine not in ('postgresql', 'postgresql_psycopg2', 'postgis'):
            raise CommandError('This command can be used only with PostgreSQL databases.')

        database_name = dbinfo['NAME']

        schema = options['schema']

        if options['interactive']:
            confirm = input("""
You have requested a database schema reset.
This will IRREVERSIBLY DESTROY ALL data
in the "{}" schema of database "{}".
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """.format(schema, database_name))
        else:
            confirm = 'yes'

        if confirm != 'yes':
            print("Reset cancelled.")
            return
        with connections[router].cursor() as cursor:
            cursor.execute("DROP SCHEMA {} CASCADE".format(schema))
            cursor.execute("CREATE SCHEMA {}".format(schema))
