# -*- coding: utf-8 -*-
import os
from collections import defaultdict

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Prints a list of all files in MEDIA_ROOT that are not referenced in the database."

    @signalcommand
    def handle(self, *args, **options):
        if settings.MEDIA_ROOT == '':
            print("MEDIA_ROOT is not set, nothing to do")
            return

        # Get a list of all files under MEDIA_ROOT
        media = []
        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for f in files:
                media.append(os.path.abspath(os.path.join(root, f)))

        # Get list of all fields (value) for each model (key)
        # that is a FileField or subclass of a FileField
        model_dict = defaultdict(list)
        for model in apps.get_models():
            for field in model._meta.fields:
                if issubclass(field.__class__, models.FileField):
                    model_dict[model].append(field)

        # Get a list of all files referenced in the database
        referenced = []
        for model in model_dict:
            all = model.objects.all().iterator()
            for object in all:
                for field in model_dict[model]:
                    target_file = getattr(object, field.name)
                    if target_file:
                        referenced.append(os.path.abspath(target_file.path))

        # Print each file in MEDIA_ROOT that is not referenced in the database
        for m in media:
            if m not in referenced:
                print(m)
