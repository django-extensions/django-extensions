# -*- coding: utf-8 -*-
"""
sqldns.py

Prints Data Source Name on stdout
"""

import sys
import warnings
from typing import List

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import color_style
from django.db import DEFAULT_DB_ALIAS
from django_extensions.settings import SQLITE_ENGINES, POSTGRESQL_ENGINES, MYSQL_ENGINES
from django_extensions.utils.deprecation import RemovedInNextVersionWarning


def _sqlite_name(dbhost, dbport, dbname, dbuser, dbpass):
    return dbname


def _mysql_keyvalue(dbhost, dbport, dbname, dbuser, dbpass):
    dsnstr = f'host="{dbhost}", db="{dbname}", user="{dbuser}", passwd="{dbpass}"'
    if dbport is not None:
        dsnstr += f', port="{dbport}"'
    return dsnstr


def _mysql_args(dbhost, dbport, dbname, dbuser, dbpass):
    dsnstr = f'-h "{dbhost}" -D "{dbname}" -u "{dbuser}" -p "{dbpass}"'
    if dbport is not None:
        dsnstr += f' -P {dbport}'
    return dsnstr


def _postgresql_keyvalue(dbhost, dbport, dbname, dbuser, dbpass):
    dsnstr = f"host='{dbhost}' dbname='{dbname}' user='{dbuser}' password='{dbpass}'"
    if dbport is not None:
        dsnstr += f" port='{dbport}'"
    return dsnstr


def _postgresql_kwargs(dbhost, dbport, dbname, dbuser, dbpass):
    dsnstr = f"host={dbhost!r}, database={dbname!r}, user={dbuser!r}, password={dbpass!r}"
    if dbport is not None:
        dsnstr += f", port={dbport!r}"
    return dsnstr


def _postgresql_pgpass(dbhost, dbport, dbname, dbuser, dbpass):
    return ':'.join(str(s) for s in [dbhost, dbport, dbname, dbuser, dbpass])


def _uri(engine):
    def inner(dbhost, dbport, dbname, dbuser, dbpass):
        host = dbhost or ''
        if dbport is not None and dbport != '':
            host += f':{dbport}'
        if dbuser is not None and dbuser != '':
            user = dbuser
            if dbpass is not None and dbpass != '':
                user += f':{dbpass}'
            host = f'{user}@{host}'
        return f'{engine}://{host}/{dbname}'
    return inner


_FORMATTERS = [
    (SQLITE_ENGINES, None, _sqlite_name),
    (SQLITE_ENGINES, 'filename', _sqlite_name),
    (SQLITE_ENGINES, 'uri', _uri('sqlite')),
    (MYSQL_ENGINES, None, _mysql_keyvalue),
    (MYSQL_ENGINES, 'keyvalue', _mysql_keyvalue),
    (MYSQL_ENGINES, 'args', _mysql_args),
    (MYSQL_ENGINES, 'uri', _uri('mysql')),
    (POSTGRESQL_ENGINES, None, _postgresql_keyvalue),
    (POSTGRESQL_ENGINES, 'keyvalue', _postgresql_keyvalue),
    (POSTGRESQL_ENGINES, 'kwargs', _postgresql_kwargs),
    (POSTGRESQL_ENGINES, 'uri', _uri('postgresql')),
    (POSTGRESQL_ENGINES, 'pgpass', _postgresql_pgpass),
]


class Command(BaseCommand):
    help = "Prints DSN on stdout, as specified in settings.py"
    requires_system_checks: List[str] = []
    can_import_settings = True

    def add_arguments(self, parser):
        super().add_arguments(parser)
        dbspec = parser.add_mutually_exclusive_group()
        dbspec.add_argument(
            '-R', '--router', action='store',
            dest='router', default=DEFAULT_DB_ALIAS,
            help='Use this router-database other then default (deprecated: use --database instead)'
        )
        dbspec.add_argument(
            '--database', default=DEFAULT_DB_ALIAS,
            help='Nominates a database to run command for. Defaults to the "%s" database.' % DEFAULT_DB_ALIAS,
        )
        styles = sorted(set([style for _, style, _ in _FORMATTERS if style is not None]))
        parser.add_argument(
            '-s', '--style', action='store',
            dest='style', default=None, choices=styles + ['all'],
            help='DSN format style.'
        )
        dbspec.add_argument(
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

        engine = dbinfo.get('ENGINE')
        dbuser = dbinfo.get('USER')
        dbpass = dbinfo.get('PASSWORD')
        dbname = dbinfo.get('NAME')
        dbhost = dbinfo.get('HOST')
        dbport = dbinfo.get('PORT')
        if dbport == '':
            dbport = None

        dsn = [
            formatter(dbhost, dbport, dbname, dbuser, dbpass)
            for engines, style, formatter in _FORMATTERS
            if engine in engines and (
                dsn_style == style or dsn_style == 'all' and style is not None)
        ]

        if not dsn:
            available = ', '.join(
                style for engines, style, _ in _FORMATTERS
                if engine in engines and style is not None)
            dsn = [self.style.ERROR(
                f"Invalid style {dsn_style} for {engine} (available: {available})"
                if available else "Unknown database, can't generate DSN"
            )]

        if not quiet:
            sys.stdout.write(self.style.SQL_TABLE(f'DSN for database {database!r} with engine {engine!r}:\n'))

        for output in dsn:
            sys.stdout.write(f'{output}\n')
