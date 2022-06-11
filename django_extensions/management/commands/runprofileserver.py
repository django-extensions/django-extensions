# -*- coding: utf-8 -*-
"""
runprofileserver.py

    Starts a lightweight Web server with profiling enabled.

Credits for kcachegrind support taken from lsprofcalltree.py go to:
 David Allouche
 Jp Calderone & Itamar Shtull-Trauring
 Johan Dahlin
"""

import sys
from datetime import datetime

from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management.base import BaseCommand, CommandError
from django.core.servers.basehttp import get_internal_wsgi_application

from django_extensions.management.utils import signalcommand

USE_STATICFILES = 'django.contrib.staticfiles' in settings.INSTALLED_APPS


class KCacheGrind:
    def __init__(self, profiler):
        self.data = profiler.getstats()
        self.out_file = None

    def output(self, out_file):
        self.out_file = out_file
        self.out_file.write('events: Ticks\n')
        self._print_summary()
        for entry in self.data:
            self._entry(entry)

    def _print_summary(self):
        max_cost = 0
        for entry in self.data:
            totaltime = int(entry.totaltime * 1000)
            max_cost = max(max_cost, totaltime)
        self.out_file.write('summary: %d\n' % (max_cost,))

    def _entry(self, entry):
        out_file = self.out_file

        code = entry.code
        if isinstance(code, str):
            out_file.write('fn=%s\n' % code)
        else:
            out_file.write('fl=%s\n' % code.co_filename)
            out_file.write('fn=%s\n' % code.co_name)

        inlinetime = int(entry.inlinetime * 1000)
        if isinstance(code, str):
            out_file.write('0  %s\n' % inlinetime)
        else:
            out_file.write('%d %d\n' % (code.co_firstlineno, inlinetime))

        # recursive calls are counted in entry.calls
        if entry.calls:
            calls = entry.calls
        else:
            calls = []

        if isinstance(code, str):
            lineno = 0
        else:
            lineno = code.co_firstlineno

        for subentry in calls:
            self._subentry(lineno, subentry)
        out_file.write("\n")

    def _subentry(self, lineno, subentry):
        out_file = self.out_file
        code = subentry.code
        if isinstance(code, str):
            out_file.write('cfn=%s\n' % code)
            out_file.write('calls=%d 0\n' % (subentry.callcount,))
        else:
            out_file.write('cfl=%s\n' % code.co_filename)
            out_file.write('cfn=%s\n' % code.co_name)
            out_file.write('calls=%d %d\n' % (subentry.callcount, code.co_firstlineno))

        totaltime = int(subentry.totaltime * 1000)
        out_file.write('%d %d\n' % (lineno, totaltime))


