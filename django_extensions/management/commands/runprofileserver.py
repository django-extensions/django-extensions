from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import os
import sys

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noreload', action='store_false', dest='use_reloader', default=True,
            help='Tells Django to NOT use the auto-reloader.'),
        make_option('--adminmedia', dest='admin_media_path', default='',
            help='Specifies the directory from which to serve admin media.'),
        make_option('--prof-path', dest='prof_path', default='/tmp',
            help='Specifies the directory which to save profile information in.'),
        make_option('--nomedia', action='store_true', dest='no_media', default=False,
            help='Do not profile MEDIA_URL and ADMIN_MEDIA_URL'),
        make_option('--use-cprofile', action='store_true', dest='use_cprofile', default=False,
            help='Use cProfile if available, this is disabled per default because of incompatibilities.'),
    )
    help = "Starts a lightweight Web server for development."
    args = '[optional port number, or ipaddr:port]'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def handle(self, addrport='', *args, **options):
        import django
        from django.core.servers.basehttp import run, AdminMediaHandler, WSGIServerException
        from django.core.handlers.wsgi import WSGIHandler
        if args:
            raise CommandError('Usage is runserver %s' % self.args)
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

        use_reloader = options.get('use_reloader', True)
        admin_media_path = options.get('admin_media_path', '')
        shutdown_message = options.get('shutdown_message', '')
        no_media = options.get('no_media', False)
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        def inner_run():
            from django.conf import settings

            import hotshot, time, os
            if options.get('use_cprofile', False):
                try:
                    import cProfile
                    USE_CPROFILE = True
                except ImportError:
                    USE_CPROFILE = False
            else:
                USE_CPROFILE = False
            prof_path = options.get('prof_path', '/tmp')
            def make_profiler_handler(inner_handler):
                def handler(environ, start_response):
                    path_info = environ['PATH_INFO']
                    # normally /media/ is MEDIA_URL, but in case still check it in case it's differently
                    # should be hardly a penalty since it's an OR expression.
                    # TODO: fix this to check the configuration settings and not make assumpsions about where media are on the url
                    if no_media and (path_info.startswith('/media') or path_info.startswith(settings.MEDIA_URL)):
                        return inner_handler(environ, start_response)
                    path_name = path_info.strip("/").replace('/', '.') or "root"
                    profname = "%s.%.3f.prof" % (path_name, time.time())
                    profname = os.path.join(prof_path, profname)
                    if USE_CPROFILE:
                        prof = cProfile.Profile()
                    else:
                        prof = hotshot.Profile(profname)
                    try:
                        return prof.runcall(inner_handler, environ, start_response)
                    finally:
                        if USE_CPROFILE:
                            prof.dump_stats(profname)
                return handler

            print "Validating models..."
            self.validate(display_num_errors=True)
            print "\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE)
            print "Development server is running at http://%s:%s/" % (addr, port)
            print "Quit the server with %s." % quit_command
            try:
                path = admin_media_path or django.__path__[0] + '/contrib/admin/media'
                handler = make_profiler_handler(AdminMediaHandler(WSGIHandler(), path))
                run(addr, int(port), handler)
            except WSGIServerException, e:
                # Use helpful error messages instead of ugly tracebacks.
                ERRORS = {
                    13: "You don't have permission to access that port.",
                    98: "That port is already in use.",
                    99: "That IP address can't be assigned-to.",
                }
                try:
                    error_text = ERRORS[e.args[0].args[0]]
                except (AttributeError, KeyError):
                    error_text = str(e)
                sys.stderr.write(self.style.ERROR("Error: %s" % error_text) + '\n')
                # Need to use an OS exit because sys.exit doesn't work in a thread
                os._exit(1)
            except KeyboardInterrupt:
                if shutdown_message:
                    print shutdown_message
                sys.exit(0)
        if use_reloader:
            from django.utils import autoreload
            autoreload.main(inner_run)
        else:
            inner_run()
