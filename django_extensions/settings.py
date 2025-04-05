# -*- coding: utf-8 -*-
import os

from django.conf import settings

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
REPLACEMENTS = getattr(settings, "EXTENSIONS_REPLACEMENTS", {})

DEFAULT_SQLITE_ENGINES = (
    "django.db.backends.sqlite3",
    "django.db.backends.spatialite",
    "django_prometheus.db.backends.sqlite3",
)
DEFAULT_MYSQL_ENGINES = (
    "django.db.backends.mysql",
    "django.contrib.gis.db.backends.mysql",
    "django_prometheus.db.backends.mysql",
    "mysql.connector.django",
)
DEFAULT_POSTGRESQL_ENGINES = (
    "django.db.backends.postgresql",
    "django.db.backends.postgresql_psycopg2",
    "django.db.backends.postgis",
    "django.contrib.gis.db.backends.postgis",
    "psqlextra.backend",
    "django_zero_downtime_migrations.backends.postgres",
    "django_zero_downtime_migrations.backends.postgis",
    "django_prometheus.db.backends.postgresql",
    "django_prometheus.db.backends.postgis",
    "django_tenants.postgresql_backend",
)

SQLITE_ENGINES = getattr(
    settings, "DJANGO_EXTENSIONS_RESET_DB_SQLITE_ENGINES", DEFAULT_SQLITE_ENGINES
)
MYSQL_ENGINES = getattr(
    settings, "DJANGO_EXTENSIONS_RESET_DB_MYSQL_ENGINES", DEFAULT_MYSQL_ENGINES
)
POSTGRESQL_ENGINES = getattr(
    settings,
    "DJANGO_EXTENSIONS_RESET_DB_POSTGRESQL_ENGINES",
    DEFAULT_POSTGRESQL_ENGINES,
)

DEFAULT_PRINT_SQL_TRUNCATE_CHARS = 1000
