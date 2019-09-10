# -*- coding: utf-8 -*-
import os

from django.conf import settings

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
REPLACEMENTS = getattr(settings, 'EXTENSIONS_REPLACEMENTS', {})

DEFAULT_SQLITE_ENGINES = (
    'django.db.backends.sqlite3',
    'django.db.backends.spatialite',
)
DEFAULT_MYSQL_ENGINES = (
    'django.db.backends.mysql',
    'django.contrib.gis.db.backends.mysql',
)
DEFAULT_POSTGRESQL_ENGINES = (
    'django.db.backends.postgresql',
    'django.db.backends.postgresql_psycopg2',
    'django.db.backends.postgis',
    'django.contrib.gis.db.backends.postgis',
    'psqlextra.backend',
)

SQLITE_ENGINES = getattr(settings, 'DJANGO_EXTENSIONS_RESET_DB_SQLITE_ENGINES', DEFAULT_SQLITE_ENGINES)
MYSQL_ENGINES = getattr(settings, 'DJANGO_EXTENSIONS_RESET_DB_MYSQL_ENGINES', DEFAULT_MYSQL_ENGINES)
POSTGRESQL_ENGINES = getattr(settings, 'DJANGO_EXTENSIONS_RESET_DB_POSTGRESQL_ENGINES', DEFAULT_POSTGRESQL_ENGINES)
