# -*- coding: utf-8 -*-
# Author: OmenApps. http://www.omenapps.com
from django.apps import apps as django_apps
from django.core.management.base import BaseCommand
from django_extensions.management.utils import signalcommand
import ast


class Command(BaseCommand):
    """A simple management command which lists model metadata."""
    help = 'List out useful metadata for each model'

    def list_fields(self):
        model_list = sorted(django_apps.get_models(), key=lambda x: (x._meta.app_label, x._meta.object_name), reverse=False)
        for model in model_list:
            print('\nFields for App "' + model._meta.app_label + '", Model "' + model._meta.object_name + '":')

            fields = str([f.name for f in model._meta.get_fields()])
            field_list = ast.literal_eval(fields)
            for field in field_list:
                print('\t' + field)

    @signalcommand
    def handle(self, *args, **kwargs):
        self.list_fields()
