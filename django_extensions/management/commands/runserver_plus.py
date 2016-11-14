# -*- coding: utf-8 -*-
import logging
import os
import re
import socket
import sys
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django.db.backends import utils
from django.db.migrations.executor import MigrationExecutor
from django.core.exceptions import ImproperlyConfigured
from django.core.servers.basehttp import get_internal_wsgi_application
from django.utils.autoreload import gen_filenames

from django_extensions.management.technical_response import null_technical_500_response
from django_extensions.management.utils import RedirectHandler, setup_logger, signalcommand, has_ipdb

try:
    if 'whitenoise.runserver_nostatic' in settings.INSTALLED_APPS:
        USE_STATICFILES = False
    elif 'django.contrib.staticfiles' in settings.INSTALLED_APPS:
        from django.contrib.staticfiles.handlers import StaticFilesHandler
        USE_STATICFILES = True
    elif 'staticfiles' in settings.INSTALLED_APPS:
        from staticfiles.handlers import StaticFilesHandler  # noqa
        USE_STATICFILES = True
    else:
        USE_STATICFILES = False
except ImportError:
    USE_STATICFILES = False

naiveip_re = re.compile(r"""^(?:
(?P<addr>
    (?P<ipv4>\d{1,3}(?:\.\d{1,3}){3}) |         # IPv4 address
    (?P<ipv6>\[[a-fA-F0-9:]+\]) |               # IPv6 address
    (?P<fqdn>[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*) # FQDN
):)?(?P<port>\d+)$""", re.X)
DEFAULT_PORT = "8000"
DEFAULT_POLLER_RELOADER_INTERVAL = getattr(settings, 'RUNSERVERPLUS_POLLER_RELOADER_INTERVAL', 1)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Starts a lightweight Web server for development."

    # Validation is called explicitly each time the server is reloaded.
    requires_system_checks = False

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('addrport', nargs='?',
                            help='Optional port number, or ipaddr:port')
        parser.add_argument('--ipv6', '-6', action='store_true', dest='use_ipv6', default=False,
                            help='Tells Django to use a IPv6 address.')
        parser.add_argument('--noreload', action='store_false', dest='use_reloader', default=True,
                            help='Tells Django to NOT use the auto-reloader.')
        parser.add_argument('--browser', action='store_true', dest='open_browser',
                            help='Tells Django to open a browser.')
        parser.add_argument('--nothreading', action='store_false', dest='threaded',
                            help='Do not run in multithreaded mode.')
        parser.add_argument('--threaded', action='store_true', dest='threaded',
                            help='Run in multithreaded mode.')
        parser.add_argument('--output', dest='output_file', default=None,
                            help='Specifies an output file to send a copy of all messages (not flushed immediately).')
        parser.add_argument('--print-sql', action='store_true', default=False,
                            help="Print SQL queries as they're executed")
        parser.add_argument('--cert', dest='cert_path', action="store", type=str,
                            help='To use SSL, specify certificate path.')
        parser.add_argument('--extra-file', dest='extra_files', action="append", type=str,
                            help='auto-reload whenever the given file changes too (can be specified multiple times)')
        parser.add_argument('--reloader-interval', dest='reloader_interval', action="store", type=int, default=DEFAULT_POLLER_RELOADER_INTERVAL,
                            help='After how many seconds auto-reload should scan for updates in poller-mode [default=%s]' % DEFAULT_POLLER_RELOADER_INTERVAL)
        parser.add_argument('--pdb', action='store_true', dest='pdb', default=False,
                            help='Drop into pdb shell at the start of any view.')
        parser.add_argument('--ipdb', action='store_true', dest='ipdb', default=False,
                            help='Drop into ipdb shell at the start of any view.')
        parser.add_argument('--pm', action='store_true', dest='pm', default=False,
                            help='Drop into (i)pdb shell if an exception is raised in a view.')
        parser.add_argument('--startup-messages', dest='startup_messages', action="store", default='reload',
                            help='When to show startup messages: reload [default], once, always, never.')
        parser.add_argument('--keep-meta-shutdown', dest='keep_meta_shutdown_func', action='store_true', default=False,
                            help="Keep request.META['werkzeug.server.shutdown'] function which is automatically removed "
                                 "because Django debug pages tries to call the function and unintentionally shuts down "
                                 "the Werkzeug server.")
        parser.add_argument("--nopin", dest="nopin", action="store_true", default=False,
                            help="Disable the PIN in werkzeug. USE IT WISELY!"),

        if USE_STATICFILES:
            parser.add_argument('--nostatic', action="store_false", dest='use_static_handler', default=True,
                                help='Tells Django to NOT automatically serve static files at STATIC_URL.')
            parser.add_argument('--insecure', action="store_true", dest='insecure_serving', default=False,
                                help='Allows serving static files even if DEBUG is False.')

    @signalcommand
    def handle(self, *args, **options):
        addrport = options.get('addrport')
        startup_messages = options.get('startup_messages', 'reload')
        if startup_messages == "reload":
            self.show_startup_messages = os.environ.get('RUNSERVER_PLUS_SHOW_MESSAGES')
        elif startup_messages == "once":
            self.show_startup_messages = not os.environ.get('RUNSERVER_PLUS_SHOW_MESSAGES')
        elif startup_messages == "never":
            self.show_startup_messages = False
        else:
            self.show_startup_messages = True

        os.environ['RUNSERVER_PLUS_SHOW_MESSAGES'] = '1'

        # Do not use default ending='\n', because StreamHandler() takes care of it
        if hasattr(self.stderr, 'ending'):
            self.stderr.ending = None

        setup_logger(logger, self.stderr, filename=options.get('output_file', None))  # , fmt="[%(name)s] %(message)s")
        logredirect = RedirectHandler(__name__)

        # Redirect werkzeug log items
        werklogger = logging.getLogger('werkzeug')
        werklogger.setLevel(logging.INFO)
        werklogger.addHandler(logredirect)
        werklogger.propagate = False

        if options.get("print_sql", False):
            try:
                import sqlparse
            except ImportError:
                sqlparse = None  # noqa

            class PrintQueryWrapper(utils.CursorDebugWrapper):
                def execute(self, sql, params=()):
                    starttime = time.time()
                    try:
                        return self.cursor.execute(sql, params)
                    finally:
                        raw_sql = self.db.ops.last_executed_query(self.cursor, sql, params)
                        execution_time = time.time() - starttime
                        therest = ' -- [Execution time: %.6fs] [Database: %s]' % (execution_time, self.db.alias)
                        if sqlparse:
                            logger.info(sqlparse.format(raw_sql, reindent=True) + therest)
                        else:
                            logger.info(raw_sql + therest)

            utils.CursorDebugWrapper = PrintQueryWrapper

        pdb_option = options.get('pdb', False)
        ipdb_option = options.get('ipdb', False)
        pm = options.get('pm', False)
        try:
            from django_pdb.middleware import PdbMiddleware
        except ImportError:
            if pdb_option or ipdb_option or pm:
                raise CommandError("django-pdb is required for --pdb, --ipdb and --pm options. Please visit https://pypi.python.org/pypi/django-pdb or install via pip. (pip install django-pdb)")
            pm = False
        else:
            # Add pdb middleware if --pdb is specified or if in DEBUG mode
            middleware = 'django_pdb.middleware.PdbMiddleware'
            if (pdb_option or ipdb_option or settings.DEBUG) and middleware not in settings.MIDDLEWARE_CLASSES:
                settings.MIDDLEWARE_CLASSES += (middleware,)

            # If --pdb is specified then always break at the start of views.
            # Otherwise break only if a 'pdb' query parameter is set in the url
            if pdb_option:
                PdbMiddleware.always_break = 'pdb'
            elif ipdb_option:
                PdbMiddleware.always_break = 'ipdb'

            def postmortem(request, exc_type, exc_value, tb):
                if has_ipdb():
                    import ipdb
                    p = ipdb
                else:
                    import pdb
                    p = pdb
                print >>sys.stderr, "Exception occured: %s, %s" % (exc_type,
                                                                   exc_value)
                p.post_mortem(tb)

        # usurp django's handler
        from django.views import debug
        debug.technical_500_response = postmortem if pm else null_technical_500_response

        self.use_ipv6 = options.get('use_ipv6')
        if self.use_ipv6 and not socket.has_ipv6:
            raise CommandError('Your Python does not support IPv6.')
        self._raw_ipv6 = False
        if not addrport:
            try:
                addrport = settings.RUNSERVERPLUS_SERVER_ADDRESS_PORT
            except AttributeError:
                pass
        if not addrport:
            self.addr = ''
            self.port = DEFAULT_PORT
        else:
            m = re.match(naiveip_re, addrport)
            if m is None:
                raise CommandError('"%s" is not a valid port number '
                                   'or address:port pair.' % addrport)
            self.addr, _ipv4, _ipv6, _fqdn, self.port = m.groups()
            if not self.port.isdigit():
                raise CommandError("%r is not a valid port number." %
                                   self.port)
            if self.addr:
                if _ipv6:
                    self.addr = self.addr[1:-1]
                    self.use_ipv6 = True
                    self._raw_ipv6 = True
                elif self.use_ipv6 and not _fqdn:
                    raise CommandError('"%s" is not a valid IPv6 address.'
                                       % self.addr)
        if not self.addr:
            self.addr = '::1' if self.use_ipv6 else '127.0.0.1'

        self.inner_run(options)

    def inner_run(self, options):
        import django

        try:
            from werkzeug import run_simple, DebuggedApplication
            from werkzeug.serving import WSGIRequestHandler as _WSGIRequestHandler

            # Set colored output
            if settings.DEBUG:
                try:
                    set_werkzeug_log_color()
                except:  # We are dealing with some internals, anything could go wrong
                    if self.show_startup_messages:
                        print("Wrapping internal werkzeug logger for color highlighting has failed!")
                    pass

        except ImportError:
            raise CommandError("Werkzeug is required to use runserver_plus.  Please visit http://werkzeug.pocoo.org/ or install via pip. (pip install Werkzeug)")

        class WSGIRequestHandler(_WSGIRequestHandler):
            def make_environ(self):
                environ = super(WSGIRequestHandler, self).make_environ()
                if not options.get('keep_meta_shutdown_func'):
                    del environ['werkzeug.server.shutdown']
                return environ

        threaded = options.get('threaded', True)
        use_reloader = options.get('use_reloader', True)
        open_browser = options.get('open_browser', False)
        cert_path = options.get("cert_path")
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'
        bind_url = "http://%s:%s/" % (
            self.addr if not self._raw_ipv6 else '[%s]' % self.addr, self.port)
        extra_files = options.get('extra_files', None) or []
        reloader_interval = options.get('reloader_interval', 1)

        self.nopin = options.get('nopin', False)

        if self.show_startup_messages:
            print("Performing system checks...\n")
        if hasattr(self, 'check'):
            self.check(display_num_errors=self.show_startup_messages)
        else:
            self.validate(display_num_errors=self.show_startup_messages)
        try:
            self.check_migrations()
        except ImproperlyConfigured:
            pass
        if self.show_startup_messages:
            print("\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE))
            print("Development server is running at %s" % (bind_url,))
            print("Using the Werkzeug debugger (http://werkzeug.pocoo.org/)")
            print("Quit the server with %s." % quit_command)
        handler = get_internal_wsgi_application()
        if USE_STATICFILES:
            use_static_handler = options.get('use_static_handler', True)
            insecure_serving = options.get('insecure_serving', False)
            if use_static_handler and (settings.DEBUG or insecure_serving):
                handler = StaticFilesHandler(handler)
        if open_browser:
            import webbrowser
            webbrowser.open(bind_url)
        if cert_path:
            """
            OpenSSL is needed for SSL support.

            This will make flakes8 throw warning since OpenSSL is not used
            directly, alas, this is the only way to show meaningful error
            messages. See:
            http://lucumr.pocoo.org/2011/9/21/python-import-blackbox/
            for more information on python imports.
            """
            try:
                import OpenSSL  # NOQA
            except ImportError:
                raise CommandError("Python OpenSSL Library is "
                                   "required to use runserver_plus with ssl support. "
                                   "Install via pip (pip install pyOpenSSL).")

            dir_path, cert_file = os.path.split(cert_path)
            if not dir_path:
                dir_path = os.getcwd()
            root, ext = os.path.splitext(cert_file)
            certfile = os.path.join(dir_path, root + ".crt")
            keyfile = os.path.join(dir_path, root + ".key")
            try:
                from werkzeug.serving import make_ssl_devcert
                if os.path.exists(certfile) and \
                        os.path.exists(keyfile):
                            ssl_context = (certfile, keyfile)
                else:  # Create cert, key files ourselves.
                    ssl_context = make_ssl_devcert(
                        os.path.join(dir_path, root), host='localhost')
            except ImportError:
                if self.show_startup_messages:
                    print("Werkzeug version is less than 0.9, trying adhoc certificate.")
                ssl_context = "adhoc"

        else:
            ssl_context = None

        if use_reloader and settings.USE_I18N:
            extra_files.extend(filter(lambda filename: filename.endswith('.mo'), gen_filenames()))

        # Werkzeug needs to be clued in its the main instance if running
        # without reloader or else it won't show key.
        # https://git.io/vVIgo
        if not use_reloader:
            os.environ['WERKZEUG_RUN_MAIN'] = 'true'

        # Don't run a second instance of the debugger / reloader
        # See also: https://github.com/django-extensions/django-extensions/issues/832
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            if self.nopin:
                os.environ['WERKZEUG_DEBUG_PIN'] = 'off'
            handler = DebuggedApplication(handler, True)

        run_simple(
            self.addr,
            int(self.port),
            handler,
            use_reloader=use_reloader,
            use_debugger=True,
            extra_files=extra_files,
            reloader_interval=reloader_interval,
            threaded=threaded,
            request_handler=WSGIRequestHandler,
            ssl_context=ssl_context,
        )

    def check_migrations(self):
        """
        Checks to see if the set of migrations on disk matches the
        migrations in the database. Prints a warning if they don't match.
        """
        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan and self.show_startup_messages:
            self.stdout.write(self.style.NOTICE("\nYou have unapplied migrations; your app may not work properly until they are applied."))
            self.stdout.write(self.style.NOTICE("Run 'python manage.py migrate' to apply them.\n"))


def set_werkzeug_log_color():
    """Try to set color to the werkzeug log.
    """
    from django.core.management.color import color_style
    from werkzeug.serving import WSGIRequestHandler
    from werkzeug._internal import _log

    _style = color_style()
    _orig_log = WSGIRequestHandler.log

    def werk_log(self, type, message, *args):
        try:
            msg = '%s - - [%s] %s' % (
                self.address_string(),
                self.log_date_time_string(),
                message % args,
            )
            http_code = str(args[1])
        except:
            return _orig_log(type, message, *args)

        # Utilize terminal colors, if available
        if http_code[0] == '2':
            # Put 2XX first, since it should be the common case
            msg = _style.HTTP_SUCCESS(msg)
        elif http_code[0] == '1':
            msg = _style.HTTP_INFO(msg)
        elif http_code == '304':
            msg = _style.HTTP_NOT_MODIFIED(msg)
        elif http_code[0] == '3':
            msg = _style.HTTP_REDIRECT(msg)
        elif http_code == '404':
            msg = _style.HTTP_NOT_FOUND(msg)
        elif http_code[0] == '4':
            msg = _style.HTTP_BAD_REQUEST(msg)
        else:
            # Any 5XX, or any other response
            msg = _style.HTTP_SERVER_ERROR(msg)

        _log(type, msg)

    WSGIRequestHandler.log = werk_log
