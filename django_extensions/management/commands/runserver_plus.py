import logging
import os
import re
import socket
import sys
import time
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.technical_response import \
    null_technical_500_response
from django_extensions.management.utils import (
    RedirectHandler, setup_logger, signalcommand,
)

try:
    if 'django.contrib.staticfiles' in settings.INSTALLED_APPS:
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
    option_list = BaseCommand.option_list + (
        make_option('--ipv6', '-6', action='store_true', dest='use_ipv6', default=False,
                    help='Tells Django to use a IPv6 address.'),
        make_option('--noreload', action='store_false', dest='use_reloader', default=True,
                    help='Tells Django to NOT use the auto-reloader.'),
        make_option('--browser', action='store_true', dest='open_browser',
                    help='Tells Django to open a browser.'),
        make_option('--adminmedia', dest='admin_media_path', default='',
                    help='Specifies the directory from which to serve admin media.'),
        make_option('--nothreading', action='store_false', dest='threaded',
                    help='Do not run in multithreaded mode.'),
        make_option('--threaded', action='store_true', dest='threaded',
                    help='Run in multithreaded mode.'),
        make_option('--output', dest='output_file', default=None,
                    help='Specifies an output file to send a copy of all messages (not flushed immediately).'),
        make_option('--print-sql', action='store_true', default=False,
                    help="Print SQL queries as they're executed"),
        make_option('--cert', dest='cert_path', action="store", type="string",
                    help='To use SSL, specify certificate path.'),
        make_option('--extra-file', dest='extra_files', action="append", type="string",
                    help='auto-reload whenever the given file changes too (can be specified multiple times)'),
        make_option('--reloader-interval', dest='reloader_interval', action="store", type="int", default=DEFAULT_POLLER_RELOADER_INTERVAL,
                    help='After how many seconds auto-reload should scan for updates in poller-mode [default=%s]' % DEFAULT_POLLER_RELOADER_INTERVAL),
    )
    if USE_STATICFILES:
        option_list += (
            make_option('--nostatic', action="store_false", dest='use_static_handler', default=True,
                        help='Tells Django to NOT automatically serve static files at STATIC_URL.'),
            make_option('--insecure', action="store_true", dest='insecure_serving', default=False,
                        help='Allows serving static files even if DEBUG is False.'),
        )
    help = "Starts a lightweight Web server for development."
    args = '[optional port number, or ipaddr:port]'

    # Validation is called explicitly each time the server is reloaded.
    requires_system_checks = False

    @signalcommand
    def handle(self, addrport='', *args, **options):
        import django

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
                # Django 1.7 onwards
                from django.db.backends import utils
            except ImportError:
                # Django 1.6 below
                from django.db.backends import util as utils

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

        try:
            from django.core.servers.basehttp import AdminMediaHandler
            USE_ADMINMEDIAHANDLER = True
        except ImportError:
            USE_ADMINMEDIAHANDLER = False

        try:
            from django.core.servers.basehttp import get_internal_wsgi_application as WSGIHandler
        except ImportError:
            from django.core.handlers.wsgi import WSGIHandler  # noqa

        try:
            from werkzeug import run_simple, DebuggedApplication

            # Set colored output
            if settings.DEBUG:
                try:
                    set_werkzeug_log_color()
                except:     # We are dealing with some internals, anything could go wrong
                    print("Wrapping internal werkzeug logger for color highlighting has failed!")
                    pass

        except ImportError:
            raise CommandError("Werkzeug is required to use runserver_plus.  Please visit http://werkzeug.pocoo.org/ or install via pip. (pip install Werkzeug)")

        # usurp django's handler
        from django.views import debug
        debug.technical_500_response = null_technical_500_response

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

        threaded = options.get('threaded', True)
        use_reloader = options.get('use_reloader', True)
        open_browser = options.get('open_browser', False)
        cert_path = options.get("cert_path")
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'
        bind_url = "http://%s:%s/" % (
            self.addr if not self._raw_ipv6 else '[%s]' % self.addr, self.port)
        extra_files = options.get('extra_files', None) or []
        reloader_interval = options.get('reloader_interval', 1)

        def inner_run():
            print("Validating models...")
            self.validate(display_num_errors=True)
            print("\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE))
            print("Development server is running at %s" % (bind_url,))
            print("Using the Werkzeug debugger (http://werkzeug.pocoo.org/)")
            print("Quit the server with %s." % quit_command)
            path = options.get('admin_media_path', '')
            if not path:
                admin_media_path = os.path.join(django.__path__[0], 'contrib/admin/static/admin')
                if os.path.isdir(admin_media_path):
                    path = admin_media_path
                else:
                    path = os.path.join(django.__path__[0], 'contrib/admin/media')
            handler = WSGIHandler()
            if USE_ADMINMEDIAHANDLER:
                handler = AdminMediaHandler(handler, path)
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
                    print("Werkzeug version is less than 0.9, trying adhoc certificate.")
                    ssl_context = "adhoc"

            else:
                ssl_context = None

            if use_reloader and settings.USE_I18N:
                try:
                    from django.utils.autoreload import gen_filenames
                except ImportError:
                    pass
                else:
                    extra_files.extend(filter(lambda filename: filename.endswith('.mo'), gen_filenames()))

            run_simple(
                self.addr,
                int(self.port),
                DebuggedApplication(handler, True),
                use_reloader=use_reloader,
                use_debugger=True,
                extra_files=extra_files,
                reloader_interval=reloader_interval,
                threaded=threaded,
                ssl_context=ssl_context,
            )
        inner_run()


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
