from collections import defaultdict
import fnmatch
import functools
import re
import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template

from django_extensions.compat import get_template_setting
from django_extensions.management.color import color_style, no_style
from django_extensions.management.utils import signalcommand
from django_extensions.utils.extract_views_from_urlpatterns import (
    extract_views_from_urlpatterns,
)


class Command(BaseCommand):
    args = ""
    help = "Verify named URLs in templates"
    ignores = set(
        [
            "*.swp",
            "*~",
        ]
    )

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--ignore-app",
            action="append",
            dest="ignore_apps",
            default=["admin"],
            help="Ignore these apps",
        )
        parser.add_argument(
            "--urlconf",
            "-c",
            dest="urlconf",
            default="ROOT_URLCONF",
            help="Set the settings URL conf variable to use",
        )

    def ignore_filename(self, filename):
        filename = os.path.basename(filename)
        for ignore_pattern in self.ignores:
            if fnmatch.fnmatch(filename, ignore_pattern):
                return True
        return False

    @signalcommand
    def handle(self, *args, **options):
        style = no_style() if options["no_color"] else color_style()

        self.names = defaultdict(list)
        self.views = {}

        self.collect_templates(options)
        self.collect_views(options)

        for name in sorted(self.names):
            n = len(self.names[name])
            color = style.MODULE
            try:
                v = self.views[name]
                print(
                    style.INFO(
                        f"Name: {name} ({n} occurrences, handled in {v[0]}, {v[1]})"
                    )
                )
            except KeyError:
                print(style.URL_NAME(f"Name: {name} ({n} occurrences, UNKNOWN VIEW)"))
                color = style.URL_NAME
            for item in self.names[name]:
                print(color(f"* {item[0]}:{item[1]}"))

    def collect_templates(self, options):
        template_dirs = set(get_template_setting("DIRS", []))

        for app in apps.get_app_configs():
            if app.name.split(".")[-1] in options["ignore_apps"]:
                continue
            app_template_dir = os.path.join(app.path, "templates")
            if os.path.isdir(app_template_dir):
                template_dirs.add(app_template_dir)

        settings.TEMPLATES[0]["DIRS"] = list(template_dirs)

        self.template_parse_errors = 0
        self.names_re = re.compile(r"\{%\s*url\s*['\"]([\w\-]+)['\"]")

        for template_dir in template_dirs:
            for root, dirs, filenames in os.walk(template_dir):
                for filename in filenames:
                    if self.ignore_filename(filename):
                        continue
                    filepath = os.path.join(root, filename)
                    self.process_template(filepath)

        if self.template_parse_errors > 0:
            self.stdout.write(
                f"{self.template_parse_errors} template parse errors found"
            )

    def collect_views(self, options):
        urlconf = options["urlconf"]

        if not hasattr(settings, urlconf):
            raise CommandError(
                "Settings module {} does not have the attribute {}.".format(
                    settings, urlconf
                )
            )

        try:
            urlconf = __import__(getattr(settings, urlconf), {}, {}, [""])
        except Exception as e:
            raise CommandError(
                "Error occurred while trying to load %s: %s"
                % (getattr(settings, urlconf), str(e))
            )

        view_functions = extract_views_from_urlpatterns(urlconf.urlpatterns)
        for func, regex, view in view_functions:
            if view is not None:
                if isinstance(func, functools.partial):
                    func = func.func
                if hasattr(func, "view_class"):
                    func = func.view_class
                if hasattr(func, "__name__"):
                    func_name = func.__name__
                elif hasattr(func, "__class__"):
                    func_name = "%s()" % func.__class__.__name__
                else:
                    func_name = re.sub(r" at 0x[0-9a-f]+", "", repr(func))

                self.views[view] = (func_name, regex)

    def process_template(self, filepath):
        try:
            get_template(filepath)
        except Exception:
            self.template_parse_errors += 1
            self.stdout.write(f"Error parsing template {filepath}")

        with open(filepath, "r") as file:
            lineno = 1
            for line in file:
                for match in self.names_re.findall(line):
                    self.names[match].append((filepath, lineno))
                lineno += 1
