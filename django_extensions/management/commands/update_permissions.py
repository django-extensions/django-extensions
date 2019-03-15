# -*- coding: utf-8 -*-
from django.apps import apps as django_apps
from django.contrib.auth.management import create_permissions
from django.core.management.base import BaseCommand

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = 'reloads permissions for specified apps, or all apps if no args are specified'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--apps',
            dest='apps',
            help='Reload permissions only for apps (comma separated)'
        )

    @signalcommand
    def handle(self, *args, **options):
        if options['apps']:
            app_names = options['apps'].split(',')
            apps = [django_apps.get_app_config(x) for x in app_names]
        else:
            apps = django_apps.get_app_configs()

        for app in apps:
            create_permissions(app, options['verbosity'])
