# -*- coding: utf-8 -*-
from django.apps import apps as django_apps
from django.contrib.auth.management import create_permissions
from django.core.management.base import BaseCommand

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    args = '<app app ...>'
    help = 'reloads permissions for specified apps, or all apps if no args are specified'

    @signalcommand
    def handle(self, *args, **options):
        apps = set()
        if not args:
            apps = django_apps.get_app_configs()
        else:
            for arg in args:
                apps.add(django_apps.get_app_config(arg))

        for app in apps:
            create_permissions(app, int(options.get('verbosity', 3)))
