# -*- coding: utf-8 -*-
import logging
import os
import re
import socket
import sys
import traceback
import webbrowser
import functools
from pathlib import Path
from typing import List, Set  # NOQA

import django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, SystemCheckError
from django.core.management.color import color_style
from django.core.servers.basehttp import get_internal_wsgi_application
from django.dispatch import Signal
from django.template.autoreload import get_template_directories, reset_loaders
from django.utils.autoreload import file_changed, get_reloader
from django.views import debug as django_views_debug

try:
    if "whitenoise.runserver_nostatic" in settings.INSTALLED_APPS:
        USE_STATICFILES = False
    else:
        from django.contrib.staticfiles.handlers import StaticFilesHandler

        USE_STATICFILES = True
except ImportError:
    USE_STATICFILES = False

try:
    from werkzeug import run_simple
    from werkzeug.debug import DebuggedApplication
    from werkzeug.serving import WSGIRequestHandler as _WSGIRequestHandler
    from werkzeug.serving import make_ssl_devcert
    from werkzeug._internal import _log  # type: ignore
    from werkzeug import _reloader

    HAS_WERKZEUG = True
except ImportError:
    HAS_WERKZEUG = False

try:
    import OpenSSL  # NOQA

    HAS_OPENSSL = True
except ImportError:
    HAS_OPENSSL = False

from django_extensions.management.technical_response import null_technical_500_response
from django_extensions.management.utils import (
    RedirectHandler,
    has_ipdb,
    setup_logger,
    signalcommand,
)
from django_extensions.management.debug_cursor import monkey_patch_cursordebugwrapper


runserver_plus_started = Signal()
naiveip_re = re.compile(
    r"""^(?:
(?P<addr>
    (?P<ipv4>\d{1,3}(?:\.\d{1,3}){3}) |         # IPv4 address
    (?P<ipv6>\[[a-fA-F0-9:]+\]) |               # IPv6 address
    (?P<fqdn>[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*) # FQDN
):)?(?P<port>\d+)$""",
    re.X,
)
# 7-bit C1 ANSI sequences (https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python)
ansi_escape = re.compile(
    r"""
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
""",
    re.VERBOSE,
)
DEFAULT_PORT = "8000"
DEFAULT_POLLER_RELOADER_INTERVAL = getattr(
    settings, "RUNSERVERPLUS_POLLER_RELOADER_INTERVAL", 1
)
DEFAULT_POLLER_RELOADER_TYPE = getattr(
    settings, "RUNSERVERPLUS_POLLER_RELOADER_TYPE", "auto"
)

logger = logging.getLogger(__name__)
_error_files = set()  # type: Set[str]


def get_all_template_files() -> Set[str]:
    template_list = set()

    for template_dir in get_template_directories():
        for base_dir, _, filenames in os.walk(template_dir):
            for filename in filenames:
                template_list.add(os.path.join(base_dir, filename))

    return template_list


if HAS_WERKZEUG:
    # Monkey patch the reloader to support adding more files to extra_files
    for name, reloader_loop_klass in _reloader.reloader_loops.items():

        class WrappedReloaderLoop(reloader_loop_klass):  # type: ignore
            def __init__(self, *args, **kwargs):
                self._template_files: Set[str] = get_all_template_files()
                super().__init__(*args, **kwargs)
                self._extra_files = self.extra_files

            @property
            def extra_files(self):
                template_files = get_all_template_files()

                # reset loaders if there are new files detected
                if len(self._template_files) != len(template_files):
                    changed = template_files.difference(self._template_files)
                    for filename in changed:
                        _log(
                            "info",
                            f" * New file {filename} added, reset template loaders",
                        )
                        self.register_file_changed(filename)

                    reset_loaders()

                self._template_files = template_files

                return self._extra_files.union(_error_files, template_files)

            @extra_files.setter
            def extra_files(self, extra_files):
                self._extra_files = extra_files

            def trigger_reload(self, filename: str) -> None:
                path = Path(filename)
                results = file_changed.send(sender=self, file_path=path)
                if not any(res[1] for res in results):
                    super().trigger_reload(filename)
                else:
                    _log(
                        "info",
                        f" * Detected change in {filename!r}, reset template loaders",
                    )
                    self.register_file_changed(filename)

            def register_file_changed(self, filename):
                if hasattr(self, "mtimes"):
                    mtime = os.stat(filename).st_mtime
                    self.mtimes[filename] = mtime

        _reloader.reloader_loops[name] = WrappedReloaderLoop


