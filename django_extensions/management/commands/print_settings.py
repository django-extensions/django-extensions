# coding=utf-8
"""
print_settings
==============

Django command similar to 'diffsettings' but shows all active Django settings.
"""

from django.conf import settings
from django.core.management.base import CommandError

from django_extensions.management.utils import signalcommand
from django_extensions.compat import CompatibilityBaseCommand as BaseCommand


class Command(BaseCommand):
    """print_settings command"""

    help = "Print the active Django settings."

    def add_arguments(self, parser):
        parser.add_argument('--format', default='simple', dest='format',
                            help='Specifies output format.')
        parser.add_argument('--indent', default=4, dest='indent', type=int,
                            help='Specifies indent level for JSON and YAML')

    @signalcommand
    def handle(self, *args, **options):
        a_dict = {}

        for attr in dir(settings):
            if self.include_attr(attr, args):
                value = getattr(settings, attr)
                a_dict[attr] = value

        for setting in args:
            if setting not in a_dict:
                raise CommandError('%s not found in settings.' % setting)

        output_format = options.get('format', 'json')
        indent = options.get('indent', 4)

        if output_format == 'json':
            json = self.import_json()
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
    def include_attr(attr, args):
        """Whether or not to include attribute in output"""

        if not attr.startswith('__'):
            if args is not ():
                if attr in args:
                    return True
            else:
                return True
        else:
            return False

    @staticmethod
    def print_simple(a_dict):
        """A very simple output format"""

        for key, value in a_dict.items():
            print('%-40s = %r' % (key, value))

    @staticmethod
    def import_json():
        """Import a module for JSON"""

        try:
            import json
        except ImportError:
            import simplejson as json  # NOQA
        return json
