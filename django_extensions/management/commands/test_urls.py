# -*- coding: utf-8 -*-
import functools
import json
import re
import urllib

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
    'dense': "{code}\t{url}\t{module}\t{url_name}\t{decorator}",
    'table': "{code},{url},{module},{url_name},{decorator}",
    'aligned': "{code},{url},{module},{url_name},{decorator},{code}",
    'verbose': "Code: {code}\n\t{url}\n\tController: {module}\n\tURL Name: {url_name}\n\tDecorators: {decorator}\n",
    'json': '',
    'pretty-json': ''
}


class Command(BaseCommand):
    help = "Tests all of the url matching routes for the project (requires running server)."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--unsorted", "-u", action="store_true", dest="unsorted",
            help="Show urls unsorted but same order as found in url patterns"
        )
        parser.add_argument(
            "--language", "-l", dest="language",
            help="Only show this language code (useful for i18n_patterns)"
        )
        parser.add_argument(
            "--decorator", "-d", action="append", dest="decorator", default=[],
            help="Show the presence of given decorator on views"
        )
        parser.add_argument(
            "--format", "-f", dest="format_style", default="dense",
            help="Style of the output. Choices: %s" % FMTR.keys()
        )
        parser.add_argument(
            "--urlconf", "-c", dest="urlconf", default="ROOT_URLCONF",
            help="Set the settings URL conf variable to use"
        )
        parser.add_argument(
            "--base", "-b", dest="base", default="http://127.0.0.1:8000/",
            help="Set your host url variable to use"
        )
        parser.add_argument(
            "--mockpk", "-p", dest="mock_pk", default="1",
            help="Set your default value for insert in <placeholders>"
        )

    @signalcommand
    def handle(self, *args, **options):
        style = no_style() if options['no_color'] else color_style()

        language = options['language']
        if language is not None:
            translation.activate(language)
            self.LANGUAGES = [(code, name) for code, name in getattr(settings, 'LANGUAGES', []) if code == language]
        else:
            self.LANGUAGES = getattr(settings, 'LANGUAGES', ((None, None), ))

        decorator = options['decorator']
        if not decorator:
            decorator = ['login_required']

        host = options['base']
        mock_pk = options['mock_pk']

        format_style = options['format_style']
        if format_style not in FMTR:
            raise CommandError(
                "Format style '%s' does not exist. Options: %s" % (
                    format_style,
                    ", ".join(sorted(FMTR.keys())),
                )
            )
        pretty_json = format_style == 'pretty-json'
        if pretty_json:
            format_style = 'json'
        fmtr = FMTR[format_style]

        urlconf = options['urlconf']

        views = []
        if not hasattr(settings, urlconf):
            raise CommandError("Settings module {} does not have the attribute {}.".format(settings, urlconf))

        try:
            urlconf = __import__(getattr(settings, urlconf), {}, {}, [''])
        except Exception as e:
            if options['traceback']:
                import traceback
                traceback.print_exc()
            raise CommandError("Error occurred while trying to load %s: %s" % (getattr(settings, urlconf), str(e)))

        view_functions = self.extract_views_from_urlpatterns(urlconf.urlpatterns)
        coverage = len(view_functions)
        for (func, regex, url_name) in view_functions:
            if hasattr(func, '__globals__'):
                func_globals = func.__globals__
            elif hasattr(func, 'func_globals'):
                func_globals = func.func_globals
            else:
                func_globals = {}

            decorators = [d for d in decorator if d in func_globals]

            try:
                p = re.compile(r'<.*?>|\(.*?\)|\[.*?\]')
                url = p.sub(str(mock_pk), regex).replace('^','').replace('\\','').replace('$','')#mock pk 1
                conn = urllib.request.urlopen(host+url)
                response = conn.getcode()
                conn.close()
            except urllib.error.HTTPError as e:
                response = str(e.code)
                coverage -= 1
            except urllib.error.URLError as e:
                response = e.reason
                coverage -= 1
            except Exception as e:
                print(url,e)
                coverage -= 1
                response = e

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
            code = response

            if format_style == 'json':
                views.append({"url": url, "module": module, "name": url_name, "decorators": decorator, "code": code})
            else:
                views.append(fmtr.format(
                    module='{0}.{1}'.format(style.MODULE(func.__module__), style.MODULE_NAME(func_name)),
                    url_name=style.URL_NAME(url_name),
                    url=style.URL(url),
                    decorator=decorator,
                    code=code
                ).strip())

        if not options['unsorted'] and format_style != 'json':
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


        return "\n".join([v for v in views]) + "\n coverage: " + str(coverage)+" / " + str(len(view_functions))+"\n"

    def extract_views_from_urlpatterns(self, urlpatterns, base='', namespace=None):
        """
        Return a list of views from a list of urlpatterns.

        Each object in the returned list is a three-tuple: (view_func, regex, name)
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
                    for language in self.LANGUAGES:
                        with translation.override(language[0]):
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