class Command(BaseCommand):
    help = "Starts a lightweight Web server with profiling enabled."
    args = '[optional port number, or ipaddr:port]'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            'addrport', nargs='?',
            help='Optional port number, or ipaddr:port'
        )
        parser.add_argument(
            '--noreload', action='store_false', dest='use_reloader',
            default=True,
            help='Tells Django to NOT use the auto-reloader.')
        parser.add_argument(
            '--nothreading', action='store_false', dest='use_threading', default=True,
            help='Tells Django to NOT use threading.',
        )
        parser.add_argument(
            '--prof-path', dest='prof_path', default='/tmp',
            help='Specifies the directory which to save profile information '
            'in.'
        )
        parser.add_argument(
            '--prof-file', dest='prof_file',
            default='{path}.{duration:06d}ms.{time}',
            help='Set filename format, default if '
            '"{path}.{duration:06d}ms.{time}".'
        )
        parser.add_argument(
            '--nomedia', action='store_true', dest='no_media', default=False,
            help='Do not profile MEDIA_URL'
        )
        parser.add_argument(
            '--use-cprofile', action='store_true', dest='use_cprofile',
            default=False,
            help='Use cProfile if available, this is disabled per default '
            'because of incompatibilities.'
        )
        parser.add_argument(
            '--kcachegrind', action='store_true', dest='use_lsprof',
            default=False,
            help='Create kcachegrind compatible lsprof files, this requires '
            'and automatically enables cProfile.'
        )

        if USE_STATICFILES:
            parser.add_argument(
                '--nostatic', action="store_false", dest='use_static_handler',
                default=True,
                help='Tells Django to NOT automatically serve static files '
                'at STATIC_URL.')
            parser.add_argument(
                '--insecure', action="store_true", dest='insecure_serving',
                default=False,
                help='Allows serving static files even if DEBUG is False.')

    @signalcommand
    def handle(self, addrport='', *args, **options):
        import django
        import socket
        import errno
        from django.core.servers.basehttp import run

        if not addrport:
            addr = ''
            port = '8000'
        else:
            try:
                addr, port = addrport.split(':')
            except ValueError:
                addr, port = '', addrport
        if not addr:
            addr = '127.0.0.1'

        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)

        use_reloader = options['use_reloader']
        shutdown_message = options.get('shutdown_message', '')
        no_media = options['no_media']
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        def inner_run():
            import os
            import time
            try:
                import hotshot
                HAS_HOTSHOT = True
            except ImportError:
                HAS_HOTSHOT = False  # python 3.x
            USE_CPROFILE = options['use_cprofile']
            USE_LSPROF = options['use_lsprof']
            if USE_LSPROF:
                USE_CPROFILE = True
            if USE_CPROFILE:
                try:
                    import cProfile
                    USE_CPROFILE = True
                except ImportError:
                    print("cProfile disabled, module cannot be imported!")
                    USE_CPROFILE = False
            if USE_LSPROF and not USE_CPROFILE:
                raise CommandError("Kcachegrind compatible output format required cProfile from Python 2.5")

            if not HAS_HOTSHOT and not USE_CPROFILE:
                raise CommandError("Hotshot profile library not found. (and not using cProfile)")

            prof_path = options['prof_path']

            prof_file = options['prof_file']
            if not prof_file.format(path='1', duration=2, time=3):
                prof_file = '{path}.{duration:06d}ms.{time}'
                print("Filename format is wrong. Default format used: '{path}.{duration:06d}ms.{time}'.")

            def get_exclude_paths():
                exclude_paths = []
                media_url = getattr(settings, 'MEDIA_URL', None)
                if media_url:
                    exclude_paths.append(media_url)
                static_url = getattr(settings, 'STATIC_URL', None)
                if static_url:
                    exclude_paths.append(static_url)
                return exclude_paths

            def make_profiler_handler(inner_handler):
                def handler(environ, start_response):
                    path_info = environ['PATH_INFO']
                    # when using something like a dynamic site middleware is could be necessary
                    # to refetch the exclude_paths every time since they could change per site.
                    if no_media and any(path_info.startswith(p) for p in get_exclude_paths()):
                        return inner_handler(environ, start_response)
                    path_name = path_info.strip("/").replace('/', '.') or "root"
                    profname = "%s.%d.prof" % (path_name, time.time())
                    profname = os.path.join(prof_path, profname)
                    if USE_CPROFILE:
                        prof = cProfile.Profile()
                    else:
                        prof = hotshot.Profile(profname)
                    start = datetime.now()
                    try:
                        return prof.runcall(inner_handler, environ, start_response)
                    finally:
                        # seeing how long the request took is important!
                        elap = datetime.now() - start
                        elapms = elap.seconds * 1000.0 + elap.microseconds / 1000.0
                        if USE_LSPROF:
                            kg = KCacheGrind(prof)
                            with open(profname, 'w') as f:
                                kg.output(f)
                        elif USE_CPROFILE:
                            prof.dump_stats(profname)
                        profname2 = prof_file.format(path=path_name, duration=int(elapms), time=int(time.time()))
                        profname2 = os.path.join(prof_path, "%s.prof" % profname2)
                        if not USE_CPROFILE:
                            prof.close()
                        os.rename(profname, profname2)
                return handler

            print("Performing system checks...")
            self.check(display_num_errors=True)

            print("\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE))
            print("Development server is running at http://%s:%s/" % (addr, port))
            print("Quit the server with %s." % quit_command)
            try:
                handler = get_internal_wsgi_application()
                if USE_STATICFILES:
                    use_static_handler = options['use_static_handler']
                    insecure_serving = options['insecure_serving']
                    if use_static_handler and (settings.DEBUG or insecure_serving):
                        handler = StaticFilesHandler(handler)
                handler = make_profiler_handler(handler)
                run(addr, int(port), handler, threading=options['use_threading'])
            except socket.error as e:
                # Use helpful error messages instead of ugly tracebacks.
                ERRORS = {
                    errno.EACCES: "You don't have permission to access that port.",
                    errno.EADDRINUSE: "That port is already in use.",
                    errno.EADDRNOTAVAIL: "That IP address can't be assigned-to.",
                }
                try:
                    error_text = ERRORS[e.errno]
                except (AttributeError, KeyError):
                    error_text = str(e)
                sys.stderr.write(self.style.ERROR("Error: %s" % error_text) + '\n')
                # Need to use an OS exit because sys.exit doesn't work in a thread
                os._exit(1)
            except KeyboardInterrupt:
                if shutdown_message:
                    print(shutdown_message)
                sys.exit(0)
        if use_reloader:
            try:
                from django.utils.autoreload import run_with_reloader
                run_with_reloader(inner_run)
            except ImportError:
                from django.utils import autoreload
                autoreload.main(inner_run)
        else:
            inner_run()
