# -*- coding: utf-8 -*-
"""
sqldns.py - Prints Data Source Name on stdout

"""

import sys
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import color_style


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-R', '--router', action='store',
                    dest='router', default='default',
                    help='Use this router-database other then default'),
        make_option('-s', '--style', action='store',
                    dest='style', default=None,
                    help='DSN format style: keyvalue, uri, pgpass, all'),
        make_option('-a', '--all', action='store_true',
                    dest='all', default=False,
                    help='Show DSN for all database routes'),
        make_option('-q', '--quiet', action='store_true',
                    dest='quiet', default=False,
                    help='Quiet mode only show DSN'),
    )
    help = """Prints DSN on stdout, as specified in settings.py

    ./manage.py sqldsn [--router=<routername>] [--style=pgpass]"""

    requires_system_checks = False
    can_import_settings = True

    def handle(self, *args, **options):
        self.style = color_style()
        all_routers = options.get('all')

        if all_routers:
            routers = settings.DATABASES.keys()
        else:
            routers = [options.get('router')]

        for i, router in enumerate(routers):
            if i != 0:
                sys.stdout.write("\n")
            self.show_dsn(router, options)

    def show_dsn(self, router, options):
        dbinfo = settings.DATABASES.get(router)
        quiet = options.get('quiet')
        dsn_style = options.get('style')

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

        elif engine in ['postgresql_psycopg2', 'postgis']:
            dsn = self.postgresql(dbhost, dbport, dbname, dbuser, dbpass, dsn_style=dsn_style)

        elif engine == 'sqlite3':
            dsn.append('{}'.format(dbname))

        else:
            dsn.append(self.style.ERROR('Unknown database, can''t generate DSN'))

        if not quiet:
            sys.stdout.write(self.style.SQL_TABLE("DSN for router '%s' with engine '%s':\n" % (router, engine)))

        for output in dsn:
            sys.stdout.write("{}\n".format(output))

    def postgresql(self, dbhost, dbport, dbname, dbuser, dbpass, dsn_style=None):
        """PostgreSQL psycopg2 driver  accepts two syntaxes

        Plus a string for .pgpass file
        """
        dsn = []

        if dsn_style is None or dsn_style == 'all' or dsn_style == 'keyvalue':
            dsnstr = "host='{0}' dbname='{2}' user='{3}' password='{4}'"

            if dbport is not None:
                dsnstr = dsnstr + " port='{1}'"

            dsn.append(dsnstr.format(dbhost,
                                     dbport,
                                     dbname,
                                     dbuser,
                                     dbpass,))

        if dsn_style == 'all' or dsn_style == 'kwargs':
            dsnstr = "host='{0}', database='{2}', user='{3}', password='{4}'"
            if dbport is not None:
                dsnstr = dsnstr + ", port='{1}'"

            dsn.append(dsnstr.format(dbhost,
                                     dbport,
                                     dbname,
                                     dbuser,
                                     dbpass))

        if dsn_style == 'all' or dsn_style == 'uri':
            if dbport is not None:
                dsnstr = "postgresql://{3}:{4}@{0}:{1}/{2}"
            else:
                dsnstr = "postgresql://{3}:{4}@{0}/{2}"

            dsn.append(dsnstr.format(dbhost,
                                     dbport,
                                     dbname,
                                     dbuser,
                                     dbpass,))

        if dsn_style == 'all' or dsn_style == 'pgpass':
            if dbport is not None:
                dbport = 5432
            dsn.append('{0}:{1}:{2}:{3}:{4}'.format(dbhost,
                                                    dbport,
                                                    dbname,
                                                    dbuser,
                                                    dbpass))
        return dsn
