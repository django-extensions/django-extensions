"""
print_settings
==============

Django command similar to 'diffsettings' but shows all active Django settings.
"""

import fnmatch
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_extensions.compat import get_safe_settings
from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Print the active Django settings."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "setting", nargs="*", help="Specifies setting to be printed."
        )
        parser.add_argument(
            "-f",
            "--fail",
            action="store_true",
            dest="fail",
            help="Fail if invalid setting name is given.",
        )
        parser.add_argument(
            "--format", default="simple", dest="format", help="Specifies output format."
        )
        parser.add_argument(
            "--indent",
            default=4,
            dest="indent",
            type=int,
            help="Specifies indent level for JSON and YAML",
        )
        parser.add_argument(
            "--show-secrets",
            action="store_true",
            dest="show_secrets",
            help="Show secrets in the output without masking.",
        )

    @signalcommand
    def handle(self, *args, **options):
        setting_names = options["setting"]

        if not options["show_secrets"]:
            settings_dct = get_safe_settings()
        else:
            settings_dct = {
                k: getattr(settings, k) for k in dir(settings) if k.isupper()
            }

        if setting_names:
            settings_dct = {
                key: value
                for key, value in settings_dct.items()
                if any(
                    fnmatch.fnmatchcase(key, setting_name)
                    for setting_name in setting_names
                )
            }

        if options["fail"]:
            for setting_name in setting_names:
                if not any(
                    fnmatch.fnmatchcase(key, setting_name)
                    for key in settings_dct.keys()
                ):
                    raise CommandError("%s not found in settings." % setting_name)

        output_format = options["format"]
        indent = options["indent"]

        if output_format == "json":
            print(json.dumps(settings_dct, indent=indent))
        elif output_format == "yaml":
            import yaml  # requires PyYAML

            print(yaml.dump(settings_dct, indent=indent))
        elif output_format == "pprint":
            from pprint import pprint

            pprint(settings_dct)
        elif output_format == "text":
            for key, value in settings_dct.items():
                print("%s = %s" % (key, value))
        elif output_format == "value":
            for value in settings_dct.values():
                print(value)
        else:
            for key, value in settings_dct.items():
                print("%-40s = %r" % (key, value))
