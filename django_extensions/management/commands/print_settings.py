# -*- coding: utf-8 -*-
"""
print_settings
==============

Django command similar to 'diffsettings' but shows all active Django settings.
"""

import json

from django.conf import settings as default_settings
from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.utils import signalcommand
from django.views.debug import SafeExceptionReporterFilter

DEFAULT_FORMAT = 'simple'
DEFAULT_INDENT = 4
DEFAULT_SECRETS = False


class Command(BaseCommand):
    help = "Print the active Django settings."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            'setting',
            nargs='*',
            help='Specifies setting to be printed.'
        )
        parser.add_argument(
            '--format',
            default=DEFAULT_FORMAT,
            dest='format',
            help='Specifies output format.'
        )
        parser.add_argument(
            '--indent',
            default=DEFAULT_INDENT,
            dest='indent',
            type=int,
            help='Specifies indent level for JSON and YAML'
        )
        parser.add_argument(
            '--show-secrets',
            default=DEFAULT_SECRETS,
            dest='show secrets',
            type=bool,
            help='Specifies if should be revealed the value of secrets'
        )

    @signalcommand
    def handle(self, *args, **options):

        show_secrets, output_format, indent = self.get_defaults(options)

        a_dict = {}

        if show_secrets:
            for attr in dir(default_settings):
                if self.include_attr(attr, options['setting']):
                    value = getattr(default_settings, attr)
                    a_dict[attr] = value
        else:
            settings = self.safe_settings()
            for key in settings.keys():
                if key in options['setting'] or not options['setting']:
                    a_dict[key] = settings.get(key)

        for setting in args:
            if setting not in a_dict:
                raise CommandError('%s not found in settings.' % setting)

        if output_format == 'json':
            print(json.dumps(a_dict, indent=indent))
        elif output_format == 'yaml':
            import yaml  # requires PyYAML
            print(yaml.dump(a_dict, indent=indent))
        elif output_format == 'pprint':
            from pprint import pprint
            pprint(a_dict)
        elif output_format == 'text':
            for key, value in a_dict.items():
                print("%s = %s" % (key, value))
        elif output_format == 'value':
            for value in a_dict.values():
                print(value)
        else:
            self.print_simple(a_dict)

    @staticmethod
    def get_defaults(options):
        a_options = [
            options.get('show secrets', DEFAULT_SECRETS),
            options.get('format', DEFAULT_FORMAT),
            options.get('indent', DEFAULT_INDENT)
        ]
        return a_options

    @staticmethod
    def include_attr(attr, settings):
        if attr.startswith('__'):
            return False
        elif settings == []:
            return True
        elif attr in settings:
            return True

    @staticmethod
    def print_simple(a_dict):
        for key, value in a_dict.items():
            print('%-40s = %r' % (key, value))

    @staticmethod
    def safe_settings():
        try:
            return SafeExceptionReporterFilter().get_safe_settings()
        except AttributeError:
            # In django < 3.0 does not have this class
            # We have to make a different import
            from django.views.debug import get_safe_settings
            return get_safe_settings()
