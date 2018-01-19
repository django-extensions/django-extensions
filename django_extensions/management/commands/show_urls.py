# -*- coding: utf-8 -*-
import functools
import json
import re

import django
from django.conf import settings
from django.contrib.admindocs.views import simplify_regex
from django.core.exceptions import ViewDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.utils import translation

from django_extensions.management.color import color_style, no_style
from django_extensions.management.utils import signalcommand

if django.VERSION >= (2, 0):
    from django.urls import URLPattern, URLResolver  # type: ignore

    class RegexURLPattern:  # type: ignore
        pass

    class RegexURLResolver:  # type: ignore
        pass

    class LocaleRegexURLResolver:  # type: ignore
        pass

    def describe_pattern(p):
        return str(p.pattern)
else:
    try:
        from django.urls import RegexURLPattern, RegexURLResolver, LocaleRegexURLResolver  # type: ignore
    except ImportError:
        from django.core.urlresolvers import RegexURLPattern, RegexURLResolver, LocaleRegexURLResolver  # type: ignore

    class URLPattern:  # type: ignore
        pass

    class URLResolver:  # type: ignore
        pass

    def describe_pattern(p):
        return p.regex.pattern

FMTR = {
    'dense': "{url}\t{module}\t{url_name}\t{decorator}",
    'table': "{url},{module},{url_name},{decorator}",
    'aligned': "{url},{module},{url_name},{decorator}",
    'verbose': "{url}\n\tController: {module}\n\tURL Name: {url_name}\n\tDecorators: {decorator}\n",
    'json': '',
    'pretty-json': ''
}


