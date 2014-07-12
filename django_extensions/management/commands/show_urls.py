import re
import functools
from optparse import make_option

from django.conf import settings
from django.core.exceptions import ViewDoesNotExist
from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.core.management.base import BaseCommand, CommandError
from django.contrib.admindocs.views import simplify_regex
from django.utils.translation import activate

from django_extensions.management.color import color_style


FMTR = {
    'dense': "%(url)s\t%(module)s.%(name)s\t%(url_name)s\t%(decorator)s",
    'verbose': "%(url)s\n\tController: %(module)s.%(name)s\n\tURL Name: %(url_name)s\n\tDecorators: %(decorator)s\n",
}


def extract_views_from_urlpatterns(urlpatterns, base=''):
    """
    Return a list of views from a list of urlpatterns.

    Each object in the returned list is a two-tuple: (view_func, regex)
    """
    views = []
    for p in urlpatterns:
        if isinstance(p, RegexURLPattern):
            try:
                views.append((p.callback, base + p.regex.pattern, p.name))
            except ViewDoesNotExist:
                continue
        elif isinstance(p, RegexURLResolver):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            views.extend(extract_views_from_urlpatterns(patterns, base + p.regex.pattern))
        elif hasattr(p, '_get_callback'):
            try:
                views.append((p._get_callback(), base + p.regex.pattern, p.name))
            except ViewDoesNotExist:
                continue
        elif hasattr(p, 'url_patterns') or hasattr(p, '_get_url_patterns'):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            views.extend(extract_views_from_urlpatterns(patterns, base + p.regex.pattern))
        else:
            raise TypeError("%s does not appear to be a urlpattern object" % p)
    return views


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--unsorted", "-u", action="store_true", dest="unsorted",
                    help="Show urls unsorted but same order as found in url patterns"),
        make_option("--language", "-l", dest="language",
                    help="Set the language code (useful for i18n_patterns)"),
        make_option("--decorator", "-d", dest="decorator",
                    help="Show the presence of given decorator on views"),
        make_option("--format", "-f", dest="format_style",
                    help="Style of the output. Choices: %s" % FMTR.keys())
    )

    help = "Displays all of the url matching routes for the project."

    requires_model_validation = True

    def handle(self, *args, **options):
        if args:
            appname, = args

        style = color_style()

        if settings.ADMIN_FOR:
            settings_modules = [__import__(m, {}, {}, ['']) for m in settings.ADMIN_FOR]
        else:
            settings_modules = [settings]

        language = options.get('language', None)
        if language is not None:
            activate(language)

        decorator = options.get('decorator')
        if decorator is None:
            decorator = 'login_required'

        format_style = options.get('format_style')
        if format_style is None:
            format_style = 'dense'
        if format_style not in FMTR:
            raise CommandError("Format style '%s' does not exist. Options: %s" % (format_style, FMTR.keys()))
        fmtr = FMTR[format_style]

        views = []
        for settings_mod in settings_modules:
            try:
                urlconf = __import__(settings_mod.ROOT_URLCONF, {}, {}, [''])
            except Exception as e:
                if options.get('traceback', None):
                    import traceback
                    traceback.print_exc()
                print(style.ERROR("Error occurred while trying to load %s: %s" % (settings_mod.ROOT_URLCONF, str(e))))
                continue

            view_functions = extract_views_from_urlpatterns(urlconf.urlpatterns)
            for (func, regex, url_name) in view_functions:

                if hasattr(func, '__globals__'):
                    func_globals = func.__globals__
                elif hasattr(func, 'func_globals'):
                    func_globals = func.func_globals
                else:
                    func_globals = {}

                decorators = [decorator] if decorator in func_globals else []

                if isinstance(func, functools.partial):
                    func = func.func
                    decorators.insert(0, 'functools.partial')

                if hasattr(func, '__name__'):
                    func_name = func.__name__
                elif hasattr(func, '__class__'):
                    func_name = '%s()' % func.__class__.__name__
                else:
                    func_name = re.sub(r' at 0x[0-9a-f]+', '', repr(func))

                views.append(fmtr % {
                    'name': style.MODULE_NAME(func_name),
                    'module': style.MODULE(func.__module__),
                    'url_name': style.URL_NAME(url_name or ''),
                    'url': style.URL(simplify_regex(regex)),
                    'decorator': ', '.join(decorators),
                })

        if not options.get('unsorted', False):
            views = sorted(views)

        return "\n".join([v for v in views]) + "\n"
