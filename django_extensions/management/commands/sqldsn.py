# -*- coding: utf-8 -*-
"""
sqldns.py - Prints Data Source Name on stdout

"""

import sys
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-R', '--router', action='store',
                    dest='router', default='default',
                    help='Use this router-database other then default'),
    )
    help = """Prints DSN on stdout, as specified in settings.py

    ./manage.py sqldsn [--router=<routername>]"""

    requires_model_validation = False
    can_import_settings = True

    def handle(self, *args, **options):
        router = options.get('router')
        dbinfo = settings.DATABASES.get(router)
        if dbinfo is None:
            raise CommandError("Unknown database router %s" % router)

        engine = dbinfo.get('ENGINE').split('.')[-1]
        dbuser = dbinfo.get('USER')
        dbpass = dbinfo.get('PASSWORD')
        dbname = dbinfo.get('NAME')
        dbhost = dbinfo.get('HOST')
        dbport = dbinfo.get('PORT')

        dsn = []

        if engine == 'mysql':
            dsnstr = 'host="{0}", db="{2}", user="{3}", passwd="{4}"'
            if dbport is not None:
                dsnstr = dsnstr + ', port="{1}"'

            dsn.append(dsnstr.format(dbhost,
                                     dbport,
                                     dbname,
                                     dbuser,
                                     dbpass))

        elif engine == 'postgresql_psycopg2':
            dsn = self.postgresql(dbhost, dbport, dbname, dbuser, dbpass)

        elif engine == 'sqlite3':
            dsn.append('{}'.format(dbname))

        else:
            dsn.append('Unknown database, can''t generate DSN')

        for output in dsn:
            sys.stdout.write("{}\n".format(output))

    def postgresql(self, dbhost, dbport, dbname, dbuser, dbpass):
        """PostgreSQL psycopg2 driver  accepts two syntaxes

        Plus a string for .pgapss file
        """
        dsn = []
        dsnstr = "host='{0}', database='{2}', user='{3}', password='{4}'"
        if dbport is not None:
            dsnstr = dsnstr + ", port='{1}'"

        dsn.append(dsnstr.format(dbhost,
                                 dbport,
                                 dbname,
                                 dbuser,
                                 dbpass))

        dsnstr = "host={0} dbname={2} user={3} password={4}"

        if dbport is not None:
            dsnstr = dsnstr + " port={1}"

        dsn.append(dsnstr.format(dbhost,
                                 dbport,
                                 dbname,
                                 dbuser,
                                 dbpass,))

        if dbport is not None:
            dbport = 5432
        dsn.append('{0}:{1}:{2}:{3}:{4}'.format(dbhost,
                                                dbport,
                                                dbname,
                                                dbuser,
                                                dbpass))
        return dsn