class Command(BaseCommand):
    help = "Displays all of the url matching routes for the project."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--unsorted", "-u", action="store_true", dest="unsorted",
            help="Show urls unsorted but same order as found in url patterns")
        parser.add_argument(
            "--language", "-l", dest="language",
            help="Only show this language code (useful for i18n_patterns)")
        parser.add_argument(
            "--decorator", "-d", action="append", dest="decorator", default=[],
            help="Show the presence of given decorator on views")
        parser.add_argument(
            "--format", "-f", dest="format_style", default="dense",
            help="Style of the output. Choices: %s" % FMTR.keys())
        parser.add_argument(
            "--urlconf", "-c", dest="urlconf", default="ROOT_URLCONF",
            help="Set the settings URL conf variable to use")

    @signalcommand
    def handle(self, *args, **options):
        if args:
            appname, = args

        if options.get('no_color', False):
            style = no_style()
        else:
            style = color_style()

        if getattr(settings, 'ADMIN_FOR', None):
            settings_modules = [__import__(m, {}, {}, ['']) for m in settings.ADMIN_FOR]
        else:
            settings_modules = [settings]

        self.LANGUAGES = getattr(settings, 'LANGUAGES', ((None, None), ))

        language = options.get('language', None)
        if language is not None:
            translation.activate(language)
            self.LANGUAGES = [(code, name) for code, name in self.LANGUAGES if code == language]

        decorator = options.get('decorator')
        if not decorator:
            decorator = ['login_required']

        format_style = options.get('format_style')
        if format_style not in FMTR:
            raise CommandError("Format style '%s' does not exist. Options: %s" % (format_style, FMTR.keys()))
        pretty_json = format_style == 'pretty-json'
        if pretty_json:
            format_style = 'json'
        fmtr = FMTR[format_style]

        urlconf = options.get('urlconf')

        views = []
        for settings_mod in settings_modules:
            if not hasattr(settings_mod, urlconf):
                raise CommandError("Settings module {} does not have the attribute {}.".format(settings_mod, urlconf))

            try:
                urlconf = __import__(getattr(settings_mod, urlconf), {}, {}, [''])
            except Exception as e:
                if options.get('traceback', None):
                    import traceback
                    traceback.print_exc()
                print(style.ERROR("Error occurred while trying to load %s: %s" % (getattr(settings_mod, urlconf), str(e))))
                continue

            view_functions = self.extract_views_from_urlpatterns(urlconf.urlpatterns)
            for (func, regex, url_name) in view_functions:
                if hasattr(func, '__globals__'):
                    func_globals = func.__globals__
                elif hasattr(func, 'func_globals'):
                    func_globals = func.func_globals
                else:
                    func_globals = {}

                decorators = [d for d in decorator if d in func_globals]

                if isinstance(func, functools.partial):
                    func = func.func
                    decorators.insert(0, 'functools.partial')

                if hasattr(func, '__name__'):
                    func_name = func.__name__
                elif hasattr(func, '__class__'):
                    func_name = '%s()' % func.__class__.__name__
                else:
                    func_name = re.sub(r' at 0x[0-9a-f]+', '', repr(func))

                module = '{0}.{1}'.format(func.__module__, func_name)
                url_name = url_name or ''
                url = simplify_regex(regex)
                decorator = ', '.join(decorators)

                if format_style == 'json':
                    views.append({"url": url, "module": module, "name": url_name, "decorators": decorator})
                else:
                    views.append(fmtr.format(
                        module='{0}.{1}'.format(style.MODULE(func.__module__), style.MODULE_NAME(func_name)),
                        url_name=style.URL_NAME(url_name),
                        url=style.URL(url),
                        decorator=decorator,
                    ).strip())

        if not options.get('unsorted', False) and format_style != 'json':
            views = sorted(views)

        if format_style == 'aligned':
            views = [row.split(',', 3) for row in views]
            widths = [len(max(columns, key=len)) for columns in zip(*views)]
            views = [
                '   '.join('{0:<{1}}'.format(cdata, width) for width, cdata in zip(widths, row))
                for row in views
            ]
        elif format_style == 'table':
            # Reformat all data and show in a table format

            views = [row.split(',', 3) for row in views]
            widths = [len(max(columns, key=len)) for columns in zip(*views)]
            table_views = []

            header = (style.MODULE_NAME('URL'), style.MODULE_NAME('Module'), style.MODULE_NAME('Name'), style.MODULE_NAME('Decorator'))
            table_views.append(
                ' | '.join('{0:<{1}}'.format(title, width) for width, title in zip(widths, header))
            )
            table_views.append('-+-'.join('-' * width for width in widths))

            for row in views:
                table_views.append(
                    ' | '.join('{0:<{1}}'.format(cdata, width) for width, cdata in zip(widths, row))
                )

            # Replace original views so we can return the same object
            views = table_views

        elif format_style == 'json':
            if pretty_json:
                return json.dumps(views, indent=4)
            return json.dumps(views)

        return "\n".join([v for v in views]) + "\n"

    def extract_views_from_urlpatterns(self, urlpatterns, base='', namespace=None):
        """
        Return a list of views from a list of urlpatterns.

        Each object in the returned list is a two-tuple: (view_func, regex)
        """
        views = []
        for p in urlpatterns:
            if isinstance(p, (URLPattern, RegexURLPattern)):
                try:
                    if not p.name:
                        name = p.name
                    elif namespace:
                        name = '{0}:{1}'.format(namespace, p.name)
                    else:
                        name = p.name
                    pattern = describe_pattern(p)
                    views.append((p.callback, base + pattern, name))
                except ViewDoesNotExist:
                    continue
            elif isinstance(p, (URLResolver, RegexURLResolver)):
                try:
                    patterns = p.url_patterns
                except ImportError:
                    continue
                if namespace and p.namespace:
                    _namespace = '{0}:{1}'.format(namespace, p.namespace)
                else:
                    _namespace = (p.namespace or namespace)
                pattern = describe_pattern(p)
                if isinstance(p, LocaleRegexURLResolver):
                    for langauge in self.LANGUAGES:
                        with translation.override(langauge[0]):
                            views.extend(self.extract_views_from_urlpatterns(patterns, base + pattern, namespace=_namespace))
                else:
                    views.extend(self.extract_views_from_urlpatterns(patterns, base + pattern, namespace=_namespace))
            elif hasattr(p, '_get_callback'):
                try:
                    views.append((p._get_callback(), base + describe_pattern(p), p.name))
                except ViewDoesNotExist:
                    continue
            elif hasattr(p, 'url_patterns') or hasattr(p, '_get_url_patterns'):
                try:
                    patterns = p.url_patterns
                except ImportError:
                    continue
                views.extend(self.extract_views_from_urlpatterns(patterns, base + describe_pattern(p), namespace=namespace))
            else:
                raise TypeError("%s does not appear to be a urlpattern object" % p)
        return views
