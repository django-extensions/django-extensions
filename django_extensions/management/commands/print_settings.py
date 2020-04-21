# -*- coding: utf-8 -*-
"""
print_settings
==============

Django command similar to 'diffsettings' but shows all active Django settings.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.utils import signalcommand


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
            default='simple',
            dest='format',
            help='Specifies output format.'
        )
        parser.add_argument(
            '--indent',
            default=4,
            dest='indent',
            type=int,
            help='Specifies indent level for JSON and YAML'
        )

    @signalcommand
    def handle(self, *args, **options):
        a_dict = {}

        for attr in dir(settings):
            if self.include_attr(attr, options['setting']):
                value = getattr(settings, attr)
                a_dict[attr] = value

        for setting in args:
            if setting not in a_dict:
                raise CommandError('%s not found in settings.' % setting)

        output_format = options['format']
        indent = options['indent']

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
