# -*- coding: utf-8 -*-
"""
sqldns.py

Prints Data Source Name on stdout
"""

import sys
import warnings

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import color_style
from django.db import DEFAULT_DB_ALIAS
from django_extensions.utils.deprecation import RemovedInNextVersionWarning


class Command(BaseCommand):
    help = "Prints DSN on stdout, as specified in settings.py"
    requires_system_checks = False
    can_import_settings = True

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '-R', '--router', action='store',
            dest='router', default=DEFAULT_DB_ALIAS,
            help='Use this router-database other then default (deprecated: use --database instead)'
        )
        parser.add_argument(
            '--database', default=DEFAULT_DB_ALIAS,
            help='Nominates a database to run command for. Defaults to the "%s" database.' % DEFAULT_DB_ALIAS,
        )
        parser.add_argument(
            '-s', '--style', action='store',
            dest='style', default=None,
            help='DSN format style: keyvalue, uri, pgpass, all'
        )
        parser.add_argument(
            '-a', '--all', action='store_true',
            dest='all', default=False,
            help='Show DSN for all database routes'
        )
        parser.add_argument(
            '-q', '--quiet', action='store_true',
            dest='quiet', default=False,
            help='Quiet mode only show DSN'
        )

    def handle(self, *args, **options):
        self.style = color_style()
        all_databases = options['all']

        if all_databases:
            databases = settings.DATABASES.keys()
        else:
            databases = [options['database']]
            if options['router'] != DEFAULT_DB_ALIAS:
                warnings.warn("--router is deprecated. You should use --database.", RemovedInNextVersionWarning, stacklevel=2)
                databases = [options['router']]

        for i, database in enumerate(databases):
            if i != 0:
                sys.stdout.write("\n")
            self.show_dsn(database, options)

    def show_dsn(self, database, options):
        dbinfo = settings.DATABASES.get(database)
        quiet = options['quiet']
        dsn_style = options['style']

        if dbinfo is None:
            raise CommandError("Unknown database %s" % database)

        engine = engine = dbinfo.get('ENGINE')
        if 'psqlextra' not in engine:
            engine = engine.split('.')[-1]
        dbuser = dbinfo.get('USER')
        dbpass = dbinfo.get('PASSWORD')
        dbname = dbinfo.get('NAME')
        dbhost = dbinfo.get('HOST')
        dbport = dbinfo.get('PORT')

        dsn = []

        if engine == 'mysql':
            dsn.append(self._mysql(dbhost, dbport, dbname, dbuser, dbpass))
        elif engine in ['postgresql', 'postgresql_psycopg2', 'postgis', 'psqlextra.backend']:
            dsn.extend(self._postgresql(
                dbhost, dbport, dbname, dbuser, dbpass, dsn_style=dsn_style))
        elif engine == 'sqlite3':
            dsn.append('{}'.format(dbname))
        else:
            dsn.append(self.style.ERROR('Unknown database, can''t generate DSN'))

        if not quiet:
            sys.stdout.write(self.style.SQL_TABLE("DSN for database '%s' with engine '%s':\n" % (database, engine)))

        for output in dsn:
            sys.stdout.write("{}\n".format(output))

    def _mysql(self, dbhost, dbport, dbname, dbuser, dbpass):
        dsnstr = 'host="{0}", db="{2}", user="{3}", passwd="{4}"'

        if dbport is not None:
            dsnstr += ', port="{1}"'

        return dsnstr.format(dbhost, dbport, dbname, dbuser, dbpass)

    def _postgresql(self, dbhost, dbport, dbname, dbuser, dbpass, dsn_style=None):  # noqa
        """PostgreSQL psycopg2 driver accepts two syntaxes

        Plus a string for .pgpass file
        """
        dsn = []

        if dsn_style is None or dsn_style == 'all' or dsn_style == 'keyvalue':
            dsnstr = "host='{0}' dbname='{2}' user='{3}' password='{4}'"

            if dbport is not None:
                dsnstr += " port='{1}'"

            dsn.append(dsnstr.format(
                dbhost,
                dbport,
                dbname,
                dbuser,
                dbpass,
            ))

        if dsn_style in ('all', 'kwargs'):
            dsnstr = "host='{0}', database='{2}', user='{3}', password='{4}'"
            if dbport is not None:
                dsnstr += ", port='{1}'"

            dsn.append(dsnstr.format(
                dbhost,
                dbport,
                dbname,
                dbuser,
                dbpass,
            ))

        if dsn_style in ('all', 'uri'):
            dsnstr = "postgresql://{user}:{password}@{host}/{name}"

            dsn.append(dsnstr.format(
                host="{host}:{port}".format(host=dbhost, port=dbport) if dbport else dbhost,  # noqa
                name=dbname,
                user=dbuser,
                password=dbpass,
            ))

        if dsn_style in ('all', 'pgpass'):
            dsn.append(':'.join(map(str, filter(None, [dbhost, dbport, dbname, dbuser, dbpass]))))

        return dsn
