import functools
import json
import re

from django.conf import settings
from django.contrib.admindocs.views import simplify_regex
from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.color import color_style, no_style
from django_extensions.management.utils import signalcommand
from django_extensions.utils.extract_views_from_urlpatterns import (
    extract_views_from_urlpatterns,
)


FMTR = {
    "dense": "{url}\t{module}\t{url_name}\t{decorator}",
    "table": "{url},{module},{url_name},{decorator}",
    "aligned": "{url},{module},{url_name},{decorator}",
    "verbose": "{url}\n\tController: {module}\n\tURL Name: {url_name}\n\tDecorators: {decorator}\n",  # noqa: E501
    "json": "",
    "pretty-json": "",
}


class Command(BaseCommand):
    help = "Displays all of the url matching routes for the project."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--unsorted",
            "-u",
            action="store_true",
            dest="unsorted",
            help="Show urls unsorted but same order as found in url patterns",
        )
        parser.add_argument(
            "--decorator",
            "-d",
            action="append",
            dest="decorator",
            default=[],
            help="Show the presence of given decorator on views",
        )
        parser.add_argument(
            "--format",
            "-f",
            dest="format_style",
            default="dense",
            help="Style of the output. Choices: %s" % FMTR.keys(),
        )
        parser.add_argument(
            "--urlconf",
            "-c",
            dest="urlconf",
            default="ROOT_URLCONF",
            help="Set the settings URL conf variable to use",
        )

    @signalcommand
    def handle(self, *args, **options):
        style = no_style() if options["no_color"] else color_style()

        decorator = options["decorator"]
        if not decorator:
            decorator = ["login_required"]

        format_style = options["format_style"]
        if format_style not in FMTR:
            raise CommandError(
                "Format style '%s' does not exist. Options: %s"
                % (
                    format_style,
                    ", ".join(sorted(FMTR.keys())),
                )
            )
        pretty_json = format_style == "pretty-json"
        if pretty_json:
            format_style = "json"
        fmtr = FMTR[format_style]

        urlconf = options["urlconf"]

        views = []
        if not hasattr(settings, urlconf):
            raise CommandError(
                "Settings module {} does not have the attribute {}.".format(
                    settings, urlconf
                )
            )

        try:
            urlconf = __import__(getattr(settings, urlconf), {}, {}, [""])
        except Exception as e:
            if options["traceback"]:
                import traceback

                traceback.print_exc()
            raise CommandError(
                "Error occurred while trying to load %s: %s"
                % (getattr(settings, urlconf), str(e))
            )

        view_functions = extract_views_from_urlpatterns(urlconf.urlpatterns)
        for func, regex, url_name in view_functions:
            if hasattr(func, "__globals__"):
                func_globals = func.__globals__
            elif hasattr(func, "func_globals"):
                func_globals = func.func_globals
            else:
                func_globals = {}

            decorators = [d for d in decorator if d in func_globals]

            if isinstance(func, functools.partial):
                func = func.func
                decorators.insert(0, "functools.partial")

            if hasattr(func, "view_class"):
                func = func.view_class
            if hasattr(func, "__name__"):
                func_name = func.__name__
            elif hasattr(func, "__class__"):
                func_name = "%s()" % func.__class__.__name__
            else:
                func_name = re.sub(r" at 0x[0-9a-f]+", "", repr(func))

            module = "{0}.{1}".format(func.__module__, func_name)
            url_name = url_name or ""
            url = simplify_regex(regex)
            decorator = ", ".join(decorators)

            if format_style == "json":
                views.append(
                    {
                        "url": url,
                        "module": module,
                        "name": url_name,
                        "decorators": decorator,
                    }
                )
            else:
                views.append(
                    fmtr.format(
                        module="{0}.{1}".format(
                            style.MODULE(func.__module__), style.MODULE_NAME(func_name)
                        ),
                        url_name=style.URL_NAME(url_name),
                        url=style.URL(url),
                        decorator=decorator,
                    ).strip()
                )

        if not options["unsorted"] and format_style != "json":
            views = sorted(views)

        if format_style == "aligned":
            views = [row.split(",", 3) for row in views]
            widths = [len(max(columns, key=len)) for columns in zip(*views)]
            views = [
                "   ".join(
                    "{0:<{1}}".format(cdata, width) for width, cdata in zip(widths, row)
                )
                for row in views
            ]
        elif format_style == "table":
            # Reformat all data and show in a table format

            views = [row.split(",", 3) for row in views]
            widths = [len(max(columns, key=len)) for columns in zip(*views)]
            table_views = []

            header = (
                style.MODULE_NAME("URL"),
                style.MODULE_NAME("Module"),
                style.MODULE_NAME("Name"),
                style.MODULE_NAME("Decorator"),
            )
            table_views.append(
                " | ".join(
                    "{0:<{1}}".format(title, width)
                    for width, title in zip(widths, header)
                )
            )
            table_views.append("-+-".join("-" * width for width in widths))

            for row in views:
                table_views.append(
                    " | ".join(
                        "{0:<{1}}".format(cdata, width)
                        for width, cdata in zip(widths, row)
                    )
                )

            # Replace original views so we can return the same object
            views = table_views

        elif format_style == "json":
            if pretty_json:
                return json.dumps(views, indent=4)
            return json.dumps(views)

        return "\n".join([v for v in views]) + "\n"
