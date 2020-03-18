# -*- coding: utf-8 -*-
# Author: OmenApps. http://www.omenapps.com
import ast

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand
from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    """A simple management command which lists model metadata."""

    help = "List out useful metadata for each model"

    def list_fields(self):
        model_list = sorted(
            django_apps.get_models(), key=lambda x: (x._meta.app_label, x._meta.object_name), reverse=False
        )
        for model in model_list:
            print('\n\n"' + model._meta.app_label + "." + model._meta.object_name + '"\n')

            fields = str([f.name for f in model._meta.get_fields()])
            field_list = ast.literal_eval(fields)
            for field in field_list:
                print("\t" + field)

        print("\n\nTotal Models in Project: ", len(model_list), "\n")

    @signalcommand
    def handle(self, *args, **kwargs):
        self.list_fields()
