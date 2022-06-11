# -*- coding: utf-8 -*-
import time
import traceback
from contextlib import contextmanager

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends import utils

from django_extensions.settings import DEFAULT_PRINT_SQL_TRUNCATE_CHARS


@contextmanager
def monkey_patch_cursordebugwrapper(print_sql=None, print_sql_location=False, truncate=None, logger=print, confprefix="DJANGO_EXTENSIONS"):
    if not print_sql:
        yield
    else:
        if truncate is None:
            truncate = getattr(settings, '%s_PRINT_SQL_TRUNCATE' % confprefix, DEFAULT_PRINT_SQL_TRUNCATE_CHARS)

        # Code orginally from http://gist.github.com/118990
        sqlparse = None
        if getattr(settings, '%s_SQLPARSE_ENABLED' % confprefix, True):
            try:
                import sqlparse

                sqlparse_format_kwargs_defaults = dict(
                    reindent_aligned=True,
                    truncate_strings=500,
                )
                sqlparse_format_kwargs = getattr(settings, '%s_SQLPARSE_FORMAT_KWARGS' % confprefix, sqlparse_format_kwargs_defaults)
            except ImportError:
                sqlparse = None

        pygments = None
        if getattr(settings, '%s_PYGMENTS_ENABLED' % confprefix, True):
            try:
                import pygments.lexers
                import pygments.formatters

                pygments_formatter = getattr(settings, '%s_PYGMENTS_FORMATTER' % confprefix, pygments.formatters.TerminalFormatter)
                pygments_formatter_kwargs = getattr(settings, '%s_PYGMENTS_FORMATTER_KWARGS' % confprefix, {})
            except ImportError:
                pass

        class PrintQueryWrapperMixin:
            def execute(self, sql, params=()):
                starttime = time.time()
                try:
                    return utils.CursorWrapper.execute(self, sql, params)
                finally:
                    execution_time = time.time() - starttime
                    raw_sql = self.db.ops.last_executed_query(self.cursor, sql, params)
                    if truncate:
                        raw_sql = raw_sql[:truncate]

                    if sqlparse:
                        raw_sql = sqlparse.format(raw_sql, **sqlparse_format_kwargs)

                    if pygments:
                        raw_sql = pygments.highlight(
                            raw_sql,
                            pygments.lexers.get_lexer_by_name("sql"),
                            pygments_formatter(**pygments_formatter_kwargs),
                        )

                    logger(raw_sql)
                    logger("Execution time: %.6fs [Database: %s]" % (execution_time, self.db.alias))
                    if print_sql_location:
                        logger("Location of SQL Call:")
                        logger(''.join(traceback.format_stack()))

        _CursorDebugWrapper = utils.CursorDebugWrapper

        class PrintCursorQueryWrapper(PrintQueryWrapperMixin, _CursorDebugWrapper):
            pass

        try:
            from django.db import connections
            _force_debug_cursor = {}
            for connection_name in connections:
                _force_debug_cursor[connection_name] = connections[connection_name].force_debug_cursor
        except Exception:
            connections = None

        utils.CursorDebugWrapper = PrintCursorQueryWrapper

        postgresql_base = None
        try:
            from django.db.backends.postgresql import base as postgresql_base
            _PostgreSQLCursorDebugWrapper = postgresql_base.CursorDebugWrapper

            class PostgreSQLPrintCursorDebugWrapper(PrintQueryWrapperMixin, _PostgreSQLCursorDebugWrapper):
                pass
        except (ImproperlyConfigured, TypeError):
            postgresql_base = None

        if postgresql_base:
            postgresql_base.CursorDebugWrapper = PostgreSQLPrintCursorDebugWrapper

        if connections:
            for connection_name in connections:
                connections[connection_name].force_debug_cursor = True

        yield

        utils.CursorDebugWrapper = _CursorDebugWrapper

        if postgresql_base:
            postgresql_base.CursorDebugWrapper = _PostgreSQLCursorDebugWrapper

        if connections:
            for connection_name in connections:
                connections[connection_name].force_debug_cursor = _force_debug_cursor[connection_name]
