# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
import os
import re
import socket
import sys

import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.core.servers.basehttp import get_internal_wsgi_application
try:
    from django.utils.autoreload import gen_filenames
except ImportError:  # Django >=2.2
    from django.utils.autoreload import get_reloader

    def gen_filenames():
        return get_reloader().watched_files()

try:
    if 'whitenoise.runserver_nostatic' in settings.INSTALLED_APPS:
        USE_STATICFILES = False
    else:
        from django.contrib.staticfiles.handlers import StaticFilesHandler
        USE_STATICFILES = True
except ImportError:
    USE_STATICFILES = False

from django_extensions.management.technical_response import null_technical_500_response
from django_extensions.management.utils import RedirectHandler, has_ipdb, setup_logger, signalcommand
from django_extensions.management.debug_cursor import monkey_patch_cursordebugwrapper


naiveip_re = re.compile(r"""^(?:
(?P<addr>
    (?P<ipv4>\d{1,3}(?:\.\d{1,3}){3}) |         # IPv4 address
    (?P<ipv6>\[[a-fA-F0-9:]+\]) |               # IPv6 address
    (?P<fqdn>[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*) # FQDN
):)?(?P<port>\d+)$""", re.X)
DEFAULT_PORT = "8000"
DEFAULT_POLLER_RELOADER_INTERVAL = getattr(settings, 'RUNSERVERPLUS_POLLER_RELOADER_INTERVAL', 1)
DEFAULT_POLLER_RELOADER_TYPE = getattr(settings, 'RUNSERVERPLUS_POLLER_RELOADER_TYPE', 'auto')

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Starts a lightweight Web server for development."

    # Validation is called explicitly each time the server is reloaded.
    requires_system_checks = False
    DEFAULT_CRT_EXTENSION = ".crt"
    DEFAULT_KEY_EXTENSION = ".key"

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
        parser.add_argument('--print-sql-location', action='store_true', default=False,
                            help="Show location in code where SQL query generated from")
        cert_group = parser.add_mutually_exclusive_group()
        cert_group.add_argument('--cert', dest='cert_path', action="store", type=str,
                                help='Deprecated alias for --cert-file option.')
        cert_group.add_argument('--cert-file', dest='cert_path', action="store", type=str,
                                help='SSL .crt file path. If not provided path from --key-file will be selected. '
                                     'Either --cert-file or --key-file must be provided to use SSL.')
        parser.add_argument('--key-file', dest='key_file_path', action="store", type=str,
                            help='SSL .key file path. If not provided path from --cert-file will be selected. '
                                 'Either --cert-file or --key-file must be provided to use SSL.')
        parser.add_argument('--extra-file', dest='extra_files', action="append", type=str, default=[],
                            help='auto-reload whenever the given file changes too (can be specified multiple times)')
        parser.add_argument('--reloader-interval', dest='reloader_interval', action="store", type=int, default=DEFAULT_POLLER_RELOADER_INTERVAL,
                            help='After how many seconds auto-reload should scan for updates in poller-mode [default=%s]' % DEFAULT_POLLER_RELOADER_INTERVAL)
        parser.add_argument('--reloader-type', dest='reloader_type', action="store", type=str, default=DEFAULT_POLLER_RELOADER_TYPE,
                            help='Werkzeug reloader type [options are auto, watchdog, or stat, default=%s]' % DEFAULT_POLLER_RELOADER_TYPE)
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
        addrport = options['addrport']
        startup_messages = options['startup_messages']
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

        setup_logger(logger, self.stderr, filename=options['output_file'])  # , fmt="[%(name)s] %(message)s")
        logredirect = RedirectHandler(__name__)

        # Redirect werkzeug log items
        werklogger = logging.getLogger('werkzeug')
        werklogger.setLevel(logging.INFO)
        werklogger.addHandler(logredirect)
        werklogger.propagate = False

        pdb_option = options['pdb']
        ipdb_option = options['ipdb']
        pm = options['pm']
        try:
            from django_pdb.middleware import PdbMiddleware
        except ImportError:
            if pdb_option or ipdb_option or pm:
                raise CommandError("django-pdb is required for --pdb, --ipdb and --pm options. Please visit https://pypi.python.org/pypi/django-pdb or install via pip. (pip install django-pdb)")
            pm = False
        else:
            # Add pdb middleware if --pdb is specified or if in DEBUG mode
            if (pdb_option or ipdb_option or settings.DEBUG):
                middleware = 'django_pdb.middleware.PdbMiddleware'
                settings_middleware = getattr(settings, 'MIDDLEWARE', None) or settings.MIDDLEWARE_CLASSES

                if middleware not in settings_middleware:
                    if isinstance(settings_middleware, tuple):
                        settings_middleware += (middleware,)
                    else:
                        settings_middleware += [middleware]

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
                print("Exception occured: %s, %s" % (exc_type, exc_value), file=sys.stderr)
                p.post_mortem(tb)

        # usurp django's handler
        from django.views import debug
        debug.technical_500_response = postmortem if pm else null_technical_500_response

        self.use_ipv6 = options['use_ipv6']
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
            self._raw_ipv6 = True

        with monkey_patch_cursordebugwrapper(print_sql=options["print_sql"], print_sql_location=options["print_sql_location"], logger=logger.info, confprefix="RUNSERVER_PLUS"):
            self.inner_run(options)

    def inner_run(self, options):
        try:
            from werkzeug import run_simple
            from werkzeug.debug import DebuggedApplication
            from werkzeug.serving import WSGIRequestHandler as _WSGIRequestHandler

            # Set colored output
            if settings.DEBUG:
                try:
                    set_werkzeug_log_color()
                except Exception:  # We are dealing with some internals, anything could go wrong
                    if self.show_startup_messages:
                        print("Wrapping internal werkzeug logger for color highlighting has failed!")
                    pass

        except ImportError:
            raise CommandError("Werkzeug is required to use runserver_plus.  Please visit http://werkzeug.pocoo.org/ or install via pip. (pip install Werkzeug)")

        class WSGIRequestHandler(_WSGIRequestHandler):
            def make_environ(self):
                environ = super(WSGIRequestHandler, self).make_environ()
                if not options['keep_meta_shutdown_func']:
                    del environ['werkzeug.server.shutdown']
                return environ

        threaded = options['threaded']
        use_reloader = options['use_reloader']
        open_browser = options['open_browser']
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'
        extra_files = options['extra_files']
        reloader_interval = options['reloader_interval']
        reloader_type = options['reloader_type']

        self.nopin = options['nopin']

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
        handler = get_internal_wsgi_application()
        if USE_STATICFILES:
            use_static_handler = options['use_static_handler']
            insecure_serving = options['insecure_serving']
            if use_static_handler and (settings.DEBUG or insecure_serving):
                handler = StaticFilesHandler(handler)
        if options["cert_path"] or options["key_file_path"]:
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

            certfile, keyfile = self.determine_ssl_files_paths(options)
            dir_path, root = os.path.split(certfile)
            root, _ = os.path.splitext(root)
            try:
                from werkzeug.serving import make_ssl_devcert
                if os.path.exists(certfile) and os.path.exists(keyfile):
                    ssl_context = (certfile, keyfile)
                else:  # Create cert, key files ourselves.
                    ssl_context = make_ssl_devcert(os.path.join(dir_path, root), host='localhost')
            except ImportError:
                if self.show_startup_messages:
                    print("Werkzeug version is less than 0.9, trying adhoc certificate.")
                ssl_context = "adhoc"

        else:
            ssl_context = None

        bind_url = "%s://%s:%s/" % (
            "https" if ssl_context else "http", self.addr if not self._raw_ipv6 else '[%s]' % self.addr, self.port)

        if self.show_startup_messages:
            print("\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE))
            print("Development server is running at %s" % (bind_url,))
            print("Using the Werkzeug debugger (http://werkzeug.pocoo.org/)")
            print("Quit the server with %s." % quit_command)

        if open_browser:
            import webbrowser
            webbrowser.open(bind_url)

        if use_reloader and settings.USE_I18N:
            extra_files.extend(filter(lambda filename: str(filename).endswith('.mo'), gen_filenames()))

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
            reloader_type=reloader_type,
            threaded=threaded,
            request_handler=WSGIRequestHandler,
            ssl_context=ssl_context,
        )

    @classmethod
    def determine_ssl_files_paths(cls, options):
        key_file_path = options.get('key_file_path') or ""
        cert_path = options.get('cert_path') or ""
        cert_file = cls._determine_path_for_file(cert_path, key_file_path, cls.DEFAULT_CRT_EXTENSION)
        key_file = cls._determine_path_for_file(key_file_path, cert_path, cls.DEFAULT_KEY_EXTENSION)
        return cert_file, key_file

    @classmethod
    def _determine_path_for_file(cls, current_file_path, other_file_path, expected_extension):
        directory = cls._get_directory_basing_on_file_paths(current_file_path, other_file_path)
        file_name = cls._get_file_name(current_file_path) or cls._get_file_name(other_file_path)
        extension = cls._get_extension(current_file_path) or expected_extension
        return os.path.join(directory, file_name + extension)

    @classmethod
    def _get_directory_basing_on_file_paths(cls, current_file_path, other_file_path):
        return cls._get_directory(current_file_path) or cls._get_directory(other_file_path) or os.getcwd()

    @classmethod
    def _get_directory(cls, file_path):
        return os.path.split(file_path)[0]

    @classmethod
    def _get_file_name(cls, file_path):
        return os.path.splitext(os.path.split(file_path)[1])[0]

    @classmethod
    def _get_extension(cls, file_path):
        return os.path.splitext(file_path)[1]


def set_werkzeug_log_color():
    """Try to set color to the werkzeug log."""
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
        except Exception:
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