def gen_filenames():
    return get_reloader().watched_files()


def check_errors(fn):
    # Inspired by https://github.com/django/django/blob/master/django/utils/autoreload.py
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            _exception = sys.exc_info()

            _, ev, tb = _exception

            if getattr(ev, "filename", None) is None:
                # get the filename from the last item in the stack
                filename = traceback.extract_tb(tb)[-1][0]
            else:
                filename = ev.filename

            if filename not in _error_files:
                _error_files.add(filename)

            raise

    return wrapper


class Command(BaseCommand):
    help = "Starts a lightweight Web server for development."

    # Validation is called explicitly each time the server is reloaded.
    requires_system_checks: List[str] = []
    DEFAULT_CRT_EXTENSION = ".crt"
    DEFAULT_KEY_EXTENSION = ".key"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "addrport", nargs="?", help="Optional port number, or ipaddr:port"
        )
        parser.add_argument(
            "--ipv6",
            "-6",
            action="store_true",
            dest="use_ipv6",
            default=False,
            help="Tells Django to use a IPv6 address.",
        )
        parser.add_argument(
            "--noreload",
            action="store_false",
            dest="use_reloader",
            default=True,
            help="Tells Django to NOT use the auto-reloader.",
        )
        parser.add_argument(
            "--browser",
            action="store_true",
            dest="open_browser",
            help="Tells Django to open a browser.",
        )
        parser.add_argument(
            "--nothreading",
            action="store_false",
            dest="threaded",
            help="Do not run in multithreaded mode.",
        )
        parser.add_argument(
            "--threaded",
            action="store_true",
            dest="threaded",
            help="Run in multithreaded mode.",
        )
        parser.add_argument(
            "--output",
            dest="output_file",
            default=None,
            help="Specifies an output file to send a copy of all messages "
            "(not flushed immediately).",
        )
        parser.add_argument(
            "--print-sql",
            action="store_true",
            default=False,
            help="Print SQL queries as they're executed",
        )
        parser.add_argument(
            "--truncate-sql",
            action="store",
            type=int,
            help="Truncate SQL queries to a number of characters.",
        )
        parser.add_argument(
            "--print-sql-location",
            action="store_true",
            default=False,
            help="Show location in code where SQL query generated from",
        )
        cert_group = parser.add_mutually_exclusive_group()
        cert_group.add_argument(
            "--cert",
            dest="cert_path",
            action="store",
            type=str,
            help="Deprecated alias for --cert-file option.",
        )
        cert_group.add_argument(
            "--cert-file",
            dest="cert_path",
            action="store",
            type=str,
            help="SSL .crt file path. If not provided path from --key-file will be "
            "selected. Either --cert-file or --key-file must be provided to use SSL.",
        )
        parser.add_argument(
            "--key-file",
            dest="key_file_path",
            action="store",
            type=str,
            help="SSL .key file path. If not provided path from --cert-file "
            "will be selected. Either --cert-file or --key-file must be provided "
            "to use SSL.",
        )
        parser.add_argument(
            "--extra-file",
            dest="extra_files",
            action="append",
            type=str,
            default=[],
            help="auto-reload whenever the given file changes too"
            " (can be specified multiple times)",
        )
        parser.add_argument(
            "--exclude-pattern",
            dest="exclude_patterns",
            action="append",
            type=str,
            default=[],
            help="ignore reload on changes to files matching this pattern"
            " (can be specified multiple times)",
        )
        parser.add_argument(
            "--reloader-interval",
            dest="reloader_interval",
            action="store",
            type=int,
            default=DEFAULT_POLLER_RELOADER_INTERVAL,
            help="After how many seconds auto-reload should scan for updates"
            " in poller-mode [default=%s]" % DEFAULT_POLLER_RELOADER_INTERVAL,
        )
        parser.add_argument(
            "--reloader-type",
            dest="reloader_type",
            action="store",
            type=str,
            default=DEFAULT_POLLER_RELOADER_TYPE,
            help="Werkzeug reloader type "
            "[options are auto, watchdog, or stat, default=%s]"
            % DEFAULT_POLLER_RELOADER_TYPE,
        )
        parser.add_argument(
            "--pdb",
            action="store_true",
            dest="pdb",
            default=False,
            help="Drop into pdb shell at the start of any view.",
        )
        parser.add_argument(
            "--ipdb",
            action="store_true",
            dest="ipdb",
            default=False,
            help="Drop into ipdb shell at the start of any view.",
        )
        parser.add_argument(
            "--pm",
            action="store_true",
            dest="pm",
            default=False,
            help="Drop into (i)pdb shell if an exception is raised in a view.",
        )
        parser.add_argument(
            "--startup-messages",
            dest="startup_messages",
            action="store",
            default="reload",
            help="When to show startup messages: "
            "reload [default], once, always, never.",
        )
        parser.add_argument(
            "--keep-meta-shutdown",
            dest="keep_meta_shutdown_func",
            action="store_true",
            default=False,
            help="Keep request.META['werkzeug.server.shutdown'] function which is "
            "automatically removed because Django debug pages tries to call the "
            "function and unintentionally shuts down the Werkzeug server.",
        )
        parser.add_argument(
            "--nopin",
            dest="nopin",
            action="store_true",
            default=False,
            help="Disable the PIN in werkzeug. USE IT WISELY!",
        )

        if USE_STATICFILES:
            parser.add_argument(
                "--nostatic",
                action="store_false",
                dest="use_static_handler",
                default=True,
                help="Tells Django to NOT automatically serve static files.",
            )
            parser.add_argument(
                "--insecure",
                action="store_true",
                dest="insecure_serving",
                default=False,
                help="Allows serving static files even if DEBUG is False.",
            )

    @signalcommand
    def handle(self, *args, **options):
        addrport = options["addrport"]
        startup_messages = options["startup_messages"]
        if startup_messages == "reload":
            self.show_startup_messages = os.environ.get("RUNSERVER_PLUS_SHOW_MESSAGES")
        elif startup_messages == "once":
            self.show_startup_messages = not os.environ.get(
                "RUNSERVER_PLUS_SHOW_MESSAGES"
            )
        elif startup_messages == "never":
            self.show_startup_messages = False
        else:
            self.show_startup_messages = True

        os.environ["RUNSERVER_PLUS_SHOW_MESSAGES"] = "1"

        setup_logger(
            logger, self.stderr, filename=options["output_file"]
        )  # , fmt="[%(name)s] %(message)s")
        logredirect = RedirectHandler(__name__)

        # Redirect werkzeug log items
        werklogger = logging.getLogger("werkzeug")
        werklogger.setLevel(logging.INFO)
        werklogger.addHandler(logredirect)
        werklogger.propagate = False

        pdb_option = options["pdb"]
        ipdb_option = options["ipdb"]
        pm = options["pm"]
        try:
            from django_pdb.middleware import PdbMiddleware
        except ImportError:
            if pdb_option or ipdb_option or pm:
                raise CommandError(
                    "django-pdb is required for --pdb, --ipdb and --pm options. "
                    "Please visit https://pypi.python.org/pypi/django-pdb or install "
                    "via pip. (pip install django-pdb)"
                )
            pm = False
        else:
            # Add pdb middleware if --pdb is specified or if in DEBUG mode
            if pdb_option or ipdb_option or settings.DEBUG:
                middleware = "django_pdb.middleware.PdbMiddleware"
                settings_middleware = (
                    getattr(settings, "MIDDLEWARE", None) or settings.MIDDLEWARE_CLASSES
                )

                if middleware not in settings_middleware:
                    if isinstance(settings_middleware, tuple):
                        settings_middleware += (middleware,)
                    else:
                        settings_middleware += [middleware]

            # If --pdb is specified then always break at the start of views.
            # Otherwise break only if a 'pdb' query parameter is set in the url
            if pdb_option:
                PdbMiddleware.always_break = "pdb"
            elif ipdb_option:
                PdbMiddleware.always_break = "ipdb"

            def postmortem(request, exc_type, exc_value, tb):
                if has_ipdb():
                    import ipdb

                    p = ipdb
                else:
                    import pdb

                    p = pdb
                print(
                    "Exception occured: %s, %s" % (exc_type, exc_value), file=sys.stderr
                )
                p.post_mortem(tb)

        # usurp django's handler
        django_views_debug.technical_500_response = (
            postmortem if pm else null_technical_500_response
        )

        self.use_ipv6 = options["use_ipv6"]
        if self.use_ipv6 and not socket.has_ipv6:
            raise CommandError("Your Python does not support IPv6.")
        self._raw_ipv6 = False
        if not addrport:
            try:
                addrport = settings.RUNSERVERPLUS_SERVER_ADDRESS_PORT
            except AttributeError:
                pass
        if not addrport:
            self.addr = ""
            self.port = DEFAULT_PORT
        else:
            m = re.match(naiveip_re, addrport)
            if m is None:
                raise CommandError(
                    '"%s" is not a valid port number or address:port pair.' % addrport
                )
            self.addr, _ipv4, _ipv6, _fqdn, self.port = m.groups()
            if not self.port.isdigit():
                raise CommandError("%r is not a valid port number." % self.port)
            if self.addr:
                if _ipv6:
                    self.addr = self.addr[1:-1]
                    self.use_ipv6 = True
                    self._raw_ipv6 = True
                elif self.use_ipv6 and not _fqdn:
                    raise CommandError('"%s" is not a valid IPv6 address.' % self.addr)
        if not self.addr:
            self.addr = "::1" if self.use_ipv6 else "127.0.0.1"
            self._raw_ipv6 = True

        truncate = None if options["truncate_sql"] == 0 else options["truncate_sql"]

        with monkey_patch_cursordebugwrapper(
            print_sql=options["print_sql"],
            print_sql_location=options["print_sql_location"],
            truncate=truncate,
            logger=logger.info,
            confprefix="RUNSERVER_PLUS",
        ):
            self.inner_run(options)

    def get_handler(self, *args, **options):
        """Return the default WSGI handler for the runner."""
        return get_internal_wsgi_application()

    def get_error_handler(self, exc, **options):
        def application(env, start_response):
            if isinstance(exc, SystemCheckError):
                error_message = ansi_escape.sub("", str(exc))
                raise SystemCheckError(error_message)

            raise exc

        return application

    def inner_run(self, options):
        if not HAS_WERKZEUG:
            raise CommandError(
                "Werkzeug is required to use runserver_plus. "
                "Please visit https://werkzeug.palletsprojects.com/ or install via pip."
                " (pip install Werkzeug)"
            )

        # Set colored output
        if settings.DEBUG:
            try:
                set_werkzeug_log_color()
            except (
                Exception
            ):  # We are dealing with some internals, anything could go wrong
                if self.show_startup_messages:
                    print(
                        "Wrapping internal werkzeug logger "
                        "for color highlighting has failed!"
                    )

        class WSGIRequestHandler(_WSGIRequestHandler):
            def make_environ(self):
                environ = super().make_environ()
                if (
                    not options["keep_meta_shutdown_func"]
                    and "werkzeug.server.shutdown" in environ
                ):
                    del environ["werkzeug.server.shutdown"]
                remote_user = os.getenv("REMOTE_USER")
                if remote_user is not None:
                    environ["REMOTE_USER"] = remote_user
                return environ

        threaded = options["threaded"]
        use_reloader = options["use_reloader"]
        open_browser = options["open_browser"]
        quit_command = "CONTROL-C" if sys.platform != "win32" else "CTRL-BREAK"
        reloader_interval = options["reloader_interval"]
        reloader_type = options["reloader_type"]
        self.extra_files = set(options["extra_files"])
        exclude_patterns = set(options["exclude_patterns"])

        self.nopin = options["nopin"]

        if self.show_startup_messages:
            print("Performing system checks...\n")

        try:
            check_errors(self.check)(display_num_errors=self.show_startup_messages)
            check_errors(self.check_migrations)()
            handler = check_errors(self.get_handler)(**options)
        except Exception as exc:
            self.stderr.write("Error occurred during checks: %r" % exc, ending="\n\n")
            handler = self.get_error_handler(exc, **options)

        if USE_STATICFILES:
            use_static_handler = options["use_static_handler"]
            insecure_serving = options["insecure_serving"]
            if use_static_handler and (settings.DEBUG or insecure_serving):
                handler = StaticFilesHandler(handler)

        if options["cert_path"] or options["key_file_path"]:
            if not HAS_OPENSSL:
                raise CommandError(
                    "Python OpenSSL Library is "
                    "required to use runserver_plus with ssl support. "
                    "Install via pip (pip install pyOpenSSL)."
                )

            certfile, keyfile = self.determine_ssl_files_paths(options)
            dir_path, root = os.path.split(certfile)
            root, _ = os.path.splitext(root)
            try:
                if os.path.exists(certfile) and os.path.exists(keyfile):
                    ssl_context = (certfile, keyfile)
                else:  # Create cert, key files ourselves.
                    ssl_context = make_ssl_devcert(
                        os.path.join(dir_path, root), host="localhost"
                    )
            except ImportError:
                if self.show_startup_messages:
                    print(
                        "Werkzeug version is less than 0.9, trying adhoc certificate."
                    )
                ssl_context = "adhoc"
        else:
            ssl_context = None

        bind_url = "%s://%s:%s/" % (
            "https" if ssl_context else "http",
            self.addr if not self._raw_ipv6 else "[%s]" % self.addr,
            self.port,
        )

        if self.show_startup_messages:
            print(
                "\nDjango version %s, using settings %r"
                % (django.get_version(), settings.SETTINGS_MODULE)
            )
            print("Development server is running at %s" % (bind_url,))
            print("Using the Werkzeug debugger (https://werkzeug.palletsprojects.com/)")
            print("Quit the server with %s." % quit_command)

        if open_browser:
            webbrowser.open(bind_url)

        if use_reloader and settings.USE_I18N:
            self.extra_files |= set(
                filter(lambda filename: str(filename).endswith(".mo"), gen_filenames())
            )

        if getattr(settings, "RUNSERVER_PLUS_EXTRA_FILES", []):
            self.extra_files |= set(settings.RUNSERVER_PLUS_EXTRA_FILES)

        exclude_patterns |= set(
            getattr(settings, "RUNSERVER_PLUS_EXCLUDE_PATTERNS", [])
        )

        # Werkzeug needs to be clued in its the main instance if running
        # without reloader or else it won't show key.
        # https://git.io/vVIgo
        if not use_reloader:
            os.environ["WERKZEUG_RUN_MAIN"] = "true"

        # Don't run a second instance of the debugger / reloader
        # See also: https://github.com/django-extensions/django-extensions/issues/832
        if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            if self.nopin:
                os.environ["WERKZEUG_DEBUG_PIN"] = "off"
            handler = DebuggedApplication(handler, True)

        runserver_plus_started.send(sender=self)
        run_simple(
            self.addr,
            int(self.port),
            handler,
            use_reloader=use_reloader,
            use_debugger=True,
            extra_files=self.extra_files,
            exclude_patterns=exclude_patterns,
            reloader_interval=reloader_interval,
            reloader_type=reloader_type,
            threaded=threaded,
            request_handler=WSGIRequestHandler,
            ssl_context=ssl_context,
        )

    @classmethod
    def determine_ssl_files_paths(cls, options):
        key_file_path = os.path.expanduser(options.get("key_file_path") or "")
        cert_path = os.path.expanduser(options.get("cert_path") or "")
        cert_file = cls._determine_path_for_file(
            cert_path, key_file_path, cls.DEFAULT_CRT_EXTENSION
        )
        key_file = cls._determine_path_for_file(
            key_file_path, cert_path, cls.DEFAULT_KEY_EXTENSION
        )
        return cert_file, key_file

    @classmethod
    def _determine_path_for_file(
        cls, current_file_path, other_file_path, expected_extension
    ):
        directory = cls._get_directory_basing_on_file_paths(
            current_file_path, other_file_path
        )
        file_name = cls._get_file_name(current_file_path) or cls._get_file_name(
            other_file_path
        )
        extension = cls._get_extension(current_file_path) or expected_extension
        return os.path.join(directory, file_name + extension)

    @classmethod
    def _get_directory_basing_on_file_paths(cls, current_file_path, other_file_path):
        return (
            cls._get_directory(current_file_path)
            or cls._get_directory(other_file_path)
            or os.getcwd()
        )

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
    _style = color_style()
    _orig_log = _WSGIRequestHandler.log

    def werk_log(self, type, message, *args):
        try:
            msg = "%s - - [%s] %s" % (
                self.address_string(),
                self.log_date_time_string(),
                message % args,
            )
            http_code = str(args[1])
        except Exception:
            return _orig_log(type, message, *args)

        # Utilize terminal colors, if available
        if http_code[0] == "2":
            # Put 2XX first, since it should be the common case
            msg = _style.HTTP_SUCCESS(msg)
        elif http_code[0] == "1":
            msg = _style.HTTP_INFO(msg)
        elif http_code == "304":
            msg = _style.HTTP_NOT_MODIFIED(msg)
        elif http_code[0] == "3":
            msg = _style.HTTP_REDIRECT(msg)
        elif http_code == "404":
            msg = _style.HTTP_NOT_FOUND(msg)
        elif http_code[0] == "4":
            msg = _style.HTTP_BAD_REQUEST(msg)
        else:
            # Any 5XX, or any other response
            msg = _style.HTTP_SERVER_ERROR(msg)

        _log(type, msg)

    _WSGIRequestHandler.log = werk_log
